"""Tables shared between the Journey and the Doctor Dashboard (DATABASE.md §3.3, §3.6).

doctor_notes is owned jointly with the Dashboard spec. inbox_items moved from Phase 3 into
migration 0002 (DEC-044) so the pregnancy-end flow can notify the doctor (Journey §11.3).
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Text, false, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, created_now, fk, uuid_pk

INBOX_TYPES = (
    "'symptom_l1', 'symptom_l2', 'pattern_p1', 'pattern_p2', 'pattern_p3', 'pattern_p4', "
    "'pattern_p5', 'genetic_pending', 'genetic_high_priority', 'pregnancy_ended', "
    "'record_uploaded', 'ai_note_flag', 'chat_urgent'"
)


class DoctorNote(Base):
    """Append-only. The only change allowed: visible_to_patient false -> true (backend rule)."""

    __tablename__ = "doctor_notes"
    id: Mapped[uuid.UUID] = uuid_pk()
    patient_id: Mapped[uuid.UUID] = fk("patients.id", index=True)
    doctor_id: Mapped[uuid.UUID] = fk("doctors.id")
    body: Mapped[str] = mapped_column(Text)
    visible_to_patient: Mapped[bool] = mapped_column(Boolean, server_default=false())
    related_ref: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created_now()


class InboxItem(Base):
    """Doctor's needs-attention inbox. Never deleted."""

    __tablename__ = "inbox_items"
    id: Mapped[uuid.UUID] = uuid_pk()
    patient_id: Mapped[uuid.UUID] = fk("patients.id", index=True)
    type: Mapped[str] = mapped_column(Text)
    ref_table: Mapped[str] = mapped_column(Text)
    ref_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = created_now()
    seen_by: Mapped[uuid.UUID | None] = fk("doctors.id")
    seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint(f"type IN ({INBOX_TYPES})", name="type"),
        Index("ix_inbox_items_unseen", "patient_id", postgresql_where=text("seen_at IS NULL")),
    )


class MedicalRecord(Base):
    """An uploaded file in the private Storage bucket (Dashboard spec §14). Not deleted in v1."""

    __tablename__ = "medical_records"
    id: Mapped[uuid.UUID] = uuid_pk()
    patient_id: Mapped[uuid.UUID] = fk("patients.id", index=True)
    uploaded_by: Mapped[uuid.UUID] = fk("doctors.id")
    file_type: Mapped[str] = mapped_column(Text)
    storage_path: Mapped[str] = mapped_column(Text, unique=True)
    original_filename: Mapped[str] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    uploaded_at: Mapped[datetime] = created_now()
    __table_args__ = (
        CheckConstraint(
            "file_type IN ('ultrasound', 'blood_report', 'prescription', 'other')",
            name="file_type",
        ),
    )


class RuleSignoff(Base):
    """A doctor's tick and comment on one rule-review row (Dashboard spec §19). Append-only:
    the newest row per (module, rules_version, item_id) is the current state."""

    __tablename__ = "rule_signoffs"
    id: Mapped[uuid.UUID] = uuid_pk()
    module: Mapped[str] = mapped_column(Text)
    rules_version: Mapped[str] = mapped_column(Text)
    item_id: Mapped[str] = mapped_column(Text)
    checked: Mapped[bool] = mapped_column(Boolean)
    comment: Mapped[str | None] = mapped_column(Text)
    doctor_id: Mapped[uuid.UUID] = fk("doctors.id")
    created_at: Mapped[datetime] = created_now()
    __table_args__ = (
        CheckConstraint("module IN ('genetic', 'symptom', 'journey')", name="module"),
        Index("ix_rule_signoffs_module_version", "module", "rules_version"),
    )
