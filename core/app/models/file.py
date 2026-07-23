from shared.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, String, func
from datetime import datetime


class File(Base):
    """
    ORM model of an uploaded file (table "files").

    filepath is the internal storage location and is never exposed to
    clients; filename keeps the original upload name for downloads.
    """

    __tablename__ = "files"
    id: Mapped[int] = mapped_column(primary_key=True)
    filepath: Mapped[str] = mapped_column(String(1024))
    title: Mapped[str] = mapped_column(String(255))
    filename: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    organisation_id: Mapped[int] = mapped_column()
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column()
    owner_id: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
