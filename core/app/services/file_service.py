from sqlalchemy.ext.asyncio import AsyncSession
from shared.base_service import BaseService
from app.repositories.file_repository import FileRepository
from app.storage.file_storage import FileStorage
from fastapi import UploadFile
from app.models.file import File
from app.schemas.file import FileCreate, FileRead, FileUpdate, FilePage
from app.exceptions import FileNotFoundError


class FileService(BaseService):
    def __init__(
        self,
        session: AsyncSession,
        repository: FileRepository,
        storage: FileStorage,
    ) -> None:
        super().__init__()
        self._session = session
        self._repository = repository
        self._storage = storage

    async def create(
        self, upload: UploadFile, data: FileCreate, owner_id: int
    ) -> FileRead:
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

        return FileRead.model_validate(file)

    async def get(self, file_id: int) -> FileRead:
        file = await self._repository.get(file_id)
        if file is None:
            raise FileNotFoundError(f"file {file_id} does not exist")
        return FileRead.model_validate(file)

    async def list_by_organisation(
        self, organisation_id: int, page: int, page_size: int
    ) -> FilePage:
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

    async def update(self, file_id: int, data: FileUpdate) -> FileRead:
        file = await self._repository.get(file_id)
        if file is None:
            raise FileNotFoundError(f"file {file_id} does not exist")

        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(file, field, value)

        try:
            await self._repository.update(file)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

        return FileRead.model_validate(file)

    async def delete(self, file_id: int) -> None:
        file = await self._repository.get(file_id)
        if file is None:
            raise FileNotFoundError(f"file {file_id} does not exist")

        path = file.filepath

        try:
            await self._repository.delete(file)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

        self._storage.delete(path)

    async def get_content(self, file_id: int) -> File:
        """Return the File ORM object (incl. filepath) for streaming.

        Unlike get(), this returns the model itself so the router can
        access filepath / content_type to build the file response.
        """
        file = await self._repository.get(file_id)
        if file is None:
            raise FileNotFoundError(f"file {file_id} does not exist")
        return file
