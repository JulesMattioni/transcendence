from fastapi import APIRouter, Depends, File, Form, UploadFile, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import get_session
from app.repositories.file_repository import FileRepository
from app.storage.file_storage import FileStorage
from app.services.file_service import FileService
from app.schemas.file import FileCreate, FileRead, FileUpdate, FilePage

router = APIRouter(prefix="/files", tags=["files"])


def get_file_service(
    session: AsyncSession = Depends(get_session),
) -> FileService:
    repository = FileRepository(session)
    storage = FileStorage()
    return FileService(session, repository, storage)


def get_current_user_id() -> int:
    """MOCK authentication: always returns user 1.

    In production this will read and verify the JWT issued by the auth
    service (Authorization: Bearer <token>), extract the user id from it,
    and raise 401 if the token is missing or invalid. The signature stays
    the same, so routes depending on it will not change when auth is wired.
    """
    return 1


@router.post("", response_model=FileRead, status_code=status.HTTP_201_CREATED)
async def upload_file(
    upload: UploadFile = File(...),
    title: str = Form(...),
    organisation_id: int = Form(...),
    description: str | None = Form(default=None),
    service: FileService = Depends(get_file_service),
    owner_id: int = Depends(get_current_user_id),
) -> FileRead:
    data = FileCreate(
        title=title,
        organisation_id=organisation_id,
        description=description,
    )
    return await service.create(upload, data, owner_id)


@router.get("/{file_id}", response_model=FileRead)
async def get_file(
    file_id: int,
    service: FileService = Depends(get_file_service),
) -> FileRead:
    return await service.get(file_id)


@router.get("", response_model=FilePage)
async def list_files(
    organisation_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=9, ge=1, le=100),
    service: FileService = Depends(get_file_service),
) -> FilePage:
    return await service.list_by_organisation(organisation_id, page, page_size)


@router.patch("/{file_id}", response_model=FileRead)
async def update_file(
    file_id: int,
    data: FileUpdate,
    service: FileService = Depends(get_file_service),
) -> FileRead:
    return await service.update(file_id, data)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: int,
    service: FileService = Depends(get_file_service),
) -> None:
    await service.delete(file_id)
