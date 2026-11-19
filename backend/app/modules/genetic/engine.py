"""Genetic risk engine (Genetic spec §5-9). Pure functions: no database, no clock.

Safety-critical: a missing number is always safer than a wrong number (§1.3). Every rule row,
evidence rule and conflict has its own test (tests/unit/test_genetic_engine.py). The engine
never asks for, infers or returns the baby's sex (§11.3), and never returns percent 0 (§8.2).
"""

from typing import Any, Literal

from pydantic import BaseModel

from app.modules.genetic.rules import (
    CONDITIONS,
    PERCENT,
    Condition,
    ConflictRule,
    GeneticRules,
    Outcome,
)

Status = Literal[
    "calculated",
    "needs_testing_or_counselling",
    "counselling_flag",
    "conflict",
    "error",
    "not_assessed",
]
_PRIORITY: dict[str, int] = {  # §6.4: the highest wins
    "error": 5,
    "conflict": 4,
    "counselling_flag": 3,
    "needs_testing_or_counselling": 2,
    "calculated": 1,
    "not_assessed": 0,
}
_STATUS_MESSAGE = {
    "needs_testing_or_counselling": "msg_needs_testing",
    "counselling_flag": "msg_counselling_flag",
    "conflict": "msg_sent_for_review",
    "not_assessed": "msg_not_assessed",
}
_CALCULATED_MESSAGE = {
    "haemoglobin_group": "result_hbb_calculated",
    "haemophilia": "result_hem_calculated",
    "marfan": "result_mar_calculated",
}
_ANSWERS = ("yes", "no", "not_sure")
_PREVIOUS_CHILD = ("yes", "no", "not_sure", "no_previous_child")
_RISK_CHANCES = ("1_in_2", "1_in_4", "all_children")
# haemoglobin statuses that make a parent "a carrier or affected" (§9.3, §9.4)
_HBB_CARRIER_OR_AFFECTED = {
    "beta_thal_carrier", "sickle_carrier", "hbe_carrier", "hbd_carrier",
    "beta_thal_major", "sickle_cell_disease",
}  # fmt: skip


class GeneticInputError(ValueError):
    """§6.1 E1 (missing) or E2 (not allowed). `field` names the input, e.g. haemophilia.entry."""

    def __init__(self, code: Literal["E1", "E2"], field: str) -> None:
        super().__init__(f"{code} on {field}")
        self.code = code
        self.field = field


class OutcomeOut(BaseModel):
    outcome: str
    chance: str
    percent: int | None  # 50 / 25 / 100, or null; never 0 (§8.2)


class ConditionResult(BaseModel):
    condition: Condition
    rule_id: str | None  # the rule row, or the conflict / error code that decided the status
    status: Status
    outcomes: list[OutcomeOut] | None = None
    outcomes_if_boy: list[OutcomeOut] | None = None
    outcomes_if_girl: list[OutcomeOut] | None = None
    message_keys: list[str] = []
    warnings: list[str] = []
    notes: list[str] = []


class Flags(BaseModel):
    consanguinity: bool
    risk_indicated: bool
    timing_prompt: bool


class Assessment(BaseModel):
    """§8.2 output (without the id and timestamps the service adds)."""

    rules_version: str
    review_status: Literal["pending_review", "reviewed"]
    priority: Literal["normal", "high"]
    show_numbers_to_patient: bool
    conditions: list[ConditionResult]
    flags: Flags
    message_keys: list[str]  # messages for the whole assessment (consanguinity, timing, review)
    disclaimer_key: str = "disclaimer_main"


# ---- §6.1 validation ----


def _pick(value: Any, allowed: set[str] | tuple[str, ...], field: str) -> str:
    if value is None:
        raise GeneticInputError("E1", field)
    if not isinstance(value, str) or value not in allowed:
        raise GeneticInputError("E2", field)
    return value


def _parent(
    raw: Any, condition: Condition, who: str, rules: GeneticRules, at: str
) -> dict[str, str]:
    """One parent's status and evidence (§5.1-5.4). Evidence is required except for unknown."""
    if not isinstance(raw, dict):
        raise GeneticInputError("E1", at)
    allowed = rules.statuses(condition, who)
    if condition == "haemophilia" and who == "father":
        allowed = allowed | set(rules.haemophilia.father_api_only)  # C2 can be reported (DEC-068)
    status = _pick(raw.get("status"), allowed, f"{at}.status")
    evidence = raw.get("evidence")
    if status == "unknown":
        if evidence is not None:
            raise GeneticInputError("E2", f"{at}.evidence")
        return {"status": status}
    kind = rules.evidence.evidence.get(
        _pick(evidence, set(rules.evidence.evidence), f"{at}.evidence")
    )
    assert kind is not None
    if condition not in kind.conditions or (
        kind.haemoglobin_statuses is not None and status not in kind.haemoglobin_statuses
    ):
        raise GeneticInputError("E2", f"{at}.evidence")  # §5.4 "allowed with"
    return {"status": status, "evidence": str(evidence)}


