"""Patient symptom routes (docs/API.md §4.3). Patient role, own record only."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import API_PREFIX
from app.common.responses import Envelope, ok
from app.core.database import get_db
from app.modules.journey import service as journey
from app.modules.journey.engine import local_today
from app.modules.symptoms import engine, service
from app.modules.symptoms.rules import (
    CommonSymptom,
    PuqeQuestion,
    PuqeSource,
    SymptomRules,
    WarningSymptom,
)
from app.modules.symptoms.schemas import (
    ChartsOut,
    CheckinHistoryOut,
    CheckinIn,
    CheckinOut,
    PuqeBandOut,
)
from app.modules.users.models import Patient
from app.modules.users.service import get_patient

router = APIRouter(prefix=f"{API_PREFIX}/patient/symptoms")

OwnPatient = Annotated[Patient, Depends(get_patient)]
Db = Annotated[Session, Depends(get_db)]


class VocabularyOut(BaseModel):
    """The log form (§5), filtered by pregnancy week (§5.2)."""

    logging_open: bool  # false after the pregnancy has ended (DEC-064)
    pregnancy_week: int | None
    severities: dict[str, str]
    durations: dict[str, str]
    labour_durations: dict[str, str]
    body_areas: dict[str, str]
    common: list[CommonSymptom]
    warning: list[WarningSymptom]
    puqe_questions: list[PuqeQuestion]
    puqe_source: PuqeSource
    puqe_bands: list[PuqeBandOut]  # §8, for the live score band on the Log
    draft_ttl_minutes: int  # DEC-109: unsaved Log draft kept on the device


def _week(request: Request, patient: Patient) -> int | None:
    cfg = request.app.state.journey_config
    return journey.pregnancy_week(patient, cfg, local_today(cfg.timezone))


def _rules(request: Request) -> SymptomRules:
    rules: SymptomRules = request.app.state.symptom_rules
    return rules


@router.get("/vocabulary", response_model=Envelope[VocabularyOut])
def vocabulary(request: Request, patient: OwnPatient) -> dict[str, Any]:
    rules = _rules(request)
    week = _week(request, patient)
    offered = set(engine.offered_warning_ids(rules, week))
    v = rules.vocabulary
    out = VocabularyOut(
        logging_open=service.logging_open(patient),
        pregnancy_week=week,
        severities=v.severities,
        durations=v.durations,
        labour_durations=v.labour_durations,
        body_areas=v.body_areas,
        common=list(v.common),
        warning=[s for s in v.warning if s.id in offered],
        puqe_questions=list(rules.puqe.questions),
        puqe_source=rules.puqe.source,
        puqe_bands=[PuqeBandOut(band=b.band, min=b.min, max=b.max) for b in rules.puqe.bands],
        draft_ttl_minutes=rules.settings.draft_ttl_minutes,
    )
    return ok(out.model_dump(mode="json"))


@router.post("/checkins", status_code=201, response_model=Envelope[CheckinOut])
def create_checkin(
    request: Request, body: CheckinIn, patient: OwnPatient, db: Db
) -> dict[str, Any]:
    """Validate, run the rules, save; returns the level and message keys (never pattern
    changes). The advice is shown at once, never delayed for doctor review (§11.1)."""
    out = service.create_checkin(
        db,
        patient,
        body,
        _rules(request),
        _week(request, patient),
        request.app.state.journey_config.timezone,
    )
    return ok(out.model_dump(mode="json"))


@router.get("/checkins", response_model=Envelope[list[CheckinHistoryOut]])
def list_checkins(request: Request, patient: OwnPatient, db: Db) -> dict[str, Any]:
    tz = request.app.state.journey_config.timezone
    out = service.list_checkins(db, patient, _rules(request), tz)
    return ok([c.model_dump(mode="json") for c in out])


@router.get("/charts", response_model=Envelope[ChartsOut])
def charts(request: Request, patient: OwnPatient, db: Db) -> dict[str, Any]:
    tz = request.app.state.journey_config.timezone
    return ok(service.charts(db, patient, _rules(request), tz).model_dump(mode="json"))
