"""Doctor home: patient list order, patient records, invite links, inbox and "seen"
(Dashboard spec §5.1, §6, §7, §8.1-8.2; §25 tests 1, 3, 4, 9). Runs against alovia-test."""

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from tests.helpers import add_doctor, add_linked_patient, assign, bearer, make_app

API = "/api/v1/doctor"
APP_URL = "https://patient.example.test"


@pytest.fixture(scope="module")
def client(test_db_url: str, engine: Engine) -> Iterator[TestClient]:
    app: FastAPI = make_app(database_url=test_db_url, patient_app_url=APP_URL)
    yield TestClient(app)
    app.state.engine.dispose()


def h(user_id: uuid.UUID) -> dict[str, str]:
    return bearer(sub=str(user_id))


def doctor(engine: Engine) -> tuple[dict[str, str], uuid.UUID]:
    user_id, doctor_id = add_doctor(engine)
    return h(user_id), doctor_id


def my_patient(engine: Engine, doctor_id: uuid.UUID, name: str = "Test Patient") -> uuid.UUID:
    _, patient_id = add_linked_patient(engine)
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE patients SET name = :n WHERE id = :p"), {"n": name, "p": patient_id}
        )
    assign(engine, doctor_id, patient_id)
    return patient_id


def inbox_item(engine: Engine, patient_id: uuid.UUID, kind: str, minutes_ago: int = 0) -> uuid.UUID:
    with engine.begin() as conn:
        item_id: uuid.UUID = conn.execute(
            text(
                "INSERT INTO inbox_items (patient_id, type, ref_table, ref_id, created_at) "
                "VALUES (:p, :t, 'symptom_checkins', :r, :c) RETURNING id"
            ),
            {
                "p": patient_id,
                "t": kind,
                "r": uuid.uuid4(),
                "c": datetime.now(UTC) - timedelta(minutes=minutes_ago),
            },
        ).scalar_one()
    return item_id


def audit_actions(engine: Engine, patient_id: uuid.UUID) -> list[str]:
    with engine.connect() as conn:
        return list(
            conn.execute(
                text("SELECT action FROM audit_log WHERE patient_id = :p ORDER BY created_at"),
                {"p": patient_id},
            ).scalars()
        )


def test_patient_list_follows_the_default_order(client: TestClient, engine: Engine) -> None:
    """§6 / §25 test 3: groups 1-4, newest item first inside a group, the rest by name."""
    headers, doc = doctor(engine)
    g1_old = my_patient(engine, doc, "G1 older")
    g1_new = my_patient(engine, doc, "G1 newer")
    g2 = my_patient(engine, doc, "G2")
    g3 = my_patient(engine, doc, "G3")
    seen_only = my_patient(engine, doc, "Bea")
    quiet = my_patient(engine, doc, "Ann")
    inbox_item(engine, g1_old, "symptom_l1", minutes_ago=30)
    inbox_item(engine, g1_old, "genetic_pending", minutes_ago=1)  # newer, but not a group-1 type
    inbox_item(engine, g1_new, "chat_urgent", minutes_ago=5)
    inbox_item(engine, g2, "pattern_p5", minutes_ago=2)
    inbox_item(engine, g2, "pattern_p1", minutes_ago=0)
    inbox_item(engine, g3, "record_uploaded")
    seen = inbox_item(engine, seen_only, "symptom_l1")
    with engine.begin() as conn:
        conn.execute(text("UPDATE inbox_items SET seen_at = now() WHERE id = :i"), {"i": seen})
    other_doctor_patient = my_patient(engine, doctor(engine)[1], "Not mine")
    inbox_item(engine, other_doctor_patient, "symptom_l1")

    res = client.get(f"{API}/patients", headers=headers)
    assert res.status_code == 200
    rows = res.json()["data"]
    assert [r["name"] for r in rows] == ["G1 newer", "G1 older", "G2", "G3", "Ann", "Bea"]
    assert [r["group"] for r in rows] == [1, 1, 2, 3, 4, 4]
    assert [r["unseen_count"] for r in rows] == [1, 2, 2, 1, 0, 0]
    assert rows[4]["id"] == str(quiet)
    assert rows[0]["fetal"] is None and rows[0]["pregnancy_status"] == "active"


def test_create_edit_and_overview(client: TestClient, engine: Engine) -> None:
    """§8.1: the creating doctor is assigned and primary; edits are logged; §5.1 overview."""
    headers, doc = doctor(engine)
    res = client.post(f"{API}/patients", json={"name": "  Asha  ", "age": 29}, headers=headers)
    assert res.status_code == 201
    created = res.json()["data"]
    pid = created["id"]
    assert created["name"] == "Asha" and created["linked"] is False
    assert created["doctors"] == [{"id": str(doc), "name": "Test Doctor", "is_primary": True}]

    res = client.put(
        f"{API}/patients/{pid}", json={"name": "Asha K", "age": 30, "notes": "n"}, headers=headers
    )
    assert res.status_code == 200
    assert (res.json()["data"]["name"], res.json()["data"]["notes"]) == ("Asha K", "n")
    assert client.get(f"{API}/patients/{pid}", headers=headers).json()["data"]["age"] == 30
    assert audit_actions(engine, uuid.UUID(pid)) == ["patient created", "patient edited"]


