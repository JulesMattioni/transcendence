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
    """
    Database model representing an application user.

    Attributes:
        id: Primary key.
        first_name: User's first name.
        last_name: User's last name.
        email: User's unique email address, used for login.
        location: Optional user location.
        avatar_id: ID of the user's selected avatar.
        hashed_password: Bcrypt hash of the user's password.
        is_2fa_enabled: Whether two-factor authentication is enabled.
        secret_2fa: Base32 TOTP secret used for 2FA, if enabled.
        tokens: Refresh tokens issued to this user.
        oauth_accounts: OAuth accounts linked to this user.
        created_at: Timestamp of user creation.
    """

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
    """
    Database model representing a refresh token issued to a user.

    Attributes:
        id: Primary key.
        token: The refresh token string.
        user_id: ID of the user the token belongs to.
        user: The user the token belongs to.
        created_at: Timestamp of token creation.
        expired_at: Timestamp at which the token expires.
    """

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
    """
    Database model representing an OAuth account linked to a user.

    Attributes:
        id: Primary key.
        provider: Name of the OAuth provider (e.g. "google", "42").
        provider_user_id: User ID as returned by the OAuth provider.
        user_id: ID of the linked user.
        user: The linked user.
        created_at: Timestamp of account linking.
    """

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
