# ruff: noqa: E501  -- expected tables are copied one row per line so they read like the spec
"""Genetic engine (Genetic spec §14 tests 1-9; test 10, the doctor correction, is Phase 5).
Safety-critical: the expected results below are typed from the spec tables, independently of
the rule files."""

import json
from itertools import combinations_with_replacement
from typing import Any

import pytest

from app.modules.genetic import engine
from app.modules.genetic.engine import GeneticInputError, assess, validate
from app.modules.genetic.rules import load_genetic_rules

RULES = load_genetic_rules()
CODE = {
    "N": "tested_negative", "B": "beta_thal_carrier", "S": "sickle_carrier", "E": "hbe_carrier",
    "D": "hbd_carrier", "BB": "beta_thal_major", "SS": "sickle_cell_disease",
    "O": "other_or_unclear", "U": "unknown",
}  # fmt: skip


def parent(status: str, evidence: str | None = "test_report") -> dict[str, Any]:
    return {"status": status} if status == "unknown" else {"status": status, "evidence": evidence}


def inputs(
    hbb: tuple[str, str] = ("tested_negative", "tested_negative"),
    hem: tuple[str, str] | None = None,
    mar: tuple[str, str] | None = None,
    consanguinity: str = "no",
    hbb_child: str = "no",
    hem_child: str = "no",
    mar_child: str = "no",
    evidence: tuple[str | None, str | None] = ("hplc_report", "hplc_report"),
) -> dict[str, Any]:
    def section(
        pair: tuple[str, str] | None, child: str, ev: tuple[str | None, str | None]
    ) -> dict[str, Any]:
        if pair is None:
            return {"entry": "no"}
        return {
            "entry": "yes",
            "mother": parent(pair[0], ev[0]),
            "father": parent(pair[1], ev[1]),
            "previous_child": child,
        }

    hbb_section = {
        "mother": parent(hbb[0], evidence[0]),
        "father": parent(hbb[1], evidence[1]),
        "previous_child": hbb_child,
    }
    return {
        "haemoglobin_group": hbb_section,
        "haemophilia": section(hem, hem_child, ("test_report", "test_report")),
        "marfan": section(mar, mar_child, ("test_report", "test_report")),
        "consanguinity": consanguinity,
    }


def run(raw: dict[str, Any]) -> engine.Assessment:
    return assess(validate(raw, RULES), RULES)


def condition(result: engine.Assessment, name: str) -> engine.ConditionResult:
    return next(c for c in result.conditions if c.condition == name)


def chances(outcomes: list[engine.OutcomeOut] | None) -> dict[str, str]:
    return {o.outcome: o.chance for o in outcomes or []}


# ---- test 1: one test per unordered haemoglobin pair (45) ----

