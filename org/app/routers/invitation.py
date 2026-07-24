"""Invitation endpoints: issue, list, accept and decline invitations."""

from fastapi import APIRouter, status, Depends, Header
from typing import Annotated
from app.schemas.organisation import InvitationCreate, InvitationRead
from app.schemas.roles import Role
from app.schemas.user import User
from app.dependancies import (
    get_invitation_service,
    get_current_user,
    required_admin_role,
)
from app.services.invitation_service import InvitationService

router = APIRouter(tags=["Invitations"])


@router.post(
    "/organisations/{org_id}/invitations",
    response_model=InvitationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_invitation(
    org_id: int,
    data: InvitationCreate,
    authorization: Annotated[str, Header()],
    user: User = Depends(get_current_user),
    service: InvitationService = Depends(get_invitation_service),
    _: Role = Depends(required_admin_role),
) -> InvitationRead:
    """Invite a user to an organisation (admin only)."""
    return await service.invite(
        org_id=org_id,
        email=data.email,
        role_id=data.role_id,
        invited_by=user.id,
        authorization=authorization,
    )


@router.get(
    "/organisations/{org_id}/invitations",
    response_model=list[InvitationRead],
)
async def list_org_invitations(
    org_id: int,
    service: InvitationService = Depends(get_invitation_service),
    _: Role = Depends(required_admin_role),
) -> list[InvitationRead]:
    """List every invitation of an organisation (admin only)."""
    return await service.list_for_org(org_id)


@router.get("/invitations/me", response_model=list[InvitationRead])
async def list_my_invitations(
    user: User = Depends(get_current_user),
    service: InvitationService = Depends(get_invitation_service),
) -> list[InvitationRead]:
    """List the caller's pending invitations."""
    return await service.list_my_pending(user.id)


@router.post(
    "/invitations/{invitation_id}/accept", response_model=InvitationRead
)
async def accept_invitation(
    invitation_id: int,
    user: User = Depends(get_current_user),
    service: InvitationService = Depends(get_invitation_service),
) -> InvitationRead:
    """Accept one of the caller's pending invitations."""
    return await service.accept(invitation_id, user.id)


@router.post(
    "/invitations/{invitation_id}/decline", response_model=InvitationRead
)
async def decline_invitation(
    invitation_id: int,
    user: User = Depends(get_current_user),
    service: InvitationService = Depends(get_invitation_service),
) -> InvitationRead:
    """Decline one of the caller's pending invitations."""
    return await service.decline(invitation_id, user.id)
