from sqlalchemy.orm import Session

from src.config import MASTERY_LEARNING_RATE, INITIAL_MASTERY_PRIOR
from src.db.repository import get_mastery, set_mastery, log_interaction
from src.models.schemas import EvaluationResult, MasteryUpdate


def compute_new_mastery(previous_mastery: float | None, evidence_score: float) -> float:
    """
    EMA-style update: new_mastery = base + learning_rate * (evidence - base).
    If there's no prior mastery at all, start from a neutral prior (0.5) rather than
    jumping straight to whatever this one answer scored — avoids over-reacting to
    a single lucky guess or one bad slip.
    """
    base = previous_mastery if previous_mastery is not None else INITIAL_MASTERY_PRIOR
    new_mastery = base + MASTERY_LEARNING_RATE * (evidence_score - base)
    return max(0.0, min(1.0, new_mastery))  # clamp to valid range


def apply_evaluation_results(
    db: Session, student_id: str, results: list[EvaluationResult]
) -> list[MasteryUpdate]:
    """
    Updates mastery for every concept touched by these evaluation results,
    and logs each answer as an interaction for the audit trail.
    Results are applied in order — if a quiz has 3 questions on the same concept,
    each one nudges mastery a bit further based on cumulative evidence.
    """
    updates = []
    for result in results:
        previous = get_mastery(db, student_id, result.concept_id)
        new_mastery = compute_new_mastery(previous, result.correctness_score)

        set_mastery(db, student_id, result.concept_id, new_mastery)
        log_interaction(
            db,
            student_id,
            result.concept_id,
            interaction_type="quiz_answer",
            content=result.student_answer,
            correct=result.is_correct,
        )

        updates.append(
            MasteryUpdate(
                concept_id=result.concept_id,
                previous_mastery=previous,
                new_mastery=new_mastery,
                evidence_score=result.correctness_score,
            )
        )
    return updates