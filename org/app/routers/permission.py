from fastapi import APIRouter
from app.services.permission_service import PermService

router = APIRouter()

_service = PermService()

@router.get("/organisation")
def permission():
    pass