from src.db.database import engine, Base, DATABASE_URL
from src.db import models  # noqa: F401 — ensures models are registered on Base before create_all

def init_db():
    Base.metadata.create_all(bind=engine)
    print(f"Database tables created at {DATABASE_URL}")

if __name__ == "__main__":
    init_db()