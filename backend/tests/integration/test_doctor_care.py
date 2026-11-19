"""Doctor sides of other modules (Dashboard spec §8.3, §12, §13, §15-17; Genetic §10;
§25 tests 1, 10, 11; Genetic §14 test 10). Runs against alovia-test."""

import uuid
from collections.abc import Iterator
from datetime import date, timedelta
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from tests.helpers import add_doctor, add_linked_patient, assign, bearer, make_app

API = "/api/v1/doctor"
TODAY = date.today()


@pytest.fixture(scope="module")
def client(test_db_url: str, engine: Engine) -> Iterator[TestClient]:
    app: FastAPI = make_app(database_url=test_db_url)
    yield TestClient(app)
    app.state.engine.dispose()


def setup(engine: Engine) -> tuple[dict[str, str], dict[str, str], uuid.UUID, uuid.UUID]:
    """(doctor headers, patient headers, patient id, doctor id), assigned and linked."""
    doctor_user, doctor_id = add_doctor(engine)
    patient_user, patient_id = add_linked_patient(engine)
    assign(engine, doctor_id, patient_id, primary=True)
    return bearer(sub=str(doctor_user)), bearer(sub=str(patient_user)), patient_id, doctor_id


def second_doctor(engine: Engine, patient_id: uuid.UUID) -> dict[str, str]:
    user, doctor_id = add_doctor(engine)
    assign(engine, doctor_id, patient_id)
    return bearer(sub=str(user))


def stranger(engine: Engine) -> dict[str, str]:
    return bearer(sub=str(add_doctor(engine)[0]))


def genetic_body(mother: str = "beta_thal_carrier", father: str = "beta_thal_carrier") -> Any:
    def p(status: str) -> dict[str, str]:
        return (
            {"status": status}
            if status == "unknown"
            else {"status": status, "evidence": "hplc_report"}
        )

    return {
        "haemoglobin_group": {"mother": p(mother), "father": p(father), "previous_child": "no"},
        "haemophilia": {"entry": "no"},
        "marfan": {"entry": "no"},
        "consanguinity": "no",
    }


def submit(client: TestClient, ph: dict[str, str], **kw: str) -> str:
    res = client.post("/api/v1/patient/genetic/assessments", json=genetic_body(**kw), headers=ph)
    assert res.status_code == 201
    found: str = res.json()["data"]["assessment_id"]
    return found


def notification_types(client: TestClient, ph: dict[str, str]) -> list[str]:
    return [
        n["type"] for n in client.get("/api/v1/patient/notifications", headers=ph).json()["data"]
    ]


# ---- genetic review (Genetic §10, Dashboard §12) ----


def test_queue_confirm_and_second_doctor_is_rejected(client: TestClient, engine: Engine) -> None:
    h, ph, pid, _ = setup(engine)
    low = submit(client, ph, mother="tested_negative", father="tested_negative")
    high = submit(client, ph)  # both carriers: risk indicated, high priority
    queue = [a["id"] for a in client.get(f"{API}/genetic/review-queue", headers=h).json()["data"]]
    assert queue == [high, low]  # high priority first, then oldest

    url = f"{API}/genetic/assessments/{high}/review"
    assert client.post(url, json={"doctor_note": "  "}, headers=h).status_code == 400
    res = client.post(url, json={"doctor_note": "Test review note"}, headers=h)
    assert res.status_code == 200
    out = res.json()["data"]
    assert out["review_status"] == "reviewed" and out["reviewed_by_name"] == "Test Doctor"

    other = second_doctor(engine, pid)
    again = client.post(url, json={"doctor_note": "Second"}, headers=other)
    assert again.status_code == 409
    assert again.json()["error"]["message"] == "Already reviewed by Test Doctor."
    fix = client.post(
        f"{API}/genetic/assessments/{high}/correct",
        json={"inputs": genetic_body(), "doctor_note": "x"},
        headers=other,
    )
    assert fix.status_code == 409
    assert [
        a["id"] for a in client.get(f"{API}/genetic/review-queue", headers=h).json()["data"]
    ] == [low]

    mine = client.get(f"/api/v1/patient/genetic/assessments/{high}", headers=ph).json()["data"]
    assert mine["doctor_note"] == "Test review note"
    notes = client.get("/api/v1/patient/doctor-notes", headers=ph).json()["data"]
    assert notes[0]["related_ref"] == f"genetic_assessment:{high}"
    types = notification_types(client, ph)
    assert types.count("genetic_reviewed") == 1 and "doctor_note" not in types


