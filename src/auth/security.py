import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from jose import jwt
from passlib.context import CryptContext

from src.config import REFRESH_TOKEN_EXPIRE_DAYS
from jose import JWTError
from src.config import JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

load_dotenv()
_secret = os.getenv("JWT_SECRET_KEY")
if not _secret:
    raise RuntimeError(
        "JWT_SECRET_KEY is not set — refusing to start with an empty/missing signing key. "
        "Set it in .env (e.g. `python -c \"import secrets; print(secrets.token_hex(32))\"`)."
    )
# Re-typed as a plain str (not str | None) — the guard above only narrows at module
# scope; this explicit annotation makes the narrower type visible inside functions
# below that read this global too.
SECRET_KEY: str = _secret

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(student_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": student_id, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> str:
    """Returns the student_id encoded in the token, or raises if invalid/expired."""
    payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    return payload["sub"]


def create_refresh_token(student_id: str) -> str:
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": student_id, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_refresh_token(token: str) -> str:
    """Raises jose.JWTError if invalid/expired, OR if someone tries to use
    a normal access token here instead of a real refresh token."""
    payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    if payload.get("type") != "refresh":
        raise JWTError("Token is not a refresh token")
    return payload["sub"]