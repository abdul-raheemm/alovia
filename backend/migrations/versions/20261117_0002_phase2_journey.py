"""Phase 2: Pregnancy Journey tables, plus inbox_items moved forward from Phase 3 (DEC-044).

DATABASE.md §3.3 and §3.6 inbox_items. No Row-Level Security until Phase 8 (DEC-022).

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TZ = sa.DateTime(timezone=True)
SOURCES = "'lmp_estimate', 'clinician_confirmed', 'ultrasound'"
STATUSES = "'active', 'ended_birth', 'ended_loss', 'ended_not_specified'"
NOTIFICATION_TYPES = (
    "'new_week', 'new_month', 'appointment_soon', 'doctor_note', "
    "'result_available', 'genetic_reviewed', 'dates_updated'"
)
INBOX_TYPES = (
    "'symptom_l1', 'symptom_l2', 'pattern_p1', 'pattern_p2', 'pattern_p3', 'pattern_p4', "
    "'pattern_p5', 'genetic_pending', 'genetic_high_priority', 'pregnancy_ended', "
    "'record_uploaded', 'ai_note_flag', 'chat_urgent'"
)


def _id() -> sa.Column[object]:
    return sa.Column(
        "id", UUID(as_uuid=True), server_default=sa.func.gen_random_uuid(), nullable=False
    )


def _now(name: str) -> sa.Column[object]:
    return sa.Column(name, TZ, server_default=sa.func.now(), nullable=False)


def _fk(column: str, table: str, target: str) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(
        [column], [f"{target}.id"], name=f"fk_{table}_{column}_{target}", ondelete="RESTRICT"
    )


def _check(table: str, name: str, condition: str) -> sa.CheckConstraint:
    return sa.CheckConstraint(condition, name=op.f(f"ck_{table}_{name}"))


def upgrade() -> None:
    t = "pregnancy_date_history"  # append-only
    op.create_table(
        t,
        _id(),
        sa.Column("patient_id", UUID(as_uuid=True), nullable=False),
        sa.Column("changed_by", UUID(as_uuid=True), nullable=False),
        sa.Column("old_due_date", sa.Date),
        sa.Column("new_due_date", sa.Date),
        sa.Column("old_source", sa.Text),
        sa.Column("new_source", sa.Text),
        sa.Column("old_status", sa.Text),
        sa.Column("new_status", sa.Text),
        _now("created_at"),
        sa.PrimaryKeyConstraint("id", name=f"pk_{t}"),
        _check(t, "old_source", f"old_source IN ({SOURCES})"),
        _check(t, "new_source", f"new_source IN ({SOURCES})"),
        _check(t, "old_status", f"old_status IN ({STATUSES})"),
        _check(t, "new_status", f"new_status IN ({STATUSES})"),
        _fk("patient_id", t, "patients"),
        _fk("changed_by", t, "users"),
    )
    op.create_index(f"ix_{t}_patient_id", t, ["patient_id"])

    t = "appointments"  # planning data: hard delete allowed
    op.create_table(
        t,
        _id(),
        sa.Column("patient_id", UUID(as_uuid=True), nullable=False),
        sa.Column("appointment_at", TZ, nullable=False),
        sa.Column("has_time", sa.Boolean, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("note", sa.Text),
        sa.Column("created_by", UUID(as_uuid=True), nullable=False),
        sa.Column("source", sa.Text, nullable=False),
        _now("created_at"),
        _now("updated_at"),
        sa.PrimaryKeyConstraint("id", name=f"pk_{t}"),
        _check(t, "source", "source IN ('patient', 'doctor')"),
        _check(t, "title_length", "char_length(title) <= 100"),
        _check(t, "note_length", "char_length(note) <= 500"),
        _fk("patient_id", t, "patients"),
        _fk("created_by", t, "users"),
    )
    op.create_index("ix_appointments_patient_at", t, ["patient_id", "appointment_at"])

    t = "notifications"
    op.create_table(
        t,
        _id(),
        sa.Column("patient_id", UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.Text, nullable=False),
        sa.Column("target_ref", sa.Text),
        _now("created_at"),
        sa.Column("read_at", TZ),
        sa.Column("dismissed_at", TZ),
        sa.PrimaryKeyConstraint("id", name=f"pk_{t}"),
        _check(t, "type", f"type IN ({NOTIFICATION_TYPES})"),
        sa.UniqueConstraint(
            "patient_id",
            "type",
            "target_ref",
            name="uq_notifications_patient_id_type_target_ref",
            postgresql_nulls_not_distinct=True,
        ),
        _fk("patient_id", t, "patients"),
    )

    t = "doctor_notes"  # append-only; only visible_to_patient false -> true
    op.create_table(
        t,
        _id(),
        sa.Column("patient_id", UUID(as_uuid=True), nullable=False),
        sa.Column("doctor_id", UUID(as_uuid=True), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("visible_to_patient", sa.Boolean, server_default=sa.false(), nullable=False),
        sa.Column("related_ref", sa.Text),
        _now("created_at"),
        sa.PrimaryKeyConstraint("id", name=f"pk_{t}"),
        _fk("patient_id", t, "patients"),
        _fk("doctor_id", t, "doctors"),
    )
    op.create_index(f"ix_{t}_patient_id", t, ["patient_id"])

    t = "inbox_items"  # never deleted
    op.create_table(
        t,
        _id(),
        sa.Column("patient_id", UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.Text, nullable=False),
        sa.Column("ref_table", sa.Text, nullable=False),
        sa.Column("ref_id", UUID(as_uuid=True), nullable=False),
        _now("created_at"),
        sa.Column("seen_by", UUID(as_uuid=True)),
        sa.Column("seen_at", TZ),
        sa.PrimaryKeyConstraint("id", name=f"pk_{t}"),
        _check(t, "type", f"type IN ({INBOX_TYPES})"),
        _fk("patient_id", t, "patients"),
        _fk("seen_by", t, "doctors"),
    )
    op.create_index(f"ix_{t}_patient_id", t, ["patient_id"])
    op.create_index(
        "ix_inbox_items_unseen", t, ["patient_id"], postgresql_where=sa.text("seen_at IS NULL")
    )


def downgrade() -> None:
    for table in (
        "inbox_items",
        "doctor_notes",
        "notifications",
        "appointments",
        "pregnancy_date_history",
    ):
        op.drop_table(table)
