"""Admin routes (Dashboard spec §21, API.md §4.8): doctor accounts, assignments, activity
log. Every route needs the admin role and the current consent (users.service.get_admin).
Admins never get clinical values."""

import uuid
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api import API_PREFIX
from app.common.responses import Envelope, ok
from app.core.database import get_db
from app.modules.dashboard import admin
from app.modules.dashboard.schemas import (
    AdminDoctorOut,
    AssignmentIn,
    AssignmentPatientOut,
    AuditEntryOut,
    DoctorInviteIn,
    DoctorUpdateIn,
)
from app.modules.users.models import User
from app.modules.users.service import get_admin

router = APIRouter(prefix=f"{API_PREFIX}/admin")

Admin = Annotated[User, Depends(get_admin)]
Db = Annotated[Session, Depends(get_db)]


@router.get("/doctors", response_model=Envelope[list[AdminDoctorOut]])
def list_doctors(user: Admin, db: Db) -> dict[str, Any]:
    return ok([d.model_dump(mode="json") for d in admin.list_doctors(db)])


@router.post("/doctors", status_code=201, response_model=Envelope[AdminDoctorOut])
def invite_doctor(request: Request, body: DoctorInviteIn, user: Admin, db: Db) -> dict[str, Any]:
    state = request.app.state
    out = admin.invite_doctor(db, user, state.auth_admin, state.settings.doctor_app_url, body)
    return ok(out.model_dump(mode="json"))


@router.put("/doctors/{doctor_id}", response_model=Envelope[AdminDoctorOut])
def update_doctor(
    doctor_id: uuid.UUID, body: DoctorUpdateIn, user: Admin, db: Db
) -> dict[str, Any]:
    return ok(admin.update_doctor(db, user, doctor_id, body).model_dump(mode="json"))


@router.get("/assignments", response_model=Envelope[list[AssignmentPatientOut]])
def search_assignments(user: Admin, db: Db, q: str = "") -> dict[str, Any]:
    return ok([p.model_dump(mode="json") for p in admin.search_patients(db, q)])


@router.post("/assignments", response_model=Envelope[AssignmentPatientOut])
def assign(body: AssignmentIn, user: Admin, db: Db) -> dict[str, Any]:
    return ok(admin.assign(db, user, body).model_dump(mode="json"))


@router.delete("/assignments", response_model=Envelope[AssignmentPatientOut])
def unassign(patient_id: uuid.UUID, doctor_id: uuid.UUID, user: Admin, db: Db) -> dict[str, Any]:
    return ok(admin.unassign(db, user, patient_id, doctor_id).model_dump(mode="json"))


@router.get("/audit", response_model=Envelope[list[AuditEntryOut]])
def audit(
    request: Request,
    user: Admin,
    db: Db,
    actor: str | None = None,
    action: str | None = None,
    day_from: date | None = None,
    day_to: date | None = None,
) -> dict[str, Any]:
    """UX A3: filter by user, action and date."""
    tz = request.app.state.journey_config.timezone
    out = admin.admin_audit(db, actor, action, day_from, day_to, tz)
    return ok([e.model_dump(mode="json") for e in out])


@router.get("/audit/actions", response_model=Envelope[list[str]])
def audit_actions(user: Admin, db: Db) -> dict[str, Any]:
    """The action names in the log, for the filter list."""
    return ok(admin.audit_actions(db))
