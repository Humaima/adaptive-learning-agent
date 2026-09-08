import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# docker-compose sets DATABASE_URL to the Postgres service; local (non-Docker) dev
# falls back to a SQLite file. check_same_thread is a SQLite-only connect arg — it
# doesn't exist for psycopg2, so it's only passed for the SQLite case.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/student_model.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI-style dependency — yields a session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()