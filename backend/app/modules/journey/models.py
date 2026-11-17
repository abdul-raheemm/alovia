"""Pregnancy Journey tables (DATABASE.md §3.3, Journey spec §14.2). Phase 2, migration 0002.

journey_content and size_reference are created only when content_source = knowledge_base
(Phase 7+); until then content comes from backend/content/*.yaml.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Index,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, created_now, fk, uuid_pk

SOURCES = "'lmp_estimate', 'clinician_confirmed', 'ultrasound'"
STATUSES = "'active', 'ended_birth', 'ended_loss', 'ended_not_specified'"
NOTIFICATION_TYPES = (
    "'new_week', 'new_month', 'appointment_soon', 'doctor_note', "
    "'result_available', 'genetic_reviewed', 'dates_updated'"
)


class PregnancyDateHistory(Base):
    __tablename__ = "pregnancy_date_history"  # append-only
    id: Mapped[uuid.UUID] = uuid_pk()
    patient_id: Mapped[uuid.UUID] = fk("patients.id", index=True)
    changed_by: Mapped[uuid.UUID] = fk("users.id")
    old_due_date: Mapped[date | None] = mapped_column(Date)
    new_due_date: Mapped[date | None] = mapped_column(Date)
    old_source: Mapped[str | None] = mapped_column(Text)
    new_source: Mapped[str | None] = mapped_column(Text)
    old_status: Mapped[str | None] = mapped_column(Text)
    new_status: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created_now()
    __table_args__ = (
        CheckConstraint(f"old_source IN ({SOURCES})", name="old_source"),
        CheckConstraint(f"new_source IN ({SOURCES})", name="new_source"),
        CheckConstraint(f"old_status IN ({STATUSES})", name="old_status"),
        CheckConstraint(f"new_status IN ({STATUSES})", name="new_status"),
    )


class Appointment(Base):
    """Planning data, not a clinical record: hard delete is allowed (DATABASE.md §8)."""

    __tablename__ = "appointments"
    id: Mapped[uuid.UUID] = uuid_pk()
    patient_id: Mapped[uuid.UUID] = fk("patients.id")
    # time optional: a date-only appointment is stored at 00:00 with has_time = false (§14.2)
    appointment_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    has_time: Mapped[bool] = mapped_column(Boolean)
    title: Mapped[str] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID] = fk("users.id")
    source: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = created_now()
    updated_at: Mapped[datetime] = created_now()  # the backend sets it on every change
    __table_args__ = (
        CheckConstraint("source IN ('patient', 'doctor')", name="source"),
        CheckConstraint("char_length(title) <= 100", name="title_length"),
        CheckConstraint("char_length(note) <= 500", name="note_length"),
        # also serves every lookup by patient_id (as DEC-035 for the result tables)
        Index("ix_appointments_patient_at", "patient_id", "appointment_at"),
    )


class Notification(Base):
    """In-app notifications only (Journey D11)."""

    __tablename__ = "notifications"
    id: Mapped[uuid.UUID] = uuid_pk()
    patient_id: Mapped[uuid.UUID] = fk("patients.id")
    type: Mapped[str] = mapped_column(Text)
    target_ref: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created_now()
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint(f"type IN ({NOTIFICATION_TYPES})", name="type"),
        # one notification per (patient, type, target), even when target_ref is empty;
        # the constraint's leading patient_id also serves lookups by patient
        UniqueConstraint("patient_id", "type", "target_ref", postgresql_nulls_not_distinct=True),
    )
