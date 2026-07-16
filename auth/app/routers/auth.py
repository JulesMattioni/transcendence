from fastapi import APIRouter
from app.services import AuthService
from app.schemas import UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", model_response=UserRead)
def get_user(token: Depends()):
    pass
