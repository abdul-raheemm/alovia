"""Journey home data, month detail and pregnancy dates (spec §4, §5, §7-8; API.md §4.2)."""

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.logging import logger
from app.modules.journey import engine
from app.modules.journey.config import JourneyConfig, Message
from app.modules.journey.content import ContentProvider, select_for_home
from app.modules.journey.models import Appointment, PregnancyDateHistory
from app.modules.journey.schemas import (
    AppointmentOut,
    DatesOut,
    DueDateIn,
    HomeOut,
    LmpDatesIn,
    MonthDetailOut,
    MonthSummary,
    NavItemOut,
    PregnancyOut,
    UltrasoundDatesIn,
)
from app.modules.users.models import Patient, User

# §4.3 "This stage" home block shows these content types; the rest live in the month detail
HOME_STAGE_TYPES = ["fetal_development", "body_changes"]


def _current_ga(patient: Patient, cfg: JourneyConfig, today: date) -> engine.GestationalAge | None:
    """Defensive guard (owner decision 2026-11-17, ERR review): a stored due date outside
    rule D2's range must never crash /home. It cannot be written through the patient route;
    the Phase 5 doctor dates route must apply D2 too. If bad data appears anyway, the home
    falls back to the onboarding state and the error is logged."""
    if patient.due_date is None:
        return None
    try:
        return engine.gestational_age(patient.due_date, today, cfg.month_map)
    except ValueError:
        logger.error("stored due date is out of range", extra={"reason": "GA outside 0-42 weeks"})
        return None


def _next_appointment(
    db: Session, patient: Patient, timezone: str, today: date
) -> AppointmentOut | None:
    """§4.3 "next appointment": the soonest upcoming one. A date-only appointment
    (has_time false, stored at 00:00) counts as upcoming for its whole day."""
    rows = db.scalars(
        select(Appointment)
        .where(Appointment.patient_id == patient.id)
        .order_by(Appointment.appointment_at)
    )
    now = datetime.now(UTC)
    tz = ZoneInfo(timezone)
    for row in rows:
        upcoming = (
            row.appointment_at >= now
            if row.has_time
            else row.appointment_at.astimezone(tz).date() >= today
        )
        if upcoming:
            return AppointmentOut(
                appointment_at=row.appointment_at, has_time=row.has_time, title=row.title
            )
    return None


def get_home(
    db: Session,
    patient: Patient,
    cfg: JourneyConfig,
    messages: dict[str, Message],
    provider: ContentProvider,
    today: date,
    notices: list[str] | None = None,
) -> HomeOut:
    state = engine.home_state(patient.pregnancy_status, patient.due_date, today)
    pregnancy = None
    months: list[MonthSummary] = []
    stage_items = []
    size = None
    if state != "ended":
        ga = _current_ga(patient, cfg, today)
        if ga is None and patient.due_date is not None:
            state = "no_date"  # bad stored date: onboarding card only (guard above)
        if ga is not None:
            pregnancy = PregnancyOut(
                completed_weeks=ga.completed_weeks,
                days=ga.days,
                days_to_go=ga.days_to_go,
                content_week=ga.content_week,
                trimester=ga.trimester,
                month=ga.month,
                is_estimate=patient.due_date_source == "lmp_estimate",
            )
            # §4.3/§4.4: month cards and stage content only with an active dated pregnancy
            months = [
                MonthSummary(month=m.month, week_start=m.weeks[0], week_end=m.weeks[1])
                for m in cfg.month_map
            ]
            stage_items = select_for_home(provider, ga.content_week, ga.month, HOME_STAGE_TYPES)
            size = provider.size_for_week(ga.content_week)
    return HomeOut(
        months=months,
        stage_items=stage_items,
        size=size,
        next_appointment=_next_appointment(db, patient, cfg.timezone, today),
        state=state,
        dates=DatesOut(
            due_date=patient.due_date,
            lmp_date=patient.lmp_date,
            due_date_source=patient.due_date_source,
        ),
        pregnancy=pregnancy,
        nav_items=[NavItemOut(key=i.key, label=i.label) for i in cfg.nav_items],
        show_prototype_banner=cfg.show_prototype_banner,
        messages={key: m.text for key, m in messages.items()},
        notices=notices or [],
    )


def get_month_detail(
    patient: Patient, cfg: JourneyConfig, provider: ContentProvider, month: int, today: date
) -> MonthDetailOut:
    """§4.4 month detail. Month cards stop when the pregnancy has ended (§11.3)."""
    if patient.pregnancy_status != "active":
        raise AppError("NOT_FOUND", "We couldn't find this.", status=404)
    month_range = next(m for m in cfg.month_map if m.month == month)
    ga = _current_ga(patient, cfg, today)
    return MonthDetailOut(
        month=month,
        week_start=month_range.weeks[0],
        week_end=month_range.weeks[1],
        is_current=ga is not None and ga.month == month,
        items=provider.items_for_month(month),
    )


def _resolve(body: LmpDatesIn | DueDateIn | UltrasoundDatesIn, today: date) -> engine.ResolvedDates:
    try:
        if isinstance(body, LmpDatesIn):
            return engine.dates_from_lmp(body.lmp_date, today)
        if isinstance(body, DueDateIn):
            return engine.dates_from_due_date(body.due_date, today)
        return engine.dates_from_ultrasound(body.scan_date, body.ga_weeks, body.ga_days, today)
    except engine.DateRuleError as exc:  # D1, D2, D3
        raise AppError(
            "VALIDATION_ERROR", "Please check the dates.", fields={exc.field: exc.code}
        ) from exc


def set_dates(
    db: Session,
    user: User,
    patient: Patient,
    body: LmpDatesIn | DueDateIn | UltrasoundDatesIn,
    today: date,
) -> list[str]:
    """Set or change the pregnancy dates (§5). Returns message keys to show.

    The patient row and its history entry are saved together or not at all.
    """
    new = _resolve(body, today)
    old_due, old_source = patient.due_date, patient.due_date_source

    if engine.needs_override_confirmation(old_source, new.source) and not body.confirm_override:
        raise AppError(
            "CONFLICT",
            "Confirmation is needed to replace a date set by a doctor or a scan.",
            status=409,
            # the app shows this message key and asks before sending confirm_override: true
            fields={"confirm_override": "msg_confirm_override_clinician_date"},
        )

    if (new.due_date, new.source) == (old_due, old_source) and new.lmp_date in (
        None,
        patient.lmp_date,
    ):
        return []  # nothing changed: no history entry

    patient.due_date = new.due_date
    patient.due_date_source = new.source
    if new.lmp_date is not None:  # §5.1: the LMP is stored when given
        patient.lmp_date = new.lmp_date
    patient.updated_at = datetime.now(UTC)
    db.add(
        PregnancyDateHistory(
            patient_id=patient.id,
            changed_by=user.id,
            old_due_date=old_due,
            new_due_date=new.due_date,
            old_source=old_source,
            new_source=new.source,
        )
    )
    db.commit()
    # §5.3: a clinician or scan date now replaces an LMP estimate
    if old_source == "lmp_estimate" and new.source != "lmp_estimate":
        return ["msg_dates_updated_by_clinician"]
    return []
