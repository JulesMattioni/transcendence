from datetime import datetime
from shared.database import Base
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class Conversation(Base):
    """
    ORM model of a chat conversation (table "conversations").

    A conversation groups the messages exchanged between one user and the
    assistant. organisation_id and user_id are indexed and together scope
    ownership: a conversation is only ever served to the user who created
    it, within its organisation.
    """

    __tablename__ = "conversations"
    id: Mapped[int] = mapped_column(primary_key=True)
    organisation_id: Mapped[int] = mapped_column(index=True)
    user_id: Mapped[int] = mapped_column(index=True)
    title: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
