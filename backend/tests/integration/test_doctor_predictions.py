"""Doctor predictions (Dashboard spec §9-11, §25 tests 1, 5, 6, 7, 8): schema, unit
conversion, range warnings, the unchanged models, history, sharing, trends, the patient's
shared results and the result_available notification. Runs against alovia-test."""

import json
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from tests.helpers import add_doctor, add_linked_patient, assign, bearer, make_app

API = "/api/v1/doctor"
CASES = {
    c["id"]: c
    for c in json.loads(
        (Path(__file__).resolve().parents[1] / "fixtures/ml_reference_outputs.json").read_text(
            "utf-8"
        )
    )["cases"]
}
HBA1C, GLUCOSE, TEMP = (
    "Blood Glucose(HbA1c mmol/mol)",
    "Blood Glucose(Fasting mmol/L)",
    "Body Temperature(F) ",
)
MODEL_UNITS = {"hba1c": "mmol/mol", "glucose": "mmol/L", "temperature": "°F"}


@pytest.fixture(scope="module")
def client(test_db_url: str, engine: Engine) -> Iterator[TestClient]:
    app: FastAPI = make_app(database_url=test_db_url)
    yield TestClient(app)
    app.state.engine.dispose()


def setup(engine: Engine) -> tuple[dict[str, str], dict[str, str], uuid.UUID]:
    """(doctor headers, patient headers, patient id) for an assigned, linked patient."""
    doctor_user, doctor_id = add_doctor(engine)
    patient_user, patient_id = add_linked_patient(engine)
    assign(engine, doctor_id, patient_id, primary=True)
    return bearer(sub=str(doctor_user)), bearer(sub=str(patient_user)), patient_id


def predict(
    client: TestClient, h: dict[str, str], pid: uuid.UUID, model: str, body: dict[str, Any]
) -> Any:
    return client.post(f"{API}/patients/{pid}/predictions/{model}", json=body, headers=h)


def maternal(case: str = "maternal_low", **units: str) -> dict[str, Any]:
    return {"values": dict(CASES[case]["input"]), "units": {**MODEL_UNITS, **units}}


def test_schema_lists_every_input_with_ranges_and_units(client: TestClient, engine: Engine) -> None:
    h, _, _ = setup(engine)
    data = client.get(f"{API}/predictions/schema/maternal", headers=h).json()["data"]
    fields = [f for g in data["groups"] for f in g["fields"]]
    assert sorted(f["feature"] for f in fields) == sorted(CASES["maternal_low"]["input"])
    hba1c = next(f for f in fields if f["feature"] == HBA1C)
    assert hba1c["unit"] == {
        "name": "hba1c",
        "model_unit": "mmol/mol",
        "other_unit": "%",
        "default": "%",
    }
    assert hba1c["range"]["min"] <= hba1c["range"]["max"]
    assert "lim_maternal_separable" in data["limitation_keys"]
    fetal = client.get(f"{API}/predictions/schema/fetal", headers=h).json()["data"]
    assert len([f for g in fetal["groups"] for f in g["fields"]]) == 21
    assert all(f["unit"] is None for g in fetal["groups"] for f in g["fields"])


@pytest.mark.parametrize("case", ["fetal_normal", "fetal_pathological", "maternal_high"])
def test_prediction_matches_the_reference_model(
    client: TestClient, engine: Engine, case: str
) -> None:
    """The saved prediction equals the old backend's output (models unchanged)."""
    h, _, pid = setup(engine)
    model = CASES[case]["model"]
    body = maternal(case) if model == "maternal" else {"values": CASES[case]["input"]}
    res = predict(client, h, pid, model, body)
    assert res.status_code == 201
    out = res.json()["data"]
    expected = CASES[case]["expected_output"]
    for key in ("predicted_class", "confidence", "class_probabilities", "top_contributing_factors"):
        assert out[key] == expected[key]
    assert out["entered_by_name"] == "Test Doctor" and out["model_version"].startswith("XGBoost")
    assert out["share"] is None