# §7.1, typed from the spec: rule id -> its pairs; status and outcomes per rule
HBB_PAIRS = {
    "HBB-01": ["N+N"], "HBB-02": ["N+B"], "HBB-03": ["N+S"], "HBB-04": ["N+E"], "HBB-05": ["N+D"],
    "HBB-06": ["N+BB"], "HBB-07": ["N+SS"], "HBB-08": ["N+O"], "HBB-09": ["N+U"],
    "HBB-10": ["B+B"], "HBB-11": ["S+S"], "HBB-12": ["B+S"],
    "HBB-13": ["B+E", "B+D", "S+E", "S+D", "E+E", "E+D", "D+D"],
    "HBB-14": ["BB+B", "BB+S", "BB+E", "BB+D", "BB+BB", "BB+SS", "SS+B", "SS+S", "SS+E", "SS+D", "SS+SS"],
    "HBB-15": ["O+B", "O+S", "O+E", "O+D", "O+BB", "O+SS", "O+O"],
    "HBB-16": ["U+B", "U+S", "U+E", "U+D", "U+BB", "U+SS", "U+U"],
    "HBB-17": ["U+O"],
}  # fmt: skip
HBB_RESULT = {
    "HBB-01": ("calculated", {"affected": "not_expected", "carrier": "not_expected"}),
    "HBB-02": ("calculated", {"affected": "not_expected", "beta_thal_carrier": "1_in_2", "neither": "1_in_2"}),
    "HBB-03": ("calculated", {"affected": "not_expected", "sickle_carrier": "1_in_2", "neither": "1_in_2"}),
    "HBB-04": ("calculated", {"affected": "not_expected", "hbe_carrier": "1_in_2", "neither": "1_in_2"}),
    "HBB-05": ("calculated", {"affected": "not_expected", "hbd_carrier": "1_in_2", "neither": "1_in_2"}),
    "HBB-06": ("calculated", {"affected": "not_expected", "beta_thal_carrier": "all_children"}),
    "HBB-07": ("calculated", {"affected": "not_expected", "sickle_carrier": "all_children"}),
    "HBB-08": ("counselling_flag", {}),
    "HBB-09": ("calculated", {"affected": "not_expected", "carrier": "not_calculable"}),
    "HBB-10": ("calculated", {"beta_thal_major": "1_in_4", "beta_thal_carrier": "1_in_2", "neither": "1_in_4"}),
    "HBB-11": ("calculated", {"sickle_cell_disease": "1_in_4", "sickle_carrier": "1_in_2", "neither": "1_in_4"}),
    "HBB-12": ("calculated", {"sickle_cell_disease": "1_in_4", "beta_thal_carrier": "1_in_4", "sickle_carrier": "1_in_4", "neither": "1_in_4"}),
    "HBB-13": ("counselling_flag", {}),
    "HBB-14": ("counselling_flag", {}),
    "HBB-15": ("counselling_flag", {}),
    "HBB-16": ("needs_testing_or_counselling", {}),
    "HBB-17": ("counselling_flag", {}),
}  # fmt: skip
EXPECTED_PAIR = {
    frozenset(p.split("+")): rule_id for rule_id, pairs in HBB_PAIRS.items() for p in pairs
}
ALL_PAIRS = list(combinations_with_replacement(CODE, 2))


def test_the_spec_lists_45_distinct_pairs() -> None:
    assert len(ALL_PAIRS) == 45 and len(EXPECTED_PAIR) == 45


@pytest.mark.parametrize(("a", "b"), ALL_PAIRS, ids=[f"{a}+{b}" for a, b in ALL_PAIRS])
def test_haemoglobin_pair(a: str, b: str) -> None:
    rule_id = EXPECTED_PAIR[frozenset((a, b))]
    status, outcomes = HBB_RESULT[rule_id]
    for mother, father in {(a, b), (b, a)}:  # the order of parents does not matter
        r = condition(run(inputs(hbb=(CODE[mother], CODE[father]))), "haemoglobin_group")
        assert (r.rule_id, r.status, chances(r.outcomes)) == (rule_id, status, outcomes)
        if status != "calculated":
            assert r.outcomes is None and r.outcomes_if_boy is None and r.outcomes_if_girl is None
    if rule_id == "HBB-09":
        assert r.warnings == ["warn_carrier_depends_on_partner"]


# ---- test 2: every haemophilia row (boy and girl) and every Marfan row ----

HEM = [  # mother, father, rule, status, if boy, if girl, notes
    ("tested_negative", "not_affected", "HEM-01", "calculated", {"haemophilia": "not_expected"}, {"carrier": "not_expected"}, ["note_no_family_history_not_no_risk"]),
    ("carrier", "not_affected", "HEM-02", "calculated", {"haemophilia": "1_in_2", "unaffected": "1_in_2"}, {"carrier": "1_in_2", "neither": "1_in_2", "haemophilia": "not_expected"}, ["note_carrier_girls_may_bleed"]),
    ("tested_negative", "affected", "HEM-03", "calculated", {"haemophilia": "not_expected"}, {"carrier": "all_children"}, ["note_carrier_girls_may_bleed"]),
    ("carrier", "affected", "HEM-04", "counselling_flag", {}, {}, []),
    ("affected", "affected", "HEM-05", "counselling_flag", {}, {}, []),
    ("affected", "not_affected", "HEM-05", "counselling_flag", {}, {}, []),
    ("unknown", "not_affected", "HEM-06", "needs_testing_or_counselling", {}, {}, []),
    ("unknown", "affected", "HEM-07", "needs_testing_or_counselling", {}, {}, []),
]  # fmt: skip


