"""Invite check and patient link (dashboard spec §8.2 and §25 test 9, DEC-024, DEC-036).

Runs against the alovia-test database (see tests/conftest.py).
"""

import uuid
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from app.modules.users.invites import ALPHABET, INVALID, create_invite, invite_settings
from tests.helpers import bearer, make_app


@pytest.fixture(scope="module")
def client(test_db_url: str, engine: Engine) -> Iterator[TestClient]:
    app: FastAPI = make_app(database_url=test_db_url)
    yield TestClient(app)
    app.state.engine.dispose()


def new_patient_with_invite(engine: Engine) -> tuple[uuid.UUID, str]:
    """A doctor-created patient record plus a fresh invite code (as the seed and Phase 5 do)."""
    with Session(engine) as db:
        doctor_user = uuid.uuid4()
        db.execute(
            text("INSERT INTO users (id, email, role) VALUES (:id, :e, 'doctor')"),
            {"id": doctor_user, "e": f"{doctor_user}@example.test"},
        )
        patient_id: uuid.UUID = db.execute(
            text("INSERT INTO patients (name) VALUES ('Test Patient 2') RETURNING id")
        ).scalar_one()
        code = create_invite(db, patient_id, doctor_user)
        db.commit()
    return patient_id, code


def check(client: TestClient, code: str) -> bool:
    res = client.get(f"/api/v1/invites/{code}/check")
    assert res.status_code == 200
    valid: bool = res.json()["data"]["valid"]
    return valid


def link(client: TestClient, code: str, uid: uuid.UUID | None = None, **claims: Any) -> Any:
    uid = uid or uuid.uuid4()
    headers = bearer(sub=str(uid), email=claims.pop("email", f"{uid}@example.test"), **claims)
    return client.post("/api/v1/patient/link", json={"code": code}, headers=headers)


def test_code_format_follows_config() -> None:
    length, days = invite_settings()
    assert (length, days) == (8, 7)  # defaults from doctor_dashboard_module_spec.md §23
    assert not set("0O1IL") & set(ALPHABET)


def test_valid_invite_links_once(client: TestClient, engine: Engine) -> None:
    patient_id, code = new_patient_with_invite(engine)
    assert check(client, code) is True
    assert check(client, code.lower()) is True  # case does not matter

    uid = uuid.uuid4()
    res = link(client, code, uid)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["user"]["role"] == "patient"
    assert data["patient"]["id"] == str(patient_id)
    assert data["consent"]["accepted"] is False  # consent is recorded next, by the app

    assert check(client, code) is False  # used
    second = link(client, code)
    assert second.status_code == 404
    with engine.connect() as conn:
        actions = conn.execute(
            text("SELECT action FROM audit_log WHERE patient_id = :p ORDER BY created_at"),
            {"p": patient_id},
        ).scalars()
        assert list(actions) == ["invite created", "invite used"]


def test_wrong_used_and_expired_codes_fail_the_same_way(client: TestClient, engine: Engine) -> None:
    _, expired = new_patient_with_invite(engine)
    with engine.begin() as conn:  # make this one invite expire
        conn.execute(
            text(
                "UPDATE patient_invites SET expires_at = now() - interval '1 minute' "
                "WHERE code_hash = encode(sha256(convert_to(:c, 'UTF8')), 'hex')"
            ),
            {"c": expired},
        )
    _, used = new_patient_with_invite(engine)
    assert link(client, used).status_code == 200

    responses = [link(client, c) for c in ("WRONGCOD", expired, used)]
    assert [r.status_code for r in responses] == [404, 404, 404]
    assert {r.json()["error"]["message"] for r in responses} == {INVALID}
    assert [check(client, c) for c in ("WRONGCOD", expired, used)] == [False, False, False]


def test_failed_link_saves_nothing(client: TestClient, engine: Engine) -> None:
    uid = uuid.uuid4()
    assert link(client, "WRONGCOD", uid).status_code == 404
    with engine.connect() as conn:
        assert (
            conn.execute(text("SELECT count(*) FROM users WHERE id = :u"), {"u": uid}).scalar() == 0
        )


def test_existing_account_cannot_link_again(client: TestClient, engine: Engine) -> None:
    _, first = new_patient_with_invite(engine)
    _, second = new_patient_with_invite(engine)
    uid = uuid.uuid4()
    assert link(client, first, uid).status_code == 200
    res = link(client, second, uid)
    assert res.status_code == 409
    assert check(client, second) is True  # the second invite was not used up


def test_email_already_used_is_409(client: TestClient, engine: Engine) -> None:
    _, first = new_patient_with_invite(engine)
    _, second = new_patient_with_invite(engine)
    assert link(client, first, email="same.person@example.test").status_code == 200
    res = link(client, second, email="same.person@example.test")
    assert res.status_code == 409
    assert check(client, second) is True


def test_token_without_email_is_400(client: TestClient, engine: Engine) -> None:
    _, code = new_patient_with_invite(engine)
    res = link(client, code, email=None)
    assert res.status_code == 400
    assert check(client, code) is True


def test_link_needs_a_token(client: TestClient, engine: Engine) -> None:
    _, code = new_patient_with_invite(engine)
    assert client.post("/api/v1/patient/link", json={"code": code}).status_code == 401


def test_link_with_non_uuid_subject_is_401(client: TestClient, engine: Engine) -> None:
    _, code = new_patient_with_invite(engine)
    headers = bearer(sub="not-a-uuid")
    res = client.post("/api/v1/patient/link", json={"code": code}, headers=headers)
    assert res.status_code == 401


@pytest.mark.parametrize(
    "content",
    [
        "invite_code_length: 3\ninvite_code_days: 7\n",
        "invite_code_length: '8'\ninvite_code_days: 7\n",
    ],
)
def test_bad_invite_config_is_refused(
    content: str, tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.modules.users import invites

    bad = tmp_path / "config.yaml"
    bad.write_text(content, encoding="utf-8")
    monkeypatch.setattr(invites, "CONFIG_FILE", bad)
    invites.invite_settings.cache_clear()
    try:
        with pytest.raises(ValueError):
            invites.invite_settings()
    finally:
        invites.invite_settings.cache_clear()
