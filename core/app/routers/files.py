from datetime import datetime
from fastapi import APIRouter, Depends, File, Form, UploadFile, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import get_session
from app.repositories.file_repository import FileRepository
from app.storage.file_storage import FileStorage
from app.services.file_service import FileService
from app.schemas.file import (
    FileCreate,
    FileRead,
    FileUpdate,
    FilePage,
    FileStats,
)
from fastapi.responses import FileResponse
from app.clients.rag_client import RagClient
from app.clients.realtime_client import RealtimeClient
from app.get_user import get_current_user_id

router = APIRouter(prefix="/files", tags=["files"])


def get_file_service(
    session: AsyncSession = Depends(get_session),
) -> FileService:
    """
    Build a FileService with all its dependencies for one request.

    Args:
        session: Async SQLAlchemy session provided by the shared
        get_session dependency.

    Returns:
        A FileService wired with repository, storage and clients.
    """

    repository = FileRepository(session)
    storage = FileStorage()
    rag_client = RagClient()
    realtime_client = RealtimeClient()
    return FileService(
        session, repository, storage, rag_client, realtime_client
    )


@router.post("", response_model=FileRead, status_code=status.HTTP_201_CREATED)
async def upload_file(
    upload: UploadFile = File(...),
    title: str = Form(...),
    organisation_id: int = Form(...),
    description: str | None = Form(default=None),
    service: FileService = Depends(get_file_service),
    owner_id: int = Depends(get_current_user_id),
) -> FileRead:
    """
    Upload a file with its metadata and create its database record.

    Args:
        upload: Uploaded binary content (multipart).
        title: User-facing title of the file.
        organisation_id: Organisation the file belongs to.
        description: Optional description of the file.
        service: Injected FileService instance.
        owner_id: Id of the authenticated user, resolved via auth.

    Returns:
        FileRead with the created file's metadata.
    """

    data = FileCreate(
        title=title,
        organisation_id=organisation_id,
        description=description,
    )
    return await service.create(upload, data, owner_id)


@router.get("", response_model=FilePage)
async def list_files(
    organisation_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=9, ge=1, le=100),
    service: FileService = Depends(get_file_service),
) -> FilePage:
    """
    List one page of an organisation's files, newest first.

    Args:
        organisation_id: Organisation whose files are listed.
        page: 1-based page number.
        page_size: Number of items per page (1-100).
        service: Injected FileService instance.

    Returns:
        FilePage with the requested items and the total count.
    """

    return await service.list_by_organisation(organisation_id, page, page_size)


@router.get("/stats", response_model=FileStats)
async def get_file_stats(
    organisation_id: int,
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    service: FileService = Depends(get_file_service),
) -> FileStats:
    """
    Return aggregated analytics for an organisation's files.

    Declared before the "/{file_id}" route so "stats" is matched here
    instead of being parsed as a file id. The optional start/end bounds
    let the client drive a customizable date range; omitting them covers
    every file.

    Args:
        organisation_id: Organisation whose analytics are computed.
        start: Inclusive lower bound on created_at (ISO datetime), or None.
        end: Exclusive upper bound on created_at (ISO datetime), or None.
        service: Injected FileService instance.

    Returns:
        FileStats with headline totals and per-type/per-month breakdowns.
    """

    return await service.stats_by_organisation(organisation_id, start, end)


@router.get("/{file_id}", response_model=FileRead)
async def get_file(
    file_id: int,
    organisation_id: int,
    service: FileService = Depends(get_file_service),
) -> FileRead:
    """
    Return the metadata of a single file.

    Args:
        file_id: Id of the requested file.
        organisation_id: Organisation the file must belong to.
        service: Injected FileService instance.

    Returns:
        FileRead with the file's metadata.

    Raises:
        FileNotFoundError: If the file does not exist in this
        organisation.
    """

    return await service.get(file_id, organisation_id)


@router.get("/{file_id}/content")
async def get_file_content(
    file_id: int,
    organisation_id: int,
    service: FileService = Depends(get_file_service),
) -> FileResponse:
    """
    Download the binary content with its original filename.

    Args:
        file_id: Id of the requested file.
        organisation_id: Organisation the file must belong to.
        service: Injected FileService instance.

    Returns:
        FileResponse streaming the stored binary with its content type
        and original filename.

    Raises:
        FileNotFoundError: If the file does not exist in this
        organisation.
    """

    file = await service.get_content(file_id, organisation_id)
    return FileResponse(
        path=file.filepath,
        media_type=file.content_type,
        filename=file.filename,
    )


@router.patch("/{file_id}", response_model=FileRead)
async def update_file(
    file_id: int,
    organisation_id: int,
    data: FileUpdate,
    service: FileService = Depends(get_file_service),
) -> FileRead:
    """
    Partially update a file's metadata (title, description).

    Args:
        file_id: Id of the file to update.
        organisation_id: Organisation the file must belong to.
        data: Fields to change; unset fields are left untouched.
        service: Injected FileService instance.

    Returns:
        FileRead with the updated metadata.

    Raises:
        FileNotFoundError: If the file does not exist in this
        organisation.
    """

    return await service.update(file_id, organisation_id, data)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: int,
    organisation_id: int,
    service: FileService = Depends(get_file_service),
) -> None:
    """
    Delete a file record and its binary content.

    Args:
        file_id: Id of the file to delete.
        organisation_id: Organisation the file must belong to.
        service: Injected FileService instance.

    Raises:
        FileNotFoundError: If the file does not exist in this
        organisation.
    """

    await service.delete(file_id, organisation_id)
