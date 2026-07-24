from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from shared.base_service import BaseService
from app.repositories.file_repository import FileRepository
from app.storage.file_storage import FileStorage
from fastapi import UploadFile
from app.models.file import File
from app.schemas.file import (
    FileCreate,
    FileRead,
    FileUpdate,
    FilePage,
    FileStats,
    FileTypeStat,
    FileBucketStat,
)
from app.exceptions import FileNotFoundError
from app.clients.rag_client import RagClient
from app.clients.realtime_client import RealtimeClient

BUCKET_MINUTES = 15
BUCKET_INTERVAL = timedelta(minutes=BUCKET_MINUTES)
BUCKET_ORIGIN = datetime(1970, 1, 1, tzinfo=timezone.utc)
MAX_BUCKETS = 500


def _floor_to_bucket(moment: datetime) -> datetime:
    """
    Round a timestamp down to the start of its 15-minute bucket.

    Aligned to BUCKET_ORIGIN so it matches Postgres date_bin exactly.

    Args:
        moment: Timezone-aware timestamp to floor.

    Returns:
        The first instant of the bucket containing moment.
    """

    delta = moment - BUCKET_ORIGIN
    step = timedelta(minutes=BUCKET_MINUTES)
    floored = (delta // step) * step
    return BUCKET_ORIGIN + floored


def categorize_content_type(content_type: str) -> str:
    """
    Map a raw MIME type to a coarse, human-readable category.

    Keeps the analytics chart legible by collapsing dozens of MIME
    strings into a handful of buckets. Anything unrecognised falls back
    to "other" so the categories stay a closed, chart-friendly set.

    Args:
        content_type: Raw MIME type stored on the file.

    Returns:
        One of image, pdf, document, spreadsheet, video, audio,
        archive, other.
    """

    value = (content_type or "").lower()
    if value.startswith("image/"):
        return "image"
    if value.startswith("video/"):
        return "video"
    if value.startswith("audio/"):
        return "audio"
    if value == "application/pdf":
        return "pdf"
    if any(
        token in value for token in ("zip", "tar", "rar", "compressed", "7z")
    ):
        return "archive"
    if any(token in value for token in ("spreadsheet", "excel", "csv")):
        return "spreadsheet"
    if value.startswith("text/") or any(
        token in value
        for token in ("word", "document", "presentation", "powerpoint")
    ):
        return "document"
    return "other"


class FileService(BaseService):
    """
    Service handling file upload, listing, metadata updates and deletion.

    Coordinates the repository (database), the storage (disk) and the
    outbound clients (rag, realtime). It is the only layer that commits
    or rolls back the session.
    """

    def __init__(
        self,
        session: AsyncSession,
        repository: FileRepository,
        storage: FileStorage,
        rag_client: RagClient,
        realtime_client: RealtimeClient,
    ) -> None:
        """
        Initialize the service with its collaborators.

        Args:
            session: Async SQLAlchemy session used for transactions.
            repository: Repository for File persistence.
            storage: Disk storage for uploaded binaries.
            rag_client: Client triggering document ingestion in rag.
            realtime_client: Client pushing file events to realtime.
        """

        super().__init__()
        self._session = session
        self._repository = repository
        self._storage = storage
        self._rag_client = rag_client
        self._realtime_client = realtime_client

    async def _get_owned(self, file_id: int, organisation_id: int) -> File:
        """
        Return the file if it belongs to the given organisation.

        A file from another organisation is indistinguishable from a
        missing one, so its existence is never leaked.

        Args:
            file_id: Id of the requested file.
            organisation_id: Organisation the file must belong to.

        Returns:
            The matching File ORM object.

        Raises:
            FileNotFoundError: If the file does not exist or belongs to
            another organisation.
        """

        file = await self._repository.get(file_id)
        if file is None or file.organisation_id != organisation_id:
            raise FileNotFoundError(f"file {file_id} does not exist")
        return file

    async def create(
        self, upload: UploadFile, data: FileCreate, owner_id: int
    ) -> FileRead:
        """
        Save the binary to disk, persist the record and notify services.

        If the database insert fails after the binary was written, the
        file is removed from disk so storage and database stay in sync.
        RAG ingestion and the realtime event are fire-and-forget.

        Args:
            upload: Uploaded binary content.
            data: Client-provided metadata (title, description,
            organisation_id).
            owner_id: Id of the authenticated user uploading the file.

        Returns:
            FileRead with the created file's metadata.
        """

        destination = self._storage.build_path(
            data.organisation_id, upload.filename or ""
        )
        size = await self._storage.save(upload, destination)

        file = File(
            title=data.title,
            description=data.description,
            organisation_id=data.organisation_id,
            filename=upload.filename or "",
            filepath=destination,
            content_type=upload.content_type or "application/octet-stream",
            size_bytes=size,
            owner_id=owner_id,
        )

        try:
            await self._repository.create(file)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            self._storage.delete(destination)
            raise

        self._rag_client.trigger_ingest(
            file_id=file.id,
            organisation_id=file.organisation_id,
            filepath=file.filepath,
            content_type=file.content_type,
        )

        self._realtime_client.notify_file_event(
            "file.created", file.organisation_id, file.filename
        )

        return FileRead.model_validate(file)

    async def list_by_organisation(
        self, organisation_id: int, page: int, page_size: int
    ) -> FilePage:
        """
        Return one page of an organisation's files plus the total count.

        Args:
            organisation_id: Organisation whose files are listed.
            page: 1-based page number.
            page_size: Number of items per page.

        Returns:
            FilePage with the requested items and the total count.
        """

        offset = (page - 1) * page_size
        files = await self._repository.list_by_organisation(
            organisation_id, limit=page_size, offset=offset
        )
        total = await self._repository.count_by_organisation(organisation_id)
        return FilePage(
            items=[FileRead.model_validate(f) for f in files],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def stats_by_organisation(
        self,
        organisation_id: int,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> FileStats:
        """
        Build the analytics summary for an organisation's files.

        Aggregates headline totals plus per-category and per-bucket
        breakdowns in a few grouped queries, then folds raw MIME types
        into human-readable categories and fills empty 15-minute buckets
        with zeros so the uploads chart is continuous. All figures honour
        the optional date range; when it is omitted they span every file.

        Args:
            organisation_id: Organisation whose files are analysed.
            start: Inclusive lower bound on created_at, or None.
            end: Exclusive upper bound on created_at, or None.

        Returns:
            FileStats with total_files, total_bytes, by_type, by_bucket.
        """

        total_files = await self._repository.count_by_organisation_in_range(
            organisation_id, start, end
        )
        total_bytes = await self._repository.total_bytes_by_organisation(
            organisation_id, start, end
        )
        raw_types = await self._repository.stats_by_content_type(
            organisation_id, start, end
        )
        raw_buckets = await self._repository.stats_by_bucket(
            organisation_id, BUCKET_INTERVAL, BUCKET_ORIGIN, start, end
        )

        counts: dict[str, int] = {}
        sizes: dict[str, int] = {}
        for content_type, file_count, total in raw_types:
            category = categorize_content_type(content_type)
            counts[category] = counts.get(category, 0) + file_count
            sizes[category] = sizes.get(category, 0) + total

        by_type = [
            FileTypeStat(
                category=category,
                file_count=counts[category],
                total_bytes=sizes[category],
            )
            for category in sorted(
                counts, key=lambda c: counts[c], reverse=True
            )
        ]

        by_bucket = await self._build_buckets(
            organisation_id, raw_buckets, start, end
        )

        return FileStats(
            total_files=total_files,
            total_bytes=total_bytes,
            by_type=by_type,
            by_bucket=by_bucket,
        )

    async def _build_buckets(
        self,
        organisation_id: int,
        raw_buckets: list[tuple[datetime, int]],
        start: datetime | None,
        end: datetime | None,
    ) -> list[FileBucketStat]:
        """
        Turn sparse bucket rows into a continuous, zero-filled series.

        Determines the window to span (the requested range, or the oldest
        upload through now when the range is open), then walks it in
        15-minute steps, emitting every bucket with its count or zero.

        Args:
            organisation_id: Organisation the buckets belong to.
            raw_buckets: Non-empty (bucket_start, count) rows from SQL.
            start: Inclusive lower bound on created_at, or None.
            end: Exclusive upper bound on created_at, or None.

        Returns:
            An ordered list of FileBucketStat, oldest first, at most
            MAX_BUCKETS entries.
        """

        by_start = {b: c for b, c in raw_buckets}

        window_start = start
        if window_start is None:
            window_start = await self._repository.earliest_created_at(
                organisation_id
            )
        if window_start is None:
            return []

        now = datetime.now(timezone.utc)
        window_end = end if end is not None else now

        step = timedelta(minutes=BUCKET_MINUTES)
        cursor = _floor_to_bucket(window_start)
        last = _floor_to_bucket(window_end)

        buckets: list[FileBucketStat] = []
        while cursor <= last and len(buckets) < MAX_BUCKETS:
            buckets.append(
                FileBucketStat(
                    bucket_start=cursor.isoformat(),
                    file_count=by_start.get(cursor, 0),
                )
            )
            cursor += step

        return buckets

    async def get(self, file_id: int, organisation_id: int) -> FileRead:
        """
        Return the metadata of a single file.

        Args:
            file_id: Id of the requested file.
            organisation_id: Organisation the file must belong to.

        Returns:
            FileRead with the file's metadata.

        Raises:
            FileNotFoundError: If the file does not exist in this
            organisation.
        """

        file = await self._get_owned(file_id, organisation_id)
        return FileRead.model_validate(file)

    async def update(
        self, file_id: int, organisation_id: int, data: FileUpdate
    ) -> FileRead:
        """
        Apply a partial metadata update and broadcast the event.

        Args:
            file_id: Id of the file to update.
            organisation_id: Organisation the file must belong to.
            data: Fields to change; unset fields are left untouched.

        Returns:
            FileRead with the updated metadata.

        Raises:
            FileNotFoundError: If the file does not exist in this
            organisation.
        """

        file = await self._get_owned(file_id, organisation_id)

        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(file, field, value)

        try:
            await self._repository.update(file)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

        self._realtime_client.notify_file_event(
            "file.updated", file.organisation_id, file.filename
        )
        return FileRead.model_validate(file)

    async def delete(self, file_id: int, organisation_id: int) -> None:
        """
        Delete the record, then the binary, then broadcast the event.

        The database row is removed first (transactional); the disk file
        is only deleted once the commit succeeded.

        Args:
            file_id: Id of the file to delete.
            organisation_id: Organisation the file must belong to.

        Raises:
            FileNotFoundError: If the file does not exist in this
            organisation.
        """

        file = await self._get_owned(file_id, organisation_id)
        path = file.filepath
        org_id = file.organisation_id
        filename = file.filename

        try:
            await self._repository.delete(file)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

        self._realtime_client.notify_file_event(
            "file.deleted", org_id, filename
        )
        self._storage.delete(path)

    async def get_content(self, file_id: int, organisation_id: int) -> File:
        """
        Return the ORM object so the router can serve the binary.

        Args:
            file_id: Id of the requested file.
            organisation_id: Organisation the file must belong to.

        Returns:
            The File ORM object, exposing filepath, content_type and
            filename for the download response.

        Raises:
            FileNotFoundError: If the file does not exist in this
            organisation.
        """

        return await self._get_owned(file_id, organisation_id)
