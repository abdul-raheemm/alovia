"""Patient genetic routes (docs/API.md §4.4). Patient role, own record only."""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api import API_PREFIX
from app.common.responses import Envelope, ok
from app.core.database import get_db
from app.modules.genetic import service
from app.modules.genetic.schemas import AssessmentIn, AssessmentOut
from app.modules.users.models import Patient, User
from app.modules.users.service import get_account, get_patient

router = APIRouter(prefix=f"{API_PREFIX}/patient/genetic/assessments")

OwnPatient = Annotated[Patient, Depends(get_patient)]
Account = Annotated[User, Depends(get_account)]
Db = Annotated[Session, Depends(get_db)]


@router.post("", status_code=201, response_model=Envelope[AssessmentOut])
def create_assessment(
    request: Request, body: AssessmentIn, patient: OwnPatient, user: Account, db: Db
) -> dict[str, Any]:
    """Submit, run the engine, save (pending doctor review)."""
    out = service.create_assessment(db, user, patient, body, request.app.state.genetic_rules)
    return ok(out.model_dump(mode="json"))


@router.get("", response_model=Envelope[list[AssessmentOut]])
def list_assessments(patient: OwnPatient, db: Db) -> dict[str, Any]:
    return ok([a.model_dump(mode="json") for a in service.list_assessments(db, patient)])


@router.get("/{assessment_id}", response_model=Envelope[AssessmentOut])
def get_assessment(assessment_id: uuid.UUID, patient: OwnPatient, db: Db) -> dict[str, Any]:
    return ok(service.get_assessment(db, patient, assessment_id).model_dump(mode="json"))
