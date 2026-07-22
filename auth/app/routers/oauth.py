from fastapi import APIRouter, Response, Depends, Cookie

from app.services import AuthService
from app.schemas import OAuthRedirect, LoginResponse, TwoFactorRequired
from app.dependencies import get_auth_service
from app.exceptions import InvalidOAuthStateError

router = APIRouter(prefix="/oauth", tags=["auth"])


@router.get("/google/login", response_model=OAuthRedirect)
async def google_login(
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> OAuthRedirect:
    return auth_service.oauth_google_redirect(response)


@router.get(
    "/google/callback", response_model=LoginResponse | TwoFactorRequired
)
async def google_callback(
    code: str,
    state: str,
    oauth_state: str | None = Cookie(default=None),
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse | TwoFactorRequired:
    if not state or state != oauth_state:
        raise InvalidOAuthStateError()
    return await auth_service.oauth_google_login(code=code)
