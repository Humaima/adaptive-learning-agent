from sqlalchemy.orm import Session
from langgraph.types import interrupt

from src.graph.concept_graph import ConceptGraph
from src.agents.assessment import assess_knowledge
from src.agents.difficulty_estimator import estimate_difficulty
from src.agents.tutor import generate_tutoring_content
from src.agents.quiz_generator import generate_quiz
from src.agents.evaluator import evaluate_quiz
from src.agents.update_loop import run_update_loop
from src.agents.graph_state import TutorGraphState
from src.models.schemas import MasteryStatus
from src.config import MAX_LOOP_ITERATIONS


def build_nodes(db: Session, cg: ConceptGraph):
    """Returns a dict of node functions, all closing over the same db session and concept graph."""

    def assess_node(state: TutorGraphState) -> dict:
        student_id = state.get("student_id")
        original_question = state.get("original_question")
        if student_id is None or original_question is None:
            raise ValueError("student_id and original_question are required to assess knowledge")
        result = assess_knowledge(db, student_id, original_question, cg)
        return {
            "assessment": result,
            "target_concept_id": result.target_concept_id,
            "teaching_history": [],
            "iteration_count": 0,
        }

    def difficulty_node(state: TutorGraphState) -> dict:
        assessment = state.get("assessment")
        if assessment is None:
            raise ValueError("assessment is required before estimating difficulty")
        estimate = estimate_difficulty(assessment)
        return {"difficulty_estimate": estimate}

    def tutor_node(state: TutorGraphState) -> dict:
        assessment = state.get("assessment")
        difficulty_estimate = state.get("difficulty_estimate")
        if assessment is None or difficulty_estimate is None:
            raise ValueError("assessment and difficulty_estimate are required before tutoring")
        response = generate_tutoring_content(cg, assessment, difficulty_estimate)
        history = state.get("teaching_history", []) + [response]
        return {"tutor_response": response, "teaching_history": history}

    def quiz_node(state: TutorGraphState) -> dict:
        tutor_response = state.get("tutor_response")
        if tutor_response is None:
            raise ValueError("tutor_response is required before generating a quiz")
        quiz = generate_quiz(cg, tutor_response.concept_id, tutor_response.difficulty)
        return {"quiz": quiz}

    def collect_answers_node(state: TutorGraphState) -> dict:
        """
        Pauses the graph here and waits for the real student to answer.
        The payload passed to interrupt() is what your Phase 10 API/UI will
        show the student; whatever comes back via Command(resume=...) becomes
        the return value of interrupt() right here.
        """
        quiz = state.get("quiz")
        if quiz is None:
            raise ValueError("quiz is required before collecting answers")
        payload = {
            "concept_id": quiz.concept_id,
            "difficulty": quiz.difficulty.value,
            "questions": [
                {
                    "question_id": q.question_id,
                    "question_type": q.question_type.value,
                    "question_text": q.question_text,
                    "options": [{"label": o.label, "text": o.text} for o in q.options],
                }
                for q in quiz.questions
            ],
        }
        student_answers = interrupt(payload)  # <-- graph pauses HERE until resumed
        return {"student_answers": student_answers}

    def evaluate_node(state: TutorGraphState) -> dict:
        quiz = state.get("quiz")
        student_answers = state.get("student_answers")
        if quiz is None or student_answers is None:
            raise ValueError("quiz and student_answers are required before evaluation")
        results = evaluate_quiz(quiz.questions, student_answers)
        return {"eval_results": results}

    def update_node(state: TutorGraphState) -> dict:
        student_id = state.get("student_id")
        original_question = state.get("original_question")
        target_concept_id = state.get("target_concept_id")
        eval_results = state.get("eval_results")
        if (
            student_id is None
            or original_question is None
            or target_concept_id is None
            or eval_results is None
        ):
            raise ValueError(
                "student_id, original_question, target_concept_id, and eval_results "
                "are required before updating"
            )
        result = run_update_loop(
            db,
            student_id,
            original_question,
            target_concept_id,
            cg,
            eval_results,
        )
        return {
            "update_result": result,
            "assessment": result.updated_assessment,  # freshest mastery picture, feeds next loop
            "iteration_count": state.get("iteration_count", 0) + 1,
        }

    return {
        "assess": assess_node,
        "difficulty": difficulty_node,
        "tutor": tutor_node,
        "quiz": quiz_node,
        "collect_answers": collect_answers_node,
        "evaluate": evaluate_node,
        "update": update_node,
    }


def route_after_update(state: TutorGraphState) -> str:
    """
    Decides: are we truly done (the ORIGINAL target concept is now mastered),
    or do we need another teach->quiz->evaluate->update round on the next gap?
    """
    target_id = state.get("target_concept_id")
    assessment = state.get("assessment")
    if target_id is None or assessment is None:
        raise ValueError("target_concept_id and assessment are required after update")
    target_assessment = next(
        a for a in assessment.assessments if a.concept_id == target_id
    )

    if target_assessment.status == MasteryStatus.MASTERED:
        return "done"
    if state.get("iteration_count", 0) >= MAX_LOOP_ITERATIONS:
        return "done"  # safety cap — avoid an unbounded loop from a stubborn concept
    return "continue"