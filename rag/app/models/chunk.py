from shared.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Text, DateTime, func
from pgvector.sqlalchemy import Vector
from datetime import datetime


class Chunk(Base):
    """
    ORM model of an embedded document chunk (table "chunks").

    Each chunk stores a slice of an ingested file's text alongside its
    384-dimensional embedding, so similarity search can retrieve the
    relevant passages. file_id and organisation_id are indexed to scope
    retrieval to one organisation and to delete a file's chunks on
    re-ingestion.
    """

    __tablename__ = "chunks"
    id: Mapped[int] = mapped_column(primary_key=True)
    file_id: Mapped[int] = mapped_column(index=True)
    organisation_id: Mapped[int] = mapped_column(index=True)
    chunk_index: Mapped[int] = mapped_column()
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(384))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
