"""Symptom engine (Symptom spec §5-10). Pure functions: no database, no clock unless passed in.

Safety-critical: every rule in rules/symptoms/red_flags.yaml has its own test
(tests/unit/test_symptom_engine.py). The engine never reads notes (§1.2) and never relaxes a
rule by pregnancy stage (§7.4). A week rule with no known week counts as a match (§1.3).
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Literal

from app.modules.symptoms.rules import CommonSymptom, Condition, SymptomRules

Level = Literal["L0", "L1", "L2"]
LEVEL_MESSAGE = {
    "L1": "msg_level1_go_now",
    "L2": "msg_level2_contact_today",
    "L0": "msg_level0_logged",
}
_RANK = {"L0": 0, "L2": 1, "L1": 2}
_SEVERITY_RANK = {"mild": 0, "moderate": 1, "severe": 2}
_BAND_RANK = {"mild": 0, "moderate": 1, "severe": 2}
FLAG_FIELDS = ("with_vision_problems", "with_swelling", "unable_to_keep_fluids")


class CheckinError(ValueError):
    """§6 V1 (missing) or V2 (not allowed). `field` names the input, e.g. entries.0.severity."""

    def __init__(self, code: Literal["V1", "V2"], field: str) -> None:
        super().__init__(f"{code} on {field}")
        self.code = code
        self.field = field


@dataclass(frozen=True)
class Entry:
    """One validated symptom entry (§2). `text` is the craving food or the `other` name."""

    symptom: str
    severity: str | None = None
    duration: str | None = None
    body_area: str | None = None
    flags: frozenset[str] = frozenset()
    puqe_answers: tuple[int, int, int] | None = None
    text: str | None = None
    choice: str | None = None
    occurred_at: time | None = None
    notes: str | None = None  # stored, never read by the rules (§1.2)

    @property
    def puqe_score(self) -> int | None:
        return sum(self.puqe_answers) if self.puqe_answers else None

    def pattern_key(self) -> str:
        """P1-P3 compare `other` entries by their text name, case-insensitive (§9)."""
        if self.symptom == "other" and self.text:
            return f"other:{self.text.strip().lower()}"
        return self.symptom


@dataclass(frozen=True)
class Assessment:
    level: Level
    matched_rules: list[str]
    message_keys: list[str]


# ---- §5.2 / §5.5 which warning signs are offered ----


def offered_warning_ids(rules: SymptomRules, week: int | None) -> list[str]:
    """Warning signs offered at this pregnancy week. A week-gated sign is offered from its week
    on, or whenever the week is unknown (§5.2, §14 test 3, DEC-065)."""
    offered = []
    for s in rules.vocabulary.warning:
        from_week = getattr(rules.settings, s.from_week_setting) if s.from_week_setting else None
        if from_week is None or week is None or week >= from_week:
            offered.append(s.id)
    return offered


# ---- §6 validation (V1 / V2) ----


def validate(raw: Sequence[dict[str, object]], source: str, rules: SymptomRules,
             week: int | None) -> list[Entry]:  # fmt: skip
    """Turn submitted entries into Entry objects, or raise CheckinError (nothing is saved)."""
    if not raw:
        raise CheckinError("V1", "entries")
    vocab = rules.vocabulary
    common = {s.id: s for s in vocab.common}
    warning_offered = set(offered_warning_ids(rules, week))
    warning_all = {s.id: s for s in vocab.warning}
    seen: set[str] = set()
    entries = []
    for i, item in enumerate(raw):
        at = f"entries.{i}"
        symptom = item.get("symptom")
        if not isinstance(symptom, str) or (symptom not in common and symptom not in warning_all):
            raise CheckinError("V2", f"{at}.symptom")
        if source == "urgent_button" and symptom in common:  # urgent page: warning signs only
            raise CheckinError("V2", f"{at}.symptom")
        if symptom in warning_all and symptom not in warning_offered:
            raise CheckinError("V2", f"{at}.symptom")
        if symptom != "other" and symptom in seen:  # each symptom once per check-in
            raise CheckinError("V2", f"{at}.symptom")
        seen.add(symptom)
        if symptom in common:
            entries.append(_common_entry(item, common[symptom], rules, at))
        else:
            entries.append(_warning_entry(item, warning_all[symptom].labour_duration, rules, at))
    return entries


def _only(item: dict[str, object], allowed: set[str], at: str) -> None:
    for key, value in item.items():
        if key not in allowed and value is not None and value is not False:
            raise CheckinError("V2", f"{at}.{key}")  # a detail this symptom does not ask for


def _pick(item: dict[str, object], key: str, allowed: dict[str, str] | Sequence[str],
          required: bool, at: str) -> str | None:  # fmt: skip
    value = item.get(key)
    if value is None:
        if required:
            raise CheckinError("V1", f"{at}.{key}")
        return None
    if not isinstance(value, str) or value not in allowed:
        raise CheckinError("V2", f"{at}.{key}")
    return value


def _shared(item: dict[str, object], at: str) -> tuple[time | None, str | None]:
    """§5.3 optional time of occurrence and notes (max 500, never read by the rules)."""
    occurred = item.get("occurred_at")
    if occurred is not None and not isinstance(occurred, time):
        raise CheckinError("V2", f"{at}.occurred_at")
    notes = item.get("notes")
    if notes is not None and (not isinstance(notes, str) or len(notes) > 500):
        raise CheckinError("V2", f"{at}.notes")
    return occurred, (notes.strip() or None) if isinstance(notes, str) else None


def _common_entry(item: dict[str, object], spec: CommonSymptom, rules: SymptomRules,
                  at: str) -> Entry:  # fmt: skip
    vocab = rules.vocabulary
    allowed = {"symptom", "occurred_at", "notes", *spec.flags}
    severity = duration = body_area = text = choice = None
    if spec.severity:
        allowed.add("severity")
        severity = _pick(item, "severity", vocab.severities, True, at)
    if spec.duration:
        allowed.add("duration")
        duration = _pick(item, "duration", vocab.durations, True, at)
    if spec.body_area:
        allowed.add("body_area")
        body_area = _pick(item, "body_area", spec.body_area.choices, spec.body_area.required, at)
    if spec.text:
        allowed.add(spec.text.field)
        raw_text = item.get(spec.text.field)
        if raw_text is not None and not isinstance(raw_text, str):
            raise CheckinError("V2", f"{at}.{spec.text.field}")
        text = raw_text.strip() if isinstance(raw_text, str) else ""
        if spec.text.required and not text:
            raise CheckinError("V1", f"{at}.{spec.text.field}")
        if len(text) > spec.text.max_length:
            raise CheckinError("V2", f"{at}.{spec.text.field}")
        text = text or None
    if spec.choice:
        allowed.add(spec.choice.field)
        choice = _pick(item, spec.choice.field, spec.choice.options, True, at)
    puqe = None
    if spec.puqe:
        allowed.add("puqe_answers")
        answers = item.get("puqe_answers")
        if answers is None:
            raise CheckinError("V1", f"{at}.puqe_answers")
        if (
            not isinstance(answers, (list, tuple))
            or len(answers) != 3
            or not all(type(a) is int and 1 <= a <= 5 for a in answers)
        ):
            raise CheckinError("V2", f"{at}.puqe_answers")
        puqe = (answers[0], answers[1], answers[2])
    flags = set()
    for flag in spec.flags:
        value = item.get(flag)
        if value is not None and not isinstance(value, bool):
            raise CheckinError("V2", f"{at}.{flag}")
        if value:
            flags.add(flag)
    _only(item, allowed, at)
    occurred, notes = _shared(item, at)
    return Entry(
        symptom=spec.id,
        severity=severity,
        duration=duration,
        body_area=body_area,
        flags=frozenset(flags),
        puqe_answers=puqe,
        text=text,
        choice=choice,
        occurred_at=occurred,
        notes=notes,
    )


def _warning_entry(item: dict[str, object], labour: bool, rules: SymptomRules,
                   at: str) -> Entry:  # fmt: skip
    allowed = {"symptom", "occurred_at", "notes"}
    duration = None
    if labour:  # §5.4: labour pains ask their own duration range
        allowed.add("duration")
        duration = _pick(item, "duration", rules.vocabulary.labour_durations, True, at)
    _only(item, allowed, at)
    occurred, notes = _shared(item, at)
    return Entry(symptom=str(item["symptom"]), duration=duration, occurred_at=occurred, notes=notes)


# ---- §7 red-flag rules ----


def _week_ok(cond: Condition, week: int | None, rules: SymptomRules) -> bool:
    if week is None:  # §1.3: a rule that cannot be evaluated counts as matching
        return True
    s = rules.settings
    if cond.week_below and not week < getattr(s, cond.week_below):
        return False
    return not (cond.week_at_least and not week >= getattr(s, cond.week_at_least))


def _matching_entries(cond: Condition, entries: list[Entry], week: int | None,
                      rules: SymptomRules) -> set[int]:  # fmt: skip
    present = {e.symptom for e in entries}
    if cond.with_symptom and cond.with_symptom not in present:
        return set()
    if cond.without_symptom and cond.without_symptom in present:
        return set()
    if (cond.week_below or cond.week_at_least) and not _week_ok(cond, week, rules):
        return set()
    hits = set()
    for i, e in enumerate(entries):
        if e.symptom != cond.symptom:
            continue
        if cond.any_flag and not (e.flags & set(cond.any_flag)):
            continue
        if cond.severity and e.severity != cond.severity:
            continue
        if cond.duration and e.duration != cond.duration:
            continue
        if cond.puqe_at_least is not None and (e.puqe_score or 0) < cond.puqe_at_least:
            continue
        hits.add(i)
    return hits


def assess(entries: list[Entry], week: int | None, rules: SymptomRules) -> Assessment:
    """§7.1: collect every matching rule; the level is the highest matched (L1 > L2 > L0)."""
    matched: dict[str, set[int]] = {}
    ordered = sorted(
        rules.rules,
        key=lambda r: (r.when.catch_all_severity is not None, bool(r.when.unless_rules)),
    )  # plain rules first, then "unless" rules, then the catch-all
    for rule in ordered:
        cond = rule.when
        if cond.catch_all_severity:
            covered = set().union(*matched.values()) if matched else set()
            hits = {
                i
                for i, e in enumerate(entries)
                if e.severity == cond.catch_all_severity and i not in covered
            }
        elif any(r in matched for r in cond.unless_rules):
            hits = set()
        else:
            hits = _matching_entries(cond, entries, week, rules)
        if hits:
            matched[rule.id] = hits
    ids = [r.id for r in rules.rules if r.id in matched]  # file (= spec) order
    level: Level = "L0"
    for rule in rules.rules:
        if rule.id in matched and _RANK[rule.level] > _RANK[level]:
            level = rule.level
    return Assessment(level, ids, message_keys(level, entries))


def message_keys(level: Level, entries: list[Entry]) -> list[str]:
    """§11.2 / §7.5: the level message, plus mood support and the notes notice when they apply."""
    keys = [LEVEL_MESSAGE[level]]
    if any(e.symptom == "mood_change" for e in entries):
        keys.append("msg_mood_support")
    if any(e.notes for e in entries):
        keys.append("msg_notes_not_read")
    return keys


FALLBACK = Assessment("L2", ["ERR"], ["msg_safe_fallback"])  # §6 V3


# ---- §8 PUQE and §9 pattern changes ----


def puqe_band(entry: Entry, rules: SymptomRules) -> str | None:
    score = entry.puqe_score
    return rules.puqe.band_for(score) if score is not None else None


@dataclass(frozen=True)
class PastEntry:
    key: str  # Entry.pattern_key()
    severity: str | None
    puqe_band: str | None
    created_at: datetime
    local_day: date


@dataclass(frozen=True)
class History:
    entries: list[PastEntry] = field(default_factory=list)  # oldest first
    l2_checkins: list[datetime] = field(default_factory=list)


def pattern_changes(entries: list[Entry], level: Level, history: History, now: datetime,
                    today: date, rules: SymptomRules) -> list[dict[str, str | None]]:  # fmt: skip
    """§9 P1-P5 for a new check-in (doctor only). Returns [{code, symptom}], symptom null for P5."""
    s = rules.settings
    window_start = now - timedelta(days=s.pattern_window_days)
    common_ids = {c.id for c in rules.vocabulary.common}
    found: list[dict[str, str | None]] = []

    def add(code: str, symptom: str | None) -> None:
        item = {"code": code, "symptom": symptom}
        if item not in found:
            found.append(item)

    for e in entries:
        if e.symptom not in common_ids:
            continue
        key = e.pattern_key()
        earlier = [p for p in history.entries if p.key == key]
        if not earlier:
            add("P1", key)
        recent = [p for p in earlier if p.created_at >= window_start and p.severity]
        if (
            e.severity
            and recent  # P2 compares with earlier entries; none in the window -> no change
            and all(_SEVERITY_RANK[e.severity] > _SEVERITY_RANK[str(p.severity)] for p in recent)
        ):
            add("P2", key)
        days = {p.local_day for p in earlier if p.created_at >= window_start} | {today}
        if len(days) >= s.p3_min_days:
            add("P3", key)
        band = puqe_band(e, rules)
        previous = [p.puqe_band for p in history.entries if p.puqe_band]
        if band and previous and _BAND_RANK[band] > _BAND_RANK[previous[-1]]:
            add("P4", key)
    # P5 is a plain count, computed after every check-in (this one included when it is L2)
    l2_count = sum(t >= window_start for t in history.l2_checkins) + (level == "L2")
    if l2_count >= s.p5_min_l2:
        add("P5", None)
    return found
