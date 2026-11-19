# ruff: noqa: E501  -- spec tables are copied one row per line so they read like the spec
"""The shipped genetic rule files match the spec tables row for row (Genetic spec §0 rule 4,
§7), and broken files are refused at startup."""

import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.modules.genetic.rules import RULES_DIR, load_genetic_rules, parse_genetic_rules

RULES = load_genetic_rules()


def outcomes(rule: object, field: str = "outcomes") -> dict[str, str]:
    return {o.outcome: o.chance for o in getattr(rule, field) or ()}


# §7.1: rule id -> (number of pairs, status, outcomes) copied from the spec table
SPEC_HBB = {
    "HBB-01": (1, "calculated", {"affected": "not_expected", "carrier": "not_expected"}),
    "HBB-02": (1, "calculated", {"affected": "not_expected", "beta_thal_carrier": "1_in_2", "neither": "1_in_2"}),
    "HBB-03": (1, "calculated", {"affected": "not_expected", "sickle_carrier": "1_in_2", "neither": "1_in_2"}),
    "HBB-04": (1, "calculated", {"affected": "not_expected", "hbe_carrier": "1_in_2", "neither": "1_in_2"}),
    "HBB-05": (1, "calculated", {"affected": "not_expected", "hbd_carrier": "1_in_2", "neither": "1_in_2"}),
    "HBB-06": (1, "calculated", {"affected": "not_expected", "beta_thal_carrier": "all_children"}),
    "HBB-07": (1, "calculated", {"affected": "not_expected", "sickle_carrier": "all_children"}),
    "HBB-08": (1, "counselling_flag", {}),
    "HBB-09": (1, "calculated", {"affected": "not_expected", "carrier": "not_calculable"}),
    "HBB-10": (1, "calculated", {"beta_thal_major": "1_in_4", "beta_thal_carrier": "1_in_2", "neither": "1_in_4"}),
    "HBB-11": (1, "calculated", {"sickle_cell_disease": "1_in_4", "sickle_carrier": "1_in_2", "neither": "1_in_4"}),
    "HBB-12": (1, "calculated", {"sickle_cell_disease": "1_in_4", "beta_thal_carrier": "1_in_4",
                                 "sickle_carrier": "1_in_4", "neither": "1_in_4"}),
    "HBB-13": (7, "counselling_flag", {}),
    "HBB-14": (11, "counselling_flag", {}),
    "HBB-15": (7, "counselling_flag", {}),
    "HBB-16": (7, "needs_testing_or_counselling", {}),
    "HBB-17": (1, "counselling_flag", {}),
}  # fmt: skip

# §7.2: rule id -> (mother, father, status, if boy, if girl, notes)
SPEC_HEM = {
    "HEM-01": ("tested_negative", "not_affected", "calculated", {"haemophilia": "not_expected"},
               {"carrier": "not_expected"}, ("note_no_family_history_not_no_risk",)),
    "HEM-02": ("carrier", "not_affected", "calculated",
               {"haemophilia": "1_in_2", "unaffected": "1_in_2"},
               {"carrier": "1_in_2", "neither": "1_in_2", "haemophilia": "not_expected"},
               ("note_carrier_girls_may_bleed",)),
    "HEM-03": ("tested_negative", "affected", "calculated", {"haemophilia": "not_expected"},
               {"carrier": "all_children"}, ("note_carrier_girls_may_bleed",)),
    "HEM-04": ("carrier", "affected", "counselling_flag", {}, {}, ()),
    "HEM-05": ("affected", "any", "counselling_flag", {}, {}, ()),
    "HEM-06": ("unknown", "not_affected", "needs_testing_or_counselling", {}, {}, ()),
    "HEM-07": ("unknown", "affected", "needs_testing_or_counselling", {}, {}, ()),
}  # fmt: skip

# §7.3: rule id -> (pair, status, outcomes, notes)
SPEC_MAR = {
    "MAR-01": (("not_affected", "not_affected"), "calculated",
               {"inherits_from_parent": "not_expected"}, ("note_new_cases_can_occur",)),
    "MAR-02": (("affected", "not_affected"), "calculated", {"inherits_condition": "1_in_2"},
               ("note_severity_varies",)),
    "MAR-03": (("affected", "affected"), "counselling_flag", {}, ()),
    "MAR-04": (("unknown", "any"), "needs_testing_or_counselling", {}, ()),
}  # fmt: skip


