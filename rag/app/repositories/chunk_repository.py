from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from app.models.chunk import Chunk


class ChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def delete_by_file(self, file_id: int) -> None:
        await self._session.execute(
            delete(Chunk).where(Chunk.file_id == file_id)
        )
        await self._session.flush()

    async def add_all(self, chunks: list[Chunk]) -> None:
        self._session.add_all(chunks)
        await self._session.flush()

    async def search_similar(
        self, embedding: list[float], organisation_id: int, k: int
    ) -> list[Chunk]:
        command = (
            select(Chunk)
            .where(Chunk.organisation_id == organisation_id)
            .order_by(Chunk.embedding.cosine_distance(embedding))
            .limit(k)
        )
        result = await self._session.execute(command)
        return list(result.scalars().all())
