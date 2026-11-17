"""GET /patient/journey/home and PUT /patient/journey/dates (Journey spec §4.5, §5; spec tests
§15 items 2 and 10). Runs against the alovia-test database (see tests/conftest.py).
"""

import uuid
from collections.abc import Iterator
from datetime import date, timedelta
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from app.modules.journey.config import load_journey_config
from app.modules.journey.engine import local_today
from tests.helpers import add_linked_patient, bearer, make_app

TODAY = local_today(load_journey_config().timezone)
HOME = "/api/v1/patient/journey/home"
DATES = "/api/v1/patient/journey/dates"


@pytest.fixture(scope="module")
def client(test_db_url: str, engine: Engine) -> Iterator[TestClient]:
    app: FastAPI = make_app(database_url=test_db_url)
    yield TestClient(app)
    app.state.engine.dispose()


def put(client: TestClient, user_id: uuid.UUID, **body: Any) -> Any:
    return client.put(DATES, json=body, headers=bearer(sub=str(user_id)))


def home(client: TestClient, user_id: uuid.UUID) -> Any:
    res = client.get(HOME, headers=bearer(sub=str(user_id)))
    assert res.status_code == 200
    return res.json()["data"]


def iso(d: date) -> str:
    return d.isoformat()


def history(engine: Engine, patient_id: uuid.UUID) -> list[tuple[Any, ...]]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT old_due_date, new_due_date, old_source, new_source, old_status, "
                "new_status, changed_by FROM pregnancy_date_history WHERE patient_id = :p "
                "ORDER BY created_at"
            ),
            {"p": patient_id},
        ).all()
    return [tuple(r) for r in rows]


# ---- who may use the routes ----


def test_needs_a_signed_in_linked_patient_with_consent(client: TestClient, engine: Engine) -> None:
    assert client.get(HOME).status_code == 401
    doctor, _ = add_linked_patient(engine, role="doctor", link=False)
    unlinked, _ = add_linked_patient(engine, link=False)
    no_consent, patient_id = add_linked_patient(engine, consent=False)
    for user_id in (doctor, unlinked, no_consent):
        assert client.get(HOME, headers=bearer(sub=str(user_id))).status_code == 403
        assert put(client, user_id, option="lmp", lmp_date=iso(TODAY)).status_code == 403
    assert history(engine, patient_id) == []  # nothing was saved without consent


# ---- home ----


def test_home_without_dates_shows_onboarding_state(client: TestClient, engine: Engine) -> None:
    user_id, _ = add_linked_patient(engine)
    data = home(client, user_id)
    assert data["state"] == "no_date"
    assert data["pregnancy"] is None
    assert data["dates"] == {"due_date": None, "lmp_date": None, "due_date_source": None}
    assert [i["key"] for i in data["nav_items"]] == [
        "home", "calendar", "log_symptoms", "appointments", "doctor_notes", "more",
    ]  # fmt: skip
    assert data["show_prototype_banner"] is True
    # DEC-041: no approved wording yet, so every message text is null
    assert "msg_onboarding" in data["messages"]
    assert set(data["messages"].values()) == {None}


# ---- option A, B, C ----


def test_option_a_lmp(client: TestClient, engine: Engine) -> None:
    user_id, patient_id = add_linked_patient(engine)
    lmp = TODAY - timedelta(days=24 * 7 + 3)
    res = put(client, user_id, option="lmp", lmp_date=iso(lmp))
    assert res.status_code == 200
    data = res.json()["data"]
    due = lmp + timedelta(days=280)
    assert data["dates"] == {
        "due_date": iso(due),
        "lmp_date": iso(lmp),
        "due_date_source": "lmp_estimate",
    }
    assert data["state"] == "active"
    assert data["pregnancy"] == {
        "completed_weeks": 24,
        "days": 3,
        "days_to_go": 280 - 171,
        "content_week": 24,
        "trimester": 2,
        "month": 6,
        "is_estimate": True,
    }
    assert data["notices"] == []
    assert home(client, user_id)["pregnancy"] == data["pregnancy"]  # saved, not just echoed
    assert history(engine, patient_id) == [(None, due, None, "lmp_estimate", None, None, user_id)]