@pytest.mark.parametrize(("mother", "father", "rule_id", "status", "boy", "girl", "notes"), HEM)
def test_haemophilia_row(
    mother: str,
    father: str,
    rule_id: str,
    status: str,
    boy: dict[str, str],
    girl: dict[str, str],
    notes: list[str],
) -> None:
    r = condition(run(inputs(hem=(mother, father))), "haemophilia")
    assert (r.rule_id, r.status, r.notes) == (rule_id, status, notes)
    assert chances(r.outcomes_if_boy) == boy and chances(r.outcomes_if_girl) == girl
    assert r.outcomes is None
    # §11.3: boy and girl always together, never one alone
    assert (r.outcomes_if_boy is None) == (r.outcomes_if_girl is None)


MAR = [  # parents, rule, status, outcomes, notes
    (("not_affected", "not_affected"), "MAR-01", "calculated", {"inherits_from_parent": "not_expected"}, ["note_new_cases_can_occur"]),
    (("affected", "not_affected"), "MAR-02", "calculated", {"inherits_condition": "1_in_2"}, ["note_severity_varies"]),
    (("not_affected", "affected"), "MAR-02", "calculated", {"inherits_condition": "1_in_2"}, ["note_severity_varies"]),
    (("affected", "affected"), "MAR-03", "counselling_flag", {}, []),
    (("unknown", "affected"), "MAR-04", "needs_testing_or_counselling", {}, []),
    (("not_affected", "unknown"), "MAR-04", "needs_testing_or_counselling", {}, []),
    (("unknown", "unknown"), "MAR-04", "needs_testing_or_counselling", {}, []),
]  # fmt: skip


@pytest.mark.parametrize(("parents", "rule_id", "status", "outcomes", "notes"), MAR)
def test_marfan_row(
    parents: tuple[str, str], rule_id: str, status: str, outcomes: dict[str, str], notes: list[str]
) -> None:
    r = condition(run(inputs(mar=parents)), "marfan")
    assert (r.rule_id, r.status, chances(r.outcomes), r.notes) == (rule_id, status, outcomes, notes)


# ---- test 3: every evidence rule and every conflict / error code ----


def test_blood_count_only_is_treated_as_unknown() -> None:
    raw = inputs(
        hbb=("beta_thal_carrier", "beta_thal_carrier"), evidence=("blood_count_only", "hplc_report")
    )
    r = condition(run(raw), "haemoglobin_group")
    assert (r.rule_id, r.status) == ("HBB-16", "needs_testing_or_counselling")  # U + B
    assert "warn_blood_count_not_enough" in r.warnings


@pytest.mark.parametrize(
    ("which", "rule_id"),
    [("haemoglobin_group", "HBB-09"), ("haemophilia", "HEM-06"), ("marfan", "MAR-04")],
)  # the mother counts as unknown: U + N, unknown + not_affected, unknown + not_affected
def test_family_history_only_is_treated_as_unknown(which: str, rule_id: str) -> None:
    raw = inputs(hem=("carrier", "not_affected"), mar=("affected", "not_affected"))
    raw[which]["mother"]["evidence"] = "family_history_only"
    r = condition(run(raw), which)
    assert r.rule_id == rule_id
    assert "warn_family_history_not_enough" in r.warnings


def test_sickle_card_with_tested_negative_is_unknown_A1() -> None:
    raw = inputs(
        hbb=("tested_negative", "tested_negative"), evidence=("sickle_status_card", "hplc_report")
    )
    r = condition(run(raw), "haemoglobin_group")
    assert (r.rule_id, r.status) == ("HBB-09", "calculated")  # U + N: no carrier number
    assert "warn_card_checks_sickle_only" in r.warnings
    carrier_card = inputs(
        hbb=("sickle_carrier", "tested_negative"), evidence=("sickle_status_card", "hplc_report")
    )
    assert (
        condition(run(carrier_card), "haemoglobin_group").rule_id == "HBB-03"
    )  # card is strong for sickle status


