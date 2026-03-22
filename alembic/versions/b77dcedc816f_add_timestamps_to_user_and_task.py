"""add timestamps to user and task

Revision ID: b77dcedc816f
Revises: ce862c7cbffd
Create Date: 2026-03-22 11:50:53.865554

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b77dcedc816f'
down_revision: Union[str, Sequence[str], None] = 'ce862c7cbffd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'tasks',
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    op.add_column(
        'tasks',
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    op.add_column(
        'users',
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    op.add_column(
        'users',
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    op.alter_column('tasks', 'created_at', server_default=None)
    op.alter_column('tasks', 'updated_at', server_default=None)
    op.alter_column('users', 'created_at', server_default=None)
    op.alter_column('users', 'updated_at', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'created_at')
    op.drop_column('tasks', 'updated_at')
    op.drop_column('tasks', 'created_at')
