from sqlalchemy.orm import Session

from src.graph.concept_graph import ConceptGraph
from src.agents.mastery_updater import apply_evaluation_results
from src.agents.assessment import build_assessment_for_target
from src.agents.difficulty_estimator import estimate_difficulty
from src.models.schemas import EvaluationResult, UpdateLoopResult


def run_update_loop(
    db: Session,
    student_id: str,
    original_question: str,
    target_concept_id: str,
    cg: ConceptGraph,
    evaluation_results: list[EvaluationResult],
) -> UpdateLoopResult:
    """
    Closes the loop:
    1. Write the graded quiz results into the student's mastery scores.
    2. Re-check readiness for the ORIGINAL question using the freshly updated scores —
       no LLM call needed here since target_concept_id is already known.
    """
    mastery_updates = apply_evaluation_results(db, student_id, evaluation_results)

    updated_assessment = build_assessment_for_target(
        db, student_id, original_question, target_concept_id, cg
    )
    updated_estimate = estimate_difficulty(updated_assessment)

    return UpdateLoopResult(
        student_id=student_id,
        original_question=original_question,
        target_concept_id=target_concept_id,
        mastery_updates=mastery_updates,
        ready_to_learn_target_now=updated_estimate.ready_to_learn_target,
        updated_assessment=updated_assessment,
    )