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


class KnowledgeAssessmentResult(BaseModel):
    student_id: str
    original_question: str
    target_concept_id: str
    learning_path: list[str]                # ordered prerequisites + target, from ConceptGraph
    assessments: list[ConceptAssessment]     # status per concept in the learning path