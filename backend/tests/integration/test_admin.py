"""Admin (Dashboard spec §21, §25 tests 2 and 14) and the activity log (§20). A fake stands in
for the Supabase Auth invite API. Runs against alovia-test."""

import uuid
from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from app.core.errors import AppError
from tests.helpers import add_account, add_doctor, add_linked_patient, assign, bearer, make_app

API = "/api/v1/admin"


class FakeAuthAdmin:
    def __init__(self) -> None:
        self.invited: list[tuple[str, str]] = []
        self.exists: set[str] = set()

    def invite(self, email: str, redirect_to: str) -> str:
        if email in self.exists:
            raise AppError("CONFLICT", "An account with this email already exists.", status=409)
        self.invited.append((email, redirect_to))
        return str(uuid.uuid4())


@pytest.fixture(scope="module")
def app(test_db_url: str, engine: Engine) -> Iterator[FastAPI]:
    application: FastAPI = make_app(
        database_url=test_db_url, doctor_app_url="https://doctor.example.test"
    )
    application.state.auth_admin = FakeAuthAdmin()
    yield application
    application.state.engine.dispose()


@pytest.fixture(scope="module")
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


def admin(engine: Engine) -> dict[str, str]:
    return bearer(sub=str(add_account(engine, "admin")))


def test_invite_creates_the_doctor_and_sends_to_set_password(
    client: TestClient, app: FastAPI, engine: Engine
) -> None:
    h = admin(engine)
    email = f"{uuid.uuid4().hex[:8]}@doctor.example.test"
    res = client.post(
        f"{API}/doctors",
        json={"email": f" {email.upper()} ", "name": "Dr Test", "specialty": "OBG"},
        headers=h,
    )
    assert res.status_code == 201
    out = res.json()["data"]
    assert (out["email"], out["name"], out["is_active"], out["patient_count"]) == (
        email,
        "Dr Test",
        True,
        0,
    )
    assert app.state.auth_admin.invited[-1] == (email, "https://doctor.example.test/set-password")
    assert any(d["email"] == email for d in client.get(f"{API}/doctors", headers=h).json()["data"])
    assert (
        client.post(f"{API}/doctors", json={"email": email, "name": "Again"}, headers=h).status_code
        == 409
    )
    taken = f"{uuid.uuid4().hex[:8]}@doctor.example.test"
    app.state.auth_admin.exists.add(taken)
    assert (
        client.post(f"{API}/doctors", json={"email": taken, "name": "X"}, headers=h).status_code
        == 409
    )
    assert (
        client.post(
            f"{API}/doctors", json={"email": "not-an-email", "name": "X"}, headers=h
        ).status_code
        == 400
    )


def test_deactivated_doctor_loses_access_until_reactivated(
    client: TestClient, engine: Engine
) -> None:
    h = admin(engine)
    user, doctor_id = add_doctor(engine)
    dh = bearer(sub=str(user))
    assert client.get("/api/v1/doctor/patients", headers=dh).status_code == 200
    body = {"name": "Test Doctor", "specialty": None, "is_active": False}
    assert (
        client.put(f"{API}/doctors/{doctor_id}", json=body, headers=h).json()["data"]["is_active"]
        is False
    )
    assert client.get("/api/v1/doctor/patients", headers=dh).status_code == 403
    client.put(f"{API}/doctors/{doctor_id}", json={**body, "is_active": True}, headers=h)
    assert client.get("/api/v1/doctor/patients", headers=dh).status_code == 200
    assert client.put(f"{API}/doctors/{uuid.uuid4()}", json=body, headers=h).status_code == 404


