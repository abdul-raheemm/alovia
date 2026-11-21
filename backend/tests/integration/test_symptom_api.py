"""Patient symptom routes (Symptom spec §4-10, §14 tests 8 and 10; API.md §4.3). Runs against
alovia-test. Notes and names are obviously fake test strings."""

import uuid
from collections.abc import Iterator
from datetime import timedelta
from typing import Any

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from app.modules.journey.config import load_journey_config
from app.modules.journey.engine import local_today
from app.modules.symptoms import engine as symptom_engine
from tests.helpers import add_linked_patient, bearer, make_app

TODAY = local_today(load_journey_config().timezone)
URL = "/api/v1/patient/symptoms"
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


def post(client: TestClient, headers: Any, *entries: dict[str, Any], source: str = "form") -> Any:
    return client.post(
        f"{URL}/checkins", json={"source": source, "entries": list(entries)}, headers=headers
    )


def rows(engine: Engine, sql: str, pid: uuid.UUID) -> list[Any]:
    with engine.connect() as conn:
        return list(conn.execute(text(sql), {"p": pid}).mappings())


def test_vocabulary_is_filtered_by_week(client: TestClient, engine: Engine) -> None:
    early = client.get(f"{URL}/vocabulary", headers=patient(engine, client, weeks=10)).json()
    data = early["data"]
    assert data["logging_open"] is True and data["pregnancy_week"] == 10
    warning = {s["id"] for s in data["warning"]}
    assert "baby_movements_reduced" not in warning and "baby_movements_never_felt" not in warning
    assert len(data["common"]) == 10 and len(data["puqe_questions"]) == 3
    assert data["draft_ttl_minutes"] == 30  # DEC-109
    assert [(b["band"], b["min"], b["max"]) for b in data["puqe_bands"]] == [
        ("mild", 3, 6),
        ("moderate", 7, 12),
        ("severe", 13, 15),
    ]
    unknown = client.get(f"{URL}/vocabulary", headers=patient(engine, client, weeks=None))
    ids = {s["id"] for s in unknown.json()["data"]["warning"]}
    assert {"baby_movements_reduced", "baby_movements_never_felt"} <= ids  # §1.3, DEC-065


def test_l1_checkin_is_saved_with_its_entries_and_inbox_item(
    client: TestClient, engine: Engine
) -> None:
    headers = patient(engine, client, weeks=24)
    res = post(client, headers, {"symptom": "vaginal_bleeding"}, source="urgent_button")
    assert res.status_code == 201, res.text
    data = res.json()["data"]
    assert (data["red_flag_level"], data["matched_rules"]) == ("L1", ["L1-01"])
    assert data["message_keys"] == ["msg_level1_go_now"] and data["pregnancy_week"] == 24
    assert "pattern_changes" not in data
    pid = patient_id_of(engine, headers)
    (checkin,) = rows(engine, "SELECT * FROM symptom_checkins WHERE patient_id = :p", pid)
    assert (checkin["source"], checkin["rules_version"]) == ("urgent_button", "1.0.0")
    assert [r["symptom"] for r in rows(engine, "SELECT * FROM symptom_logs WHERE patient_id = :p",
                                       pid)] == ["vaginal_bleeding"]  # fmt: skip
    inbox = rows(
        engine, "SELECT type, ref_table, ref_id FROM inbox_items WHERE patient_id = :p", pid
    )
    assert [(i["type"], i["ref_table"], i["ref_id"]) for i in inbox] == [
        ("symptom_l1", "symptom_checkins", checkin["id"])
    ]


def test_pattern_changes_are_stored_for_the_doctor_but_never_returned(
    client: TestClient, engine: Engine
) -> None:
    """§9 / §14 test 8."""
    headers = patient(engine, client)
    first = post(client, headers, FATIGUE)
    assert first.status_code == 201 and "pattern_changes" not in first.json()["data"]
    pid = patient_id_of(engine, headers)
    sql = "SELECT pattern_changes FROM symptom_checkins WHERE patient_id = :p"
    (stored,) = rows(engine, sql, pid)
    assert stored["pattern_changes"] == [{"code": "P1", "symptom": "fatigue"}]
    inbox = rows(engine, "SELECT type FROM inbox_items WHERE patient_id = :p", pid)
    assert [i["type"] for i in inbox] == ["pattern_p1"]
    history = client.get(f"{URL}/checkins", headers=headers).json()["data"]
    assert len(history) == 1 and "pattern_changes" not in history[0]
    assert "pattern_changes" not in str(client.get(f"{URL}/charts", headers=headers).json())
    # P5: a second L2 check-in within the window
    for _ in range(2):
        res = post(client, headers, {"symptom": "severe_itching"})
        assert res.json()["data"]["red_flag_level"] == "L2"
    types = [i["type"] for i in rows(engine, "SELECT type FROM inbox_items WHERE patient_id = :p "
                                     "ORDER BY created_at", pid)]  # fmt: skip
    assert types.count("symptom_l2") == 2 and types.count("pattern_p5") == 1


