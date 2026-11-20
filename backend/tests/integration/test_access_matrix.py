"""Access control on EVERY doctor and admin route (Dashboard spec §1.3, §4, §25 tests 1-2).

The route list is read from the app itself; the guard test fails when a new /doctor or /admin
route is not listed here, so no route can ship untested. For each route:
  - a patient and an admin get 403 on doctor routes; a doctor and a patient get 403 on admin
    routes (§25 test 2: admins never reach clinical data);
  - a doctor who is not assigned gets 404 for another doctor's patient and that patient's
    records, notes, results, assessments, appointments and inbox items (§25 test 1).
Runs against alovia-test."""

import json
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from tests.helpers import add_account, add_doctor, add_linked_patient, assign, bearer, make_app
from tests.integration.test_doctor_records import PDF, FakeStorage

FETAL = json.loads(
    (
        __import__("pathlib").Path(__file__).resolve().parents[1]
        / "fixtures/ml_reference_outputs.json"
    ).read_text("utf-8")
)["cases"][0]["input"]


@dataclass(frozen=True)
class World:
    owner: dict[str, str]  # the assigned doctor
    stranger: dict[str, str]  # a doctor with no assignment to the patient
    patient: dict[str, str]
    admin: dict[str, str]
    ids: dict[str, str]


@pytest.fixture(scope="module")
def app(test_db_url: str, engine: Engine) -> Iterator[FastAPI]:
    application: FastAPI = make_app(database_url=test_db_url)
    application.state.storage = FakeStorage()
    yield application
    application.state.engine.dispose()


@pytest.fixture(scope="module")
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="module")
def world(client: TestClient, engine: Engine) -> World:
    owner_user, owner_id = add_doctor(engine)
    stranger_user, _ = add_doctor(engine)
    patient_user, pid = add_linked_patient(engine)
    assign(engine, owner_id, pid, primary=True)
    owner, patient = bearer(sub=str(owner_user)), bearer(sub=str(patient_user))
    api = "/api/v1/doctor"
    result = client.post(
        f"{api}/patients/{pid}/predictions/fetal", json={"values": FETAL}, headers=owner
    )
    genetic = client.post(
        "/api/v1/patient/genetic/assessments",
        json={
            "haemoglobin_group": {
                "mother": {"status": "unknown"},
                "father": {"status": "unknown"},
                "previous_child": "no",
            },
            "haemophilia": {"entry": "no"},
            "marfan": {"entry": "no"},
            "consanguinity": "no",
        },
        headers=patient,
    )
    note = client.post(
        f"{api}/patients/{pid}/notes",
        json={"body": "Private", "visible_to_patient": False},
        headers=owner,
    )
    appt = client.post(
        f"{api}/patients/{pid}/appointments",
        json={"date": "2030-01-01", "title": "Visit"},
        headers=owner,
    )
    record = client.post(
        f"{api}/patients/{pid}/records",
        files={"file": ("a.pdf", PDF, "application/pdf")},
        data={"file_type": "other"},
        headers=owner,
    )
    with engine.begin() as conn:
        item = conn.execute(
            text(
                "INSERT INTO inbox_items (patient_id, type, ref_table, ref_id) "
                "VALUES (:p, 'symptom_l2', 'symptom_checkins', :r) RETURNING id"
            ),
            {"p": pid, "r": uuid.uuid4()},
        ).scalar_one()
    for r in (result, genetic, note, appt, record):
        assert r.status_code == 201, r.text
    return World(
        owner=owner,
        stranger=bearer(sub=str(stranger_user)),
        patient=patient,
        admin=bearer(sub=str(add_account(engine, "admin"))),
        ids={
            "patient_id": str(pid),
            "result_id": result.json()["data"]["id"],
            "assessment_id": genetic.json()["data"]["assessment_id"],
            "note_id": note.json()["data"]["id"],
            "appointment_id": appt.json()["data"]["id"],
            "record_id": record.json()["data"]["id"],
            "item_id": str(item),
            "doctor_id": str(owner_id),
            "model": "fetal",
            "module": "genetic",
        },
    )


