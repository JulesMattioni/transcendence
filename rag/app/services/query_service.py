from sqlalchemy.ext.asyncio import AsyncSession
from shared.base_service import BaseService
from app.repositories.chunk_repository import ChunkRepository
from app.services.embedding_service import embedding_service
from app.services.llm.openai_compatible_service import OpenAICompatibleService
from app.models.chunk import Chunk
from app.schemas.query import QueryRequest, QueryResponse, Source
from app.config import SYSTEM_PROMPT, EXCERPT_MAX_CHARS


class QueryService(BaseService):
    TOP_K = 6

    def __init__(
        self,
        session: AsyncSession,
        repository: ChunkRepository,
        llm: OpenAICompatibleService,
    ) -> None:
        super().__init__()
        self._session = session
        self._repository = repository
        self._llm = llm

    async def query(self, data: QueryRequest) -> QueryResponse:
        question_vector = embedding_service.embed_text(data.question)

        chunks = await self._repository.search_similar(
            embedding=question_vector,
            organisation_id=data.organisation_id,
            k=self.TOP_K,
        )

        if not chunks:
            return QueryResponse(
                answer="No document has been retrieved for this question.",
                sources=[],
            )

        context = self._build_context(chunks)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (f"Excerpt :\n{context}\n\n"
                            f"Question : {data.question}"),
            },
        ]

        result = await self._llm.generate(messages=messages)

        sources = [
            Source(
                file_id=chunk.file_id,
                chunk_index=chunk.chunk_index,
                excerpt=chunk.content[:EXCERPT_MAX_CHARS],
            )
            for chunk in chunks
        ]

        return QueryResponse(answer=result.content, sources=sources)

    def _build_context(self, chunks: list[Chunk]) -> str:
        blocks = [
            f"[{i}] {chunk.content}" for i, chunk in enumerate(chunks, start=1)
        ]
        return "\n\n".join(blocks)
