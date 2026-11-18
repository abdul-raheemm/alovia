"""Journey date engine (Journey spec §5.1, §6, §4.5; tests §15 items 1, 3, 4)."""

from datetime import UTC, date, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.modules.journey.config import (
    load_journey_config,
    load_journey_messages,
    parse_journey_config,
)
from app.modules.journey.engine import (
    DateRuleError,
    DateSource,
    ResolvedDates,
    calendar_range,
    dates_from_due_date,
    dates_from_lmp,
    dates_from_ultrasound,
    due_date_from_lmp,
    due_date_from_ultrasound,
    gestational_age,
    home_state,
    local_today,
    milestones,
    month_for_week,
    needs_override_confirmation,
    suggested_checkup_days,
    trimester,
)

CFG = load_journey_config()
MONTHS = CFG.month_map
TODAY = date(2026, 11, 17)


def due_for(weeks: int, days: int = 0, today: date = TODAY) -> date:
    """A due date that puts `today` at exactly weeks + days (inverse of §6.1)."""
    return today + timedelta(days=280 - (weeks * 7 + days))


# ---- §15 item 1: GA for options A, B and C, day boundaries, patient timezone ----


def test_option_a_lmp_today_is_ga_zero_and_due_in_280_days() -> None:
    due = due_date_from_lmp(TODAY)
    assert due == date(2027, 8, 24)
    ga = gestational_age(due, TODAY, MONTHS)
    assert (ga.ga_days, ga.completed_weeks, ga.days, ga.days_to_go) == (0, 0, 0, 280)


def test_option_a_lmp_counts_whole_days() -> None:
    lmp = TODAY - timedelta(days=24 * 7 + 3)  # 24 weeks 3 days ago
    ga = gestational_age(due_date_from_lmp(lmp), TODAY, MONTHS)
    assert (ga.completed_weeks, ga.days, ga.ga_days) == (24, 3, 171)


def test_option_b_doctor_due_date_is_used_as_entered() -> None:
    ga = gestational_age(date(2027, 3, 1), TODAY, MONTHS)
    assert ga.ga_days == 280 - (date(2027, 3, 1) - TODAY).days  # = 176
    assert (ga.completed_weeks, ga.days, ga.days_to_go) == (25, 1, 104)


def test_option_c_ultrasound_scan_date_plus_remaining_days() -> None:
    scan = date(2026, 10, 1)
    due = due_date_from_ultrasound(scan, weeks=12, days=4)
    assert due == scan + timedelta(days=280 - 88)
    # 47 days after a 12w4d scan the pregnancy is 12w4d + 47 days = 19w2d
    ga = gestational_age(due, scan + timedelta(days=47), MONTHS)
    assert (ga.completed_weeks, ga.days) == (19, 2)


def test_week_changes_exactly_on_the_seventh_day() -> None:
    due = due_for(20, 6)
    assert gestational_age(due, TODAY, MONTHS).completed_weeks == 20
    tomorrow = gestational_age(due, TODAY + timedelta(days=1), MONTHS)
    assert (tomorrow.completed_weeks, tomorrow.days) == (21, 0)


def test_days_to_go_only_while_positive() -> None:
    assert gestational_age(due_for(39, 6), TODAY, MONTHS).days_to_go == 1
    assert gestational_age(due_for(40, 0), TODAY, MONTHS).days_to_go is None  # due today
    assert gestational_age(due_for(40, 3), TODAY, MONTHS).days_to_go is None


def test_today_is_the_patients_local_date() -> None:
    # 20:00 UTC is already the next day in Asia/Kolkata (UTC+05:30)
    late_utc = datetime(2026, 11, 17, 20, 0, tzinfo=UTC)
    assert local_today("Asia/Kolkata", late_utc) == date(2026, 11, 18)
    assert local_today("UTC", late_utc) == date(2026, 11, 17)
    # 18:29 UTC is still the same day in India
    assert local_today("Asia/Kolkata", datetime(2026, 11, 17, 18, 29, tzinfo=UTC)) == TODAY


def test_negative_gestational_age_is_refused() -> None:
    with pytest.raises(ValueError):
        gestational_age(TODAY + timedelta(days=281), TODAY, MONTHS)


# ---- §15 item 3: month mapping at every boundary; trimester at 13/14 and 27/28 ----


