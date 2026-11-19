"""The symptom rule-review sheet (Symptom spec §16) lists every rule, PUQE item, pattern,
setting, message, phone number and assumption, once, with the rules version."""

import importlib.util
from collections import Counter
from pathlib import Path
from types import ModuleType

from app.modules.symptoms.rules import load_symptom_rules


def load_script() -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "scripts" / "export_symptom_rule_review.py"
    spec = importlib.util.spec_from_file_location("export_symptom_rule_review", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sheet_covers_everything_the_doctor_signs_off() -> None:
    rules = load_symptom_rules()
    rows = load_script().rows(rules)
    count = Counter(r["section"].split(" ")[0] for r in rows)
    assert count["1"] == len(rules.rules) == 25
    assert count["2"] == 4  # three PUQE questions + the bands
    assert count["3"] == 5 and count["4"] == 3
    assert count["5"] == len(rules.messages) and count["6"] == len(rules.helplines)
    assert count["7"] == 4  # A1-A4
    assert len({(r["section"], r["item_id"]) for r in rows}) == len(rows)
    assert {r["rules_version"] for r in rows} == {rules.settings.rules_version}
    assert all(r["checked"] == r["reviewer"] == "" for r in rows)