def test_c1_previous_child_affected_but_a_parent_tested_negative() -> None:
    r = condition(
        run(inputs(hbb=("tested_negative", "beta_thal_carrier"), hbb_child="yes")),
        "haemoglobin_group",
    )
    assert (r.rule_id, r.status, r.outcomes) == ("C1", "conflict", None)
    assert r.message_keys[0] == "msg_sent_for_review"


@pytest.mark.parametrize("father", ["carrier", "unknown"])
def test_c2_father_carrier_or_unknown_through_the_api(father: str) -> None:
    r = condition(run(inputs(hem=("carrier", father))), "haemophilia")
    assert (r.rule_id, r.status) == ("C2", "conflict")
    assert r.outcomes_if_boy is None and r.outcomes_if_girl is None


def test_f1_previous_son_and_mother_tested_negative() -> None:
    r = condition(
        run(inputs(hem=("tested_negative", "not_affected"), hem_child="yes")), "haemophilia"
    )
    assert (r.rule_id, r.status) == ("F1", "counselling_flag")  # beats HEM-01 calculated (§6.4)


def test_f2_previous_child_marfan_and_both_not_affected() -> None:
    r = condition(run(inputs(mar=("not_affected", "not_affected"), mar_child="yes")), "marfan")
    assert (r.rule_id, r.status, r.outcomes) == ("F2", "counselling_flag", None)


def test_e3_no_rule_row_matches() -> None:
    without = RULES.model_copy(
        update={"haemoglobin": RULES.haemoglobin.model_copy(
            update={"rules": tuple(r for r in RULES.haemoglobin.rules if r.id != "HBB-10")}
        )}
    )  # fmt: skip
    raw = inputs(hbb=("beta_thal_carrier", "beta_thal_carrier"))
    r = condition(assess(validate(raw, RULES), without), "haemoglobin_group")
    assert (r.rule_id, r.status, r.outcomes) == ("E3", "error", None)


