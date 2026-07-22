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
    return await auth_service.register(user_create=user)


@router.post("/login", response_model=LoginResponse | TwoFactorRequired)
async def login(
    user: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse | TwoFactorRequired:
    return await auth_service.login(email=user.email, password=user.password)


@router.post("/login/2fa/verify", response_model=LoginResponse)
async def login_verify_2fa(
    two_factor_verify: TwoFactorVerify,
    user_id: int = Depends(get_pending_user_id),
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    return await auth_service.login_2fa(
        user_id=user_id,
        code=two_factor_verify.code,
    )


@router.post("/2fa/enable", response_model=TwoFactorCredentials)
async def enable_2fa(
    user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> TwoFactorCredentials:
    return await auth_service.enable_2fa(user=user)


@router.post("/2fa/enable/verify")
async def enable_2fa_verify(
    two_factor_verify: TwoFactorVerify,
    user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    return await auth_service.enable_2fa_verify(
        user=user, code=two_factor_verify.code
    )


@router.post("/2fa/disable", response_model=UserRead)
async def disable_2fa(
    user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserRead:
    await auth_service.disable_2fa(user=user)
    return UserRead.model_validate(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    refresh_token: str, auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    return await auth_service.refresh(refresh_token=refresh_token)


@router.post("/logout")
async def logout(
    refresh_token: str, auth_service: AuthService = Depends(get_auth_service)
) -> None:
    return await auth_service.logout(refresh_token=refresh_token)


@router.patch("/update", response_model=UserRead)
async def update_user(
    user_update: UserUpdate,
    user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserRead:
    await auth_service.update_user(user=user, user_update=user_update)
    return UserRead.model_validate(user)


@router.get("/me", response_model=UserRead)
async def get_user(user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(user)
