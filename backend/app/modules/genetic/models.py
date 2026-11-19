"""Genetic Risk table (Genetic spec §12.3, DATABASE.md §3.5). Phase 4, migration 0004.

Append-only: rows are never deleted; only the review columns are filled in, once (Phase 5).
No `genetic_conditions` table: the rules are YAML files (D6). RLS arrives in Phase 8 (DEC-022).
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, created_now, fk, uuid_pk


class GeneticAssessment(Base):
    __tablename__ = "genetic_assessments"
    id: Mapped[uuid.UUID] = uuid_pk()
    patient_id: Mapped[uuid.UUID] = fk("patients.id")
    submitted_by: Mapped[uuid.UUID] = fk("users.id")  # the patient, or a doctor's correction
    inputs: Mapped[dict[str, Any]] = mapped_column(JSONB)  # §5 answers as submitted
    results: Mapped[dict[str, Any]] = mapped_column(JSONB)  # §8.2 structure
    rules_version: Mapped[str] = mapped_column(Text)
    show_numbers_to_patient: Mapped[bool] = mapped_column(Boolean)
    risk_indicated: Mapped[bool] = mapped_column(Boolean)
    priority: Mapped[str] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(Text)
    reviewed_by: Mapped[uuid.UUID | None] = fk("doctors.id")
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    doctor_note: Mapped[str | None] = mapped_column(Text)
    supersedes_id: Mapped[uuid.UUID | None] = fk("genetic_assessments.id")
    created_at: Mapped[datetime] = created_now()
    __table_args__ = (
        CheckConstraint("priority IN ('normal', 'high')", name="priority"),
        CheckConstraint("review_status IN ('pending_review', 'reviewed')", name="review_status"),
        # history screens; also serves every lookup by patient_id (DATABASE.md §6)
        Index("ix_genetic_assessments_patient_created", "patient_id", text("created_at DESC")),
        Index("ix_genetic_assessments_review_priority", "review_status", "priority"),  # queue
    )
