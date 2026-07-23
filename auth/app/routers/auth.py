from fastapi import APIRouter, Depends
from app.services import AuthService
from app.schemas import (
    UserRead,
    UserCreate,
    UserLogin,
    UserUpdate,
    LoginResponse,
    TokenResponse,
    TwoFactorRequired,
    TwoFactorVerify,
    TwoFactorCredentials,
    UserLookup,
)
from app.models.auth import User
from app.dependencies import (
    get_current_user,
    get_auth_service,
    get_pending_user_id,
)

router = APIRouter(tags=["auth"])


@router.post("/signup", response_model=LoginResponse)
async def register(
    user: UserCreate, auth_service: AuthService = Depends(get_auth_service)
) -> LoginResponse:
    """
    Register a new user account.

    Args:
        user: New user's registration data.
        auth_service: Injected authentication service.

    Returns:
        LoginResponse containing the issued tokens (access/refresh) and the
        created user's data.
    """

    return await auth_service.register(user_create=user)


@router.post("/login", response_model=LoginResponse | TwoFactorRequired)
async def login(
    user: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse | TwoFactorRequired:
    """
    Authenticate a user with email and password.

    Args:
        user: User's login credentials (email, password).
        auth_service: Injected authentication service.

    Returns:
        LoginResponse with the issued tokens and user data if 2FA is disabled,
        or TwoFactorRequired with a pending token if 2FA must be verified
        first.
    """

    return await auth_service.login(email=user.email, password=user.password)


@router.post("/login/2fa/verify", response_model=LoginResponse)
async def login_verify_2fa(
    two_factor_verify: TwoFactorVerify,
    user_id: int = Depends(get_pending_user_id),
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    """
    Complete login by verifying a 2FA code for a pending user.

    Args:
        two_factor_verify: 2FA code submitted by the user.
        user_id: ID of the user pending 2FA verification.
        auth_service: Injected authentication service.

    Returns:
        LoginResponse containing the issued tokens (access/refresh) and the
        user's data.
    """

    return await auth_service.login_2fa(
        user_id=user_id,
        code=two_factor_verify.code,
    )


@router.post("/2fa/enable", response_model=TwoFactorCredentials)
async def enable_2fa(
    user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> TwoFactorCredentials:
    """
    Start 2FA setup for the current user.

    Args:
        user: Currently authenticated user.
        auth_service: Injected authentication service.

    Returns:
        TwoFactorCredentials containing the TOTP secret and its otpauth
        provisioning URI.
    """

    return await auth_service.enable_2fa(user=user)


@router.post("/2fa/enable/verify")
async def enable_2fa_verify(
    two_factor_verify: TwoFactorVerify,
    user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    """
    Confirm 2FA setup by verifying a code and enabling 2FA for the user.

    Args:
        two_factor_verify: 2FA code submitted by the user.
        user: Currently authenticated user.
        auth_service: Injected authentication service.
    """

    return await auth_service.enable_2fa_verify(
        user=user, code=two_factor_verify.code
    )


@router.post("/2fa/disable", response_model=UserRead)
async def disable_2fa(
    user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserRead:
    """
    Disable 2FA for the current user.

    Args:
        user: Currently authenticated user.
        auth_service: Injected authentication service.

    Returns:
        UserRead with the user's updated profile data
        (is_2fa_enabled now False).
    """

    await auth_service.disable_2fa(user=user)
    return UserRead.model_validate(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    refresh_token: str, auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """
    Exchange a valid refresh token for a new access/refresh token pair.

    Args:
        refresh_token: Refresh token to exchange.
        auth_service: Injected authentication service.

    Returns:
        TokenResponse containing the newly issued access_token and
        refresh_token.
    """

    return await auth_service.refresh(refresh_token=refresh_token)


@router.post("/logout")
async def logout(
    refresh_token: str, auth_service: AuthService = Depends(get_auth_service)
) -> None:
    """
    Log out a user by revoking their refresh token.

    Args:
        refresh_token: Refresh token to revoke.
        auth_service: Injected authentication service.
    """

    return await auth_service.logout(refresh_token=refresh_token)


@router.patch("/update", response_model=UserRead)
async def update_user(
    user_update: UserUpdate,
    user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserRead:
    """
    Update the current user's location and avatar.

    Args:
        user_update: New location and avatar_id to apply.
        user: Currently authenticated user.
        auth_service: Injected authentication service.

    Returns:
        UserRead with the user's updated profile data.
    """

    await auth_service.update_user(user=user, user_update=user_update)
    return UserRead.model_validate(user)


@router.get("/me", response_model=UserRead)
async def get_user(user: User = Depends(get_current_user)) -> UserRead:
    """
    Retrieve the currently authenticated user's profile.

    Args:
        user: Currently authenticated user.

    Returns:
        UserRead with the user's id, name, email, location, avatar_id and 2FA
        status.
    """

    return UserRead.model_validate(user)


@router.get("/users/by-email", response_model=UserLookup)
async def get_user_by_email(
    email: str,
    _: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserLookup:
    """
    Look up basic user information by email address.

    Args:
        email: Email address to look up.
        _: Currently authenticated user (used only to require authentication).
        auth_service: Injected authentication service.

    Returns:
        UserLookup containing the matching user's id, email, first_name and
        last_name.
    """

    user = await auth_service.get_user_by_email(email)
    return UserLookup.model_validate(user)