@pytest.mark.parametrize(
    ("week", "month"),
    [
        (0, 1), (4, 1), (5, 2), (8, 2), (9, 3), (13, 3), (14, 4), (17, 4), (18, 5),
        (22, 5), (23, 6), (27, 6), (28, 7), (31, 7), (32, 8), (35, 8), (36, 9), (42, 9),
    ],
)  # fmt: skip
def test_month_map_boundaries(week: int, month: int) -> None:
    assert month_for_week(week, MONTHS) == month


def test_week_outside_the_month_map_is_an_error() -> None:
    with pytest.raises(ValueError):
        month_for_week(43, MONTHS)


def test_trimester_boundaries() -> None:
    assert [trimester(w) for w in (0, 13, 14, 27, 28, 42)] == [1, 1, 2, 2, 3, 3]


def test_month_and_trimester_come_through_gestational_age() -> None:
    ga = gestational_age(due_for(27, 6), TODAY, MONTHS)
    assert (ga.content_week, ga.month, ga.trimester) == (27, 6, 2)
    ga = gestational_age(due_for(28, 0), TODAY, MONTHS)
    assert (ga.content_week, ga.month, ga.trimester) == (28, 7, 3)


# ---- §15 item 4 / §4.5: states no date, 39, 40, 42+ (counter stops at 42) ----


def test_home_states() -> None:
    assert home_state("active", None, TODAY) == "no_date"
    assert home_state("active", due_for(39, 6), TODAY) == "active"
    assert home_state("active", due_for(40, 0), TODAY) == "past_due"
    assert home_state("active", due_for(41, 6), TODAY) == "past_due"
    assert home_state("active", due_for(42, 0), TODAY) == "beyond_42"
    for status in ("ended_birth", "ended_loss", "ended_not_specified"):
        assert home_state(status, due_for(30), TODAY) == "ended"
        assert home_state(status, None, TODAY) == "ended"


def test_content_week_stops_at_42() -> None:
    ga = gestational_age(due_for(43, 2), TODAY, MONTHS)
    assert (ga.completed_weeks, ga.content_week, ga.month) == (43, 42, 9)


# ---- §6.4 milestones and §9.1 calendar range ----


def test_milestones_over_the_whole_pregnancy() -> None:
    due = date(2027, 6, 1)
    start, end = calendar_range(due)
    assert (start, end) == (due - timedelta(days=280), due + timedelta(days=14))
    found = milestones(due, MONTHS, CFG.term_from_week, start, end)
    by_kind = {k: [m for m in found if m.kind == k] for k in {m.kind for m in found}}
    assert [m.value for m in by_kind["new_week"]][:3] == [1, 2, 3]
    assert len(by_kind["new_week"]) == 42  # weeks 1-42 all fall before due + 14 days
    assert [m.value for m in by_kind["new_month"]] == list(range(1, 10))
    assert by_kind["new_month"][0].on == start  # month 1 starts at GA 0
    assert by_kind["new_month"][3].on == start + timedelta(weeks=14)
    assert [(m.value, m.on) for m in by_kind["new_trimester"]] == [
        (2, start + timedelta(weeks=14)),
        (3, start + timedelta(weeks=28)),
    ]
    assert [(m.value, m.on) for m in by_kind["term"]] == [(37, start + timedelta(weeks=37))]
    assert [m.on for m in by_kind["due_date"]] == [due]
    assert found == sorted(found, key=lambda m: (m.on, m.kind))


def test_milestones_only_inside_the_requested_range() -> None:
    due = date(2027, 6, 1)
    ga0 = due - timedelta(days=280)
    window = milestones(due, MONTHS, 37, ga0 + timedelta(weeks=14), ga0 + timedelta(weeks=14))
    assert {(m.kind, m.value) for m in window} == {
        ("new_week", 14),
        ("new_month", 4),
        ("new_trimester", 2),
    }


# ---- config.yaml checks (§14.4; wrong settings stop the backend) ----


