from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from app.exceptions import EmailAlreadyExistsError
from app.models.auth import User


class UserRepository:
    """
    Repository for managing User persistence.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository with a database session.

        Args:
            session: Async SQLAlchemy session used for database operations.
        """

        self._session = session

    async def get_by_id(self, id: int) -> User | None:
        """
        Retrieve a user by ID.

        Args:
            id: ID of the user to retrieve.

        Returns:
            The matching User with its tokens eagerly loaded, or None if not
            found.
        """

        return await self._session.get(
            User, id, options=[selectinload(User.tokens)]
        )

    async def get_by_email(self, email: str) -> User | None:
        """
        Retrieve a user by email address.

        Args:
            email: Email address of the user to retrieve.

        Returns:
            The matching User with its tokens eagerly loaded, or None if not
            found.
        """

        stmt = (
            select(User)
            .where(User.email == email)
            .options(selectinload(User.tokens))
        )

        result: User | None = await self._session.scalar(stmt)

        return result

    async def create_user(
        self, first_name: str, last_name: str, email: str, hashed_password: str
    ) -> User:
        """
        Create and persist a new user.

        Args:
            first_name: User's first name.
            last_name: User's last name.
            email: User's email address, must be unique.
            hashed_password: Bcrypt hash of the user's password.

        Returns:
            The newly created User.

        Raises:
            EmailAlreadyExistsError: If a user with the given email already
            exists.
        """

        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            hashed_password=hashed_password,
        )

        try:
            self._session.add(user)
            await self._session.flush()
            return user
        except IntegrityError as e:
            raise EmailAlreadyExistsError() from e

    async def register_2fa_secret(self, user: User, secret: str) -> None:
        """
        Register a TOTP secret for a user's 2FA setup.

        Args:
            user: User to register the secret for.
            secret: Base32-encoded TOTP secret.
        """

        user.secret_2fa = secret
        await self._session.flush()

    async def enable_2fa(self, user: User) -> None:
        """
        Enable two-factor authentication for a user.

        Args:
            user: User to enable 2FA for.
        """

        user.is_2fa_enabled = True
        await self._session.flush()

    async def disable_2fa(self, user: User) -> None:
        """
        Disable two-factor authentication for a user.

        Args:
            user: User to disable 2FA for.
        """

        user.is_2fa_enabled = False
        await self._session.flush()

    async def change_location(self, user: User, location: str) -> None:
        """
        Update a user's location.

        Args:
            user: User to update.
            location: New location value.
        """

        user.location = location
        await self._session.flush()

    async def change_avatar_id(self, user: User, avatar_id: int) -> None:
        """
        Update a user's selected avatar.

        Args:
            user: User to update.
            avatar_id: ID of the new avatar.
        """

        user.avatar_id = avatar_id
        await self._session.flush()


# Norme Unit of Work Martin Fowler
