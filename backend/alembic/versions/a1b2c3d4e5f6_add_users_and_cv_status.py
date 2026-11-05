"""add users and candidate tracking statuses

Revision ID: a1b2c3d4e5f6
Revises: 9a2b3c4d5e6f
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "9a2b3c4d5e6f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "users" not in inspector.get_table_names():
        op.execute(
            "DO $$ BEGIN CREATE TYPE user_role AS ENUM ('admin', 'recruiter'); "
            "EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
        )
        table_role_enum = postgresql.ENUM("admin", "recruiter", name="user_role", create_type=False)
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("email", sa.String(255), nullable=False),
            sa.Column("hashed_password", sa.String(255), nullable=False),
            sa.Column("role", table_role_enum, nullable=False, server_default="recruiter"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("email"),
        )
        op.create_index("ix_users_id", "users", ["id"])
        op.create_index("ix_users_email", "users", ["email"])

    columns = {column["name"] for column in inspector.get_columns("candidate_cvs")}
    if "application_status" not in columns:
        op.add_column(
            "candidate_cvs",
            sa.Column("application_status", sa.String(30), nullable=False, server_default="PENDIENTE"),
        )
        op.create_index("ix_candidate_cvs_application_status", "candidate_cvs", ["application_status"])
    if "extraction_status" not in columns:
        op.add_column(
            "candidate_cvs",
            sa.Column("extraction_status", sa.String(30), nullable=False, server_default="PENDIENTE"),
        )
    op.execute(
        "UPDATE candidate_cvs SET extraction_status = CASE "
        "WHEN processing_status = 'failed' THEN 'ERROR_FORMATO' ELSE 'OK' END"
    )


def downgrade() -> None:
    op.drop_index("ix_candidate_cvs_application_status", table_name="candidate_cvs")
    op.drop_column("candidate_cvs", "application_status")
    op.drop_column("candidate_cvs", "extraction_status")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
    sa.Enum(name="user_role").drop(op.get_bind(), checkfirst=True)
