"""normalize education level values to Spanish

Revision ID: 9a2b3c4d5e6f
Revises: 8f1a2b3c4d5e
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "9a2b3c4d5e6f"
down_revision: Union[str, None] = "8f1a2b3c4d5e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE candidate_evaluations "
            "SET education_level = 'técnico' "
            "WHERE education_level = 'tecnico'"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE candidate_evaluations "
            "SET education_level = 'tecnico' "
            "WHERE education_level = 'técnico'"
        )
    )
