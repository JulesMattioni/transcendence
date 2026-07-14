from pydantic import BaseModel, ConfigDict, EmailStr


class User(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    first_name: str
    last_name: str
    email: EmailStr
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: EmailStr
