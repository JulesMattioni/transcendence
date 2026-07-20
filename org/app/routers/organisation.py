from fastapi import APIRouter
# from app.schemas.organisation import (OrganisationCreate, OrganisationRead,
# OrganisationUpdate)
from app.services.organisation_service import OrganisationService


router = APIRouter()

_service = OrganisationService()


@router.get("/organisation")
def organisation():
    pass
