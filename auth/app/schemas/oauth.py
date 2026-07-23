from pydantic import BaseModel, ConfigDict


class OAuthRedirect(BaseModel):
    """
    Response containing the URL to redirect the user to for OAuth login.

    Attributes:
        authorization_url: URL of the OAuth provider's authorization page.
    """

    model_config = ConfigDict(from_attributes=True)

    authorization_url: str


class OAuthExchange(BaseModel):
    """
    Request body to exchange a one-time OAuth code for a full session.

    Attributes:
        exchange_code: One-time code issued after a successful OAuth callback.
    """

    model_config = ConfigDict(from_attributes=True)

    exchange_code: str
