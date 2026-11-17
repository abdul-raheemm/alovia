"""Task 8: when a pregnancy ends, and undo (Journey spec §11.2-11.6, §15 test 9;
API.md §4.2). Runs against alovia-test."""

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from app.modules.journey.config import load_journey_config
from app.modules.journey.engine import local_today
from tests.helpers import add_linked_patient, bearer, make_app

CFG = load_journey_config()
TODAY = local_today(CFG.timezone)
END = "/api/v1/patient/pregnancy-end"


@pytest.fixture(scope="module")
def client(test_db_url: str, engine: Engine) -> Iterator[TestClient]:
    app: FastAPI = make_app(database_url=test_db_url)
    yield TestClient(app)
    app.state.engine.dispose()


def dated_patient(engine: Engine, client: TestClient, weeks: int = 30) -> Any:
    user_id, _ = add_linked_patient(engine)
    headers = bearer(sub=str(user_id))
    lmp = TODAY - timedelta(days=weeks * 7)
    res = client.put(
        "/api/v1/patient/journey/dates",
        json={"option": "lmp", "lmp_date": lmp.isoformat()},
        headers=headers,
    )
    assert res.status_code == 200
    return headers


def patient_id_of(engine: Engine, headers: Any) -> uuid.UUID:
    sub = jwt.decode(headers["Authorization"].split()[1], options={"verify_signature": False})
    with engine.connect() as conn:
        found: uuid.UUID = conn.execute(
            text("SELECT id FROM patients WHERE user_id = :u"), {"u": sub["sub"]}
        ).scalar_one()
    return found


def rows(engine: Engine, sql: str, patient_id: uuid.UUID) -> list[Any]:
    with engine.connect() as conn:
        return list(conn.execute(text(sql), {"p": patient_id}).mappings())


@pytest.mark.parametrize("status", ["ended_birth", "ended_loss", "ended_not_specified"])
def test_each_choice_stops_baby_content(client: TestClient, engine: Engine, status: str) -> None:
    headers = dated_patient(engine, client)
    assert len(client.get("/api/v1/patient/notifications", headers=headers).json()["data"]) == 2
    res = client.post(END, json={"status": status, "inform_doctor": False}, headers=headers)
    assert res.status_code == 200, res.text
    home = res.json()["data"]
    # §11.3: no baby card, size, month cards or weekly content
    assert home["state"] == "ended" and home["pregnancy"] is None
    assert home["months"] == [] and home["stage_items"] == [] and home["size"] is None
    assert home["ended"]["status"] == status
    ended_at = datetime.fromisoformat(home["ended"]["ended_at"])
    undo_until = datetime.fromisoformat(home["ended"]["undo_until"])
    assert undo_until - ended_at == timedelta(days=CFG.resume_window_days)
    assert client.get("/api/v1/patient/journey/months/7", headers=headers).status_code == 404
    # new_week / new_month stop and old unread ones are not shown
    assert client.get("/api/v1/patient/notifications", headers=headers).json()["data"] == []
    patient_id = patient_id_of(engine, headers)
    (p,) = rows(engine, "SELECT * FROM patients WHERE id = :p", patient_id)
    assert p["pregnancy_status"] == status and p["doctor_informed_of_end"] is False
    history = rows(
        engine,
        "SELECT old_status, new_status FROM pregnancy_date_history "
        "WHERE patient_id = :p AND new_status IS NOT NULL",
        patient_id,
    )
    assert [(h["old_status"], h["new_status"]) for h in history] == [("active", status)]


def test_doctor_is_informed_only_on_yes(client: TestClient, engine: Engine) -> None:
    said_no = dated_patient(engine, client)
    client.post(END, json={"status": "ended_loss", "inform_doctor": False}, headers=said_no)
    assert (
        rows(
            engine,
            "SELECT * FROM inbox_items WHERE patient_id = :p",
            patient_id_of(engine, said_no),
        )
        == []
    )

    said_yes = dated_patient(engine, client)
    client.post(END, json={"status": "ended_loss", "inform_doctor": True}, headers=said_yes)
    patient_id = patient_id_of(engine, said_yes)
    (item,) = rows(engine, "SELECT * FROM inbox_items WHERE patient_id = :p", patient_id)
    assert (item["type"], item["ref_table"]) == ("pregnancy_ended", "pregnancy_date_history")
    (history,) = rows(
        engine,
        "SELECT id FROM pregnancy_date_history WHERE patient_id = :p AND new_status IS NOT NULL",
        patient_id,
    )
    assert item["ref_id"] == history["id"]  # points at the status change it reports


