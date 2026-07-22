from app.repositories import (
    OrganisationRepository,
    OrganisationMemberRepository,
    InvitationRepository,
)
from fastapi import Depends, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import get_session
from app.schemas.roles import Role
from app.schemas.user import User
from app.get_user import get_current_user
from app.services.organisation_service import OrganisationService
from app.services.invitation_service import InvitationService


def get_organisation_repository(
    session: AsyncSession = Depends(get_session),
) -> OrganisationRepository:
    return OrganisationRepository(session)


def get_org_member_repository(
    session: AsyncSession = Depends(get_session),
) -> OrganisationMemberRepository:
    return OrganisationMemberRepository(session)


# apply sur repo
def get_organisation_service(
    session: AsyncSession = Depends(get_session),
    repo: OrganisationRepository = Depends(get_organisation_repository),
    member_repo: OrganisationMemberRepository = Depends(
        get_org_member_repository
    ),
) -> OrganisationService:

    return OrganisationService(
        session=session, repository=repo, member_repo=member_repo
    )


class RoleChecker:
    def __init__(self, allowed_roles: List[Role]) -> None:
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        org_id: int,
        get_user: User = Depends(get_current_user),
        user_repo: OrganisationMemberRepository = Depends(
            get_org_member_repository
        ),
    ):
        user_id = get_user.id
        user_roles = await user_repo.get_user_perm(user_id, org_id)
        if not user_roles or user_roles not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have necessary permission ",
            )
        return user_roles


required_admin_role = RoleChecker([Role.ADMIN])
required_editor_role = RoleChecker([Role.ADMIN, Role.EDITOR])
required_reader_role = RoleChecker([Role.ADMIN, Role.EDITOR, Role.READER])


def get_invitation_repository(
    session: AsyncSession = Depends(get_session),
) -> InvitationRepository:
    return InvitationRepository(session)


def get_invitation_service(
    session: AsyncSession = Depends(get_session),
    invitation_repo: InvitationRepository = Depends(get_invitation_repository),
    member_repo: OrganisationMemberRepository = Depends(
        get_org_member_repository
    ),
    org_repo: OrganisationRepository = Depends(get_organisation_repository),
) -> InvitationService:
    return InvitationService(
        session=session,
        invitation_repo=invitation_repo,
        member_repo=member_repo,
        org_repo=org_repo,
    )
