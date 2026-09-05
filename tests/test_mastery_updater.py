import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.database import Base
from src.models.schemas import EvaluationResult, QuestionType
from src.agents import mastery_updater


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def test_compute_new_mastery_with_no_prior_uses_neutral_prior():
    # previous=None -> base is 0.5; evidence=1.0 -> moves 30% of the way from 0.5 to 1.0
    new_mastery = mastery_updater.compute_new_mastery(None, 1.0)
    assert new_mastery == pytest.approx(0.65, abs=0.01)


def test_compute_new_mastery_moves_toward_evidence():
    new_mastery = mastery_updater.compute_new_mastery(0.2, 1.0)
    assert new_mastery == pytest.approx(0.44, abs=0.01)


def test_compute_new_mastery_clamps_to_valid_range():
    assert mastery_updater.compute_new_mastery(0.95, 1.0) <= 1.0
    assert mastery_updater.compute_new_mastery(0.05, 0.0) >= 0.0


def test_apply_evaluation_results_updates_db_and_logs_interaction(db_session):
    results = [
        EvaluationResult(
            question_id="q1", concept_id="calculus", question_type=QuestionType.MCQ,
            student_answer="B", is_correct=True, correctness_score=1.0, feedback="Correct!",
        )
    ]
    updates = mastery_updater.apply_evaluation_results(db_session, "student_001", results)

    assert len(updates) == 1
    assert updates[0].concept_id == "calculus"
    assert updates[0].previous_mastery is None
    assert updates[0].new_mastery == pytest.approx(0.65, abs=0.01)

    from src.db.repository import get_student_model
    model = get_student_model(db_session, "student_001")
    assert model.mastery["calculus"] == pytest.approx(0.65, abs=0.01)
    assert len(model.history) == 1
    assert model.history[0].correct is True


def test_sequential_updates_compound(db_session):
    """Three correct answers in a row on the same concept should push mastery up each time."""
    for i in range(3):
        result = EvaluationResult(
            question_id=f"q{i}", concept_id="calculus", question_type=QuestionType.MCQ,
            student_answer="B", is_correct=True, correctness_score=1.0, feedback="Correct!",
        )
        mastery_updater.apply_evaluation_results(db_session, "student_001", [result])

    from src.db.repository import get_mastery
    final_mastery = get_mastery(db_session, "student_001", "calculus")
    assert final_mastery is not None
    assert final_mastery > 0.7  # three consecutive correct answers should clear the mastery threshold