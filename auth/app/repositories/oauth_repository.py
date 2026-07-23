from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from app.models.auth import User, OAuthAccount


class OAuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_provider(
        self, provider: str, provider_user_id: str
    ) -> OAuthAccount | None:
        stmt = (
            select(OAuthAccount)
            .where(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_user_id == provider_user_id,
            )
            .options(joinedload(OAuthAccount.user))
        )

        result: OAuthAccount | None = await self._session.scalar(stmt)
        return result

    async def create(
        self, user: User, provider: str, provider_user_id: str
    ) -> OAuthAccount:
        oauth_account = OAuthAccount(
            provider=provider, provider_user_id=provider_user_id, user=user
        )
        self._session.add(oauth_account)
        return oauth_account
