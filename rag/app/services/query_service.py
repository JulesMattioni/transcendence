from typing import AsyncIterator
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
    """
    Service answering questions from an organisation's documents (RAG).

    Runs the retrieval-augmented pipeline: expand the question, retrieve
    candidate chunks, fuse and rerank them, then ask the LLM to answer
    grounded in the selected excerpts. Supports a one-shot answer and a
    streaming variant that also folds in prior conversation history.
    """

    def __init__(
        self,
        session: AsyncSession,
        repository: ChunkRepository,
        llm: OpenAICompatibleService,
    ) -> None:
        """
        Initialize the service with its collaborators.

        Args:
            session: Async SQLAlchemy session used for reads.
            repository: Repository for chunk retrieval.
            llm: OpenAI-compatible client used for expansion, rewriting,
            summarising and answer generation.
        """

        super().__init__()
        self._session = session
        self._repository = repository
        self._llm = llm

    async def query(self, data: QueryRequest) -> QueryResponse:
        """
        Answer a question in one shot, without conversation history.

        Retrieves the relevant chunks and, when any are found, asks the
        LLM to answer grounded in them; otherwise returns a fixed
        no-document message with no sources.

        Args:
            data: Question and the organisation to search within.

        Returns:
            QueryResponse with the answer and the cited sources.
        """

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
    ) -> AsyncIterator[tuple[str, list[Source] | str]]:
        """
        Answer a question as a stream, using conversation history.

        Folds the prior history into a summary plus recent turns, rewrites
        the question into a standalone form for retrieval, then yields the
        sources once followed by the answer token by token. When no chunk
        is found it yields a single no-document token instead.

        Args:
            data: Question and the organisation to search within.
            history: Prior messages as {"role", "content"} dicts, or None.

        Yields:
            ("sources", list[Source]) once, then ("token", str) for each
            generated token.
        """

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
        """
        Retrieve the most relevant chunks for a question.

        Expands the question into several queries, runs a vector search
        per query, fuses the ranked lists with reciprocal rank fusion,
        then reranks the fused candidates with the cross-encoder.

        Args:
            question: Question to retrieve chunks for.
            organisation_id: Organisation whose chunks are searched.

        Returns:
            The top reranked chunks, most relevant first; empty when the
            organisation has no matching chunk.
        """

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
        """
        Render chunks as a numbered context block for the prompt.

        The [1], [2] markers line up with the citation markers the model
        is instructed to use, so its citations map back to these chunks.

        Args:
            chunks: Chunks to include, in the order they should be cited.

        Returns:
            The chunks joined into one numbered, blank-line-separated
            string.
        """

        blocks = [
            f"[{i}] {chunk.content}" for i, chunk in enumerate(chunks, start=1)
        ]
        return "\n\n".join(blocks)

    def _fuse_rrf(
        self, ranked_lists: list[list[Chunk]], top_n: int
    ) -> list[Chunk]:
        """
        Merge several ranked chunk lists with reciprocal rank fusion.

        A chunk's fused score sums 1 / (RRF_K + rank) across the lists it
        appears in, so chunks ranked highly by several queries rise to the
        top. Deduplicates by chunk id.

        Args:
            ranked_lists: One ranked list of chunks per expanded query.
            top_n: Maximum number of fused candidates to keep.

        Returns:
            The top_n chunks by fused score, best first.
        """

        scores: dict[int, float] = {}
        by_id: dict[int, Chunk] = {}

        for ranked in ranked_lists:
            for rank, chunk in enumerate(ranked):
                scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (
                    RRF_K + rank
                )
                by_id[chunk.id] = chunk

        best_ids = sorted(
            scores, key=lambda cid: scores[cid], reverse=True
        )[:top_n]
        return [by_id[cid] for cid in best_ids]

    async def _expand_query(self, question: str) -> list[str]:
        """
        Expand a question into several retrieval queries.

        Asks the LLM for alternative phrasings plus a hypothetical answer
        (HyDE) to widen recall. The original question is always kept, and
        any LLM failure degrades gracefully to just that question.

        Args:
            question: Original user question.

        Returns:
            The question followed by its usable variants and HyDE
            paragraph; just the question on failure.
        """

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
        """
        Extract the JSON object substring from an LLM reply.

        Models sometimes wrap the JSON in prose or code fences; this keeps
        only the outermost {...} span so json.loads can parse it.

        Args:
            text: Raw LLM reply expected to contain a JSON object.

        Returns:
            The substring from the first "{" to the last "}", or the whole
            text when no such span exists.
        """

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start: end + 1]
        return text

    def _rerank(self, question: str, chunks: list[Chunk]) -> list[Chunk]:
        """
        Rerank fused candidates and keep the best TOP_K.

        Args:
            question: Original question the chunks are scored against.
            chunks: Fused candidate chunks to rerank.

        Returns:
            The TOP_K most relevant chunks, best first.
        """

        ranked = rerank_service.rerank(question, [c.content for c in chunks])
        return [chunks[idx] for idx, _ in ranked[:TOP_K]]

    def _build_messages(
        self,
        question: str,
        chunks: list[Chunk],
        summary: str = "",
        recent: list[dict] | None = None,
    ) -> list[dict]:
        """
        Assemble the chat messages sent to the LLM to answer.

        Starts from the grounding system prompt, optionally injects a
        summary of earlier turns and the recent messages, then appends the
        excerpts and the question as the final user turn.

        Args:
            question: Question to answer.
            chunks: Retrieved chunks used as grounding excerpts.
            summary: Summary of older conversation turns, or "".
            recent: Recent conversation messages to replay, or None.

        Returns:
            The ordered list of chat messages for the LLM.
        """

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
        """
        Turn chunks into truncated Source citations for the client.

        Args:
            chunks: Chunks cited by the answer, in citation order.

        Returns:
            One Source per chunk, its excerpt truncated to
            EXCERPT_MAX_CHARS.
        """

        return [
            Source(
                file_id=chunk.file_id,
                chunk_index=chunk.chunk_index,
                excerpt=chunk.content[:EXCERPT_MAX_CHARS],
            )
            for chunk in chunks
        ]

    async def _summarize(self, messages: list[dict]) -> str:
        """
        Summarize older conversation turns into a short paragraph.

        Keeps the LLM context small while preserving the facts a
        follow-up might reference. Any LLM failure degrades to "".

        Args:
            messages: Older messages to condense.

        Returns:
            The summary text, or "" on failure.
        """

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
        """
        Split history into a summary of old turns plus recent turns.

        Up to HISTORY_RAW_LIMIT messages are kept verbatim; anything older
        is summarized so long conversations stay within the LLM context.

        Args:
            messages: Full conversation history, oldest first.

        Returns:
            A (summary, recent_messages) pair; summary is "" when nothing
            was old enough to condense.
        """

        if len(messages) <= HISTORY_RAW_LIMIT:
            return "", messages

        old = messages[:-HISTORY_RAW_LIMIT]
        recent = messages[-HISTORY_RAW_LIMIT:]
        summary = await self._summarize(old)
        return summary, recent

    async def _rewrite_question(
        self, question: str, summary: str, recent: list[dict]
    ) -> str:
        """
        Rewrite a follow-up into a standalone question for retrieval.

        Resolves pronouns and references against the conversation context
        so vector search sees a self-contained query. With no context, or
        on LLM failure, the original question is returned unchanged.

        Args:
            question: Follow-up question, possibly context-dependent.
            summary: Summary of earlier turns, or "".
            recent: Recent messages providing context, possibly empty.

        Returns:
            The standalone question, or the original when no rewrite
            applies.
        """

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
