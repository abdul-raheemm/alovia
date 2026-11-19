"""Loads and checks backend/rules/genetic/*.yaml (Genetic spec §5-7, §11.4, §12).

Every file is checked at startup and cross-checked against the others; the rule tables must
cover every input combination exactly once (§7.1 coverage check). A wrong file stops the backend
(ARCHITECTURE.md §12), so a broken inheritance rule can never reach a patient.
"""

from functools import lru_cache
from itertools import combinations_with_replacement, product
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.common.rule_texts import Message

RULES_DIR = Path(__file__).resolve().parents[3] / "rules" / "genetic"
Condition = Literal["haemoglobin_group", "haemophilia", "marfan"]
CONDITIONS: tuple[Condition, ...] = ("haemoglobin_group", "haemophilia", "marfan")
Chance = Literal["1_in_2", "1_in_4", "all_children", "not_expected", "not_calculable"]
RuleStatus = Literal["calculated", "needs_testing_or_counselling", "counselling_flag"]
PERCENT: dict[str, int | None] = {  # §8.2: never 0
    "1_in_2": 50,
    "1_in_4": 25,
    "all_children": 100,
    "not_expected": None,
    "not_calculable": None,
}
REQUIRED_MESSAGES = {
    "review_with_doctor", "results_after_review", "msg_sent_for_review",
    "msg_counselling_flag", "msg_needs_testing", "msg_not_assessed",
    "msg_hplc_test_suggested", "msg_partner_test_suggested",
    "msg_haemophilia_carrier_test_suggested", "msg_marfan_assessment_suggested",
    "msg_consanguinity_counselling", "msg_speak_to_doctor_soon", "msg_safe_fallback",
    "result_hbb_calculated", "result_hem_calculated", "result_mar_calculated",
    "warn_blood_count_not_enough", "warn_family_history_not_enough",
    "warn_card_checks_sickle_only", "warn_carrier_depends_on_partner",
    "note_carrier_girls_may_bleed", "note_no_family_history_not_no_risk",
    "note_new_cases_can_occur", "note_severity_varies", "disclaimer_main",
}  # fmt: skip


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class GeneticSettings(_Strict):
    rules_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    show_result_before_review: bool


class Outcome(_Strict):
    outcome: str
    chance: Chance
    names_condition: bool = False  # names a condition, not a carrier state (§9.4)


class _Rule(_Strict):
    status: RuleStatus
    warnings: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    confirm: str | None = None  # [CONFIRM AT RULE REVIEW] assumption id
    sources: tuple[str, ...] = ()

    def outcome_lists(self) -> list[tuple[Outcome, ...] | None]:
        return []

    @model_validator(mode="after")
    def outcomes_only_when_calculated(self) -> _Rule:
        lists = self.outcome_lists()
        if self.status == "calculated" and not all(lists):
            raise ValueError("a calculated rule needs its outcomes")
        if self.status != "calculated" and any(lists):
            raise ValueError("only calculated rules have outcomes (§8.2)")
        return self


class HbbRule(_Rule):
    id: str = Field(pattern=r"^HBB-\d\d$")
    pairs: tuple[tuple[str, str], ...] = Field(min_length=1)
    outcomes: tuple[Outcome, ...] | None = None

    def outcome_lists(self) -> list[tuple[Outcome, ...] | None]:
        return [self.outcomes]


