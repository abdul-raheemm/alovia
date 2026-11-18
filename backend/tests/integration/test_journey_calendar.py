"""Task 6: calendar markers and appointments (Journey spec §6.4, §9.1-9.3, §14.2;
API.md §4.2). Runs against alovia-test. Titles and notes are obviously fake test strings."""

import uuid
from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
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
TZ = ZoneInfo(CFG.timezone)
TODAY = local_today(CFG.timezone)
APPTS = "/api/v1/patient/appointments"
CAL = "/api/v1/patient/journey/calendar"


@pytest.fixture(scope="module")
def client(test_db_url: str, engine: Engine) -> Iterator[TestClient]:
    app: FastAPI = make_app(database_url=test_db_url)
    yield TestClient(app)
    app.state.engine.dispose()


def patient(engine: Engine, client: TestClient, weeks: int | None = 24) -> tuple[Any, date | None]:
    """A linked patient; with `weeks`, dated by LMP so that GA = weeks today. Returns
    (auth headers, LMP = the day GA is 0)."""
    user_id, _ = add_linked_patient(engine)
    headers = bearer(sub=str(user_id))
    if weeks is None:
        return headers, None
    lmp = TODAY - timedelta(days=weeks * 7)
    res = client.put(
        "/api/v1/patient/journey/dates",
        json={"option": "lmp", "lmp_date": lmp.isoformat()},
        headers=headers,
    )
    assert res.status_code == 200
    return headers, lmp


