from sqlalchemy.ext.asyncio import AsyncSession
from shared.base_service import BaseService
from app.repositories.organisation_repository import OrganisationRepository
from app.schemas.organisation import OrganisationRead, OrganisationUpdate
from app.repositories import OrganisationMemberRepository


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
        new_org = await self.repository.create(name_org=org_name)

        await self.member_repo.create_user_from_org(
            org_id=new_org.id,
            user_id=user_id,
            role_id=1  # admin !
        )
        await self.session.commit()
        return OrganisationRead.model_validate(new_org)

    async def creatuser_from_org(self, org_id: int, user_id: int, role_id: int):
        add_member = await self.member_repo.create_user_from_org(
            org_id=org_id,
            user_id=user_id,
            role_id=role_id
        )
        await self.session.commit()
        return add_member

    async def delete_user_from_org(self, org_id: int, user_id: int):
        delete_user = await self.member_repo.delete_user_from_org(
            org_id, user_id)
        if delete_user:
            await self.session.commit()
        return delete_user

    async def get_org_by_id(self, org_id: int) -> OrganisationRead | None:
        organisation = await self.repository.get_by_id(org_id)
        if organisation:
            return OrganisationRead.model_validate(organisation)
        return None

    async def update_organisation(self, org_id: str,
                                  update_org: OrganisationUpdate
                                  ) -> OrganisationRead | None:
        update = await self.repository.update(org_id, update_org)
        if not update:
            return None
        await self.session.commit()
        return OrganisationRead.model_validate(update)

    async def delete_organisation(self, org_id: int) -> bool:
        organisation = await self.repository.delete_org(org_id)
        if organisation:
            await self.session.commit()
            return True
        return False

    async def get_user_organisation_endpoint(self, user_id: int):
        return await self.member_repo.get_user_organisation_format(user_id)
