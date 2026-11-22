"""scripts/seed_dev.py (owner 2026-11-22): seven connected accounts against the test database.
The Supabase logins are faked (random ids); create_user is tested on its own below."""

import importlib.util
import io
import json
import urllib.request
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from app.core import auth_admin
from app.modules.journey.engine import local_today
from app.modules.journey.service import pregnancy_week
from app.modules.users.models import Patient


def load_seed() -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "scripts" / "seed_dev.py"
    spec = importlib.util.spec_from_file_location("seed_dev", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rows(engine: Engine, sql: str, **params: Any) -> list[tuple[Any, ...]]:
    with engine.connect() as conn:
        return [tuple(r) for r in conn.execute(text(sql), params).all()]


def test_seed_creates_the_connected_accounts_and_data(engine: Engine) -> None:
    seed_dev = load_seed()
    state = seed_dev.State.load()
    logins = {a.key: uuid.uuid4() for a in seed_dev.ACCOUNTS}
    with Session(engine) as db:
        patients = seed_dev.seed(db, state, logins)
    ids = {str(v) for v in logins.values()}

    accounts = rows(
        engine, "SELECT role, email FROM users WHERE id = ANY(:ids) ORDER BY email", ids=list(ids)
    )
    assert accounts == [
        ("admin", "admin01@email.com"),
        ("doctor", "drmary@email.com"),
        *[("patient", f"testpatient{n}@email.com") for n in range(1, 6)],
    ]
    # the admin invited Dr Mary; Dr Mary is the primary doctor of all five
    assert rows(
        engine,
        "SELECT actor_user_id FROM audit_log WHERE action = 'doctor invited' "
        "AND actor_user_id = :a",
        a=str(logins["ADMIN"]),
    ) == [(logins["ADMIN"],)]
    assigned = rows(
        engine,
        "SELECT count(*) FROM doctor_patient_assignments a JOIN doctors d ON d.id = a.doctor_id "
        "WHERE d.user_id = :d AND a.is_primary AND a.assigned_by = :admin",
        d=str(logins["DOCTOR"]),
        admin=str(logins["ADMIN"]),
    )
    assert assigned == [(5,)]
    # patients joined through consent; staff accept it at their first sign-in
    consented = rows(
        engine, "SELECT count(*) FROM consents WHERE user_id = ANY(:ids)", ids=list(ids)
    )
    assert consented == [(5,)]

    cfg = state.journey_config
    today = local_today(cfg.timezone)
    with Session(engine) as db:
        p = {n: db.get(Patient, pid) for n, pid in patients.items()}
        weeks = {n: pregnancy_week(p[n], cfg, today) for n in (1, 2, 3)}  # type: ignore[arg-type]
        assert weeks == {1: 10, 2: 22, 3: 33}  # one per trimester
        assert p[4] and p[4].user_id and p[4].due_date is None  # joined, no data yet
        assert p[5] and p[5].pregnancy_status == "ended_birth"
        ended = p[5].pregnancy_ended_at
        assert ended and abs(ended - (datetime.now(UTC) - timedelta(days=14))) < timedelta(hours=1)

    checkins = dict(
        rows(
            engine,
            "SELECT patient_id, count(*) FROM symptom_checkins "
            "WHERE patient_id = ANY(:p) GROUP BY patient_id",
            p=[str(v) for v in patients.values()],
        )
    )
    assert [checkins.get(patients[n], 0) for n in range(1, 6)] == [2, 3, 2, 0, 1]
    levels = rows(
        engine,
        "SELECT red_flag_level FROM symptom_checkins WHERE patient_id = :p",
        p=str(patients[3]),
    )
    assert ("L1",) in levels  # the warning sign went through the real rules
    assert rows(
        engine, "SELECT count(*) FROM fetal_results WHERE patient_id = :p", p=str(patients[2])
    ) == [(1,)]
    assert rows(
        engine,
        "SELECT count(*) FROM result_shares s JOIN maternal_results m "
        "ON m.id = s.result_id AND s.result_type = 'maternal' WHERE m.patient_id = :p",
        p=str(patients[2]),
    ) == [(1,)]
    assert rows(
        engine, "SELECT count(*) FROM genetic_assessments WHERE patient_id = :p", p=str(patients[2])
    ) == [(1,)]


def test_create_user_makes_a_confirmed_login(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: dict[str, Any] = {}

    def fake_urlopen(req: Any, timeout: int) -> io.BytesIO:
        sent.update(url=req.full_url, body=json.loads(req.data), key=req.headers["Apikey"])
        return io.BytesIO(json.dumps({"id": "11111111-1111-1111-1111-111111111111"}).encode())

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    user_id = auth_admin.create_user("https://x.supabase.co/", "service-key", "a@b.test", "pw")
    assert user_id == "11111111-1111-1111-1111-111111111111"
    assert sent == {
        "url": "https://x.supabase.co/auth/v1/admin/users",
        "body": {"email": "a@b.test", "password": "pw", "email_confirm": True},
        "key": "service-key",
    }
