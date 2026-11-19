"""Patient invite links (doctor_dashboard_module_spec.md §8.2, DEC-024, DEC-036).

A doctor's invite is a random one-time code, stored only as a hash. It is the only way a
patient can sign up. Used, expired and wrong codes all fail the same way (spec §25 test 9).
"""

import hashlib
import secrets
import uuid
from datetime import timedelta
from functools import lru_cache
from pathlib import Path

import yaml
from sqlalchemy import func, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.core.errors import AppError
from app.modules.users.models import AuditLog, PatientInvite, User

CONFIG_FILE = Path(__file__).resolve().parents[3] / "rules" / "dashboard" / "config.yaml"
# no look-alike characters (0/O, 1/I/L), so codes are easy to read and type
ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
INVALID = "This invite link isn't valid. Please ask your doctor for a new one."


@lru_cache
def invite_settings() -> tuple[int, int]:
    """(invite_code_length, invite_code_days) from the dashboard config file."""
    cfg = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))
    length, days = cfg["invite_code_length"], cfg["invite_code_days"]
    if not (isinstance(length, int) and isinstance(days, int) and length >= 6 and days >= 1):
        raise ValueError(f"invalid invite settings in {CONFIG_FILE}")
    return length, days


def _hash(code: str) -> str:
    return hashlib.sha256(code.strip().upper().encode()).hexdigest()


def create_invite(db: Session, patient_id: uuid.UUID, created_by: uuid.UUID) -> str:
    """Add a new invite and return its code (shown once; only the hash is stored).
    The caller commits. Used by the seed script now and the doctor route in Phase 5."""
    length, days = invite_settings()
    # §8.2 step 2: a new link cancels any unused earlier link (it expires now). Database time,
    # as the checks use it: the app server's clock can differ by seconds (ERR-048).
    db.execute(
        update(PatientInvite)
        .where(
            PatientInvite.patient_id == patient_id,
            PatientInvite.used_at.is_(None),
            PatientInvite.expires_at > func.now(),
        )
        .values(expires_at=func.now())
    )
    code = "".join(secrets.choice(ALPHABET) for _ in range(length))
    invite = PatientInvite(
        patient_id=patient_id,
        code_hash=_hash(code),
        created_by=created_by,
        expires_at=func.now() + timedelta(days=days),
    )
    db.add(invite)
    db.flush()
    db.add(
        AuditLog(
            actor_user_id=created_by,
            action="invite created",
            entity_type="patient_invite",
            entity_id=str(invite.id),
            patient_id=patient_id,
        )
    )
    return code


def invite_is_valid(db: Session, code: str) -> bool:
    return bool(
        db.scalar(
            text(
                "SELECT EXISTS (SELECT 1 FROM patient_invites i JOIN patients p "
                "ON p.id = i.patient_id WHERE i.code_hash = :h AND i.used_at IS NULL "
                "AND i.expires_at > now() AND p.user_id IS NULL)"
            ),
            {"h": _hash(code)},
        )
    )


def link_patient(db: Session, current: CurrentUser, code: str) -> User:
    """Create the patient's users row and link it to the invited patient record, in one
    transaction (DEC-036). Each step is a conditional UPDATE, so two simultaneous requests
    with the same code cannot both succeed."""
    try:
        user_id = uuid.UUID(current.id)
    except ValueError as exc:
        raise AppError("AUTH_REQUIRED", "Please sign in again.", status=401) from exc
    if db.get(User, user_id) is not None:
        raise AppError("CONFLICT", "This account is already set up.", status=409)
    if not current.email:
        raise AppError("VALIDATION_ERROR", "Your sign-in has no email address.", status=400)

    user = User(id=user_id, email=current.email, role="patient")
    db.add(user)
    try:
        db.flush()
    except IntegrityError as exc:  # users.email is unique
        db.rollback()
        raise AppError(
            "CONFLICT", "An account with this email exists. Sign in instead.", status=409
        ) from exc

    invite = db.execute(
        update(PatientInvite)
        .where(
            PatientInvite.code_hash == _hash(code),
            PatientInvite.used_at.is_(None),
            PatientInvite.expires_at > func.now(),
        )
        .values(used_at=func.now(), used_by_user_id=user_id)
        .returning(PatientInvite.id, PatientInvite.patient_id)
    ).one_or_none()
    linked = (
        invite is not None
        and db.execute(
            text(
                "UPDATE patients SET user_id = :u, updated_at = now() "
                "WHERE id = :p AND user_id IS NULL RETURNING id"
            ),
            {"u": user_id, "p": invite.patient_id},
        ).one_or_none()
        is not None
    )
    if invite is None or not linked:
        db.rollback()  # nothing is saved: no users row, invite unchanged
        raise AppError("NOT_FOUND", INVALID, status=404)

    db.add(
        AuditLog(
            actor_user_id=user_id,
            action="invite used",
            entity_type="patient_invite",
            entity_id=str(invite.id),
            patient_id=invite.patient_id,
        )
    )
    db.commit()
    return user
