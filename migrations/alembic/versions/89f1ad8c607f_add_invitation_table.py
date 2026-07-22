"""add invitation table

Revision ID: 89f1ad8c607f
Revises: cd32eaae41a4
Create Date: 2026-07-22 15:36:12.724995

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '89f1ad8c607f'
down_revision: Union[str, Sequence[str], None] = 'cd32eaae41a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'invitation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('invited_user_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('last_name', sa.String(length=255), nullable=True),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column(
            'status',
            sa.String(length=20),
            server_default='pending',
            nullable=False,
        ),
        sa.Column('invited_by', sa.Integer(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['org_id'], ['organisation.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_invitation_org_id'), 'invitation', ['org_id'], unique=False
    )
    op.create_index(
        op.f('ix_invitation_invited_user_id'),
        'invitation',
        ['invited_user_id'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_invitation_invited_user_id'), table_name='invitation')
    op.drop_index(op.f('ix_invitation_org_id'), table_name='invitation')
    op.drop_table('invitation')
