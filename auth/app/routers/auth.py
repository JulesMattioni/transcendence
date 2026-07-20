from fastapi import APIRouter, Depends
from app.services import AuthService
from app.schemas import (
    UserRead,
    UserCreate,
    UserLogin,
    LoginResponse,
    TokenResponse,
)
from app.models.auth import User
from app.dependencies import get_current_user, get_auth_service

router = APIRouter(tags=["auth"])


@router.post("/signup", response_model=LoginResponse)
async def register(
    user: UserCreate, auth_service: AuthService = Depends(get_auth_service)
) -> LoginResponse:
    return await auth_service.register(user_create=user)


@router.post("/login", response_model=LoginResponse)
async def login(
    user: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    return await auth_service.login(email=user.email, password=user.password)


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


@router.get("/me", response_model=UserRead)
async def get_user(user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(user)
