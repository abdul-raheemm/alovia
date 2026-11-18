"""Symptom engine (Symptom spec §14 tests 1-7, 9, 10 at engine level). Safety-critical: one test
per rule in §7.2/§7.3, plus every boundary the spec names. Test 8 (no pattern changes in patient
responses) and the saving side of test 10 are integration tests (task 3)."""

from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest

from app.modules.symptoms.engine import (
    FALLBACK,
    CheckinError,
    Entry,
    History,
    PastEntry,
    assess,
    offered_warning_ids,
    pattern_changes,
    puqe_band,
    validate,
)
from app.modules.symptoms.rules import load_symptom_rules

RULES = load_symptom_rules()
SEVERE = {"severity": "severe", "duration": "1_to_6_hours"}


def run(*items: dict[str, Any], week: int | None = 20, source: str = "form") -> Any:
    """Validate then assess, as the API does."""
    return assess(validate(list(items), source, RULES, week), week, RULES)


def item(symptom: str, **details: Any) -> dict[str, Any]:
    return {"symptom": symptom, **details}


# ---- test 1: one test per rule ----

SIMPLE_L1 = {
    "L1-01": "vaginal_bleeding",
    "L1-02": "fits",
    "L1-05": "vision_problems",
    "L1-06": "fluid_leaking",
    "L1-07": "high_fever",
    "L1-08": "sudden_breathlessness",
    "L1-09": "chest_pain",
    "L1-10": "fainting",
    "L1-12": "baby_movements_reduced",
}
SIMPLE_L2 = {
    "L2-01": "severe_itching",
    "L2-03": "leg_pain_one_side",
    "L2-04": "pain_passing_urine",
    "L2-09": "baby_movements_never_felt",
}


@pytest.mark.parametrize(("rule", "symptom"), {**SIMPLE_L1, **SIMPLE_L2}.items())
def test_selecting_a_warning_sign_triggers_its_rule(rule: str, symptom: str) -> None:
    result = run(item(symptom), week=30)
    assert result.matched_rules == [rule]
    assert result.level == rule[:2]


@pytest.mark.parametrize("flag", ["with_vision_problems", "with_swelling"])
@pytest.mark.parametrize("severity", ["mild", "moderate", "severe"])
def test_l1_03_headache_with_a_flag_any_severity(flag: str, severity: str) -> None:
    result = run(item("headache", severity=severity, duration="under_1_hour", **{flag: True}))
    assert result.level == "L1" and "L1-03" in result.matched_rules
    assert "L2-07" not in result.matched_rules  # L1-03 vs L2-07 (§14 test 1)
    assert "L2-11" not in result.matched_rules


def test_l1_04_headache_with_sudden_swelling_and_l2_02_without() -> None:
    both = run(item("headache", severity="mild", duration="under_1_hour"), item("sudden_swelling"))
    assert both.level == "L1" and both.matched_rules == ["L1-04"]  # L2-02 needs no headache
    alone = run(item("sudden_swelling"))
    assert alone.level == "L2" and alone.matched_rules == ["L2-02"]


@pytest.mark.parametrize("area", ["upper_abdomen", "lower_abdomen"])
def test_l1_11_severe_abdominal_pain_either_area(area: str) -> None:
    result = run(item("abdominal_discomfort", body_area=area, **SEVERE))
    assert result.matched_rules == ["L1-11"] and result.level == "L1"
    moderate = run(item("abdominal_discomfort", body_area=area, severity="moderate",
                        duration="1_to_6_hours"))  # fmt: skip
    assert moderate.level == "L0"


def test_labour_pain_rules_by_week_and_duration() -> None:
    """L1-13, L1-14, L2-10; §14 test 4 boundary 36/37."""
    short = {"duration": "under_12_hours"}
    long = {"duration": "more_than_12_hours"}
    assert run(item("labour_pains", **short), week=36).matched_rules == ["L1-14"]
    assert run(item("labour_pains", **short), week=37).matched_rules == ["L2-10"]
    assert run(item("labour_pains", **short), week=37).level == "L2"
    assert run(item("labour_pains", **long), week=37).matched_rules == ["L1-13"]
    assert run(item("labour_pains", **long), week=30).matched_rules == ["L1-13", "L1-14"]


