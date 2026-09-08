import pytest
from unittest.mock import patch
from langgraph.types import Command
from langchain_core.runnables import RunnableConfig
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.database import Base
from src.graph.concept_graph import ConceptGraph
from src.models.schemas import (
    Concept, KnowledgeAssessmentResult, ConceptAssessment, MasteryStatus,
    DifficultyEstimate, DifficultyLevel, TutorResponse, QuizSet, QuizQuestion,
    QuestionType, EvaluationResult, UpdateLoopResult,
)
from src.agents.tutor_graph import build_tutor_graph


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


def make_quiz(concept_id):
    return QuizSet(
        concept_id=concept_id,
        difficulty=DifficultyLevel.EASY,
        questions=[
            QuizQuestion(
                question_id="q1", concept_id=concept_id, difficulty=DifficultyLevel.EASY,
                question_type=QuestionType.MCQ, question_text="Q?",
                options=[], correct_answer="A", explanation="because",
            )
        ],
    )


def test_single_iteration_when_only_target_is_unmastered(db_session, sample_graph):
    """calculus already mastered -> should quiz on backpropagation once, then finish."""

    assessment = KnowledgeAssessmentResult(
        student_id="student_001", original_question="Explain backpropagation.",
        target_concept_id="backpropagation", learning_path=["calculus", "backpropagation"],
        assessments=[
            ConceptAssessment(concept_id="calculus", status=MasteryStatus.MASTERED, mastery=0.9),
            ConceptAssessment(concept_id="backpropagation", status=MasteryStatus.UNKNOWN, mastery=None),
        ],
    )
    mastered_assessment = assessment.model_copy(update={
        "assessments": [
            ConceptAssessment(concept_id="calculus", status=MasteryStatus.MASTERED, mastery=0.9),
            ConceptAssessment(concept_id="backpropagation", status=MasteryStatus.MASTERED, mastery=0.8),
        ]
    })

    with patch("src.agents.graph_nodes.assess_knowledge", return_value=assessment), \
         patch("src.agents.graph_nodes.estimate_difficulty", return_value=DifficultyEstimate(
             ready_to_learn_target=True, concept_to_teach_next="backpropagation",
             recommended_difficulty=DifficultyLevel.EASY, rationale="ready")), \
         patch("src.agents.graph_nodes.generate_tutoring_content", return_value=TutorResponse(
             concept_id="backpropagation", concept_name="Backpropagation", difficulty=DifficultyLevel.EASY,
             is_prerequisite_redirect=False, target_concept_id="backpropagation",
             original_question="Explain backpropagation.", explanation="...", key_points=["a"],
             worked_example="...", transition_note="")), \
         patch("src.agents.graph_nodes.generate_quiz", return_value=make_quiz("backpropagation")), \
         patch("src.agents.graph_nodes.evaluate_quiz", return_value=[EvaluationResult(
             question_id="q1", concept_id="backpropagation", question_type=QuestionType.MCQ,
             student_answer="A", is_correct=True, correctness_score=1.0, feedback="Correct!")]), \
         patch("src.agents.graph_nodes.run_update_loop", return_value=UpdateLoopResult(
             student_id="student_001", original_question="Explain backpropagation.",
             target_concept_id="backpropagation", mastery_updates=[],
             ready_to_learn_target_now=True, updated_assessment=mastered_assessment)):

        graph = build_tutor_graph(db_session, sample_graph)
        config: RunnableConfig = {"configurable": {"thread_id": "test-thread-1"}}

        result = graph.invoke(
            {"student_id": "student_001", "original_question": "Explain backpropagation."}, config=config
        )
        assert "__interrupt__" in result  # paused for the quiz

        result = graph.invoke(Command(resume={"q1": "A"}), config=config)
        assert "__interrupt__" not in result  # finished after one round
        assert len(result["teaching_history"]) == 1
        assert result["teaching_history"][0].concept_id == "backpropagation"


def test_safety_cap_stops_infinite_loop(db_session, sample_graph):
    """If mastery never crosses the threshold, MAX_LOOP_ITERATIONS should force a stop."""

    stuck_assessment = KnowledgeAssessmentResult(
        student_id="student_001", original_question="Explain backpropagation.",
        target_concept_id="backpropagation", learning_path=["calculus", "backpropagation"],
        assessments=[
            ConceptAssessment(concept_id="calculus", status=MasteryStatus.NOT_MASTERED, mastery=0.1),
            ConceptAssessment(concept_id="backpropagation", status=MasteryStatus.UNKNOWN, mastery=None),
        ],
    )

    with patch("src.agents.graph_nodes.assess_knowledge", return_value=stuck_assessment), \
         patch("src.agents.graph_nodes.estimate_difficulty", return_value=DifficultyEstimate(
             ready_to_learn_target=False, concept_to_teach_next="calculus",
             recommended_difficulty=DifficultyLevel.EASY, rationale="still stuck")), \
         patch("src.agents.graph_nodes.generate_tutoring_content", return_value=TutorResponse(
             concept_id="calculus", concept_name="Calculus", difficulty=DifficultyLevel.EASY,
             is_prerequisite_redirect=True, target_concept_id="backpropagation",
             original_question="Explain backpropagation.", explanation="...", key_points=["a"],
             worked_example="...", transition_note="first things first")), \
         patch("src.agents.graph_nodes.generate_quiz", return_value=make_quiz("calculus")), \
         patch("src.agents.graph_nodes.evaluate_quiz", return_value=[EvaluationResult(
             question_id="q1", concept_id="calculus", question_type=QuestionType.MCQ,
             student_answer="B", is_correct=False, correctness_score=0.0, feedback="Not quite.")]), \
         patch("src.agents.graph_nodes.run_update_loop", return_value=UpdateLoopResult(
             student_id="student_001", original_question="Explain backpropagation.",
             target_concept_id="backpropagation", mastery_updates=[],
             ready_to_learn_target_now=False, updated_assessment=stuck_assessment)):  # never improves

        graph = build_tutor_graph(db_session, sample_graph)
        config: RunnableConfig = {"configurable": {"thread_id": "test-thread-2"}}

        result = graph.invoke(
            {"student_id": "student_001", "original_question": "Explain backpropagation."}, config=config
        )

        loop_count = 0
        while "__interrupt__" in result and loop_count < 10:  # outer safety net for the test itself
            result = graph.invoke(Command(resume={"q1": "B"}), config=config)
            loop_count += 1

        assert "__interrupt__" not in result  # graph gave up via MAX_LOOP_ITERATIONS, didn't hang
        assert result["iteration_count"] == 5  # matches MAX_LOOP_ITERATIONS from config