def test_units_are_converted_and_both_values_stored(client: TestClient, engine: Engine) -> None:
    """§25 test 5: 7.0 % -> 53 mmol/mol, 90 mg/dL -> 5.0 mmol/L, 37 °C -> 98.6 °F."""
    h, _, pid = setup(engine)
    body = maternal(hba1c="%", glucose="mg/dL", temperature="°C")
    body["values"] |= {HBA1C: 7.0, GLUCOSE: 90, TEMP: 37}
    out = predict(client, h, pid, "maternal", body).json()["data"]
    assert round(out["input_values"][HBA1C]) == 53
    assert out["input_values"][GLUCOSE] == pytest.approx(5.0)
    assert out["input_values"][TEMP] == pytest.approx(98.6)
    assert out["entered_values"][HBA1C] == {"value": 7.0, "unit": "%"}
    assert out["entered_values"][TEMP] == {"value": 37, "unit": "°C"}


def test_out_of_range_value_warns_and_still_predicts(client: TestClient, engine: Engine) -> None:
    """§25 test 6."""
    h, _, pid = setup(engine)
    body = {"values": {**CASES["fetal_normal"]["input"], "LB": 400}}
    res = predict(client, h, pid, "fetal", body)
    assert res.status_code == 201
    out = res.json()["data"]
    assert out["range_warnings"] == ["LB"] and out["predicted_class"]
    with engine.connect() as conn:
        stored = conn.execute(
            text("SELECT range_warnings FROM fetal_results WHERE id = :i"), {"i": out["id"]}
        ).scalar_one()
    assert stored == ["LB"]


@pytest.mark.parametrize(
    "body",
    [
        {"values": {"LB": 133}},  # inputs missing
        {"values": {**CASES["fetal_normal"]["input"], "Extra": 1}},
        {"values": CASES["fetal_normal"]["input"], "units": {"hba1c": "%"}},  # no switch here
        {"values": CASES["fetal_normal"]["input"], "other": 1},
    ],
)
def test_fetal_input_is_validated(client: TestClient, engine: Engine, body: dict[str, Any]) -> None:
    h, _, pid = setup(engine)
    assert predict(client, h, pid, "fetal", body).status_code == 400


def test_maternal_units_are_required_and_checked(client: TestClient, engine: Engine) -> None:
    h, _, pid = setup(engine)
    res = predict(client, h, pid, "maternal", {"values": CASES["maternal_low"]["input"]})
    assert res.status_code == 400
    assert set(res.json()["error"]["fields"]) == {
        "units.hba1c",
        "units.glucose",
        "units.temperature",
    }
    assert predict(client, h, pid, "maternal", maternal(glucose="g/L")).status_code == 400
    assert predict(client, h, pid, "unknown", maternal()).status_code == 400


def add_assessment(engine: Engine, pid: uuid.UUID, mother_status: str) -> None:
    with engine.begin() as conn:
        user = conn.execute(
            text("SELECT user_id FROM patients WHERE id = :p"), {"p": pid}
        ).scalar_one()
        conn.execute(
            text(
                "INSERT INTO genetic_assessments (patient_id, submitted_by, inputs, results, "
                "rules_version, show_numbers_to_patient, risk_indicated, priority, review_status) "
                "VALUES (:p, :u, :i, '{}', '1.0.0', false, false, 'normal', 'pending_review')"
            ),
            {
                "p": pid,
                "u": user,
                "i": json.dumps({"haemoglobin_group": {"mother": {"status": mother_status}}}),
            },
        )


def test_hba1c_note_follows_the_mothers_haemoglobin_status(
    client: TestClient, engine: Engine
) -> None:
    """§9.5 / §25 test 7: shown unless the status is tested_negative or unknown (or none)."""
    h, _, pid = setup(engine)
    assert predict(client, h, pid, "maternal", maternal()).json()["data"]["hba1c_note"] is False
    add_assessment(engine, pid, "unknown")
    assert predict(client, h, pid, "maternal", maternal()).json()["data"]["hba1c_note"] is False
    add_assessment(engine, pid, "beta_thal_carrier")
    out = predict(client, h, pid, "maternal", maternal()).json()["data"]
    assert out["hba1c_note"] is True
    fetal = predict(client, h, pid, "fetal", {"values": CASES["fetal_normal"]["input"]})
    assert fetal.json()["data"]["hba1c_note"] is False
    history = client.get(f"{API}/patients/{pid}/predictions?model=maternal", headers=h).json()
    assert len(history["data"]) == 3 and all(r["hba1c_note"] for r in history["data"])


