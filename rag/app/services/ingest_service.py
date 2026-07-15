import io
from pypdf import PdfReader
from sqlalchemy.ext.asyncio import AsyncSession
from shared.base_service import BaseService
from app.repositories.chunk_repository import ChunkRepository
from app.storage.reader_storage import ReaderStorage
from app.services.embedding_service import embedding_service
from app.models.chunk import Chunk
from app.schemas.ingest import IngestRequest, IngestResponse
from app.exceptions import UnsupportedFileType


class IngestService(BaseService):
    CHUNK_SIZE = 800
    CHUNK_OVERLAP = 100

    def __init__(
        self,
        session: AsyncSession,
        repository: ChunkRepository,
        storage: ReaderStorage,
    ) -> None:
        super().__init__()
        self._session = session
        self._repository = repository
        self._storage = storage

    async def ingest(self, data: IngestRequest) -> IngestResponse:
        raw = self._storage.read_bytes(data.filepath)
        text = self._extract_text(raw, data.content_type)
        pieces = self._chunk(text)

        embeddings = embedding_service.embed_texts(pieces) if pieces else []

        chunks = [
            Chunk(
                file_id=data.file_id,
                organisation_id=data.organisation_id,
                chunk_index=index,
                content=content,
                embedding=vector,
            )
            for index, (content, vector) in enumerate(zip(pieces, embeddings))
        ]

        try:
            await self._repository.delete_by_file(data.file_id)
            if chunks:
                await self._repository.add_all(chunks)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

        return IngestResponse(file_id=data.file_id, chunks_created=len(chunks))

    def _extract_text(self, raw: bytes, content_type: str) -> str:
        if content_type == "application/pdf":
            reader = PdfReader(io.BytesIO(raw))
            parts = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(parts)
        if content_type.startswith("text/"):
            return raw.decode("utf-8", errors="ignore")
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            raise UnsupportedFileType(content_type)

    def _chunk(self, text: str) -> list[str]:
        text = text.strip()
        if not text:
            return []

        chunks: list[str] = []
        start = 0
        step = self.CHUNK_SIZE - self.CHUNK_OVERLAP
        while start < len(text):
            piece = text[start: start + self.CHUNK_SIZE].strip()
            if piece:
                chunks.append(piece)
            start += step

        return chunks
