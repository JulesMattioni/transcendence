"""Internal, service-to-service router (not exposed through the gateway)."""

from fastapi import APIRouter, Depends
from app.models.organisation import OrganisationMember
from app.schemas.organisation import OrganisationMemberRead
from app.dependancies import (
    get_organisation_service,
    get_org_member_repository,
)
from app.services.organisation_service import OrganisationService
from app.repositories import OrganisationMemberRepository

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
) -> list[OrganisationMember]:
    """Return the members of an organisation for internal callers."""
    return await service.get_org_members(org_id)


@router.get("/organisations/{org_id}/members/{user_id}/role")
async def get_member_role_internal(
    org_id: int,
    user_id: int,
    member_repo: OrganisationMemberRepository = Depends(
        get_org_member_repository
    ),
) -> dict[str, int | None]:
    """Return the caller's role in an organisation for internal callers.

    Args:
        org_id: Organisation the role is looked up in.
        user_id: User whose role is requested.
        member_repo: Repository used to read the membership row.

    Returns:
        A mapping ``{"role_id": <int>}``, or ``{"role_id": None}`` when the
        user is not a member of the organisation.
    """
    role = await member_repo.get_user_perm(user_id, org_id)
    return {"role_id": role.value if role else None}
