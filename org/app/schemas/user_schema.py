from pydantic import BaseModel, EmailStr


class UserCreqtion(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    hashed_password: str