@pytest.mark.parametrize(
    "body",
    [
        {"status": "ended_birth"},  # §11.2: the question has no default
        {"status": "ended_birth", "inform_doctor": "yes"},
        {"status": "ended_birth", "inform_doctor": None},
        {"status": "active", "inform_doctor": False},
        {"status": "ended_birth", "inform_doctor": False, "note": "x"},
    ],
)
def test_end_input_is_validated(client: TestClient, engine: Engine, body: dict[str, Any]) -> None:
    headers = dated_patient(engine, client)
    res = client.post(END, json=body, headers=headers)
    assert res.status_code == 400
    home = client.get("/api/v1/patient/journey/home", headers=headers).json()["data"]
    assert home["state"] == "active"  # nothing changed


def test_ending_twice_is_refused(client: TestClient, engine: Engine) -> None:
    headers = dated_patient(engine, client)
    body = {"status": "ended_birth", "inform_doctor": False}
    assert client.post(END, json=body, headers=headers).status_code == 200
    assert client.post(END, json=body, headers=headers).status_code == 409


def test_undo_within_the_window_restores_active(client: TestClient, engine: Engine) -> None:
    headers = dated_patient(engine, client)
    client.post(END, json={"status": "ended_not_specified", "inform_doctor": True}, headers=headers)
    res = client.post(f"{END}/undo", headers=headers)
    assert res.status_code == 200
    home = res.json()["data"]
    assert home["state"] == "active" and home["ended"] is None
    assert home["pregnancy"]["completed_weeks"] == 30 and len(home["months"]) == 9
    patient_id = patient_id_of(engine, headers)
    (p,) = rows(engine, "SELECT * FROM patients WHERE id = :p", patient_id)
    assert p["pregnancy_ended_at"] is None and p["doctor_informed_of_end"] is None
    history = rows(
        engine,
        "SELECT old_status, new_status FROM pregnancy_date_history "
        "WHERE patient_id = :p AND new_status IS NOT NULL ORDER BY created_at",
        patient_id,
    )
    assert [(h["old_status"], h["new_status"]) for h in history] == [
        ("active", "ended_not_specified"),
        ("ended_not_specified", "active"),  # §11.6: the undo is logged
    ]
    # the inbox item already sent is never deleted (DATABASE.md)
    assert len(rows(engine, "SELECT * FROM inbox_items WHERE patient_id = :p", patient_id)) == 1


def test_undo_after_the_window_or_when_active_is_refused(
    client: TestClient, engine: Engine
) -> None:
    headers = dated_patient(engine, client)
    assert client.post(f"{END}/undo", headers=headers).status_code == 409  # not ended
    client.post(END, json={"status": "ended_birth", "inform_doctor": False}, headers=headers)
    with engine.begin() as conn:  # move the end back past resume_window_days
        conn.execute(
            text("UPDATE patients SET pregnancy_ended_at = :t WHERE id = :p"),
            {
                "t": datetime.now(UTC) - timedelta(days=CFG.resume_window_days, minutes=1),
                "p": patient_id_of(engine, headers),
            },
        )
    home = client.get("/api/v1/patient/journey/home", headers=headers).json()["data"]
    assert home["ended"]["undo_until"] is None  # the app hides the undo button
    assert client.post(f"{END}/undo", headers=headers).status_code == 409


def test_routes_need_a_linked_patient_with_consent(client: TestClient, engine: Engine) -> None:
    user_id, _ = add_linked_patient(engine, consent=False)
    headers = bearer(sub=str(user_id))
    body = {"status": "ended_birth", "inform_doctor": False}
    assert client.post(END, json=body, headers=headers).status_code == 403
    assert client.post(f"{END}/undo", headers=headers).status_code == 403