def test_option_b_doctor_due_date(client: TestClient, engine: Engine) -> None:
    user_id, _ = add_linked_patient(engine)
    due = TODAY + timedelta(days=100)
    data = put(client, user_id, option="due_date", due_date=iso(due)).json()["data"]
    assert data["dates"] == {
        "due_date": iso(due),
        "lmp_date": None,
        "due_date_source": "clinician_confirmed",
    }
    assert data["pregnancy"]["is_estimate"] is False
    assert (data["pregnancy"]["completed_weeks"], data["pregnancy"]["days"]) == (25, 5)


def test_option_c_ultrasound(client: TestClient, engine: Engine) -> None:
    user_id, _ = add_linked_patient(engine)
    scan = TODAY - timedelta(days=47)
    res = put(client, user_id, option="ultrasound", scan_date=iso(scan), ga_weeks=12, ga_days=4)
    data = res.json()["data"]
    assert data["dates"]["due_date"] == iso(scan + timedelta(days=280 - 88))
    assert data["dates"]["due_date_source"] == "ultrasound"
    assert (data["pregnancy"]["completed_weeks"], data["pregnancy"]["days"]) == (19, 2)


# ---- validation D1-D3 ----


@pytest.mark.parametrize(
    ("body", "fields"),
    [
        ({"option": "lmp", "lmp_date": iso(TODAY + timedelta(days=1))}, {"lmp_date": "D1"}),
        ({"option": "lmp", "lmp_date": iso(TODAY - timedelta(days=295))}, {"lmp_date": "D2"}),
        ({"option": "due_date", "due_date": iso(TODAY + timedelta(days=281))}, {"due_date": "D2"}),
        ({"option": "due_date", "due_date": iso(TODAY - timedelta(days=15))}, {"due_date": "D2"}),
        (
            {
                "option": "ultrasound",
                "scan_date": iso(TODAY + timedelta(days=1)),
                "ga_weeks": 12,
                "ga_days": 0,
            },
            {"scan_date": "D1"},
        ),
        (
            {"option": "ultrasound", "scan_date": iso(TODAY), "ga_weeks": 43, "ga_days": 0},
            {"ga_weeks": "D3"},
        ),
        (
            {"option": "ultrasound", "scan_date": iso(TODAY), "ga_weeks": 42, "ga_days": 1},
            {"ga_weeks": "D3"},
        ),
    ],
    ids=["D1-lmp", "D2-lmp", "D2-due-far", "D2-due-old", "D1-scan", "D3-43w", "D3-42w1d"],
)
def test_date_rules_reject_and_save_nothing(
    client: TestClient, engine: Engine, body: dict[str, Any], fields: dict[str, str]
) -> None:
    user_id, patient_id = add_linked_patient(engine)
    res = put(client, user_id, **body)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"
    assert res.json()["error"]["fields"] == fields
    assert home(client, user_id)["state"] == "no_date"
    assert history(engine, patient_id) == []


def test_limits_themselves_are_accepted(client: TestClient, engine: Engine) -> None:
    for body in (
        {"option": "lmp", "lmp_date": iso(TODAY)},  # GA 0
        {"option": "lmp", "lmp_date": iso(TODAY - timedelta(days=294))},  # exactly 42 weeks
        {"option": "due_date", "due_date": iso(TODAY + timedelta(days=280))},
        {"option": "ultrasound", "scan_date": iso(TODAY), "ga_weeks": 42, "ga_days": 0},
    ):
        user_id, _ = add_linked_patient(engine)
        assert put(client, user_id, **body).status_code == 200, body


@pytest.mark.parametrize(
    "body",
    [
        {"option": "lmp"},  # date missing
        {"option": "lmp", "lmp_date": "17-11-2026"},  # not a date
        {"option": "moon", "lmp_date": "2026-11-17"},  # unknown option
        {"option": "lmp", "lmp_date": "2026-11-17", "due_date": "2027-01-01"},  # extra field
        {"option": "ultrasound", "scan_date": "2026-11-17", "ga_weeks": 12, "ga_days": 7},
        {"option": "lmp", "lmp_date": "2026-11-17", "confirm_override": "yes"},  # not a boolean
    ],
    ids=["missing", "bad-date", "bad-option", "extra", "ga-days-7", "confirm-string"],
)
def test_malformed_bodies_are_400(client: TestClient, engine: Engine, body: dict[str, Any]) -> None:
    user_id, _ = add_linked_patient(engine)
    res = put(client, user_id, **body)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


# ---- §5.3 changing dates ----


