"""Account lookup, /me and app-wide consent (SECURITY.md §1, API.md §4.1, DEC-023, DEC-031)."""

import uuid
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
from app.modules.users.models import Consent, Doctor, Patient, User
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
