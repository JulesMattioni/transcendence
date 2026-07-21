from sqlalchemy.ext.asyncio import AsyncSession
from shared.base_service import BaseService
from app.repositories.organisation_repository import OrganisationRepository
from app.schemas.organisation import OrganisationRead, OrganisationUpdate


class OrganisationService(BaseService):
    def __init__(self, repository: OrganisationRepository,
                 session: AsyncSession) -> None:
        super().__init__()
        self.repository = repository
        self.session = session

    async def create_organisation(self, org_name: str) -> OrganisationRead:
        new_org = await self.repository.create(name_org=org_name)
        await self.session.commit()
        return OrganisationRead.model_validate(new_org)

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
