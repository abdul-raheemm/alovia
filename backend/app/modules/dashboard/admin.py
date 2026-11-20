"""Minimal admin (Dashboard spec §21) and the activity log (§20): doctor accounts,
assignments, and log views for admins (all entries) and doctors (their patients' entries).
Admins never see clinical values (§1.3): these views hold names, ids and actions only."""

import uuid
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import Select, func, select, update
from sqlalchemy.orm import Session, aliased

from app.core.auth_admin import AuthAdmin
from app.core.errors import AppError
from app.modules.dashboard.schemas import (
    AdminDoctorOut,
    AssignedDoctorAdmin,
    AssignmentIn,
    AssignmentPatientOut,
    AuditEntryOut,
    DoctorInviteIn,
    DoctorUpdateIn,
)
from app.modules.users.models import (
    AuditLog,
    Doctor,
    DoctorPatientAssignment,
    Patient,
    User,
)
from app.modules.users.service import add_audit

AUDIT_LIMIT = 200  # shortcut: newest entries only; add paging when the log outgrows one page
SEARCH_LIMIT = 50


# ---- doctors ----


def _doctor_out(db: Session, doctor: Doctor) -> AdminDoctorOut:
    email = db.scalar(select(User.email).where(User.id == doctor.user_id)) or ""
    patients = db.scalar(
        select(func.count()).where(
            DoctorPatientAssignment.doctor_id == doctor.id,
            DoctorPatientAssignment.removed_at.is_(None),
        )
    )
    return AdminDoctorOut(
        id=doctor.id,
        name=doctor.name,
        specialty=doctor.specialty,
        email=email,
        is_active=doctor.is_active,
        patient_count=patients or 0,
    )


def list_doctors(db: Session) -> list[AdminDoctorOut]:
    return [_doctor_out(db, d) for d in db.scalars(select(Doctor).order_by(Doctor.name))]


def invite_doctor(
    db: Session, admin: User, auth: AuthAdmin, doctor_app_url: str, body: DoctorInviteIn
) -> AdminDoctorOut:
    """§21: Supabase sends the invite email (its link opens Set password, DEC-101); the
    backend creates the users and doctors rows with the new login's id.
    shortcut: if saving the rows fails after the invite, the Supabase login exists without a
    users row; the admin then sees "already exists" and the owner links it with make_admin-style
    steps. Revisit in Phase 8 with the deletion flow."""
    email = body.email.lower()
    if db.scalar(select(User.id).where(func.lower(User.email) == email)) is not None:
        raise AppError("CONFLICT", "An account with this email already exists.", status=409)
    user_id = auth.invite(email, f"{doctor_app_url.rstrip('/')}/set-password")
    user = User(id=uuid.UUID(user_id), email=email, role="doctor")
    db.add(user)
    db.flush()
    doctor = Doctor(user_id=user.id, name=body.name, specialty=body.specialty)
    db.add(doctor)
    db.flush()
    add_audit(db, admin, "doctor invited", "doctor", doctor.id, None)
    db.commit()
    return _doctor_out(db, doctor)


def update_doctor(
    db: Session, admin: User, doctor_id: uuid.UUID, body: DoctorUpdateIn
) -> AdminDoctorOut:
    """§21: name, specialty, deactivate / reactivate. A deactivated doctor cannot use any
    doctor route (users.service.get_doctor); assignments stay for history."""
    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        raise AppError("NOT_FOUND", "We couldn't find this doctor.", status=404)
    action = "doctor edited"
    if body.is_active != doctor.is_active:
        action = "doctor reactivated" if body.is_active else "doctor deactivated"
    doctor.name, doctor.specialty, doctor.is_active = body.name, body.specialty, body.is_active
    add_audit(db, admin, action, "doctor", doctor.id, None)
    db.commit()
    return _doctor_out(db, doctor)


# ---- assignments ----


def _assigned(db: Session, patient_id: uuid.UUID) -> list[tuple[DoctorPatientAssignment, Doctor]]:
    return [
        (a, d)
        for a, d in db.execute(
            select(DoctorPatientAssignment, Doctor)
            .join(Doctor, Doctor.id == DoctorPatientAssignment.doctor_id)
            .where(
                DoctorPatientAssignment.patient_id == patient_id,
                DoctorPatientAssignment.removed_at.is_(None),
            )
            .order_by(DoctorPatientAssignment.is_primary.desc(), Doctor.name)
        )
    ]


def _patient_out(db: Session, patient: Patient) -> AssignmentPatientOut:
    return AssignmentPatientOut(
        patient_id=patient.id,
        patient_name=patient.name,
        doctors=[
            AssignedDoctorAdmin(
                doctor_id=d.id, name=d.name, is_primary=a.is_primary, is_active=d.is_active
            )
            for a, d in _assigned(db, patient.id)
        ],
    )


def search_patients(db: Session, q: str) -> list[AssignmentPatientOut]:
    """§21: search patients by name (no clinical data)."""
    stmt = select(Patient).order_by(Patient.name).limit(SEARCH_LIMIT)
    if q.strip():
        stmt = stmt.where(Patient.name.ilike(f"%{q.strip()}%"))
    return [_patient_out(db, p) for p in db.scalars(stmt)]


