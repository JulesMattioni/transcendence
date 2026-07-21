import secrets
import pyotp
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from app.config import REFRESH_TOKEN_EXPIRE_DAYS
from app.models.auth import User
from app.repositories import UserRepository, TokenRepository
from app.schemas import (
    LoginResponse,
    UserCreate,
    TokenResponse,
    UserRead,
    TwoFactorRequired,
    TwoFactorCredentials,
)
from app.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidTokenError,
    TokenExpiredError,
    Auth2faError,
    UserNotFoundError,
    TwoFactorAlreadyEnabledError,
    TwoFactorNotConfiguredError,
)
from app.core import (
    hash_password,
    create_access_token,
    verify_password,
    create_temporary_token,
    verify_2fa,
    generate_2fa_secret,
)


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

    async def __issue_tokens(self, user: User) -> TokenResponse:
        now = datetime.now(timezone.utc)
        refresh_token = secrets.token_urlsafe(32)

        try:
            await self._token_repository.create_token(
                refresh_token,
                user,
                now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            )

            access_token = create_access_token(user_id=user.id)

            await self._session.commit()

        except Exception:
            await self._session.rollback()
            raise

        return TokenResponse(
            access_token=access_token, refresh_token=refresh_token
        )

    async def register(self, user_create: UserCreate) -> LoginResponse:
        if (
            await self._user_repository.get_by_email(user_create.email)
            is not None
        ):
            raise EmailAlreadyExistsError()

        hashed_password = hash_password(user_create.password)

        try:

            user = await self._user_repository.create_user(
                user_create.first_name,
                user_create.last_name,
                user_create.email,
                hashed_password,
            )

        except Exception:
            await self._session.rollback()
            raise

        tokens = await self.__issue_tokens(user=user)

        return LoginResponse(
            tokens=tokens,
            user=UserRead.model_validate(user),
        )

    async def login(self, email: str, password: str) -> LoginResponse:
        user = await self._user_repository.get_by_email(email)

        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()

        if user.is_2fa_enabled:
            return TwoFactorRequired(
                pending_token=create_temporary_token(user_id=user.id)
            )

        tokens = await self.__issue_tokens(user=user)

        return LoginResponse(
            tokens=tokens,
            user=UserRead.model_validate(user),
        )

    async def login_2fa(self, user_id: int, code: str) -> LoginResponse:
        user: User = await self._user_repository.get_by_id(user_id)

        if user is None:
            raise UserNotFoundError()

        secret = user.secret_2fa

        if not verify_2fa(secret=secret, code=code):
            raise Auth2faError()

        tokens = await self.__issue_tokens(user=user)

        return LoginResponse(
            tokens=tokens,
            user=UserRead.model_validate(user),
        )

    async def enable_2fa(self, user: User) -> TwoFactorCredentials:
        if user.is_2fa_enabled:
            raise TwoFactorAlreadyEnabledError()

        secret = generate_2fa_secret()

        try:
            await self._user_repository.register_2fa_secret(
                user=user, secret=secret
            )
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

        uri = pyotp.TOTP(secret).provisioning_uri(
            name=user.email, issuer_name="Keepr"
        )
        return TwoFactorCredentials(otpauth_uri=uri, secret=secret)

    async def enable_2fa_verify(self, user: User, code: str):
        secret = user.secret_2fa

        if not secret:
            raise TwoFactorNotConfiguredError()

        if not verify_2fa(secret=secret, code=code):
            raise Auth2faError()

        try:
            await self._user_repository.enable_2fa(user=user)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

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
                refresh_token,
                rt.user,
                now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
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