def test_correction_creates_a_new_row_and_leaves_the_old(
    client: TestClient, engine: Engine
) -> None:
    """Genetic §14 test 10."""
    h, ph, pid, _ = setup(engine)
    old = submit(client, ph)
    with engine.connect() as conn:
        before = conn.execute(
            text("SELECT inputs, results, review_status FROM genetic_assessments WHERE id = :i"),
            {"i": old},
        ).one()
    res = client.post(
        f"{API}/genetic/assessments/{old}/correct",
        json={
            "inputs": genetic_body(father="tested_negative"),
            "doctor_note": "Father was tested",
        },
        headers=h,
    )
    assert res.status_code == 201
    new = res.json()["data"]
    assert new["supersedes_id"] == old and new["review_status"] == "reviewed"
    assert (
        new["by_doctor"] is True
        and new["inputs"]["haemoglobin_group"]["father"]["status"] == "tested_negative"
    )
    with engine.connect() as conn:
        after = conn.execute(
            text("SELECT inputs, results, review_status FROM genetic_assessments WHERE id = :i"),
            {"i": old},
        ).one()
    assert tuple(after) == tuple(before)  # the old row is never edited
    rows = client.get(f"{API}/patients/{pid}/genetic", headers=h).json()["data"]
    assert [(r["id"], r["replaced"]) for r in rows] == [(new["id"], False), (old, True)]
    assert client.get(f"{API}/genetic/review-queue", headers=h).json()["data"] == []
    bad = client.post(
        f"{API}/genetic/assessments/{new['id']}/correct",
        json={"inputs": genetic_body(), "doctor_note": "x"},
        headers=h,
    )
    assert bad.status_code == 409  # already reviewed


def test_genetic_routes_hide_other_doctors_patients(client: TestClient, engine: Engine) -> None:
    _, ph, pid, _ = setup(engine)
    aid = submit(client, ph)
    s = stranger(engine)
    assert client.get(f"{API}/genetic/review-queue", headers=s).json()["data"] == []
    assert client.get(f"{API}/patients/{pid}/genetic", headers=s).status_code == 404
    res = client.post(
        f"{API}/genetic/assessments/{aid}/review", json={"doctor_note": "x"}, headers=s
    )
    assert res.status_code == 404


# ---- symptoms view (Symptom §12) ----


def test_symptom_view_shows_rules_patterns_and_labels(client: TestClient, engine: Engine) -> None:
    h, ph, pid, _ = setup(engine)
    res = client.post(
        "/api/v1/patient/symptoms/checkins",
        json={"source": "form", "entries": [{"symptom": "fits"}]},
        headers=ph,
    )
    assert res.status_code == 201
    data = client.get(f"{API}/patients/{pid}/symptoms", headers=h).json()["data"]
    first = data["checkins"][0]
    assert first["red_flag_level"] == "L1" and first["matched_rules"]
    assert "pattern_changes" in first and data["labels"]["fits"]
    assert [b["band"] for b in data["puqe_bands"]] == ["mild", "moderate", "severe"]
    assert client.get(f"{API}/patients/{pid}/symptoms", headers=stranger(engine)).status_code == 404


# ---- notes (§15) ----


def test_private_note_is_hidden_until_shared(client: TestClient, engine: Engine) -> None:
    h, ph, pid, _ = setup(engine)
    url = f"{API}/patients/{pid}/notes"
    assert (
        client.post(url, json={"body": " ", "visible_to_patient": True}, headers=h).status_code
        == 400
    )
    private = client.post(
        url, json={"body": "Private test", "visible_to_patient": False}, headers=h
    )
    assert private.status_code == 201
    nid = private.json()["data"]["id"]
    client.post(url, json={"body": "Shared test", "visible_to_patient": True}, headers=h)
    assert [
        n["body"] for n in client.get("/api/v1/patient/doctor-notes", headers=ph).json()["data"]
    ] == ["Shared test"]
    assert len(client.get(url, headers=h).json()["data"]) == 2
    assert client.post(f"{API}/notes/{nid}/share", headers=stranger(engine)).status_code == 404
    assert client.post(f"{API}/notes/{nid}/share", headers=h).json()["data"]["visible_to_patient"]
    assert client.post(f"{API}/notes/{nid}/share", headers=h).status_code == 409
    assert len(client.get("/api/v1/patient/doctor-notes", headers=ph).json()["data"]) == 2


