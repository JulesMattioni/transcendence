from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.routers import health, auth
from app.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidTokenError,
    TokenExpiredError,
)

app = FastAPI(title="auth")
app.include_router(health.router)
app.include_router(auth.router)


@app.exception_handler(EmailAlreadyExistsError)
async def email_exists_handler(
    request: Request, exc: EmailAlreadyExistsError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Email already registered"},
    )


@app.exception_handler(InvalidCredentialsError)
async def invalid_credentials_handler(
    request: Request, exc: InvalidCredentialsError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Invalid credentials"},
    )


@app.exception_handler(InvalidTokenError)
async def invalid_token_handler(
    request: Request, exc: InvalidTokenError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Invalid token"},
    )


@app.exception_handler(TokenExpiredError)
async def token_expired_handler(
    request: Request, exc: TokenExpiredError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Token expired"},
    )
