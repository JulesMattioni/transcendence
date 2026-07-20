import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from app.repositories import UserRepository, TokenRepository
from app.schemas import LoginResponse, UserCreate, TokenResponse, UserRead
from app.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidTokenError,
    TokenExpiredError,
)
from app.core import hash_password, create_access_token, verify_password


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        token_repository: TokenRepository,
        session: AsyncSession,
    ) -> None:
        self._user_repository = user_repository
        self._token_repository = token_repository
        self._session = session

    async def register(self, user_create: UserCreate) -> LoginResponse:
        if (
            await self._user_repository.get_by_email(user_create.email)
            is not None
        ):
            raise EmailAlreadyExistsError()

        hashed_password = hash_password(user_create.password)

        now = datetime.now(timezone.utc)

        try:

            user = await self._user_repository.create_user(
                user_create.first_name,
                user_create.last_name,
                user_create.email,
                hashed_password,
            )

            refresh_token = secrets.token_urlsafe(32)

            await self._token_repository.create_token(
                refresh_token, user, now + timedelta(days=7)
            )

            access_token = create_access_token(user.id)

            await self._session.commit()

        except Exception:
            await self._session.rollback()
            raise

        return LoginResponse(
            tokens=TokenResponse(
                access_token=access_token, refresh_token=refresh_token
            ),
            user=UserRead.model_validate(user),
        )

    async def login(self, email: str, password: str) -> LoginResponse:
        user = await self._user_repository.get_by_email(email)

        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()

        now = datetime.now(timezone.utc)
        refresh_token = secrets.token_urlsafe(32)

        try:
            await self._token_repository.create_token(
                refresh_token, user, now + timedelta(days=7)
            )

            access_token = create_access_token(user.id)

            await self._session.commit()

        except Exception:
            await self._session.rollback()
            raise

        return LoginResponse(
            tokens=TokenResponse(
                access_token=access_token, refresh_token=refresh_token
            ),
            user=UserRead.model_validate(user),
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        rt = await self._token_repository.get_by_token(refresh_token)

        if rt is None:
            raise InvalidTokenError()

        now = datetime.now(timezone.utc)

        if rt.expired_at < now:
            raise TokenExpiredError()

        refresh_token = secrets.token_urlsafe(32)

        try:
            token = await self._token_repository.create_token(
                refresh_token, rt.user, now + timedelta(days=7)
            )
            await self._token_repository.delete_token(rt)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

        access_token = create_access_token(token.user_id)

        return TokenResponse(
            access_token=access_token, refresh_token=refresh_token
        )

    async def logout(self, refresh_token: str) -> None:
        rt = await self._token_repository.get_by_token(refresh_token)

        if rt is None:
            return

        try:
            await self._token_repository.delete_token(rt)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