def test_clinician_date_is_not_silently_replaced_by_an_lmp_estimate(
    client: TestClient, engine: Engine
) -> None:
    user_id, patient_id = add_linked_patient(engine)
    doctor_due = TODAY + timedelta(days=100)
    assert put(client, user_id, option="due_date", due_date=iso(doctor_due)).status_code == 200
    lmp = TODAY - timedelta(days=150)

    res = put(client, user_id, option="lmp", lmp_date=iso(lmp))
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "CONFLICT"
    assert res.json()["error"]["fields"] == {
        "confirm_override": "msg_confirm_override_clinician_date"
    }
    assert home(client, user_id)["dates"]["due_date"] == iso(doctor_due)  # unchanged
    assert len(history(engine, patient_id)) == 1

    res = put(client, user_id, option="lmp", lmp_date=iso(lmp), confirm_override=True)
    assert res.status_code == 200
    assert res.json()["data"]["dates"]["due_date_source"] == "lmp_estimate"
    assert history(engine, patient_id)[-1] == (
        doctor_due,
        lmp + timedelta(days=280),
        "clinician_confirmed",
        "lmp_estimate",
        None,
        None,
        user_id,
    )


def test_scan_date_is_protected_the_same_way(client: TestClient, engine: Engine) -> None:
    user_id, _ = add_linked_patient(engine)
    assert (
        put(
            client, user_id, option="ultrasound", scan_date=iso(TODAY), ga_weeks=10, ga_days=0
        ).status_code
        == 200
    )
    assert (
        put(client, user_id, option="lmp", lmp_date=iso(TODAY - timedelta(days=80))).status_code
        == 409
    )


def test_clinician_or_scan_date_replaces_an_estimate_with_a_notice(
    client: TestClient, engine: Engine
) -> None:
    user_id, patient_id = add_linked_patient(engine)
    lmp = TODAY - timedelta(days=90)
    assert put(client, user_id, option="lmp", lmp_date=iso(lmp)).status_code == 200
    res = put(client, user_id, option="due_date", due_date=iso(TODAY + timedelta(days=180)))
    assert res.status_code == 200  # no confirmation needed in this direction
    data = res.json()["data"]
    assert data["notices"] == ["msg_dates_updated_by_clinician"]
    assert data["dates"]["due_date_source"] == "clinician_confirmed"
    assert data["dates"]["lmp_date"] == iso(lmp)  # the LMP she gave stays on record
    assert len(history(engine, patient_id)) == 2
    assert home(client, user_id)["notices"] == []  # a notice is shown once, with the change


def test_same_dates_again_add_no_history(client: TestClient, engine: Engine) -> None:
    user_id, patient_id = add_linked_patient(engine)
    body = {"option": "lmp", "lmp_date": iso(TODAY - timedelta(days=70))}
    assert put(client, user_id, **body).status_code == 200
    assert put(client, user_id, **body).status_code == 200
    assert len(history(engine, patient_id)) == 1


# ---- home states from stored dates (§4.5) ----


@pytest.mark.parametrize(
    ("ga_days", "state", "weeks", "content_week"),
    [(39 * 7 + 6, "active", 39, 39), (40 * 7, "past_due", 40, 40), (42 * 7, "beyond_42", 42, 42)],
)
def test_home_states_follow_the_week(
    client: TestClient, engine: Engine, ga_days: int, state: str, weeks: int, content_week: int
) -> None:
    user_id, _ = add_linked_patient(engine)
    assert (
        put(
            client, user_id, option="lmp", lmp_date=iso(TODAY - timedelta(days=ga_days))
        ).status_code
        == 200
    )
    data = home(client, user_id)
    assert data["state"] == state
    assert (data["pregnancy"]["completed_weeks"], data["pregnancy"]["content_week"]) == (
        weeks,
        content_week,
    )


def test_ended_pregnancy_shows_no_pregnancy_numbers(client: TestClient, engine: Engine) -> None:
    user_id, patient_id = add_linked_patient(engine)
    assert (
        put(client, user_id, option="lmp", lmp_date=iso(TODAY - timedelta(days=100))).status_code
        == 200
    )
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE patients SET pregnancy_status = 'ended_loss' WHERE id = :p"),
            {"p": patient_id},
        )
    data = home(client, user_id)
    assert data["state"] == "ended"
    assert data["pregnancy"] is None  # §11.3: no baby content after the pregnancy has ended
