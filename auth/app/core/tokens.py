import jwt
from fastapi import HTTPException
from datetime import datetime, timedelta, timezone
from typing import Any
from app.config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    TEMPORARY_TOKEN_EXPIRE_MINUTES,
    OAUTH_EXCHANGE_EXPIRE_SECONDS,
)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token: Encoded JWT token to decode.

    Returns:
        The decoded token payload as a dictionary.

    Raises:
        HTTPException: If the token is expired or invalid.
    """

    try:
        return jwt.decode(jwt=token, key=SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")


def create_access_token(user_id: int) -> str:
    """
    Create a signed JWT access token for an authenticated user.

    Args:
        user_id: ID of the user to encode in the token.

    Returns:
        The encoded JWT access token.
    """

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access",
    }
    return jwt.encode(payload=payload, key=SECRET_KEY, algorithm=ALGORITHM)


def create_temporary_token(user_id: int) -> str:
    """
    Create a short-lived JWT token for a user pending 2FA verification.

    Args:
        user_id: ID of the user to encode in the token.

    Returns:
        The encoded JWT temporary token.
    """

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=TEMPORARY_TOKEN_EXPIRE_MINUTES),
        "type": "2fa_pending",
    }
    return jwt.encode(payload=payload, key=SECRET_KEY, algorithm=ALGORITHM)


def create_oauth_exchange_token(user_id: int) -> str:
    """
    Create a short-lived JWT token to exchange for a full session after OAuth
    login.

    Args:
        user_id: ID of the user to encode in the token.

    Returns:
        The encoded JWT OAuth exchange token.
    """

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(seconds=OAUTH_EXCHANGE_EXPIRE_SECONDS),
        "type": "oauth_exchange",
    }
    return jwt.encode(payload=payload, key=SECRET_KEY, algorithm=ALGORITHM)