class HaemoglobinFile(_Strict):
    statuses: dict[str, tuple[str, str]]  # value -> (short code, label)
    rules: tuple[HbbRule, ...]

    @model_validator(mode="after")
    def every_pair_exactly_once(self) -> HaemoglobinFile:
        codes = [code for code, _ in self.statuses.values()]
        if len(codes) != 9 or len(set(codes)) != 9:
            raise ValueError("the haemoglobin group has 9 distinct codes (§5.1)")
        seen: dict[frozenset[str], str] = {}
        for rule in self.rules:
            for a, b in rule.pairs:
                if a not in codes or b not in codes:
                    raise ValueError(f"{rule.id}: unknown code in {a}+{b}")
                key = frozenset((a, b))
                if key in seen:
                    raise ValueError(f"{a}+{b} is in both {seen[key]} and {rule.id}")
                seen[key] = rule.id
        missing = [f"{a}+{b}" for a, b in combinations_with_replacement(codes, 2)
                   if frozenset((a, b)) not in seen]  # fmt: skip
        if missing:
            raise ValueError(f"pairs without a rule: {missing}")
        return self

    def code(self, status: str) -> str:
        return self.statuses[status][0]


class HemRule(_Rule):
    id: str = Field(pattern=r"^HEM-\d\d$")
    mother: str
    father: str  # a status or "any"
    if_boy: tuple[Outcome, ...] | None = None
    if_girl: tuple[Outcome, ...] | None = None

    def outcome_lists(self) -> list[tuple[Outcome, ...] | None]:
        return [self.if_boy, self.if_girl]  # always both or neither (§11.3)


class HaemophiliaStatuses(_Strict):
    mother: dict[str, str]
    father: dict[str, str]


class HaemophiliaFile(_Strict):
    statuses: HaemophiliaStatuses
    father_api_only: tuple[str, ...]
    rules: tuple[HemRule, ...]

    @model_validator(mode="after")
    def every_form_combination_exactly_once(self) -> HaemophiliaFile:
        for mother, father in product(self.statuses.mother, self.statuses.father):
            hits = [r.id for r in self.rules if r.mother == mother and r.father in (father, "any")]
            if len(hits) != 1:
                raise ValueError(f"mother {mother} + father {father}: {len(hits)} rules match")
        for r in self.rules:
            if r.mother not in self.statuses.mother:
                raise ValueError(f"{r.id}: unknown mother status")
            if r.father != "any" and r.father not in self.statuses.father:
                raise ValueError(f"{r.id}: unknown father status")
        return self


class MarRule(_Rule):
    id: str = Field(pattern=r"^MAR-\d\d$")
    pair: tuple[str, str]  # a status or "any"; the order of parents does not matter
    outcomes: tuple[Outcome, ...] | None = None

    def outcome_lists(self) -> list[tuple[Outcome, ...] | None]:
        return [self.outcomes]

    def matches(self, a: str, b: str) -> bool:
        x, y = self.pair

        def ok(rule: str, value: str) -> bool:
            return rule in ("any", value)

        return (ok(x, a) and ok(y, b)) or (ok(x, b) and ok(y, a))


class MarfanFile(_Strict):
    statuses: dict[str, str]
    rules: tuple[MarRule, ...]

    @model_validator(mode="after")
    def every_pair_exactly_once(self) -> MarfanFile:
        for a, b in combinations_with_replacement(self.statuses, 2):
            hits = [r.id for r in self.rules if r.matches(a, b)]
            if len(hits) != 1:
                raise ValueError(f"{a} + {b}: {len(hits)} rules match")
        return self


class EvidenceKind(_Strict):
    label: str
    strength: Literal["strong", "weak"]
    conditions: tuple[Condition, ...]
    haemoglobin_statuses: tuple[str, ...] | None = None  # only with these statuses


class EvidenceRule(_Strict):
    evidence: str
    condition: Condition | None = None
    status: str | None = None
    treat_as: Literal["unknown"]
    warning: str


class EvidenceFile(_Strict):
    conditions: tuple[Condition, ...]
    evidence: dict[str, EvidenceKind]
    handling: tuple[EvidenceRule, ...]


class ConflictWhen(_Strict):
    previous_child: Literal["yes", "no", "not_sure", "no_previous_child"] | None = None
    any_parent: tuple[str, ...] = ()
    mother: tuple[str, ...] = ()
    father: tuple[str, ...] = ()
    both_parents: tuple[str, ...] = ()


