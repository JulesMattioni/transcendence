from shared.base_service import BaseService
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.organisation import OrganisationMember, Organisation

# Roles management (admin, user, guest, moderator, etc.)
# add users to organizations
# Remove users from organizations.
# View organizations

class RoleManagment(BaseService):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_member_to_org(self, org_id: int, user_id: int, roles: str):
        attr_roles = ["ADMIN", "GUEST", "MODERATOR"]
        if roles not in attr_roles:
            raise ValueError('Error Role is unvalid')

        new_member = OrganisationMember(
            org_id=org_id,
            user_id=user_id,
            roles=roles
        )
        self.session.add(new_member)
        await self.session.commit()
        return new_member

    async def remove_member():
        pass

    async def update_perm():
        pass

    async def view_from_org():
        pass
