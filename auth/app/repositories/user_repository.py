from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from app.exceptions import EmailAlreadyExistsError
from app.models.auth import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: int) -> User | None:
        return await self._session.get(
            User, id, options=[selectinload(User.tokens)]
        )

    async def get_by_email(self, email: str) -> User | None:
        stmt = (
            select(User)
            .where(User.email == email)
            .options(selectinload(User.tokens))
        )

        return await self._session.scalar(stmt)

    async def create_user(
        self, first_name: str, last_name: str, email: str, hashed_password: str
    ) -> User:
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


# Norme Unit of Work Martin Fowler
