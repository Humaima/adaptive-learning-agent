from unittest.mock import patch
from src.models.schemas import (
    QuizQuestion, QuizOption, QuestionType, DifficultyLevel, ShortAnswerGradingDraft,
)
from src.agents import evaluator


def make_mcq_question(correct_answer="B"):
    return QuizQuestion(
        question_id="q1",
        concept_id="calculus",
        difficulty=DifficultyLevel.EASY,
        question_type=QuestionType.MCQ,
        question_text="What is a derivative?",
        options=[QuizOption(label=l, text=f"Option {l}") for l in ["A", "B", "C", "D"]],
        correct_answer=correct_answer,
        explanation="Because B describes rate of change.",
    )


def make_short_answer_question():
    return QuizQuestion(
        question_id="q2",
        concept_id="calculus",
        difficulty=DifficultyLevel.EASY,
        question_type=QuestionType.SHORT_ANSWER,
        question_text="Explain the chain rule in one sentence.",
        options=[],
        correct_answer="It lets you differentiate composed functions by multiplying derivatives.",
        explanation="This is the standard definition.",
    )


def fake_grading_result(score, feedback="Good job."):
    return {"parsed": ShortAnswerGradingDraft(correctness_score=score, feedback=feedback)}


# --- MCQ tests: no mocking needed, pure rule-based logic ---

def test_mcq_correct_answer():
    question = make_mcq_question(correct_answer="B")
    result = evaluator.evaluate_answer(question, "B")
    assert result.is_correct is True
    assert result.correctness_score == 1.0


def test_mcq_incorrect_answer():
    question = make_mcq_question(correct_answer="B")
    result = evaluator.evaluate_answer(question, "C")
    assert result.is_correct is False
    assert result.correctness_score == 0.0


def test_mcq_answer_is_case_and_whitespace_insensitive():
    question = make_mcq_question(correct_answer="B")
    result = evaluator.evaluate_answer(question, "  b ")
    assert result.is_correct is True


# --- Short-answer tests: LLM call mocked ---

def test_short_answer_above_threshold_counts_correct():
    question = make_short_answer_question()
    with patch("src.agents.evaluator.with_structured_output_retry",
               return_value=fake_grading_result(0.9)):
        result = evaluator.evaluate_answer(question, "It multiplies derivatives of nested functions.")
    assert result.is_correct is True
    assert result.correctness_score == 0.9


def test_short_answer_below_threshold_counts_incorrect():
    question = make_short_answer_question()
    with patch("src.agents.evaluator.with_structured_output_retry",
               return_value=fake_grading_result(0.3)):
        result = evaluator.evaluate_answer(question, "Not sure, something about functions.")
    assert result.is_correct is False
    assert result.correctness_score == 0.3


# --- evaluate_quiz batch behavior ---

def test_evaluate_quiz_skips_unanswered_questions():
    mcq = make_mcq_question(correct_answer="B")
    sa = make_short_answer_question()
    # Only answer the MCQ, leave the short-answer question unanswered
    results = evaluator.evaluate_quiz([mcq, sa], {"q1": "B"})
    assert len(results) == 1
    assert results[0].question_id == "q1"