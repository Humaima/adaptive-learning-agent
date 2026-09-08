from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from langgraph.types import Command
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.runnables import RunnableConfig

from src.graph.concept_graph import ConceptGraph
from src.agents.tutor_graph import build_tutor_graph
from src.db.database import SessionLocal
from src.db.repository import get_student_model
from src.api.schemas import (
    AskRequest, AnswerRequest, TutorTurnResponse, QuizOut, QuizOptionOut, QuizQuestionOut,
    TutoringStepOut, StudentMasteryResponse, MasteryEntry, ConceptOut,
)
from src.api.auth_routes import router as auth_router
from src.auth.dependencies import get_current_student_id

# Built once at startup — shared across all requests. Cheap/pure, no I/O beyond the JSON read.
cg = ConceptGraph.from_dataset_json("data/concepts_dataset.json")


@asynccontextmanager
async def lifespan(app: FastAPI):
    with SqliteSaver.from_conn_string("data/checkpoints.sqlite") as checkpointer:
        checkpointer.setup()  # creates the checkpoint tables on first run — no-op if they already exist
        app.state.graph = build_tutor_graph(cg, checkpointer)
        yield
    # connection closes automatically when the `with` block exits (server shutdown)


app = FastAPI(title="Adaptive Learning Agent API", lifespan=lifespan)

app.include_router(auth_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite's default dev server port
    allow_methods=["*"],
    allow_headers=["*"],
)


def _thread_config(student_id: str) -> RunnableConfig:
    return {"configurable": {"thread_id": f"student-{student_id}"}}


def _teaching_step_out(tr) -> TutoringStepOut:
    return TutoringStepOut(
        concept_id=tr.concept_id, concept_name=tr.concept_name, difficulty=tr.difficulty.value,
        is_prerequisite_redirect=tr.is_prerequisite_redirect, explanation=tr.explanation,
        key_points=tr.key_points, worked_example=tr.worked_example, transition_note=tr.transition_note,
    )


def _result_to_response(result: dict) -> TutorTurnResponse:
    if "__interrupt__" in result:
        quiz_payload = result["__interrupt__"][0].value
        quiz_out = QuizOut(
            concept_id=quiz_payload["concept_id"],
            difficulty=quiz_payload["difficulty"],
            questions=[
                QuizQuestionOut(
                    question_id=q["question_id"], question_type=q["question_type"],
                    question_text=q["question_text"],
                    options=[QuizOptionOut(**o) for o in q["options"]],
                )
                for q in quiz_payload["questions"]
            ],
        )
        history = [_teaching_step_out(tr) for tr in result.get("teaching_history", [])]
        return TutorTurnResponse(
            status="awaiting_answers", quiz=quiz_out,
            latest_teaching=history[-1] if history else None, teaching_history=history,
        )

    history = [_teaching_step_out(tr) for tr in result.get("teaching_history", [])]
    return TutorTurnResponse(
        status="done", quiz=None,
        latest_teaching=history[-1] if history else None, teaching_history=history,
    )


@app.post("/ask", response_model=TutorTurnResponse)
def ask(request: Request, body: AskRequest, student_id: str = Depends(get_current_student_id)):
    config = _thread_config(student_id)
    result = request.app.state.graph.invoke(
        {"student_id": student_id, "original_question": body.question}, config=config
    )
    return _result_to_response(result)


@app.post("/answer", response_model=TutorTurnResponse)
def answer(request: Request, body: AnswerRequest, student_id: str = Depends(get_current_student_id)):
    config = _thread_config(student_id)
    try:
        result = request.app.state.graph.invoke(Command(resume=body.answers), config=config)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No active session to resume: {e}")
    return _result_to_response(result)


@app.get("/student/me/mastery", response_model=StudentMasteryResponse)
def student_mastery(student_id: str = Depends(get_current_student_id)):
    db = SessionLocal()
    try:
        model = get_student_model(db, student_id)
    finally:
        db.close()

    entries = []
    student_mastery_map = model.mastery or {}
    for concept_id, data in cg.graph.nodes(data=True):
        node_data = data or {}
        entries.append(MasteryEntry(
            concept_id=concept_id, concept_name=node_data.get("name", concept_id),
            domain=node_data.get("domain", ""), mastery=student_mastery_map.get(concept_id),
        ))
    return StudentMasteryResponse(student_id=student_id, mastery=entries)


@app.get("/concepts", response_model=list[ConceptOut])
def list_concepts():
    return [
        ConceptOut(
            id=cid, name=(data or {}).get("name", cid),
            domain=(data or {}).get("domain", ""), description=(data or {}).get("description", ""),
        )
        for cid, data in cg.graph.nodes(data=True)
    ]