def test_haemoglobin_table_matches_the_spec() -> None:
    shipped = {r.id: (len(r.pairs), r.status, outcomes(r)) for r in RULES.haemoglobin.rules}
    assert shipped == SPEC_HBB
    assert sum(n for n, _, _ in SPEC_HBB.values()) == 45  # §7.1 coverage check
    codes = {s: c for s, (c, _) in RULES.haemoglobin.statuses.items()}
    assert codes == {
        "tested_negative": "N", "beta_thal_carrier": "B", "sickle_carrier": "S",
        "hbe_carrier": "E", "hbd_carrier": "D", "beta_thal_major": "BB",
        "sickle_cell_disease": "SS", "other_or_unclear": "O", "unknown": "U",
    }  # fmt: skip
    hbb09 = next(r for r in RULES.haemoglobin.rules if r.id == "HBB-09")
    assert hbb09.warnings == ("warn_carrier_depends_on_partner",)
    assumptions = {r.id: r.confirm for r in RULES.haemoglobin.rules if r.confirm}
    assert assumptions == {"HBB-04": "A2", "HBB-05": "A2", "HBB-06": "A4", "HBB-07": "A4"}


def test_haemophilia_table_matches_the_spec() -> None:
    shipped = {
        r.id: (r.mother, r.father, r.status, outcomes(r, "if_boy"), outcomes(r, "if_girl"), r.notes)
        for r in RULES.haemophilia.rules
    }
    assert shipped == SPEC_HEM
    assert set(RULES.haemophilia.statuses.mother) == {
        "tested_negative",
        "carrier",
        "affected",
        "unknown",
    }
    assert set(RULES.haemophilia.statuses.father) == {"affected", "not_affected"}  # §5.2
    assert RULES.haemophilia.father_api_only == ("carrier", "unknown")  # for C2 only


def test_marfan_table_matches_the_spec() -> None:
    shipped = {r.id: (r.pair, r.status, outcomes(r), r.notes) for r in RULES.marfan.rules}
    assert shipped == SPEC_MAR
    assert set(RULES.marfan.statuses) == {"affected", "not_affected", "unknown"}


def test_evidence_and_conflicts_match_the_spec() -> None:
    ev = RULES.evidence.evidence
    assert {k: (v.strength, v.conditions) for k, v in ev.items()} == {
        "hplc_report": ("strong", ("haemoglobin_group",)),
        "sickle_status_card": ("strong", ("haemoglobin_group",)),
        "test_report": ("strong", ("haemoglobin_group", "haemophilia", "marfan")),
        "doctor_told": ("strong", ("haemoglobin_group", "haemophilia", "marfan")),
        "blood_count_only": ("weak", ("haemoglobin_group",)),
        "family_history_only": ("weak", ("haemoglobin_group", "haemophilia", "marfan")),
    }
    assert ev["sickle_status_card"].haemoglobin_statuses == (
        "tested_negative", "sickle_carrier", "sickle_cell_disease",
    )  # fmt: skip
    assert [(h.evidence, h.status, h.warning) for h in RULES.evidence.handling] == [
        ("blood_count_only", None, "warn_blood_count_not_enough"),
        ("family_history_only", None, "warn_family_history_not_enough"),
        ("sickle_status_card", "tested_negative", "warn_card_checks_sickle_only"),
    ]
    assert [(c.id, c.condition, c.status) for c in RULES.conflicts.conflicts] == [
        ("C1", "haemoglobin_group", "conflict"),
        ("C2", "haemophilia", "conflict"),
        ("F1", "haemophilia", "counselling_flag"),
        ("F2", "marfan", "counselling_flag"),
    ]


def test_settings_and_messages() -> None:
    assert RULES.settings.rules_version == "1.0.0"
    assert RULES.settings.show_result_before_review is True  # D4 default
    pending = {k for k, m in RULES.messages.items() if m.text is None}
    assert pending == set(RULES.messages) - {"disclaimer_main"}
    assert RULES.messages["disclaimer_main"].text == (
        "This is for knowledge only and is not medical advice. Counselling is recommended."
    )  # §11.2, word for word


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
        ("haemoglobin_group.yaml", "pairs: [[U, O]]", "pairs: [[U, B]]", "both"),  # duplicate
        ("haemoglobin_group.yaml", "pairs: [[N, O]]", "pairs: [[N, N]]", "both"),
        ("haemoglobin_group.yaml", "[O, O]]", "[O, E]]", "both"),
        ("haemoglobin_group.yaml", "    pairs: [[U, O]]\n", "    pairs: [[N, X]]\n", "unknown code"),
        ("haemoglobin_group.yaml", "status: counselling_flag\n    sources: []\n  - id: HBB-09",
         "status: calculated\n    sources: []\n  - id: HBB-09", "needs its outcomes"),
        ("haemophilia.yaml", "father: any", "father: affected", "rules match"),
        ("marfan.yaml", "pair: [affected, affected]", "pair: [affected, not_affected]", "rules match"),
        ("messages.yaml", "  note_severity_varies:", "  note_other:", "§11.4 keys"),
        ("labels.yaml", "  neither: \"Neither\"\n", "", "no label"),
        ("config.yaml", "show_result_before_review: true", "show_result_before_review: maybe", "bool"),
    ],
)  # fmt: skip
def test_broken_rule_files_are_refused(
    tmp_path: Path, name: str, old: str, new: str, match: str
) -> None:
    with pytest.raises(ValidationError, match=match):
        parse_genetic_rules(_broken(tmp_path, name, old, new))
