from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, literal, Interval
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

    @staticmethod
    def _range_filters(
        organisation_id: int,
        start: datetime | None,
        end: datetime | None,
    ) -> list:
        """
        Build the common WHERE clauses for stat queries.

        Args:
            organisation_id: Organisation the files must belong to.
            start: Inclusive lower bound on created_at, or None.
            end: Exclusive upper bound on created_at, or None.

        Returns:
            A list of SQLAlchemy boolean clauses to unpack into where().
        """

        clauses = [File.organisation_id == organisation_id]
        if start is not None:
            clauses.append(File.created_at >= start)
        if end is not None:
            clauses.append(File.created_at < end)
        return clauses

    async def stats_by_content_type(
        self,
        organisation_id: int,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[tuple[str, int, int]]:
        """
        Aggregate file count and total size per raw content type.

        Grouping raw MIME types into human-readable categories is left to
        the service layer; the repository only returns the raw rows.

        Args:
            organisation_id: Organisation whose files are aggregated.
            start: Inclusive lower bound on created_at, or None.
            end: Exclusive upper bound on created_at, or None.

        Returns:
            List of (content_type, file_count, total_bytes) tuples.
        """

        command = (
            select(
                File.content_type,
                func.count().label("file_count"),
                func.coalesce(func.sum(File.size_bytes), 0).label(
                    "total_bytes"
                ),
            )
            .where(*self._range_filters(organisation_id, start, end))
            .group_by(File.content_type)
        )
        result = await self._session.execute(command)
        return [(row[0], row[1], row[2]) for row in result.all()]

    async def stats_by_bucket(
        self,
        organisation_id: int,
        bucket: timedelta,
        origin: datetime,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[tuple[datetime, int]]:
        """
        Count uploads per fixed-width time bucket for an organisation.

        Uses Postgres date_bin (PG14+) so any interval width works, e.g.
        a 15-minute timedelta. Only non-empty buckets are returned; the
        service fills the gaps with zeros to produce a continuous series.

        The interval is passed as a typed literal (a Python timedelta)
        rather than a string, because asyncpg encodes bind parameters to
        their native PG type before any SQL-level cast would run.

        Args:
            organisation_id: Organisation whose uploads are aggregated.
            bucket: Bucket width as a timedelta, e.g. 15 minutes.
            origin: Alignment origin the bins are anchored to.
            start: Inclusive lower bound on created_at, or None.
            end: Exclusive upper bound on created_at, or None.

        Returns:
            List of (bucket_start, file_count) tuples, oldest first.
        """

        binned = func.date_bin(
            literal(bucket, Interval),
            File.created_at,
            origin,
        ).label("bucket")
        command = (
            select(binned, func.count().label("file_count"))
            .where(*self._range_filters(organisation_id, start, end))
            .group_by(binned)
            .order_by(binned)
        )
        result = await self._session.execute(command)
        return [(row[0], row[1]) for row in result.all()]

    async def earliest_created_at(
        self, organisation_id: int
    ) -> datetime | None:
        """
        Return the timestamp of an organisation's oldest file.

        Args:
            organisation_id: Organisation to inspect.

        Returns:
            The earliest created_at, or None when the org has no file.
        """

        command = select(func.min(File.created_at)).where(
            File.organisation_id == organisation_id
        )
        result = await self._session.execute(command)
        return result.scalar_one_or_none()

    async def total_bytes_by_organisation(
        self,
        organisation_id: int,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> int:
        """
        Sum the size in bytes of an organisation's files.

        Args:
            organisation_id: Organisation whose storage is summed.
            start: Inclusive lower bound on created_at, or None.
            end: Exclusive upper bound on created_at, or None.

        Returns:
            The total number of bytes stored, 0 when there is no file.
        """

        command = select(func.coalesce(func.sum(File.size_bytes), 0)).where(
            *self._range_filters(organisation_id, start, end)
        )
        result = await self._session.execute(command)
        return result.scalar_one()

    async def count_by_organisation_in_range(
        self,
        organisation_id: int,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> int:
        """
        Count files of an organisation within an optional date range.

        Args:
            organisation_id: Organisation whose files are counted.
            start: Inclusive lower bound on created_at, or None.
            end: Exclusive upper bound on created_at, or None.

        Returns:
            The number of files matching the organisation and range.
        """

        command = (
            select(func.count())
            .select_from(File)
            .where(*self._range_filters(organisation_id, start, end))
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
