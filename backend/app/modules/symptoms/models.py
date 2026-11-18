"""Symptom Tracking tables (Symptom spec §13.3, DATABASE.md §3.4). Phase 3, migration 0003.

Both tables are append-only: no edits or deletes in v1. Row-Level Security arrives in Phase 8
(DEC-022).
"""

import uuid
from datetime import datetime, time
from typing import Any

from sqlalchemy import CheckConstraint, Index, Integer, Text, Time, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, created_now, fk, uuid_pk

SEVERITIES = "'mild', 'moderate', 'severe'"
DURATIONS = (
    "'under_1_hour', '1_to_6_hours', 'most_of_the_day', 'more_than_1_day', "
    "'under_12_hours', 'more_than_12_hours'"
)
BODY_AREAS = "'head', 'chest', 'upper_abdomen', 'lower_abdomen', 'back', 'pelvis', 'legs', 'other'"


class SymptomCheckin(Base):
    """One submission (§2 "check-in") with its red-flag result (§10, D12)."""

    __tablename__ = "symptom_checkins"
    id: Mapped[uuid.UUID] = uuid_pk()
    patient_id: Mapped[uuid.UUID] = fk("patients.id")
    source: Mapped[str] = mapped_column(Text)
    pregnancy_week: Mapped[int | None] = mapped_column(Integer)  # at submission; null = no date
    red_flag_level: Mapped[str] = mapped_column(Text)
    matched_rules: Mapped[list[str]] = mapped_column(JSONB)
    message_keys: Mapped[list[str]] = mapped_column(JSONB)
    pattern_changes: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)  # doctors only (§9)
    rules_version: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = created_now()
    __table_args__ = (
        CheckConstraint("source IN ('form', 'urgent_button')", name="source"),
        CheckConstraint("red_flag_level IN ('L0', 'L1', 'L2')", name="red_flag_level"),
        # history screens (DATABASE.md §6); also serves every lookup by patient_id
        Index("ix_symptom_checkins_patient_created", "patient_id", text("created_at DESC")),
    )


class SymptomLog(Base):
    """One symptom entry inside a check-in (§2 "symptom entry")."""

    __tablename__ = "symptom_logs"
    id: Mapped[uuid.UUID] = uuid_pk()
    checkin_id: Mapped[uuid.UUID] = fk("symptom_checkins.id", index=True)
    patient_id: Mapped[uuid.UUID] = fk("patients.id", index=True)  # copied for fast queries
    symptom: Mapped[str] = mapped_column(Text)
    severity: Mapped[str | None] = mapped_column(Text)
    duration: Mapped[str | None] = mapped_column(Text)
    body_area: Mapped[str | None] = mapped_column(Text)
    # checkboxes, PUQE answers/score/band, craving text, appetite choice, `other` name (§13.3)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    occurred_at: Mapped[time | None] = mapped_column(Time)
    notes: Mapped[str | None] = mapped_column(Text)  # never read by the rules (§1.2)
    created_at: Mapped[datetime] = created_now()
    __table_args__ = (
        CheckConstraint(f"severity IN ({SEVERITIES})", name="severity"),
        CheckConstraint(f"duration IN ({DURATIONS})", name="duration"),
        CheckConstraint(f"body_area IN ({BODY_AREAS})", name="body_area"),
        CheckConstraint("char_length(notes) <= 500", name="notes_length"),
    )
