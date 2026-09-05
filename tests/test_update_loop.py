import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.database import Base
from src.db.repository import set_mastery
from src.graph.concept_graph import ConceptGraph
from src.models.schemas import Concept, EvaluationResult, QuestionType
from src.agents.update_loop import run_update_loop


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture
def sample_graph():
    cg = ConceptGraph()
    cg.add_concept(Concept(id="calculus", name="Calculus", domain="Math", description="Rates of change."))
    cg.add_concept(Concept(id="backpropagation", name="Backpropagation", domain="ML", description="Gradient descent."))
    cg.add_prerequisite("calculus", "backpropagation")
    return cg


def test_update_loop_flips_readiness_after_enough_correct_answers(db_session, sample_graph):
    set_mastery(db_session, "student_001", "calculus", 0.2)  # starts weak

    # Simulate 3 correct answers in one quiz pass
    eval_results = [
        EvaluationResult(
            question_id=f"q{i}", concept_id="calculus", question_type=QuestionType.MCQ,
            student_answer="B", is_correct=True, correctness_score=1.0, feedback="Correct!",
        )
        for i in range(3)
    ]

    result = run_update_loop(
        db_session, "student_001", "Explain backpropagation.", "backpropagation", sample_graph, eval_results
    )

    assert result.ready_to_learn_target_now is True  # calculus mastery cleared threshold
    calculus_update = next(u for u in result.mastery_updates if u.concept_id == "calculus")
    assert calculus_update.new_mastery > calculus_update.previous_mastery


def test_update_loop_stays_not_ready_with_poor_performance(db_session, sample_graph):
    set_mastery(db_session, "student_001", "calculus", 0.2)

    eval_results = [
        EvaluationResult(
            question_id="q1", concept_id="calculus", question_type=QuestionType.MCQ,
            student_answer="A", is_correct=False, correctness_score=0.0, feedback="Not quite.",
        )
    ]

    result = run_update_loop(
        db_session, "student_001", "Explain backpropagation.", "backpropagation", sample_graph, eval_results
    )

    assert result.ready_to_learn_target_now is False  # calculus mastery dropped further, not up