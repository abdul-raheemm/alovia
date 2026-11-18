"""The doctor review sheet (scripts/export_review_sheet.py) lists everything that needs a
doctor's sign-off (Journey spec §16): no message, content item, size row or rule is left out."""

import importlib.util
from collections import Counter
from pathlib import Path
from types import ModuleType

from app.modules.journey.config import load_helplines, load_journey_config, load_journey_messages


def load_script() -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "scripts" / "export_review_sheet.py"
    spec = importlib.util.spec_from_file_location("export_review_sheet", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sheet_covers_every_reviewable_thing() -> None:
    rows = load_script().rows()
    count = Counter(r["section"].split(" ")[0] for r in rows)
    assert count["1"] == len(load_journey_messages())
    assert count["2"] == 21  # every prototype content item, once
    assert count["3"] == 27  # every size row, weeks 14-40
    assert count["4"] == len(load_journey_config().month_map)
    assert count["5"] == 1 and count["6"] == 1 + len(load_helplines())
    assert len({(r["section"], r["id"]) for r in rows}) == len(rows)  # no duplicates
    assert all(r["doctor_verdict"] == "" and r["doctor_comment"] == "" for r in rows)
