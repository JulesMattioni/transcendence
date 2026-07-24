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
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import CHUNK_OVERLAP, CHUNK_SIZE


class IngestService(BaseService):
    """
    Service turning an uploaded file into embedded, searchable chunks.

    Reads the binary from the shared uploads volume, extracts its text,
    splits it into overlapping chunks, embeds them and persists them.
    Coordinates the repository and storage and owns the transaction
    boundary: it is the only layer that commits or rolls back.
    """

    def __init__(
        self,
        session: AsyncSession,
        repository: ChunkRepository,
        storage: ReaderStorage,
    ) -> None:
        """
        Initialize the service with its collaborators.

        Args:
            session: Async SQLAlchemy session used for transactions.
            repository: Repository for Chunk persistence.
            storage: Read-only access to the uploads volume.
        """

        super().__init__()
        self._session = session
        self._repository = repository
        self._storage = storage

    async def ingest(self, data: IngestRequest) -> IngestResponse:
        """
        Ingest a file: extract, chunk, embed and persist its chunks.

        Re-ingestion is idempotent: the file's existing chunks are
        deleted first, so a re-uploaded file never leaves stale chunks.
        The delete and insert share one transaction.

        Args:
            data: Ingestion request with the file id, organisation,
            storage path and content type.

        Returns:
            IngestResponse with the file id and the number of chunks
            created.

        Raises:
            UnsupportedFileType: If the content type cannot be decoded to
            text.
            FileNotFoundError: If the binary is missing from storage.
        """

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
        """
        Decode a binary into plain text according to its content type.

        PDFs are read page by page; text/* is decoded as UTF-8 ignoring
        errors; anything else is attempted as strict UTF-8 and rejected if
        it is not decodable.

        Args:
            raw: Raw file bytes.
            content_type: MIME type driving the extraction strategy.

        Returns:
            The extracted text.

        Raises:
            UnsupportedFileType: If the bytes cannot be decoded to text.
        """

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
        """
        Split text into overlapping chunks for embedding.

        Uses a recursive splitter that prefers natural boundaries
        (paragraphs, then lines, then sentences) so chunks stay coherent;
        the overlap preserves context across chunk edges.

        Args:
            text: Full document text to split.

        Returns:
            The list of chunk strings, empty when the text is blank.
        """

        text = text.strip()
        if not text:
            return []

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        return splitter.split_text(text)
