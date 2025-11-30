"""Add results_data column

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if column exists before adding (safe migration)
    try:
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        columns = [col['name'] for col in inspector.get_columns('audit')]
        
        if 'results_data' not in columns:
            op.add_column('audit', sa.Column('results_data', sqlite.JSON, nullable=True))
    except Exception:
        # Column might already exist, that's fine
        pass


def downgrade() -> None:
    # Check if column exists before removing
    try:
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        columns = [col['name'] for col in inspector.get_columns('audit')]
        
        if 'results_data' in columns:
            op.drop_column('audit', 'results_data')
    except Exception:
        # Column might not exist, that's fine
        pass

