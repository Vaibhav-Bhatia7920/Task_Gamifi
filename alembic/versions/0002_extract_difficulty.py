"""add extracted content and difficulty score

Revision ID: 0002_extract_difficulty
Revises: 0001_initial
Create Date: 2026-09-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_extract_difficulty"
down_revision: Union[str, Sequence[str], None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("timeline", sa.Column("extracted_content", sa.Text(), nullable=True))
    op.add_column(
        "timeline",
        sa.Column("difficulty_score", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("timeline", "difficulty_score")
    op.drop_column("timeline", "extracted_content")
