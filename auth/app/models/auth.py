from shared.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    DateTime,
    String,
    Text,
    ForeignKey,
    func,
    UniqueConstraint,
)
from datetime import datetime
from typing import List


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    location: Mapped[str | None] = mapped_column()
    avatar_id: Mapped[int] = mapped_column(default=1)
    hashed_password: Mapped[str] = mapped_column(Text)
    is_2fa_enabled: Mapped[bool] = mapped_column(default=False)
    secret_2fa: Mapped[str | None] = mapped_column()
    tokens: Mapped[List["RefreshToken"]] = relationship(back_populates="user")
    oauth_accounts: Mapped[List["OAuthAccount"]] = relationship(
        back_populates="user"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class RefreshToken(Base):
    __tablename__ = "tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(Text)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    user: Mapped["User"] = relationship(back_populates="tokens")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(50))
    provider_user_id: Mapped[str] = mapped_column(String(255))
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    user: Mapped["User"] = relationship(back_populates="oauth_accounts")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (UniqueConstraint("provider", "provider_user_id"),)
