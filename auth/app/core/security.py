import pyotp
import secrets

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(pwd: str) -> str:
    return str(pwd_context.hash(pwd))


def verify_password(pwd: str, h: str) -> bool:
    return bool(pwd_context.verify(pwd, h))


def generate_2fa_secret() -> str:
    return pyotp.random_base32()


def verify_2fa(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)

    return totp.verify(code, valid_window=1)


def generate_token() -> str:
    return secrets.token_urlsafe(32)
