from shared.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, String, Integer, ForeignKey, func
from datetime import datetime


class OrganisationMember(Base):
    __tablename__ = "organisation_member"
    id: Mapped[int] = mapped_column(primary_key=True)

    org_id: Mapped[int] = mapped_column(
        ForeignKey("organisation.id", ondelete="CASCADE")
    )
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    role_id: Mapped[int] = mapped_column(Integer)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Organisation(Base):
    __tablename__ = "organisation"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
