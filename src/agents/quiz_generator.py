import uuid

from src.agents.llm_client import get_groq_llm, with_structured_output_retry
from src.agents.tutor import DIFFICULTY_INSTRUCTIONS  # reuse the same difficulty phrasing as the Tutor
from src.graph.concept_graph import ConceptGraph
from src.config import NUM_QUIZ_QUESTIONS
from src.models.schemas import (
    DifficultyLevel,
    QuestionType,
    QuizDraft,
    QuizQuestion,
    QuizSet,
)
from src.models.schemas import QuizQuestionDraft

QUIZ_PROMPT_TEMPLATE = """
You are writing a short quiz to check whether a student understood a concept they were just taught.

Concept: {concept_name}
Description: {concept_description}

Difficulty instructions (match the question difficulty to this, not just the topic): {difficulty_instruction}

Write exactly {num_questions} questions testing real understanding (not just recall of definitions).
Use a mix of question types: at least one "mcq" and at least one "short_answer" if {num_questions} >= 2.

For every "mcq" question:
- Provide exactly 4 options labeled "A", "B", "C", "D".
- correct_answer must be exactly one of those labels (e.g. "B").
- Only one option should be correct; the other 3 should be plausible but wrong.

For every "short_answer" question:
- Leave options empty.
- correct_answer should be a concise model answer usable as a grading reference.

Every question needs an explanation field describing why the correct_answer is right.
"""


def _validate_and_fix(draft: QuizDraft) -> list[QuizQuestionDraft]:
    """
    Filters out any MCQ question where the LLM's correct_answer label doesn't
    actually match one of the provided options — this occasionally happens
    (e.g. correct_answer='E' when only A-D exist). Better to drop a bad
    question than serve the student an unscorable one.
    """
    valid_questions = []
    for q in draft.questions:
        if q.question_type == QuestionType.MCQ:
            option_labels = {opt.label for opt in q.options}
            if len(q.options) != 4 or q.correct_answer not in option_labels:
                continue  # skip malformed MCQ
        valid_questions.append(q)
    return valid_questions


def generate_quiz(
    cg: ConceptGraph,
    concept_id: str,
    difficulty: DifficultyLevel,
    num_questions: int = NUM_QUIZ_QUESTIONS,
) -> QuizSet:
    concept_info = cg.get_concept_info(concept_id)

    prompt = QUIZ_PROMPT_TEMPLATE.format(
        concept_name=concept_info["name"],
        concept_description=concept_info["description"],
        difficulty_instruction=DIFFICULTY_INSTRUCTIONS[difficulty],
        num_questions=num_questions,
    )

    llm = get_groq_llm(reasoning_effort="medium", temperature=0.5)
    result = with_structured_output_retry(llm, QuizDraft, prompt)
    parsed_result = result["parsed"] if isinstance(result, dict) else getattr(result, "parsed", result)
    if isinstance(parsed_result, QuizDraft):
        draft = parsed_result
    elif isinstance(parsed_result, dict):
        draft = QuizDraft.model_validate(parsed_result)
    else:
        raise TypeError("Structured quiz output is not a QuizDraft")

    valid_drafts = _validate_and_fix(draft)

    questions = [
        QuizQuestion(
            question_id=str(uuid.uuid4())[:8],
            concept_id=concept_id,
            difficulty=difficulty,
            question_type=q.question_type,
            question_text=q.question_text,
            options=q.options,
            correct_answer=q.correct_answer,
            explanation=q.explanation,
        )
        for q in valid_drafts
    ]

    return QuizSet(concept_id=concept_id, difficulty=difficulty, questions=questions)