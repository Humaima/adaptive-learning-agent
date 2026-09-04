from src.config import DIFFICULTY_EASY_MAX, DIFFICULTY_HARD_MIN
from src.models.schemas import (
    KnowledgeAssessmentResult,
    ConceptAssessment,
    MasteryStatus,
    DifficultyLevel,
    DifficultyEstimate,
)


def _mastery_to_difficulty(mastery: float | None) -> DifficultyLevel:
    """Turns a raw mastery number into an easy/medium/hard label."""
    if mastery is None:
        return DifficultyLevel.EASY  # never assessed -> start safe
    if mastery < DIFFICULTY_EASY_MAX:
        return DifficultyLevel.EASY
    if mastery >= DIFFICULTY_HARD_MIN:
        return DifficultyLevel.HARD
    return DifficultyLevel.MEDIUM


def _find_first_gap(assessments: list[ConceptAssessment]) -> ConceptAssessment | None:
    """
    Walks the learning path IN ORDER (it's already topologically sorted from Phase 1 —
    earliest prerequisites first) and returns the first concept that isn't mastered yet.
    Returns None if everything up to and including the target is already mastered.
    """
    for assessment in assessments:
        if assessment.status != MasteryStatus.MASTERED:
            return assessment
    return None


def estimate_difficulty(result: KnowledgeAssessmentResult) -> DifficultyEstimate:
    gap = _find_first_gap(result.assessments)

    if gap is None:
        # Every prerequisite AND the target itself are already mastered.
        # Nothing to fix — teach the target at a challenging level to extend them.
        target_assessment = result.assessments[-1]
        return DifficultyEstimate(
            ready_to_learn_target=True,
            concept_to_teach_next=result.target_concept_id,
            recommended_difficulty=_mastery_to_difficulty(target_assessment.mastery),
            rationale=(
                f"All prerequisites and '{result.target_concept_id}' itself are already "
                f"mastered — teaching directly, at a challenging level."
            ),
        )

    if gap.concept_id == result.target_concept_id:
        # Every PREREQUISITE is mastered, only the target itself is new/unmastered.
        # This is the normal case: student is ready, just hasn't learned this specific thing yet.
        return DifficultyEstimate(
            ready_to_learn_target=True,
            concept_to_teach_next=result.target_concept_id,
            recommended_difficulty=_mastery_to_difficulty(gap.mastery),
            rationale=(
                f"All prerequisites for '{result.target_concept_id}' are mastered — "
                f"student is ready to learn it directly."
            ),
        )

    # A prerequisite BEFORE the target is not mastered — redirect there instead.
    return DifficultyEstimate(
        ready_to_learn_target=False,
        concept_to_teach_next=gap.concept_id,
        recommended_difficulty=_mastery_to_difficulty(gap.mastery),
        rationale=(
            f"Cannot teach '{result.target_concept_id}' yet — prerequisite "
            f"'{gap.concept_id}' is not mastered (status: {gap.status.value}). "
            f"Redirecting to teach '{gap.concept_id}' first."
        ),
    )