def test_shipped_config_matches_the_spec_defaults() -> None:
    assert CFG.content_source == "prototype"
    assert CFG.show_prototype_banner is True
    assert CFG.assistant_enabled is False
    # §9.2 / R3: on only because an official schedule with its source is in config.yaml
    # (owner decision 2026-11-18, DEC-056); the spec default was false until then
    assert CFG.suggested_checkups_enabled is True
    assert CFG.suggested_checkups is not None
    assert CFG.suggested_checkups.source.url.startswith("https://nhm.gov.in/")
    assert CFG.timezone == "Asia/Kolkata"
    assert (CFG.term_from_week, CFG.appointment_notice_hours, CFG.resume_window_days) == (37, 24, 7)
    assert [i.key for i in CFG.nav_items] == [
        "home", "calendar", "log_symptoms", "appointments", "doctor_notes", "more",
    ]  # fmt: skip


def _config_text(**changes: str) -> str:
    from app.modules.journey.config import CONFIG_FILE

    text = CONFIG_FILE.read_text(encoding="utf-8")
    for old, new in changes.items():
        assert old in text
        text = text.replace(old, new)
    return text


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("{ month: 2, weeks: [5, 8] }", "{ month: 2, weeks: [6, 8] }"),  # gap at week 5
        ("{ month: 2, weeks: [5, 8] }", "{ month: 2, weeks: [4, 8] }"),  # overlap at week 4
        ("{ month: 9, weeks: [36, 42] }", "{ month: 9, weeks: [36, 41] }"),  # stops early
        ("{ month: 3, weeks: [9, 13] }", "{ month: 4, weeks: [9, 13] }"),  # months out of order
        ("timezone: Asia/Kolkata", "timezone: Asia/Nowhere"),
        ("content_source: prototype", "content_source: guesses"),
        ("term_from_week: 37", "term_from_week: 50"),
        ("{ key: more, label: More }", "{ key: home, label: More }"),  # duplicate nav key
        ("day_of_month: 9", "day_of_month: 30"),  # not every month has the day
        ("url: https://nhm.gov.in", "url: http://nhm.gov.in"),  # official source over https
    ],
)
def test_bad_config_is_refused(old: str, new: str) -> None:
    with pytest.raises(ValidationError):
        parse_journey_config(_config_text(**{old: new}))


def test_checkups_cannot_be_on_without_an_official_schedule() -> None:
    """§9.2 / R3: suggested check-ups only after the official schedule is in config.yaml."""
    text = _config_text()
    without_schedule = text[: text.index("suggested_checkups:\n")]  # the block is last
    with pytest.raises(ValidationError, match="needs a suggested_checkups schedule"):
        parse_journey_config(without_schedule)
    off = without_schedule.replace(
        "suggested_checkups_enabled: true", "suggested_checkups_enabled: false"
    )
    assert parse_journey_config(off).suggested_checkups is None


def test_suggested_checkup_days() -> None:
    """PMSMA (config): the 9th of each month from week 14 to due date + 2 weeks."""
    due = date(2027, 3, 1)  # GA 0 on 2026-05-25; week 14 starts 2026-08-31
    days = suggested_checkup_days(due, 9, 14, date(2026, 1, 1), date(2028, 1, 1))
    assert days[0] == date(2026, 9, 9) and days[-1] == date(2027, 3, 9)  # last within due + 14
    assert len(days) == 7 and all(d.day == 9 for d in days)
    # the requested range limits the result; a 9th before week 14 is never included
    assert suggested_checkup_days(due, 9, 14, date(2026, 11, 1), date(2026, 11, 30)) == [
        date(2026, 11, 9)
    ]
    assert suggested_checkup_days(due, 9, 14, date(2026, 8, 1), date(2026, 8, 31)) == []
    # boundary: week 14 starting on the 9th includes it; starting on the 10th does not
    sept = (date(2026, 9, 1), date(2026, 9, 30))
    assert suggested_checkup_days(date(2027, 3, 10), 9, 14, *sept) == [date(2026, 9, 9)]
    assert suggested_checkup_days(date(2027, 3, 11), 9, 14, *sept) == []


# ---- §5.2 validation D1-D3 and §5.3 override rule (spec tests §15 items 2 and 10) ----


def rule(call: object) -> tuple[str, str]:
    """Run a zero-argument callable that must fail a date rule; return (code, field)."""
    with pytest.raises(DateRuleError) as err:
        call()  # type: ignore[operator]
    return err.value.code, err.value.field


def days_ago(n: int) -> date:
    return TODAY - timedelta(days=n)


