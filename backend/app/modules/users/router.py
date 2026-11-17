"""GET /me and POST /me/consent (docs/API.md §4.1). Any signed-in role."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import API_PREFIX
from app.common.responses import Envelope, ok
from app.core.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.modules.users.invites import invite_is_valid, link_patient
from app.modules.users.models import User
from app.modules.users.schemas import ConsentIn, ConsentStatus, InviteCheckOut, LinkIn, MeOut
from app.modules.users.service import get_account, get_me, record_consent, record_sign_in

router = APIRouter(prefix=API_PREFIX)

Account = Annotated[User, Depends(get_account)]
Db = Annotated[Session, Depends(get_db)]


@router.get("/me", response_model=Envelope[MeOut])
def me(
    user: Account, current: Annotated[CurrentUser, Depends(get_current_user)], db: Db
) -> dict[str, Any]:
    """Both apps call this first after sign-in, so a new sign-in session is logged here."""
    out = get_me(db, user)
    record_sign_in(db, user, current.session_id, out.patient.id if out.patient else None)
    return ok(out.model_dump(mode="json"))


@router.post("/me/consent", response_model=Envelope[ConsentStatus])
def consent(body: ConsentIn, user: Account, db: Db) -> dict[str, Any]:
    return ok(record_consent(db, user, body).model_dump(mode="json"))


@router.get("/invites/{code}/check", response_model=Envelope[InviteCheckOut])
def check_invite(code: str, db: Db) -> dict[str, Any]:
    """No sign-in needed. Answers only valid / not valid (rate limits come in Phase 8)."""
    return ok({"valid": invite_is_valid(db, code)})


@router.post("/patient/link", response_model=Envelope[MeOut])
def link(
    body: LinkIn, current: Annotated[CurrentUser, Depends(get_current_user)], db: Db
) -> dict[str, Any]:
    """Right after sign-up: create the patient's account from the invite (DEC-036)."""
    user = link_patient(db, current, body.code)
    return ok(get_me(db, user).model_dump(mode="json"))
