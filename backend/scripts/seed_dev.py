"""Development seed data — synthetic people only, never real (DATABASE.md §12; owner 2026-11-22).

Creates seven sign-in accounts and the data that connects them:
  Admin (admin01@email.com), who invited Dr Mary (drmary@email.com), the doctor of all five:
  Test Patient 1 — first trimester (week 10)
  Test Patient 2 — second trimester (week 22), with a genetic check and a shared result
  Test Patient 3 — third trimester (week 33), with a warning-sign check-in
  Test Patient 4 — joined, no pregnancy data yet (Dr Mary enters it while testing)
  Test Patient 5 — gave birth about two weeks ago (pregnancy ended, history kept)
Check-ins go through the real red-flag rules, predictions through the real models (inputs from
tests/fixtures/ml_reference_outputs.json), the genetic check through the genetic engine.

Passwords never go in git: put them in backend/.env (git-ignored) as
  SEED_PASSWORD_ADMIN, SEED_PASSWORD_DOCTOR, SEED_PASSWORD_PATIENT1 .. SEED_PASSWORD_PATIENT5
The logins are created in Supabase with the service-role key from .env (a network call).

Run the reset SQL first (docs/review/reset_seed_data.sql): this script refuses to run when
any user exists, and when APP_ENV=production.

Usage (from backend/):  python scripts/seed_dev.py
"""

import json
import sys
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import func, select, update  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.config import CONSENT_VERSION  # noqa: E402
from app.modules.dashboard import care, predictions  # noqa: E402
from app.modules.dashboard.predictions import Ranges  # noqa: E402
from app.modules.dashboard.rules import DashboardRules, load_dashboard_rules, load_ranges  # noqa: E402
from app.modules.dashboard.schemas import ModelName, NoteIn, PredictionIn, ShareIn  # noqa: E402
from app.modules.genetic import service as genetic  # noqa: E402
from app.modules.genetic.rules import GeneticRules, load_genetic_rules  # noqa: E402
from app.modules.genetic.schemas import AssessmentIn  # noqa: E402
from app.modules.journey import service as journey  # noqa: E402
from app.modules.journey.config import JourneyConfig, load_journey_config  # noqa: E402
from app.modules.journey.engine import local_today  # noqa: E402
from app.modules.journey.schemas import AppointmentIn, LmpDatesIn  # noqa: E402
from app.modules.predictions.risk_model import Models, load_models  # noqa: E402
from app.modules.symptoms import service as symptoms  # noqa: E402
from app.modules.symptoms.models import SymptomCheckin, SymptomLog  # noqa: E402
from app.modules.symptoms.rules import SymptomRules, load_symptom_rules  # noqa: E402
from app.modules.symptoms.schemas import CheckinIn, EntryIn  # noqa: E402
from app.modules.users.models import (  # noqa: E402
    Consent,
    Doctor,
    DoctorPatientAssignment,
    Patient,
    User,
)
from app.modules.users.service import DoctorAccount, add_audit  # noqa: E402

ML_CASES = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "ml_reference_outputs.json"


@dataclass(frozen=True)
class Account:
    key: str  # SEED_PASSWORD_<KEY>
    role: str
    name: str
    email: str


ACCOUNTS = (
    Account("ADMIN", "admin", "Admin", "admin01@email.com"),
    Account("DOCTOR", "doctor", "Dr Mary", "drmary@email.com"),
    *(
        Account(f"PATIENT{n}", "patient", f"Test Patient {n}", f"testpatient{n}@email.com")
        for n in range(1, 6)
    ),
)

# patient number -> (age, pregnancy week today; None = no dates yet)
PATIENTS: dict[int, tuple[int, int | None]] = {1: (26, 10), 2: (29, 22), 3: (31, 33), 4: (24, None)}
BIRTH_DAYS_AGO = 14  # Test Patient 5 gave birth two weeks ago, at 39 weeks
BIRTH_WEEK = 39


def lmp_for(weeks: int, today: date) -> date:
    """The first day of the last period that gives `weeks` completed weeks today."""
    return today - timedelta(weeks=weeks)


