from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from datetime import datetime
from app.models.auth import RefreshToken, User


class TokenRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_token(self, token: str) -> RefreshToken | None:
        stmt = (
            select(RefreshToken)
            .where(RefreshToken.token == token)
            .options(joinedload(RefreshToken.user))
        )
        return await self._session.scalar(stmt)

    async def delete_token(self, token: RefreshToken) -> None:
        await self._session.delete(token)

    async def create_token(
        self, token_str: str, user: User, expired_at: datetime
    ) -> RefreshToken | None:
        token = RefreshToken(token=token_str, user=user, expired_at=expired_at)
        self._session.add(token)
        return token
