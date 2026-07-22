from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.organisation import Invitation


class InvitationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        org_id: int,
        invited_user_id: int,
        email: str,
        first_name: str | None,
        last_name: str | None,
        role_id: int,
        invited_by: int,
    ) -> Invitation:
        invitation = Invitation(
            org_id=org_id,
            invited_user_id=invited_user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role_id=role_id,
            status="pending",
            invited_by=invited_by,
        )
        self._session.add(invitation)
        await self._session.flush()
        return invitation

    async def get_by_id(self, invitation_id: int) -> Invitation | None:
        return await self._session.get(Invitation, invitation_id)

    async def list_by_org(self, org_id: int) -> list[Invitation]:
        stmt = select(Invitation).where(Invitation.org_id == org_id)
        res = await self._session.execute(stmt)
        return list(res.scalars().all())

    async def list_pending_for_user(self, user_id: int) -> list[Invitation]:
        stmt = select(Invitation).where(
            Invitation.invited_user_id == user_id,
            Invitation.status == "pending",
        )
        res = await self._session.execute(stmt)
        return list(res.scalars().all())

    async def set_status(
        self, invitation: Invitation, status: str
    ) -> Invitation:
        invitation.status = status
        await self._session.flush()
        return invitation

    async def pending_exists(self, org_id: int, invited_user_id: int) -> bool:
        stmt = select(Invitation.id).where(
            Invitation.org_id == org_id,
            Invitation.invited_user_id == invited_user_id,
            Invitation.status == "pending",
        )
        res = await self._session.execute(stmt)
        return res.scalar_one_or_none() is not None
