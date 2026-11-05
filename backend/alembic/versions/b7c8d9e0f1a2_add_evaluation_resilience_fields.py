"""add evaluation resilience fields

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("candidate_cvs")}
    if "status" not in columns:
        op.add_column(
            "candidate_cvs",
            sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        )
        op.create_index("ix_candidate_cvs_status", "candidate_cvs", ["status"])
    op.execute(
        "UPDATE candidate_cvs SET status = CASE "
        "WHEN processing_status = 'processed' AND error_message IS NULL "
        "THEN 'pending' WHEN processing_status = 'failed' THEN 'error' "
        "WHEN processing_status = 'processing' THEN 'processing' ELSE 'pending' END"
    )


def downgrade() -> None:
    op.drop_index("ix_candidate_cvs_status", table_name="candidate_cvs")
    op.drop_column("candidate_cvs", "status")
