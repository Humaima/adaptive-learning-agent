from src.agents.llm_client import get_groq_llm, with_structured_output_retry
from src.config import SHORT_ANSWER_CORRECT_THRESHOLD
from src.models.schemas import (
    QuizQuestion,
    QuestionType,
    ShortAnswerGradingDraft,
    EvaluationResult,
)

SHORT_ANSWER_GRADING_PROMPT_TEMPLATE = """
You are grading a student's answer to a quiz question.

Question: {question_text}

Reference/model answer: {model_answer}
Why the reference answer is correct: {explanation}

Student's answer: {student_answer}

Judge the student's answer on MEANING, not exact wording — a correct idea phrased
differently from the reference answer should still score highly.

Give a correctness_score from 0.0 (completely wrong or missing the point) to
1.0 (fully correct, even if worded differently). Partial credit (e.g. 0.5) is fine
for an answer that's on the right track but incomplete or has a minor error.

Give brief, encouraging feedback explaining the score.
"""


def _evaluate_mcq(question: QuizQuestion, student_answer: str) -> EvaluationResult:
    """Rule-based — no LLM call needed, exact label match."""
    normalized_answer = student_answer.strip().upper()
    is_correct = normalized_answer == question.correct_answer.strip().upper()

    feedback = (
        "Correct!" if is_correct
        else f"Not quite — the correct answer was {question.correct_answer}. {question.explanation}"
    )

    return EvaluationResult(
        question_id=question.question_id,
        concept_id=question.concept_id,
        question_type=question.question_type,
        student_answer=student_answer,
        is_correct=is_correct,
        correctness_score=1.0 if is_correct else 0.0,
        feedback=feedback,
    )


def _evaluate_short_answer(question: QuizQuestion, student_answer: str) -> EvaluationResult:
    """LLM-graded — judges meaning, not exact wording."""
    prompt = SHORT_ANSWER_GRADING_PROMPT_TEMPLATE.format(
        question_text=question.question_text,
        model_answer=question.correct_answer,
        explanation=question.explanation,
        student_answer=student_answer,
    )

    llm = get_groq_llm(reasoning_effort="medium", temperature=0.0)
    result = with_structured_output_retry(llm, ShortAnswerGradingDraft, prompt)
    draft = result.get("parsed") if isinstance(result, dict) else result
    if not isinstance(draft, ShortAnswerGradingDraft):
        raise TypeError(f"Expected ShortAnswerGradingDraft, got {type(draft).__name__}")

    return EvaluationResult(
        question_id=question.question_id,
        concept_id=question.concept_id,
        question_type=question.question_type,
        student_answer=student_answer,
        is_correct=draft.correctness_score >= SHORT_ANSWER_CORRECT_THRESHOLD,
        correctness_score=draft.correctness_score,
        feedback=draft.feedback,
    )


def evaluate_answer(question: QuizQuestion, student_answer: str) -> EvaluationResult:
    """Single entry point — routes to the right grading strategy based on question type."""
    if question.question_type == QuestionType.MCQ:
        return _evaluate_mcq(question, student_answer)
    return _evaluate_short_answer(question, student_answer)


def evaluate_quiz(
    questions: list[QuizQuestion], student_answers: dict[str, str]
) -> list[EvaluationResult]:
    """
    student_answers maps question_id -> the student's raw answer text.
    Any question without a submitted answer is skipped (not scored as wrong) —
    the caller can decide separately how to handle unanswered questions.
    """
    results = []
    for question in questions:
        answer = student_answers.get(question.question_id)
        if answer is None:
            continue
        results.append(evaluate_answer(question, answer))
    return results