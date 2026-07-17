from shared.base_service import BaseService
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.organisation import Organisation, OrganisationMember
from typing import Dict, Any

# Create, edit, and delete organizations
class OrganisationSerive(BaseService):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_organisation(self, org_name: str,
                           user_id: int,
                           roles: str) -> Organisation:
        new_org = Organisation(name=org_name)
        self.session.add(new_org)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(new_org)
        return new_org

    async def edit_org(self):
        pass

    async def delete_org(self) -> bool:
        pass
