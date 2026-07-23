import pyotp

from fastapi import Response
from urllib.parse import urlencode

from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from app.config import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    GOOGLE_CLIENT_ID,
    GOOGLE_REDIRECT_URI,
    FT_CLIENT_ID,
    FT_REDIRECT_URI,
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
    OAuthExchange,
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
    create_oauth_exchange_token,
    decode_token,
    get_ft_profile,
)


class AuthService:
    """
    Service handling user authentication, registration, 2FA and OAuth logins.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        token_repository: TokenRepository,
        oauth_repository: OAuthRepository,
        session: AsyncSession,
    ) -> None:
        """
        Initialize the service with its repositories and database session.

        Args:
            user_repository: Repository for User persistence.
            token_repository: Repository for RefreshToken persistence.
            oauth_repository: Repository for OAuthAccount persistence.
            session: Async SQLAlchemy session used for database operations.
        """

        self._user_repository = user_repository
        self._token_repository = token_repository
        self._oauth_repository = oauth_repository
        self._session = session

    async def __issue_tokens(self, user: User) -> TokenResponse:
        """
        Create and persist a new refresh token and issue an access token for a
        user.

        Args:
            user: User to issue tokens for.

        Returns:
            TokenResponse containing the newly issued access_token and
            refresh_token.
        """

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

    def oauth_google_redirect(self, response: Response) -> OAuthRedirect:
        """
        Build the Google OAuth authorization URL and set the CSRF state cookie.

        Args:
            response: FastAPI response, used to set the oauth_state_google
            cookie.

        Returns:
            OAuthRedirect containing the Google authorization_url.
        """

        state = generate_token()

        response.set_cookie(
            key="oauth_state_google",
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
            "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
        )
        return OAuthRedirect(authorization_url=authorization_url)

    def oauth_ft_redirect(self, response: Response) -> OAuthRedirect:
        """
        Build the 42 OAuth authorization URL and set the CSRF state cookie.

        Args:
            response: FastAPI response, used to set the oauth_state_ft cookie.

        Returns:
            OAuthRedirect containing the 42 authorization_url.
        """

        state = generate_token()

        response.set_cookie(
            key="oauth_state_ft",
            value=state,
            max_age=600,
            httponly=True,
            secure=True,
            samesite="lax",
        )

        params = {
            "client_id": FT_CLIENT_ID,
            "redirect_uri": FT_REDIRECT_URI,
            "response_type": "code",
            "scope": "public",
            "state": state,
        }

        authorization_url = (
            "https://api.intra.42.fr/oauth/authorize?" + urlencode(params)
        )
        return OAuthRedirect(authorization_url=authorization_url)

    async def get_user_by_email(self, email: str) -> UserRead:
        """
        Retrieve a user's public profile by email address.

        Args:
            email: Email address to look up.

        Returns:
            UserRead with the matching user's profile data.

        Raises:
            UserByEmailNotFoundError: If no user with the given email exists.
        """

        user = await self._user_repository.get_by_email(email)

        if not user:
            raise UserByEmailNotFoundError()

        return UserRead.model_validate(user)

    async def register(self, user_create: UserCreate) -> LoginResponse:
        """
        Register a new user, hashing their password and issuing session tokens.

        Args:
            user_create: New user's registration data.

        Returns:
            LoginResponse containing the issued tokens and the created user's
            data.

        Raises:
            EmailAlreadyExistsError: If a user with the given email already
            exists.
        """

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

    async def login(
        self, email: str, password: str
    ) -> LoginResponse | TwoFactorRequired:
        """
        Authenticate a user with email and password.

        Args:
            email: User's email address.
            password: User's plaintext password.

        Returns:
            LoginResponse with issued tokens and user data if 2FA is disabled,
            or TwoFactorRequired with a pending token if 2FA must be verified
            first.

        Raises:
            InvalidCredentialsError: If the email is unknown or the password
            is wrong.
        """

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
    ) -> OAuthExchange | TwoFactorRequired:
        """
        Log in or register a user via Google OAuth.

        Fetches the Google profile for the authorization code, then links it to
        an existing OAuth account, an existing user matched by email, or
        creates a new user if neither exists.

        Args:
            code: OAuth authorization code from the Google callback.

        Returns:
            TwoFactorRequired with a pending token if the matched user has 2FA
            enabled, otherwise OAuthExchange with a one-time exchange code.
        """

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

            await self._session.commit()
            return OAuthExchange(
                exchange_code=create_oauth_exchange_token(
                    user_id=oauth_account.user.id
                )
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

            await self._session.commit()
            return OAuthExchange(
                exchange_code=create_oauth_exchange_token(user_id=user.id)
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

        await self._session.commit()
        return OAuthExchange(
            exchange_code=create_oauth_exchange_token(user_id=user.id)
        )

    async def oauth_ft_login(
        self, code: str
    ) -> OAuthExchange | TwoFactorRequired:
        """
        Log in or register a user via 42 OAuth.

        Fetches the 42 profile for the authorization code, then links it to
        an existing OAuth account, an existing user matched by email, or
        creates a new user if neither exists.

        Args:
            code: OAuth authorization code from the 42 callback.

        Returns:
            TwoFactorRequired with a pending token if the matched user has 2FA
            enabled, otherwise OAuthExchange with a one-time exchange code.
        """

        profile_response = await get_ft_profile(code=code)

        oauth_account = await self._oauth_repository.get_by_provider(
            provider="42", provider_user_id=str(profile_response["id"])
        )

        if oauth_account:
            if oauth_account.user.is_2fa_enabled:
                return TwoFactorRequired(
                    pending_token=create_temporary_token(
                        user_id=oauth_account.user.id
                    )
                )

            await self._session.commit()
            return OAuthExchange(
                exchange_code=create_oauth_exchange_token(
                    user_id=oauth_account.user.id
                )
            )

        user = await self._user_repository.get_by_email(
            profile_response["email"]
        )

        if user is not None:
            try:
                oauth_account: OAuthAccount = (
                    await self._oauth_repository.create(
                        user=user,
                        provider="42",
                        provider_user_id=str(profile_response["id"]),
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

            await self._session.commit()
            return OAuthExchange(
                exchange_code=create_oauth_exchange_token(user_id=user.id)
            )

        try:
            user = await self._user_repository.create_user(
                first_name=profile_response["first_name"],
                last_name=profile_response["last_name"],
                email=profile_response["email"],
                hashed_password="IMPOSSIBLE",
            )

        except Exception:
            await self._session.rollback()
            raise

        try:
            oauth_account: OAuthAccount = await self._oauth_repository.create(
                user=user,
                provider="42",
                provider_user_id=str(profile_response["id"]),
            )
        except Exception:
            await self._session.rollback()
            raise

        await self._session.commit()
        return OAuthExchange(
            exchange_code=create_oauth_exchange_token(user_id=user.id)
        )

    async def exchange_oauth_code(self, exchange_code: str) -> LoginResponse:
        """
        Exchange a one-time OAuth exchange code for a full login session.

        Args:
            exchange_code: One-time exchange code issued after an OAuth login.

        Returns:
            LoginResponse containing the issued tokens and the user's data.

        Raises:
            InvalidTokenError: If the exchange code is not a valid
            oauth_exchange token.
            UserNotFoundError: If the user referenced by the token no longer
            exists.
        """

        payload = decode_token(exchange_code)

        if payload["type"] != "oauth_exchange":
            raise InvalidTokenError()

        try:
            user = await self._user_repository.get_by_id(
                id=int(payload["sub"])
            )
        except ValueError:
            raise InvalidTokenError()

        if user is None:
            raise UserNotFoundError()

        tokens = await self.__issue_tokens(user=user)

        return LoginResponse(tokens=tokens, user=UserRead.model_validate(user))

    async def login_2fa(self, user_id: int, code: str) -> LoginResponse:
        """
        Complete login by verifying a 2FA code for a pending user.

        Args:
            user_id: ID of the user pending 2FA verification.
            code: 6-digit TOTP code submitted by the user.

        Returns:
            LoginResponse containing the issued tokens and the user's data.

        Raises:
            UserNotFoundError: If the user no longer exists.
            Auth2faError: If the TOTP code is invalid.
        """

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
        """
        Generate a new TOTP secret and start 2FA setup for a user.

        Args:
            user: User to enable 2FA for.

        Returns:
            TwoFactorCredentials containing the TOTP secret and its
            provisioning URI.

        Raises:
            TwoFactorAlreadyEnabledError: If 2FA is already enabled for the
            user.
        """

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
        """
        Confirm 2FA setup by verifying a TOTP code and enabling 2FA for the
        user.

        Args:
            user: User completing 2FA setup.
            code: 6-digit TOTP code submitted by the user.

        Raises:
            TwoFactorNotConfiguredError: If no TOTP secret was registered for
            the user.
            Auth2faError: If the TOTP code is invalid.
        """

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

    async def disable_2fa(self, user: User) -> None:
        """
        Disable 2FA for a user.

        Args:
            user: User to disable 2FA for.

        Raises:
            TwoFactorNotConfiguredError: If 2FA is not currently enabled for
            the user.
        """

        if not user.is_2fa_enabled:
            raise TwoFactorNotConfiguredError()

        try:
            await self._user_repository.disable_2fa(user=user)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    async def refresh(self, refresh_token: str) -> TokenResponse:
        """
        Rotate a refresh token and issue a new access/refresh token pair.

        Args:
            refresh_token: Refresh token to exchange.

        Returns:
            TokenResponse containing the newly issued access_token and
            refresh_token.

        Raises:
            InvalidTokenError: If the refresh token doesn't exist.
            TokenExpiredError: If the refresh token has expired.
        """

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
        """
        Update a user's location and avatar.

        Args:
            user: User to update.
            user_update: New location and avatar_id to apply.
        """

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
        """
        Log out a user by deleting their refresh token, if it exists.

        Args:
            refresh_token: Refresh token to revoke.
        """

        rt = await self._token_repository.get_by_token(refresh_token)

        if rt is None:
            return

        try:
            await self._token_repository.delete_token(rt)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
