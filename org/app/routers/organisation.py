from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.organisation import (
    OrganisationCreate,
    OrganisationRead,
    OrganisationUpdate
)
from app.dependancies import get_organisation_service, required_admin_role
from app.services.organisation_service import OrganisationService

router = APIRouter(
    prefix="/organisations",
    tags=["Organisations"],
)


@router.post("/", response_model=OrganisationRead,
             status_code=status.HTTP_201_CREATED)
async def create_organisation(data: OrganisationCreate,
                              service: OrganisationService = Depends(
                                  get_organisation_service)):
    new_org = await service.create_organisation(data.name)
    if not new_org:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Failed to create organisation")
    return new_org


@router.post("/{org_id}/users/{user_id}", status_code=status.HTTP_201_CREATED)
async def create_user_from_organisation(org_id: int, user_id: int,
                                        service: OrganisationService
                                        = Depends(get_organisation_service),
                                        _=Depends(required_admin_role)):
    create_user = await service.creatuser_from_org(org_id, user_id)
    if not create_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Create user failed")
    return create_user


@router.get("/{org_id}", response_model=OrganisationRead)
async def get_organisation_by_id(org_id: int,
                                 service: OrganisationService = Depends(
                                     get_organisation_service)):
    organisation = await service.get_org_by_id(org_id)
    if not organisation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Organisation not found")
    return organisation


@router.get("/users/{user_id}/organisations")
async def get_user_organisation_endpoint(user_id: int,
                                         service: OrganisationService
                                         = Depends(get_organisation_service)):
    return await service.get_user_organisation_endpoint(user_id)


@router.patch("/{org_id}", response_model=OrganisationRead)
async def edit_organisation(org_id: int,
                            data_updated: OrganisationUpdate,
                            service: OrganisationService = Depends
                            (
                                get_organisation_service
                            ),
                            _=Depends(required_admin_role)):
    update = await service.update_organisation(org_id, data_updated)
    if not update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Organisation not found")
    return update


@router.patch("/{org_id}/users/{user_id}")
async def update_permission_member(org_id: int, user_id: int, new_role: int,
                                   service: OrganisationService
                                   = Depends(get_organisation_service),
                                   _=Depends(required_admin_role)):
    update_role = await service.update_perm_from_organisation(org_id,
                                                              user_id,
                                                              new_role)
    if not update_role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User Not found")
    return update_role


@router.delete("/{org_id}/users/{user_id}",
               status_code=status.HTTP_204_NO_CONTENT)
async def del_user_from_organisation(org_id: int,
                                     user_id: int,
                                     service: OrganisationService
                                     = Depends(get_organisation_service),
                                     _=Depends(required_admin_role)):
    deleted_user = await service.delete_user_from_org(org_id, user_id)
    if not deleted_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")
    return deleted_user


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organisation(
    org_id: int,
    service: OrganisationService = Depends(get_organisation_service),
    _=Depends(
        required_admin_role)):
    deleted = await service.delete_organisation(org_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Organisation not found")
    return deleted
