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
from app.repositories.conversation_repository import ConversationRepository
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/query", tags=["query"])


def get_current_user_id() -> int:
    """MOCK auth: user 1."""
    return 1


def get_conversation_service(
    session: AsyncSession = Depends(get_session),
) -> ConversationService:
    repository = ConversationRepository(session)
    return ConversationService(session, repository)


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
    conversations: ConversationService = Depends(get_conversation_service),
    user_id: int = Depends(get_current_user_id),
) -> StreamingResponse:
    conversation = await conversations.get_or_create(
        conversation_id=data.conversation_id,
        organisation_id=data.organisation_id,
        user_id=user_id,
        first_question=data.question,
    )
    history = []
    if data.conversation_id is not None:
        detail = await conversations.get_detail(
            data.conversation_id, data.organisation_id, user_id
        )
        history = [
            {"role": m.role, "content": m.content} for m in detail.messages
        ]

    await conversations.add_message(
        conversation_id=conversation.id, role="user", content=data.question
    )

    async def event_stream():
        yield _sse_format("conversation", {"conversation_id": conversation.id})

        answer_parts: list[str] = []
        sources_payload: list[dict] = []

        async for kind, payload in service.query_stream(data, history):
            if kind == "sources":
                sources_payload = [s.model_dump() for s in payload]
                yield _sse_format("sources", {"sources": sources_payload})
            else:
                answer_parts.append(payload)
                yield _sse_format("token", {"text": payload})

        answer = "".join(answer_parts)
        await conversations.add_message(
            conversation_id=conversation.id,
            role="assistant",
            content=answer,
            sources=sources_payload or None,
        )

        yield _sse_format("done", {})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
