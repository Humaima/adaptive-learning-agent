from fastapi import APIRouter, Depends, HTTPException

from src.db.database import get_db
from src.db.repository import create_note, list_notes, delete_note
from src.auth.dependencies import get_current_student_id
from src.api.schemas import NoteCreate, NoteOut

router = APIRouter(tags=["study-tools"])


@router.post("/notes", response_model=NoteOut)
def add_note(body: NoteCreate, student_id: str = Depends(get_current_student_id), db=Depends(get_db)):
    note = create_note(db, student_id, body.concept_id, body.title, body.content)
    return NoteOut.model_validate(note)


@router.get("/notes", response_model=list[NoteOut])
def get_notes(student_id: str = Depends(get_current_student_id), db=Depends(get_db)):
    notes = list_notes(db, student_id)
    return [NoteOut.model_validate(n) for n in notes]


@router.delete("/notes/{note_id}")
def remove_note(note_id: int, student_id: str = Depends(get_current_student_id), db=Depends(get_db)):
    if not delete_note(db, student_id, note_id):
        raise HTTPException(status_code=404, detail="Note not found")
    return {"deleted": True}