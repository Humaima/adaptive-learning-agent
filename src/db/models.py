from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from src.db.database import Base



class StudentDB(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, unique=True, index=True, nullable=False)  # == username
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)  # nullable so old test fixtures without auth still work
    created_at = Column(DateTime, default=datetime.utcnow)

    mastery_records = relationship("MasteryRecordDB", back_populates="student", cascade="all, delete-orphan")
    interactions = relationship("InteractionDB", back_populates="student", cascade="all, delete-orphan")
    notes = relationship("NoteDB", back_populates="student", cascade="all, delete-orphan")


class MasteryRecordDB(Base):
    """One row per (student, concept) — current mastery estimate."""
    __tablename__ = "mastery_records"

    id = Column(Integer, primary_key=True, index=True)
    student_pk = Column(Integer, ForeignKey("students.id"), nullable=False)
    concept_id = Column(String, nullable=False, index=True)
    mastery = Column(Float, default=0.0)   # 0.0 - 1.0
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("StudentDB", back_populates="mastery_records")


class InteractionDB(Base):
    """One row per question/quiz-answer event — full audit trail."""
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    student_pk = Column(Integer, ForeignKey("students.id"), nullable=False)
    concept_id = Column(String, nullable=False, index=True)
    interaction_type = Column(String, nullable=False)  # "question" | "quiz_answer"
    content = Column(String, nullable=False)
    correct = Column(Boolean, nullable=True)  # null for plain questions, set for quiz answers
    timestamp = Column(DateTime, default=datetime.utcnow)

    student = relationship("StudentDB", back_populates="interactions")

class NoteDB(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    student_pk = Column(Integer, ForeignKey("students.id"), nullable=False)
    concept_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("StudentDB", back_populates="notes")