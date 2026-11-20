"""scripts/make_doctor.py (DEC-104): an owner's Supabase login becomes a working doctor account.
Runs on alovia-test."""

import importlib.util
import uuid
from pathlib import Path
from types import ModuleType

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from app.modules.users.models import User
from tests.helpers import add_account, bearer, make_app


def load_script() -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "scripts" / "make_doctor.py"
    spec = importlib.util.spec_from_file_location("make_doctor", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_login_becomes_a_doctor_who_sees_seed_patients(test_db_url: str, engine: Engine) -> None:
    script = load_script()
    uid = uuid.uuid4()
    with engine.begin() as conn:
        seed_id = conn.execute(
            text("INSERT INTO patients (name) VALUES ('Test Patient 9') RETURNING id")
        ).scalar_one()
        conn.execute(text("INSERT INTO patients (name) VALUES ('Someone Else')"))
    with Session(engine) as db:
        result = script.make_doctor(db, uid, f" {uid}@example.test ", "Dr Owner", assign_seed=True)
        db.commit()
        assert result.startswith("doctor account created; assigned")
        again = script.make_doctor(db, uid, f"{uid}@example.test", "Dr Owner", assign_seed=True)
        db.commit()
        assert again == "already a doctor; nothing changed"

    # the account works through the real routes (after the app's consent step)
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO consents (user_id, consent_version, age_confirmed_18_plus, "
                "accepted_at) VALUES (:u, '2026-11-v1', true, now())"
            ),
            {"u": uid},
        )
    app = make_app(database_url=test_db_url)
    try:
        rows = TestClient(app).get("/api/v1/doctor/patients", headers=bearer(sub=str(uid)))
        names = [r["name"] for r in rows.json()["data"]]
        assert rows.status_code == 200 and "Someone Else" not in names
        assert str(seed_id) in [r["id"] for r in rows.json()["data"]]
    finally:
        app.state.engine.dispose()


def test_never_changes_another_role(engine: Engine) -> None:
    script = load_script()
    uid = add_account(engine, "patient")
    with Session(engine) as db, pytest.raises(SystemExit, match="role 'patient'"):
        script.make_doctor(db, uid, "x@example.test", "X")
    with Session(engine) as db:
        user = db.get(User, uid)
        assert user is not None and user.role == "patient"


def test_email_used_by_another_account_is_refused_clearly(engine: Engine) -> None:
    """An email already taken by a different user id gives a plain message, not a crash."""
    script = load_script()
    other = add_account(engine, "admin")
    with Session(engine) as db, pytest.raises(SystemExit, match="role 'admin'"):
        script.make_doctor(db, uuid.uuid4(), f" {str(other).upper()}@EXAMPLE.TEST ", "X")
