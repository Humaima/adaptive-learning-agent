import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from langgraph.types import Command
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.runnables import RunnableConfig

from src.graph.concept_graph import ConceptGraph
from src.agents.tutor_graph import build_tutor_graph
from src.db.database import SessionLocal
from src.db.repository import get_student_model
from src.api.schemas import (
    AskRequest, AnswerRequest, TutorTurnResponse, QuizOut, QuizOptionOut, QuizQuestionOut,
    TutoringStepOut, StudentMasteryResponse, MasteryEntry, ConceptOut, LearningPathStep,
)
from src.api.auth_routes import router as auth_router
from src.auth.dependencies import get_current_student_id
from src.config import MASTERY_THRESHOLD

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.api.rate_limit import limiter

# Rough estimate — could later be derived from actual quiz/tutoring time logs
_MINUTES_BY_DOMAIN = {"Math": 15, "CS": 20, "ML": 25, "Physics": 20}

# Built once at startup — shared across all requests. Cheap/pure, no I/O beyond the JSON read.
cg = ConceptGraph.from_dataset_json("data/concepts_dataset.json")

# docker-compose sets DATABASE_URL to the Postgres service (same URL src/db/database.py
# uses for the student model) so checkpoints persist there too; local (non-Docker) dev
# without DATABASE_URL set falls back to a SQLite file, same as before.
DATABASE_URL = os.getenv("DATABASE_URL")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if DATABASE_URL:
        with PostgresSaver.from_conn_string(DATABASE_URL) as checkpointer:
            checkpointer.setup()  # creates the checkpoint tables on first run — no-op if they already exist
            app.state.graph = build_tutor_graph(cg, checkpointer)
            yield
    else:
        with SqliteSaver.from_conn_string("data/checkpoints.sqlite") as checkpointer:
            checkpointer.setup()
            app.state.graph = build_tutor_graph(cg, checkpointer)
            yield
    # connection closes automatically when the `with` block exits (server shutdown)


app = FastAPI(title="Adaptive Learning Agent API", lifespan=lifespan)

app.include_router(auth_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://adaptive-learning-agent-lake.vercel.app/"],  # Vite dev + prod
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
# slowapi's handler is (correctly) typed for the specific RateLimitExceeded it's
# registered for, but Starlette's add_exception_handler expects a handler generic
# over any Exception — a stub-strictness mismatch, not a real bug; this is
# slowapi's own documented usage pattern.
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # pyright: ignore[reportArgumentType]
app.add_middleware(SlowAPIMiddleware)


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
@limiter.limit("15/minute")
def ask(request: Request, body: AskRequest, student_id: str = Depends(get_current_student_id)):
    config = _thread_config(student_id)
    result = request.app.state.graph.invoke(
        {"student_id": student_id, "original_question": body.question}, config=config
    )
    return _result_to_response(result)


@app.post("/answer", response_model=TutorTurnResponse)
@limiter.limit("30/minute")
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


@app.get("/student/me/learning-path", response_model=list[LearningPathStep])
def learning_path(student_id: str = Depends(get_current_student_id)):
    db = SessionLocal()
    try:
        model = get_student_model(db, student_id)
    finally:
        db.close()

    recommended_ids = cg.get_next_recommended_concepts(model.mastery, MASTERY_THRESHOLD, limit=4)

    steps = []
    for cid in recommended_ids:
        info = cg.get_concept_info(cid)
        steps.append(LearningPathStep(
            concept_id=cid, concept_name=info["name"], domain=info["domain"],
            estimated_minutes=_MINUTES_BY_DOMAIN.get(info["domain"], 15),
            done=False,
        ))
    return steps
