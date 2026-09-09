from datetime import datetime, timedelta
from typing import cast

from sqlalchemy.orm import Session

from src.db.models import StudentDB, MasteryRecordDB, InteractionDB, NoteDB, FlashcardDB
from src.models.schemas import StudentModel, MasteryRecord, Interaction
from src.study_tools.spaced_repetition import compute_next_interval


def get_or_create_student(db: Session, student_id: str) -> StudentDB:
    student = db.query(StudentDB).filter_by(student_id=student_id).first()
    if student is None:
        student = StudentDB(student_id=student_id)
        db.add(student)
        db.commit()
        db.refresh(student)
    return student


def set_mastery(db: Session, student_id: str, concept_id: str, mastery: float) -> MasteryRecordDB:
    student = get_or_create_student(db, student_id)
    record = (
        db.query(MasteryRecordDB)
        .filter_by(student_pk=student.id, concept_id=concept_id)
        .first()
    )
    if record is None:
        record = MasteryRecordDB(student_pk=student.id, concept_id=concept_id, mastery=mastery)
        db.add(record)
    else:
        setattr(record, "mastery", mastery)
        setattr(record, "last_updated", datetime.utcnow())
    db.commit()
    db.refresh(record)
    return record


def get_mastery(db: Session, student_id: str, concept_id: str) -> float | None:
    """Returns None if the concept has never been assessed for this student —
    distinct from an actual mastery score of 0.0."""
    student = get_or_create_student(db, student_id)
    record = (
        db.query(MasteryRecordDB)
        .filter_by(student_pk=student.id, concept_id=concept_id)
        .first()
    )
    return cast(float, record.mastery) if record else None


def log_interaction(
    db: Session,
    student_id: str,
    concept_id: str,
    interaction_type: str,
    content: str,
    correct: bool | None = None,
) -> InteractionDB:
    student = get_or_create_student(db, student_id)
    interaction = InteractionDB(
        student_pk=student.id,
        concept_id=concept_id,
        interaction_type=interaction_type,
        content=content,
        correct=correct,
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


def get_student_model(db: Session, student_id: str) -> StudentModel:
    """Aggregates everything into the single object other agent nodes will consume."""
    student = get_or_create_student(db, student_id)

    mastery = {r.concept_id: r.mastery for r in student.mastery_records}
    history = [Interaction.model_validate(i) for i in student.interactions]

    return StudentModel(student_id=cast(str, student.student_id), mastery=mastery, history=history)


def get_student_by_username(db: Session, username: str) -> StudentDB | None:
    return db.query(StudentDB).filter_by(student_id=username).first()


def get_student_by_email(db: Session, email: str) -> StudentDB | None:
    return db.query(StudentDB).filter_by(email=email).first()


def create_student_with_password(db: Session, username: str, email: str, hashed_password: str) -> StudentDB:
    student = StudentDB(student_id=username, email=email, hashed_password=hashed_password)
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def create_note(db: Session, student_id: str, concept_id: str, title: str, content: str) -> NoteDB:
    student = get_or_create_student(db, student_id)
    note = NoteDB(student_pk=student.id, concept_id=concept_id, title=title, content=content)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def list_notes(db: Session, student_id: str) -> list[NoteDB]:
    student = get_or_create_student(db, student_id)
    return db.query(NoteDB).filter_by(student_pk=student.id).order_by(NoteDB.created_at.desc()).all()


def delete_note(db: Session, student_id: str, note_id: int) -> bool:
    student = get_or_create_student(db, student_id)
    note = db.query(NoteDB).filter_by(id=note_id, student_pk=student.id).first()
    if not note:
        return False
    db.delete(note)
    db.commit()
    return True


def create_flashcards(db: Session, student_id: str, concept_id: str, cards: list[tuple[str, str]]) -> list[FlashcardDB]:
    student = get_or_create_student(db, student_id)
    created = [FlashcardDB(student_pk=student.id, concept_id=concept_id, front=f, back=b) for f, b in cards]
    db.add_all(created)
    db.commit()
    for card in created:
        db.refresh(card)
    return created


def get_due_flashcards(db: Session, student_id: str) -> list[FlashcardDB]:
    student = get_or_create_student(db, student_id)
    return (
        db.query(FlashcardDB)
        .filter(FlashcardDB.student_pk == student.id, FlashcardDB.next_review_at <= datetime.utcnow())
        .all()
    )


def review_flashcard(db: Session, student_id: str, flashcard_id: int, knew_it: bool) -> FlashcardDB | None:
    student = get_or_create_student(db, student_id)
    card = db.query(FlashcardDB).filter_by(id=flashcard_id, student_pk=student.id).first()
    if not card:
        return None
    new_interval = compute_next_interval(cast(int, card.interval_days), knew_it)
    setattr(card, "interval_days", new_interval)
    setattr(card, "next_review_at", datetime.utcnow() + timedelta(days=new_interval))
    db.commit()
    db.refresh(card)
    return card

def get_quiz_history(db: Session, student_id: str) -> list[InteractionDB]:
    student = get_or_create_student(db, student_id)
    return (
        db.query(InteractionDB)
        .filter_by(student_pk=student.id, interaction_type="quiz_answer")
        .order_by(InteractionDB.timestamp.desc())
        .all()
    )