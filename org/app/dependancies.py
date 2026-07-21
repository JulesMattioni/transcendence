from app.repositories import (
    OrganisationRepository,
    OrganisationMemberRepository
)
from fastapi import Depends, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import get_session
from app.schemas.roles import Role
from app.schemas.user import User
from get_user import get_current_user
from app.services.organisation_service import OrganisationService


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
        repo:
        OrganisationRepository = Depends(
                                 get_organisation_repository
                                 )) -> OrganisationService:
    return OrganisationService(repo)


class RoleChecker:
    def __init__(self, allowed_roles: List[Role]) -> None:
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        org_id: int,
        get_user: User = Depends(get_current_user),
        user_repo:
        OrganisationMemberRepository = Depends(get_org_member_repository),
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
required_member = RoleChecker([Role.GUEST])
required_modo_role = RoleChecker([Role.MODERATOR])
