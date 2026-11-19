"""Prediction results and shares, used by other modules (ARCHITECTURE §8: through this
service). Results and shares are append-only (Dashboard spec §9.2, §10)."""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal, cast

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.predictions.models import FetalResult, MaternalResult, ResultShare
from app.modules.predictions.risk_model import Models

Model = Literal["fetal", "maternal"]
Result = FetalResult | MaternalResult
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


def model_version(models: Models, model: Model) -> str:
    """From the model's metadata file (DATABASE.md §3.2), e.g. "XGBoost 2026-09-17"."""
    meta = getattr(models, model).metadata
    return f"{meta.get('model_type', 'model')} {meta.get('trained_on', 'unknown')}"


def predict_and_save(
    db: Session,
    models: Models,
    model: Model,
    patient_id: uuid.UUID,
    doctor_id: uuid.UUID,
    input_values: dict[str, float],
    entered_values: dict[str, Any],
    range_warnings: list[str],
) -> Result:
    """§9.2 steps 4-5: run the unchanged model on model-unit values and save one row.
    The caller commits."""
    out = getattr(models, model).predict(input_values)
    row = TABLES[model](
        patient_id=patient_id,
        input_values=input_values,
        entered_values=entered_values,
        range_warnings=range_warnings,
        predicted_class=out["predicted_class"],
        confidence=out["confidence"],
        class_probabilities=out["class_probabilities"],
        top_contributing_factors=out["top_contributing_factors"],
        entered_by=doctor_id,
        model_version=model_version(models, model),
    )
    db.add(row)
    db.flush()
    return row


def results(db: Session, patient_id: uuid.UUID, model: Model) -> list[Result]:
    table = TABLES[model]
    return list(
        db.scalars(
            select(table).where(table.patient_id == patient_id).order_by(table.created_at.desc())
        )
    )


def get_result(db: Session, model: Model, result_id: uuid.UUID) -> Result | None:
    return cast(Result | None, db.get(TABLES[model], result_id))


def shares_for(
    db: Session, model: Model, result_ids: list[uuid.UUID]
) -> dict[uuid.UUID, ResultShare]:
    rows = db.scalars(
        select(ResultShare).where(
            ResultShare.result_type == model, ResultShare.result_id.in_(result_ids)
        )
    )
    return {r.result_id: r for r in rows}


def add_share(
    db: Session,
    model: Model,
    result_id: uuid.UUID,
    doctor_id: uuid.UUID,
    template_key: str,
    doctor_message: str | None,
) -> ResultShare:
    """§10 step 3: one share per result; a share cannot be undone. The caller commits."""
    share = ResultShare(
        result_type=model,
        result_id=result_id,
        shared_by=doctor_id,
        template_key=template_key,
        doctor_message=doctor_message,
    )
    db.add(share)
    try:
        db.flush()
    except IntegrityError as exc:  # unique (result_type, result_id)
        db.rollback()
        raise AppError("CONFLICT", "This result is already shared.", status=409) from exc
    return share


@dataclass(frozen=True)
class SharedResult:
    """What the patient may see of a shared result (§10 step 4): never probabilities,
    confidence or factors."""

    share_id: uuid.UUID
    result_type: Model
    result_date: datetime
    shared_at: datetime
    template_key: str
    doctor_message: str | None
    shared_by: uuid.UUID


def shared_results(db: Session, patient_id: uuid.UUID) -> list[SharedResult]:
    found: list[SharedResult] = []
    for model, table in TABLES.items():
        for share, created in db.execute(
            select(ResultShare, table.created_at)
            .join(table, table.id == ResultShare.result_id)
            .where(ResultShare.result_type == model, table.patient_id == patient_id)
        ):
            found.append(
                SharedResult(
                    share.id,
                    model,
                    created,
                    share.created_at,
                    share.template_key,
                    share.doctor_message,
                    share.shared_by,
                )
            )
    return sorted(found, key=lambda r: r.shared_at, reverse=True)
