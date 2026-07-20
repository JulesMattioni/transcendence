from shared.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationships
from sqlalchemy import DateTime, String, Integer, ForeignKey, func
from datetime import datetime


class Role(Base):
    __tablename__ = "role"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    permission: Mapped[list["Permission"]] = relationships(
        "permission_role",
        lazy="selectin"  # async
    )


class Permission(Base):
    __tablename__ = "permission"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)


class PermissionRoles(Base):
    __tablename__ = "permission_roles"
    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("role.id"))
    permission_id: Mapped[int] = mapped_column(ForeignKey("permission.id"))


class OrganisationMember(Base):
    __tablename__ = "organisation_member"
    id: Mapped[int] = mapped_column(primary_key=True)

    org_id: Mapped[int] = mapped_column(
        ForeignKey("organisation.id", ondelete="CASCADE")
    )
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    role_id: Mapped[int] = mapped_column(Integer)


class Organisation(Base):
    __tablename__ = "organisation"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
