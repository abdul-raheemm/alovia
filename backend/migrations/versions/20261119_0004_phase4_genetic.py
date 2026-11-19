"""Phase 4: Genetic Risk table (Genetic spec §12.3, DATABASE.md §3.5).

Append-only; no `genetic_conditions` table (D6). No Row-Level Security until Phase 8 (DEC-022).

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TZ = sa.DateTime(timezone=True)


def _fk(column: str, table: str, target: str) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(
        [column], [f"{target}.id"], name=f"fk_{table}_{column}_{target}", ondelete="RESTRICT"
    )


def upgrade() -> None:
    t = "genetic_assessments"
    op.create_table(
        t,
        sa.Column(
            "id", UUID(as_uuid=True), server_default=sa.func.gen_random_uuid(), nullable=False
        ),
        sa.Column("patient_id", UUID(as_uuid=True), nullable=False),
        sa.Column("submitted_by", UUID(as_uuid=True), nullable=False),
        sa.Column("inputs", JSONB, nullable=False),
        sa.Column("results", JSONB, nullable=False),
        sa.Column("rules_version", sa.Text, nullable=False),
        sa.Column("show_numbers_to_patient", sa.Boolean, nullable=False),
        sa.Column("risk_indicated", sa.Boolean, nullable=False),
        sa.Column("priority", sa.Text, nullable=False),
        sa.Column("review_status", sa.Text, nullable=False),
        sa.Column("reviewed_by", UUID(as_uuid=True)),
        sa.Column("reviewed_at", TZ),
        sa.Column("doctor_note", sa.Text),
        sa.Column("supersedes_id", UUID(as_uuid=True)),
        sa.Column("created_at", TZ, server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=f"pk_{t}"),
        sa.CheckConstraint("priority IN ('normal', 'high')", name=op.f(f"ck_{t}_priority")),
        sa.CheckConstraint(
            "review_status IN ('pending_review', 'reviewed')", name=op.f(f"ck_{t}_review_status")
        ),
        _fk("patient_id", t, "patients"),
        _fk("submitted_by", t, "users"),
        _fk("reviewed_by", t, "doctors"),
        _fk("supersedes_id", t, "genetic_assessments"),
    )
    op.create_index(
        "ix_genetic_assessments_patient_created", t, ["patient_id", sa.text("created_at DESC")]
    )
    op.create_index("ix_genetic_assessments_review_priority", t, ["review_status", "priority"])


def downgrade() -> None:
    op.drop_table("genetic_assessments")