def test_assign_set_primary_and_keep_one_doctor(client: TestClient, engine: Engine) -> None:
    """§21 / §25 test 14."""
    h = admin(engine)
    _, pid = add_linked_patient(engine)
    _, a = add_doctor(engine)
    _, b = add_doctor(engine)
    assign(engine, a, pid, primary=True)
    unique = f"Assign Test {uuid.uuid4().hex[:6]}"
    with engine.begin() as conn:
        conn.execute(text("UPDATE patients SET name = :n WHERE id = :p"), {"n": unique, "p": pid})
    found = client.get(f"{API}/assignments", params={"q": unique.lower()}, headers=h).json()["data"]
    assert [p["patient_id"] for p in found] == [str(pid)]

    url = f"{API}/assignments"
    out = client.post(url, json={"patient_id": str(pid), "doctor_id": str(b)}, headers=h).json()[
        "data"
    ]
    assert [(d["doctor_id"], d["is_primary"]) for d in out["doctors"]] == [
        (str(a), True),
        (str(b), False),
    ]
    assert (
        client.post(url, json={"patient_id": str(pid), "doctor_id": str(b)}, headers=h).status_code
        == 409
    )
    out = client.post(
        url, json={"patient_id": str(pid), "doctor_id": str(b), "is_primary": True}, headers=h
    ).json()["data"]
    assert [(d["doctor_id"], d["is_primary"]) for d in out["doctors"]] == [
        (str(b), True),
        (str(a), False),
    ]

    res = client.delete(url, params={"patient_id": str(pid), "doctor_id": str(b)}, headers=h)
    assert [d["doctor_id"] for d in res.json()["data"]["doctors"]] == [str(a)]
    last = client.delete(url, params={"patient_id": str(pid), "doctor_id": str(a)}, headers=h)
    assert last.status_code == 409 and "at least one" in last.json()["error"]["message"]
    assert (
        client.delete(
            url, params={"patient_id": str(pid), "doctor_id": str(b)}, headers=h
        ).status_code
        == 404
    )

    _, inactive = add_doctor(engine, active=False)
    res = client.post(url, json={"patient_id": str(pid), "doctor_id": str(inactive)}, headers=h)
    assert res.status_code == 409


def test_audit_log_views(client: TestClient, engine: Engine) -> None:
    """§20: admins see every entry, filtered; doctors see their patients' entries; nothing
    clinical in either."""
    h = admin(engine)
    duser, doctor_id = add_doctor(engine)
    dh = bearer(sub=str(duser))
    created = client.post(
        "/api/v1/doctor/patients", json={"name": "Audit Test"}, headers=dh
    ).json()["data"]
    entries = client.get(f"{API}/audit", params={"action": "patient created"}, headers=h).json()[
        "data"
    ]
    mine = next(e for e in entries if e["patient_id"] == created["id"])
    assert set(mine) == {
        "id",
        "created_at",
        "actor_email",
        "actor_role",
        "actor_name",
        "action",
        "entity_type",
        "entity_id",
        "patient_id",
        "patient_name",
    }
    assert (mine["actor_role"], mine["actor_name"], mine["patient_name"]) == (
        "doctor",
        "Test Doctor",
        "Audit Test",
    )
    by_actor = client.get(f"{API}/audit", params={"actor": str(duser)[:8]}, headers=h).json()[
        "data"
    ]
    assert by_actor and all(e["actor_email"].startswith(str(duser)[:8]) for e in by_actor)
    assert "patient created" in client.get(f"{API}/audit/actions", headers=h).json()["data"]

    own = client.get(f"/api/v1/doctor/patients/{created['id']}/audit", headers=dh).json()["data"]
    assert [e["action"] for e in own] == ["patient created"]
    stranger = bearer(sub=str(add_doctor(engine)[0]))
    assert (
        client.get(f"/api/v1/doctor/patients/{created['id']}/audit", headers=stranger).status_code
        == 404
    )


def test_admin_routes_reject_doctors_and_patients(client: TestClient, engine: Engine) -> None:
    """§25 test 2 for every admin route."""
    doctor = bearer(sub=str(add_doctor(engine)[0]))
    patient = bearer(sub=str(add_linked_patient(engine)[0]))
    pid, did = str(uuid.uuid4()), str(uuid.uuid4())
    calls = [
        ("GET", f"{API}/doctors", None),
        ("POST", f"{API}/doctors", {"email": "x@y.zz", "name": "X"}),
        ("PUT", f"{API}/doctors/{did}", {"name": "X", "is_active": True}),
        ("GET", f"{API}/assignments", None),
        ("POST", f"{API}/assignments", {"patient_id": pid, "doctor_id": did}),
        ("DELETE", f"{API}/assignments?patient_id={pid}&doctor_id={did}", None),
        ("GET", f"{API}/audit", None),
        ("GET", f"{API}/audit/actions", None),
    ]
    for h in (doctor, patient):
        for method, url, body in calls:
            assert client.request(method, url, json=body, headers=h).status_code == 403, url
