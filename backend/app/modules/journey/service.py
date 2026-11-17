"""Journey home data and pregnancy dates (Journey spec §4.5, §5; API.md §4.2)."""

from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.journey import engine
from app.modules.journey.config import JourneyConfig, Message
from app.modules.journey.models import PregnancyDateHistory
from app.modules.journey.schemas import (
    DatesOut,
    DueDateIn,
    HomeOut,
    LmpDatesIn,
    NavItemOut,
    PregnancyOut,
    UltrasoundDatesIn,
)
from app.modules.users.models import Patient, User


def get_home(
    patient: Patient,
    cfg: JourneyConfig,
    messages: dict[str, Message],
    today: date,
    notices: list[str] | None = None,
) -> HomeOut:
    state = engine.home_state(patient.pregnancy_status, patient.due_date, today)
    pregnancy = None
    if patient.due_date is not None and state != "ended":
        ga = engine.gestational_age(patient.due_date, today, cfg.month_map)
        pregnancy = PregnancyOut(
            completed_weeks=ga.completed_weeks,
            days=ga.days,
            days_to_go=ga.days_to_go,
            content_week=ga.content_week,
            trimester=ga.trimester,
            month=ga.month,
            is_estimate=patient.due_date_source == "lmp_estimate",
        )
    return HomeOut(
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
