from unittest.mock import patch
from src.graph.concept_graph import ConceptGraph
from src.models.schemas import (
    Concept, QuizDraft, QuizQuestionDraft, QuizOption, QuestionType, DifficultyLevel,
)
from src.agents import quiz_generator


def make_graph():
    cg = ConceptGraph()
    cg.add_concept(Concept(id="calculus", name="Calculus", domain="Math", description="Derivatives and rates of change."))
    return cg


def fake_quiz_result(questions):
    return {"parsed": QuizDraft(questions=questions)}


def test_generate_quiz_assigns_ids_and_metadata():
    cg = make_graph()
    draft_questions = [
        QuizQuestionDraft(
            question_type=QuestionType.MCQ,
            question_text="What is a derivative?",
            options=[QuizOption(label=l, text=f"Option {l}") for l in ["A", "B", "C", "D"]],
            correct_answer="B",
            explanation="Because...",
        ),
        QuizQuestionDraft(
            question_type=QuestionType.SHORT_ANSWER,
            question_text="Explain the chain rule in one sentence.",
            options=[],
            correct_answer="It lets you differentiate composed functions.",
            explanation="Because...",
        ),
    ]

    with patch("src.agents.quiz_generator.with_structured_output_retry",
               return_value=fake_quiz_result(draft_questions)):
        quiz_set = quiz_generator.generate_quiz(cg, "calculus", DifficultyLevel.EASY, num_questions=2)

    assert len(quiz_set.questions) == 2
    assert quiz_set.concept_id == "calculus"
    assert quiz_set.difficulty == DifficultyLevel.EASY
    assert all(q.question_id for q in quiz_set.questions)  # every question got a real id
    assert len({q.question_id for q in quiz_set.questions}) == 2  # ids are unique


def test_malformed_mcq_is_filtered_out():
    cg = make_graph()
    draft_questions = [
        QuizQuestionDraft(
            question_type=QuestionType.MCQ,
            question_text="Broken question",
            options=[QuizOption(label="A", text="Only one option")],  # only 1 option, invalid
            correct_answer="Z",  # doesn't match any option label either
            explanation="n/a",
        ),
        QuizQuestionDraft(
            question_type=QuestionType.SHORT_ANSWER,
            question_text="A valid short answer question",
            options=[],
            correct_answer="Some answer",
            explanation="n/a",
        ),
    ]

    with patch("src.agents.quiz_generator.with_structured_output_retry",
               return_value=fake_quiz_result(draft_questions)):
        quiz_set = quiz_generator.generate_quiz(cg, "calculus", DifficultyLevel.MEDIUM, num_questions=2)

    # The malformed MCQ should have been dropped, only the valid short-answer remains
    assert len(quiz_set.questions) == 1
    assert quiz_set.questions[0].question_type == QuestionType.SHORT_ANSWER


def test_valid_mcq_is_kept():
    cg = make_graph()
    draft_questions = [
        QuizQuestionDraft(
            question_type=QuestionType.MCQ,
            question_text="Valid question",
            options=[QuizOption(label=l, text=f"Option {l}") for l in ["A", "B", "C", "D"]],
            correct_answer="C",
            explanation="n/a",
        ),
    ]

    with patch("src.agents.quiz_generator.with_structured_output_retry",
               return_value=fake_quiz_result(draft_questions)):
        quiz_set = quiz_generator.generate_quiz(cg, "calculus", DifficultyLevel.HARD, num_questions=1)

    assert len(quiz_set.questions) == 1
    assert quiz_set.questions[0].correct_answer == "C"