def test_option_a_stores_lmp_and_estimate_source() -> None:
    lmp = days_ago(70)
    assert dates_from_lmp(lmp, TODAY) == ResolvedDates(
        lmp + timedelta(days=280), "lmp_estimate", lmp
    )


def test_d1_future_lmp_rejected_but_today_allowed() -> None:
    assert rule(lambda: dates_from_lmp(TODAY + timedelta(days=1), TODAY)) == ("D1", "lmp_date")
    assert dates_from_lmp(TODAY, TODAY).due_date == TODAY + timedelta(days=280)


def test_d2_lmp_limits_are_0_and_294_days() -> None:
    assert dates_from_lmp(days_ago(294), TODAY).source == "lmp_estimate"  # exactly 42 weeks
    assert rule(lambda: dates_from_lmp(days_ago(295), TODAY)) == ("D2", "lmp_date")


def test_option_b_due_date_may_be_in_the_future() -> None:
    due = TODAY + timedelta(days=100)
    assert dates_from_due_date(due, TODAY) == ResolvedDates(due, "clinician_confirmed", None)


def test_d2_due_date_limits() -> None:
    assert dates_from_due_date(TODAY + timedelta(days=280), TODAY).due_date  # GA 0: allowed
    assert rule(lambda: dates_from_due_date(TODAY + timedelta(days=281), TODAY)) == (
        "D2",
        "due_date",
    )
    assert dates_from_due_date(days_ago(14), TODAY).due_date  # GA 294: allowed
    assert rule(lambda: dates_from_due_date(days_ago(15), TODAY)) == ("D2", "due_date")


def test_option_c_ultrasound() -> None:
    scan = days_ago(10)
    got = dates_from_ultrasound(scan, 12, 4, TODAY)
    assert got == ResolvedDates(scan + timedelta(days=280 - 88), "ultrasound", None)


def test_d1_future_scan_date_rejected() -> None:
    assert rule(lambda: dates_from_ultrasound(TODAY + timedelta(days=1), 12, 0, TODAY)) == (
        "D1",
        "scan_date",
    )


def test_d3_ultrasound_ga_must_be_0_to_42_weeks() -> None:
    assert dates_from_ultrasound(TODAY, 42, 0, TODAY).source == "ultrasound"
    assert dates_from_ultrasound(TODAY, 0, 0, TODAY).due_date == TODAY + timedelta(days=280)
    for weeks, days in ((42, 1), (43, 0), (-1, 0), (10, 7), (10, -1)):
        assert rule(lambda w=weeks, d=days: dates_from_ultrasound(TODAY, w, d, TODAY)) == (
            "D3",
            "ga_weeks",
        )


def test_d2_old_scan_that_now_exceeds_42_weeks() -> None:
    # 40 weeks at a scan 15 days ago is 42 weeks 1 day today
    assert rule(lambda: dates_from_ultrasound(days_ago(15), 40, 0, TODAY)) == ("D2", "scan_date")
    assert dates_from_ultrasound(days_ago(14), 40, 0, TODAY).source == "ultrasound"


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        ("clinician_confirmed", "lmp_estimate", True),
        ("ultrasound", "lmp_estimate", True),
        ("lmp_estimate", "lmp_estimate", False),
        (None, "lmp_estimate", False),
        ("lmp_estimate", "clinician_confirmed", False),
        ("clinician_confirmed", "ultrasound", False),
        ("ultrasound", "clinician_confirmed", False),
    ],
)
def test_only_an_lmp_estimate_over_a_clinician_date_needs_confirmation(
    old: str | None, new: DateSource, expected: bool
) -> None:
    assert needs_override_confirmation(old, new) is expected


def test_messages_file_lists_every_spec_key_with_no_unapproved_text() -> None:
    messages = load_journey_messages()
    assert set(messages) == {
        "msg_onboarding", "msg_estimate_label", "msg_dates_updated_by_clinician",
        "msg_confirm_override_clinician_date", "msg_past_due_date", "msg_beyond_42_weeks",
        "msg_typical_not_yours", "msg_prototype_content", "msg_loss_support",
        "msg_after_pregnancy_danger_signs", "msg_birth_congratulations",
    }  # fmt: skip
    # DEC-041: no wording until a doctor approves it; this fails when text is added
    # without updating the review record
    assert all(m.text is None for m in messages.values())
