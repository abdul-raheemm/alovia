"""Identity and access tables (DATABASE.md §3.1, Phase 1). No RLS until Phase 8 (DEC-022)."""

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    false,
    func,
    text,
    true,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )


def _now() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now())


def _fk(target: str, **kwargs: Any) -> Any:
    return mapped_column(ForeignKey(target, ondelete="RESTRICT"), **kwargs)


class User(Base):
    __tablename__ = "users"
    # id = Supabase Auth user id; no FK to auth.users (owner decision 2026-11-17)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(Text, unique=True)
    role: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=true())
    created_at: Mapped[datetime] = _now()
    __table_args__ = (CheckConstraint("role IN ('patient', 'doctor', 'admin')", name="role"),)


class Consent(Base):
    __tablename__ = "consents"
    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = _fk("users.id")
    consent_version: Mapped[str] = mapped_column(Text)
    age_confirmed_18_plus: Mapped[bool] = mapped_column(Boolean, server_default=false())
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Doctor(Base):
    __tablename__ = "doctors"
    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = _fk("users.id", unique=True)
    name: Mapped[str] = mapped_column(Text)
    specialty: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=true())
    created_at: Mapped[datetime] = _now()


class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID | None] = _fk("users.id", unique=True)
    name: Mapped[str] = mapped_column(Text)
    age: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)  # doctor-private, never shown to the patient
    due_date: Mapped[date | None] = mapped_column(Date)
    lmp_date: Mapped[date | None] = mapped_column(Date)
    due_date_source: Mapped[str | None] = mapped_column(Text)
    pregnancy_status: Mapped[str] = mapped_column(Text, server_default=text("'active'"))
    pregnancy_ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    doctor_informed_of_end: Mapped[bool | None] = mapped_column(Boolean)
    created_by: Mapped[uuid.UUID | None] = _fk("users.id")
    created_at: Mapped[datetime] = _now()
    updated_at: Mapped[datetime] = _now()  # the backend sets it on every change
    __table_args__ = (
        CheckConstraint(
            "due_date_source IN ('lmp_estimate', 'clinician_confirmed', 'ultrasound')",
            name="due_date_source",
        ),
        CheckConstraint(
            "pregnancy_status IN ('active', 'ended_birth', 'ended_loss', 'ended_not_specified')",
            name="pregnancy_status",
        ),
    )


class DoctorPatientAssignment(Base):
    __tablename__ = "doctor_patient_assignments"
    id: Mapped[uuid.UUID] = _uuid_pk()
    doctor_id: Mapped[uuid.UUID] = _fk("doctors.id")
    patient_id: Mapped[uuid.UUID] = _fk("patients.id", index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, server_default=false())
    assigned_by: Mapped[uuid.UUID] = _fk("users.id")
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        # one active row per (doctor, patient); one primary doctor per patient among active rows
        Index(
            "uq_assignments_active_doctor_patient",
            "doctor_id",
            "patient_id",
            unique=True,
            postgresql_where=text("removed_at IS NULL"),
        ),
        Index(
            "uq_assignments_one_primary",
            "patient_id",
            unique=True,
            postgresql_where=text("is_primary AND removed_at IS NULL"),
        ),
        Index(
            "ix_assignments_active_doctor",
            "doctor_id",
            postgresql_where=text("removed_at IS NULL"),
        ),
    )


class PatientInvite(Base):
    __tablename__ = "patient_invites"
    id: Mapped[uuid.UUID] = _uuid_pk()
    patient_id: Mapped[uuid.UUID] = _fk("patients.id", index=True)
    code_hash: Mapped[str] = mapped_column(Text, unique=True)  # never the code itself
    created_by: Mapped[uuid.UUID] = _fk("users.id")
    created_at: Mapped[datetime] = _now()
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    used_by_user_id: Mapped[uuid.UUID | None] = _fk("users.id")


class AuditLog(Base):
    __tablename__ = "audit_log"  # append-only
    id: Mapped[uuid.UUID] = _uuid_pk()
    actor_user_id: Mapped[uuid.UUID | None] = _fk("users.id")
    action: Mapped[str] = mapped_column(Text)
    entity_type: Mapped[str] = mapped_column(Text)
    entity_id: Mapped[str | None] = mapped_column(Text)
    # no FK on purpose: the row is kept after deletion requests
    patient_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB)  # never clinical values
    created_at: Mapped[datetime] = _now()
