from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from app.models.auth import User, OAuthAccount


class OAuthRepository:
    """
    Repository for managing OAuthAccount persistence.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize the repository with a database session.

        Args:
            session: Async SQLAlchemy session used for database operations.
        """

        self._session = session

    async def get_by_provider(
        self, provider: str, provider_user_id: str
    ) -> OAuthAccount | None:
        """
        Retrieve an OAuth account by provider and provider user ID.

        Args:
            provider: Name of the OAuth provider (e.g. "google", "42").
            provider_user_id: User ID as returned by the OAuth provider.

        Returns:
            The matching OAuthAccount with its user eagerly loaded, or None if
            not found.
        """

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
        """
        Create and stage a new OAuth account linked to a user.

        Args:
            user: User to link the OAuth account to.
            provider: Name of the OAuth provider (e.g. "google", "42").
            provider_user_id: User ID as returned by the OAuth provider.

        Returns:
            The newly created OAuthAccount, added to the session but not yet
            committed.
        """

        oauth_account = OAuthAccount(
            provider=provider, provider_user_id=provider_user_id, user=user
        )
        self._session.add(oauth_account)
        return oauth_account
