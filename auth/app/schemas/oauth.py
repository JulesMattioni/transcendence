from pydantic import BaseModel, ConfigDict


class OAuthRedirect(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    authorization_url: str


class OAuthExchange(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    exchange_code: str
