"""Backend access checks for doctor and admin routes (Dashboard spec §1.3, §4, §25 tests 1-2).
A test-only router uses the real dependencies; the route-by-route matrix comes with the routes.
Runs against alovia-test."""

import uuid
from collections.abc import Iterator
from typing import Annotated

import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from app.modules.users.models import Patient, User
from app.modules.users.service import (
    DoctorAccount,
    get_admin,
    get_assigned_patient,
    get_doctor,
)
from tests.helpers import add_account, add_doctor, add_linked_patient, assign, bearer, make_app

probe = APIRouter(prefix="/probe")


@probe.get("/doctor")
def doctor_only(account: Annotated[DoctorAccount, Depends(get_doctor)]) -> dict[str, str]:
    return {"doctor": str(account.doctor.id)}


@probe.get("/patients/{patient_id}")
def assigned_only(patient: Annotated[Patient, Depends(get_assigned_patient)]) -> dict[str, str]:
    return {"patient": str(patient.id)}


@probe.get("/admin")
def admin_only(user: Annotated[User, Depends(get_admin)]) -> dict[str, str]:
    return {"admin": str(user.id)}


@pytest.fixture(scope="module")
def client(test_db_url: str, engine: Engine) -> Iterator[TestClient]:
    app: FastAPI = make_app(database_url=test_db_url)
    app.include_router(probe)
    yield TestClient(app)
    app.state.engine.dispose()


def h(user_id: uuid.UUID) -> dict[str, str]:
    return bearer(sub=str(user_id))


def test_doctor_routes_need_an_active_doctor_with_consent(
    client: TestClient, engine: Engine
) -> None:
    ok_user, doctor_id = add_doctor(engine)
    res = client.get("/probe/doctor", headers=h(ok_user))
    assert res.status_code == 200 and res.json() == {"doctor": str(doctor_id)}
    no_consent, _ = add_doctor(engine, consent=False)
    inactive, _ = add_doctor(engine, active=False)
    patient_user, _ = add_linked_patient(engine)
    admin = add_account(engine, "admin")
    for user in (no_consent, inactive, patient_user, admin):
        assert client.get("/probe/doctor", headers=h(user)).status_code == 403


def test_patient_data_needs_an_active_assignment(client: TestClient, engine: Engine) -> None:
    user, doctor_id = add_doctor(engine)
    _, mine = add_linked_patient(engine)
    _, other = add_linked_patient(engine)
    _, removed = add_linked_patient(engine)
    assign(engine, doctor_id, mine, primary=True)
    assign(engine, doctor_id, removed, removed=True)
    assert client.get(f"/probe/patients/{mine}", headers=h(user)).json() == {"patient": str(mine)}
    for pid in (other, removed, uuid.uuid4()):  # not assigned, removed, unknown: all the same
        res = client.get(f"/probe/patients/{pid}", headers=h(user))
        assert res.status_code == 404 and res.json()["error"]["code"] == "NOT_FOUND"


def test_admin_routes_reject_doctors_and_patients(client: TestClient, engine: Engine) -> None:
    admin = add_account(engine, "admin")
    assert client.get("/probe/admin", headers=h(admin)).status_code == 200
    doctor, _ = add_doctor(engine)
    patient, _ = add_linked_patient(engine)
    no_consent = add_account(engine, "admin", consent=False)
    for user in (doctor, patient, no_consent):
        assert client.get("/probe/admin", headers=h(user)).status_code == 403
