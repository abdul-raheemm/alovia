"""Doctor sides of other modules on the patient page: genetic review (Genetic §10, Dashboard
§12), doctor notes (§15). Appointments, dates and pregnancy status go straight through the
Journey service from the router (§8.3, §16, §17); the symptom view through the symptoms
service (§13)."""

import uuid

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.dashboard import service as dashboard
from app.modules.dashboard.models import DoctorNote
from app.modules.dashboard.schemas import (
    DoctorAssessmentOut,
    GeneticCorrectIn,
    NoteIn,
    NoteOut,
)
from app.modules.genetic import engine
from app.modules.genetic import service as genetic
from app.modules.genetic.models import GeneticAssessment
from app.modules.genetic.rules import GeneticRules
from app.modules.users.models import Doctor, DoctorPatientAssignment, Patient
from app.modules.users.service import DoctorAccount, add_audit, assigned_patient

# ---- genetic review ----


def _assessment_out(db: Session, row: GeneticAssessment) -> DoctorAssessmentOut:
    patient_name = db.scalar(select(Patient.name).where(Patient.id == row.patient_id)) or ""
    return DoctorAssessmentOut(
        id=row.id,
        patient_id=row.patient_id,
        patient_name=patient_name,
        created_at=row.created_at,
        rules_version=row.rules_version,
        review_status=row.review_status,
        priority=row.priority,
        risk_indicated=row.risk_indicated,
        result=engine.Assessment.model_validate(row.results),
        inputs=row.inputs,
        doctor_note=row.doctor_note,
        reviewed_at=row.reviewed_at,
        reviewed_by_name=genetic.reviewer_name_for(db, row.reviewed_by),
        supersedes_id=row.supersedes_id,
        replaced=genetic.is_replaced(db, row.id),
        by_doctor=db.scalar(select(Patient.user_id).where(Patient.id == row.patient_id))
        != row.submitted_by,
    )


def review_queue(db: Session, doctor_id: uuid.UUID) -> list[DoctorAssessmentOut]:
    """Genetic §10.1 for the doctor's assigned patients."""
    patient_ids = list(
        db.scalars(
            select(DoctorPatientAssignment.patient_id).where(
                DoctorPatientAssignment.doctor_id == doctor_id,
                DoctorPatientAssignment.removed_at.is_(None),
            )
        )
    )
    return [_assessment_out(db, r) for r in genetic.review_queue(db, patient_ids)]


def patient_assessments(db: Session, patient: Patient) -> list[DoctorAssessmentOut]:
    return [_assessment_out(db, r) for r in genetic.patient_assessments(db, patient.id)]


def _assigned_assessment(
    db: Session, account: DoctorAccount, assessment_id: uuid.UUID
) -> GeneticAssessment:
    row = genetic.get_row(db, assessment_id)
    if row is None:
        raise AppError("NOT_FOUND", "We couldn't find this.", status=404)
    assigned_patient(db, account.doctor.id, row.patient_id)  # 404 when not assigned
    return row


def confirm(
    db: Session, account: DoctorAccount, assessment_id: uuid.UUID, note: str
) -> DoctorAssessmentOut:
    _assigned_assessment(db, account, assessment_id)
    return _assessment_out(
        db, genetic.confirm(db, account.user, account.doctor.id, assessment_id, note)
    )


def correct(
    db: Session,
    account: DoctorAccount,
    assessment_id: uuid.UUID,
    body: GeneticCorrectIn,
    rules: GeneticRules,
) -> DoctorAssessmentOut:
    _assigned_assessment(db, account, assessment_id)
    row = genetic.correct(
        db, account.user, account.doctor.id, assessment_id, body.inputs, body.doctor_note, rules
    )
    return _assessment_out(db, row)


# ---- §15 doctor notes ----


def _note_out(note: DoctorNote, doctor_name: str) -> NoteOut:
    return NoteOut(
        id=note.id,
        body=note.body,
        visible_to_patient=note.visible_to_patient,
        doctor_name=doctor_name,
        created_at=note.created_at,
        related_ref=note.related_ref,
    )


def list_notes(db: Session, patient: Patient) -> list[NoteOut]:
    """All notes on the patient (private and shared), newest first, doctors only."""
    rows = db.execute(
        select(DoctorNote, Doctor.name)
        .join(Doctor, Doctor.id == DoctorNote.doctor_id)
        .where(DoctorNote.patient_id == patient.id)
        .order_by(DoctorNote.created_at.desc())
    )
    return [_note_out(n, name) for n, name in rows]


def write_note(db: Session, account: DoctorAccount, patient: Patient, body: NoteIn) -> NoteOut:
    """Notes are never edited or deleted; corrections are new notes (§15)."""
    note = dashboard.add_note(db, patient.id, account.doctor.id, body.body, body.visible_to_patient)
    add_audit(db, account.user, "note written", "doctor_note", note.id, patient.id)
    db.commit()
    db.refresh(note)
    return _note_out(note, account.doctor.name)


def share_note(db: Session, account: DoctorAccount, note_id: uuid.UUID) -> NoteOut:
    """§15: a private note can be shared later; the only change a note allows (false -> true)."""
    note = db.get(DoctorNote, note_id)
    if note is None:
        raise AppError("NOT_FOUND", "We couldn't find this.", status=404)
    assigned_patient(db, account.doctor.id, note.patient_id)
    changed = db.scalar(
        update(DoctorNote)
        .where(DoctorNote.id == note_id, DoctorNote.visible_to_patient.is_(False))
        .values(visible_to_patient=True)
        .returning(DoctorNote.id)
    )
    if changed is None:
        raise AppError("CONFLICT", "This note is already shared.", status=409)
    add_audit(db, account.user, "note shared", "doctor_note", note.id, note.patient_id)
    db.commit()
    db.refresh(note)
    name = db.scalar(select(Doctor.name).where(Doctor.id == note.doctor_id)) or ""
    return _note_out(note, name)
