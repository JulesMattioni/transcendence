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
    return new_org


@router.get("/{org_id}", response_model=OrganisationRead)
async def get_organisation_by_id(org_id: int,
                                 service: OrganisationService = Depends(
                                     get_organisation_service)):
    organisation = await service.get_org_by_id(org_id)
    if not organisation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Organisation not found")
    return organisation


@router.get("/users/{user_id}/organisations", response_model=OrganisationRead)
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


@router.delete("/{org_id}", status_code=status.HTTP_404_NOT_FOUND)
async def del_user_from_organisation(org_id: int,
                                     user_id: int,
                                     service: OrganisationService
                                     = Depends(get_organisation_service)):
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
