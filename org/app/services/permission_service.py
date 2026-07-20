from shared.generic_crud import GenericCrud
from app.models.organisation import Permission, PermissionRoles, OrganisationMember, Role
from sqlalchemy.ext.asyncio import AsyncSession


ATTR_ROLES = ["ADMIN", "GUEST", "MODERATOR"]

class PermissionService(GenericCrud[Permission]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Permission)
        self.session = session



class RoleService(GenericCrud[Role]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Role)
        self.session = session


class PermissionRoleServ(GenericCrud[PermissionRoles]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, PermissionRoles)
        self.session = session


class OrganisationMemberService(GenericCrud[OrganisationMember]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, OrganisationMember)
        self.session = session