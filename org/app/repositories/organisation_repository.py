from sqlalchemy.ext.asyncio import AsyncSession
from app.models.organisation import Organisation
from app.schemas.organisation import OrganisationUpdate


class OrganisationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, name_org: str):
        new_org = Organisation(name_org)
        self.session.add(new_org)
        await self.session.flush()
        return new_org

    async def get_by_id(self, org_id: int):
        return await self.session.get(Organisation, org_id)

    async def update(self, org_id: int,
                     table_data: OrganisationUpdate) -> Organisation:
        organisation = await self.get_by_id(org_id)
        if organisation:
            update_dict = table_data.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                if hasattr(organisation, key):
                    setattr(organisation, key, value)
            await self.session.flush()
            return organisation

    async def delete_org(self, org_id: int) -> bool:
        organisation = await self.get_by_id(org_id)
        if organisation:
            await self.session.delete(organisation)
            await self.session.flush()
            return True
        return False
