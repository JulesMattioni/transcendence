from sqlalchemy.ext.asyncio import AsyncSession
from shared.base_service import BaseService
from app.repositories import (
    InvitationRepository,
    OrganisationMemberRepository,
    OrganisationRepository,
)
from app.schemas.organisation import InvitationRead
from app.get_user import lookup_user_by_email
from app.exceptions import (
    OrganisationNotFoundError,
    AlreadyMemberError,
    InvitationAlreadyExistsError,
    InvitationNotFoundError,
)


class InvitationService(BaseService):
    def __init__(
        self,
        session: AsyncSession,
        invitation_repo: InvitationRepository,
        member_repo: OrganisationMemberRepository,
        org_repo: OrganisationRepository,
    ) -> None:
        super().__init__()
        self.session = session
        self.invitation_repo = invitation_repo
        self.member_repo = member_repo
        self.org_repo = org_repo

    async def invite(
        self,
        org_id: int,
        email: str,
        role_id: int,
        invited_by: int,
        authorization: str,
    ) -> InvitationRead:
        # 1. l'org existe ?
        org = await self.org_repo.get_by_id(org_id)
        if not org:
            raise OrganisationNotFoundError()

        user = await lookup_user_by_email(email, authorization)
        invited_user_id = user["id"]

        is_member = (
            await self.member_repo.get_user_perm(invited_user_id, org_id)
            is not None
        )
        if is_member:
            raise AlreadyMemberError()

        if await self.invitation_repo.pending_exists(org_id, invited_user_id):
            raise InvitationAlreadyExistsError()

        try:
            invitation = await self.invitation_repo.create(
                org_id=org_id,
                invited_user_id=invited_user_id,
                email=user["email"],
                first_name=user.get("first_name"),
                last_name=user.get("last_name"),
                role_id=role_id,
                invited_by=invited_by,
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        return InvitationRead.model_validate(invitation)

    async def list_for_org(self, org_id: int) -> list[InvitationRead]:
        invitations = await self.invitation_repo.list_by_org(org_id)
        return [InvitationRead.model_validate(i) for i in invitations]

    async def list_my_pending(self, user_id: int) -> list[InvitationRead]:
        invitations = await self.invitation_repo.list_pending_for_user(user_id)
        return [InvitationRead.model_validate(i) for i in invitations]

    async def accept(self, invitation_id: int, user_id: int) -> InvitationRead:
        invitation = await self.invitation_repo.get_by_id(invitation_id)
        if not invitation or invitation.invited_user_id != user_id:
            raise InvitationNotFoundError()
        if invitation.status != "pending":
            raise InvitationNotFoundError()

        try:
            await self.member_repo.create_user_from_org(
                org_id=invitation.org_id,
                user_id=invitation.invited_user_id,
                role_id=invitation.role_id,
                email=invitation.email,
                first_name=invitation.first_name,
                last_name=invitation.last_name,
            )
            await self.invitation_repo.set_status(invitation, "accepted")
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        return InvitationRead.model_validate(invitation)

    async def decline(
        self, invitation_id: int, user_id: int
    ) -> InvitationRead:
        invitation = await self.invitation_repo.get_by_id(invitation_id)
        if not invitation or invitation.invited_user_id != user_id:
            raise InvitationNotFoundError()
        if invitation.status != "pending":
            raise InvitationNotFoundError()

        try:
            await self.invitation_repo.set_status(invitation, "declined")
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        return InvitationRead.model_validate(invitation)
