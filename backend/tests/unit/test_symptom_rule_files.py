"""The shipped symptom rule files match the spec (Symptom spec §0 rule 4: "The YAML rule files
must match the tables row for row"), and broken files are refused at startup."""

import shutil
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from app.modules.symptoms.rules import RULES_DIR, load_symptom_rules, parse_symptom_rules

RULES = load_symptom_rules()

# §7.2 and §7.3, copied from the spec tables
SPEC_RULES = {
    **{f"L1-{n:02d}": "L1" for n in range(1, 15)},
    **{f"L2-{n:02d}": "L2" for n in range(1, 12)},
}

# §5.1 and §5.2 "ID | Shown as", copied from the spec tables
SPEC_COMMON = {
    "nausea_vomiting": "Nausea / vomiting",
    "fatigue": "Tiredness",
    "headache": "Headache",
    "abdominal_discomfort": "Stomach / abdominal pain or discomfort",
    "back_pain": "Back pain",
    "breast_tenderness": "Breast tenderness",
    "food_craving": "Food craving",
    "appetite_change": "Change in appetite",
    "mood_change": "Mood change",
    "other": "Something else",
}
SPEC_WARNING = {
    "vaginal_bleeding": "Bleeding from the vagina (any amount)",
    "fits": "Fits / convulsions",
    "vision_problems": "Blurred vision, flashing lights or spots",
    "fluid_leaking": "Water breaking or fluid leaking from the vagina",
    "high_fever": "High fever",
    "sudden_breathlessness": "Sudden breathlessness",
    "chest_pain": "Chest pain",
    "fainting": "Fainting",
    "baby_movements_reduced": "Baby moving less, or movements changed",
    "baby_movements_never_felt": "Have not yet felt the baby move",
    "labour_pains": "Labour pains / regular tightenings",
    "severe_itching": "Severe itching",
    "sudden_swelling": "Sudden swelling of face, hands or body",
    "leg_pain_one_side": "Pain or swelling in one leg",
    "pain_passing_urine": "Pain or burning when passing urine",
}


def test_every_spec_rule_is_shipped_once_at_its_level() -> None:
    assert {r.id: r.level for r in RULES.rules} == SPEC_RULES
    assert len(RULES.rules) == 25


def test_vocabulary_matches_the_spec() -> None:
    assert {s.id: s.label for s in RULES.vocabulary.common} == SPEC_COMMON
    assert {s.id: s.label for s in RULES.vocabulary.warning} == SPEC_WARNING
    assert list(RULES.vocabulary.durations) == [
        "under_1_hour", "1_to_6_hours", "most_of_the_day", "more_than_1_day",
    ]  # fmt: skip
    assert list(RULES.vocabulary.labour_durations) == ["under_12_hours", "more_than_12_hours"]
    assert list(RULES.vocabulary.body_areas) == [
        "head", "chest", "upper_abdomen", "lower_abdomen", "back", "pelvis", "legs", "other",
    ]  # fmt: skip
    common = {s.id: s for s in RULES.vocabulary.common}
    assert set(common["headache"].flags) == {"with_vision_problems", "with_swelling"}
    assert set(common["nausea_vomiting"].flags) == {"unable_to_keep_fluids"}
    assert common["abdominal_discomfort"].body_area is not None
    assert common["abdominal_discomfort"].body_area.choices == ("upper_abdomen", "lower_abdomen")
    warning = {s.id: s for s in RULES.vocabulary.warning}
    assert warning["baby_movements_reduced"].from_week_setting == "movements_from_week"
    assert warning["baby_movements_never_felt"].from_week_setting == "never_felt_from_week"
    assert [s.id for s in RULES.vocabulary.warning if s.labour_duration] == ["labour_pains"]


def test_settings_are_the_spec_defaults() -> None:
    s = RULES.settings
    assert (s.rules_version, s.pattern_window_days, s.p3_min_days, s.p5_min_l2) == (
        "1.0.0",
        7,
        5,
        2,
    )
    assert (s.movements_from_week, s.never_felt_from_week, s.preterm_before_week) == (16, 24, 37)


def test_puqe_scores_and_bands() -> None:
    """§8: three questions scored 1-5; bands 3-6 mild, 7-12 moderate, 13-15 severe."""
    assert len(RULES.puqe.questions) == 3
    assert all(sorted(q.answers) == [1, 2, 3, 4, 5] for q in RULES.puqe.questions)
    assert [RULES.puqe.band_for(n) for n in (3, 6, 7, 12, 13, 15)] == [
        "mild", "mild", "moderate", "moderate", "severe", "severe",
    ]  # fmt: skip


def test_messages_and_phone_numbers() -> None:
    assert all(m.text is None for m in RULES.messages.values())  # pending doctor approval
    assert RULES.helpline("emergency").numbers == ("102", "108")
    assert RULES.helpline("mental_health").numbers == ("14416", "18008914416")
    assert all(h.source_url.startswith("https://") for h in RULES.helplines)


def _broken(tmp_path: Path, name: str, old: str, new: str) -> Path:
    shutil.copytree(RULES_DIR, tmp_path, dirs_exist_ok=True)
    path = tmp_path / name
    text = path.read_text(encoding="utf-8")
    assert old in text, old
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize(
    ("name", "old", "new", "match"),
    [
        ("red_flags.yaml", "- id: L1-02", "- id: L1-01", "unique"),
        ("red_flags.yaml", "symptom: fits }", "symptom: seizure }", "unknown symptom"),
        ("red_flags.yaml", "[unable_to_keep_fluids]", "[dizzy]", "unknown flag"),
        ("red_flags.yaml", "- id: L2-01\n    level: L2", "- id: L2-01\n    level: L1", "level"),
        ("red_flags.yaml", "unless_rules: [L1-03, L1-04]", "unless_rules: [L1-99]", "unless_rules"),
        ("puqe.yaml", "min: 7, max: 12", "min: 8, max: 12", "gap"),
        ("config.yaml", "p3_min_days: 5", "p3_min_days: 9", "p3_min_days"),
        ("messages.yaml", "  msg_safe_fallback:", "  msg_other:", "§11.2 keys"),
        ("messages.yaml", "  - key: mental_health", "  - key: counselling", "mental_health"),
    ],
)
def test_broken_rule_files_are_refused(
    tmp_path: Path, name: str, old: str, new: str, match: str
) -> None:
    with pytest.raises(ValidationError, match=match):
        parse_symptom_rules(_broken(tmp_path, name, old, new))


def test_yaml_is_plain_data() -> None:
    """The rule files load with safe_load (no code, no custom tags)."""
    for path in RULES_DIR.glob("*.yaml"):
        assert yaml.safe_load(path.read_text(encoding="utf-8"))
