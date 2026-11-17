"""Patient-side activity log (Dashboard spec §20; owner decision 2026-11-17): dates changed,
appointment created / edited / deleted, pregnancy status changed. Runs against alovia-test."""

import uuid
from collections.abc import Iterator
from datetime import timedelta
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from app.modules.journey.config import load_journey_config
from app.modules.journey.engine import local_today
from tests.helpers import add_linked_patient, bearer, make_app

TODAY = local_today(load_journey_config().timezone)


@pytest.fixture(scope="module")
def client(test_db_url: str, engine: Engine) -> Iterator[TestClient]:
    app: FastAPI = make_app(database_url=test_db_url)
    yield TestClient(app)
    app.state.engine.dispose()


def audit(engine: Engine, user_id: uuid.UUID) -> list[Any]:
    with engine.connect() as conn:
        return list(
            conn.execute(
                text(
                    "SELECT action, entity_type, entity_id, patient_id, details FROM audit_log "
                    "WHERE actor_user_id = :u AND action <> 'signed in' ORDER BY created_at, action"
                ),
                {"u": user_id},
            ).mappings()
        )


def test_patient_changes_are_logged_without_clinical_values(
    client: TestClient, engine: Engine
) -> None:
    user_id, patient_id = add_linked_patient(engine)
    h = bearer(sub=str(user_id))
    lmp = (TODAY - timedelta(days=150)).isoformat()
    assert (
        client.put(
            "/api/v1/patient/journey/dates", json={"option": "lmp", "lmp_date": lmp}, headers=h
        ).status_code
        == 200
    )
    created = client.post(
        "/api/v1/patient/appointments",
        json={"date": TODAY.isoformat(), "title": "Test visit", "note": "Test note"},
        headers=h,
    ).json()["data"]
    url = f"/api/v1/patient/appointments/{created['id']}"
    body = {"date": TODAY.isoformat(), "title": "Test visit 2"}
    assert client.put(url, json=body, headers=h).status_code == 200
    assert client.delete(url, headers=h).status_code == 200
    end = {"status": "ended_not_specified", "inform_doctor": False}
    assert client.post("/api/v1/patient/pregnancy-end", json=end, headers=h).status_code == 200
    assert client.post("/api/v1/patient/pregnancy-end/undo", headers=h).status_code == 200

    rows = audit(engine, user_id)
    assert [r["action"] for r in rows] == [
        "dates changed",
        "appointment created",
        "appointment edited",
        "appointment deleted",
        "pregnancy status changed",
        "pregnancy status changed",
    ]
    assert all(r["patient_id"] == patient_id for r in rows)
    assert all(r["details"] is None for r in rows)  # no dates, titles, notes or statuses
    appointment_rows = [r for r in rows if r["entity_type"] == "appointment"]
    assert {r["entity_id"] for r in appointment_rows} == {created["id"]}  # kept after delete


def test_refused_or_unchanged_actions_are_not_logged(client: TestClient, engine: Engine) -> None:
    user_id, _ = add_linked_patient(engine)
    h = bearer(sub=str(user_id))
    lmp = (TODAY - timedelta(days=150)).isoformat()
    for _ in range(2):  # the second, identical call changes nothing
        client.put(
            "/api/v1/patient/journey/dates", json={"option": "lmp", "lmp_date": lmp}, headers=h
        )
    bad = {"option": "lmp", "lmp_date": (TODAY + timedelta(days=1)).isoformat()}  # D1
    assert client.put("/api/v1/patient/journey/dates", json=bad, headers=h).status_code == 400
    assert (
        client.delete(f"/api/v1/patient/appointments/{uuid.uuid4()}", headers=h).status_code == 404
    )
    assert client.post("/api/v1/patient/pregnancy-end/undo", headers=h).status_code == 409
    assert [r["action"] for r in audit(engine, user_id)] == ["dates changed"]
