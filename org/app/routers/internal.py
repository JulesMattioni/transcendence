from fastapi import APIRouter, Depends
from app.schemas.organisation import OrganisationMemberRead
from app.dependancies import get_organisation_service
from app.services.organisation_service import OrganisationService

router = APIRouter(
    prefix="/internal",
    tags=["Internal"],
)


@router.get(
    "/organisations/{org_id}/members",
    response_model=list[OrganisationMemberRead],
)
async def get_organisation_members_internal(
    org_id: int,
    service: OrganisationService = Depends(get_organisation_service),
):
    return await service.get_org_members(org_id)
