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
