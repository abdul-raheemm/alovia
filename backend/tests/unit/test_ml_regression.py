"""Moved ML code must reproduce the old ml-test backend exactly (ml_models_spec.md §0, §6).

Reference: tests/fixtures/ml_reference_outputs.json, recorded from the old backend's own
/predict endpoints for 12 owner-approved cases.
"""

import hashlib
import json
from importlib.metadata import version
from pathlib import Path
from typing import Any

import pytest

from app.modules.predictions.risk_model import MODELS_DIR, load_models

REFERENCE = json.loads(
    (Path(__file__).resolve().parents[1] / "fixtures/ml_reference_outputs.json").read_text("utf-8")
)
ML_PACKAGES = ("xgboost", "scikit-learn", "shap", "numpy", "pandas", "joblib", "scipy", "numba")


def test_model_files_identical_to_reference() -> None:
    actual = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(MODELS_DIR.iterdir())
        if p.is_file()
    }
    assert actual == REFERENCE["model_files_sha256"]


def test_ml_package_versions_match_reference() -> None:
    assert {p: version(p) for p in ML_PACKAGES} == {
        p: REFERENCE["packages"][p] for p in ML_PACKAGES
    }


@pytest.mark.parametrize("case", REFERENCE["cases"], ids=[c["id"] for c in REFERENCE["cases"]])
def test_output_identical_to_old_backend(case: dict[str, Any]) -> None:
    model = getattr(load_models(), case["model"])
    # same path as the old endpoint: validate through the generated input schema, then model_dump
    payload = model.input_schema("Input")(**case["input"]).model_dump()
    assert model.predict(payload) == case["expected_output"]
