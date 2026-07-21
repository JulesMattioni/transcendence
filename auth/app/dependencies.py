from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import get_session
from app.repositories import UserRepository, TokenRepository
from app.models.auth import User
from app.services.auth_service import AuthService
from app.core.tokens import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_user_repository(
    session: AsyncSession = Depends(get_session),
) -> UserRepository:
    return UserRepository(session)


def get_token_repository(
    session: AsyncSession = Depends(get_session),
) -> TokenRepository:
    return TokenRepository(session)


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    token_repo: TokenRepository = Depends(get_token_repository),
    session: AsyncSession = Depends(get_session),
) -> AuthService:
    return AuthService(user_repo, token_repo, session)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    payload = decode_token(token)

    if payload.get("type") != "access":
        raise HTTPException(401, "Invalid token")

    user_id = int(payload["sub"])

    user = await user_repo.get_by_id(user_id)

    if user is None:
        raise HTTPException(401, "User not found")

    return user


async def get_pending_user_id(pending_token: str) -> int:
    payload = decode_token(pending_token)

    if payload.get("type") != "2fa_pending":
        raise HTTPException(401, "Invalid token")

    return int(payload["sub"])
