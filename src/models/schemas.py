from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


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