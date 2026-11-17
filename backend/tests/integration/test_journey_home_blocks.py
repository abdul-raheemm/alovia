"""Task 5 home blocks and month detail (Journey spec §4.3-§4.5, §7-8, §11.3) plus the
defensive bad-date guard (owner decision 2026-11-17). Runs against alovia-test."""

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from app.modules.journey.config import load_journey_config
from app.modules.journey.engine import local_today
from tests.helpers import add_linked_patient, bearer, make_app

CFG = load_journey_config()
TODAY = local_today(CFG.timezone)
HOME = "/api/v1/patient/journey/home"


@pytest.fixture(scope="module")
def client(test_db_url: str, engine: Engine) -> Iterator[TestClient]:
    app: FastAPI = make_app(database_url=test_db_url)
    yield TestClient(app)
    app.state.engine.dispose()


def dated_patient(engine: Engine, client: TestClient, weeks: int = 24) -> uuid.UUID:
    user_id, _ = add_linked_patient(engine)
    lmp = TODAY - timedelta(days=weeks * 7)
    res = client.put(
        "/api/v1/patient/journey/dates",
        json={"option": "lmp", "lmp_date": lmp.isoformat()},
        headers=bearer(sub=str(user_id)),
    )
    assert res.status_code == 200
    return user_id


def home(client: TestClient, user_id: uuid.UUID) -> Any:
    res = client.get(HOME, headers=bearer(sub=str(user_id)))
    assert res.status_code == 200
    return res.json()["data"]


def month_detail(client: TestClient, user_id: uuid.UUID, month: int) -> Any:
    return client.get(f"/api/v1/patient/journey/months/{month}", headers=bearer(sub=str(user_id)))


def test_home_blocks_with_a_dated_pregnancy(client: TestClient, engine: Engine) -> None:
    user_id = dated_patient(engine, client, weeks=24)
    data = home(client, user_id)
    # 9 month cards from the config month map (§4.4)
    assert [m["month"] for m in data["months"]] == list(range(1, 10))
    assert data["months"][0] == {"month": 1, "week_start": 0, "week_end": 4}
    assert data["months"][8] == {"month": 9, "week_start": 36, "week_end": 42}
    # task 4 content at week 24: the 0-42 fetal item + the trimester-2 body item; the
    # month-6 fetal item is held back for the detail view (§8.1 precedence)
    assert {i["id"] for i in data["stage_items"]} == {"mlp_fetal_trimesters", "owh_body_t2"}
    assert all(
        i["is_prototype"] and i["review_status"] == "unreviewed" for i in data["stage_items"]
    )
    # WHO Table 11, 50th percentile at week 24 (DEC-043 sample)
    assert data["size"]["weight_g"] == 665 and data["size"]["object_icon_id"] == "coconut"
    assert data["next_appointment"] is None


def test_home_without_dates_has_no_month_cards(client: TestClient, engine: Engine) -> None:
    user_id, _ = add_linked_patient(engine)
    data = home(client, user_id)
    assert data["state"] == "no_date"
    assert data["months"] == [] and data["stage_items"] == [] and data["size"] is None


def test_next_appointment_picks_the_soonest_upcoming(client: TestClient, engine: Engine) -> None:
    user_id = dated_patient(engine, client)
    with engine.connect() as conn:
        patient_id = conn.execute(
            text("SELECT id FROM patients WHERE user_id = :u"), {"u": user_id}
        ).scalar_one()
    now = datetime.now(UTC)
    rows = [
        ("Past visit", now - timedelta(days=2), True),
        ("Sooner visit", now + timedelta(days=3), True),
        ("Later visit", now + timedelta(days=10), True),
    ]
    with engine.begin() as conn:
        for title, at, has_time in rows:
            conn.execute(
                text(
                    "INSERT INTO appointments (patient_id, appointment_at, has_time, title, "
                    "created_by, source) VALUES (:p, :at, :h, :t, :u, 'patient')"
                ),
                {"p": patient_id, "at": at, "h": has_time, "t": title, "u": user_id},
            )
    assert home(client, user_id)["next_appointment"]["title"] == "Sooner visit"
    # a date-only appointment today (stored 00:00, has_time false) still counts as upcoming
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO appointments (patient_id, appointment_at, has_time, title, "
                "created_by, source) VALUES (:p, :at, false, 'Today visit', :u, 'patient')"
            ),
            {
                "p": patient_id,
                # stored at LOCAL midnight (§14.2), which is the previous day in UTC
                "at": datetime(TODAY.year, TODAY.month, TODAY.day, tzinfo=ZoneInfo(CFG.timezone)),
                "u": user_id,
            },
        )
    got = home(client, user_id)["next_appointment"]
    assert got["title"] == "Today visit" and got["has_time"] is False
    assert got["date"] == TODAY.isoformat() and got["time"] is None  # never the UTC day


def test_bad_stored_due_date_never_crashes_home(client: TestClient, engine: Engine) -> None:
    user_id = dated_patient(engine, client)
    with engine.begin() as conn:  # simulate a future doctor-route bug writing past D2's range
        conn.execute(
            text("UPDATE patients SET due_date = :d WHERE user_id = :u"),
            {"d": TODAY + timedelta(days=400), "u": user_id},
        )
    data = home(client, user_id)
    assert data["state"] == "no_date"  # safe fallback, logged server-side
    assert data["pregnancy"] is None and data["months"] == []


def test_month_detail_and_is_current(client: TestClient, engine: Engine) -> None:
    user_id = dated_patient(engine, client, weeks=24)  # week 24 -> month 6
    res = month_detail(client, user_id, 6)
    assert res.status_code == 200
    data = res.json()["data"]
    assert (data["month"], data["week_start"], data["week_end"], data["is_current"]) == (
        6,
        23,
        27,
        True,
    )
    assert [i["id"] for i in data["items"]] == ["owh_month_6"]  # the held-back month item
    assert month_detail(client, user_id, 1).json()["data"]["is_current"] is False


@pytest.mark.parametrize("month", [0, 10])
def test_month_outside_1_to_9_is_rejected(client: TestClient, engine: Engine, month: int) -> None:
    user_id = dated_patient(engine, client)
    res = month_detail(client, user_id, month)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_month_cards_stop_after_the_pregnancy_ends(client: TestClient, engine: Engine) -> None:
    user_id = dated_patient(engine, client)
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE patients SET pregnancy_status = 'ended_loss' WHERE user_id = :u"),
            {"u": user_id},
        )
    assert home(client, user_id)["months"] == []  # §11.3
    assert month_detail(client, user_id, 5).status_code == 404
