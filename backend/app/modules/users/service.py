"""Account lookup, /me and app-wide consent (SECURITY.md §1, API.md §4.1, DEC-023, DEC-031)."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends
from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, get_current_user
from app.core.config import CONSENT_VERSION
from app.core.database import get_db
from app.core.errors import AppError
from app.core.logging import logger
from app.modules.users.models import (
    AuditLog,
    Consent,
    Doctor,
    DoctorPatientAssignment,
    Patient,
    User,
)
from app.modules.users.schemas import (
    ConsentIn,
    ConsentStatus,
    DoctorRef,
    MeOut,
    PatientRef,
    UserOut,
)


def get_account(
    current: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """The signed-in person's users row. 403 if it does not exist yet or is deactivated.

    New patients get their row from POST /patient/link (DEC-036); others are created by
    admins and the owner (DEC-032).
    """
    try:
        user_id = uuid.UUID(current.id)
    except ValueError as exc:
        raise AppError("AUTH_REQUIRED", "Please sign in again.", status=401) from exc
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        logger.warning(
            "permission denied", extra={"reason": "no account" if user is None else "inactive"}
        )
        raise AppError("FORBIDDEN", "Your account is not set up yet.", status=403)
    return user


def _consent_accepted(db: Session, user_id: uuid.UUID) -> bool:
    return bool(
        db.scalar(
            select(
                exists().where(
                    Consent.user_id == user_id, Consent.consent_version == CONSENT_VERSION
                )
            )
        )
    )


def get_patient(
    user: Annotated[User, Depends(get_account)],
    db: Annotated[Session, Depends(get_db)],
) -> Patient:
    """The signed-in patient's own record, for every /patient/... data route.

    Patient-entered data exists only after she has linked her account and accepted the
    app-wide consent (Dashboard spec §8), so all three are checked here, in the backend.
    """
    patient = (
        db.scalar(select(Patient).where(Patient.user_id == user.id))
        if user.role == "patient"
        else None
    )
    if patient is None:
        logger.warning("permission denied", extra={"reason": "not a linked patient"})
        raise AppError("FORBIDDEN", "You don't have access to this.", status=403)
    _require_consent(db, user)
    return patient


@dataclass(frozen=True)
class DoctorAccount:
    user: User
    doctor: Doctor


def _require_consent(db: Session, user: User) -> None:
    if not _consent_accepted(db, user.id):
        logger.warning("permission denied", extra={"reason": "consent not accepted"})
        raise AppError("FORBIDDEN", "Please accept the consent first.", status=403)


def get_doctor(
    user: Annotated[User, Depends(get_account)],
    db: Annotated[Session, Depends(get_db)],
) -> DoctorAccount:
    """The signed-in doctor, for every /doctor/... route (Dashboard spec §4): doctor role, an
    active doctor record and the current app-wide consent, checked in the backend."""
    doctor = (
        db.scalar(select(Doctor).where(Doctor.user_id == user.id))
        if user.role == "doctor"
        else None
    )
    if doctor is None or not doctor.is_active:
        logger.warning("permission denied", extra={"reason": "not an active doctor"})
        raise AppError("FORBIDDEN", "You don't have access to this.", status=403)
    _require_consent(db, user)
    return DoctorAccount(user=user, doctor=doctor)


def get_admin(
    user: Annotated[User, Depends(get_account)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """The signed-in admin, for every /admin/... route (Dashboard spec §4, §21)."""
    if user.role != "admin":
        logger.warning("permission denied", extra={"reason": "not an admin"})
        raise AppError("FORBIDDEN", "You don't have access to this.", status=403)
    _require_consent(db, user)
    return user


def assigned_patient(db: Session, doctor_id: uuid.UUID, patient_id: uuid.UUID) -> Patient:
    """The patient, only when this doctor has an active assignment to her (spec §1.3, §4).
    Otherwise 404, so a doctor cannot even learn that another doctor's patient exists."""
    patient = db.scalar(
        select(Patient)
        .join(DoctorPatientAssignment, DoctorPatientAssignment.patient_id == Patient.id)
        .where(
            Patient.id == patient_id,
            DoctorPatientAssignment.doctor_id == doctor_id,
            DoctorPatientAssignment.removed_at.is_(None),
        )
    )
    if patient is None:
        logger.warning("permission denied", extra={"reason": "patient not assigned"})
        raise AppError("NOT_FOUND", "Patient not found.", status=404)
    return patient


def get_assigned_patient(
    patient_id: uuid.UUID,
    account: Annotated[DoctorAccount, Depends(get_doctor)],
    db: Annotated[Session, Depends(get_db)],
) -> Patient:
    """Dependency for /doctor/patients/{patient_id}/... routes."""
    return assigned_patient(db, account.doctor.id, patient_id)


def get_me(db: Session, user: User) -> MeOut:
    patient = db.scalar(select(Patient).where(Patient.user_id == user.id))
    doctor = db.scalar(select(Doctor).where(Doctor.user_id == user.id))
    return MeOut(
        user=UserOut(id=user.id, email=user.email, role=user.role),
        patient=PatientRef(id=patient.id, name=patient.name) if patient else None,
        doctor=(
            DoctorRef(id=doctor.id, name=doctor.name, specialty=doctor.specialty)
            if doctor
            else None
        ),
        consent=ConsentStatus(
            current_version=CONSENT_VERSION, accepted=_consent_accepted(db, user.id)
        ),
    )


def record_consent(db: Session, user: User, body: ConsentIn) -> ConsentStatus:
    if body.consent_version != CONSENT_VERSION:
        raise AppError(
            "VALIDATION_ERROR",
            "Please read and accept the current consent text.",
            fields={"consent_version": "not the current version"},
        )
    if not body.age_confirmed_18_plus:  # DEC-023: users 18+ only
        raise AppError(
            "VALIDATION_ERROR",
            "Alovia is only for people aged 18 or older.",
            fields={"age_confirmed_18_plus": "must be confirmed"},
        )
    # shortcut: two simultaneous requests can both add a row; harmless for a consent log.
    if not _consent_accepted(db, user.id):
        db.add(
            Consent(
                user_id=user.id,
                consent_version=CONSENT_VERSION,
                age_confirmed_18_plus=True,
                accepted_at=datetime.now(UTC),
            )
        )
        db.commit()
    return ConsentStatus(current_version=CONSENT_VERSION, accepted=True)


def record_sign_in(
    db: Session, user: User, session_id: str | None, patient_id: uuid.UUID | None
) -> None:
    """Dashboard spec §20 "sign-in": sign-in happens in Supabase, so the backend logs it the
    first time it sees a new sign-in session (the token's session_id). Tokens without one
    are not logged.
    shortcut: two first requests at the same moment may both log the session; harmless for
    an activity log; a unique index would stop it if it ever matters."""
    if not session_id:
        return
    seen = db.scalar(
        select(
            exists().where(
                AuditLog.actor_user_id == user.id,
                AuditLog.action == "signed in",
                AuditLog.entity_id == session_id,
            )
        )
    )
    if not seen:
        db.add(
            AuditLog(
                actor_user_id=user.id,
                action="signed in",
                entity_type="session",
                entity_id=session_id,
                patient_id=patient_id,
                details={"role": user.role},
            )
        )
        db.commit()


def add_audit(
    db: Session,
    actor: User,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    patient_id: uuid.UUID | None,
) -> None:
    """Append an activity-log row (Dashboard spec §20; never clinical values). The caller
    commits, so the row is saved together with the change it records."""
    db.add(
        AuditLog(
            actor_user_id=actor.id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            patient_id=patient_id,
        )
    )
