import pyotp

from fastapi import Response
from urllib.parse import urlencode

from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from app.config import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    GOOGLE_CLIENT_ID,
    GOOGLE_REDIRECT_URI,
)
from app.models.auth import User, OAuthAccount
from app.repositories import UserRepository, TokenRepository, OAuthRepository
from app.schemas import (
    LoginResponse,
    UserCreate,
    UserUpdate,
    TokenResponse,
    UserRead,
    TwoFactorRequired,
    TwoFactorCredentials,
    OAuthRedirect,
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
    UserByEmailNotFoundError,
)
from app.core import (
    hash_password,
    create_access_token,
    verify_password,
    create_temporary_token,
    verify_2fa,
    generate_2fa_secret,
    generate_token,
    get_google_profile,
)


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        token_repository: TokenRepository,
        oauth_repository: OAuthRepository,
        session: AsyncSession,
    ) -> None:
        self._user_repository = user_repository
        self._token_repository = token_repository
        self._oauth_repository = oauth_repository
        self._session = session

    async def __issue_tokens(self, user: User) -> TokenResponse:
        now = datetime.now(timezone.utc)
        refresh_token = generate_token()

        try:
            await self._token_repository.create(
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
                first_name=user_create.first_name,
                last_name=user_create.last_name,
                email=user_create.email,
                hashed_password=hashed_password,
            )

        except Exception:
            await self._session.rollback()
            raise

        tokens = await self.__issue_tokens(user=user)

        return LoginResponse(
            tokens=tokens,
            user=UserRead.model_validate(user),
        )

    def oauth_google_redirect(self, response: Response) -> OAuthRedirect:
        state = generate_token()

        response.set_cookie(
            key="oauth_state",
            value=state,
            max_age=600,
            httponly=True,
            secure=True,
            samesite="lax",
        )

        params = {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
        }

        authorization_url = (
            "https://accounts.google.com/o/oauth2/auth?" + urlencode(params)
        )
        return OAuthRedirect(authorization_url=authorization_url)

    async def login(
        self, email: str, password: str
    ) -> LoginResponse | TwoFactorRequired:
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

    async def oauth_google_login(
        self, code: str
    ) -> LoginResponse | TwoFactorRequired:
        profile_response = await get_google_profile(code=code)

        oauth_account = await self._oauth_repository.get_by_provider(
            provider="google", provider_user_id=profile_response["sub"]
        )

        if oauth_account:
            if oauth_account.user.is_2fa_enabled:
                return TwoFactorRequired(
                    pending_token=create_temporary_token(
                        user_id=oauth_account.user.id
                    )
                )

            tokens = await self.__issue_tokens(user=oauth_account.user)
            return LoginResponse(
                tokens=tokens, user=UserRead.model_validate(oauth_account.user)
            )

        user = await self._user_repository.get_by_email(
            profile_response["email"]
        )

        if user is not None:
            try:
                oauth_account: OAuthAccount = (
                    await self._oauth_repository.create(
                        user=user,
                        provider="google",
                        provider_user_id=profile_response["sub"],
                    )
                )
            except Exception:
                await self._session.rollback()
                raise

            if user.is_2fa_enabled:
                await self._session.commit()
                return TwoFactorRequired(
                    pending_token=create_temporary_token(user_id=user.id)
                )

            tokens = await self.__issue_tokens(user=user)
            return LoginResponse(
                tokens=tokens,
                user=UserRead.model_validate(user),
            )

        try:
            user = await self._user_repository.create_user(
                first_name=profile_response["given_name"],
                last_name=profile_response["family_name"],
                email=profile_response["email"],
                hashed_password="IMPOSSIBLE",
            )

        except Exception:
            await self._session.rollback()
            raise

        try:
            oauth_account: OAuthAccount = await self._oauth_repository.create(
                user=user,
                provider="google",
                provider_user_id=profile_response["sub"],
            )
        except Exception:
            await self._session.rollback()
            raise

        tokens = await self.__issue_tokens(user=user)

        return LoginResponse(
            tokens=tokens,
            user=UserRead.model_validate(user),
        )

    async def login_2fa(self, user_id: int, code: str) -> LoginResponse:
        user = await self._user_repository.get_by_id(user_id)

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

    async def enable_2fa_verify(self, user: User, code: str) -> None:
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

    # May add password to confirm it s the user
    async def disable_2fa(self, user: User) -> None:
        if not user.is_2fa_enabled:
            raise TwoFactorNotConfiguredError()

        try:
            await self._user_repository.disable_2fa(user=user)
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

        refresh_token = generate_token()

        try:
            token = await self._token_repository.create(
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

    async def update_user(
        self,
        user: User,
        user_update: UserUpdate,
    ) -> None:
        try:
            await self._user_repository.change_location(
                user=user, location=user_update.location
            )
            await self._user_repository.change_avatar_id(
                user=user, avatar_id=user_update.avatar_id
            )
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

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

    async def get_user_by_email(self, email: str) -> UserRead:
        user = await self._user_repository.get_by_email(email)
        if not user:
            raise UserByEmailNotFoundError()
        return UserRead.model_validate(user)
