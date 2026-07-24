"""Data access for organisation members and their roles."""

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.organisation import OrganisationMember
from app.models.organisation import Organisation
from sqlalchemy import select
from app.schemas.roles import Role
from typing import Dict, Any


class OrganisationMemberRepository:
    """Persist and query :class:`OrganisationMember` rows."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the repository to a database session."""
        self._session = session

    async def create_user_from_org(
        self,
        org_id: int,
        user_id: int,
        role_id: int,
        email: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> OrganisationMember:
        """Add a member to an organisation and return the created row."""
        new_member = OrganisationMember(
            org_id=org_id,
            user_id=user_id,
            role_id=role_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        self._session.add(new_member)
        await self._session.flush()
        return new_member

    async def delete_user_from_org(self, org_id: int, user_id: int) -> bool:
        """Remove a member; return ``True`` if one was removed."""
        stmt = select(OrganisationMember).where(
            OrganisationMember.user_id == user_id,
            OrganisationMember.org_id == org_id,
        )
        res = await self._session.execute(stmt)
        member = res.scalar_one_or_none()
        if member:
            await self._session.delete(member)
            await self._session.flush()
            return True
        return False

    async def get_user_perm(self, user_id: int, org_id: int) -> Role | None:
        """Return the member's role in the organisation, or ``None``."""
        stmt = select(OrganisationMember.role_id).where(
            OrganisationMember.user_id == user_id,
            OrganisationMember.org_id == org_id,
        )
        res = await self._session.execute(stmt)
        role_id = res.scalar_one_or_none()
        if role_id:
            return Role(role_id)
        return None

    async def update_role(
        self, org_id: int, user_id: int, new_role_id: int
    ) -> bool:
        """Set a member's role; return ``True`` if the member exists."""
        stmt = select(OrganisationMember).where(
            OrganisationMember.org_id == org_id,
            OrganisationMember.user_id == user_id,
        )
        res = await self._session.execute(stmt)
        new_role = res.scalar_one_or_none()
        if new_role:
            new_role.role_id = new_role_id
            await self._session.flush()
            return True
        return False

    async def get_user_organisation_format(
        self, user_id: int
    ) -> Dict[str, Any]:
        """Return the user's organisations and role in each.

        Args:
            user_id: User whose memberships are listed.

        Returns:
            A mapping ``{"user_id": ..., "organisation": [...]}`` where each
            entry holds ``org_id``, ``name`` and ``role``.
        """
        stmt = (
            select(Organisation, OrganisationMember.role_id)
            .join(
                OrganisationMember,
                Organisation.id == OrganisationMember.org_id,
            )
            .where(OrganisationMember.user_id == user_id)
        )
        res = await self._session.execute(stmt)
        org_list = []
        for org, role_id in res.all():
            org_list.append(
                {"org_id": org.id, "name": org.name, "role": role_id}
            )
        return {"user_id": user_id, "organisation": org_list}

    async def get_org_members(self, org_id: int) -> list[OrganisationMember]:
        """Return every member of the organisation."""
        stmt = select(OrganisationMember).where(
            OrganisationMember.org_id == org_id
        )
        res = await self._session.execute(stmt)
        return list(res.scalars().all())
