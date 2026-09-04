from src.db.database import SessionLocal
from src.db.repository import set_mastery, log_interaction, get_student_model

if __name__ == "__main__":
    db = SessionLocal()

    set_mastery(db, "student_001", "linear_algebra", 0.9)
    set_mastery(db, "student_001", "calculus", 0.3)
    log_interaction(db, "student_001", "backpropagation", "question", "Explain backpropagation.")

    model = get_student_model(db, "student_001")
    print(model.model_dump_json(indent=2))
