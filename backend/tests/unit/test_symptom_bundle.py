"""The patient app's bundled symptom texts (DEC-060/061) match the rule files."""

import importlib.util
from pathlib import Path
from types import ModuleType

from app.modules.symptoms.rules import parse_symptom_rules


def load_script() -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "scripts" / "export_symptom_bundle.py"
    spec = importlib.util.spec_from_file_location("export_symptom_bundle", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bundled_file_is_up_to_date() -> None:
    script = load_script()
    committed = script.OUT.read_text(encoding="utf-8")
    assert committed == script.render(parse_symptom_rules()), (
        "run: python scripts/export_symptom_bundle.py"
    )
