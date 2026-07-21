from pydantic import BaseModel, ConfigDict


class TwoFactorRequired(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pending_token: str


class TwoFactorVerify(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str


class TwoFactorCredentials(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    otpauth_uri: str
    secret: str
