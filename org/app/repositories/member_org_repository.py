from sqlalchemy.ext.asyncio import AsyncSession
from app.models.organisation import OrganisationMember
from app.models.organisation import Organisation
from sqlalchemy import select
from app.schemas.roles import Role
from typing import Dict, Any


class OrganisationMemberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_user_from_org(self, org_id: int, user_id: int,
                                   role_id: int) -> OrganisationMember:
        new_member = OrganisationMember(
            org_id=org_id,
            user_id=user_id,
            role_id=role_id
        )
        self._session.add(new_member)
        await self._session.flush()
        return new_member

    async def delete_user_from_org(self, org_id, user_id: int) -> bool:
        stmt = select(OrganisationMember).where(
            OrganisationMember.user_id == user_id,
            OrganisationMember.org_id == org_id
        )
        res = await self._session.execute(stmt)
        member = res.scalar_one_or_none()
        if member:
            await self._session.delete(member)
            await self._session.flush()
            return True
        return False

    async def get_user_perm(self, user_id: int, org_id: int) -> Role | None:
        stmt = select(OrganisationMember.role_id).where(
            OrganisationMember.user_id == user_id,
            OrganisationMember.org_id == org_id
        )
        res = await self._session.execute(stmt)
        role_id = res.scalar_one_or_none()
        if role_id:
            return Role(role_id)
        return None

    async def update_role(self, org_id: int,
                          user_id: int,
                          new_role_id: int) -> bool:
        stmt = (
            select(OrganisationMember).where(
                OrganisationMember.org_id == org_id,
                OrganisationMember.user_id == user_id
            )
        )
        res = await self._session.execute(stmt)
        new_role = res.scalar_one_or_none()
        if new_role:
            new_role.role_id = new_role_id
            await self._session.flush()
            return True
        return False

    async def get_user_organisation_format(self, user_id: int
                                           ) -> Dict[str, Any]:
        stmt = (
            select(Organisation, OrganisationMember.role_id)
            .join(OrganisationMember,
                  Organisation.id == OrganisationMember.org_id)
            .where(OrganisationMember.user_id == user_id)
        )
        res = await self._session.execute(stmt)
        org_list = []
        for org, role_id in res.all():
            org_list.append({
                "org_id": org.id,
                "name": org.name_org,
                "role": role_id
            })
        return {
            "user_id": user_id,
            "organisation": org_list
        }