def test_l2_05_puqe_at_least_13_and_l2_06_fluids() -> None:
    assert run(item("nausea_vomiting", puqe_answers=[5, 4, 4])).matched_rules == ["L2-05"]  # 13
    assert run(item("nausea_vomiting", puqe_answers=[4, 4, 4])).level == "L0"  # 12
    fluids = run(item("nausea_vomiting", puqe_answers=[1, 1, 1], unable_to_keep_fluids=True))
    assert fluids.matched_rules == ["L2-06"] and fluids.level == "L2"


def test_l2_07_severe_headache_alone() -> None:
    result = run(item("headache", **SEVERE))
    assert result.matched_rules == ["L2-07"] and result.level == "L2"


def test_l2_08_severe_mood_change_adds_mood_support() -> None:
    result = run(item("mood_change", severity="severe"))
    assert result.matched_rules == ["L2-08"]
    assert result.message_keys == ["msg_level2_contact_today", "msg_mood_support"]
    mild = run(item("mood_change", severity="mild"))  # §7.5: support message regardless of level
    assert mild.level == "L0" and mild.message_keys == ["msg_level0_logged", "msg_mood_support"]


# ---- test 2: highest level wins ----


def test_highest_level_wins_and_all_matches_are_kept() -> None:
    mixed = run(item("vaginal_bleeding"), item("severe_itching"))
    assert mixed.level == "L1" and mixed.matched_rules == ["L1-01", "L2-01"]
    assert mixed.message_keys == ["msg_level1_go_now"]
    l2_l0 = run(item("severe_itching"), item("fatigue", severity="mild", duration="under_1_hour"))
    assert l2_l0.level == "L2" and l2_l0.matched_rules == ["L2-01"]
    nothing = run(item("back_pain", severity="moderate", duration="1_to_6_hours"))
    assert (nothing.level, nothing.matched_rules) == ("L0", [])
    assert nothing.message_keys == ["msg_level0_logged"]


# ---- tests 3 and 4: unknown week, week boundaries ----


def test_unknown_week_applies_week_rules_and_offers_movements() -> None:
    result = run(item("labour_pains", duration="under_12_hours"), week=None)
    assert "L1-14" in result.matched_rules and result.level == "L1"
    offered = offered_warning_ids(RULES, None)
    assert "baby_movements_reduced" in offered
    assert "baby_movements_never_felt" in offered  # DEC-065


def test_week_boundaries_for_movement_signs() -> None:
    """§14 test 4: 15/16 for movements, 23/24 for never-felt."""
    assert "baby_movements_reduced" not in offered_warning_ids(RULES, 15)
    assert "baby_movements_reduced" in offered_warning_ids(RULES, 16)
    assert "baby_movements_never_felt" not in offered_warning_ids(RULES, 23)
    assert "baby_movements_never_felt" in offered_warning_ids(RULES, 24)
    with pytest.raises(CheckinError) as err:
        run(item("baby_movements_reduced"), week=15)  # not offered -> V2
    assert (err.value.code, err.value.field) == ("V2", "entries.0.symptom")


# ---- test 5: catch-all ----


def test_catch_all_for_severe_entries_no_other_rule_covers() -> None:
    assert run(item("back_pain", **SEVERE)).matched_rules == ["L2-11"]
    other = run(item("other", name="Test pain", **SEVERE))
    assert other.matched_rules == ["L2-11"] and other.level == "L2"
    # an entry already covered by a rule is not caught again
    assert run(item("headache", **SEVERE)).matched_rules == ["L2-07"]
    assert run(item("mood_change", severity="severe")).matched_rules == ["L2-08"]


# ---- test 6: PUQE ----


@pytest.mark.parametrize(
    ("answers", "score", "band"),
    [
        ((1, 1, 1), 3, "mild"),
        ((2, 2, 2), 6, "mild"),
        ((3, 2, 2), 7, "moderate"),
        ((4, 4, 4), 12, "moderate"),
        ((5, 4, 4), 13, "severe"),
        ((5, 5, 5), 15, "severe"),
    ],
)
def test_puqe_score_and_band(answers: tuple[int, int, int], score: int, band: str) -> None:
    entry = validate([item("nausea_vomiting", puqe_answers=list(answers))], "form", RULES, 10)[0]
    assert entry.puqe_score == score and puqe_band(entry, RULES) == band
    assert ("L2-05" in assess([entry], 10, RULES).matched_rules) == (score >= 13)


# ---- test 9: notes are never read ----


