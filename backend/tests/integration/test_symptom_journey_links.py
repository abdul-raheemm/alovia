"""Symptoms in the Journey (Journey spec §4.3 quick log, §9.2 calendar dots and red-flag
icons, §9.4 weekly summary, §15 test 8). Runs against alovia-test."""

from collections.abc import Iterator
from datetime import timedelta
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from app.modules.journey.config import load_journey_config
from app.modules.journey.engine import local_today
from tests.helpers import add_linked_patient, bearer, make_app

TODAY = local_today(load_journey_config().timezone)
FATIGUE = {"symptom": "fatigue", "severity": "mild", "duration": "under_1_hour"}


@pytest.fixture(scope="module")
def client(test_db_url: str, engine: Engine) -> Iterator[TestClient]:
    app: FastAPI = make_app(database_url=test_db_url)
    yield TestClient(app)
    app.state.engine.dispose()


def patient(engine: Engine, client: TestClient, weeks: int | None = 24) -> Any:
    user_id, _ = add_linked_patient(engine)
    headers = bearer(sub=str(user_id))
    if weeks is not None:
        lmp = TODAY - timedelta(days=weeks * 7)
        client.put(
            "/api/v1/patient/journey/dates",
            json={"option": "lmp", "lmp_date": lmp.isoformat()},
            headers=headers,
        )
    return headers


def log(client: TestClient, headers: Any, *entries: dict[str, Any]) -> None:
    res = client.post(
        "/api/v1/patient/symptoms/checkins",
        json={"source": "form", "entries": list(entries)},
        headers=headers,
    )
    assert res.status_code == 201, res.text


def home(client: TestClient, headers: Any) -> Any:
    return client.get("/api/v1/patient/journey/home", headers=headers).json()["data"]


def test_logged_today_and_weekly_summary(client: TestClient, engine: Engine) -> None:
    headers = patient(engine, client, weeks=24)
    before = home(client, headers)
    assert before["logged_today"] is False
    summary = before["weekly_summary"]
    assert summary["days_logged"] == 0
    assert summary["top_symptoms"] == [] and summary["red_flag_days"] == []
    # §9.4 "Common at this stage": the common_symptoms content for the content week
    assert [i["content_type"] for i in summary["common_at_stage"]] == ["common_symptoms"]
    start = TODAY - timedelta(days=(TODAY.weekday() + 1) % 7)  # Sunday-to-Saturday week
    assert (summary["week_start"], summary["week_end"]) == (
        start.isoformat(),
        (start + timedelta(days=6)).isoformat(),
    )

    log(client, headers, FATIGUE)
    log(client, headers, FATIGUE, {"symptom": "severe_itching"})  # L2
    after = home(client, headers)
    assert after["logged_today"] is True
    s = after["weekly_summary"]
    assert s["days_logged"] == 1
    assert s["top_symptoms"] == [
        {"symptom": "fatigue", "label": "Tiredness", "count": 2},
        {"symptom": "severe_itching", "label": "Severe itching", "count": 1},
    ]
    assert s["red_flag_days"] == [TODAY.isoformat()]


def test_summary_without_dates_has_no_stage_content(client: TestClient, engine: Engine) -> None:
    headers = patient(engine, client, weeks=None)
    log(client, headers, FATIGUE)
    data = home(client, headers)
    assert data["logged_today"] is True and data["weekly_summary"]["common_at_stage"] == []


def test_calendar_symptom_days_with_levels(client: TestClient, engine: Engine) -> None:
    """§9.2 / Journey §15 test 8: a dot for any check-in, the levels for red-flag icons."""
    headers = patient(engine, client, weeks=24)
    log(client, headers, FATIGUE)
    log(client, headers, {"symptom": "vaginal_bleeding"})  # L1
    cal = client.get(
        "/api/v1/patient/journey/calendar",
        params={"from": TODAY.isoformat(), "to": TODAY.isoformat()},
        headers=headers,
    ).json()["data"]
    assert cal["symptom_days"] == [{"date": TODAY.isoformat(), "levels": ["L0", "L1"]}]
    other_day = TODAY - timedelta(days=3)
    empty = client.get(
        "/api/v1/patient/journey/calendar",
        params={"from": other_day.isoformat(), "to": other_day.isoformat()},
        headers=headers,
    ).json()["data"]
    assert empty["symptom_days"] == []


def test_no_weekly_summary_after_the_end_but_history_on_the_calendar(
    client: TestClient, engine: Engine
) -> None:
    headers = patient(engine, client, weeks=30)
    log(client, headers, FATIGUE)
    client.post(
        "/api/v1/patient/pregnancy-end",
        json={"status": "ended_not_specified", "inform_doctor": False},
        headers=headers,
    )
    data = home(client, headers)
    assert data["state"] == "ended" and data["weekly_summary"] is None
    cal = client.get(
        "/api/v1/patient/journey/calendar",
        params={"from": TODAY.isoformat(), "to": TODAY.isoformat()},
        headers=headers,
    ).json()["data"]
    assert [d["levels"] for d in cal["symptom_days"]] == [["L0"]]  # history stays (§11.3)
