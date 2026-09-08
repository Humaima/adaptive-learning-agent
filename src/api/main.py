from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langgraph.types import Command
from langchain_core.runnables import RunnableConfig

from src.graph.concept_graph import ConceptGraph
from src.agents.tutor_graph import build_tutor_graph
from src.db.database import SessionLocal
from src.db.repository import get_student_model
from src.api.schemas import (
    AskRequest, AnswerRequest, TutorTurnResponse, QuizOut, QuizOptionOut, QuizQuestionOut,
    TutoringStepOut, StudentMasteryResponse, MasteryEntry, ConceptOut,
)

app = FastAPI(title="Adaptive Learning Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite's default dev server port
    allow_methods=["*"],
    allow_headers=["*"],
)

# Built once at startup — shared across all requests.
cg = ConceptGraph.from_dataset_json("data/concepts_dataset.json")
graph = build_tutor_graph(cg)


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
def ask(request: AskRequest):
    config = _thread_config(request.student_id)
    result = graph.invoke(
        {"student_id": request.student_id, "original_question": request.question}, config=config
    )
    return _result_to_response(result)


@app.post("/answer", response_model=TutorTurnResponse)
def answer(request: AnswerRequest):
    config = _thread_config(request.student_id)
    try:
        result = graph.invoke(Command(resume=request.answers), config=config)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No active session to resume: {e}")
    return _result_to_response(result)


@app.get("/student/{student_id}/mastery", response_model=StudentMasteryResponse)
def student_mastery(student_id: str):
    db = SessionLocal()
    try:
        model = get_student_model(db, student_id)
    finally:
        db.close()

    entries = []
    student_mastery_map = (model.mastery or {}) if model is not None else {}
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