def test_notes_never_change_the_level_but_add_the_notice() -> None:
    alarming = "bleeding fits chest pain fainting severe emergency"
    result = run(item("fatigue", severity="mild", duration="under_1_hour", notes=alarming))
    assert result.level == "L0" and result.matched_rules == []
    assert result.message_keys == ["msg_level0_logged", "msg_notes_not_read"]


# ---- test 10 (engine side): V1 / V2; V3 fallback value ----


@pytest.mark.parametrize(
    ("items", "code", "field"),
    [
        ([], "V1", "entries"),
        ([item("headache", duration="under_1_hour")], "V1", "entries.0.severity"),
        ([item("headache", severity="mild")], "V1", "entries.0.duration"),
        ([item("abdominal_discomfort", severity="mild", duration="under_1_hour")], "V1",
         "entries.0.body_area"),
        ([item("nausea_vomiting")], "V1", "entries.0.puqe_answers"),
        ([item("labour_pains")], "V1", "entries.0.duration"),
        ([item("other", severity="mild", duration="under_1_hour")], "V1", "entries.0.name"),
        ([item("appetite_change")], "V1", "entries.0.appetite"),
        ([item("dizziness")], "V2", "entries.0.symptom"),
        ([item("headache", severity="extreme", duration="under_1_hour")], "V2",
         "entries.0.severity"),
        ([item("fatigue", severity="mild", duration="a_week")], "V2", "entries.0.duration"),
        ([item("abdominal_discomfort", severity="mild", duration="under_1_hour",
               body_area="back")], "V2", "entries.0.body_area"),
        ([item("nausea_vomiting", puqe_answers=[1, 2])], "V2", "entries.0.puqe_answers"),
        ([item("nausea_vomiting", puqe_answers=[1, 2, 6])], "V2", "entries.0.puqe_answers"),
        ([item("fits", severity="severe")], "V2", "entries.0.severity"),
        ([item("labour_pains", duration="under_1_hour")], "V2", "entries.0.duration"),
        ([item("food_craving", food="x" * 101)], "V2", "entries.0.food"),
        ([item("fatigue", severity="mild", duration="under_1_hour", notes="x" * 501)], "V2",
         "entries.0.notes"),
        ([item("fits"), item("fits")], "V2", "entries.1.symptom"),
        ([item("headache", severity="mild", duration="under_1_hour", with_swelling="yes")], "V2",
         "entries.0.with_swelling"),
    ],
)  # fmt: skip
def test_validation_codes(items: list[dict[str, Any]], code: str, field: str) -> None:
    with pytest.raises(CheckinError) as err:
        validate(items, "form", RULES, 20)
    assert (err.value.code, err.value.field) == (code, field)


def test_urgent_button_takes_warning_signs_only() -> None:
    assert run(item("fits"), source="urgent_button").level == "L1"
    with pytest.raises(CheckinError) as err:
        run(item("fatigue", severity="mild", duration="under_1_hour"), source="urgent_button")
    assert err.value.code == "V2"


def test_optional_details_are_kept() -> None:
    entries = validate(
        [
            item("food_craving", food="  Test food  "),
            item("other", name="Test", severity="mild", duration="under_1_hour"),
            item("appetite_change", appetite="less"),
            item("fatigue", severity="mild", duration="under_1_hour", notes="   "),
        ],
        "form",
        RULES,
        20,
    )
    assert entries[0].text == "Test food" and entries[1].body_area is None
    assert entries[2].choice == "less" and entries[3].notes is None  # blank notes are no notes


def test_safe_fallback_is_l2_with_err() -> None:
    assert (FALLBACK.level, FALLBACK.matched_rules, FALLBACK.message_keys) == (
        "L2",
        ["ERR"],
        ["msg_safe_fallback"],
    )


# ---- test 7: pattern changes P1-P5 (default settings and one changed setting) ----

NOW = datetime(2026, 11, 18, 10, 0, tzinfo=UTC)
TODAY = date(2026, 11, 18)


def past(
    key: str, days_ago: float, severity: str | None = "mild", band: str | None = None
) -> PastEntry:  # noqa: E501
    at = NOW - timedelta(days=days_ago)
    return PastEntry(key, severity, band, at, at.date())


def entry(symptom: str, **kw: Any) -> Entry:
    return Entry(symptom=symptom, **kw)


