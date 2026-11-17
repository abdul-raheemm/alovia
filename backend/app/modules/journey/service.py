"""Journey home data, month detail, pregnancy dates, calendar and appointments
(spec §4, §5, §7-9; API.md §4.2)."""

import uuid
from datetime import UTC, date, datetime, time, timedelta
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
    AppointmentIn,
    AppointmentOut,
    AppointmentsOut,
    CalendarOut,
    DatesOut,
    DueDateIn,
    HomeOut,
    LmpDatesIn,
    MilestoneOut,
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


# ---- §9.3 appointments ----


def _appointment_out(row: Appointment, tz: ZoneInfo) -> AppointmentOut:
    # the database returns UTC; a date-only appointment is local midnight, so its day must
    # be read in the patient's time zone, never from the UTC value
    local = row.appointment_at.astimezone(tz)
    return AppointmentOut(
        id=row.id,
        appointment_at=local,
        has_time=row.has_time,
        date=local.date(),
        time=local.time() if row.has_time else None,
        title=row.title,
        note=row.note,
        source=row.source,  # CHECK constraint: patient | doctor
        can_edit=row.source == "patient",
    )


def list_appointments(db: Session, patient: Patient, timezone: str, today: date) -> AppointmentsOut:
    """Her appointments (her own and doctor-added). A date-only appointment (has_time false,
    stored at local 00:00) counts as upcoming for its whole day."""
    tz = ZoneInfo(timezone)
    now = datetime.now(UTC)
    upcoming: list[AppointmentOut] = []
    past: list[AppointmentOut] = []
    rows = db.scalars(
        select(Appointment)
        .where(Appointment.patient_id == patient.id)
        .order_by(Appointment.appointment_at, Appointment.created_at)
    )
    for row in rows:
        out = _appointment_out(row, tz)
        is_upcoming = row.appointment_at >= now if row.has_time else out.date >= today
        (upcoming if is_upcoming else past).append(out)
    return AppointmentsOut(upcoming=upcoming, past=past[::-1])


def _next_appointment(
    db: Session, patient: Patient, timezone: str, today: date
) -> AppointmentOut | None:
    """§4.3 "next appointment": the soonest upcoming one."""
    upcoming = list_appointments(db, patient, timezone, today).upcoming
    return upcoming[0] if upcoming else None


def _stored_moment(body: AppointmentIn, timezone: str) -> datetime:
    # §14.2: time optional -> store the date at 00:00 (local) with has_time = false
    return datetime.combine(body.date, body.time or time(0, 0), tzinfo=ZoneInfo(timezone))


def create_appointment(
    db: Session, user: User, patient: Patient, body: AppointmentIn, timezone: str
) -> AppointmentOut:
    row = Appointment(
        patient_id=patient.id,
        appointment_at=_stored_moment(body, timezone),
        has_time=body.time is not None,
        title=body.title,
        note=body.note,
        created_by=user.id,
        source="patient",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _appointment_out(row, ZoneInfo(timezone))


def _own_editable(db: Session, patient: Patient, appointment_id: uuid.UUID) -> Appointment:
    """§9.3: she edits and deletes only appointments she added herself. Another patient's
    appointment is "not found" (API.md §3: same message whether missing or not visible)."""
    row = db.scalar(
        select(Appointment).where(
            Appointment.id == appointment_id, Appointment.patient_id == patient.id
        )
    )
    if row is None:
        raise AppError("NOT_FOUND", "We couldn't find this.", status=404)
    if row.source != "patient":
        logger.warning("permission denied", extra={"reason": "doctor-added appointment"})
        raise AppError(
            "FORBIDDEN",
            "This appointment was added by your doctor and can't be changed.",
            status=403,
        )
    return row


def update_appointment(
    db: Session, patient: Patient, appointment_id: uuid.UUID, body: AppointmentIn, timezone: str
) -> AppointmentOut:
    row = _own_editable(db, patient, appointment_id)
    row.appointment_at = _stored_moment(body, timezone)
    row.has_time = body.time is not None
    row.title = body.title
    row.note = body.note
    row.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(row)
    return _appointment_out(row, ZoneInfo(timezone))


def delete_appointment(db: Session, patient: Patient, appointment_id: uuid.UUID) -> None:
    """Hard delete: planning data, not a clinical record (DATABASE.md §8)."""
    db.delete(_own_editable(db, patient, appointment_id))
    db.commit()


# ---- §9.1-9.2 calendar ----


def get_calendar(
    db: Session, patient: Patient, cfg: JourneyConfig, start: date, end: date, today: date
) -> CalendarOut:
    """Markers for the days start..end (inclusive): §6.4 milestones and appointments.
    Milestones are baby-stage markers, so they appear only for an active pregnancy with a
    usable due date (§11.3); appointments always stay visible."""
    if start > end:
        raise AppError("VALIDATION_ERROR", "Please check the dates.", fields={"to": "before from"})
    tz = ZoneInfo(cfg.timezone)
    rows = db.scalars(
        select(Appointment)
        .where(
            Appointment.patient_id == patient.id,
            Appointment.appointment_at >= datetime.combine(start, time(0, 0), tzinfo=tz),
            Appointment.appointment_at
            < datetime.combine(end + timedelta(days=1), time(0, 0), tzinfo=tz),
        )
        .order_by(Appointment.appointment_at, Appointment.created_at)
    )
    appointments = [_appointment_out(row, tz) for row in rows]
    due = patient.due_date
    if patient.pregnancy_status != "active" or due is None or not _current_ga(patient, cfg, today):
        return CalendarOut(start=None, end=None, milestones=[], appointments=appointments)
    first, last = engine.calendar_range(due)
    found = engine.milestones(due, cfg.month_map, cfg.term_from_week, start, end)
    return CalendarOut(
        start=first,
        end=last,
        milestones=[MilestoneOut(date=m.on, kind=m.kind, value=m.value) for m in found],
        appointments=appointments,
    )


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
