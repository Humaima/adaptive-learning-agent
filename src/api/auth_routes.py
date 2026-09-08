from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from src.db.database import get_db
from src.db.repository import get_student_by_username, create_student_with_password
from src.auth.security import hash_password, verify_password, create_access_token
from src.api.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=TokenResponse)
@limiter.limit("5/minute")
def register(request: Request, body: RegisterRequest, db=Depends(get_db)):
    if get_student_by_username(db, body.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    create_student_with_password(db, body.username, body.email, hash_password(body.password))
    token = create_access_token(body.username)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    student = get_student_by_username(db, form_data.username)
    hashed_password = cast(str, student.hashed_password) if student is not None else None
    if (
        student is None
        or hashed_password is None
        or not verify_password(form_data.password, hashed_password)
    ):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    token = create_access_token(cast(str, student.student_id))
    return TokenResponse(access_token=token)
