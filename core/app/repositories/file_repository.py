from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.file import File


class FileRepository:
    """
    Data-access layer for File. The ONLY layer that talks SQL.

    It receives an AsyncSession and never creates one itself: the caller
    (the service) owns the session and the transaction boundary.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize the repository with its database session.

        Args:
            session: Async SQLAlchemy session used for all queries.
        """

        self._session = session

    async def create(self, file: File) -> File:
        """
        Persist a new File.

        Args:
            file: File ORM object to persist.

        Returns:
            The same File, refreshed with its generated id and defaults.
        """

        self._session.add(file)
        await self._session.flush()
        await self._session.refresh(file)
        return file

    async def get(self, file_id: int) -> File | None:
        """
        Fetch a File by its id.

        Args:
            file_id: Id of the requested file.

        Returns:
            The matching File, or None if it does not exist.
        """

        return await self._session.get(File, file_id)

    async def list_by_organisation(
        self, organisation_id: int, limit: int, offset: int
    ) -> list[File]:
        """
        Fetch one page of an organisation's files, newest first.

        Args:
            organisation_id: Organisation whose files are listed.
            limit: Maximum number of rows to return.
            offset: Number of rows to skip.

        Returns:
            List of File objects for the requested page.
        """

        command = (
            select(File)
            .where(File.organisation_id == organisation_id)
            .order_by(File.created_at.desc(), File.id.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(command)
        return list(result.scalars().all())

    async def count_by_organisation(self, organisation_id: int) -> int:
        """
        Count the files belonging to an organisation.

        Args:
            organisation_id: Organisation whose files are counted.

        Returns:
            The total number of files for this organisation.
        """

        command = (
            select(func.count())
            .select_from(File)
            .where(File.organisation_id == organisation_id)
        )
        result = await self._session.execute(command)
        return result.scalar_one()

    async def update(self, file: File) -> File:
        """
        Persist changes made to an already-loaded File.

        Args:
            file: File ORM object with pending attribute changes.

        Returns:
            The same File, refreshed from the database.
        """

        await self._session.flush()
        await self._session.refresh(file)
        return file

    async def delete(self, file: File) -> None:
        """
        Delete a File from the database.

        Args:
            file: File ORM object to delete.
        """

        await self._session.delete(file)
        await self._session.flush()
