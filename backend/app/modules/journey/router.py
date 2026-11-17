"""Pregnancy Journey routes for the patient (docs/API.md §4.2). Patient role, own record only."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path, Request
from sqlalchemy.orm import Session

from app.api import API_PREFIX
from app.common.responses import Envelope, ok
from app.core.database import get_db
from app.modules.journey import service
from app.modules.journey.config import load_journey_messages
from app.modules.journey.engine import local_today
from app.modules.journey.schemas import DatesIn, HomeOut, MonthDetailOut
from app.modules.users.models import Patient, User
from app.modules.users.service import get_account, get_patient

router = APIRouter(prefix=f"{API_PREFIX}/patient/journey")

OwnPatient = Annotated[Patient, Depends(get_patient)]


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
