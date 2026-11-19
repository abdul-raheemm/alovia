"""Prediction results read by other modules (ARCHITECTURE §8: through this service)."""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.predictions.models import FetalResult, MaternalResult

Model = Literal["fetal", "maternal"]
TABLES: dict[Model, type[FetalResult] | type[MaternalResult]] = {
    "fetal": FetalResult,
    "maternal": MaternalResult,
}


@dataclass(frozen=True)
class LatestResult:
    predicted_class: str  # the model label (Dashboard §6)
    created_at: datetime


def latest_result(db: Session, patient_id: uuid.UUID, model: Model) -> LatestResult | None:
    table = TABLES[model]
    row = db.execute(
        select(table.predicted_class, table.created_at)
        .where(table.patient_id == patient_id)
        .order_by(table.created_at.desc())
        .limit(1)
    ).first()
    return LatestResult(row.predicted_class, row.created_at) if row else None
