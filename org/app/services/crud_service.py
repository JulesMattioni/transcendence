from auth.app.repositories.user_repository import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession
from shared.base_service import BaseService
from auth.app.models.auth import User
from typing import Dict, Any

# View, edit, and delete users (CRUD).
# "Advanced permissions system" into auth


class CrudUser(BaseService):
    def __init__(self, service_name: str, session: AsyncSession) -> None:
        super().__init__()
        self._service_name = service_name
        self.session = session
        self.user_repository = UserRepository(session)

    def check_service(self) -> dict[str, str]:
        return {"status": "ok", "service": self._service_name}

    async def create_user(self, user_table: Dict[str, Any]) -> User:
        user = await self.user_repository.create_user(
            first_name=user_table["first_name"],
            last_name=user_table["last_name"],
            email=user_table["email"],
            hashed_password=user_table["hashed_password"]
        )
        await self.session.commit()
        return user

    async def read_from_user(self, user_id: int):
        return await self.user_repository.get_by_id(user_id)

    async def update_from_user(self, user_id: int,
                               user_table: Dict[str, Any]) -> User | None:
        user = await self.user_repository.get_by_id(user_id)

        if not user:
            return None
        for key, value in user_table.items():
            if hasattr(user, key):
                setattr(user, key, value)

        await self.session.commit()
        return user

    async def delete_from_user(self, user_id: int) -> bool:
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return False
        await self.session.delete(user)
        await self.session.commit()
        return True
