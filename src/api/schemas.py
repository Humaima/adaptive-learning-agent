from pydantic import BaseModel, ConfigDict

from datetime import datetime

class AskRequest(BaseModel):
    question: str

class AnswerRequest(BaseModel):
    answers: dict[str, str]  # question_id -> answer text/label


class QuizOptionOut(BaseModel):
    label: str
    text: str


class QuizQuestionOut(BaseModel):
    question_id: str
    question_type: str
    question_text: str
    options: list[QuizOptionOut]


class QuizOut(BaseModel):
    concept_id: str
    difficulty: str
    questions: list[QuizQuestionOut]


class TutoringStepOut(BaseModel):
    concept_id: str
    concept_name: str
    difficulty: str
    is_prerequisite_redirect: bool
    explanation: str
    key_points: list[str]
    worked_example: str
    transition_note: str


class TutorTurnResponse(BaseModel):
    status: str                      # "awaiting_answers" | "done"
    quiz: QuizOut | None = None
    latest_teaching: TutoringStepOut | None = None
    teaching_history: list[TutoringStepOut] = []


class MasteryEntry(BaseModel):
    concept_id: str
    concept_name: str
    domain: str
    mastery: float | None


class StudentMasteryResponse(BaseModel):
    student_id: str
    mastery: list[MasteryEntry]


class ConceptOut(BaseModel):
    id: str
    name: str
    domain: str
    description: str

class LearningPathStep(BaseModel):
    concept_id: str
    concept_name: str
    domain: str
    estimated_minutes: int
    done: bool


class NoteCreate(BaseModel):
    concept_id: str
    title: str
    content: str

class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    concept_id: str
    title: str
    content: str
    created_at: datetime