GENETIC_INPUT = {
    "haemoglobin_group": {
        "mother": {"status": "unknown"},
        "father": {"status": "unknown"},
        "previous_child": "no",
    },
    "haemophilia": {"entry": "no"},
    "marfan": {"entry": "no"},
    "consanguinity": "no",
}
# (method, path template) -> valid body, so a stranger is refused for access, not for input.
# None in BODIES means no body. Multipart uploads are handled separately.
BODIES: dict[tuple[str, str], Any] = {
    ("POST", "/api/v1/doctor/patients/{patient_id}/predictions/{model}"): {"values": FETAL},
    ("POST", "/api/v1/doctor/predictions/{model}/{result_id}/share"): {},
    ("POST", "/api/v1/doctor/genetic/assessments/{assessment_id}/review"): {"doctor_note": "x"},
    ("POST", "/api/v1/doctor/genetic/assessments/{assessment_id}/correct"): {
        "inputs": GENETIC_INPUT,
        "doctor_note": "x",
    },
    ("POST", "/api/v1/doctor/patients/{patient_id}/notes"): {
        "body": "x",
        "visible_to_patient": False,
    },
    ("POST", "/api/v1/doctor/patients/{patient_id}/appointments"): {
        "date": "2030-01-02",
        "title": "x",
    },
    ("PUT", "/api/v1/doctor/appointments/{appointment_id}"): {"date": "2030-01-02", "title": "x"},
    ("PUT", "/api/v1/doctor/patients/{patient_id}"): {"name": "x"},
    ("PUT", "/api/v1/doctor/patients/{patient_id}/dates"): {
        "option": "due_date",
        "due_date": "2030-01-01",
    },
    ("POST", "/api/v1/doctor/patients/{patient_id}/pregnancy-end"): {"status": "ended_birth"},
    ("POST", "/api/v1/doctor/patients"): {"name": "x"},
    ("POST", "/api/v1/doctor/rules/{module}/signoff"): {"key": "1:HBB-01", "checked": True},
    ("POST", "/api/v1/admin/doctors"): {"email": "x@y.zz", "name": "x"},
    ("PUT", "/api/v1/admin/doctors/{doctor_id}"): {"name": "x", "is_active": True},
    ("POST", "/api/v1/admin/assignments"): {
        "patient_id": str(uuid.uuid4()),
        "doctor_id": str(uuid.uuid4()),
    },
}
QUERY: dict[tuple[str, str], str] = {
    ("GET", "/api/v1/doctor/patients/{patient_id}/predictions"): "?model=fetal",
    ("DELETE", "/api/v1/admin/assignments"): f"?patient_id={uuid.uuid4()}&doctor_id={uuid.uuid4()}",
}
UPLOAD = ("POST", "/api/v1/doctor/patients/{patient_id}/records")
# doctor routes that touch one patient's data: an unassigned doctor must get 404
PATIENT_SCOPED_PARAMS = {
    "patient_id",
    "result_id",
    "assessment_id",
    "note_id",
    "appointment_id",
    "record_id",
    "item_id",
}


def routes(app: FastAPI) -> list[tuple[str, str]]:
    """Every doctor/admin (method, path), from the app's own OpenAPI document."""
    paths: dict[str, dict[str, Any]] = app.openapi()["paths"]
    return sorted(
        (method.upper(), path)
        for path, ops in paths.items()
        if path.startswith(("/api/v1/doctor", "/api/v1/admin"))
        for method in ops
    )


def call(client: TestClient, world: World, method: str, path: str, headers: dict[str, str]) -> int:
    url = path.format(**world.ids) + QUERY.get((method, path), "")
    if (method, path) == UPLOAD:
        res = client.post(
            url,
            files={"file": ("b.pdf", PDF, "application/pdf")},
            data={"file_type": "other"},
            headers=headers,
        )
    else:
        res = client.request(method, url, json=BODIES.get((method, path)), headers=headers)
    return res.status_code


def test_every_route_is_in_this_matrix(app: FastAPI) -> None:
    """Guard: a new doctor/admin route with a body must get a valid body here."""
    with_body = {(m, p) for m, p in routes(app) if m in ("POST", "PUT")}
    missing = with_body - set(BODIES) - {UPLOAD}
    no_body_ok = {
        ("POST", "/api/v1/doctor/patients/{patient_id}/invite"),
        ("POST", "/api/v1/doctor/inbox/{item_id}/seen"),
        ("POST", "/api/v1/doctor/notes/{note_id}/share"),
    }
    assert missing - no_body_ok == set()
    assert len(routes(app)) >= 40  # every Phase 5 route is collected


def test_wrong_roles_are_refused_everywhere(client: TestClient, app: FastAPI, world: World) -> None:
    """§25 test 2 (and the doctor side): 403 before any data is read."""
    failures = []
    for method, path in routes(app):
        wrong = (
            (world.patient, world.admin)
            if path.startswith("/api/v1/doctor")
            else (
                world.patient,
                world.owner,
            )
        )
        for h in wrong:
            code = call(client, world, method, path, h)
            if code != 403:
                failures.append((method, path, code))
    assert failures == []


def test_unassigned_doctor_gets_404_on_every_patient_route(
    client: TestClient, app: FastAPI, world: World
) -> None:
    """§25 test 1: every route that touches the patient's data, with real ids."""
    failures = []
    checked = 0
    for method, path in routes(app):
        if not path.startswith("/api/v1/doctor"):
            continue
        params = {p.strip("{}") for p in path.split("/") if p.startswith("{")}
        if not params & PATIENT_SCOPED_PARAMS:
            continue
        checked += 1
        code = call(client, world, method, path, world.stranger)
        if code != 404:
            failures.append((method, path, code))
    assert failures == [] and checked >= 25


def test_patient_wide_lists_hold_only_assigned_patients(client: TestClient, world: World) -> None:
    api = "/api/v1/doctor"
    pid = world.ids["patient_id"]
    s = world.stranger
    assert all(r["id"] != pid for r in client.get(f"{api}/patients", headers=s).json()["data"])
    assert all(i["patient_id"] != pid for i in client.get(f"{api}/inbox", headers=s).json()["data"])
    queue = client.get(f"{api}/genetic/review-queue", headers=s).json()["data"]
    assert all(a["patient_id"] != pid for a in queue)
