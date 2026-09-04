from enum import Enum
from pydantic import BaseModel, Field


class MasteryStatus(str, Enum):
    MASTERED = "mastered"        # ✓
    NOT_MASTERED = "not_mastered"  # ✗
    UNKNOWN = "unknown"           # ?


class Concept(BaseModel):
    id: str = Field(..., description="Unique slug, e.g. 'backpropagation'")
    name: str = Field(..., description="Human-readable name, e.g. 'Backpropagation'")
    description: str = Field(default="", description="Short explanation of the concept")


class ConceptAssessment(BaseModel):
    concept_id: str
    status: MasteryStatus