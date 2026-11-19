"""Phase 5: Doctor Dashboard (Dashboard spec §22, DATABASE.md §3.2, §3.6).

Adds entered_values and range_warnings to both result tables, and the result_shares,
medical_records and rule_signoffs tables. ai_drafts is Phase 6 (DEC-085).
No Row-Level Security until Phase 8 (DEC-022).

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TZ = sa.DateTime(timezone=True)
RESULT_TABLES = ("fetal_results", "maternal_results")


def _id() -> sa.Column[object]:
    return sa.Column(
        "id", UUID(as_uuid=True), server_default=sa.func.gen_random_uuid(), nullable=False
    )


def _created(name: str = "created_at") -> sa.Column[object]:
    return sa.Column(name, TZ, server_default=sa.func.now(), nullable=False)


def _fk(column: str, table: str, target: str) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(
        [column], [f"{target}.id"], name=f"fk_{table}_{column}_{target}", ondelete="RESTRICT"
    )


def upgrade() -> None:
    for t in RESULT_TABLES:
        op.add_column(t, sa.Column("entered_values", JSONB))
        op.add_column(t, sa.Column("range_warnings", JSONB))

    t = "result_shares"
    op.create_table(
        t,
        _id(),
        sa.Column("result_type", sa.Text, nullable=False),
        sa.Column("result_id", UUID(as_uuid=True), nullable=False),
        sa.Column("shared_by", UUID(as_uuid=True), nullable=False),
        sa.Column("template_key", sa.Text, nullable=False),
        sa.Column("doctor_message", sa.Text),
        sa.Column("ai_draft_id", UUID(as_uuid=True)),
        _created(),
        sa.PrimaryKeyConstraint("id", name=f"pk_{t}"),
        sa.CheckConstraint(
            "result_type IN ('fetal', 'maternal')", name=op.f(f"ck_{t}_result_type")
        ),
        sa.UniqueConstraint("result_type", "result_id", name=f"uq_{t}_result_type_result_id"),
        _fk("shared_by", t, "doctors"),
    )

    t = "medical_records"
    op.create_table(
        t,
        _id(),
        sa.Column("patient_id", UUID(as_uuid=True), nullable=False),
        sa.Column("uploaded_by", UUID(as_uuid=True), nullable=False),
        sa.Column("file_type", sa.Text, nullable=False),
        sa.Column("storage_path", sa.Text, nullable=False),
        sa.Column("original_filename", sa.Text, nullable=False),
        sa.Column("note", sa.Text),
        _created("uploaded_at"),
        sa.PrimaryKeyConstraint("id", name=f"pk_{t}"),
        sa.CheckConstraint(
            "file_type IN ('ultrasound', 'blood_report', 'prescription', 'other')",
            name=op.f(f"ck_{t}_file_type"),
        ),
        sa.UniqueConstraint("storage_path", name=f"uq_{t}_storage_path"),
        _fk("patient_id", t, "patients"),
        _fk("uploaded_by", t, "doctors"),
    )
    op.create_index(f"ix_{t}_patient_id", t, ["patient_id"])

    t = "rule_signoffs"
    op.create_table(
        t,
        _id(),
        sa.Column("module", sa.Text, nullable=False),
        sa.Column("rules_version", sa.Text, nullable=False),
        sa.Column("item_id", sa.Text, nullable=False),
        sa.Column("checked", sa.Boolean, nullable=False),
        sa.Column("comment", sa.Text),
        sa.Column("doctor_id", UUID(as_uuid=True), nullable=False),
        _created(),
        sa.PrimaryKeyConstraint("id", name=f"pk_{t}"),
        sa.CheckConstraint(
            "module IN ('genetic', 'symptom', 'journey')", name=op.f(f"ck_{t}_module")
        ),
        _fk("doctor_id", t, "doctors"),
    )
    op.create_index("ix_rule_signoffs_module_version", t, ["module", "rules_version"])


def downgrade() -> None:
    op.drop_table("rule_signoffs")
    op.drop_table("medical_records")
    op.drop_table("result_shares")
    for t in RESULT_TABLES:
        op.drop_column(t, "range_warnings")
        op.drop_column(t, "entered_values")
