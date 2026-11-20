"""Rule review screen (Dashboard spec §19, §25 test 13; DEC-080..082, DEC-099/100).
Runs against alovia-test."""

import uuid
from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

import app.main as main_module
from app.modules.dashboard.rule_review import MODULES, module_rows, require_signoff
from app.modules.dashboard.rules import load_dashboard_rules
from app.modules.genetic.rules import load_genetic_rules
from app.modules.symptoms.rules import load_symptom_rules
from tests.helpers import (
    add_account,
    add_doctor,
    add_linked_patient,
    bearer,
    make_app,
    make_settings,
)

API = "/api/v1/doctor/rules"


@pytest.fixture(scope="module")
def client(test_db_url: str, engine: Engine) -> Iterator[TestClient]:
    app: FastAPI = make_app(database_url=test_db_url)
    yield TestClient(app)
    app.state.engine.dispose()


def doctor(engine: Engine) -> dict[str, str]:
    return bearer(sub=str(add_doctor(engine)[0]))


def test_overview_lists_every_sheet_row(client: TestClient, engine: Engine) -> None:
    data = client.get(API, headers=doctor(engine)).json()["data"]
    assert [m["module"] for m in data] == ["genetic", "symptom", "journey"]
    assert [m["total"] for m in data] == [66, 50, 72]  # the same rows as the CSV sheets
    assert data[0]["rules_version"] == "1.0.0" and data[2]["rules_version"].startswith("j-")
    first = data[0]["rows"][0]
    assert first["key"] == "1:HBB-01" and first["checked"] is None


def test_sign_off_keeps_the_newest_answer(client: TestClient, engine: Engine) -> None:
    h = doctor(engine)
    url = f"{API}/symptom/signoff"
    res = client.post(url, json={"key": "1:L1-01", "checked": True, "comment": " Fine "}, headers=h)
    assert res.status_code == 201
    assert res.json()["data"]["doctor_name"] == "Test Doctor"
    client.post(url, json={"key": "1:L1-01", "checked": False, "comment": "Wording"}, headers=h)
    symptom = next(m for m in client.get(API, headers=h).json()["data"] if m["module"] == "symptom")
    row = next(r for r in symptom["rows"] if r["key"] == "1:L1-01")
    assert (row["checked"], row["comment"]) == (False, "Wording")
    assert client.post(url, json={"key": "nope", "checked": True}, headers=h).status_code == 404
    bad = client.post(f"{API}/dashboard/signoff", json={"key": "x", "checked": True}, headers=h)
    assert bad.status_code == 400


def test_export_is_a_markdown_download(client: TestClient, engine: Engine) -> None:
    h = doctor(engine)
    client.post(
        f"{API}/genetic/signoff",
        json={"key": "7:A1", "checked": True, "comment": "a | b"},
        headers=h,
    )
    res = client.get(f"{API}/genetic/export", headers=h)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/markdown")
    assert 'filename="rule_review_signoff_genetic.md"' in res.headers["content-disposition"]
    line = next(x for x in res.text.splitlines() if x.startswith("| 7:A1 |"))
    assert "| yes | Test Doctor |" in line and "a \\| b" in line  # pipes escaped


def test_only_doctors_use_the_rule_review(client: TestClient, engine: Engine) -> None:
    admin = bearer(sub=str(add_account(engine, "admin")))
    patient = bearer(sub=str(add_linked_patient(engine)[0]))
    for h in (admin, patient):
        assert client.get(API, headers=h).status_code == 403
        assert (
            client.post(
                f"{API}/symptom/signoff", json={"key": "1:L1-01", "checked": True}, headers=h
            ).status_code
            == 403
        )


def test_require_signoff_stops_startup_until_every_row_is_checked(
    test_db_url: str, engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """§25 test 13 (DEC-081). Kept last in this file: it signs every row."""
    genetic, symptoms = load_genetic_rules(), load_symptom_rules()
    with pytest.raises(RuntimeError, match="not signed off"):
        require_signoff(engine, genetic, symptoms)
    rules = load_dashboard_rules()
    strict = rules.model_copy(
        update={"settings": rules.settings.model_copy(update={"require_signoff": True})}
    )
    monkeypatch.setattr(main_module, "load_dashboard_rules", lambda: strict)
    with pytest.raises(RuntimeError, match="not signed off"):
        main_module.create_app(make_settings(database_url=test_db_url))

    _, doctor_id = add_doctor(engine)
    with engine.begin() as conn:
        for module in MODULES:
            version, rows = module_rows(module, genetic, symptoms)
            conn.execute(
                text(
                    "INSERT INTO rule_signoffs (module, rules_version, item_id, checked, "
                    "doctor_id) VALUES (:m, :v, :i, true, :d)"
                ),
                [{"m": module, "v": version, "i": r.key, "d": doctor_id} for r in rows],
            )
    require_signoff(engine, genetic, symptoms)  # no error now
    app = main_module.create_app(make_settings(database_url=test_db_url))
    app.state.engine.dispose()
    assert uuid.UUID(str(doctor_id))
