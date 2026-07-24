"""Business logic for organisations and their members."""

from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from shared.base_service import BaseService
from app.models.organisation import Organisation, OrganisationMember
from app.repositories.organisation_repository import OrganisationRepository
from app.schemas.organisation import OrganisationRead, OrganisationUpdate
from app.repositories import OrganisationMemberRepository
from app.exceptions import (
    OrgnisationCreationError,
    UserNotInOrganisationError,
    OrganisationNotFoundError,
)


class OrganisationService(BaseService):
    """Orchestrate organisation and membership operations."""

    def __init__(
        self,
        repository: OrganisationRepository,
        session: AsyncSession,
        member_repo: OrganisationMemberRepository,
    ) -> None:
        """Store the session and the organisation/member repositories."""
        super().__init__()
        self.repository = repository
        self.session = session
        self.member_repo = member_repo

    async def create_organisation(
        self,
        org_name: str,
        user_id: int,
        email: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> OrganisationRead:
        """Create an organisation and add its creator as admin.

        Args:
            org_name: Name of the new organisation.
            user_id: Creator, registered as the first admin member.
            email: Creator email stored on the membership row.
            first_name: Creator first name stored on the membership row.
            last_name: Creator last name stored on the membership row.

        Returns:
            The created organisation.

        Raises:
            OrgnisationCreationError: If the organisation could not be
                created.
        """
        new_org = await self.repository.create_organisation(name_org=org_name)
        if not new_org:
            raise OrgnisationCreationError()

        await self.member_repo.create_user_from_org(
            org_id=new_org.id,
            user_id=user_id,
            role_id=1,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        await self.session.commit()
        return OrganisationRead.model_validate(new_org)

    async def create_user_from_org(
        self, org_id: int, user_id: int, role_id: int
    ) -> OrganisationMember:
        """Add a member to an organisation with the given role."""
        add_member = await self.member_repo.create_user_from_org(
            org_id=org_id, user_id=user_id, role_id=role_id
        )
        if not add_member:
            raise UserNotInOrganisationError()

        await self.session.commit()
        return add_member

    async def delete_user_from_org(self, org_id: int, user_id: int) -> bool:
        """Remove a member from an organisation.

        Raises:
            UserNotInOrganisationError: If the member does not exist.
        """
        delete_user = await self.member_repo.delete_user_from_org(
            org_id, user_id
        )
        if not delete_user:
            raise UserNotInOrganisationError()

        await self.session.commit()
        return delete_user

    async def get_org_by_id(self, org_id: int) -> Organisation:
        """Return an organisation by id.

        Raises:
            OrganisationNotFoundError: If the organisation does not exist.
        """
        organisation = await self.repository.get_by_id(org_id)
        if not organisation:
            raise OrganisationNotFoundError()

        return organisation

    async def update_organisation(
        self, org_id: int, update_org: OrganisationUpdate
    ) -> OrganisationRead | None:
        """Update an organisation and return its new representation.

        Raises:
            OrganisationNotFoundError: If the organisation does not exist.
        """
        update = await self.repository.update(org_id, update_org)
        if not update:
            raise OrganisationNotFoundError()

        await self.session.commit()
        return OrganisationRead.model_validate(update)

    async def delete_organisation(self, org_id: int) -> bool:
        """Delete an organisation.

        Raises:
            OrganisationNotFoundError: If the organisation does not exist.
        """
        organisation = await self.repository.delete_org(org_id)
        if not organisation:
            raise OrganisationNotFoundError()

        await self.session.commit()
        return organisation

    async def update_perm_from_organisation(
        self, org_id: int, user_id: int, new_role_id: int
    ) -> bool:
        """Change a member's role within an organisation.

        Raises:
            UserNotInOrganisationError: If the member does not exist.
        """
        new_role = await self.member_repo.update_role(
            org_id, user_id, new_role_id
        )
        if not new_role:
            raise UserNotInOrganisationError()

        await self.session.commit()
        return new_role

    async def get_user_organisation_endpoint(
        self, user_id: int
    ) -> Dict[str, Any]:
        """Return the organisations a user belongs to and their roles."""
        return await self.member_repo.get_user_organisation_format(user_id)

    async def get_org_members(
        self, org_id: int
    ) -> list[OrganisationMember]:
        """Return the members of an organisation.

        Raises:
            OrganisationNotFoundError: If the organisation does not exist.
        """
        organisation = await self.repository.get_by_id(org_id)
        if not organisation:
            raise OrganisationNotFoundError()
        return await self.member_repo.get_org_members(org_id)
