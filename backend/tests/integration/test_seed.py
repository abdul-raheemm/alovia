"""Seed script (DATABASE.md §12) against the alovia-test database."""

import importlib.util
import uuid
from datetime import date
from pathlib import Path
from types import ModuleType

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from app.modules.users.invites import invite_is_valid


def load_seed() -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "scripts" / "seed_dev.py"
    spec = importlib.util.spec_from_file_location("seed_dev", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_due_dates_give_the_requested_weeks() -> None:
    seed_dev = load_seed()
    today = date(2026, 11, 17)
    for weeks in (8, 16, 24, 34, 41):
        due = seed_dev.due_date_for(weeks, today)
        assert 280 - (due - today).days == weeks * 7  # Journey spec: GA_days = 280 − (due − today)


def test_seed_creates_fake_people_and_working_invites(engine: Engine) -> None:
    # rows stay until the end of the run, when tests/conftest.py empties the test database
    seed_dev = load_seed()
    owner = seed_dev.Login(uuid.uuid4(), "owner.admin@example.test")
    with Session(engine) as db:
        links = seed_dev.seed(
            db, today=date.today(), patient_app_url="http://localhost:5173/", admin=owner
        )
        db.commit()
    assert [name for name, _ in links] == [f"Test Patient {n}" for n in range(1, 6)]
    assert all(link.startswith("http://localhost:5173/join?code=") for _, link in links)
    with Session(engine) as db:
        for _, link in links:
            assert invite_is_valid(db, link.split("code=")[1])
    with engine.connect() as conn:
        roles = conn.execute(
            text(
                "SELECT role, count(*) FROM users WHERE email LIKE '%seed.alovia.test' "
                "OR id = :o GROUP BY role ORDER BY role"
            ),
            {"o": owner.user_id},
        ).all()
        assert [tuple(r) for r in roles] == [("admin", 1), ("doctor", 2)]
        primaries = conn.execute(
            text(
                "SELECT count(*) FROM doctor_patient_assignments a JOIN patients p "
                "ON p.id = a.patient_id WHERE p.name LIKE 'Test Patient %' AND a.is_primary"
            )
        ).scalar()
        assert primaries == 5
    with Session(engine) as db, pytest.raises(SystemExit, match="already exists"):
        seed_dev.seed(db, today=date.today(), patient_app_url="http://x")