def test_sharing_shows_only_template_and_message(client: TestClient, engine: Engine) -> None:
    """§10 / §25 test 8: invisible before sharing, template + message only after, once."""
    h, ph, pid = setup(engine)
    rid = predict(client, h, pid, "fetal", {"values": CASES["fetal_suspect"]["input"]}).json()[
        "data"
    ]["id"]
    assert client.get("/api/v1/patient/results", headers=ph).json()["data"] == []

    res = client.post(
        f"{API}/predictions/fetal/{rid}/share", json={"doctor_message": " Test note "}, headers=h
    )
    assert res.status_code == 201
    share = res.json()["data"]["share"]
    assert share["template_key"] == "result_template_fetal_suspect"
    assert share["doctor_message"] == "Test note" and share["shared_by_name"] == "Test Doctor"

    mine = client.get("/api/v1/patient/results", headers=ph).json()["data"]
    assert len(mine) == 1
    assert set(mine[0]) == {
        "id",
        "result_type",
        "result_date",
        "shared_at",
        "template_key",
        "template_text",
        "doctor_message",
        "doctor_name",
    }
    assert mine[0]["template_text"] is None  # pending doctor approval (DEC-041)
    assert "Suspect" not in json.dumps(mine)  # no class label or numbers leak

    again = client.post(f"{API}/predictions/fetal/{rid}/share", json={}, headers=h)
    assert again.status_code == 409
    notes = client.get("/api/v1/patient/notifications", headers=ph).json()["data"]
    assert [n["type"] for n in notes].count("result_available") == 1


def test_other_doctors_cannot_predict_read_or_share(client: TestClient, engine: Engine) -> None:
    """§25 test 1 for these routes."""
    h, _, pid = setup(engine)
    other, _, _ = setup(engine)
    rid = predict(client, h, pid, "fetal", {"values": CASES["fetal_normal"]["input"]}).json()[
        "data"
    ]["id"]
    fetal = {"values": CASES["fetal_normal"]["input"]}
    assert predict(client, other, pid, "fetal", fetal).status_code == 404
    assert (
        client.get(f"{API}/patients/{pid}/predictions?model=fetal", headers=other).status_code
        == 404
    )
    assert client.get(f"{API}/patients/{pid}/trends", headers=other).status_code == 404
    res = client.post(f"{API}/predictions/fetal/{rid}/share", json={}, headers=other)
    assert res.status_code == 404
    assert (
        client.post(f"{API}/predictions/maternal/{rid}/share", json={}, headers=h).status_code
        == 404
    )


def test_trends_list_raw_values_oldest_first(client: TestClient, engine: Engine) -> None:
    """§11: maternal inputs and the configured fetal inputs; week label from the due date."""
    h, _, pid = setup(engine)
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE patients SET due_date = CURRENT_DATE + 70 WHERE id = :p"), {"p": pid}
        )
    first = predict(client, h, pid, "maternal", maternal("maternal_low")).json()["data"]
    predict(client, h, pid, "maternal", maternal("maternal_high"))
    predict(client, h, pid, "fetal", {"values": CASES["fetal_normal"]["input"]})
    data = client.get(f"{API}/patients/{pid}/trends", headers=h).json()["data"]
    assert data["fetal_features"] == ["LB", "ASTV", "ALTV"]
    assert [p["result_id"] for p in data["maternal"]][0] == first["id"]
    assert data["maternal"][0]["ga_week"] == 30  # 280 - 70 days = 210 days
    assert set(data["fetal"][0]["values"]) == {"LB", "ASTV", "ALTV"}
    assert data["fetal"][0]["predicted_class"] == "Normal"