@dataclass
class State:
    """What the running app loads at start (app/main.py), loaded the same way here."""

    journey_config: JourneyConfig
    symptom_rules: SymptomRules
    genetic_rules: GeneticRules
    dashboard_rules: DashboardRules
    ranges: Ranges
    models: Models

    @classmethod
    def load(cls) -> State:
        return cls(
            load_journey_config(),
            load_symptom_rules(),
            load_genetic_rules(),
            load_dashboard_rules(),
            load_ranges(),
            load_models(),
        )


def seed(
    db: Session, state: State, logins: dict[str, uuid.UUID], now: datetime | None = None
) -> dict[int, uuid.UUID]:
    """Add the connected seed rows for already-created logins (key -> Supabase user id).
    The services commit as they go. Returns patient number -> patient id. main() refuses to run
    on a database that already has users; this function itself does not check (tests)."""
    now = now or datetime.now(UTC)
    cfg = state.journey_config
    today = local_today(cfg.timezone)

    users: dict[str, User] = {}
    for a in ACCOUNTS:
        users[a.key] = User(id=logins[a.key], email=a.email, role=a.role)
        db.add(users[a.key])
        db.flush()  # the models have no relationships to order the inserts
    admin, doctor_user = users["ADMIN"], users["DOCTOR"]
    doctor = Doctor(user_id=doctor_user.id, name="Dr Mary")
    db.add(doctor)
    db.flush()
    add_audit(db, admin, "doctor invited", "doctor", doctor.id, None)  # the admin created her
    account = DoctorAccount(doctor_user, doctor)

    patients: dict[int, Patient] = {}
    for n in range(1, 6):
        user = users[f"PATIENT{n}"]
        # patients join through the consent screen, so a joined patient has accepted it
        db.add(
            Consent(
                user_id=user.id,
                consent_version=CONSENT_VERSION,
                age_confirmed_18_plus=True,
                accepted_at=now,
            )
        )
        age = PATIENTS[n][0] if n in PATIENTS else 30
        patient = Patient(
            name=f"Test Patient {n}", age=age, user_id=user.id, created_by=doctor_user.id
        )
        db.add(patient)
        db.flush()
        db.add(
            DoctorPatientAssignment(
                doctor_id=doctor.id,
                patient_id=patient.id,
                is_primary=True,
                assigned_by=admin.id,
                assigned_at=now,
            )
        )
        add_audit(db, doctor_user, "patient created", "patient", patient.id, patient.id)
        patients[n] = patient
    db.commit()

    def dates(n: int, weeks: int, days_ago: int = 0) -> None:
        p = patients[n]
        lmp = lmp_for(weeks, today - timedelta(days=days_ago))
        journey.set_dates(
            db, users[f"PATIENT{n}"], p, LmpDatesIn(option="lmp", lmp_date=lmp), today
        )

    for n, (_, weeks) in PATIENTS.items():
        if weeks is not None:
            dates(n, weeks)
    dates(5, BIRTH_WEEK, days_ago=BIRTH_DAYS_AGO)

    def checkin(n: int, days_ago: int, *entries: EntryIn) -> None:
        p = patients[n]
        week = journey.pregnancy_week(p, cfg, today)
        out = symptoms.create_checkin(
            db,
            p,
            CheckinIn(source="form", entries=list(entries)),
            state.symptom_rules,
            week,
            cfg.timezone,
        )
        if days_ago:  # move it back in time, with the week it was logged in
            at = now - timedelta(days=days_ago)
            past_week = None if week is None else week - days_ago // 7
            db.execute(
                update(SymptomCheckin)
                .where(SymptomCheckin.id == out.checkin_id)
                .values(created_at=at, pregnancy_week=past_week)
            )
            db.execute(
                update(SymptomLog)
                .where(SymptomLog.checkin_id == out.checkin_id)
                .values(created_at=at)
            )
            db.commit()

    e = EntryIn
    checkin(1, 3, e(symptom="fatigue", severity="mild", duration="1_to_6_hours"))
    checkin(1, 1, e(symptom="nausea_vomiting", puqe_answers=[2, 2, 1]))
    checkin(2, 8, e(symptom="back_pain", severity="moderate", duration="most_of_the_day"))
    checkin(2, 2, e(symptom="headache", severity="moderate", duration="1_to_6_hours"))
    checkin(2, 0, e(symptom="pain_passing_urine"))
    checkin(3, 5, e(symptom="fatigue", severity="severe", duration="most_of_the_day"))
    checkin(3, 0, e(symptom="vaginal_bleeding"))
    checkin(5, 21, e(symptom="back_pain", severity="mild", duration="under_1_hour"))

    cases = {c["id"]: c["input"] for c in json.loads(ML_CASES.read_text(encoding="utf-8"))["cases"]}

    def predict(n: int, model: ModelName, case: str) -> uuid.UUID:
        sch = predictions.schema(model, state.dashboard_rules, state.ranges)
        units = {f.unit.name: f.unit.model_unit for g in sch.groups for f in g.fields if f.unit}
        out = predictions.run(
            db,
            account,
            patients[n],
            model,
            PredictionIn(values=cases[case], units=units),
            state.dashboard_rules,
            state.ranges,
            state.models,
        )
        return out.id

    predict(2, "fetal", "fetal_suspect")
    shared = predict(2, "maternal", "maternal_low")
    predictions.share(
        db,
        account,
        "maternal",
        shared,
        ShareIn(doctor_message="Test message from Dr Mary (synthetic data)."),
    )
    predict(3, "fetal", "fetal_normal")
    predict(3, "maternal", "maternal_mid")

    carrier = {"status": "beta_thal_carrier", "evidence": "hplc_report"}
    genetic.create_assessment(
        db,
        users["PATIENT2"],
        patients[2],
        AssessmentIn.model_validate(
            {
                "haemoglobin_group": {
                    "mother": carrier,
                    "father": {"status": "unknown"},
                    "previous_child": "no",
                },
                "haemophilia": {"entry": "no"},
                "marfan": {"entry": "no"},
                "consanguinity": "no",
            }
        ),
        state.genetic_rules,
    )

    for n, visible in ((1, True), (3, False)):
        text = f"Test note from Dr Mary for Test Patient {n} (synthetic data)."
        care.write_note(db, account, patients[n], NoteIn(body=text, visible_to_patient=visible))
    for n, days in ((1, 7), (2, 3), (3, 10)):
        journey.create_appointment(
            db,
            doctor_user,
            patients[n],
            AppointmentIn(date=today + timedelta(days=days), time=time(10, 30), title="Check-up"),
            cfg.timezone,
            editor="doctor",
        )

    # Test Patient 5: her doctor records the birth (Dashboard §17), two weeks ago
    journey.end_pregnancy(db, doctor_user, patients[5], "ended_birth", None)
    patients[5].pregnancy_ended_at = now - timedelta(days=BIRTH_DAYS_AGO)
    db.commit()
    return {n: p.id for n, p in patients.items()}


