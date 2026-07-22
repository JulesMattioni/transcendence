from sqlalchemy.ext.asyncio import AsyncSession
from shared.base_service import BaseService
from app.repositories.organisation_repository import OrganisationRepository
from app.schemas.organisation import (OrganisationRead,
                                      OrganisationUpdate,
                                      OrganisationMemberRead)
from app.repositories import OrganisationMemberRepository
from app.exceptions import (
    OrgnisationCreationError,
    UserNotInOrganisationError,
    OrganisationNotFoundError,
)


class OrganisationService(BaseService):
    def __init__(self, repository: OrganisationRepository,
                 session: AsyncSession,
                 member_repo: OrganisationMemberRepository) -> None:
        super().__init__()
        self.repository = repository
        self.session = session
        self.member_repo = member_repo

    async def create_organisation(self, org_name: str, user_id: int
                                  ) -> OrganisationRead:
        new_org = await self.repository.create_organisation(name_org=org_name)
        if not new_org:
            raise OrgnisationCreationError()

        await self.member_repo.create_user_from_org(
            org_id=new_org.id,
            user_id=user_id,
            role_id=1  # admin !
        )
        await self.session.commit()
        return OrganisationRead.model_validate(new_org)

    async def create_user_from_org(self, org_id: int,
                                   user_id: int,
                                   role_id: int):
        add_member = await self.member_repo.create_user_from_org(
            org_id=org_id,
            user_id=user_id,
            role_id=role_id
        )
        if not add_member:
            raise UserNotInOrganisationError()

        await self.session.commit()
        return add_member

    async def delete_user_from_org(self, org_id: int, user_id: int):
        delete_user = await self.member_repo.delete_user_from_org(
            org_id, user_id)
        if not delete_user:
            raise UserNotInOrganisationError()

        await self.session.commit()
        return delete_user

    async def get_org_by_id(self, org_id: int) -> OrganisationRead:
        organisation = await self.repository.get_by_id(org_id)
        if not organisation:
            raise OrganisationNotFoundError()

        return organisation

    async def update_organisation(self, org_id: int,
                                  update_org: OrganisationUpdate
                                  ) -> OrganisationRead | None:
        update = await self.repository.update(org_id, update_org)
        if not update:
            raise OrganisationNotFoundError()

        await self.session.commit()
        return OrganisationRead.model_validate(update)

    async def delete_organisation(self, org_id: int):
        organisation = await self.repository.delete_org(org_id)
        if not organisation:
            raise OrganisationNotFoundError()

        await self.session.commit()
        return organisation

    async def update_perm_from_organisation(self, org_id: int,
                                            user_id: int,
                                            new_role_id: int):
        new_role = await self.member_repo.update_role(org_id,
                                                      user_id,
                                                      new_role_id)
        if not new_role:
            raise UserNotInOrganisationError()

        await self.session.commit()
        return new_role

    async def get_user_organisation_endpoint(self, user_id: int):
        return await self.member_repo.get_user_organisation_format(user_id)

    async def organisation_member_read(self,
                                       org_id: int,
                                       user_id: int,
                                       role_id: int
                                       ) -> OrganisationMemberRead:
        return await self.member_repo.get_organisation_read(org_id,
                                                            user_id,
                                                            role_id)
