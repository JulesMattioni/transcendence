import jwt
from fastapi import HTTPException
from datetime import datetime, timedelta, timezone
from config import SECRET_KEY, ALGORITHM


def decode_token(token: str) -> dict:
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
        "exp": now + timedelta(minutes=15),
    }
    return jwt.encode(payload=payload, key=SECRET_KEY, algorithms=[ALGORITHM])
