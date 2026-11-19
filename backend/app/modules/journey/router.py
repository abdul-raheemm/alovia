"""Pregnancy Journey routes for the patient (docs/API.md §4.2). Patient role, own record only."""

import uuid
from datetime import date, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path, Query, Request
from sqlalchemy.orm import Session

from app.api import API_PREFIX
from app.common.responses import Envelope, ok
from app.core.database import get_db
from app.modules.genetic import service as genetic
from app.modules.journey import service
from app.modules.journey.config import load_journey_messages
from app.modules.journey.content import select_for_home
from app.modules.journey.engine import local_today
from app.modules.journey.schemas import (
    AppointmentIn,
    AppointmentOut,
    AppointmentsOut,
    CalendarOut,
    DatesIn,
    DoctorNoteOut,
    HomeOut,
    MonthDetailOut,
    NotificationOut,
    PregnancyEndIn,
    SymptomDayOut,
    WeeklySummaryOut,
)
from app.modules.symptoms import service as symptoms
from app.modules.users.models import Patient, User
from app.modules.users.service import get_account, get_patient

router = APIRouter(prefix=f"{API_PREFIX}/patient/journey")
appointments_router = APIRouter(prefix=f"{API_PREFIX}/patient/appointments")
notifications_router = APIRouter(prefix=f"{API_PREFIX}/patient/notifications")
notes_router = APIRouter(prefix=f"{API_PREFIX}/patient/doctor-notes")
end_router = APIRouter(prefix=f"{API_PREFIX}/patient/pregnancy-end")

OwnPatient = Annotated[Patient, Depends(get_patient)]
Db = Annotated[Session, Depends(get_db)]
Account = Annotated[User, Depends(get_account)]


def _home(
    request: Request, db: Session, patient: Patient, notices: list[str] | None = None
) -> dict[str, Any]:
    """The home data (§4.3) plus what the symptom module adds: "logged today" and the §9.4
    weekly summary for this calendar week (Sunday to Saturday, as the week strip)."""
    cfg = request.app.state.journey_config
    today = local_today(cfg.timezone)
    provider = request.app.state.content_provider
    out = service.get_home(db, patient, cfg, load_journey_messages(), provider, today, notices)
    out.genetic_check = genetic.latest_check(db, patient.id)
    if out.state != "ended":
        start = today - timedelta(days=(today.weekday() + 1) % 7)
        end = start + timedelta(days=6)
        rules = request.app.state.symptom_rules
        summary = symptoms.week_summary(db, patient.id, rules, start, end, cfg.timezone)
        common = (
            select_for_home(
                provider, out.pregnancy.content_week, out.pregnancy.month, ["common_symptoms"]
            )
            if out.pregnancy
            else []
        )
        out.logged_today = symptoms.logged_on(db, patient.id, today, cfg.timezone)
        out.weekly_summary = WeeklySummaryOut(
            week_start=start, week_end=end, common_at_stage=common, **summary
        )
    return ok(out.model_dump(mode="json"))


@router.get("/home", response_model=Envelope[HomeOut])
def home(request: Request, patient: OwnPatient, db: Db) -> dict[str, Any]:
    return _home(request, db, patient)


@router.get("/months/{month}", response_model=Envelope[MonthDetailOut])
def month_detail(
    request: Request, patient: OwnPatient, month: Annotated[int, Path(ge=1, le=9)]
) -> dict[str, Any]:
    cfg = request.app.state.journey_config
    out = service.get_month_detail(
        patient, cfg, request.app.state.content_provider, month, local_today(cfg.timezone)
    )
    return ok(out.model_dump(mode="json"))


