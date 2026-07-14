from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: int) -> User | None:
        user = await self._session.get(User, id)

        return user
