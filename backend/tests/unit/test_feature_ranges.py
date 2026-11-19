"""Training-range files (Dashboard spec §9.4, DEC-076): one entry per model input, in model
order, min <= max, written by scripts/compute_feature_ranges.py (never typed by hand).

When the cleaned training CSVs are present (git-ignored, backend/ml_training/data/), the
committed files must equal a fresh computation, and the split must reproduce the models'
recorded test F1."""

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

from app.modules.predictions.risk_model import MODELS_DIR

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "compute_feature_ranges.py"


def load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("compute_feature_ranges", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("model", ["fetal", "maternal"])
def test_range_file_covers_every_input_in_order(model: str) -> None:
    order = json.loads((MODELS_DIR / f"{model}_risk_feature_order.json").read_text("utf-8"))
    ranges = json.loads((MODELS_DIR / f"{model}_risk_feature_ranges.json").read_text("utf-8"))
    assert list(ranges["features"]) == order
    assert all(r["min"] <= r["max"] for r in ranges["features"].values())


@pytest.mark.parametrize("model", ["fetal", "maternal"])
def test_range_file_matches_the_training_data(model: str) -> None:
    script = load_script()
    src = next(s for s in script.SOURCES if s.model == model)
    if not (script.DATA / src.csv).exists():
        pytest.skip(f"{src.csv} is not here (git-ignored training data)")
    x_train, x_test, _, y_test = script.split(src)
    score = script.check_split(src, x_test, y_test)
    committed = json.loads((MODELS_DIR / f"{model}_risk_feature_ranges.json").read_text("utf-8"))
    assert committed == script.ranges(src, x_train, score)