@pytest.mark.parametrize(
    "body",
    [{"name": "  "}, {"name": "A", "age": 17}, {"name": "A", "extra": 1}, {}],
)
def test_patient_input_is_validated(
    client: TestClient, engine: Engine, body: dict[str, Any]
) -> None:
    headers, _ = doctor(engine)
    assert client.post(f"{API}/patients", json=body, headers=headers).status_code == 400


def test_other_doctors_patients_are_not_found(client: TestClient, engine: Engine) -> None:
    """§25 test 1 for these routes: read, edit and invite all answer 404."""
    headers, _ = doctor(engine)
    theirs = my_patient(engine, doctor(engine)[1])
    assert client.get(f"{API}/patients/{theirs}", headers=headers).status_code == 404
    res = client.put(f"{API}/patients/{theirs}", json={"name": "X"}, headers=headers)
    assert res.status_code == 404
    assert client.post(f"{API}/patients/{theirs}/invite", headers=headers).status_code == 404
    assert all(
        r["id"] != str(theirs)
        for r in client.get(f"{API}/patients", headers=headers).json()["data"]
    )


def check(client: TestClient, link: str) -> bool:
    code = link.split("code=")[1]
    valid: bool = client.get(f"/api/v1/invites/{code}/check").json()["data"]["valid"]
    return valid


def test_invite_link_replaces_the_unused_one(client: TestClient, engine: Engine) -> None:
    """§8.2: link on the patient app URL, one-time code; a new link cancels the old one."""
    headers, _ = doctor(engine)
    pid = client.post(f"{API}/patients", json={"name": "New"}, headers=headers).json()["data"]["id"]
    first = client.post(f"{API}/patients/{pid}/invite", headers=headers)
    assert first.status_code == 201
    link = first.json()["data"]["link"]
    assert link.startswith(f"{APP_URL}/join?code=") and check(client, link)
    second = client.post(f"{API}/patients/{pid}/invite", headers=headers).json()["data"]["link"]
    assert check(client, second) and not check(client, link)
    assert audit_actions(engine, uuid.UUID(pid)).count("invite created") == 2


def test_linked_patient_cannot_get_a_new_invite(client: TestClient, engine: Engine) -> None:
    headers, doc = doctor(engine)
    pid = my_patient(engine, doc)  # already has a login
    res = client.post(f"{API}/patients/{pid}/invite", headers=headers)
    assert res.status_code == 409 and res.json()["error"]["code"] == "CONFLICT"


def test_inbox_seen_by_one_doctor_shows_for_the_other(client: TestClient, engine: Engine) -> None:
    """§7.2 / §25 test 4: one item per event; "seen" stores who and when for every doctor."""
    a_headers, doc_a = doctor(engine)
    b_headers, doc_b = doctor(engine)
    pid = my_patient(engine, doc_a)
    assign(engine, doc_b, pid)
    ai = inbox_item(engine, pid, "ai_note_flag", minutes_ago=0)
    rule = inbox_item(engine, pid, "symptom_l2", minutes_ago=10)

    unseen = client.get(f"{API}/inbox", headers=b_headers).json()["data"]
    assert [i["id"] for i in unseen] == [str(rule), str(ai)]  # AI suggestion below rule items

    res = client.post(f"{API}/inbox/{rule}/seen", headers=a_headers)
    assert res.status_code == 200 and res.json()["data"]["seen_by_name"] == "Test Doctor"
    first_seen = res.json()["data"]["seen_at"]
    again = client.post(f"{API}/inbox/{rule}/seen", headers=b_headers).json()["data"]
    assert again["seen_at"] == first_seen  # the first doctor stays recorded

    assert [i["id"] for i in client.get(f"{API}/inbox", headers=b_headers).json()["data"]] == [
        str(ai)
    ]
    seen = client.get(f"{API}/inbox?seen=true", headers=b_headers).json()["data"]
    assert seen[0]["id"] == str(rule) and seen[0]["seen_at"] == first_seen
    assert audit_actions(engine, pid).count("inbox item seen") == 1


def test_inbox_of_other_patients_is_hidden(client: TestClient, engine: Engine) -> None:
    headers, _ = doctor(engine)
    item = inbox_item(engine, my_patient(engine, doctor(engine)[1]), "symptom_l1")
    assert all(
        i["id"] != str(item) for i in client.get(f"{API}/inbox", headers=headers).json()["data"]
    )
    assert client.post(f"{API}/inbox/{item}/seen", headers=headers).status_code == 404
    assert client.post(f"{API}/inbox/{uuid.uuid4()}/seen", headers=headers).status_code == 404