def add(client: TestClient, headers: Any, **body: Any) -> Any:
    res = client.post(APPTS, json=body, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()["data"]


def patient_id_of(engine: Engine, headers: Any) -> uuid.UUID:
    """The patients.id behind a test token (its `sub` is the users.id)."""
    import jwt

    sub = jwt.decode(headers["Authorization"].split()[1], options={"verify_signature": False})
    with engine.connect() as conn:
        found: uuid.UUID = conn.execute(
            text("SELECT id FROM patients WHERE user_id = :u"), {"u": sub["sub"]}
        ).scalar_one()
    return found


def doctor_appointment(engine: Engine, headers: Any, at: datetime) -> uuid.UUID:
    """A doctor-added appointment (the Phase 5 doctor route does not exist yet)."""
    patient_id = patient_id_of(engine, headers)
    with engine.begin() as conn:
        doctor_user = uuid.uuid4()
        conn.execute(
            text("INSERT INTO users (id, email, role) VALUES (:id, :e, 'doctor')"),
            {"id": doctor_user, "e": f"{doctor_user}@example.test"},
        )
        appointment_id: uuid.UUID = conn.execute(
            text(
                "INSERT INTO appointments (patient_id, appointment_at, has_time, title, "
                "created_by, source) VALUES (:p, :at, true, 'Test doctor visit', :u, 'doctor') "
                "RETURNING id"
            ),
            {"p": patient_id, "at": at, "u": doctor_user},
        ).scalar_one()
    return appointment_id


# ---- §9.3 appointments ----


def test_create_list_edit_delete_own(client: TestClient, engine: Engine) -> None:
    headers, _ = patient(engine, client)
    later = TODAY + timedelta(days=5)
    timed = add(
        client,
        headers,
        date=later.isoformat(),
        time="10:30",
        title="  Test visit A  ",
        note="",
    )
    assert timed["title"] == "Test visit A"  # trimmed
    assert timed["note"] is None  # empty note is no note
    assert (timed["date"], timed["time"], timed["has_time"]) == (
        later.isoformat(),
        "10:30:00",
        True,
    )
    assert timed["source"] == "patient" and timed["can_edit"] is True
    # the stored moment is 10:30 in the patient's time zone (config), not in UTC
    assert datetime.fromisoformat(timed["appointment_at"]) == datetime(
        later.year, later.month, later.day, 10, 30, tzinfo=TZ
    )

    date_only = add(client, headers, date=TODAY.isoformat(), title="Test visit B", note="n")
    assert date_only["time"] is None and date_only["has_time"] is False
    past = add(client, headers, date=(TODAY - timedelta(days=3)).isoformat(), title="Test old")
    older = add(client, headers, date=(TODAY - timedelta(days=9)).isoformat(), title="Test older")

    listed = client.get(APPTS, headers=headers).json()["data"]
    # upcoming soonest first (a date-only one today still counts), past most recent first
    assert [a["id"] for a in listed["upcoming"]] == [date_only["id"], timed["id"]]
    assert [a["id"] for a in listed["past"]] == [past["id"], older["id"]]

    res = client.put(
        f"{APPTS}/{timed['id']}",
        json={"date": later.isoformat(), "title": "Test visit A2", "note": "Test note"},
        headers=headers,
    )
    assert res.status_code == 200
    edited = res.json()["data"]
    assert (edited["title"], edited["note"], edited["time"]) == ("Test visit A2", "Test note", None)

    res = client.delete(f"{APPTS}/{timed['id']}", headers=headers)
    assert res.status_code == 200 and res.json() == {"data": None, "error": None}
    listed = client.get(APPTS, headers=headers).json()["data"]
    assert timed["id"] not in [a["id"] for a in listed["upcoming"] + listed["past"]]


@pytest.mark.parametrize(
    ("body", "field"),
    [
        ({"date": "2026-12-01", "title": ""}, "title"),
        ({"date": "2026-12-01", "title": "   "}, "title"),
        ({"date": "2026-12-01", "title": "x" * 101}, "title"),
        ({"date": "2026-12-01", "title": "Test", "note": "x" * 501}, "note"),
        ({"date": "2026-12-01", "title": "Test", "time": "25:00"}, "time"),
        ({"title": "Test"}, "date"),
        ({"date": "2026-12-01", "title": "Test", "source": "doctor"}, "source"),
        # outside 1900-2999 a local date overflows when stored or read back
        ({"date": "0001-01-01", "title": "Test"}, "date"),
        ({"date": "9999-12-31", "title": "Test", "time": "23:59"}, "date"),
    ],
)
def test_appointment_input_is_validated(
    client: TestClient, engine: Engine, body: dict[str, Any], field: str
) -> None:
    headers, _ = patient(engine, client, weeks=None)
    res = client.post(APPTS, json=body, headers=headers)
    assert res.status_code == 400
    assert field in res.json()["error"]["fields"]


def test_limits_are_inclusive(client: TestClient, engine: Engine) -> None:
    headers, _ = patient(engine, client, weeks=None)
    add(client, headers, date="2026-12-01", title="x" * 100, note="y" * 500)


def test_doctor_added_is_listed_but_read_only(client: TestClient, engine: Engine) -> None:
    headers, _ = patient(engine, client)
    appointment_id = doctor_appointment(engine, headers, datetime.now(UTC) + timedelta(days=2))
    listed = client.get(APPTS, headers=headers).json()["data"]["upcoming"]
    assert [(a["source"], a["can_edit"]) for a in listed] == [("doctor", False)]
    body = {"date": TODAY.isoformat(), "title": "Test change"}
    assert client.put(f"{APPTS}/{appointment_id}", json=body, headers=headers).status_code == 403
    assert client.delete(f"{APPTS}/{appointment_id}", headers=headers).status_code == 403
    # still there, unchanged
    listed = client.get(APPTS, headers=headers).json()["data"]["upcoming"]
    assert [a["title"] for a in listed] == ["Test doctor visit"]


def test_another_patients_appointment_is_not_found(client: TestClient, engine: Engine) -> None:
    owner, _ = patient(engine, client, weeks=None)
    other, _ = patient(engine, client, weeks=None)
    theirs = add(client, owner, date=TODAY.isoformat(), title="Test private")
    body = {"date": TODAY.isoformat(), "title": "Test change"}
    assert client.put(f"{APPTS}/{theirs['id']}", json=body, headers=other).status_code == 404
    assert client.delete(f"{APPTS}/{theirs['id']}", headers=other).status_code == 404
    assert client.get(APPTS, headers=other).json()["data"] == {"upcoming": [], "past": []}
    missing = client.delete(f"{APPTS}/{uuid.uuid4()}", headers=owner)
    assert missing.status_code == 404


def test_appointments_need_a_linked_patient_with_consent(
    client: TestClient, engine: Engine
) -> None:
    user_id, _ = add_linked_patient(engine, consent=False)
    assert client.get(APPTS, headers=bearer(sub=str(user_id))).status_code == 403


# ---- §9.1-9.2 calendar ----


def calendar(client: TestClient, headers: Any, start: date, end: date) -> Any:
    res = client.get(
        CAL, params={"from": start.isoformat(), "to": end.isoformat()}, headers=headers
    )
    assert res.status_code == 200, res.text
    return res.json()["data"]


def test_calendar_milestones_and_range(client: TestClient, engine: Engine) -> None:
    headers, lmp = patient(engine, client, weeks=24)
    assert lmp is not None
    due = lmp + timedelta(days=280)
    week28 = lmp + timedelta(days=28 * 7)
    data = calendar(client, headers, week28 - timedelta(days=1), week28 + timedelta(days=1))
    # §9.1 navigation: pregnancy start to due date + 2 weeks
    assert (data["start"], data["end"]) == (lmp.isoformat(), (due + timedelta(days=14)).isoformat())
    # §6.4 at week 28: new week, month 7 starts (config month map), trimester 3
    assert {(m["date"], m["kind"], m["value"]) for m in data["milestones"]} == {
        (week28.isoformat(), "new_week", 28),
        (week28.isoformat(), "new_month", 7),
        (week28.isoformat(), "new_trimester", 3),
    }
    # §9.2 suggested check-ups (R3): PMSMA, the 9th of each month from week 14 (config)
    plan = CFG.suggested_checkups
    assert plan is not None
    window = calendar(client, headers, TODAY, TODAY + timedelta(days=62))
    expected = [
        d.isoformat()
        for d in (TODAY + timedelta(days=i) for i in range(63))
        if d.day == plan.day_of_month
    ]
    assert [c["date"] for c in window["suggested_checkups"]] == expected
    assert {c["label"] for c in window["suggested_checkups"]} == {plan.label}
    assert window["suggested_source"]["url"].startswith("https://nhm.gov.in/")
    term = lmp + timedelta(days=CFG.term_from_week * 7)
    kinds = {m["kind"] for m in calendar(client, headers, term, due)["milestones"]}
    assert {"term", "due_date"} <= kinds


def test_calendar_appointments_use_local_days(client: TestClient, engine: Engine) -> None:
    headers, _ = patient(engine, client)
    day = TODAY + timedelta(days=3)
    late = add(client, headers, date=day.isoformat(), time="23:30", title="Test late")
    early = add(client, headers, date=day.isoformat(), title="Test date only")
    add(client, headers, date=(day + timedelta(days=1)).isoformat(), title="Test next day")
    got = calendar(client, headers, day, day)["appointments"]
    # local 00:00 (date only) and 23:30 belong to `day`; the next day's does not
    assert [a["id"] for a in got] == [early["id"], late["id"]]


def test_calendar_without_dates_or_after_the_end(client: TestClient, engine: Engine) -> None:
    headers, _ = patient(engine, client, weeks=None)
    add(client, headers, date=TODAY.isoformat(), title="Test visit")
    data = calendar(client, headers, TODAY, TODAY)
    assert (data["start"], data["end"], data["milestones"]) == (None, None, [])
    assert data["suggested_checkups"] == [] and data["suggested_source"] is None
    assert [a["title"] for a in data["appointments"]] == ["Test visit"]

    ended, lmp = patient(engine, client, weeks=20)
    assert lmp is not None
    with engine.begin() as conn:  # set directly; the §11 route has its own tests
        conn.execute(
            text("UPDATE patients SET pregnancy_status = 'ended_not_specified' WHERE id = :p"),
            {"p": patient_id_of(engine, ended)},
        )
    data = calendar(client, ended, lmp, lmp + timedelta(days=294))
    assert data["milestones"] == [] and data["start"] is None  # no baby markers (§11.3)
    assert data["suggested_checkups"] == []  # no pregnancy check-ups after the end


def test_calendar_rejects_a_reversed_range(client: TestClient, engine: Engine) -> None:
    headers, _ = patient(engine, client)
    res = client.get(
        CAL,
        params={"from": TODAY.isoformat(), "to": (TODAY - timedelta(days=1)).isoformat()},
        headers=headers,
    )
    assert res.status_code == 400 and "to" in res.json()["error"]["fields"]
    assert client.get(CAL, params={"from": "nope", "to": "x"}, headers=headers).status_code == 400
    edge = {"from": "9999-12-31", "to": "9999-12-31"}  # end + 1 day would overflow
    assert client.get(CAL, params=edge, headers=headers).status_code == 400
