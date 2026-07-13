from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.file import File


class FileRepository:
    """Data-access layer for File. The ONLY layer that talks SQL.

    It receives an AsyncSession and never creates one itself: the caller
    (the service) owns the session and the transaction boundary.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, file: File) -> File:
        """Persist a new File and return it with its generated id."""
        self._session.add(file)
        await self._session.flush()
        await self._session.refresh(file)
        return file

    async def get(self, file_id: int) -> File | None:
        """Return the File with this id, or None if it does not exist."""
        return await self._session.get(File, file_id)

    async def list_by_organisation(self, organisation_id: int) -> list[File]:
        """Return all files belonging to a given organisation."""
        command = select(File).where(File.organisation_id == organisation_id)
        result = await self._session.execute(command)
        return list(result.scalars().all())

    async def update(self, file: File) -> File:
        """Persist changes made to an already-loaded File."""
        await self._session.flush()
        await self._session.refresh(file)
        return file

    async def delete(self, file: File) -> None:
        """Delete a File from the database."""
        await self._session.delete(file)
        await self._session.flush()