def main() -> None:
    from dotenv import dotenv_values

    from app.core.auth_admin import create_user
    from app.core.config import ENV_FILE, get_settings
    from app.core.database import make_engine

    settings = get_settings()
    if settings.app_env == "production":
        raise SystemExit("Refusing to seed: APP_ENV is production.")
    env = dotenv_values(ENV_FILE)
    missing = [f"SEED_PASSWORD_{a.key}" for a in ACCOUNTS if not env.get(f"SEED_PASSWORD_{a.key}")]
    if missing:
        raise SystemExit(f"Add these to backend/.env first: {', '.join(missing)}")
    key = settings.supabase_service_role_key
    service_key = key.get_secret_value() if key else None

    engine = make_engine(settings.database_url)
    try:
        with Session(engine) as db:
            if db.scalar(select(func.count()).select_from(User)):
                raise SystemExit("Users already exist: run the reset SQL first. Nothing changed.")
        state = State.load()
        logins: dict[str, uuid.UUID] = {}
        for a in ACCOUNTS:
            password = str(env[f"SEED_PASSWORD_{a.key}"])
            logins[a.key] = uuid.UUID(
                create_user(settings.supabase_url, service_key, a.email, password)
            )
            print(f"login created: {a.name} <{a.email}>")
        with Session(engine) as db:
            seed(db, state, logins)
    finally:
        engine.dispose()
    print("Seed data added. Sign in with the emails above and the passwords from backend/.env.")


if __name__ == "__main__":
    main()