def assign(db: Session, admin: User, body: AssignmentIn) -> AssignmentPatientOut:
    """§21: add a doctor, or make an assigned doctor the primary one (one primary at most)."""
    patient = db.get(Patient, body.patient_id)
    doctor = db.get(Doctor, body.doctor_id)
    if patient is None or doctor is None:
        raise AppError("NOT_FOUND", "We couldn't find this patient or doctor.", status=404)
    current = {d.id: a for a, d in _assigned(db, patient.id)}
    row = current.get(doctor.id)
    if row is None:
        if not doctor.is_active:
            raise AppError("CONFLICT", "This doctor is deactivated.", status=409)
        row = DoctorPatientAssignment(
            doctor_id=doctor.id,
            patient_id=patient.id,
            is_primary=False,
            assigned_by=admin.id,
            assigned_at=datetime.now(UTC),
        )
        db.add(row)
        db.flush()
    elif not body.is_primary:
        raise AppError("CONFLICT", "This doctor is already assigned.", status=409)
    if body.is_primary and not row.is_primary:
        db.execute(
            update(DoctorPatientAssignment)
            .where(
                DoctorPatientAssignment.patient_id == patient.id,
                DoctorPatientAssignment.removed_at.is_(None),
                DoctorPatientAssignment.is_primary.is_(True),
            )
            .values(is_primary=False)
        )
        db.flush()  # the old primary is cleared before the new one (one primary at most)
        row.is_primary = True
    add_audit(db, admin, "assignment changed", "assignment", row.id, patient.id)
    db.commit()
    return _patient_out(db, patient)


def unassign(
    db: Session, admin: User, patient_id: uuid.UUID, doctor_id: uuid.UUID
) -> AssignmentPatientOut:
    """§21 / §25 test 14: removing the last assigned doctor is blocked. The patient's active
    rows are locked first, so two removals at once cannot leave her with none."""
    rows = list(
        db.scalars(
            select(DoctorPatientAssignment)
            .where(
                DoctorPatientAssignment.patient_id == patient_id,
                DoctorPatientAssignment.removed_at.is_(None),
            )
            .with_for_update()
        )
    )
    row = next((r for r in rows if r.doctor_id == doctor_id), None)
    if row is None:
        raise AppError("NOT_FOUND", "This doctor is not assigned to this patient.", status=404)
    if len(rows) == 1:
        raise AppError("CONFLICT", "A patient must keep at least one assigned doctor.", status=409)
    row.removed_at = datetime.now(UTC)
    row.is_primary = False  # removed rows are history; the primary is chosen again by the admin
    add_audit(db, admin, "assignment changed", "assignment", row.id, patient_id)
    db.commit()
    patient = db.get(Patient, patient_id)
    assert patient is not None
    return _patient_out(db, patient)


# ---- §20 activity log ----


ActorDoctor = aliased(Doctor)  # the doctor record of the person who acted, if any
AuditRow = Select[AuditLog, str, str, str, str]


def _audit_query() -> AuditRow:
    return (
        select(AuditLog, User.email, User.role, ActorDoctor.name, Patient.name)
        .outerjoin(User, User.id == AuditLog.actor_user_id)
        .outerjoin(ActorDoctor, ActorDoctor.user_id == AuditLog.actor_user_id)
        .outerjoin(Patient, Patient.id == AuditLog.patient_id)
        .order_by(AuditLog.created_at.desc(), AuditLog.id)
        .limit(AUDIT_LIMIT)
    )


def _entries(db: Session, stmt: AuditRow) -> list[AuditEntryOut]:
    return [
        AuditEntryOut(
            id=log.id,
            created_at=log.created_at,
            actor_email=email,
            actor_role=role,
            actor_name=doctor_name,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            patient_id=log.patient_id,
            patient_name=patient_name,
        )
        for log, email, role, doctor_name, patient_name in db.execute(stmt)
    ]


def admin_audit(
    db: Session,
    actor: str | None,
    action: str | None,
    day_from: date | None,
    day_to: date | None,
    timezone: str,
) -> list[AuditEntryOut]:
    """UX A3: all entries, filtered by user (email or doctor name), action and date (the
    patient's local days, as everywhere in the app). Never clinical values (§20)."""
    tz = ZoneInfo(timezone)
    stmt = _audit_query()
    if actor and actor.strip():
        like = f"%{actor.strip()}%"
        stmt = stmt.where(User.email.ilike(like) | ActorDoctor.name.ilike(like))
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if day_from:
        stmt = stmt.where(AuditLog.created_at >= datetime.combine(day_from, time(0), tzinfo=tz))
    if day_to:
        end = datetime.combine(day_to + timedelta(days=1), time(0), tzinfo=tz)
        stmt = stmt.where(AuditLog.created_at < end)
    return _entries(db, stmt)


def patient_audit(db: Session, patient_id: uuid.UUID) -> list[AuditEntryOut]:
    """§4: a doctor sees the log entries of an assigned patient."""
    return _entries(db, _audit_query().where(AuditLog.patient_id == patient_id))


def audit_actions(db: Session) -> list[str]:
    return list(db.scalars(select(AuditLog.action).distinct().order_by(AuditLog.action)))
