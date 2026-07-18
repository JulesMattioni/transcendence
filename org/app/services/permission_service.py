from shared.generic_crud import GenericCrud
from app.models.organisation import Permission
from sqlalchemy.ext.asyncio import AsyncSession


class PermService(GenericCrud[Permission]):
    def __init__(self, session: AsyncSession):
        super .__init__(session, Permission)
        self.session = session
