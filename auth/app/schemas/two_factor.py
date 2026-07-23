from pydantic import BaseModel, ConfigDict


class TwoFactorRequired(BaseModel):
    """
    Response indicating that 2FA verification is required to complete login.

    Attributes:
        pending_token: Temporary token identifying the user pending 2FA
        verification.
    """

    model_config = ConfigDict(from_attributes=True)

    pending_token: str


class TwoFactorVerify(BaseModel):
    """
    Request body to verify a 2FA code.

    Attributes:
        code: 6-digit TOTP code provided by the user.
    """

    model_config = ConfigDict(from_attributes=True)

    code: str


class TwoFactorCredentials(BaseModel):
    """
    Credentials returned when starting 2FA setup for a user.

    Attributes:
        otpauth_uri: Provisioning URI to scan with an authenticator app.
        secret: Base32-encoded TOTP secret.
    """

    model_config = ConfigDict(from_attributes=True)

    otpauth_uri: str
    secret: str