@router.put("/dates", response_model=Envelope[HomeOut])
def put_dates(
    request: Request,
    body: DatesIn,
    patient: OwnPatient,
    user: Annotated[User, Depends(get_account)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    """Set or change pregnancy dates (Journey §5); returns the refreshed home data."""
    cfg = request.app.state.journey_config
    notices = service.set_dates(db, user, patient, body, local_today(cfg.timezone))
    return _home(request, db, patient, notices)


@router.get("/calendar", response_model=Envelope[CalendarOut])
def calendar(
    request: Request,
    patient: OwnPatient,
    db: Db,
    start: Annotated[date, Query(alias="from")],
    end: Annotated[date, Query(alias="to")],
) -> dict[str, Any]:
    """Calendar markers for the days from..to, inclusive (Journey §9.1-9.2)."""
    cfg = request.app.state.journey_config
    out = service.get_calendar(db, patient, cfg, start, end, local_today(cfg.timezone))
    # §9.2 / Journey §15 test 8: symptom dots and red-flag icons from Module 7 data
    days = symptoms.symptom_days(db, patient.id, start, end, cfg.timezone)
    out.symptom_days = [SymptomDayOut(**d) for d in days]
    return ok(out.model_dump(mode="json"))


# ---- §9.3 appointments: list / create own; edit / delete own patient-created only ----


@appointments_router.get("", response_model=Envelope[AppointmentsOut])
def list_appointments(request: Request, patient: OwnPatient, db: Db) -> dict[str, Any]:
    tz = request.app.state.journey_config.timezone
    out = service.list_appointments(db, patient, tz, local_today(tz))
    return ok(out.model_dump(mode="json"))


@appointments_router.post("", status_code=201, response_model=Envelope[AppointmentOut])
def create_appointment(
    request: Request, body: AppointmentIn, patient: OwnPatient, user: Account, db: Db
) -> dict[str, Any]:
    tz = request.app.state.journey_config.timezone
    out = service.create_appointment(db, user, patient, body, tz)
    return ok(out.model_dump(mode="json"))


@appointments_router.put("/{appointment_id}", response_model=Envelope[AppointmentOut])
def update_appointment(
    request: Request,
    appointment_id: uuid.UUID,
    body: AppointmentIn,
    patient: OwnPatient,
    user: Account,
    db: Db,
) -> dict[str, Any]:
    tz = request.app.state.journey_config.timezone
    out = service.update_appointment(db, user, patient, appointment_id, body, tz)
    return ok(out.model_dump(mode="json"))


@appointments_router.delete("/{appointment_id}", response_model=Envelope[None])
def delete_appointment(
    appointment_id: uuid.UUID, patient: OwnPatient, user: Account, db: Db
) -> dict[str, Any]:
    service.delete_appointment(db, user, patient, appointment_id)
    return ok(None)


# ---- §10 notification bar and shared doctor notes ----


@notifications_router.get("", response_model=Envelope[list[NotificationOut]])
def notifications(request: Request, patient: OwnPatient, db: Db) -> dict[str, Any]:
    """Creates any notifications that are due (§10.2), then returns the unread ones."""
    cfg = request.app.state.journey_config
    out = service.get_notifications(db, patient, cfg, local_today(cfg.timezone))
    return ok([n.model_dump(mode="json") for n in out])


@notifications_router.post("/{notification_id}/read", response_model=Envelope[None])
def read_notification(notification_id: uuid.UUID, patient: OwnPatient, db: Db) -> dict[str, Any]:
    service.mark_notification(db, patient, notification_id, "read")
    return ok(None)


@notifications_router.post("/{notification_id}/dismiss", response_model=Envelope[None])
def dismiss_notification(notification_id: uuid.UUID, patient: OwnPatient, db: Db) -> dict[str, Any]:
    service.mark_notification(db, patient, notification_id, "dismiss")
    return ok(None)


@notes_router.get("", response_model=Envelope[list[DoctorNoteOut]])
def doctor_notes(request: Request, patient: OwnPatient, db: Db) -> dict[str, Any]:
    tz = request.app.state.journey_config.timezone
    return ok([n.model_dump(mode="json") for n in service.list_doctor_notes(db, patient, tz)])


# ---- §11 pregnancy end and undo; both reply with the refreshed home data ----


@end_router.post("", response_model=Envelope[HomeOut])
def end_pregnancy(
    request: Request, body: PregnancyEndIn, patient: OwnPatient, user: Account, db: Db
) -> dict[str, Any]:
    service.end_pregnancy(db, user, patient, body)
    return _home(request, db, patient)


@end_router.post("/undo", response_model=Envelope[HomeOut])
def undo_pregnancy_end(
    request: Request, patient: OwnPatient, user: Account, db: Db
) -> dict[str, Any]:
    service.undo_pregnancy_end(db, user, patient, request.app.state.journey_config)
    return _home(request, db, patient)
