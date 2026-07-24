"""FastAPI dependencies: repositories, services and role guards."""

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
    """Provide an ``OrganisationRepository`` bound to the request session."""
    return OrganisationRepository(session)


def get_org_member_repository(
    session: AsyncSession = Depends(get_session),
) -> OrganisationMemberRepository:
    """Provide an ``OrganisationMemberRepository`` for the request."""
    return OrganisationMemberRepository(session)


def get_organisation_service(
    session: AsyncSession = Depends(get_session),
    repo: OrganisationRepository = Depends(get_organisation_repository),
    member_repo: OrganisationMemberRepository = Depends(
        get_org_member_repository
    ),
) -> OrganisationService:
    """Assemble the ``OrganisationService`` with its repositories."""
    return OrganisationService(
        session=session, repository=repo, member_repo=member_repo
    )


class RoleChecker:
    """Route dependency authorising a caller against allowed roles."""

    def __init__(self, allowed_roles: List[Role]) -> None:
        """Store the roles allowed to pass this check."""
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        org_id: int,
        get_user: User = Depends(get_current_user),
        user_repo: OrganisationMemberRepository = Depends(
            get_org_member_repository
        ),
    ) -> Role:
        """Authorise the caller for ``org_id``.

        Args:
            org_id: Organisation the caller is acting on.
            get_user: The authenticated user.
            user_repo: Repository used to read the caller's role.

        Returns:
            The caller's role within the organisation.

        Raises:
            HTTPException: ``403`` if the caller lacks an allowed role.
        """
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
    """Provide an ``InvitationRepository`` bound to the request session."""
    return InvitationRepository(session)


def get_invitation_service(
    session: AsyncSession = Depends(get_session),
    invitation_repo: InvitationRepository = Depends(get_invitation_repository),
    member_repo: OrganisationMemberRepository = Depends(
        get_org_member_repository
    ),
    org_repo: OrganisationRepository = Depends(get_organisation_repository),
) -> InvitationService:
    """Assemble the ``InvitationService`` with its repositories."""
    return InvitationService(
        session=session,
        invitation_repo=invitation_repo,
        member_repo=member_repo,
        org_repo=org_repo,
    )
