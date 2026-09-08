from typing import TypedDict

from src.models.schemas import (
    KnowledgeAssessmentResult,
    DifficultyEstimate,
    TutorResponse,
    QuizSet,
    EvaluationResult,
    UpdateLoopResult,
)


class TutorGraphState(TypedDict, total=False):
    student_id: str
    original_question: str
    target_concept_id: str

    assessment: KnowledgeAssessmentResult
    difficulty_estimate: DifficultyEstimate
    tutor_response: TutorResponse
    quiz: QuizSet
    student_answers: dict[str, str]
    eval_results: list[EvaluationResult]
    update_result: UpdateLoopResult

    teaching_history: list[TutorResponse]   # every concept taught this session, in order
    iteration_count: int