def validate(raw: dict[str, Any], rules: GeneticRules) -> dict[str, Any]:
    """Check the submitted answers (§6.1). Returns the cleaned inputs, or raises E1/E2."""
    clean: dict[str, Any] = {}
    for condition in CONDITIONS:
        section = raw.get(condition)
        if not isinstance(section, dict):
            raise GeneticInputError("E1", condition)
        out: dict[str, Any] = {}
        if condition == "haemoglobin_group" and section.get("entry") is not None:
            raise GeneticInputError("E2", f"{condition}.entry")  # always assessed (§5.5)
        if condition != "haemoglobin_group":  # §5.5 entry question first
            out["entry"] = _pick(section.get("entry"), _ANSWERS, f"{condition}.entry")
            if out["entry"] == "no":
                for key in ("mother", "father", "previous_child"):
                    if section.get(key) is not None:
                        raise GeneticInputError("E2", f"{condition}.{key}")  # not asked
                clean[condition] = out
                continue
        for who in ("mother", "father"):
            out[who] = _parent(section.get(who), condition, who, rules, f"{condition}.{who}")
        out["previous_child"] = _pick(
            section.get("previous_child"), _PREVIOUS_CHILD, f"{condition}.previous_child"
        )
        clean[condition] = out
    clean["consanguinity"] = _pick(raw.get("consanguinity"), _ANSWERS, "consanguinity")
    return clean


# ---- §6.2 evidence handling, §6.3 conflicts ----


def _effective(
    parent: dict[str, str], condition: Condition, rules: GeneticRules
) -> tuple[str, list[str]]:
    """Weak evidence is treated as unknown before the rule tables (§6.2)."""
    status, evidence = parent["status"], parent.get("evidence")
    for h in rules.evidence.handling:
        if (
            h.evidence == evidence
            and h.condition in (None, condition)
            and h.status in (None, status)
        ):
            return h.treat_as, [h.warning]
    return status, []


def _conflict_matches(c: ConflictRule, mother: str, father: str, previous_child: str) -> bool:
    w = c.when
    return (
        (w.previous_child is None or w.previous_child == previous_child)
        and (not w.any_parent or mother in w.any_parent or father in w.any_parent)
        and (not w.mother or mother in w.mother)
        and (not w.father or father in w.father)
        and (not w.both_parents or (mother in w.both_parents and father in w.both_parents))
    )


# ---- §7 rule tables ----


def _outcomes(items: tuple[Outcome, ...] | None) -> list[OutcomeOut] | None:
    if items is None:
        return None
    return [
        OutcomeOut(outcome=o.outcome, chance=o.chance, percent=PERCENT[o.chance]) for o in items
    ]


def _rule_for(condition: Condition, mother: str, father: str, rules: GeneticRules) -> Any:
    """The rule row for these (effective) statuses, or None (-> E3)."""
    if condition == "haemoglobin_group":
        hb = rules.haemoglobin
        pair = frozenset((hb.code(mother), hb.code(father)))
        return next((r for r in hb.rules if any(frozenset(p) == pair for p in r.pairs)), None)
    if condition == "haemophilia":
        return next(
            (r for r in rules.haemophilia.rules
             if r.mother == mother and r.father in (father, "any")),
            None,
        )  # fmt: skip
    return next((r for r in rules.marfan.rules if r.matches(mother, father)), None)


def _nudges(condition: Condition, mother: str, father: str) -> list[str]:
    """§9.3 testing nudges (on the effective statuses)."""
    if condition == "haemoglobin_group":
        if mother == "unknown":
            return ["msg_hplc_test_suggested"]
        if mother in _HBB_CARRIER_OR_AFFECTED and father == "unknown":
            return ["msg_partner_test_suggested"]
        return []
    if condition == "haemophilia":
        return ["msg_haemophilia_carrier_test_suggested"] if mother == "unknown" else []
    return ["msg_marfan_assessment_suggested"] if "unknown" in (mother, father) else []


