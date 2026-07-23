from pydantic import BaseModel


class User(BaseModel):
    id: int
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
