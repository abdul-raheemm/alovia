"""Prediction results, Modules 1 & 2 (DATABASE.md §3.2). Append-only.

Phase 5 adds entered_values and range_warnings (DATABASE.md §13); they are not created here.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, Double, ForeignKey, Index, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.core.database import Base


class _ResultColumns:
    """Columns shared by fetal_results and maternal_results (same table shape)."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    input_values: Mapped[dict[str, Any]] = mapped_column(JSONB)  # model units
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
