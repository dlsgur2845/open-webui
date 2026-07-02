"""add token_jti to auth (0.10.2 rebase)

Revision ID: f1a2b3c4d5e6
Revises: 42e2978c7933
Create Date: 2026-07-02 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = '42e2978c7933'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Older custom deployments may already have the column — keep this idempotent
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [column['name'] for column in inspector.get_columns('auth')]

    if 'token_jti' not in columns:
        op.add_column('auth', sa.Column('token_jti', sa.String(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [column['name'] for column in inspector.get_columns('auth')]

    if 'token_jti' in columns:
        op.drop_column('auth', 'token_jti')
