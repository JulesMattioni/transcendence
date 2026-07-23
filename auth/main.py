from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.routers import health, auth, oauth
from app.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidTokenError,
    TokenExpiredError,
    Auth2faError,
    UserNotFoundError,
    TwoFactorAlreadyEnabledError,
    TwoFactorNotConfiguredError,
    InvalidOAuthStateError,
    GoogleAuthError,
    UserByEmailNotFoundError,
    FtAuthError,
)

app = FastAPI(title="auth")
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(oauth.router)


@app.exception_handler(EmailAlreadyExistsError)
async def email_exists_handler(
    request: Request, exc: EmailAlreadyExistsError
) -> JSONResponse:
    """
    Return a 409 response when registration is attempted with an existing
    email.
    """

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Email already registered"},
    )


@app.exception_handler(InvalidCredentialsError)
async def invalid_credentials_handler(
    request: Request, exc: InvalidCredentialsError
) -> JSONResponse:
    """
    Return a 401 response when login credentials are invalid.
    """

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Invalid credentials"},
    )


@app.exception_handler(InvalidTokenError)
async def invalid_token_handler(
    request: Request, exc: InvalidTokenError
) -> JSONResponse:
    """
    Return a 401 response when a token is malformed or of the wrong type.
    """

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Invalid token"},
    )


@app.exception_handler(TokenExpiredError)
async def token_expired_handler(
    request: Request, exc: TokenExpiredError
) -> JSONResponse:
    """
    Return a 401 response when a token has expired.
    """

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Token expired"},
    )


@app.exception_handler(Auth2faError)
async def auth_2fa_failed_handler(
    request: Request, exc: Auth2faError
) -> JSONResponse:
    """
    Return a 401 response when a 2FA TOTP code is invalid.
    """

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Invalid code"},
    )


@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(
    request: Request, exc: UserNotFoundError
) -> JSONResponse:
    """
    Return a 401 response when the referenced user does not exist.
    """

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "User not found"},
    )


@app.exception_handler(TwoFactorAlreadyEnabledError)
async def two_factor_already_enabled_handler(
    request: Request, exc: TwoFactorAlreadyEnabledError
) -> JSONResponse:
    """
    Return a 409 response when enabling 2FA for a user that already has it
    enabled.
    """

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "2FA already enabled"},
    )


@app.exception_handler(TwoFactorNotConfiguredError)
async def two_factor_not_configured_handler(
    request: Request, exc: TwoFactorNotConfiguredError
) -> JSONResponse:
    """
    Return a 401 response when a 2FA operation is attempted with no secret
    configured.
    """

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "2FA not configured"},
    )


@app.exception_handler(InvalidOAuthStateError)
async def invalid_oauth_state_handler(
    request: Request, exc: InvalidOAuthStateError
) -> JSONResponse:
    """
    Return a 401 response when an OAuth callback's state doesn't match the
    cookie.
    """

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "OAuth state error"},
    )


@app.exception_handler(GoogleAuthError)
async def google_auth_failed_handler(
    request: Request, exc: GoogleAuthError
) -> JSONResponse:
    """
    Return a 400 response when Google OAuth token or profile retrieval fails.
    """

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Google authentication failed"},
    )


@app.exception_handler(FtAuthError)
async def ft_auth_failed_handler(
    request: Request, exc: FtAuthError
) -> JSONResponse:
    """
    Return a 400 response when 42 OAuth token or profile retrieval fails.
    """

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "42 authentication failed"},
    )


@app.exception_handler(UserByEmailNotFoundError)
async def user_by_email_not_found_handler(
    request: Request, exc: UserByEmailNotFoundError
) -> JSONResponse:
    """
    Return a 404 response when no user matches the given email.
    """

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "No user with this email"},
    )
