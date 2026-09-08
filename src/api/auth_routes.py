from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from pydantic import BaseModel

from src.db.database import get_db
from src.db.repository import get_student_by_username, create_student_with_password
from src.auth.security import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, decode_refresh_token,
)
from src.api.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=TokenResponse)
@limiter.limit("5/minute")
def register(request: Request, body: RegisterRequest, db=Depends(get_db)):
    if get_student_by_username(db, body.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    create_student_with_password(db, body.username, body.email, hash_password(body.password))
    return TokenResponse(
        access_token=create_access_token(body.username),
        refresh_token=create_refresh_token(body.username),
    )


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

    student_id = cast(str, student.student_id)
    return TokenResponse(
        access_token=create_access_token(student_id),
        refresh_token=create_refresh_token(student_id),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest):
    try:
        student_id = decode_refresh_token(body.refresh_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    return TokenResponse(
        access_token=create_access_token(student_id),
        refresh_token=create_refresh_token(student_id),  # rotated — old refresh token still technically valid until it expires
    )
