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
    """
    Start the Google OAuth login flow.

    Args:
        response: FastAPI response, used to set the OAuth state cookie.
        auth_service: Injected authentication service.

    Returns:
        OAuthRedirect containing the Google authorization_url to redirect the
        user to.
    """

    return auth_service.oauth_google_redirect(response=response)


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str,
    oauth_state_google: str | None = Cookie(default=None),
    auth_service: AuthService = Depends(get_auth_service),
) -> RedirectResponse:
    """
    Handle the Google OAuth callback and redirect to the frontend.

    Args:
        code: OAuth authorization code returned by Google.
        state: OAuth state parameter returned by Google, checked against the
        cookie.
        oauth_state_google: OAuth state cookie set during the login redirect.
        auth_service: Injected authentication service.

    Returns:
        Redirect to the frontend OAuth callback URL, with either a
        pending_token (2FA required) or an exchange_code (login complete)
        query parameter.

    Raises:
        InvalidOAuthStateError: If the state parameter doesn't match the
        cookie.
    """

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
    """
    Start the 42 OAuth login flow.

    Args:
        response: FastAPI response, used to set the OAuth state cookie.
        auth_service: Injected authentication service.

    Returns:
        OAuthRedirect containing the 42 authorization_url to redirect the user
        to.
    """

    return auth_service.oauth_ft_redirect(response=response)


@router.get("/42/callback")
async def ft_callback(
    code: str,
    state: str,
    oauth_state_ft: str | None = Cookie(default=None),
    auth_service: AuthService = Depends(get_auth_service),
) -> RedirectResponse:
    """
    Handle the 42 OAuth callback and redirect to the frontend.

    Args:
        code: OAuth authorization code returned by 42.
        state: OAuth state parameter returned by 42, checked against the
        cookie.
        oauth_state_ft: OAuth state cookie set during the login redirect.
        auth_service: Injected authentication service.

    Returns:
        Redirect to the frontend OAuth callback URL, with either a
        pending_token (2FA required) or an exchange_code (login complete)
        query parameter.

    Raises:
        InvalidOAuthStateError: If the state parameter doesn't match the
        cookie.
    """

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
    """
    Exchange a one-time OAuth exchange code for a full session.

    Args:
        oauth_exchange: Exchange code obtained from the OAuth callback
        redirect.
        auth_service: Injected authentication service.

    Returns:
        LoginResponse containing the issued tokens (access/refresh) and the
        user's data.
    """

    return await auth_service.exchange_oauth_code(
        exchange_code=oauth_exchange.exchange_code
    )
