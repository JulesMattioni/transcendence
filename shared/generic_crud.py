from sqlalchemy.ext.asyncio import AsyncSession
from typing import TypeVar, Type, Optional, Any, Dict, Generic
from shared.database import Base


type_model = TypeVar('T', bound=Base)


class GenericCrud(Generic[type_model]):
    def __init__(self, session: AsyncSession, model: Type[type_model]) -> None:
        self.session = session
        self.model = model

    async def create(self, instance: type_model) -> type_model:
        self.session.add(instance)  # type_model
        await self.session.flush()
        return instance

    async def read(self, id: Any) -> Optional[type_model]:
        return await self.session.get(self.model, id)

    async def update(self, id: Any,
                     data: Dict[str, Any]) -> Optional[type_model]:
        instance = await self.read(id)
        if instance:
            for key, value in data.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            await self.session.flush()
            return instance

    async def delete(self, id: Any) -> bool:
        instance = await self.read(id)
        if instance:
            await self.session.delete(instance)
            await self.session.flush()
            return True
        return False
