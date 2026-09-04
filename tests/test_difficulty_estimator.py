from src.models.schemas import KnowledgeAssessmentResult, ConceptAssessment, MasteryStatus, DifficultyLevel
from src.agents.difficulty_estimator import estimate_difficulty


def make_result(assessments_data: list[tuple[str, MasteryStatus, float | None]], target: str):
    assessments = [
        ConceptAssessment(concept_id=cid, status=status, mastery=mastery)
        for cid, status, mastery in assessments_data
    ]
    return KnowledgeAssessmentResult(
        student_id="student_001",
        original_question="test question",
        target_concept_id=target,
        learning_path=[a.concept_id for a in assessments],
        assessments=assessments,
    )


def test_redirects_to_earliest_gap():
    result = make_result(
        [
            ("linear_algebra", MasteryStatus.MASTERED, 0.9),
            ("calculus", MasteryStatus.NOT_MASTERED, 0.2),
            ("neural_networks", MasteryStatus.UNKNOWN, None),
            ("backpropagation", MasteryStatus.UNKNOWN, None),
        ],
        target="backpropagation",
    )
    estimate = estimate_difficulty(result)
    assert estimate.ready_to_learn_target is False
    assert estimate.concept_to_teach_next == "calculus"
    assert estimate.recommended_difficulty == DifficultyLevel.EASY


def test_ready_when_only_target_is_new():
    result = make_result(
        [
            ("linear_algebra", MasteryStatus.MASTERED, 0.9),
            ("calculus", MasteryStatus.MASTERED, 0.8),
            ("backpropagation", MasteryStatus.UNKNOWN, None),
        ],
        target="backpropagation",
    )
    estimate = estimate_difficulty(result)
    assert estimate.ready_to_learn_target is True
    assert estimate.concept_to_teach_next == "backpropagation"
    assert estimate.recommended_difficulty == DifficultyLevel.EASY  # unknown -> safe default


def test_challenging_when_everything_mastered():
    result = make_result(
        [
            ("linear_algebra", MasteryStatus.MASTERED, 0.9),
            ("backpropagation", MasteryStatus.MASTERED, 0.85),
        ],
        target="backpropagation",
    )
    estimate = estimate_difficulty(result)
    assert estimate.ready_to_learn_target is True
    assert estimate.recommended_difficulty == DifficultyLevel.HARD


def test_medium_difficulty_band():
    result = make_result(
        [("some_concept", MasteryStatus.NOT_MASTERED, 0.5)],
        target="some_concept",
    )
    estimate = estimate_difficulty(result)
    assert estimate.recommended_difficulty == DifficultyLevel.MEDIUM