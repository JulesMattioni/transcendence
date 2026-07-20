from sqlalchemy.ext.asyncio import AsyncSession
from shared.base_service import BaseService
from app.repositories.chunk_repository import ChunkRepository
from app.services.embedding_service import embedding_service
from app.services.rerank_service import rerank_service
from app.services.llm.openai_compatible_service import OpenAICompatibleService
from app.models.chunk import Chunk
from app.schemas.query import QueryRequest, QueryResponse, Source
from app.config import (
    SYSTEM_PROMPT,
    EXCERPT_MAX_CHARS,
    RRF_K,
    EXPANSION_PROMPT,
    TOP_K,
    RERANK_CANDIDATES,
    HISTORY_RAW_LIMIT,
    SUMMARY_PROMPT,
    REWRITE_PROMPT,
)
import json


class QueryService(BaseService):
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
        chunks = await self._retrieve(data.question, data.organisation_id)
        if not chunks:
            return QueryResponse(
                answer=(
                    "No relevant document was found " "to answer the question."
                ),
                sources=[],
            )

        messages = self._build_messages(data.question, chunks)
        result = await self._llm.generate(messages=messages)

        return QueryResponse(
            answer=result.content, sources=self._build_sources(chunks)
        )

    async def query_stream(
        self, data: QueryRequest, history: list[dict] | None = None
    ):
        history = history or []
        summary, recent = await self._build_history(history)

        search_question = await self._rewrite_question(
            data.question, summary, recent
        )

        chunks = await self._retrieve(search_question, data.organisation_id)

        yield ("sources", self._build_sources(chunks))

        if not chunks:
            yield (
                "token",
                "No relevant document was found to answer the question.",
            )
            return

        messages = self._build_messages(data.question, chunks, summary, recent)
        async for token in self._llm.generate_stream(messages=messages):
            yield ("token", token)

    async def _retrieve(
        self, question: str, organisation_id: int
    ) -> list[Chunk]:
        queries = await self._expand_query(question)
        query_vectors = embedding_service.embed_texts(queries)

        ranked_lists = [
            await self._repository.search_similar(
                embedding=vector,
                organisation_id=organisation_id,
                k=10,
            )
            for vector in query_vectors
        ]

        candidates = self._fuse_rrf(ranked_lists, top_n=RERANK_CANDIDATES)
        if not candidates:
            return []
        return self._rerank(question, candidates)

    def _build_context(self, chunks: list[Chunk]) -> str:
        blocks = [
            f"[{i}] {chunk.content}" for i, chunk in enumerate(chunks, start=1)
        ]
        return "\n\n".join(blocks)

    def _fuse_rrf(
        self, ranked_lists: list[list[Chunk]], top_n: int
    ) -> list[Chunk]:
        scores: dict[int, float] = {}
        by_id: dict[int, Chunk] = {}

        for ranked in ranked_lists:
            for rank, chunk in enumerate(ranked):
                scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (
                    RRF_K + rank
                )
                by_id[chunk.id] = chunk

        best_ids = sorted(scores, key=scores.get, reverse=True)[:top_n]
        return [by_id[cid] for cid in best_ids]

    async def _expand_query(self, question: str) -> list[str]:
        messages = [
            {"role": "system", "content": EXPANSION_PROMPT},
            {"role": "user", "content": question},
        ]
        try:
            result = await self._llm.generate(messages=messages)
            payload = json.loads(self._extract_json(result.content))
            variants = payload.get("variants", [])
            hyde = payload.get("hyde", "")
        except Exception:
            return [question]

        queries = [question]
        queries.extend(v for v in variants if isinstance(v, str) and v.strip())
        if isinstance(hyde, str) and hyde.strip():
            queries.append(hyde)
        return queries

    def _extract_json(self, text: str) -> str:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start: end + 1]
        return text

    def _rerank(self, question: str, chunks: list[Chunk]) -> list[Chunk]:
        ranked = rerank_service.rerank(question, [c.content for c in chunks])
        return [chunks[idx] for idx, _ in ranked[:TOP_K]]

    def _build_messages(
        self,
        question: str,
        chunks: list[Chunk],
        summary: str = "",
        recent: list[dict] | None = None,
    ) -> list[dict]:
        context = self._build_context(chunks)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if summary:
            messages.append(
                {
                    "role": "system",
                    "content": f"Summary of earlier conversation:\n{summary}",
                }
            )
        for m in recent or []:
            messages.append({"role": m["role"], "content": m["content"]})

        messages.append(
            {
                "role": "user",
                "content": f"Excerpts:\n{context}\n\nQuestion: {question}",
            }
        )
        return messages

    def _build_sources(self, chunks: list[Chunk]) -> list[Source]:
        return [
            Source(
                file_id=chunk.file_id,
                chunk_index=chunk.chunk_index,
                excerpt=chunk.content[:EXCERPT_MAX_CHARS],
            )
            for chunk in chunks
        ]

    async def _summarize(self, messages: list[dict]) -> str:
        transcript = "\n".join(
            f"{m['role']}: {m['content']}" for m in messages
        )
        prompt = [
            {"role": "system", "content": SUMMARY_PROMPT},
            {"role": "user", "content": transcript},
        ]
        try:
            result = await self._llm.generate(messages=prompt)
            return result.content.strip()
        except Exception:
            return ""

    async def _build_history(
        self, messages: list[dict]
    ) -> tuple[str, list[dict]]:
        if len(messages) <= HISTORY_RAW_LIMIT:
            return "", messages

        old = messages[:-HISTORY_RAW_LIMIT]
        recent = messages[-HISTORY_RAW_LIMIT:]
        summary = await self._summarize(old)
        return summary, recent

    async def _rewrite_question(
        self, question: str, summary: str, recent: list[dict]
    ) -> str:
        if not summary and not recent:
            return question

        context_parts = []
        if summary:
            context_parts.append(
                f"Summary of earlier conversation:\n{summary}"
            )
        if recent:
            transcript = "\n".join(
                f"{m['role']}: {m['content']}" for m in recent
            )
            context_parts.append(f"Recent messages:\n{transcript}")
        context = "\n\n".join(context_parts)

        prompt = [
            {"role": "system", "content": REWRITE_PROMPT},
            {
                "role": "user",
                "content": f"{context}\n\nFollow-up question: {question}",
            },
        ]
        try:
            result = await self._llm.generate(messages=prompt)
            rewritten = result.content.strip()
            return rewritten or question
        except Exception:
            return question