# ---- appointments (§16, §25 test 11) ----


def test_each_side_edits_only_its_own_appointments(client: TestClient, engine: Engine) -> None:
    h, ph, pid, _ = setup(engine)
    day = (TODAY + timedelta(days=5)).isoformat()
    doc = client.post(
        f"{API}/patients/{pid}/appointments", json={"date": day, "title": "Doctor visit"}, headers=h
    ).json()["data"]
    mine = client.post(
        "/api/v1/patient/appointments", json={"date": day, "title": "My visit"}, headers=ph
    ).json()["data"]
    assert doc["source"] == "doctor" and doc["can_edit"] is True
    seen = client.get("/api/v1/patient/appointments", headers=ph).json()["data"]["upcoming"]
    assert {(a["title"], a["can_edit"]) for a in seen} == {
        ("Doctor visit", False),
        ("My visit", True),
    }

    body = {"date": day, "title": "Changed"}
    assert client.put(f"{API}/appointments/{mine['id']}", json=body, headers=h).status_code == 403
    assert client.delete(f"{API}/appointments/{mine['id']}", headers=h).status_code == 403
    assert (
        client.put(f"/api/v1/patient/appointments/{doc['id']}", json=body, headers=ph).status_code
        == 403
    )
    assert (
        client.put(f"{API}/appointments/{doc['id']}", json=body, headers=h).json()["data"]["title"]
        == "Changed"
    )
    other = second_doctor(engine, pid)  # equal permissions (D1)
    assert client.delete(f"{API}/appointments/{doc['id']}", headers=other).status_code == 200
    assert (
        client.delete(f"{API}/appointments/{mine['id']}", headers=stranger(engine)).status_code
        == 404
    )


# ---- dates and status (§8.3, §17) ----


def test_doctor_dates_follow_d2_and_notify(client: TestClient, engine: Engine) -> None:
    h, ph, pid, _ = setup(engine)
    url = f"{API}/patients/{pid}/dates"
    far = (TODAY + timedelta(days=400)).isoformat()  # GA below 0 days: rule D2
    res = client.put(url, json={"option": "due_date", "due_date": far}, headers=h)
    assert res.status_code == 400 and "due_date" in res.json()["error"]["fields"]
    assert (
        client.put(
            url, json={"option": "lmp", "lmp_date": TODAY.isoformat()}, headers=h
        ).status_code
        == 400
    )
    due = (TODAY + timedelta(days=100)).isoformat()
    out = client.put(url, json={"option": "due_date", "due_date": due}, headers=h).json()["data"]
    assert (out["due_date"], out["due_date_source"]) == (due, "clinician_confirmed")
    assert notification_types(client, ph).count("dates_updated") == 1
    # her own change does not notify her
    client.put(
        "/api/v1/patient/journey/dates",
        json={"option": "due_date", "due_date": (TODAY + timedelta(days=90)).isoformat()},
        headers=ph,
    )
    assert notification_types(client, ph).count("dates_updated") == 1


def test_doctor_sets_pregnancy_ended_without_inbox_item(client: TestClient, engine: Engine) -> None:
    h, _, pid, _ = setup(engine)
    url = f"{API}/patients/{pid}/pregnancy-end"
    assert client.post(url, json={"status": "ended", "x": 1}, headers=h).status_code == 400
    out = client.post(url, json={"status": "ended_loss"}, headers=h).json()["data"]
    assert out["pregnancy_status"] == "ended_loss"
    assert client.post(url, json={"status": "ended_birth"}, headers=h).status_code == 409
    with engine.connect() as conn:
        n = conn.execute(
            text("SELECT count(*) FROM inbox_items WHERE patient_id = :p"), {"p": pid}
        ).scalar_one()
    assert n == 0
    assert (
        client.post(url, json={"status": "ended_loss"}, headers=stranger(engine)).status_code == 404
    )