def codes(found: list[dict[str, str | None]]) -> list[str | None]:
    return [f["code"] for f in found]


def test_p1_first_time_ever() -> None:
    assert codes(pattern_changes([entry("fatigue", severity="mild")], "L0", History(), NOW, TODAY,
                                 RULES)) == ["P1"]  # fmt: skip
    seen = History(entries=[past("fatigue", 100)])
    assert pattern_changes([entry("fatigue", severity="mild")], "L0", seen, NOW, TODAY, RULES) == []
    # `other` compares by name, case-insensitive
    other = History(entries=[past("other:test pain", 30)])
    again = entry("other", severity="mild", text="TEST Pain")
    assert pattern_changes([again], "L0", other, NOW, TODAY, RULES) == []
    new_name = entry("other", severity="mild", text="Another")
    assert pattern_changes([new_name], "L0", other, NOW, TODAY, RULES) == [
        {"code": "P1", "symptom": "other:another"}
    ]
    # warning signs are not common symptoms
    assert pattern_changes([entry("fits")], "L1", History(), NOW, TODAY, RULES) == []


def test_p2_severity_higher_than_every_earlier_entry_in_the_window() -> None:
    hist = History(entries=[past("headache", 2, "mild"), past("headache", 1, "moderate")])
    up = entry("headache", severity="severe")
    assert codes(pattern_changes([up], "L2", hist, NOW, TODAY, RULES)) == ["P2"]
    same = entry("headache", severity="moderate")
    assert pattern_changes([same], "L0", hist, NOW, TODAY, RULES) == []
    old = History(entries=[past("headache", 10, "mild")])  # outside the 7-day window
    assert pattern_changes([up], "L2", old, NOW, TODAY, RULES) == []


def test_p3_logged_on_enough_days_in_the_window() -> None:
    four_days = History(entries=[past("back_pain", d) for d in (1, 2, 3, 4)])
    fifth = entry("back_pain", severity="mild")
    assert codes(pattern_changes([fifth], "L0", four_days, NOW, TODAY, RULES)) == ["P3"]
    three_days = History(entries=[past("back_pain", d) for d in (1, 2, 3)])
    assert pattern_changes([fifth], "L0", three_days, NOW, TODAY, RULES) == []
    # one changed setting: p3_min_days 3 makes four days enough
    changed = RULES.model_copy(
        update={"settings": RULES.settings.model_copy(update={"p3_min_days": 3})}
    )
    two_days = History(entries=[past("back_pain", d) for d in (1, 2)])
    assert codes(pattern_changes([fifth], "L0", two_days, NOW, TODAY, changed)) == ["P3"]


def test_p4_puqe_band_higher_than_the_previous_one() -> None:
    hist = History(entries=[past("nausea_vomiting", 3, None, "mild")])
    worse = entry("nausea_vomiting", puqe_answers=(3, 2, 2))  # 7 = moderate
    assert codes(pattern_changes([worse], "L0", hist, NOW, TODAY, RULES)) == ["P4"]
    same = entry("nausea_vomiting", puqe_answers=(2, 2, 2))  # 6 = mild
    assert pattern_changes([same], "L0", hist, NOW, TODAY, RULES) == []


def test_p5_enough_l2_checkins_in_the_window() -> None:
    one_before = History(l2_checkins=[NOW - timedelta(days=2)])
    assert codes(pattern_changes([entry("severe_itching")], "L2", one_before, NOW, TODAY,
                                 RULES)) == ["P5"]  # fmt: skip
    assert pattern_changes([entry("severe_itching")], "L2", History(), NOW, TODAY, RULES) == []
    old = History(l2_checkins=[NOW - timedelta(days=9)])
    assert pattern_changes([entry("severe_itching")], "L2", old, NOW, TODAY, RULES) == []
    changed = RULES.model_copy(
        update={"settings": RULES.settings.model_copy(update={"p5_min_l2": 1})}
    )
    assert codes(pattern_changes([entry("fits")], "L2", History(), NOW, TODAY, changed)) == ["P5"]


def test_every_rule_in_the_rule_file_has_a_test_here() -> None:
    """§14 test 1 guard: adding a rule without a test in this file fails the build."""
    import re
    from pathlib import Path

    named = set(re.findall(r"L[12]-\d\d", Path(__file__).read_text(encoding="utf-8")))
    assert {r.id for r in RULES.rules} <= named
