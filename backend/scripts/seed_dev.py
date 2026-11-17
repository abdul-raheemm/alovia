"""Development seed data — clearly fake, never real people (DATABASE.md §12).

Creates 1 admin, 2 doctors and 5 patients ("Test Patient 1".."5") at 8, 16, 24, 34 and 41
weeks, assigns them to the doctors, and prints one invite link per patient (the doctor's
invite screen arrives in Phase 5). Appointments, check-ins and genetic assessments are added
by the phases that create those tables.

Synthetic doctor and admin accounts cannot sign in (they have no Supabase login). To use your
own Supabase login as the admin or as Test Doctor 1, create the user in the Supabase dashboard
and pass its id and email (DEC-032: admins and the owner create these accounts).

Usage (from backend/, with backend/.env):
  python scripts/seed_dev.py [--admin-user-id ID --admin-email EMAIL]
                             [--doctor-user-id ID --doctor-email EMAIL]
                             [--patient-app-url http://localhost:5173]
Refuses to run when APP_ENV=production or when the seed already exists.
"""

import argparse
import sys
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.modules.users.invites import create_invite  # noqa: E402
from app.modules.users.models import (  # noqa: E402
    Doctor,
    DoctorPatientAssignment,
    Patient,
    User,
)

SEED_DOMAIN = "seed.alovia.test"
WEEKS = (8, 16, 24, 34, 41)  # DATABASE.md §12


@dataclass(frozen=True)
class Login:
    user_id: uuid.UUID
    email: str


def due_date_for(weeks: int, today: date) -> date:
    """Inverse of the Journey spec's GA_days = 280 − (due_date − today) (spec §5, line 172)."""
    return today + timedelta(days=280 - weeks * 7)


def seed(
    db: Session,
    *,
    today: date,
    patient_app_url: str,
    admin: Login | None = None,
    doctor: Login | None = None,
) -> list[tuple[str, str]]:
    """Add the seed rows (the caller commits). Returns (patient name, invite link) pairs."""
    if db.scalar(select(User.id).where(User.email.like(f"%@{SEED_DOMAIN}"))) is not None:
        raise SystemExit(f"Seed data already exists (accounts @{SEED_DOMAIN}); nothing changed.")

    def user(login: Login | None, role: str, label: str) -> User:
        login = login or Login(uuid.uuid4(), f"{label}@{SEED_DOMAIN}")
        row = User(id=login.user_id, email=login.email, role=role)
        db.add(row)
        db.flush()  # write it now: the models have no relationships to order the inserts
        return row

    admin_user = user(admin, "admin", "test.admin")
    doctors = [
        Doctor(user_id=user(doctor, "doctor", "test.doctor1").id, name="Test Doctor 1"),
        Doctor(user_id=user(None, "doctor", "test.doctor2").id, name="Test Doctor 2"),
    ]
    db.add_all(doctors)
    db.flush()

    links: list[tuple[str, str]] = []
    now = datetime.now(UTC)
    for n, weeks in enumerate(WEEKS, start=1):
        patient = Patient(
            name=f"Test Patient {n}",
            due_date=due_date_for(weeks, today),
            due_date_source="clinician_confirmed",
            created_by=doctors[0].user_id,
        )
        db.add(patient)
        db.flush()
        db.add(
            DoctorPatientAssignment(
                doctor_id=doctors[0].id,
                patient_id=patient.id,
                is_primary=True,
                assigned_by=admin_user.id,
                assigned_at=now,
            )
        )
        if n <= 2:  # a patient can have several doctors (DEC-009)
            db.add(
                DoctorPatientAssignment(
                    doctor_id=doctors[1].id,
                    patient_id=patient.id,
                    is_primary=False,
                    assigned_by=admin_user.id,
                    assigned_at=now,
                )
            )
        code = create_invite(db, patient.id, doctors[0].user_id)
        links.append((patient.name, f"{patient_app_url.rstrip('/')}/join?code={code}"))
    return links


def main() -> None:
    from app.core.config import get_settings
    from app.core.database import make_engine

    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--admin-user-id", type=uuid.UUID)
    parser.add_argument("--admin-email")
    parser.add_argument("--doctor-user-id", type=uuid.UUID)
    parser.add_argument("--doctor-email")
    parser.add_argument("--patient-app-url", default="http://localhost:5173")
    args = parser.parse_args()
    for who in ("admin", "doctor"):
        if (getattr(args, f"{who}_user_id") is None) != (getattr(args, f"{who}_email") is None):
            parser.error(f"--{who}-user-id and --{who}-email go together")

    settings = get_settings()
    if settings.app_env == "production":
        raise SystemExit("Refusing to seed: APP_ENV is production.")
    admin = Login(args.admin_user_id, args.admin_email) if args.admin_user_id else None
    doctor = Login(args.doctor_user_id, args.doctor_email) if args.doctor_user_id else None
    engine = make_engine(settings.database_url)
    try:
        with Session(engine) as db:
            links = seed(
                db,
                today=date.today(),
                patient_app_url=args.patient_app_url,
                admin=admin,
                doctor=doctor,
            )
            db.commit()
    finally:
        engine.dispose()
    print("Seeded 1 admin, 2 doctors, 5 patients. Invite links (valid for the configured days):")
    for name, link in links:
        print(f"  {name}: {link}")


if __name__ == "__main__":
    main()
