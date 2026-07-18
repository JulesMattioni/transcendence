from sqlalchemy.ext.asyncio import AsyncSession
from app.models.organisation import Organisation
from shared.generic_crud import GenericCrud

# Create, edit, and delete organizations
# GenericCrud[T] == GenericCrud[Organisation] self.model == class Organisation


class OrganisationSerive(GenericCrud[Organisation]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Organisation)
        self.session = session

    async def create_organisation(self, org_name: str) -> Organisation:
        new_org = Organisation(name=org_name)
        await self.create(new_org)
        await self.session.commit()
        return new_org

    async def edit_org(self, org_id: int, org_name: str):
        update_org = await self.update(org_id, {"name", org_name})
        await self.session.commit()
        return update_org

    async def delete_org(self, org_id: int) -> bool:
        succes = await self.delete(org_id)
        if succes:
            await self.session.commit()
            return True
        return False
