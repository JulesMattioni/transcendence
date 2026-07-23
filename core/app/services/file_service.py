from sqlalchemy.ext.asyncio import AsyncSession
from shared.base_service import BaseService
from app.repositories.file_repository import FileRepository
from app.storage.file_storage import FileStorage
from fastapi import UploadFile
from app.models.file import File
from app.schemas.file import FileCreate, FileRead, FileUpdate, FilePage
from app.exceptions import FileNotFoundError
from app.clients.rag_client import RagClient
from app.clients.realtime_client import RealtimeClient


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
