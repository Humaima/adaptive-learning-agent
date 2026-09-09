from fastapi import APIRouter, Depends, HTTPException

from src.db.database import get_db
from src.db.repository import (
    create_note, list_notes, delete_note,
    create_flashcards, get_due_flashcards, review_flashcard,
)
from src.auth.dependencies import get_current_student_id
from src.graph.concept_graph import ConceptGraph
from src.agents.flashcard_generator import generate_flashcards
from src.api.schemas import (
    NoteCreate, NoteOut,
    FlashcardGenerateRequest, FlashcardOut, FlashcardReviewRequest,
)

router = APIRouter(tags=["study-tools"])
# Study-tools routes need concept name/description lookups (flashcard generation) —
# self-contained like auth_routes.py, since main.py can't be imported back into a
# router it itself includes (circular import).
cg = ConceptGraph.from_dataset_json("data/concepts_dataset.json")


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


@router.post("/flashcards/generate", response_model=list[FlashcardOut])
def generate(body: FlashcardGenerateRequest, student_id: str = Depends(get_current_student_id), db=Depends(get_db)):
    cards = generate_flashcards(cg, body.concept_id)
    saved = create_flashcards(db, student_id, body.concept_id, cards)
    return [FlashcardOut.model_validate(c) for c in saved]


@router.get("/flashcards/due", response_model=list[FlashcardOut])
def due(student_id: str = Depends(get_current_student_id), db=Depends(get_db)):
    cards = get_due_flashcards(db, student_id)
    return [FlashcardOut.model_validate(c) for c in cards]


@router.post("/flashcards/{flashcard_id}/review", response_model=FlashcardOut)
def review(flashcard_id: int, body: FlashcardReviewRequest, student_id: str = Depends(get_current_student_id), db=Depends(get_db)):
    card = review_flashcard(db, student_id, flashcard_id, body.knew_it)
    if not card:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    return FlashcardOut.model_validate(card)
