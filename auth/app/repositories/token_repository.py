from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from app.models.auth import RefreshToken


class TokenRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_token(self, token: str) -> RefreshToken | None:
        stmt = (
            select(RefreshToken)
            .where(RefreshToken.token == token)
            .options(selectinload(RefreshToken.user))
        )
        return await self._session.scalar(stmt)

    async def delete_token() -> ...:
        pass

    async def create_token() -> RefreshToken | None:
        pass
