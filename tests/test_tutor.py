from unittest.mock import patch
from src.graph.concept_graph import ConceptGraph
from src.models.schemas import (
    Concept, KnowledgeAssessmentResult, ConceptAssessment, MasteryStatus,
    DifficultyEstimate, DifficultyLevel, TutorContentDraft,
)
from src.agents import tutor


def make_graph():
    cg = ConceptGraph()
    cg.add_concept(Concept(id="calculus", name="Calculus", domain="Math", description="Derivatives and rates of change."))
    cg.add_concept(Concept(id="backpropagation", name="Backpropagation", domain="ML", description="Gradient-based weight updates."))
    cg.add_prerequisite("calculus", "backpropagation")
    return cg


def make_assessment(target="backpropagation"):
    return KnowledgeAssessmentResult(
        student_id="student_001",
        original_question="Explain backpropagation.",
        target_concept_id=target,
        learning_path=["calculus", "backpropagation"],
        assessments=[
            ConceptAssessment(concept_id="calculus", status=MasteryStatus.NOT_MASTERED, mastery=0.2),
            ConceptAssessment(concept_id="backpropagation", status=MasteryStatus.UNKNOWN, mastery=None),
        ],
    )


def fake_llm_result(transition_note=""):
    return {
        "parsed": TutorContentDraft(
            explanation="A simple explanation.",
            key_points=["Point 1", "Point 2", "Point 3"],
            worked_example="Example: ...",
            transition_note=transition_note,
        )
    }


def test_redirect_case_produces_transition_note_and_correct_concept():
    cg = make_graph()
    assessment_result = make_assessment()
    difficulty_estimate = DifficultyEstimate(
        ready_to_learn_target=False,
        concept_to_teach_next="calculus",
        recommended_difficulty=DifficultyLevel.EASY,
        rationale="calculus not mastered",
    )

    with patch("src.agents.tutor.with_structured_output_retry",
               return_value=fake_llm_result("Let's cover calculus first since backpropagation needs it.")):
        response = tutor.generate_tutoring_content(cg, assessment_result, difficulty_estimate)

    assert response.concept_id == "calculus"
    assert response.target_concept_id == "backpropagation"
    assert response.is_prerequisite_redirect is True
    assert response.transition_note != ""
    assert response.difficulty == DifficultyLevel.EASY


def test_direct_case_has_no_redirect():
    cg = make_graph()
    assessment_result = make_assessment()
    difficulty_estimate = DifficultyEstimate(
        ready_to_learn_target=True,
        concept_to_teach_next="backpropagation",
        recommended_difficulty=DifficultyLevel.MEDIUM,
        rationale="all prerequisites mastered",
    )

    with patch("src.agents.tutor.with_structured_output_retry", return_value=fake_llm_result("")):
        response = tutor.generate_tutoring_content(cg, assessment_result, difficulty_estimate)

    assert response.concept_id == "backpropagation"
    assert response.is_prerequisite_redirect is False
    assert response.transition_note == ""


def test_prompt_includes_difficulty_instruction():
    cg = make_graph()
    prompt = tutor._build_prompt(cg, "calculus", DifficultyLevel.EASY, is_redirect=False, target_concept_id="calculus")
    assert "simple everyday language" in prompt
    assert "Calculus" in prompt