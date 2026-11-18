"""Phase 3: Symptom Tracking tables (Symptom spec §13.3, DATABASE.md §3.4).

Both append-only. No Row-Level Security until Phase 8 (DEC-022).

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TZ = sa.DateTime(timezone=True)
SEVERITIES = "'mild', 'moderate', 'severe'"
DURATIONS = (
    "'under_1_hour', '1_to_6_hours', 'most_of_the_day', 'more_than_1_day', "
    "'under_12_hours', 'more_than_12_hours'"
)
BODY_AREAS = "'head', 'chest', 'upper_abdomen', 'lower_abdomen', 'back', 'pelvis', 'legs', 'other'"


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
    t = "symptom_checkins"  # append-only
    op.create_table(
        t,
        _id(),
        sa.Column("patient_id", UUID(as_uuid=True), nullable=False),
        sa.Column("source", sa.Text, nullable=False),
        sa.Column("pregnancy_week", sa.Integer),
        sa.Column("red_flag_level", sa.Text, nullable=False),
        sa.Column("matched_rules", JSONB, nullable=False),
        sa.Column("message_keys", JSONB, nullable=False),
        sa.Column("pattern_changes", JSONB, nullable=False),
        sa.Column("rules_version", sa.Text, nullable=False),
        _now("created_at"),
        sa.PrimaryKeyConstraint("id", name=f"pk_{t}"),
        _check(t, "source", "source IN ('form', 'urgent_button')"),
        _check(t, "red_flag_level", "red_flag_level IN ('L0', 'L1', 'L2')"),
        _fk("patient_id", t, "patients"),
    )
    op.create_index(
        "ix_symptom_checkins_patient_created", t, ["patient_id", sa.text("created_at DESC")]
    )

    t = "symptom_logs"  # append-only
    op.create_table(
        t,
        _id(),
        sa.Column("checkin_id", UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", UUID(as_uuid=True), nullable=False),
        sa.Column("symptom", sa.Text, nullable=False),
        sa.Column("severity", sa.Text),
        sa.Column("duration", sa.Text),
        sa.Column("body_area", sa.Text),
        sa.Column("details", JSONB),
        sa.Column("occurred_at", sa.Time),
        sa.Column("notes", sa.Text),
        _now("created_at"),
        sa.PrimaryKeyConstraint("id", name=f"pk_{t}"),
        _check(t, "severity", f"severity IN ({SEVERITIES})"),
        _check(t, "duration", f"duration IN ({DURATIONS})"),
        _check(t, "body_area", f"body_area IN ({BODY_AREAS})"),
        _check(t, "notes_length", "char_length(notes) <= 500"),
        _fk("checkin_id", t, "symptom_checkins"),
        _fk("patient_id", t, "patients"),
    )
    op.create_index(f"ix_{t}_checkin_id", t, ["checkin_id"])
    op.create_index(f"ix_{t}_patient_id", t, ["patient_id"])


def downgrade() -> None:
    for table in ("symptom_logs", "symptom_checkins"):
        op.drop_table(table)
