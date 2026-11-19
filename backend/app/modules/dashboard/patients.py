"""Doctor home: patient list, patient records, invite links, needs-attention inbox
(Dashboard spec §5-8, API.md §4.6).

Kept apart from dashboard/service.py, which other modules import (journey and symptoms write
inbox items through it); this file reads those modules' services, so the two must not merge.
"""

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import ColumnElement, Select, case, func, select, update
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.dashboard.models import InboxItem
from app.modules.dashboard.schemas import (
    AssignedDoctor,
    GeneticStatus,
    InboxItemOut,
    InviteOut,
    LatestClass,
    PatientDetail,
    PatientIn,
    PatientRow,
    SymptomLevel,
)
from app.modules.genetic import service as genetic
from app.modules.journey import service as journey
from app.modules.journey.config import JourneyConfig
from app.modules.predictions import service as predictions
from app.modules.symptoms import service as symptoms
from app.modules.users.invites import create_invite
from app.modules.users.models import Doctor, DoctorPatientAssignment, Patient, PatientInvite
from app.modules.users.service import DoctorAccount, add_audit

# §6 default order: group 1 and 2 are defined by these unseen item types; 3 = any other unseen
GROUP_1 = {"symptom_l1", "chat_urgent"}
GROUP_2 = {"symptom_l2", "pattern_p5", "genetic_high_priority"}
SEEN_LIMIT = 100  # shortcut: newest seen items only; add paging if doctors need older ones


def _active(doctor_id: uuid.UUID) -> list[ColumnElement[bool]]:
    return [
        DoctorPatientAssignment.doctor_id == doctor_id,
        DoctorPatientAssignment.removed_at.is_(None),
    ]


def _group(unseen: list[tuple[str, datetime]]) -> tuple[int, datetime | None]:
    """§6 group and the time of its newest defining item ("newest item first")."""
    for number, types in ((1, GROUP_1), (2, GROUP_2)):
        times = [t for kind, t in unseen if kind in types]
        if times:
            return number, max(times)
    if unseen:
        return 3, max(t for _, t in unseen)
    return 4, None


def _row_fields(
    db: Session,
    patient: Patient,
    unseen: list[tuple[str, datetime]],
    cfg: JourneyConfig,
    today: date,
) -> dict[str, object]:
    ga = (
        journey.gestational_age_now(patient, cfg, today)
        if patient.pregnancy_status == "active"
        else None
    )
    fetal = predictions.latest_result(db, patient.id, "fetal")
    maternal = predictions.latest_result(db, patient.id, "maternal")
    review = genetic.latest_review(db, patient.id)
    level = symptoms.latest_level(db, patient.id)
    return {
        "id": patient.id,
        "name": patient.name,
        "linked": patient.user_id is not None,
        "ga_weeks": ga[0] if ga else None,
        "ga_days": ga[1] if ga else None,
        "due_date": patient.due_date,
        "fetal": LatestClass(**vars(fetal)) if fetal else None,
        "maternal": LatestClass(**vars(maternal)) if maternal else None,
        "genetic": GeneticStatus(**vars(review)) if review else None,
        "symptom": SymptomLevel(level=level[0], created_at=level[1]) if level else None,
        "unseen_count": len(unseen),
        "pregnancy_status": patient.pregnancy_status,
        "group": _group(unseen)[0],
    }


def _unseen(
    db: Session, patient_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[tuple[str, datetime]]]:
    found: dict[uuid.UUID, list[tuple[str, datetime]]] = {pid: [] for pid in patient_ids}
    for pid, kind, created in db.execute(
        select(InboxItem.patient_id, InboxItem.type, InboxItem.created_at).where(
            InboxItem.patient_id.in_(patient_ids), InboxItem.seen_at.is_(None)
        )
    ):
        found[pid].append((kind, created))
    return found


def list_patients(
    db: Session, doctor_id: uuid.UUID, cfg: JourneyConfig, today: date
) -> list[PatientRow]:
    """§6: the doctor's assigned patients in the default order. Search and filters are applied
    in the doctor app on this list.
    shortcut: a few queries per patient; fine for a clinic's list, batch them if it grows large."""
    patients = list(
        db.scalars(
            select(Patient)
            .join(DoctorPatientAssignment, DoctorPatientAssignment.patient_id == Patient.id)
            .where(*_active(doctor_id))
        )
    )
    unseen = _unseen(db, [p.id for p in patients])

    def order(p: Patient) -> tuple[int, float, str]:
        number, newest = _group(unseen[p.id])
        return (number, -newest.timestamp() if newest else 0.0, p.name.casefold())

    return [
        PatientRow.model_validate(_row_fields(db, p, unseen[p.id], cfg, today))
        for p in sorted(patients, key=order)
    ]


