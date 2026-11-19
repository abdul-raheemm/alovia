"""Genetic assessments: validate, run the rules, save, notify the doctor's inbox, read history
(Genetic spec §4.1, §6-10; API.md §4.4). Doctor review: §10."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.logging import logger
from app.modules.dashboard import service as dashboard
from app.modules.genetic import engine
from app.modules.genetic.models import GeneticAssessment
from app.modules.genetic.rules import GeneticRules
from app.modules.genetic.schemas import AssessmentIn, AssessmentOut
from app.modules.users.models import Doctor, Patient, User
from app.modules.users.service import add_audit


def _patient_view(row: GeneticAssessment) -> AssessmentOut:
    """§8.2 / §10.4: numbers are shown when the setting allowed it at creation, or after review."""
    result = engine.Assessment.model_validate(row.results)
    show = row.show_numbers_to_patient or row.review_status == "reviewed"
    conditions = [
        c if show else c.model_copy(
            update={"outcomes": None, "outcomes_if_boy": None, "outcomes_if_girl": None}
        )
        for c in result.conditions
    ]  # fmt: skip
    return AssessmentOut(
        assessment_id=row.id,
        created_at=row.created_at,
        rules_version=row.rules_version,
        review_status=row.review_status,
        show_numbers_to_patient=show,
        conditions=conditions,
        flags=result.flags,
        message_keys=result.message_keys,
        disclaimer_key=result.disclaimer_key,
        doctor_note=row.doctor_note if row.review_status == "reviewed" else None,
        reviewed_at=row.reviewed_at,
        inputs=row.inputs,
    )


def create_assessment(
    db: Session, user: User, patient: Patient, body: AssessmentIn, rules: GeneticRules
) -> AssessmentOut:
    """§4.1 steps 6-8: validate (E1/E2: nothing saved), run the engine, save as pending review,
    and add the doctor's inbox items in the same transaction (DEC-071)."""
    try:
        inputs = engine.validate(body.model_dump(exclude_none=True), rules)
    except engine.GeneticInputError as exc:
        raise AppError(
            "VALIDATION_ERROR", "Please check your answers.", fields={exc.field: exc.code}
        ) from exc
    result = engine.assess(inputs, rules)
    if any(c.rule_id == "E4" for c in result.conditions):  # §6.3 E4: logged, never a number
        logger.error("genetic engine failed", extra={"reason": "E4 safe fallback"})
    row = GeneticAssessment(
        patient_id=patient.id,
        submitted_by=user.id,
        inputs=inputs,
        results=result.model_dump(mode="json"),
        rules_version=result.rules_version,
        show_numbers_to_patient=result.show_numbers_to_patient,
        risk_indicated=result.flags.risk_indicated,
        priority=result.priority,
        review_status=result.review_status,
    )
    db.add(row)
    db.flush()
    dashboard.add_inbox_item(db, patient.id, "genetic_pending", "genetic_assessments", row.id)
    if result.priority == "high":
        dashboard.add_inbox_item(
            db, patient.id, "genetic_high_priority", "genetic_assessments", row.id
        )
    db.commit()
    db.refresh(row)
    return _patient_view(row)


def list_assessments(db: Session, patient: Patient) -> list[AssessmentOut]:
    rows = db.scalars(
        select(GeneticAssessment)
        .where(GeneticAssessment.patient_id == patient.id)
        .order_by(GeneticAssessment.created_at.desc())
    )
    return [_patient_view(r) for r in rows]


def get_assessment(db: Session, patient: Patient, assessment_id: uuid.UUID) -> AssessmentOut:
    row = db.scalar(
        select(GeneticAssessment).where(
            GeneticAssessment.id == assessment_id, GeneticAssessment.patient_id == patient.id
        )
    )
    if row is None:  # missing or another patient's: the same answer (API.md §6)
        raise AppError("NOT_FOUND", "We couldn't find this.", status=404)
    return _patient_view(row)


@dataclass(frozen=True)
class LatestReview:
    """Doctor-side genetic status of the latest assessment (Dashboard §5.1, §6)."""

    review_status: str  # pending_review / reviewed
    priority: str  # normal / high
    created_at: datetime


def latest_review(db: Session, patient_id: uuid.UUID) -> LatestReview | None:
    row = db.execute(
        select(
            GeneticAssessment.review_status,
            GeneticAssessment.priority,
            GeneticAssessment.created_at,
        )
        .where(GeneticAssessment.patient_id == patient_id)
        .order_by(GeneticAssessment.created_at.desc())
        .limit(1)
    ).first()
    return LatestReview(row.review_status, row.priority, row.created_at) if row else None


def mother_haemoglobin_status(db: Session, patient_id: uuid.UUID) -> str | None:
    """Dashboard §9.5: the mother's haemoglobin-group status in the latest assessment, or None
    when there is no assessment or no answer."""
    inputs = db.scalar(
        select(GeneticAssessment.inputs)
        .where(GeneticAssessment.patient_id == patient_id)
        .order_by(GeneticAssessment.created_at.desc())
        .limit(1)
    )
    mother = ((inputs or {}).get("haemoglobin_group") or {}).get("mother") or {}
    status = mother.get("status")
    return status if isinstance(status, str) else None


GeneticCheck = Literal["reviewed", "sent_to_doctor", "needs_testing", "pending_review"]


def latest_check(db: Session, patient_id: uuid.UUID) -> GeneticCheck | None:
    """Journey §10.4 "Genetic check" status card: the latest assessment's overall state
    (labels DEC-073), or None when she has none."""
    row = db.scalar(
        select(GeneticAssessment)
        .where(GeneticAssessment.patient_id == patient_id)
        .order_by(GeneticAssessment.created_at.desc())
        .limit(1)
    )
    if row is None:
        return None
    if row.review_status == "reviewed":
        return "reviewed"
    statuses = {c["status"] for c in row.results.get("conditions", [])}
    if statuses & {"conflict", "error"}:
        return "sent_to_doctor"
    if "needs_testing_or_counselling" in statuses:
        return "needs_testing"
    return "pending_review"


