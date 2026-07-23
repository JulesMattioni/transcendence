from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from datetime import datetime
from app.models.auth import RefreshToken, User


class TokenRepository:
    """
    Repository for managing RefreshToken persistence.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize the repository with a database session.

        Args:
            session: Async SQLAlchemy session used for database operations.
        """

        self._session = session

    async def get_by_token(self, token: str) -> RefreshToken | None:
        """
        Retrieve a refresh token by its token string.

        Args:
            token: The refresh token string to look up.

        Returns:
            The matching RefreshToken with its user eagerly loaded, or None if
            not found.
        """

        stmt = (
            select(RefreshToken)
            .where(RefreshToken.token == token)
            .options(joinedload(RefreshToken.user))
        )

        result: RefreshToken | None = await self._session.scalar(stmt)
        return result

    async def delete_token(self, token: RefreshToken) -> None:
        """
        Delete a refresh token from the database.

        Args:
            token: The RefreshToken instance to delete.
        """

        await self._session.delete(token)

    async def create(
        self, token_str: str, user: User, expired_at: datetime
    ) -> RefreshToken:
        """
        Create and stage a new refresh token for a user.

        Args:
            token_str: The refresh token string.
            user: User the token belongs to.
            expired_at: Timestamp at which the token expires.

        Returns:
            The newly created RefreshToken, added to the session but not yet
            committed.
        """

        token = RefreshToken(token=token_str, user=user, expired_at=expired_at)
        self._session.add(token)

        return token
