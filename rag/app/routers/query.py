from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import get_session
from app.config import GROQ_BASE_URL, GROQ_MODEL
from app.repositories.chunk_repository import ChunkRepository
from app.services.llm.openai_compatible_service import OpenAICompatibleService
from app.services.query_service import QueryService
from app.schemas.query import QueryRequest, QueryResponse

router = APIRouter(prefix="/query", tags=["query"])


def get_query_service(
    session: AsyncSession = Depends(get_session),
) -> QueryService:
    repository = ChunkRepository(session)
    llm = OpenAICompatibleService(
        model_name=GROQ_MODEL, base_url=GROQ_BASE_URL
    )
    return QueryService(session, repository, llm)


@router.post("", response_model=QueryResponse)
async def query(
    data: QueryRequest,
    service: QueryService = Depends(get_query_service),
) -> QueryResponse:
    return await service.query(data)
