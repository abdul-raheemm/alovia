"""Loads and checks backend/rules/symptoms/*.yaml (Symptom spec §5, §7-9, §11, §13.2).

Every file is checked at startup and cross-checked against the others (a rule may only name a
symptom, flag, severity, duration or setting that exists). A wrong file stops the backend
(ARCHITECTURE.md §12), so a broken red-flag rule can never reach a patient.
"""

from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.common.rule_texts import Helpline, Message

RULES_DIR = Path(__file__).resolve().parents[3] / "rules" / "symptoms"
MAX_WEEKS = 42
REQUIRED_MESSAGES = {
    "msg_level1_go_now",
    "msg_level2_contact_today",
    "msg_level0_logged",
    "msg_mood_support",
    "msg_notes_not_read",
    "msg_not_monitored_live",
    "msg_safe_fallback",
    "msg_not_saved",  # DEC-109: a failed save keeps the draft
}
WeekSetting = Literal["movements_from_week", "never_felt_from_week", "preterm_before_week"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SymptomSettings(_Strict):
    """§13.2 settings (all [CONFIGURABLE])."""

    rules_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    pattern_window_days: int = Field(gt=0)
    p3_min_days: int = Field(gt=0)
    p5_min_l2: int = Field(gt=0)
    movements_from_week: int = Field(ge=0, le=MAX_WEEKS)
    never_felt_from_week: int = Field(ge=0, le=MAX_WEEKS)
    preterm_before_week: int = Field(ge=0, le=MAX_WEEKS)
    draft_ttl_minutes: int = Field(gt=0)  # DEC-109

    @model_validator(mode="after")
    def window_holds_p3(self) -> SymptomSettings:
        if self.p3_min_days > self.pattern_window_days:
            raise ValueError("p3_min_days cannot exceed pattern_window_days")
        return self


class TextDetail(_Strict):
    field: str
    label: str
    required: bool
    max_length: int = Field(gt=0)


class ChoiceDetail(_Strict):
    field: str
    options: dict[str, str] = Field(min_length=2)


class BodyAreaDetail(_Strict):
    required: bool
    choices: tuple[str, ...] = Field(min_length=1)


class CommonSymptom(_Strict):
    """§5.1 everyday symptom and the details it asks for."""

    id: str
    label: str
    puqe: bool = False
    flags: dict[str, str] = {}
    severity: bool = False
    duration: bool = False
    body_area: BodyAreaDetail | None = None
    text: TextDetail | None = None
    choice: ChoiceDetail | None = None


class WarningSymptom(_Strict):
    """§5.2 warning sign: selecting is enough (labour pains also ask a duration)."""

    id: str
    label: str
    from_week_setting: WeekSetting | None = None  # offered from this week, or week unknown
    labour_duration: bool = False


class Vocabulary(_Strict):
    severities: dict[str, str]
    durations: dict[str, str]
    labour_durations: dict[str, str]
    body_areas: dict[str, str]
    common: tuple[CommonSymptom, ...]
    warning: tuple[WarningSymptom, ...]

    @model_validator(mode="after")
    def consistent(self) -> Vocabulary:
        ids = [s.id for s in self.common] + [s.id for s in self.warning]
        if len(ids) != len(set(ids)):
            raise ValueError("symptom ids must be unique")
        if list(self.severities) != ["mild", "moderate", "severe"]:
            raise ValueError("severities must be mild, moderate, severe (§5.3)")
        for s in self.common:
            if s.body_area and not set(s.body_area.choices) <= set(self.body_areas):
                raise ValueError(f"{s.id}: unknown body area")
        return self

    def symptom_ids(self) -> set[str]:
        return {s.id for s in self.common} | {s.id for s in self.warning}

    def flags(self) -> set[str]:
        return {f for s in self.common for f in s.flags}


class Condition(_Strict):
    """How the engine checks one rule (§7). Unset parts are not checked."""

    symptom: str | None = None
    any_flag: tuple[str, ...] = ()
    severity: str | None = None
    duration: str | None = None
    with_symptom: str | None = None
    without_symptom: str | None = None
    week_below: WeekSetting | None = None  # week unknown counts as a match (§1.3)
    week_at_least: WeekSetting | None = None  # week unknown counts as a match (§1.3)
    puqe_at_least: int | None = Field(None, ge=3, le=15)
    unless_rules: tuple[str, ...] = ()
    catch_all_severity: str | None = None

    @model_validator(mode="after")
    def has_a_subject(self) -> Condition:
        if (self.symptom is None) == (self.catch_all_severity is None):
            raise ValueError("a rule names one symptom, or is the severity catch-all")
        return self


class Rule(_Strict):
    id: str = Field(pattern=r"^L[12]-\d\d$")
    level: Literal["L1", "L2"]
    spec: str
    sources: tuple[str, ...]
    when: Condition

    @model_validator(mode="after")
    def level_matches_id(self) -> Rule:
        if not self.id.startswith(self.level):
            raise ValueError(f"{self.id}: level must be {self.id[:2]}")
        return self


class PuqeSource(_Strict):
    publisher: str
    title: str
    url: str = Field(pattern=r"^https://")
    date_accessed: date


class PuqeQuestion(_Strict):
    id: str
    text: str
    answers: dict[int, str]

    @model_validator(mode="after")
    def five_answers(self) -> PuqeQuestion:
        if sorted(self.answers) != [1, 2, 3, 4, 5]:
            raise ValueError(f"{self.id}: answers must score 1-5")
        return self


class PuqeBand(_Strict):
    band: Literal["mild", "moderate", "severe"]
    min: int
    max: int


class Puqe(_Strict):
    source: PuqeSource
    questions: tuple[PuqeQuestion, ...] = Field(min_length=3, max_length=3)
    bands: tuple[PuqeBand, ...]

    @model_validator(mode="after")
    def bands_cover_3_to_15(self) -> Puqe:
        expected = 3
        for b in self.bands:
            if b.min != expected or b.max < b.min:
                raise ValueError("PUQE bands must cover 3-15 with no gap")
            expected = b.max + 1
        if expected != 16:
            raise ValueError("PUQE bands must end at 15")
        return self

    def band_for(self, score: int) -> str:
        return next(b.band for b in self.bands if b.min <= score <= b.max)


class Pattern(_Strict):
    code: Literal["P1", "P2", "P3", "P4", "P5"]
    spec: str
    settings: tuple[str, ...] = ()


class SymptomRules(_Strict):
    settings: SymptomSettings
    vocabulary: Vocabulary
    rules: tuple[Rule, ...]
    puqe: Puqe
    patterns: tuple[Pattern, ...]
    messages: dict[str, Message]
    helplines: tuple[Helpline, ...]

    @model_validator(mode="after")
    def cross_checks(self) -> SymptomRules:
        ids = [r.id for r in self.rules]
        if len(ids) != len(set(ids)):
            raise ValueError("rule ids must be unique")
        symptoms, flags = self.vocabulary.symptom_ids(), self.vocabulary.flags()
        durations = set(self.vocabulary.durations) | set(self.vocabulary.labour_durations)
        for r in self.rules:
            w = r.when
            for s in (w.symptom, w.with_symptom, w.without_symptom):
                if s is not None and s not in symptoms:
                    raise ValueError(f"{r.id}: unknown symptom {s}")
            if not set(w.any_flag) <= flags:
                raise ValueError(f"{r.id}: unknown flag")
            for sev in (w.severity, w.catch_all_severity):
                if sev is not None and sev not in self.vocabulary.severities:
                    raise ValueError(f"{r.id}: unknown severity {sev}")
            if w.duration is not None and w.duration not in durations:
                raise ValueError(f"{r.id}: unknown duration {w.duration}")
            if not set(w.unless_rules) <= set(ids):
                raise ValueError(f"{r.id}: unknown rule in unless_rules")
        if [p.code for p in self.patterns] != ["P1", "P2", "P3", "P4", "P5"]:
            raise ValueError("patterns must be P1-P5 in order")
        names = set(SymptomSettings.model_fields)
        if not all(set(p.settings) <= names for p in self.patterns):
            raise ValueError("a pattern names an unknown setting")
        if set(self.messages) != REQUIRED_MESSAGES:
            raise ValueError("messages.yaml must hold exactly the §11.2 keys")
        if {h.key for h in self.helplines} != {"emergency", "mental_health"}:
            raise ValueError("helplines need the emergency and mental_health numbers (§11.3)")
        return self

    def helpline(self, key: str) -> Helpline:
        return next(h for h in self.helplines if h.key == key)


def _yaml(directory: Path, name: str) -> dict[str, object]:
    data: dict[str, object] = yaml.safe_load((directory / name).read_text(encoding="utf-8"))
    return data


def parse_symptom_rules(directory: Path = RULES_DIR) -> SymptomRules:
    messages = _yaml(directory, "messages.yaml")
    return SymptomRules.model_validate(
        {
            "settings": _yaml(directory, "config.yaml"),
            "vocabulary": _yaml(directory, "symptoms.yaml"),
            "rules": _yaml(directory, "red_flags.yaml")["rules"],
            "puqe": _yaml(directory, "puqe.yaml"),
            "patterns": _yaml(directory, "patterns.yaml")["patterns"],
            "messages": messages["messages"],
            "helplines": messages["helplines"],
        }
    )


@lru_cache
def load_symptom_rules() -> SymptomRules:
    return parse_symptom_rules()
