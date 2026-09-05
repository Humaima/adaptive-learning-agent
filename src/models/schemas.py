from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MasteryStatus(str, Enum):
    MASTERED = "mastered"          # ✓
    NOT_MASTERED = "not_mastered"  # ✗
    UNKNOWN = "unknown"             # ?


class Concept(BaseModel):
    id: str = Field(..., description="Unique slug, e.g. 'backpropagation'")
    name: str = Field(..., description="Human-readable name")
    domain: str = Field(default="", description="e.g. Math, CS, ML, Physics")
    description: str = Field(default="", description="Short explanation of the concept")


class MasteryRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    concept_id: str
    mastery: float = Field(ge=0.0, le=1.0)
    last_updated: datetime


class Interaction(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    concept_id: str
    interaction_type: str
    content: str
    correct: Optional[bool] = None
    timestamp: datetime


class StudentModel(BaseModel):
    student_id: str
    mastery: dict[str, float]      # concept_id -> mastery score
    history: list[Interaction] = []


class ConceptIdentification(BaseModel):
    target_concept_id: str = Field(
        ..., description="The id (from the provided list) of the concept the question is primarily about"
    )
    reasoning: str = Field(..., description="One sentence explaining why this concept was chosen")


class ConceptAssessment(BaseModel):
    concept_id: str
    status: MasteryStatus
    mastery: float | None = Field(
        default=None, description="Raw mastery score 0.0-1.0, or None if never assessed"
    )

class KnowledgeAssessmentResult(BaseModel):
    student_id: str
    original_question: str
    target_concept_id: str
    learning_path: list[str]                # ordered prerequisites + target, from ConceptGraph
    assessments: list[ConceptAssessment]     # status per concept in the learning path

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class DifficultyEstimate(BaseModel):
    ready_to_learn_target: bool = Field(
        ..., description="True if the student can go straight to the originally asked concept"
    )
    concept_to_teach_next: str = Field(
        ..., description="The concept id the Tutor should actually teach right now — "
                          "either a blocking prerequisite, or the original target if no gap exists"
    )
    recommended_difficulty: DifficultyLevel
    rationale: str = Field(..., description="Plain-language reason for this decision")


class TutorContentDraft(BaseModel):
    explanation: str = Field(..., description="Clear explanation of the concept, matched to the requested difficulty")
    key_points: list[str] = Field(..., description="3-5 short bullet-point takeaways")
    worked_example: str = Field(..., description="One concrete worked example illustrating the concept")
    transition_note: str = Field(
        default="",
        description="If this concept is being taught INSTEAD of what the student originally asked, "
                    "one sentence bridging the two (e.g. why this comes first). "
                    "Leave empty if this concept IS what the student asked about."
    )


class TutorResponse(BaseModel):
    concept_id: str
    concept_name: str
    difficulty: DifficultyLevel
    is_prerequisite_redirect: bool
    target_concept_id: str          # what the student originally asked about
    original_question: str
    explanation: str
    key_points: list[str]
    worked_example: str
    transition_note: str


class QuestionType(str, Enum):
    MCQ = "mcq"
    SHORT_ANSWER = "short_answer"


class QuizOption(BaseModel):
    label: str = Field(..., description="Option letter, e.g. 'A', 'B', 'C', 'D'")
    text: str = Field(..., description="The option's text")


class QuizQuestionDraft(BaseModel):
    question_type: QuestionType
    question_text: str
    options: list[QuizOption] = Field(
        default_factory=list,
        description="Exactly 4 options for MCQ (labels A-D). Leave empty for short_answer."
    )
    correct_answer: str = Field(
        ...,
        description="For MCQ: the correct option's label (e.g. 'B'), matching one of the options exactly. "
                    "For short_answer: a model/reference answer used for grading."
    )
    explanation: str = Field(..., description="Why this is the correct answer — shown to the student after grading")


class QuizDraft(BaseModel):
    questions: list[QuizQuestionDraft]


class QuizQuestion(BaseModel):
    question_id: str
    concept_id: str
    difficulty: DifficultyLevel
    question_type: QuestionType
    question_text: str
    options: list[QuizOption]
    correct_answer: str
    explanation: str


class QuizSet(BaseModel):
    concept_id: str
    difficulty: DifficultyLevel
    questions: list[QuizQuestion]


class ShortAnswerGradingDraft(BaseModel):
    correctness_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="0.0 = completely wrong, 1.0 = fully correct, values in between for partial credit"
    )
    feedback: str = Field(..., description="One or two sentences of feedback shown to the student")


class EvaluationResult(BaseModel):
    question_id: str
    concept_id: str
    question_type: QuestionType
    student_answer: str
    is_correct: bool
    correctness_score: float = Field(ge=0.0, le=1.0)
    feedback: str