def count(engine: Engine, pid: uuid.UUID) -> int:
    with engine.connect() as conn:
        n: int = conn.execute(
            text("SELECT count(*) FROM symptom_checkins WHERE patient_id = :p"), {"p": pid}
        ).scalar_one()
    return n


@pytest.mark.parametrize(
    ("entries", "source", "field", "code"),
    [
        ([], "form", "entries", "V1"),
        ([{"symptom": "headache", "severity": "mild"}], "form", "entries.0.duration", "V1"),
        ([{"symptom": "dizziness"}], "form", "entries.0.symptom", "V2"),
        ([{"symptom": "fatigue", "severity": "mild", "duration": "under_1_hour"}], "urgent_button",
         "entries.0.symptom", "V2"),
        ([{"symptom": "fits", "severity": "severe"}], "form", "entries.0.severity", "V2"),
    ],
)  # fmt: skip
def test_v1_v2_save_nothing(
    client: TestClient,
    engine: Engine,
    entries: list[dict[str, Any]],
    source: str,
    field: str,
    code: str,
) -> None:
    headers = patient(engine, client)
    res = post(client, headers, *entries, source=source)
    assert res.status_code == 400 and res.json()["error"]["fields"] == {field: code}
    assert count(engine, patient_id_of(engine, headers)) == 0


def test_unknown_fields_are_refused(client: TestClient, engine: Engine) -> None:
    headers = patient(engine, client)
    res = post(client, headers, {"symptom": "fits", "risk": "high"})
    assert res.status_code == 400
    assert count(engine, patient_id_of(engine, headers)) == 0


def test_v3_engine_failure_saves_l2_with_err(
    client: TestClient, engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(*_: Any) -> Any:
        raise RuntimeError("test engine failure")

    monkeypatch.setattr(symptom_engine, "assess", broken)
    headers = patient(engine, client)
    res = post(client, headers, FATIGUE)
    assert res.status_code == 201
    data = res.json()["data"]
    assert (data["red_flag_level"], data["matched_rules"], data["message_keys"]) == (
        "L2",
        ["ERR"],
        ["msg_safe_fallback"],
    )
    pid = patient_id_of(engine, headers)
    assert count(engine, pid) == 1
    assert [i["type"] for i in rows(engine, "SELECT type FROM inbox_items WHERE patient_id = :p",
                                    pid)] == ["symptom_l2"]  # fmt: skip


def test_details_notes_history_and_charts(client: TestClient, engine: Engine) -> None:
    headers = patient(engine, client, weeks=None)
    res = post(
        client,
        headers,
        {"symptom": "nausea_vomiting", "puqe_answers": [5, 4, 4], "notes": "Test bleeding words"},
        {"symptom": "other", "name": "Test thing", "severity": "mild", "duration": "under_1_hour"},
    )
    data = res.json()["data"]
    assert data["red_flag_level"] == "L2" and data["matched_rules"] == ["L2-05"]
    assert data["pregnancy_week"] is None  # no due date
    assert data["message_keys"] == ["msg_level2_contact_today", "msg_notes_not_read"]
    (checkin,) = client.get(f"{URL}/checkins", headers=headers).json()["data"]
    nausea, other = checkin["entries"]
    assert nausea["details"] == {"puqe_answers": [5, 4, 4], "puqe_score": 13, "puqe_band": "severe"}
    assert nausea["notes"] == "Test bleeding words" and other["details"] == {"name": "Test thing"}
    charts = client.get(f"{URL}/charts", headers=headers).json()["data"]
    assert [p["score"] for p in charts["puqe"]] == [13]
    assert {s["symptom"] for s in charts["symptoms"]} == {"nausea_vomiting", "other"}


def test_logging_closes_after_the_pregnancy_ends(client: TestClient, engine: Engine) -> None:
    """DEC-064: postpartum is out of scope."""
    headers = patient(engine, client)
    client.post(
        "/api/v1/patient/pregnancy-end",
        json={"status": "ended_birth", "inform_doctor": False},
        headers=headers,
    )
    assert client.get(f"{URL}/vocabulary", headers=headers).json()["data"]["logging_open"] is False
    assert post(client, headers, {"symptom": "fits"}).status_code == 409


def test_routes_need_a_linked_patient_with_consent(client: TestClient, engine: Engine) -> None:
    user_id, _ = add_linked_patient(engine, consent=False)
    headers = bearer(sub=str(user_id))
    for path in ("/vocabulary", "/checkins", "/charts"):
        assert client.get(f"{URL}{path}", headers=headers).status_code == 403
    assert post(client, headers, {"symptom": "fits"}).status_code == 403
