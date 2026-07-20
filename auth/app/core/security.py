from passlib.context import CryptContext
from typing import Any

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(pwd: str) -> str:
    return str(pwd_context.hash(pwd))


def verify_password(pwd: str, h: str) -> bool:
    return bool(pwd_context.verify(pwd, h))
