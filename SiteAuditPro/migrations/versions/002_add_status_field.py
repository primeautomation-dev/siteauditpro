"""Add status field to Audit model

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if column exists before adding (safe migration)
    try:
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        columns = [col['name'] for col in inspector.get_columns('audit')]
        
        if 'status' not in columns:
            op.add_column('audit', sa.Column('status', sa.String(), nullable=True, server_default='pending'))
            # Update existing records to 'completed' if they have results_data
            op.execute("UPDATE audit SET status = 'completed' WHERE results_data IS NOT NULL")
    except Exception:
        # Column might already exist, that's fine
        pass


def downgrade() -> None:
    # Check if column exists before removing
    try:
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        columns = [col['name'] for col in inspector.get_columns('audit')]
        
        if 'status' in columns:
            op.drop_column('audit', 'status')
    except Exception:
        # Column might not exist, that's fine
        pass