# ---- §10 doctor case review (Dashboard spec §12) ----


def review_queue(db: Session, patient_ids: list[uuid.UUID]) -> list[GeneticAssessment]:
    """§10.1: pending assessments of these patients that no correction has replaced, high
    priority first, then oldest first."""
    replaced = select(GeneticAssessment.supersedes_id).where(
        GeneticAssessment.supersedes_id.is_not(None)
    )
    return list(
        db.scalars(
            select(GeneticAssessment)
            .where(
                GeneticAssessment.patient_id.in_(patient_ids),
                GeneticAssessment.review_status == "pending_review",
                GeneticAssessment.id.not_in(replaced),
            )
            .order_by((GeneticAssessment.priority == "high").desc(), GeneticAssessment.created_at)
        )
    )


def patient_assessments(db: Session, patient_id: uuid.UUID) -> list[GeneticAssessment]:
    return list(
        db.scalars(
            select(GeneticAssessment)
            .where(GeneticAssessment.patient_id == patient_id)
            .order_by(GeneticAssessment.created_at.desc())
        )
    )


def get_row(db: Session, assessment_id: uuid.UUID) -> GeneticAssessment | None:
    return db.get(GeneticAssessment, assessment_id)


def is_replaced(db: Session, assessment_id: uuid.UUID) -> bool:
    return (
        db.scalar(
            select(GeneticAssessment.id).where(GeneticAssessment.supersedes_id == assessment_id)
        )
        is not None
    )


def _lock_pending(db: Session, assessment_id: uuid.UUID) -> GeneticAssessment:
    """Dashboard §12: lock the row, then refuse if it was already reviewed or corrected, so
    the second of two doctors acting at once is rejected ("already reviewed by Dr X")."""
    row = db.scalar(
        select(GeneticAssessment).where(GeneticAssessment.id == assessment_id).with_for_update()
    )
    if row is None:
        raise AppError("NOT_FOUND", "We couldn't find this.", status=404)
    done = row if row.review_status == "reviewed" else None
    if done is None:
        done = db.scalar(select(GeneticAssessment).where(GeneticAssessment.supersedes_id == row.id))
    if done is not None:
        raise AppError(
            "CONFLICT",
            f"Already reviewed by {reviewer_name_for(db, done.reviewed_by) or 'another doctor'}.",
            status=409,
        )
    return row


def reviewer_name_for(db: Session, doctor_id: uuid.UUID | None) -> str | None:
    if doctor_id is None:
        return None
    return db.scalar(select(Doctor.name).where(Doctor.id == doctor_id))


def confirm(
    db: Session, user: User, doctor_id: uuid.UUID, assessment_id: uuid.UUID, note: str
) -> GeneticAssessment:
    """§10.3 Confirm: the note is required; review columns are written once. The note also
    appears in the patient's Doctor notes, linked to the assessment (Journey §10.3)."""
    row = _lock_pending(db, assessment_id)
    row.review_status = "reviewed"
    row.reviewed_by = doctor_id
    row.reviewed_at = datetime.now(UTC)
    row.doctor_note = note
    dashboard.add_note(db, row.patient_id, doctor_id, note, True, f"genetic_assessment:{row.id}")
    add_audit(db, user, "genetic reviewed", "genetic_assessment", row.id, row.patient_id)
    db.commit()
    return row


def correct(
    db: Session,
    user: User,
    doctor_id: uuid.UUID,
    assessment_id: uuid.UUID,
    body: AssessmentIn,
    note: str,
    rules: GeneticRules,
) -> GeneticAssessment:
    """§10.3 Correct inputs: a new assessment from the corrected answers, run by the engine,
    reviewed at once with the doctor's note; the old row is never edited (§14 test 10)."""
    old = _lock_pending(db, assessment_id)
    try:
        inputs = engine.validate(body.model_dump(exclude_none=True), rules)
    except engine.GeneticInputError as exc:
        raise AppError(
            "VALIDATION_ERROR", "Please check the answers.", fields={exc.field: exc.code}
        ) from exc
    result = engine.assess(inputs, rules)
    if any(c.rule_id == "E4" for c in result.conditions):
        logger.error("genetic engine failed", extra={"reason": "E4 safe fallback"})
    now = datetime.now(UTC)
    row = GeneticAssessment(
        patient_id=old.patient_id,
        submitted_by=user.id,
        inputs=inputs,
        results=result.model_dump(mode="json"),
        rules_version=result.rules_version,
        show_numbers_to_patient=result.show_numbers_to_patient,
        risk_indicated=result.flags.risk_indicated,
        priority=result.priority,
        review_status="reviewed",
        reviewed_by=doctor_id,
        reviewed_at=now,
        doctor_note=note,
        supersedes_id=old.id,
    )
    db.add(row)
    db.flush()
    dashboard.add_note(db, row.patient_id, doctor_id, note, True, f"genetic_assessment:{row.id}")
    add_audit(db, user, "genetic corrected", "genetic_assessment", row.id, row.patient_id)
    db.commit()
    return row


def reviewed_ids(db: Session, patient_id: uuid.UUID) -> list[uuid.UUID]:
    """Journey §10.1 `genetic_reviewed`: each assessment a doctor reviewed."""
    return list(
        db.scalars(
            select(GeneticAssessment.id).where(
                GeneticAssessment.patient_id == patient_id,
                GeneticAssessment.review_status == "reviewed",
            )
        )
    )
