"""add structured evaluation filter fields

Revision ID: 8f1a2b3c4d5e
Revises: 75c839f9402e
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "8f1a2b3c4d5e"
down_revision: Union[str, None] = "75c839f9402e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("candidate_evaluations", sa.Column("experience_range", sa.String(20), nullable=False, server_default="0-2"))
    op.add_column("candidate_evaluations", sa.Column("education_level", sa.String(20), nullable=False, server_default="tecnico"))


def downgrade() -> None:
    op.drop_column("candidate_evaluations", "education_level")
    op.drop_column("candidate_evaluations", "experience_range")
