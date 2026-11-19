"""Prediction results, Modules 1 & 2, and result sharing (DATABASE.md §3.2). Append-only."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Double,
    ForeignKey,
    Index,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.core.database import Base, created_now, fk, uuid_pk


class _ResultColumns:
    """Columns shared by fetal_results and maternal_results (same table shape)."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    input_values: Mapped[dict[str, Any]] = mapped_column(JSONB)  # model units
    entered_values: Mapped[dict[str, Any] | None] = mapped_column(JSONB)  # values + units as typed
    range_warnings: Mapped[list[str] | None] = mapped_column(JSONB)  # features outside training
    predicted_class: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Double)
    class_probabilities: Mapped[dict[str, Any]] = mapped_column(JSONB)
    top_contributing_factors: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    model_version: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # foreign keys on a shared class must be declared per table
    @declared_attr
    def patient_id(cls) -> Mapped[uuid.UUID]:
        return mapped_column(ForeignKey("patients.id", ondelete="RESTRICT"))

    @declared_attr
    def entered_by(cls) -> Mapped[uuid.UUID | None]:
        return mapped_column(ForeignKey("doctors.id", ondelete="RESTRICT"))


class FetalResult(_ResultColumns, Base):
    __tablename__ = "fetal_results"
    __table_args__ = (
        CheckConstraint(
            "predicted_class IN ('Normal', 'Suspect', 'Pathological')", name="predicted_class"
        ),
        Index("ix_fetal_results_patient_created", "patient_id", text("created_at DESC")),
    )


class MaternalResult(_ResultColumns, Base):
    __tablename__ = "maternal_results"
    __table_args__ = (
        CheckConstraint("predicted_class IN ('Low', 'Mid', 'High')", name="predicted_class"),
        Index("ix_maternal_results_patient_created", "patient_id", text("created_at DESC")),
    )


class ResultShare(Base):
    """A fetal or maternal result made visible to the patient (Dashboard spec §10). Cannot be
    undone. result_id is checked by the backend (it points into one of two tables)."""

    __tablename__ = "result_shares"
    id: Mapped[uuid.UUID] = uuid_pk()
    result_type: Mapped[str] = mapped_column(Text)
    result_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    shared_by: Mapped[uuid.UUID] = fk("doctors.id")
    template_key: Mapped[str] = mapped_column(Text)
    doctor_message: Mapped[str | None] = mapped_column(Text)
    ai_draft_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))  # FK in Phase 6
    created_at: Mapped[datetime] = created_now()
    __table_args__ = (
        CheckConstraint("result_type IN ('fetal', 'maternal')", name="result_type"),
        UniqueConstraint("result_type", "result_id"),
    )
