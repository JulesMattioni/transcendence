import jwt
from fastapi import HTTPException
from datetime import datetime, timedelta, timezone
from typing import Any
from app.config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    TEMPORARY_TOKEN_EXPIRE_MINUTES,
)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(jwt=token, key=SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access",
    }
    return jwt.encode(payload=payload, key=SECRET_KEY, algorithm=ALGORITHM)


def create_temporary_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=TEMPORARY_TOKEN_EXPIRE_MINUTES),
        "type": "2fa_pending",
    }
    return jwt.encode(payload=payload, key=SECRET_KEY, algorithm=ALGORITHM)
