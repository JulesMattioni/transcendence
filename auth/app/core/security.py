import pyotp
import secrets

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(pwd: str) -> str:
    """
    Hash a plaintext password using bcrypt.

    Args:
        pwd: Plaintext password to hash.

    Returns:
        The bcrypt hash of the password.
    """

    return str(pwd_context.hash(secret=pwd))


def verify_password(pwd: str, h: str) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.

    Args:
        pwd: Plaintext password to check.
        h: Bcrypt hash to verify against.

    Returns:
        True if the password matches the hash, False otherwise.
    """

    return bool(pwd_context.verify(secret=pwd, hash=h))


def generate_2fa_secret() -> str:
    """
    Generate a new base32-encoded secret for TOTP-based 2FA.

    Returns:
        A random base32 secret to use with an authenticator app.
    """

    return pyotp.random_base32()


def verify_2fa(secret: str, code: str) -> bool:
    """
    Verify a TOTP code against a user's 2FA secret.

    Args:
        secret: Base32-encoded TOTP secret associated with the user.
        code: 6-digit TOTP code provided by the user.

    Returns:
        True if the code is valid within the allowed time window, False
        otherwise.
    """

    totp = pyotp.TOTP(secret)

    return totp.verify(otp=code, valid_window=1)


def generate_token() -> str:
    """
    Generate a cryptographically secure URL-safe token.

    Returns:
        A random URL-safe token string.
    """

    return secrets.token_urlsafe(32)
