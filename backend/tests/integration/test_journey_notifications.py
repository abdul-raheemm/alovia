"""Task 7: notification bar and shared doctor notes (Journey spec §10.1-10.3, §11.3;
API.md §4.2). Runs against alovia-test. Note texts are obviously fake test strings."""

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

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
NOTES = "/api/v1/patient/notifications"


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


def unread(client: TestClient, headers: Any) -> list[dict[str, Any]]:
    res = client.get(NOTES, headers=headers)
    assert res.status_code == 200, res.text
    items: list[dict[str, Any]] = res.json()["data"]
    return items


def kinds(items: list[dict[str, Any]]) -> set[tuple[str, str | None]]:
    return {(n["type"], n["target_ref"]) for n in items}


def test_week_and_month_notices_are_created_once(client: TestClient, engine: Engine) -> None:
    headers = patient(engine, client, weeks=24)  # content week 24 -> month 6 (config map)
    first = unread(client, headers)
    assert kinds(first) == {("new_week", "24"), ("new_month", "6")}
    again = unread(client, headers)  # opening the app again creates nothing new
    assert {n["id"] for n in again} == {n["id"] for n in first}
    with engine.connect() as conn:
        count = conn.execute(
            text("SELECT count(*) FROM notifications WHERE patient_id = :p"),
            {"p": patient_id_of(engine, headers)},
        ).scalar_one()
    assert count == 2


def test_no_dates_no_week_notices(client: TestClient, engine: Engine) -> None:
    assert unread(client, patient(engine, client, weeks=None)) == []


def add_appointment(client: TestClient, headers: Any, at: datetime | None, day: Any = None) -> str:
    """at: a timed appointment (local time); day: a date-only appointment."""
    if at is not None:
        local = at.astimezone(ZoneInfo(CFG.timezone))
        body = {"date": local.date().isoformat(), "time": local.strftime("%H:%M"), "title": "T"}
    else:
        body = {"date": day.isoformat(), "title": "T"}
    res = client.post("/api/v1/patient/appointments", json=body, headers=headers)
    assert res.status_code == 201
    appointment_id: str = res.json()["data"]["id"]
    return appointment_id


def test_appointment_soon_window(client: TestClient, engine: Engine) -> None:
    headers = patient(engine, client, weeks=None)
    now = datetime.now(UTC)
    hours = CFG.appointment_notice_hours
    soon = add_appointment(client, headers, now + timedelta(hours=3))
    add_appointment(client, headers, now + timedelta(hours=hours + 6))  # too far ahead
    add_appointment(client, headers, now - timedelta(hours=2))  # already past
    today_only = add_appointment(client, headers, None, day=TODAY)  # date-only, today
    add_appointment(client, headers, None, day=TODAY + timedelta(days=3))
    assert kinds(unread(client, headers)) == {
        ("appointment_soon", soon),
        ("appointment_soon", today_only),
    }


def test_read_and_dismiss_remove_from_the_bar_for_good(client: TestClient, engine: Engine) -> None:
    headers = patient(engine, client, weeks=24)
    items = {n["type"]: n["id"] for n in unread(client, headers)}
    res = client.post(f"{NOTES}/{items['new_week']}/read", headers=headers)
    assert res.status_code == 200 and res.json() == {"data": None, "error": None}
    assert client.post(f"{NOTES}/{items['new_month']}/dismiss", headers=headers).status_code == 200
    assert unread(client, headers) == []  # and not created again (unique constraint)
    # repeating is harmless; the first time stays recorded
    assert client.post(f"{NOTES}/{items['new_week']}/read", headers=headers).status_code == 200


def test_other_patients_notification_is_not_found(client: TestClient, engine: Engine) -> None:
    owner = patient(engine, client, weeks=24)
    other = patient(engine, client, weeks=None)
    theirs = unread(client, owner)[0]["id"]
    assert client.post(f"{NOTES}/{theirs}/read", headers=other).status_code == 404
    assert client.post(f"{NOTES}/{theirs}/dismiss", headers=other).status_code == 404
    assert client.post(f"{NOTES}/{uuid.uuid4()}/read", headers=owner).status_code == 404
    assert len(unread(client, owner)) == 2  # untouched


def test_ended_pregnancy_has_no_baby_stage_notices(client: TestClient, engine: Engine) -> None:
    headers = patient(engine, client, weeks=24)
    assert len(unread(client, headers)) == 2  # week + month, still unread
    soon = add_appointment(client, headers, datetime.now(UTC) + timedelta(hours=2))
    with engine.begin() as conn:  # set directly; the §11 route has its own tests
        conn.execute(
            text("UPDATE patients SET pregnancy_status = 'ended_loss' WHERE id = :p"),
            {"p": patient_id_of(engine, headers)},
        )
    # §10.2/§11.3: week and month notices stop and old unread ones are not shown;
    # other notices (appointments) continue
    assert kinds(unread(client, headers)) == {("appointment_soon", soon)}


def add_doctor_notes(engine: Engine, patient_id: uuid.UUID) -> dict[str, uuid.UUID]:
    doctor_user = uuid.uuid4()
    now = datetime.now(UTC)
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO users (id, email, role) VALUES (:id, :e, 'doctor')"),
            {"id": doctor_user, "e": f"{doctor_user}@example.test"},
        )
        doctor_id = conn.execute(
            text("INSERT INTO doctors (user_id, name) VALUES (:u, 'Test Doctor') RETURNING id"),
            {"u": doctor_user},
        ).scalar_one()
        ids = {}
        for body, visible, age in (
            ("Test shared older", True, 2),
            ("Test private", False, 1),
            ("Test shared newer", True, 0),
        ):
            ids[body] = conn.execute(
                text(
                    "INSERT INTO doctor_notes (patient_id, doctor_id, body, visible_to_patient, "
                    "created_at) VALUES (:p, :d, :b, :v, :c) RETURNING id"
                ),
                {
                    "p": patient_id,
                    "d": doctor_id,
                    "b": body,
                    "v": visible,
                    "c": now - timedelta(days=age),
                },
            ).scalar_one()
    return ids


def test_doctor_notes_only_shared_newest_first(client: TestClient, engine: Engine) -> None:
    headers = patient(engine, client, weeks=None)
    ids = add_doctor_notes(engine, patient_id_of(engine, headers))
    res = client.get("/api/v1/patient/doctor-notes", headers=headers)
    assert res.status_code == 200
    notes = res.json()["data"]
    assert [n["body"] for n in notes] == ["Test shared newer", "Test shared older"]
    assert notes[0]["doctor_name"] == "Test Doctor" and notes[0]["created_on"] == TODAY.isoformat()
    # a doctor_note notification for each shared note only, never the private one
    assert kinds(unread(client, headers)) == {
        ("doctor_note", str(ids["Test shared newer"])),
        ("doctor_note", str(ids["Test shared older"])),
    }
    # another patient sees none of them
    assert (
        client.get("/api/v1/patient/doctor-notes", headers=patient(engine, client)).json()["data"]
        == []
    )


def test_routes_need_a_linked_patient_with_consent(client: TestClient, engine: Engine) -> None:
    user_id, _ = add_linked_patient(engine, consent=False)
    headers = bearer(sub=str(user_id))
    assert client.get(NOTES, headers=headers).status_code == 403
    assert client.get("/api/v1/patient/doctor-notes", headers=headers).status_code == 403
