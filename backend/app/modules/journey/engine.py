"""Pregnancy date calculations (Journey spec §5.1, §6, §4.5). Pure functions: no database,
no clock unless one is passed in. Every screen and later module reads the pregnancy week from
here, so each rule is tested at its boundaries (tests/unit/test_journey_engine.py).
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from app.modules.journey.config import MAX_WEEKS, MonthRange

PREGNANCY_DAYS = 280  # glossary: GA_days = 280 − (due_date − today)

HomeState = Literal["no_date", "active", "past_due", "beyond_42", "ended"]
MilestoneKind = Literal["new_week", "new_month", "new_trimester", "term", "due_date"]


@dataclass(frozen=True)
class GestationalAge:
    ga_days: int
    completed_weeks: int  # floor(GA_days / 7)
    days: int  # GA_days mod 7
    days_to_go: int | None  # due_date − today, only when > 0 (§6.1)
    content_week: int  # min(completed_weeks, 42)
    trimester: int
    month: int


@dataclass(frozen=True)
class Milestone:
    on: date
    kind: MilestoneKind
    value: int  # week, month or trimester number; 0 for the due date


def local_today(timezone: str, now: datetime | None = None) -> date:
    """The patient's local date (§6.1: Asia/Kolkata in v1, from config)."""
    moment = now if now is not None else datetime.now(ZoneInfo(timezone))
    return moment.astimezone(ZoneInfo(timezone)).date()


# §5.1 input options -> stored due date
def due_date_from_lmp(lmp: date) -> date:
    """Option A: LMP + 280 days (`lmp_estimate`)."""
    return lmp + timedelta(days=PREGNANCY_DAYS)


def due_date_from_ultrasound(scan_date: date, weeks: int, days: int) -> date:
    """Option C: scan date + (280 − GA at scan in days) (`ultrasound`)."""
    return scan_date + timedelta(days=PREGNANCY_DAYS - (weeks * 7 + days))


def gestational_age_days(due_date: date, today: date) -> int:
    """§6.1: GA_days = 280 − (due_date − today)."""
    return PREGNANCY_DAYS - (due_date - today).days


def trimester(content_week: int) -> int:
    """§6.2: 1 if week ≤ 13, 2 if 14-27, 3 if ≥ 28."""
    if content_week <= 13:
        return 1
    return 2 if content_week <= 27 else 3


def month_for_week(content_week: int, month_map: tuple[MonthRange, ...]) -> int:
    """§6.3: display month from the configured month map (never stored)."""
    for m in month_map:
        if m.weeks[0] <= content_week <= m.weeks[1]:
            return m.month
    raise ValueError(f"week {content_week} is not in the month map")


def gestational_age(
    due_date: date, today: date, month_map: tuple[MonthRange, ...]
) -> GestationalAge:
    ga_days = gestational_age_days(due_date, today)
    if ga_days < 0:
        # rule D2 rejects such dates when they are entered (§5.2), so this means bad data
        raise ValueError("due date gives a negative gestational age")
    completed = ga_days // 7
    content_week = min(completed, MAX_WEEKS)
    days_left = (due_date - today).days
    return GestationalAge(
        ga_days=ga_days,
        completed_weeks=completed,
        days=ga_days % 7,
        days_to_go=days_left if days_left > 0 else None,
        content_week=content_week,
        trimester=trimester(content_week),
        month=month_for_week(content_week, month_map),
    )


def home_state(status: str, due_date: date | None, today: date) -> HomeState:
    """§4.5 table: which version of the home screen to show."""
    if status != "active":
        return "ended"
    if due_date is None:
        return "no_date"
    weeks = gestational_age_days(due_date, today) // 7
    if weeks >= MAX_WEEKS:
        return "beyond_42"
    return "past_due" if weeks >= 40 else "active"


def calendar_range(due_date: date) -> tuple[date, date]:
    """§9.1: calendar navigation from the pregnancy start to the due date plus 2 weeks."""
    return due_date - timedelta(days=PREGNANCY_DAYS), due_date + timedelta(days=14)