class ConflictRule(_Strict):
    id: str = Field(pattern=r"^[CF]\d$")
    condition: Condition
    spec: str
    when: ConflictWhen
    status: Literal["conflict", "counselling_flag"]


class ConflictsFile(_Strict):
    conflicts: tuple[ConflictRule, ...]
    errors: dict[str, str]


class Labels(_Strict):
    conditions: dict[Condition, str]
    entry_question: str
    entry_answers: dict[str, str]
    previous_child_question: str
    previous_child_answers: dict[str, str]
    question_names: dict[Condition, str]
    consanguinity_question: str
    consanguinity_answers: dict[str, str]
    outcomes: dict[str, str]
    chances: dict[Chance, str]


class GeneticRules(_Strict):
    settings: GeneticSettings
    haemoglobin: HaemoglobinFile
    haemophilia: HaemophiliaFile
    marfan: MarfanFile
    evidence: EvidenceFile
    conflicts: ConflictsFile
    messages: dict[str, Message]
    labels: Labels

    @model_validator(mode="after")
    def cross_checks(self) -> GeneticRules:
        if set(self.messages) != REQUIRED_MESSAGES:
            raise ValueError("messages.yaml must hold exactly the §11.4 keys")
        rules: list[_Rule] = [*self.haemoglobin.rules, *self.haemophilia.rules, *self.marfan.rules]
        for r in rules:
            for key in (*r.warnings, *r.notes):
                if key not in self.messages:
                    raise ValueError(f"unknown message key {key}")
            for outcomes in r.outcome_lists():
                for o in outcomes or ():
                    if o.outcome not in self.labels.outcomes:
                        raise ValueError(f"no label for outcome {o.outcome}")
        if set(self.labels.chances) != set(PERCENT):
            raise ValueError("labels.yaml needs a label for every chance")
        hbb_statuses = set(self.haemoglobin.statuses)
        for name, kind in self.evidence.evidence.items():
            if kind.haemoglobin_statuses and not set(kind.haemoglobin_statuses) <= hbb_statuses:
                raise ValueError(f"{name}: unknown haemoglobin status")
        for h in self.evidence.handling:
            if h.evidence not in self.evidence.evidence or h.warning not in self.messages:
                raise ValueError(f"evidence handling for {h.evidence} names something unknown")
        ids = [c.id for c in self.conflicts.conflicts]
        if len(ids) != len(set(ids)):
            raise ValueError("conflict ids must be unique")
        if set(self.conflicts.errors) != {"E3", "E4"}:
            raise ValueError("conflicts.yaml lists the E3 and E4 errors")
        return self

    def statuses(self, condition: Condition, parent: str) -> set[str]:
        """Statuses allowed on the form for one parent (§5.1-5.3)."""
        if condition == "haemoglobin_group":
            return set(self.haemoglobin.statuses)
        if condition == "marfan":
            return set(self.marfan.statuses)
        return set(getattr(self.haemophilia.statuses, parent))


def _yaml(directory: Path, name: str) -> dict[str, object]:
    data: dict[str, object] = yaml.safe_load((directory / name).read_text(encoding="utf-8"))
    return data


def parse_genetic_rules(directory: Path = RULES_DIR) -> GeneticRules:
    return GeneticRules.model_validate(
        {
            "settings": _yaml(directory, "config.yaml"),
            "haemoglobin": _yaml(directory, "haemoglobin_group.yaml"),
            "haemophilia": _yaml(directory, "haemophilia.yaml"),
            "marfan": _yaml(directory, "marfan.yaml"),
            "evidence": _yaml(directory, "evidence.yaml"),
            "conflicts": _yaml(directory, "conflicts.yaml"),
            "messages": _yaml(directory, "messages.yaml")["messages"],
            "labels": _yaml(directory, "labels.yaml"),
        }
    )


@lru_cache
def load_genetic_rules() -> GeneticRules:
    return parse_genetic_rules()
