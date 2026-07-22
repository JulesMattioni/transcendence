from fastapi import APIRouter, status, Depends
from app.schemas.organisation import (
    OrganisationCreate,
    OrganisationRead,
    OrganisationUpdate,
    OrganisationMemberRead,
)
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
    user_id=Depends(get_current_user),
    service: OrganisationService = Depends(get_organisation_service),
):
    new_org = await service.create_organisation(data.name, user_id=user_id.id)

    return new_org


@router.post("/{org_id}/users/{user_id}", status_code=status.HTTP_201_CREATED)
async def create_user_from_organisation(
    org_id: int,
    user_id: int,
    role_id: int,
    service: OrganisationService = Depends(get_organisation_service),
    _=Depends(required_admin_role),
):
    create_user = await service.create_user_from_org(org_id, user_id, role_id)
    return create_user


@router.get("/{org_id}", response_model=OrganisationRead)
async def get_organisation_by_id(
    org_id: int,
    service: OrganisationService = Depends(get_organisation_service),
):
    organisation = await service.get_org_by_id(org_id)
    return organisation


@router.get("/{org_id}/users", response_model=list[OrganisationMemberRead])
async def get_organisation_members(
    org_id: int,
    service: OrganisationService = Depends(get_organisation_service),
    _=Depends(required_reader_role),
):
    return await service.get_org_members(org_id)


@router.get("/users/{user_id}/organisations")
async def get_user_organisation_endpoint(
    user_id: int,
    service: OrganisationService = Depends(get_organisation_service),
):
    return await service.get_user_organisation_endpoint(user_id)


@router.get("/users/{user_id}/{org_id}")
async def get_organisation_read(org_id: int, user_id: int, role_id: int,
                                service: OrganisationService
                                = Depends(get_organisation_service)):
    return await service.organisation_member_read(
        org_id,
        user_id,
        role_id
    )


@router.patch("/{org_id}", response_model=OrganisationRead)
async def edit_organisation(
    org_id: int,
    data_updated: OrganisationUpdate,
    service: OrganisationService = Depends(get_organisation_service),
    _=Depends(required_admin_role),
):
    return await service.update_organisation(org_id, data_updated)


@router.patch("/{org_id}/users/{user_id}")
async def update_permission_member(
    org_id: int,
    user_id: int,
    new_role: int,
    service: OrganisationService = Depends(get_organisation_service),
    _=Depends(required_admin_role),
):
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
    _=Depends(required_admin_role),
):
    await service.delete_user_from_org(org_id, user_id)
    return None


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organisation(
    org_id: int,
    service: OrganisationService = Depends(get_organisation_service),
    _=Depends(required_admin_role),
):
    await service.delete_organisation(org_id)
    return None