def milestones(
    due_date: date,
    month_map: tuple[MonthRange, ...],
    term_from_week: int,
    start: date,
    end: date,
) -> list[Milestone]:
    """§6.4 calendar markers between start and end (inclusive), derived, never stored:
    each new week, the first week of each month, trimesters 2 and 3 (weeks 14 and 28),
    term (`term_from_week`), and the due date."""
    ga0 = due_date - timedelta(days=PREGNANCY_DAYS)  # the day GA is 0

    def week_day(week: int) -> date:
        return ga0 + timedelta(days=week * 7)

    found = [Milestone(week_day(w), "new_week", w) for w in range(1, MAX_WEEKS + 1)]
    found += [Milestone(week_day(m.weeks[0]), "new_month", m.month) for m in month_map]
    found += [
        Milestone(week_day(14), "new_trimester", 2),
        Milestone(week_day(28), "new_trimester", 3),
    ]
    found.append(Milestone(week_day(term_from_week), "term", term_from_week))
    found.append(Milestone(due_date, "due_date", 0))
    return sorted((m for m in found if start <= m.on <= end), key=lambda m: (m.on, m.kind))


# ---- §5 entering and changing dates ----

DateSource = Literal["lmp_estimate", "clinician_confirmed", "ultrasound"]
MAX_GA_DAYS = MAX_WEEKS * 7  # 294: rule D2's upper limit


class DateRuleError(ValueError):
    """A §5.2 validation rule failed. `code` is D1, D2 or D3; `field` is the input to mark."""

    def __init__(self, code: Literal["D1", "D2", "D3"], field: str) -> None:
        super().__init__(f"{code} on {field}")
        self.code = code
        self.field = field


@dataclass(frozen=True)
class ResolvedDates:
    due_date: date
    source: DateSource
    lmp_date: date | None  # stored only when the patient gave it (§5.1)


def _check_resulting_ga(due_date: date, today: date, field: str) -> None:
    # D2: resulting GA below 0 days or above 294 days (42 weeks)
    if not 0 <= gestational_age_days(due_date, today) <= MAX_GA_DAYS:
        raise DateRuleError("D2", field)


def dates_from_lmp(lmp_date: date, today: date) -> ResolvedDates:
    """Option A (§5.1): due date = LMP + 280 days, source `lmp_estimate`."""
    if lmp_date > today:  # D1: any date in the future except a due date
        raise DateRuleError("D1", "lmp_date")
    due = due_date_from_lmp(lmp_date)
    _check_resulting_ga(due, today, "lmp_date")
    return ResolvedDates(due, "lmp_estimate", lmp_date)


def dates_from_due_date(due_date: date, today: date) -> ResolvedDates:
    """Option B (§5.1): the doctor's due date as entered, source `clinician_confirmed`."""
    _check_resulting_ga(due_date, today, "due_date")
    return ResolvedDates(due_date, "clinician_confirmed", None)


def dates_from_ultrasound(
    scan_date: date, ga_weeks: int, ga_days: int, today: date
) -> ResolvedDates:
    """Option C (§5.1): scan date + (280 − GA at scan), source `ultrasound`."""
    if scan_date > today:  # D1
        raise DateRuleError("D1", "scan_date")
    if not 0 <= ga_weeks * 7 + ga_days <= MAX_GA_DAYS or not 0 <= ga_days <= 6:
        raise DateRuleError("D3", "ga_weeks")  # D3: ultrasound GA outside 0-42 weeks
    due = due_date_from_ultrasound(scan_date, ga_weeks, ga_days)
    _check_resulting_ga(due, today, "scan_date")
    return ResolvedDates(due, "ultrasound", None)


def needs_override_confirmation(old_source: str | None, new_source: DateSource) -> bool:
    """§5.3: a date set by a clinician or a scan is replaced by an LMP estimate only after
    the patient confirms (`msg_confirm_override_clinician_date`)."""
    return old_source in ("clinician_confirmed", "ultrasound") and new_source == "lmp_estimate"
