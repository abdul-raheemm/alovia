"""GET /me and POST /me/consent (API.md §4.1, SECURITY.md §1, DEC-023, DEC-031, DEC-036).

Runs against the alovia-test database (see tests/conftest.py).
"""

import uuid
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from app.core.config import CONSENT_VERSION
from tests.helpers import bearer, make_app


@pytest.fixture(scope="module")
def client(test_db_url: str, engine: Engine) -> Iterator[TestClient]:
    app: FastAPI = make_app(database_url=test_db_url)
    yield TestClient(app)
    app.state.engine.dispose()


def add_user(engine: Engine, role: str, active: bool = True) -> uuid.UUID:
    uid = uuid.uuid4()
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO users (id, email, role, is_active) VALUES (:id, :e, :r, :a)"),
            {"id": uid, "e": f"{uid}@example.test", "r": role, "a": active},
        )
    return uid


def add_row(engine: Engine, sql: str, **params: Any) -> uuid.UUID:
    with engine.begin() as conn:
        new_id: uuid.UUID = conn.execute(text(sql), params).scalar_one()
    return new_id


def me(client: TestClient, uid: uuid.UUID) -> Any:
    return client.get("/api/v1/me", headers=bearer(sub=str(uid)))


def consent(client: TestClient, uid: uuid.UUID, **body: Any) -> Any:
    payload = {"consent_version": CONSENT_VERSION, "age_confirmed_18_plus": True, **body}
    return client.post("/api/v1/me/consent", json=payload, headers=bearer(sub=str(uid)))


def test_no_token_is_401(client: TestClient) -> None:
    assert client.get("/api/v1/me").status_code == 401


def test_signed_in_without_account_is_403(client: TestClient) -> None:
    res = me(client, uuid.uuid4())
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"


def test_token_subject_not_a_uuid_is_401(client: TestClient) -> None:
    res = client.get("/api/v1/me", headers=bearer(sub="not-a-uuid"))
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "AUTH_REQUIRED"


def test_deactivated_account_is_403(client: TestClient, engine: Engine) -> None:
    assert me(client, add_user(engine, "doctor", active=False)).status_code == 403


def test_patient_sees_own_record_without_doctor_notes(client: TestClient, engine: Engine) -> None:
    uid = add_user(engine, "patient")
    pid = add_row(
        engine,
        "INSERT INTO patients (user_id, name, notes) VALUES (:u, 'Test Patient 1', "
        "'doctor-private note') RETURNING id",
        u=uid,
    )
    res = me(client, uid)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["user"] == {"id": str(uid), "email": f"{uid}@example.test", "role": "patient"}
    assert data["patient"] == {"id": str(pid), "name": "Test Patient 1"}
    assert data["doctor"] is None
    assert data["consent"] == {"current_version": CONSENT_VERSION, "accepted": False}
    assert "doctor-private note" not in res.text


def test_doctor_and_admin(client: TestClient, engine: Engine) -> None:
    doc_uid = add_user(engine, "doctor")
    did = add_row(
        engine,
        "INSERT INTO doctors (user_id, name, specialty) VALUES (:u, 'Test Doctor', 'OBGYN') "
        "RETURNING id",
        u=doc_uid,
    )
    doc = me(client, doc_uid).json()["data"]
    assert doc["doctor"] == {"id": str(did), "name": "Test Doctor", "specialty": "OBGYN"}
    assert doc["patient"] is None
    admin = me(client, add_user(engine, "admin")).json()["data"]
    assert (admin["user"]["role"], admin["patient"], admin["doctor"]) == ("admin", None, None)


@pytest.mark.parametrize(
    ("body", "field"),
    [
        ({"consent_version": "2020-01-v0"}, "consent_version"),
        ({"age_confirmed_18_plus": False}, "age_confirmed_18_plus"),
        ({"age_confirmed_18_plus": "true"}, "age_confirmed_18_plus"),  # strict boolean
        ({"extra": 1}, "extra"),
    ],
    ids=["old-version", "under-18", "string-bool", "unknown-field"],
)
def test_consent_rejected(client: TestClient, engine: Engine, body: Any, field: str) -> None:
    uid = add_user(engine, "patient")
    res = consent(client, uid, **body)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"
    assert field in res.json()["error"]["fields"]
    assert me(client, uid).json()["data"]["consent"]["accepted"] is False


def test_consent_recorded_once(client: TestClient, engine: Engine) -> None:
    uid = add_user(engine, "patient")
    for _ in range(2):
        res = consent(client, uid)
        assert res.status_code == 200
        assert res.json()["data"] == {"current_version": CONSENT_VERSION, "accepted": True}
    assert me(client, uid).json()["data"]["consent"]["accepted"] is True
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT consent_version, age_confirmed_18_plus FROM consents WHERE user_id = :u"),
            {"u": uid},
        ).all()
    assert [tuple(r) for r in rows] == [(CONSENT_VERSION, True)]
