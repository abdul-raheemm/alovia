"""Pregnancy Journey routes for the patient (docs/API.md §4.2). Patient role, own record only."""

import uuid
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path, Query, Request
from sqlalchemy.orm import Session

from app.api import API_PREFIX
from app.common.responses import Envelope, ok
from app.core.database import get_db
from app.modules.journey import service
from app.modules.journey.config import load_journey_messages
from app.modules.journey.engine import local_today
from app.modules.journey.schemas import (
    AppointmentIn,
    AppointmentOut,
    AppointmentsOut,
    CalendarOut,
    DatesIn,
    HomeOut,
    MonthDetailOut,
)
from app.modules.users.models import Patient, User
from app.modules.users.service import get_account, get_patient

router = APIRouter(prefix=f"{API_PREFIX}/patient/journey")
appointments_router = APIRouter(prefix=f"{API_PREFIX}/patient/appointments")

OwnPatient = Annotated[Patient, Depends(get_patient)]
Db = Annotated[Session, Depends(get_db)]
Account = Annotated[User, Depends(get_account)]


@router.get("/home", response_model=Envelope[HomeOut])
def home(
    request: Request, patient: OwnPatient, db: Annotated[Session, Depends(get_db)]
) -> dict[str, Any]:
    cfg = request.app.state.journey_config
    out = service.get_home(
        db,
        patient,
        cfg,
        load_journey_messages(),
        request.app.state.content_provider,
        local_today(cfg.timezone),
    )
    return ok(out.model_dump(mode="json"))


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
    today = local_today(cfg.timezone)
    notices = service.set_dates(db, user, patient, body, today)
    out = service.get_home(
        db,
        patient,
        cfg,
        load_journey_messages(),
        request.app.state.content_provider,
        today,
        notices,
    )
    return ok(out.model_dump(mode="json"))


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
    db: Db,
) -> dict[str, Any]:
    tz = request.app.state.journey_config.timezone
    out = service.update_appointment(db, patient, appointment_id, body, tz)
    return ok(out.model_dump(mode="json"))


@appointments_router.delete("/{appointment_id}", response_model=Envelope[None])
def delete_appointment(appointment_id: uuid.UUID, patient: OwnPatient, db: Db) -> dict[str, Any]:
    service.delete_appointment(db, patient, appointment_id)
    return ok(None)
