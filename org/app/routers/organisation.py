"""Organisation endpoints: CRUD and membership management."""

from typing import Any
from fastapi import APIRouter, status, Depends
from app.models.organisation import Organisation, OrganisationMember
from app.schemas.organisation import (
    OrganisationCreate,
    OrganisationRead,
    OrganisationUpdate,
    OrganisationMemberRead,
)
from app.schemas.roles import Role
from app.schemas.user import User
from app.dependancies import (
    get_organisation_service,
    get_current_user,
    required_admin_role,
    required_reader_role,
)
from app.services.organisation_service import OrganisationService

router = APIRouter(
    prefix="/organisations",
    tags=["Organisations"],
)


@router.post(
    "/", response_model=OrganisationRead, status_code=status.HTTP_201_CREATED
)
async def create_organisation(
    data: OrganisationCreate,
    user_id: User = Depends(get_current_user),
    service: OrganisationService = Depends(get_organisation_service),
) -> OrganisationRead:
    """Create an organisation; the caller becomes its first admin."""
    new_org = await service.create_organisation(
        data.name,
        user_id=user_id.id,
        email=user_id.email,
        first_name=user_id.first_name,
        last_name=user_id.last_name,
    )

    return new_org


@router.post(
    "/{org_id}/users/{user_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=None,
)
async def create_user_from_organisation(
    org_id: int,
    user_id: int,
    role_id: int,
    service: OrganisationService = Depends(get_organisation_service),
    _: Role = Depends(required_admin_role),
) -> OrganisationMember:
    """Add a user to an organisation with a role (admin only)."""
    create_user = await service.create_user_from_org(org_id, user_id, role_id)
    return create_user


@router.get("/{org_id}", response_model=OrganisationRead)
async def get_organisation_by_id(
    org_id: int,
    service: OrganisationService = Depends(get_organisation_service),
) -> Organisation:
    """Return an organisation by id."""
    organisation = await service.get_org_by_id(org_id)
    return organisation


@router.get("/{org_id}/users", response_model=list[OrganisationMemberRead])
async def get_organisation_members(
    org_id: int,
    service: OrganisationService = Depends(get_organisation_service),
    _: Role = Depends(required_reader_role),
) -> list[OrganisationMember]:
    """List the members of an organisation (reader and above)."""
    return await service.get_org_members(org_id)


@router.get("/users/{user_id}/organisations")
async def get_user_organisation_endpoint(
    user_id: int,
    service: OrganisationService = Depends(get_organisation_service),
) -> dict[str, Any]:
    """Return the organisations a user belongs to and their roles."""
    return await service.get_user_organisation_endpoint(user_id)


@router.patch("/{org_id}", response_model=OrganisationRead)
async def edit_organisation(
    org_id: int,
    data_updated: OrganisationUpdate,
    service: OrganisationService = Depends(get_organisation_service),
    _: Role = Depends(required_admin_role),
) -> OrganisationRead | None:
    """Update an organisation (admin only)."""
    return await service.update_organisation(org_id, data_updated)


@router.patch("/{org_id}/users/{user_id}")
async def update_permission_member(
    org_id: int,
    user_id: int,
    new_role: int,
    service: OrganisationService = Depends(get_organisation_service),
    _: Role = Depends(required_admin_role),
) -> bool:
    """Change a member's role within an organisation (admin only)."""
    update_role = await service.update_perm_from_organisation(
        org_id, user_id, new_role
    )
    return update_role


@router.delete(
    "/{org_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def del_user_from_organisation(
    org_id: int,
    user_id: int,
    service: OrganisationService = Depends(get_organisation_service),
    _: Role = Depends(required_admin_role),
) -> None:
    """Remove a member from an organisation (admin only)."""
    await service.delete_user_from_org(org_id, user_id)
    return None


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organisation(
    org_id: int,
    service: OrganisationService = Depends(get_organisation_service),
    _: Role = Depends(required_admin_role),
) -> None:
    """Delete an organisation (admin only)."""
    await service.delete_organisation(org_id)
    return None