def patient_detail(db: Session, patient: Patient, cfg: JourneyConfig, today: date) -> PatientDetail:
    """§5.1 Overview tab."""
    doctors = [
        AssignedDoctor(id=d.id, name=d.name, is_primary=primary)
        for d, primary in db.execute(
            select(Doctor, DoctorPatientAssignment.is_primary)
            .join(DoctorPatientAssignment, DoctorPatientAssignment.doctor_id == Doctor.id)
            .where(
                DoctorPatientAssignment.patient_id == patient.id,
                DoctorPatientAssignment.removed_at.is_(None),
            )
            .order_by(DoctorPatientAssignment.is_primary.desc(), Doctor.name)
        )
    ]
    unseen = _unseen(db, [patient.id])[patient.id]
    return PatientDetail.model_validate(
        {
            **_row_fields(db, patient, unseen, cfg, today),
            "age": patient.age,
            "notes": patient.notes,
            "due_date_source": patient.due_date_source,
            "doctors": doctors,
        }
    )


def create_patient(db: Session, account: DoctorAccount, body: PatientIn) -> Patient:
    """§8.1: the creating doctor is assigned, and primary (a new record has no primary)."""
    now = datetime.now(UTC)
    patient = Patient(name=body.name, age=body.age, notes=body.notes, created_by=account.user.id)
    db.add(patient)
    db.flush()
    db.add(
        DoctorPatientAssignment(
            doctor_id=account.doctor.id,
            patient_id=patient.id,
            is_primary=True,
            assigned_by=account.user.id,
            assigned_at=now,
        )
    )
    add_audit(db, account.user, "patient created", "patient", patient.id, patient.id)
    db.commit()
    return patient


def update_patient(db: Session, account: DoctorAccount, patient: Patient, body: PatientIn) -> None:
    patient.name, patient.age, patient.notes = body.name, body.age, body.notes
    patient.updated_at = datetime.now(UTC)
    add_audit(db, account.user, "patient edited", "patient", patient.id, patient.id)
    db.commit()


def invite_link(
    db: Session, account: DoctorAccount, patient: Patient, patient_app_url: str
) -> InviteOut:
    """§8.2: a one-time code in a link; a new link cancels an unused earlier one; a record
    that already has a login cannot get a code."""
    if patient.user_id is not None:
        raise AppError("CONFLICT", "This patient has already joined Alovia.", status=409)
    code = create_invite(db, patient.id, account.user.id)  # also writes "invite created"
    expires_at = db.scalar(
        select(func.max(PatientInvite.expires_at)).where(PatientInvite.patient_id == patient.id)
    )
    db.commit()
    assert expires_at is not None
    return InviteOut(link=f"{patient_app_url.rstrip('/')}/join?code={code}", expires_at=expires_at)


def _inbox_query(doctor_id: uuid.UUID) -> Select[InboxItem, str, str]:
    return (
        select(InboxItem, Patient.name, Doctor.name)
        .join(Patient, Patient.id == InboxItem.patient_id)
        .join(DoctorPatientAssignment, DoctorPatientAssignment.patient_id == Patient.id)
        .outerjoin(Doctor, Doctor.id == InboxItem.seen_by)
        .where(*_active(doctor_id))
    )


def _item_out(item: InboxItem, patient_name: str, seen_by_name: str | None) -> InboxItemOut:
    return InboxItemOut(
        id=item.id,
        patient_id=item.patient_id,
        patient_name=patient_name,
        type=item.type,
        ref_table=item.ref_table,
        ref_id=item.ref_id,
        created_at=item.created_at,
        seen_by_name=seen_by_name,
        seen_at=item.seen_at,
    )


def list_inbox(db: Session, doctor_id: uuid.UUID, seen: bool) -> list[InboxItemOut]:
    """§7: items of the doctor's patients. Unseen: all, newest first, AI suggestions below every
    rule-based item (§7.2). Seen: the newest SEEN_LIMIT, with who and when."""
    q = _inbox_query(doctor_id)
    if seen:
        q = q.where(InboxItem.seen_at.is_not(None)).order_by(InboxItem.seen_at.desc())
        q = q.limit(SEEN_LIMIT)
    else:
        ai_last = case((InboxItem.type == "ai_note_flag", 1), else_=0)
        q = q.where(InboxItem.seen_at.is_(None)).order_by(ai_last, InboxItem.created_at.desc())
    return [_item_out(item, pname, dname) for item, pname, dname in db.execute(q)]


def mark_seen(db: Session, account: DoctorAccount, item_id: uuid.UUID) -> InboxItemOut:
    """§7.2: the first doctor to mark an item seen is kept (seen_by, seen_at); marking it again
    changes nothing. Items of patients the doctor is not assigned to are 404."""
    found = db.execute(_inbox_query(account.doctor.id).where(InboxItem.id == item_id)).first()
    if found is None:
        raise AppError("NOT_FOUND", "Item not found.", status=404)
    item, patient_name, _ = found
    changed = db.scalar(
        update(InboxItem)
        .where(InboxItem.id == item_id, InboxItem.seen_at.is_(None))
        .values(seen_by=account.doctor.id, seen_at=datetime.now(UTC))
        .returning(InboxItem.id)
    )
    if changed is not None:
        add_audit(db, account.user, "inbox item seen", "inbox_item", item_id, item.patient_id)
    db.commit()
    db.refresh(item)  # the first doctor's seen_by / seen_at, whoever wrote them
    return _item_out(
        item, patient_name, db.scalar(select(Doctor.name).where(Doctor.id == item.seen_by))
    )