def test_e4_unexpected_failure_is_an_error_never_a_number(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(*_: Any) -> Any:
        raise RuntimeError("test failure")

    monkeypatch.setattr(engine, "_rule_for", broken)
    result = run(inputs(hem=("carrier", "not_affected")))
    for r in result.conditions:
        if r.condition != "marfan":  # Marfan was not assessed (entry "no")
            assert (r.rule_id, r.status, r.message_keys) == ("E4", "error", ["msg_safe_fallback"])
            assert r.outcomes is None and r.outcomes_if_boy is None


# ---- test 4: priority order (§6.4) ----


def test_priority_order() -> None:
    # conflict beats a calculated rule (C1 vs HBB-09)
    c1 = condition(
        run(inputs(hbb=("tested_negative", "unknown"), hbb_child="yes")), "haemoglobin_group"
    )
    assert c1.status == "conflict"
    # counselling_flag beats calculated (F1 vs HEM-01), see above; needs_testing beats nothing higher
    f2 = condition(run(inputs(mar=("not_affected", "not_affected"), mar_child="yes")), "marfan")
    assert f2.status == "counselling_flag"
    assert [
        engine._PRIORITY[s]
        for s in (
            "error",
            "conflict",
            "counselling_flag",
            "needs_testing_or_counselling",
            "calculated",
            "not_assessed",
        )
    ] == [5, 4, 3, 2, 1, 0]


# ---- test 5: entry question "no" ----


def test_entry_no_is_not_assessed() -> None:
    result = run(inputs())
    for name in ("haemophilia", "marfan"):
        r = condition(result, name)
        assert (r.status, r.rule_id, r.message_keys) == ("not_assessed", None, ["msg_not_assessed"])


def test_entry_not_sure_shows_the_form_and_allows_unknowns() -> None:
    raw = inputs()
    raw["marfan"] = {
        "entry": "not_sure",
        "mother": {"status": "unknown"},
        "father": {"status": "unknown"},
        "previous_child": "not_sure",
    }
    assert condition(run(raw), "marfan").rule_id == "MAR-04"


# ---- test 6: consanguinity ----


@pytest.mark.parametrize(("answer", "flag"), [("yes", True), ("not_sure", False)])
def test_consanguinity_adds_a_message_and_never_changes_numbers(answer: str, flag: bool) -> None:
    base = run(inputs(hbb=("beta_thal_carrier", "tested_negative")))
    asked = run(inputs(hbb=("beta_thal_carrier", "tested_negative"), consanguinity=answer))
    assert asked.flags.consanguinity is flag
    assert "msg_consanguinity_counselling" in asked.message_keys
    assert "msg_consanguinity_counselling" not in base.message_keys
    assert asked.conditions == base.conditions  # numbers unchanged


# ---- test 7: timing prompt and priority exactly when risk is indicated (§9.4) ----


@pytest.mark.parametrize(
    ("raw", "risk"),
    [
        (inputs(hbb=("beta_thal_carrier", "beta_thal_carrier")), True),   # HBB-10: a condition at 1 in 4
        (inputs(hbb=("beta_thal_carrier", "tested_negative")), False),    # HBB-02: carrier only
        (inputs(hbb=("tested_negative", "beta_thal_major")), False),      # HBB-06: all children carriers only
        (inputs(hbb=("unknown", "sickle_carrier")), True),                # HBB-16: other parent a carrier
        (inputs(hbb=("unknown", "unknown")), False),                      # HBB-16: no known carrier
        (inputs(hbb=("hbe_carrier", "hbe_carrier")), True),               # HBB-13: counselling flag
        (inputs(hem=("carrier", "not_affected")), True),                  # HEM-02: haemophilia 1 in 2 (boy)
        (inputs(hem=("tested_negative", "affected")), False),             # HEM-03: girls carriers only
        (inputs(hem=("unknown", "affected")), True),                      # HEM-07: other parent affected
        (inputs(hem=("unknown", "not_affected")), False),                 # HEM-06
        (inputs(mar=("affected", "not_affected")), True),                 # MAR-02
        (inputs(mar=("unknown", "affected")), True),                      # MAR-04, other parent affected
        (inputs(mar=("unknown", "not_affected")), False),                 # MAR-04
        (inputs(hbb=("tested_negative", "unknown"), hbb_child="yes"), True),  # C1 conflict
    ],
)  # fmt: skip
def test_timing_prompt_and_priority_exactly_when_risk(raw: dict[str, Any], risk: bool) -> None:
    result = run(raw)
    assert result.flags.risk_indicated is risk and result.flags.timing_prompt is risk
    assert result.priority == ("high" if risk else "normal")
    assert ("msg_speak_to_doctor_soon" in result.message_keys) is risk


# ---- test 8: show_result_before_review ----


@pytest.mark.parametrize(
    ("setting", "message"), [(True, "review_with_doctor"), (False, "results_after_review")]
)
def test_show_result_before_review(setting: bool, message: str) -> None:
    rules = RULES.model_copy(
        update={
            "settings": RULES.settings.model_copy(update={"show_result_before_review": setting})
        }
    )
    result = assess(validate(inputs(hbb=("beta_thal_carrier", "tested_negative")), rules), rules)
    assert result.show_numbers_to_patient is setting and message in result.message_keys


# ---- test 9: never percent 0, never a field for the baby's sex ----


def test_no_percent_zero_and_no_sex_field_anywhere() -> None:
    outputs = [run(inputs(hbb=(CODE[a], CODE[b]))) for a, b in ALL_PAIRS]
    outputs += [run(inputs(hem=(m, f))) for m, f, *_ in HEM]
    outputs += [run(inputs(mar=p)) for p, *_ in MAR]
    for out in outputs:
        dumped = out.model_dump()
        text = json.dumps(dumped)
        assert '"percent": 0' not in text
        keys = set(re_keys(dumped))
        assert not {k for k in keys if "sex" in k or k in {"gender", "baby_is"}}
        for c in out.conditions:
            for o in [*(c.outcomes or []), *(c.outcomes_if_boy or []), *(c.outcomes_if_girl or [])]:
                assert o.percent in (50, 25, 100, None)
                assert (o.percent is None) == (o.chance in ("not_expected", "not_calculable"))


def re_keys(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [k for k, v in value.items() for k in [k, *re_keys(v)]]
    if isinstance(value, list):
        return [k for v in value for k in re_keys(v)]
    return []


# ---- testing nudges (§9.3) ----


@pytest.mark.parametrize(
    ("raw", "which", "key"),
    [
        (inputs(hbb=("unknown", "tested_negative")), "haemoglobin_group", "msg_hplc_test_suggested"),
        (inputs(hbb=("sickle_carrier", "unknown")), "haemoglobin_group", "msg_partner_test_suggested"),
        (inputs(hem=("unknown", "not_affected")), "haemophilia", "msg_haemophilia_carrier_test_suggested"),
        (inputs(mar=("not_affected", "unknown")), "marfan", "msg_marfan_assessment_suggested"),
    ],
)  # fmt: skip
def test_testing_nudges(raw: dict[str, Any], which: str, key: str) -> None:
    assert key in condition(run(raw), which).message_keys


# ---- §6.1 validation E1 / E2 ----


def broken(path: str, value: Any) -> dict[str, Any]:
    raw = inputs(hem=("carrier", "not_affected"))
    *head, last = path.split(".")
    node: Any = raw
    for part in head:
        node = node[part]
    if value is ...:
        del node[last]
    else:
        node[last] = value
    return raw


@pytest.mark.parametrize(
    ("raw", "code", "field"),
    [
        (broken("consanguinity", ...), "E1", "consanguinity"),
        (broken("haemoglobin_group.previous_child", ...), "E1", "haemoglobin_group.previous_child"),
        (broken("haemoglobin_group.mother.evidence", ...), "E1", "haemoglobin_group.mother.evidence"),
        (broken("haemophilia.entry", ...), "E1", "haemophilia.entry"),
        (broken("haemophilia.father", ...), "E1", "haemophilia.father"),  # no default answer (DEC-069)
        (broken("haemoglobin_group.mother.status", "beta_thal_minor"), "E2", "haemoglobin_group.mother.status"),
        (broken("haemoglobin_group.mother.evidence", "rumour"), "E2", "haemoglobin_group.mother.evidence"),
        (broken("haemophilia.mother.evidence", "hplc_report"), "E2", "haemophilia.mother.evidence"),  # HPLC: haemoglobin only
        (broken("haemophilia.father.status", "maybe"), "E2", "haemophilia.father.status"),
        (broken("haemophilia.entry", "perhaps"), "E2", "haemophilia.entry"),
        (broken("consanguinity", True), "E2", "consanguinity"),
    ],
)  # fmt: skip
def test_validation_codes(raw: dict[str, Any], code: str, field: str) -> None:
    with pytest.raises(GeneticInputError) as err:
        validate(raw, RULES)
    assert (err.value.code, err.value.field) == (code, field)


def test_card_only_with_sickle_statuses_and_no_evidence_with_unknown() -> None:
    raw = inputs(
        hbb=("beta_thal_carrier", "tested_negative"), evidence=("sickle_status_card", "hplc_report")
    )
    with pytest.raises(GeneticInputError) as err:
        validate(raw, RULES)
    assert (err.value.code, err.value.field) == ("E2", "haemoglobin_group.mother.evidence")
    unknown_with_evidence = inputs()
    unknown_with_evidence["haemoglobin_group"]["father"] = {
        "status": "unknown",
        "evidence": "hplc_report",
    }
    with pytest.raises(GeneticInputError):
        validate(unknown_with_evidence, RULES)
    entry_no_with_answers = inputs()
    entry_no_with_answers["marfan"]["mother"] = {"status": "affected", "evidence": "test_report"}
    with pytest.raises(GeneticInputError) as err:
        validate(entry_no_with_answers, RULES)
    assert err.value.field == "marfan.mother"


def test_every_rule_conflict_and_error_id_has_a_test_here() -> None:
    """§14 guard: adding a rule row or conflict without a test in this file fails the build."""
    import re
    from pathlib import Path

    named = set(
        re.findall(r"(?:HBB|HEM|MAR)-\d\d|\b[CFE]\d\b", Path(__file__).read_text(encoding="utf-8"))
    )
    ids = {r.id for r in (*RULES.haemoglobin.rules, *RULES.haemophilia.rules, *RULES.marfan.rules)}
    ids |= {c.id for c in RULES.conflicts.conflicts} | set(RULES.conflicts.errors)
    assert ids <= named, ids - named
