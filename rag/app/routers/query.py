from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import get_session
from app.config import GROQ_BASE_URL, GROQ_MODEL
from app.repositories.chunk_repository import ChunkRepository
from app.services.llm.openai_compatible_service import OpenAICompatibleService
from app.services.query_service import QueryService
from app.schemas.query import QueryRequest, QueryResponse
from fastapi.responses import StreamingResponse
import json

router = APIRouter(prefix="/query", tags=["query"])


def get_query_service(
    session: AsyncSession = Depends(get_session),
) -> QueryService:
    repository = ChunkRepository(session)
    llm = OpenAICompatibleService(
        model_name=GROQ_MODEL, base_url=GROQ_BASE_URL
    )
    return QueryService(session, repository, llm)


def _sse_format(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("", response_model=QueryResponse)
async def query(
    data: QueryRequest,
    service: QueryService = Depends(get_query_service),
) -> QueryResponse:
    return await service.query(data)


@router.post("/stream")
async def query_stream(
    data: QueryRequest,
    service: QueryService = Depends(get_query_service),
) -> StreamingResponse:
    async def event_stream():
        async for kind, payload in service.query_stream(data):
            if kind == "sources":
                sources = [s.model_dump() for s in payload]
                yield _sse_format("sources", {"sources": sources})
            else:
                yield _sse_format("token", {"text": payload})
        yield _sse_format("done", {})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
