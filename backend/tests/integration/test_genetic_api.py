"""Patient genetic routes (Genetic spec §4.1, §8.2, §10.4; API.md §4.4) and the Journey
"Genetic check" card. Runs against alovia-test."""

import uuid
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from tests.helpers import add_linked_patient, bearer, make_app

URL = "/api/v1/patient/genetic/assessments"


@pytest.fixture(scope="module")
def app(test_db_url: str) -> Iterator[FastAPI]:
    application: FastAPI = make_app(database_url=test_db_url)
    yield application
    application.state.engine.dispose()


@pytest.fixture(scope="module")
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


def body(
    hbb: tuple[str, str] = ("beta_thal_carrier", "beta_thal_carrier"),
    hbb_child: str = "no",
    marfan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    def p(status: str) -> dict[str, Any]:
        return (
            {"status": status}
            if status == "unknown"
            else {"status": status, "evidence": "hplc_report"}
        )

    return {
        "haemoglobin_group": {
            "mother": p(hbb[0]),
            "father": p(hbb[1]),
            "previous_child": hbb_child,
        },
        "haemophilia": {"entry": "no"},
        "marfan": marfan or {"entry": "no"},
        "consanguinity": "no",
    }


def patient(engine: Engine) -> tuple[Any, uuid.UUID]:
    user_id, patient_id = add_linked_patient(engine)
    return bearer(sub=str(user_id)), patient_id


def inbox(engine: Engine, patient_id: uuid.UUID) -> list[str]:
    with engine.connect() as conn:
        return list(
            conn.execute(
                text("SELECT type FROM inbox_items WHERE patient_id = :p ORDER BY type"),
                {"p": patient_id},
            ).scalars()
        )


def count(engine: Engine, patient_id: uuid.UUID) -> int:
    with engine.connect() as conn:
        n: int = conn.execute(
            text("SELECT count(*) FROM genetic_assessments WHERE patient_id = :p"),
            {"p": patient_id},
        ).scalar_one()
    return n


def test_submit_saves_pending_review_with_inbox_items(client: TestClient, engine: Engine) -> None:
    headers, patient_id = patient(engine)
    res = client.post(URL, json=body(), headers=headers)
    assert res.status_code == 201, res.text
    data = res.json()["data"]
    assert data["review_status"] == "pending_review" and data["show_numbers_to_patient"] is True
    hbb = data["conditions"][0]
    assert (hbb["condition"], hbb["rule_id"], hbb["status"]) == (
        "haemoglobin_group",
        "HBB-10",
        "calculated",
    )
    assert {o["outcome"]: o["percent"] for o in hbb["outcomes"]} == {
        "beta_thal_major": 25, "beta_thal_carrier": 50, "neither": 25,
    }  # fmt: skip
    assert data["flags"]["risk_indicated"] is True
    assert data["message_keys"] == ["msg_speak_to_doctor_soon", "review_with_doctor"]
    assert data["disclaimer_key"] == "disclaimer_main" and "priority" not in data
    # DEC-071: pending always, high priority when risk is indicated (§9.2)
    assert inbox(engine, patient_id) == ["genetic_high_priority", "genetic_pending"]
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT priority, risk_indicated, rules_version FROM genetic_assessments "
                 "WHERE patient_id = :p"),
            {"p": patient_id},
        ).one()  # fmt: skip
    assert tuple(row) == ("high", True, "1.0.0")


def test_normal_priority_has_only_the_pending_item(client: TestClient, engine: Engine) -> None:
    headers, patient_id = patient(engine)
    res = client.post(URL, json=body(hbb=("tested_negative", "tested_negative")), headers=headers)
    assert res.json()["data"]["flags"]["risk_indicated"] is False
    assert inbox(engine, patient_id) == ["genetic_pending"]


@pytest.mark.parametrize(
    ("change", "field", "code"),
    [
        ({"consanguinity": None}, "consanguinity", "E1"),
        ({"marfan": {"entry": "yes"}}, "marfan.mother", "E1"),
        ({"marfan": {"entry": "maybe"}}, "marfan.entry", "E2"),
    ],
)
def test_e1_e2_save_nothing(
    client: TestClient, engine: Engine, change: dict[str, Any], field: str, code: str
) -> None:
    headers, patient_id = patient(engine)
    res = client.post(URL, json={**body(), **change}, headers=headers)
    assert res.status_code == 400 and res.json()["error"]["fields"] == {field: code}
    assert count(engine, patient_id) == 0 and inbox(engine, patient_id) == []


