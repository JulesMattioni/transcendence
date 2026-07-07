from fastapi import APIRouter
from app.services.organisation_service import OrgSerive

router = APIRouter()

_service = OrgSerive()

@router.get("/organisation")
def organisation():
    pass