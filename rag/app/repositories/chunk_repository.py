from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from app.models.chunk import Chunk


class ChunkRepository:
    """
    Data-access layer for Chunk. The ONLY layer that talks SQL.

    It receives an AsyncSession and never creates one itself: the caller
    (the service) owns the session and the transaction boundary.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize the repository with its database session.

        Args:
            session: Async SQLAlchemy session used for all queries.
        """

        self._session = session

    async def delete_by_file(self, file_id: int) -> None:
        """
        Delete every chunk belonging to a file.

        Called before re-ingesting a file so stale chunks never linger.

        Args:
            file_id: Id of the file whose chunks are removed.
        """

        await self._session.execute(
            delete(Chunk).where(Chunk.file_id == file_id)
        )
        await self._session.flush()

    async def add_all(self, chunks: list[Chunk]) -> None:
        """
        Persist a batch of new chunks in one flush.

        Args:
            chunks: Chunk ORM objects to persist.
        """

        self._session.add_all(chunks)
        await self._session.flush()

    async def search_similar(
        self, embedding: list[float], organisation_id: int, k: int
    ) -> list[Chunk]:
        """
        Return the chunks closest to an embedding, within an organisation.

        Ranks by cosine distance against the pgvector column and keeps
        the search scoped to a single organisation's documents.

        Args:
            embedding: Query embedding to compare chunks against.
            organisation_id: Organisation whose chunks are searched.
            k: Maximum number of chunks to return.

        Returns:
            The k nearest chunks, closest first.
        """

        command = (
            select(Chunk)
            .where(Chunk.organisation_id == organisation_id)
            .order_by(Chunk.embedding.cosine_distance(embedding))
            .limit(k)
        )
        result = await self._session.execute(command)
        return list(result.scalars().all())
