"""Genetic assessments: validate, run the rules, save, notify the doctor's inbox, read history
(Genetic spec §4.1, §6-10; API.md §4.4). The doctor's review and corrections are Phase 5."""

import uuid
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
from app.modules.users.models import Patient, User


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
