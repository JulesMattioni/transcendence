from pydantic import BaseModel, ConfigDict
from app.schemas import TokenResponse, UserRead


class LoginResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tokens: TokenResponse
    user: UserRead
