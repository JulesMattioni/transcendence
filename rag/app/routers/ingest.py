from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import get_session
from app.repositories.chunk_repository import ChunkRepository
from app.storage.reader_storage import ReaderStorage
from app.services.ingest_service import IngestService, UnsupportedFileType
from app.schemas.ingest import IngestRequest, IngestResponse

router = APIRouter(prefix="/ingest", tags=["ingest"])


def get_ingest_service(
    session: AsyncSession = Depends(get_session),
) -> IngestService:
    repository = ChunkRepository(session)
    storage = ReaderStorage()
    return IngestService(session, repository, storage)


@router.post("", response_model=IngestResponse)
async def ingest_file(
    data: IngestRequest,
    service: IngestService = Depends(get_ingest_service),
) -> IngestResponse:
    try:
        return await service.ingest(data)
    except UnsupportedFileType as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported content_type: {exc}",
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found on storage for file_id {data.file_id}",
        )
