from src.db.database import engine, Base
from src.db import models  # noqa: F401 — ensures models are registered on Base before create_all

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created at data/student_model.db")

if __name__ == "__main__":
    init_db()