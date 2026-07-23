from pydantic import BaseModel, ConfigDict


class TokenResponse(BaseModel):
    """
    Pair of tokens issued to an authenticated user.

    Attributes:
        access_token: Short-lived JWT used to authenticate API requests.
        refresh_token: Long-lived token used to obtain a new access token.
        token_type: Type of the token, always "bearer".
    """

    model_config = ConfigDict(from_attributes=True)

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
