from fastapi import APIRouter, Response, Depends, Cookie
from fastapi.responses import RedirectResponse
from app.services import AuthService
from app.schemas import (
    OAuthRedirect,
    LoginResponse,
    TwoFactorRequired,
    OAuthExchange,
)
from app.dependencies import get_auth_service
from app.exceptions import InvalidOAuthStateError
from app.config import FRONTEND_URL

router = APIRouter(prefix="/oauth", tags=["auth"])


@router.get("/google/login", response_model=OAuthRedirect)
async def google_login(
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> OAuthRedirect:
    return auth_service.oauth_google_redirect(response=response)


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str,
    oauth_state_google: str | None = Cookie(default=None),
    auth_service: AuthService = Depends(get_auth_service),
) -> RedirectResponse:
    if not state or state != oauth_state_google:
        raise InvalidOAuthStateError()

    result = await auth_service.oauth_google_login(code=code)

    if isinstance(result, TwoFactorRequired):
        url = (
            f"{FRONTEND_URL}/oauth/callback?pending_token="
            f"{result.pending_token}"
        )
    else:
        url = (
            f"{FRONTEND_URL}/oauth/callback?exchange_code="
            f"{result.exchange_code}"
        )

    return RedirectResponse(url=url)


@router.get("/42/login", response_model=OAuthRedirect)
async def ft_login(
    response: Response, auth_service: AuthService = Depends(get_auth_service)
) -> OAuthRedirect:
    return auth_service.oauth_ft_redirect(response=response)


@router.get("/42/callback")
async def ft_callback(
    code: str,
    state: str,
    oauth_state_ft: str | None = Cookie(default=None),
    auth_service: AuthService = Depends(get_auth_service),
) -> RedirectResponse:
    if not state or state != oauth_state_ft:
        raise InvalidOAuthStateError()

    result = await auth_service.oauth_ft_login(code=code)

    if isinstance(result, TwoFactorRequired):
        url = (
            f"{FRONTEND_URL}/oauth/callback?pending_token="
            f"{result.pending_token}"
        )
    else:
        url = (
            f"{FRONTEND_URL}/oauth/callback?exchange_code="
            f"{result.exchange_code}"
        )

    return RedirectResponse(url=url)


@router.post("/exchange", response_model=LoginResponse)
async def oauth_exchange(
    oauth_exchange: OAuthExchange,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    return await auth_service.exchange_oauth_code(
        exchange_code=oauth_exchange.exchange_code
    )
