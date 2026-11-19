"""backend/rules/dashboard/*.yaml (Dashboard spec §23, §9.4-9.6, §10) load strictly."""

import json
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.modules.dashboard.rules import CLASSES, ML_DIR, RULES_DIR, parse_dashboard_rules


def test_files_load_with_the_spec_defaults() -> None:
    rules = parse_dashboard_rules()
    s = rules.settings
    assert s.default_units.model_dump() == {"hba1c": "%", "glucose": "mg/dL", "temperature": "°F"}
    assert s.fetal_trend_features == ("LB", "ASTV", "ALTV")
    assert (s.invite_code_length, s.invite_code_days) == (8, 7)
    assert s.record_formats == ("pdf", "jpg", "png")
    assert (s.record_max_mb, s.signed_url_minutes) == (10, 5)
    assert s.require_signoff is False
    assert not (s.ai_summary_enabled or s.ai_share_draft_enabled)
    assert not (s.ai_genetic_draft_enabled or s.ai_note_flag_enabled)
    assert (s.ai_summary_days, s.ai_timeout_seconds) == (14, 15)
    assert s.llm_provider is None and s.llm_model is None  # TODO(OPEN)
    # no wording written by the agent: every text waits for a doctor (DEC-041)
    assert all(m.text is None for m in rules.messages.values())


def test_template_classes_match_the_models() -> None:
    def labels(name: str, key: str) -> set[str]:
        data = json.loads((ML_DIR / f"{name}_risk_label_mapping.json").read_text())
        return set(data[key].values())

    assert labels("fetal", "nsp_to_label") == set(CLASSES["fetal"])
    assert labels("maternal", "status_to_label") == set(CLASSES["maternal"])


def _copy(tmp_path: Path) -> None:
    for f in RULES_DIR.glob("*.yaml"):
        shutil.copy(f, tmp_path)


@pytest.mark.parametrize(
    ("line", "replacement"),
    [
        ("fetal_trend_features: [LB, ASTV, ALTV]", "fetal_trend_features: [LB, Nonsense]"),
        ('  glucose: "mg/dL"', '  glucose: "g/L"'),
        ("record_max_mb: 10", "record_max_mb: 0"),
        ("require_signoff: false", "require_signoff: false\nsurprise: 1"),
    ],
)
def test_wrong_config_is_refused(tmp_path: Path, line: str, replacement: str) -> None:
    _copy(tmp_path)
    cfg = tmp_path / "config.yaml"
    content = cfg.read_text(encoding="utf-8")
    assert line in content
    cfg.write_text(content.replace(line, replacement), encoding="utf-8")
    with pytest.raises(ValidationError):
        parse_dashboard_rules(tmp_path)


def test_a_missing_message_is_refused(tmp_path: Path) -> None:
    _copy(tmp_path)
    msgs = tmp_path / "messages.yaml"
    content = msgs.read_text(encoding="utf-8")
    msgs.write_text(content.replace("  lim_fetal_ctg:", "  lim_fetal_other:"), encoding="utf-8")
    with pytest.raises(ValidationError):
        parse_dashboard_rules(tmp_path)
