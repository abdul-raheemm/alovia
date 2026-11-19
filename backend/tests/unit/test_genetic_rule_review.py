"""The genetic rule-review sheet (Genetic spec §13) lists every rule row, evidence rule,
conflict, error, message and assumption, once, with the rules version."""

import importlib.util
from collections import Counter
from pathlib import Path
from types import ModuleType

from app.modules.genetic.rules import load_genetic_rules


def load_script() -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "scripts" / "export_genetic_rule_review.py"
    spec = importlib.util.spec_from_file_location("export_genetic_rule_review", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sheet_covers_everything_the_doctor_signs_off() -> None:
    rules = load_genetic_rules()
    rows = load_script().rows(rules)
    count = Counter(r["section"].split(" ")[0] for r in rows)
    assert count["1"] == 17 and count["2"] == 7 and count["3"] == 4  # §7 rule rows
    assert count["4"] == 3  # §6.2 evidence rules
    assert count["5"] == 6  # C1, C2, F1, F2, E3, E4
    assert count["6"] == len(rules.messages) == 25
    assert count["7"] == 4  # A1-A4
    assert len({(r["section"], r["item_id"]) for r in rows}) == len(rows)
    assert {r["rules_version"] for r in rows} == {rules.settings.rules_version}
    assert all(r["checked"] == r["reviewer"] == "" for r in rows)
