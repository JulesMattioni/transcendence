"""add org member user info

Revision ID: cd32eaae41a4
Revises: d3220205d04e
Create Date: 2026-07-22 14:52:23.629314

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cd32eaae41a4'
down_revision: Union[str, Sequence[str], None] = 'd3220205d04e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("organisation_member", sa.Column("email", sa.String(length=255), nullable=True))
    op.add_column("organisation_member", sa.Column("first_name", sa.String(length=255), nullable=True))
    op.add_column("organisation_member", sa.Column("last_name", sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("organisation_member", "last_name")
    op.drop_column("organisation_member", "first_name")
    op.drop_column("organisation_member", "email")

