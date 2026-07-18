from sqlalchemy.ext.asyncio import AsyncSession
from app.models.organisation import Organisation

# Roles management (admin, user, guest, moderator, etc.)
# add users to organizations
# Remove users from organizations.
# View organizations


ATRR_ROLES = ["ADMIN", "GUEST", "MODERATOR"]


class MembershipRole:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_user_to_org(self, org_id: int,
                              user_id: int, roles: str) -> Organisation:
        if roles not in ATRR_ROLES:
            raise ValueError('Error Role is unvalid')

    async def remove_user_from_org():
        pass

    async def update_perm_from_org():
        pass

    async def view_from_org():
        pass
