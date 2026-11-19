"""Doctor routes: patient list, patient records, invite links, inbox (Dashboard spec §5-8,
API.md §4.6). Every route needs an active doctor with consent; patient routes also need an
active assignment (users.service.get_doctor / get_assigned_patient)."""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api import API_PREFIX
from app.common.responses import Envelope, ok
from app.core.database import get_db
from app.modules.dashboard import patients as service
from app.modules.dashboard.schemas import (
    InboxItemOut,
    InviteOut,
    PatientDetail,
    PatientIn,
    PatientRow,
)
from app.modules.journey.engine import local_today
from app.modules.users.models import Patient
from app.modules.users.service import DoctorAccount, get_assigned_patient, get_doctor

router = APIRouter(prefix=f"{API_PREFIX}/doctor")

Doc = Annotated[DoctorAccount, Depends(get_doctor)]
Assigned = Annotated[Patient, Depends(get_assigned_patient)]
Db = Annotated[Session, Depends(get_db)]


def _detail(request: Request, db: Session, patient: Patient) -> dict[str, Any]:
    cfg = request.app.state.journey_config
    return ok(
        service.patient_detail(db, patient, cfg, local_today(cfg.timezone)).model_dump(mode="json")
    )


@router.get("/patients", response_model=Envelope[list[PatientRow]])
def list_patients(request: Request, account: Doc, db: Db) -> dict[str, Any]:
    cfg = request.app.state.journey_config
    rows = service.list_patients(db, account.doctor.id, cfg, local_today(cfg.timezone))
    return ok([r.model_dump(mode="json") for r in rows])


@router.post("/patients", status_code=201, response_model=Envelope[PatientDetail])
def create_patient(request: Request, body: PatientIn, account: Doc, db: Db) -> dict[str, Any]:
    return _detail(request, db, service.create_patient(db, account, body))


@router.get("/patients/{patient_id}", response_model=Envelope[PatientDetail])
def get_patient(request: Request, patient: Assigned, db: Db) -> dict[str, Any]:
    return _detail(request, db, patient)


@router.put("/patients/{patient_id}", response_model=Envelope[PatientDetail])
def update_patient(
    request: Request, body: PatientIn, patient: Assigned, account: Doc, db: Db
) -> dict[str, Any]:
    service.update_patient(db, account, patient, body)
    return _detail(request, db, patient)


@router.post("/patients/{patient_id}/invite", status_code=201, response_model=Envelope[InviteOut])
def create_invite(request: Request, patient: Assigned, account: Doc, db: Db) -> dict[str, Any]:
    url = request.app.state.settings.patient_app_url
    return ok(service.invite_link(db, account, patient, url).model_dump(mode="json"))


@router.get("/inbox", response_model=Envelope[list[InboxItemOut]])
def list_inbox(account: Doc, db: Db, seen: bool = False) -> dict[str, Any]:
    return ok([i.model_dump(mode="json") for i in service.list_inbox(db, account.doctor.id, seen)])


@router.post("/inbox/{item_id}/seen", response_model=Envelope[InboxItemOut])
def mark_seen(item_id: uuid.UUID, account: Doc, db: Db) -> dict[str, Any]:
    return ok(service.mark_seen(db, account, item_id).model_dump(mode="json"))
