from pydantic import BaseModel, ConfigDict
from app.schemas.user import UserRead
from app.schemas.token import TokenResponse


class LoginResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tokens: TokenResponse
    user: UserRead


class TwoFactorRequired(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pending_token: str


class TwoFactorVerify(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pending_token: str
    code: str
