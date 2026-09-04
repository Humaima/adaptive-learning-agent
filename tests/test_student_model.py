import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.database import Base
from src.db import repository as repo


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()
    yield session
    session.close()


def test_get_or_create_student_is_idempotent(db_session):
    s1 = repo.get_or_create_student(db_session, "student_001")
    s2 = repo.get_or_create_student(db_session, "student_001")
    assert s1.id == s2.id


def test_set_and_get_mastery(db_session):
    repo.set_mastery(db_session, "student_001", "calculus", 0.75)
    assert repo.get_mastery(db_session, "student_001", "calculus") == 0.75


def test_unknown_concept_returns_none(db_session):
    """None (not 0.0) — 'never assessed' must stay distinguishable from a real 0.0 score,
    since mastery_to_status() maps None -> UNKNOWN vs a float -> MASTERED/NOT_MASTERED."""
    assert repo.get_mastery(db_session, "student_001", "never_seen") is None


def test_log_interaction_appears_in_history(db_session):
    repo.log_interaction(db_session, "student_001", "backpropagation", "question", "Explain it.")
    model = repo.get_student_model(db_session, "student_001")
    assert len(model.history) == 1
    assert model.history[0].concept_id == "backpropagation"


def test_student_model_aggregates_mastery_and_history(db_session):
    repo.set_mastery(db_session, "student_001", "linear_algebra", 0.9)
    repo.log_interaction(db_session, "student_001", "linear_algebra", "quiz_answer", "Answer text", correct=True)
    model = repo.get_student_model(db_session, "student_001")
    assert model.mastery["linear_algebra"] == 0.9
    assert model.history[0].correct is True