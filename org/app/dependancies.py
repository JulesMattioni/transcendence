from app.repositories import (
    OrganisationRepository,
    OrganisationMemberRepository
)
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import get_session
from app.schemas.roles import Role
from typing import List, Annotated
from app.schemas.user import User
from app.config import AUTH_BASE_URL
import httpx


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="missing header"
        )
    auth_url = f"{AUTH_BASE_URL}/auth/me"
    header = {"Authorization": authorization}
    async with httpx.AsyncClient() as client:
        response = await client.get(auth_url, headers=header)
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        user_data = response.json()
        return User.model_validate(user_data)


def get_organisation(
    session: AsyncSession = Depends(get_session),
) -> OrganisationRepository:
    return OrganisationRepository(session)


def get_org_member_repository(
    session: AsyncSession = Depends(get_session),
) -> OrganisationMemberRepository:
    return OrganisationMemberRepository(session)


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
