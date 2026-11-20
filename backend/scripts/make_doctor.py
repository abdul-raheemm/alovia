"""Turn an existing Supabase sign-in into a doctor account, for the owner's manual testing
(DEC-104). First add the user in the Supabase dashboard (Authentication -> Users -> Add user,
tick "Auto confirm user"), then run, from backend/ with backend/.env:

  python scripts/make_doctor.py --user-id <Supabase user UID> --email <their email> \
      --name "Test Doctor" [--assign-seed-patients]

--assign-seed-patients also assigns every seed patient ("Test Patient ...") so there is data to
look at. Refuses to change an account of another role. Running it again changes nothing.
In normal use doctors are invited from the Admin page instead (Dashboard spec §21).
"""

import argparse
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.modules.users.models import (  # noqa: E402
    Doctor,
    DoctorPatientAssignment,
    Patient,
    User,
)

SEED_PREFIX = "Test Patient"


def make_doctor(
    db: Session, user_id: uuid.UUID, email: str, name: str, assign_seed: bool = False
) -> str:
    """Create the users and doctors rows (and seed assignments). Returns what happened; the
    caller commits."""
    user = db.get(User, user_id)
    if user is not None and user.role != "doctor":
        raise SystemExit(f"Refusing: this account already exists with role {user.role!r}.")
    done = []
    taken = db.scalar(select(User).where(func.lower(User.email) == email.strip().lower()))
    if taken is not None and taken.id != user_id:
        raise SystemExit(
            f"Refusing: {email.strip()} already belongs to another account here "
            f"(role {taken.role!r}, user id {taken.id}). Use the Supabase user that owns this "
            "email (its UID must match that id), or create the doctor with another email."
        )
    if user is None:
        user = User(id=user_id, email=email.strip(), role="doctor")
        db.add(user)
        db.flush()
    doctor = db.scalar(select(Doctor).where(Doctor.user_id == user_id))
    if doctor is None:
        doctor = Doctor(user_id=user_id, name=name.strip())
        db.add(doctor)
        db.flush()
        done.append("doctor account created")
    if assign_seed:
        assigned = set(
            db.scalars(
                select(DoctorPatientAssignment.patient_id).where(
                    DoctorPatientAssignment.doctor_id == doctor.id,
                    DoctorPatientAssignment.removed_at.is_(None),
                )
            )
        )
        seeds = db.scalars(select(Patient).where(Patient.name.like(f"{SEED_PREFIX}%")))
        added = 0
        for p in seeds:
            if p.id not in assigned:
                db.add(
                    DoctorPatientAssignment(
                        doctor_id=doctor.id,
                        patient_id=p.id,
                        is_primary=False,
                        assigned_by=user_id,
                        assigned_at=datetime.now(UTC),
                    )
                )
                added += 1
        if added:
            done.append(f"assigned {added} seed patients")
    return "; ".join(done) or "already a doctor; nothing changed"


def main() -> None:
    from app.core.config import get_settings
    from app.core.database import make_engine

    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--user-id", type=uuid.UUID, required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--assign-seed-patients", action="store_true")
    args = parser.parse_args()
    engine = make_engine(get_settings().database_url)
    try:
        with Session(engine) as db:
            result = make_doctor(db, args.user_id, args.email, args.name, args.assign_seed_patients)
            db.commit()
    finally:
        engine.dispose()
    print(result)


if __name__ == "__main__":
    main()
