"""Schema of the authenticated user resolved from the auth service."""

from pydantic import BaseModel


class User(BaseModel):
    """Minimal identity of the current user, as returned by ``auth``."""

    id: int
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
