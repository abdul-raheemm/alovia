"""Phase 1: identity and prediction-result tables (DATABASE.md §3.1-3.2, §13).

No Row-Level Security until Phase 8 (DEC-022). Result-table columns entered_values and
range_warnings arrive in Phase 5. users.id has no FK to auth.users (owner decision 2026-11-17).

Revision ID: 0001
Revises:
Create Date: 2026-11-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TZ = sa.DateTime(timezone=True)


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


def _results(table: str, classes: str) -> None:
    op.create_table(
        table,
        _id(),
        sa.Column("input_values", JSONB, nullable=False),
        sa.Column("predicted_class", sa.Text, nullable=False),
        sa.Column("confidence", sa.Double, nullable=False),
        sa.Column("class_probabilities", JSONB, nullable=False),
        sa.Column("top_contributing_factors", JSONB, nullable=False),
        sa.Column("model_version", sa.Text),
        _now("created_at"),
        sa.Column("patient_id", UUID(as_uuid=True), nullable=False),
        sa.Column("entered_by", UUID(as_uuid=True)),
        sa.PrimaryKeyConstraint("id", name=f"pk_{table}"),
        sa.CheckConstraint(
            f"predicted_class IN ({classes})", name=op.f(f"ck_{table}_predicted_class")
        ),
        _fk("patient_id", table, "patients"),
        _fk("entered_by", table, "doctors"),
    )
    op.create_index(
        f"ix_{table}_patient_created", table, ["patient_id", sa.text("created_at DESC")]
    )


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.Text, nullable=False),
        sa.Column("role", sa.Text, nullable=False),
        sa.Column("is_active", sa.Boolean, server_default=sa.true(), nullable=False),
        _now("created_at"),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.CheckConstraint("role IN ('patient', 'doctor', 'admin')", name=op.f("ck_users_role")),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_table(
        "audit_log",  # append-only
        _id(),
        sa.Column("actor_user_id", UUID(as_uuid=True)),
        sa.Column("action", sa.Text, nullable=False),
        sa.Column("entity_type", sa.Text, nullable=False),
        sa.Column("entity_id", sa.Text),
        sa.Column("patient_id", UUID(as_uuid=True)),  # no FK: kept after deletion requests
        sa.Column("details", JSONB),
        _now("created_at"),
        sa.PrimaryKeyConstraint("id", name="pk_audit_log"),
        _fk("actor_user_id", "audit_log", "users"),
    )
    op.create_index("ix_audit_log_patient_id", "audit_log", ["patient_id"])
    op.create_table(
        "consents",
        _id(),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("consent_version", sa.Text, nullable=False),
        sa.Column("age_confirmed_18_plus", sa.Boolean, server_default=sa.false(), nullable=False),
        sa.Column("accepted_at", TZ, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_consents"),
        _fk("user_id", "consents", "users"),
    )
    op.create_table(
        "doctors",
        _id(),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("specialty", sa.Text),
        sa.Column("is_active", sa.Boolean, server_default=sa.true(), nullable=False),
        _now("created_at"),
        sa.PrimaryKeyConstraint("id", name="pk_doctors"),
        sa.UniqueConstraint("user_id", name="uq_doctors_user_id"),
        _fk("user_id", "doctors", "users"),
    )
    op.create_table(
        "patients",
        _id(),
        sa.Column("user_id", UUID(as_uuid=True)),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("age", sa.Integer),
        sa.Column("notes", sa.Text),
        sa.Column("due_date", sa.Date),
        sa.Column("lmp_date", sa.Date),
        sa.Column("due_date_source", sa.Text),
        sa.Column("pregnancy_status", sa.Text, server_default=sa.text("'active'"), nullable=False),
        sa.Column("pregnancy_ended_at", TZ),
        sa.Column("doctor_informed_of_end", sa.Boolean),
        sa.Column("created_by", UUID(as_uuid=True)),
        _now("created_at"),
        _now("updated_at"),
        sa.PrimaryKeyConstraint("id", name="pk_patients"),
        sa.CheckConstraint(
            "due_date_source IN ('lmp_estimate', 'clinician_confirmed', 'ultrasound')",
            name=op.f("ck_patients_due_date_source"),
        ),
        sa.CheckConstraint(
            "pregnancy_status IN ('active', 'ended_birth', 'ended_loss', 'ended_not_specified')",
            name=op.f("ck_patients_pregnancy_status"),
        ),
        sa.UniqueConstraint("user_id", name="uq_patients_user_id"),
        _fk("user_id", "patients", "users"),
        _fk("created_by", "patients", "users"),
    )
    op.create_table(
        "doctor_patient_assignments",
        _id(),
        sa.Column("doctor_id", UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", UUID(as_uuid=True), nullable=False),
        sa.Column("is_primary", sa.Boolean, server_default=sa.false(), nullable=False),
        sa.Column("assigned_by", UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_at", TZ, nullable=False),
        sa.Column("removed_at", TZ),
        sa.PrimaryKeyConstraint("id", name="pk_doctor_patient_assignments"),
        _fk("doctor_id", "doctor_patient_assignments", "doctors"),
        _fk("patient_id", "doctor_patient_assignments", "patients"),
        _fk("assigned_by", "doctor_patient_assignments", "users"),
    )
    op.create_index(
        "ix_doctor_patient_assignments_patient_id", "doctor_patient_assignments", ["patient_id"]
    )
    op.create_index(
        "ix_assignments_active_doctor",
        "doctor_patient_assignments",
        ["doctor_id"],
        postgresql_where=sa.text("removed_at IS NULL"),
    )
    op.create_index(
        "uq_assignments_active_doctor_patient",
        "doctor_patient_assignments",
        ["doctor_id", "patient_id"],
        unique=True,
        postgresql_where=sa.text("removed_at IS NULL"),
    )
    op.create_index(
        "uq_assignments_one_primary",
        "doctor_patient_assignments",
        ["patient_id"],
        unique=True,
        postgresql_where=sa.text("is_primary AND removed_at IS NULL"),
    )
    op.create_table(
        "patient_invites",
        _id(),
        sa.Column("patient_id", UUID(as_uuid=True), nullable=False),
        sa.Column("code_hash", sa.Text, nullable=False),  # never the code itself
        sa.Column("created_by", UUID(as_uuid=True), nullable=False),
        _now("created_at"),
        sa.Column("expires_at", TZ, nullable=False),
        sa.Column("used_at", TZ),
        sa.Column("used_by_user_id", UUID(as_uuid=True)),
        sa.PrimaryKeyConstraint("id", name="pk_patient_invites"),
        sa.UniqueConstraint("code_hash", name="uq_patient_invites_code_hash"),
        _fk("patient_id", "patient_invites", "patients"),
        _fk("created_by", "patient_invites", "users"),
        _fk("used_by_user_id", "patient_invites", "users"),
    )
    op.create_index("ix_patient_invites_patient_id", "patient_invites", ["patient_id"])
    _results("fetal_results", "'Normal', 'Suspect', 'Pathological'")
    _results("maternal_results", "'Low', 'Mid', 'High'")


def downgrade() -> None:
    # reverse order of creation; indexes go with their tables
    for table in (
        "maternal_results",
        "fetal_results",
        "patient_invites",
        "doctor_patient_assignments",
        "patients",
        "doctors",
        "consents",
        "audit_log",
        "users",
    ):
        op.drop_table(table)
