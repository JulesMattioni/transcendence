import re

MIN_PASSWORD_LENGTH = 8

# bcrypt silently truncates anything past 72 bytes, so a longer password
# would authenticate any other value sharing its first 72 bytes.
MAX_PASSWORD_BYTES = 72

PASSWORD_RULES = (
    (MIN_PASSWORD_LENGTH, "at least 8 characters"),
    (r"[A-Z]", "one uppercase letter"),
    (r"[a-z]", "one lowercase letter"),
    (r"[0-9]", "one number"),
    (r"[^A-Za-z0-9]", "one special character"),
)


def validate_password_strength(password: str) -> str:
    """
    Check a password against the registration strength rules.

    Mirrors the rules the frontend shows in its live checklist, so the
    server enforces what the UI advertises instead of trusting it.

    Args:
        password: Plaintext password submitted at registration.

    Returns:
        The password unchanged when every rule is met.

    Raises:
        ValueError: Listing every unmet rule, so the caller sees all the
        problems at once rather than one per attempt.
    """

    validate_password_length(password)

    missing = [
        message
        for pattern, message in PASSWORD_RULES[1:]
        if not re.search(str(pattern), password)
    ]
    if len(password) < MIN_PASSWORD_LENGTH:
        missing.insert(0, PASSWORD_RULES[0][1])

    if missing:
        raise ValueError("Password must contain " + ", ".join(missing) + ".")

    return password


def validate_password_length(password: str) -> str:
    """
    Check a password against the bounds bcrypt imposes.

    Applied at login as well as registration: existing accounts must stay
    usable, but no password may exceed what bcrypt actually hashes.

    Args:
        password: Plaintext password submitted by the user.

    Returns:
        The password unchanged when it fits the accepted bounds.

    Raises:
        ValueError: When the password is empty or longer than bcrypt's
        72-byte limit.
    """

    if not password:
        raise ValueError("Password is required.")

    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValueError(
            f"Password must not exceed {MAX_PASSWORD_BYTES} bytes."
        )

    return password