def _other_parent_carrier_or_affected(condition: Condition, mother: str, father: str) -> bool:
    """§9.4 third bullet: needs_testing where the other parent is a carrier or affected."""
    if condition == "haemoglobin_group":
        return bool({mother, father} & _HBB_CARRIER_OR_AFFECTED)
    if condition == "haemophilia":
        known = father if mother == "unknown" else mother
        return known in ("carrier", "affected")
    known = father if mother == "unknown" else mother
    return known == "affected"


def assess_condition(
    condition: Condition, section: dict[str, Any], rules: GeneticRules
) -> tuple[ConditionResult, bool]:
    """One condition's result, and whether it indicates risk (§9.4)."""
    if section.get("entry") == "no":  # §5.5
        return ConditionResult(
            condition=condition, rule_id=None, status="not_assessed",
            message_keys=["msg_not_assessed"],
        ), False  # fmt: skip
    mother, w1 = _effective(section["mother"], condition, rules)
    father, w2 = _effective(section["father"], condition, rules)
    warnings = list(dict.fromkeys(w1 + w2))
    candidates: list[tuple[str, str]] = [  # (status, id) that apply; the highest wins (§6.4)
        (c.status, c.id)
        for c in rules.conflicts.conflicts
        if c.condition == condition
        and _conflict_matches(c, mother, father, section["previous_child"])
    ]
    rule = _rule_for(condition, mother, father, rules)
    if rule is not None:
        candidates.append((rule.status, rule.id))
    elif not any(s == "conflict" for s, _ in candidates):
        candidates.append(("error", "E3"))  # no rule row matches
    status, decided_by = max(candidates, key=lambda c: _PRIORITY[c[0]])
    result = ConditionResult(
        condition=condition,
        rule_id=decided_by,
        status=status,
        warnings=warnings,
    )
    if status == "calculated":
        if condition == "haemophilia":  # always both together (§11.3)
            result.outcomes_if_boy = _outcomes(rule.if_boy)
            result.outcomes_if_girl = _outcomes(rule.if_girl)
        else:
            result.outcomes = _outcomes(rule.outcomes)
        result.warnings = list(dict.fromkeys(warnings + list(rule.warnings)))
        result.notes = list(rule.notes)
        result.message_keys = [_CALCULATED_MESSAGE[condition]]
    elif status == "error":
        result.message_keys = ["msg_sent_for_review"]
    else:
        result.message_keys = [_STATUS_MESSAGE[status]]
    result.message_keys += [
        k for k in _nudges(condition, mother, father) if k not in result.message_keys
    ]
    # §9.4 "risk indicated", exactly
    named_risk = status == "calculated" and any(
        o.names_condition and o.chance in _RISK_CHANCES
        for o in (
            *(getattr(rule, "outcomes", None) or ()),
            *(getattr(rule, "if_boy", None) or ()),
            *(getattr(rule, "if_girl", None) or ()),
        )
    )
    risk = (
        named_risk
        or status in ("counselling_flag", "conflict")
        or (
            status == "needs_testing_or_counselling"
            and _other_parent_carrier_or_affected(condition, mother, father)
        )
    )
    return result, risk


def assess(inputs: dict[str, Any], rules: GeneticRules) -> Assessment:
    """Run every condition on validated inputs and add the §9 prompts and flags."""
    results: list[ConditionResult] = []
    risk = False
    for condition in CONDITIONS:
        try:
            r, condition_risk = assess_condition(condition, inputs[condition], rules)
            risk = risk or condition_risk
        except Exception:  # §6.3 E4: any unexpected engine failure -> error, never a number
            r = ConditionResult(
                condition=condition, rule_id="E4", status="error",
                message_keys=["msg_safe_fallback"],
            )  # fmt: skip
        results.append(r)
    messages: list[str] = []
    if inputs["consanguinity"] in ("yes", "not_sure"):  # §9.1: a message only, numbers unchanged
        messages.append("msg_consanguinity_counselling")
    if risk:  # §9.2
        messages.append("msg_speak_to_doctor_soon")
    show = rules.settings.show_result_before_review
    if any(r.status == "calculated" for r in results):
        messages.append("review_with_doctor" if show else "results_after_review")
    return Assessment(
        rules_version=rules.settings.rules_version,
        review_status="pending_review",
        priority="high" if risk else "normal",
        show_numbers_to_patient=show,
        conditions=results,
        flags=Flags(
            consanguinity=inputs["consanguinity"] == "yes", risk_indicated=risk, timing_prompt=risk
        ),
        message_keys=messages,
    )