def test_unknown_fields_and_baby_sex_are_refused(client: TestClient, engine: Engine) -> None:
    """§11.3: there is no field for the baby's sex; unknown fields are refused."""
    headers, patient_id = patient(engine)
    assert client.post(URL, json={**body(), "baby_sex": "girl"}, headers=headers).status_code == 400
    assert count(engine, patient_id) == 0


def test_own_history_and_one_others_are_not_found(client: TestClient, engine: Engine) -> None:
    owner, _ = patient(engine)
    other, _ = patient(engine)
    first = client.post(URL, json=body(), headers=owner).json()["data"]
    second = client.post(URL, json=body(hbb=("unknown", "unknown")), headers=owner).json()["data"]
    listed = client.get(URL, headers=owner).json()["data"]
    assert [a["assessment_id"] for a in listed] == [second["assessment_id"], first["assessment_id"]]
    assert listed[0]["inputs"]["haemoglobin_group"]["mother"] == {"status": "unknown"}
    one = client.get(f"{URL}/{first['assessment_id']}", headers=owner)
    assert one.status_code == 200 and one.json()["data"]["assessment_id"] == first["assessment_id"]
    assert client.get(f"{URL}/{first['assessment_id']}", headers=other).status_code == 404
    assert client.get(URL, headers=other).json()["data"] == []


def test_numbers_hidden_until_review_when_the_setting_is_off(
    app: FastAPI, client: TestClient, engine: Engine
) -> None:
    """§8.2 / D4: show_result_before_review false hides numbers; after review they show."""
    rules = app.state.genetic_rules
    app.state.genetic_rules = rules.model_copy(
        update={"settings": rules.settings.model_copy(update={"show_result_before_review": False})}
    )
    try:
        headers, patient_id = patient(engine)
        data = client.post(URL, json=body(), headers=headers).json()["data"]
    finally:
        app.state.genetic_rules = rules
    assert data["show_numbers_to_patient"] is False
    assert (
        data["conditions"][0]["status"] == "calculated"
        and data["conditions"][0]["outcomes"] is None
    )
    assert "results_after_review" in data["message_keys"] and data["doctor_note"] is None
    with engine.begin() as conn:  # the Phase 5 doctor review, simulated
        conn.execute(
            text("UPDATE genetic_assessments SET review_status = 'reviewed', reviewed_at = now(), "
                 "doctor_note = 'Test doctor note' WHERE patient_id = :p"),
            {"p": patient_id},
        )  # fmt: skip
    after = client.get(f"{URL}/{data['assessment_id']}", headers=headers).json()["data"]
    assert after["show_numbers_to_patient"] is True and after["conditions"][0]["outcomes"]
    assert after["doctor_note"] == "Test doctor note"


def test_journey_genetic_check_card(client: TestClient, engine: Engine) -> None:
    """Journey §10.4 / DEC-073: the latest assessment's state, or nothing."""
    headers, patient_id = patient(engine)

    def check() -> Any:
        return client.get("/api/v1/patient/journey/home", headers=headers).json()["data"][
            "genetic_check"
        ]

    assert check() is None
    client.post(URL, json=body(hbb=("tested_negative", "tested_negative")), headers=headers)
    assert check() == "pending_review"
    client.post(URL, json=body(hbb=("unknown", "beta_thal_carrier")), headers=headers)
    assert check() == "needs_testing"
    client.post(
        URL,
        json=body(hbb=("tested_negative", "beta_thal_carrier"), hbb_child="yes"),
        headers=headers,
    )
    assert check() == "sent_to_doctor"  # C1 conflict
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE genetic_assessments SET review_status = 'reviewed' WHERE patient_id = :p"),
            {"p": patient_id},
        )
    assert check() == "reviewed"


def test_routes_need_a_linked_patient_with_consent(client: TestClient, engine: Engine) -> None:
    user_id, _ = add_linked_patient(engine, consent=False)
    headers = bearer(sub=str(user_id))
    assert client.get(URL, headers=headers).status_code == 403
    assert client.post(URL, json=body(), headers=headers).status_code == 403
