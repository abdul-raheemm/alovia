"""The patient app's bundled genetic form and result texts match the rule files."""

import importlib.util
from pathlib import Path
from types import ModuleType

from app.modules.genetic.rules import parse_genetic_rules


def load_script() -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "scripts" / "export_genetic_bundle.py"
    spec = importlib.util.spec_from_file_location("export_genetic_bundle", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bundled_file_is_up_to_date() -> None:
    script = load_script()
    committed = script.OUT.read_text(encoding="utf-8")
    assert committed == script.render(parse_genetic_rules()), (
        "run: python scripts/export_genetic_bundle.py"
    )
