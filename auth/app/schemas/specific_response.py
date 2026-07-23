from pydantic import BaseModel, ConfigDict
from app.schemas.user import UserRead
from app.schemas.token import TokenResponse


class LoginResponse(BaseModel):
    """
    Response returned after a successful login or registration.

    Attributes:
        tokens: Issued access and refresh tokens.
        user: The authenticated user's profile data.
    """

    model_config = ConfigDict(from_attributes=True)

    tokens: TokenResponse
    user: UserRead
