from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import get_session
from app.repositories import UserRepository, TokenRepository, OAuthRepository
from app.clients import RealtimeClient
from app.models.auth import User
from app.services import AuthService
from app.core.tokens import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_user_repository(
    session: AsyncSession = Depends(get_session),
) -> UserRepository:
    """
    Build a UserRepository bound to the request's database session.

    Args:
        session: Async SQLAlchemy session injected for the current request.

    Returns:
        A UserRepository instance.
    """

    return UserRepository(session)


def get_token_repository(
    session: AsyncSession = Depends(get_session),
) -> TokenRepository:
    """
    Build a TokenRepository bound to the request's database session.

    Args:
        session: Async SQLAlchemy session injected for the current request.

    Returns:
        A TokenRepository instance.
    """

    return TokenRepository(session)


def get_oauth_repository(
    session: AsyncSession = Depends(get_session),
) -> OAuthRepository:
    """
    Build an OAuthRepository bound to the request's database session.

    Args:
        session: Async SQLAlchemy session injected for the current request.

    Returns:
        An OAuthRepository instance.
    """

    return OAuthRepository(session)


def get_realtime_client() -> RealtimeClient:
    """
    Build a RealtimeClient for notifying the realtime service of auth events.

    Returns:
        A RealtimeClient instance.
    """
    return RealtimeClient()


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    token_repo: TokenRepository = Depends(get_token_repository),
    oauth_repo: OAuthRepository = Depends(get_oauth_repository),
    realtime_client: RealtimeClient = Depends(get_realtime_client),
    session: AsyncSession = Depends(get_session),
) -> AuthService:
    """
    Build an AuthService with its required repositories and session.

    Args:
        user_repo: Injected UserRepository.
        token_repo: Injected TokenRepository.
        oauth_repo: Injected OAuthRepository.
        realtime_client: Injected RealtimeClient.
        session: Async SQLAlchemy session injected for the current request.

    Returns:
        An AuthService instance.
    """

    return AuthService(
        user_repository=user_repo,
        token_repository=token_repo,
        oauth_repository=oauth_repo,
        realtime_client=realtime_client,
        session=session,
    )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    """
    Resolve the currently authenticated user from a bearer access token.

    Args:
        token: JWT access token extracted from the Authorization header.
        user_repo: Injected UserRepository.

    Returns:
        The authenticated User.

    Raises:
        HTTPException: 401 if the token is not an access token or the user
        doesn't exist.
    """

    payload = decode_token(token)

    if payload.get("type") != "access":
        raise HTTPException(401, "Invalid token")

    user_id = int(payload["sub"])

    user = await user_repo.get_by_id(user_id)

    if user is None:
        raise HTTPException(401, "User not found")

    return user


async def get_pending_user_id(
    pending_token: str = Depends(oauth2_scheme),
) -> int:
    """
    Resolve the ID of the user pending 2FA verification from a bearer token.

    Args:
        pending_token: JWT 2fa_pending token extracted from the Authorization
        header.

    Returns:
        The pending user's ID.

    Raises:
        HTTPException: 401 if the token is not a 2fa_pending token.
    """

    payload = decode_token(pending_token)

    if payload.get("type") != "2fa_pending":
        raise HTTPException(401, "Invalid token")

    return int(payload["sub"])
