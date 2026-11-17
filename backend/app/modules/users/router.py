"""GET /me and POST /me/consent (docs/API.md §4.1). Any signed-in role."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import API_PREFIX
from app.common.responses import Envelope, ok
from app.core.database import get_db
from app.modules.users.models import User
from app.modules.users.schemas import ConsentIn, ConsentStatus, MeOut
from app.modules.users.service import get_account, get_me, record_consent

router = APIRouter(prefix=API_PREFIX)

Account = Annotated[User, Depends(get_account)]
Db = Annotated[Session, Depends(get_db)]


@router.get("/me", response_model=Envelope[MeOut])
def me(user: Account, db: Db) -> dict[str, Any]:
    return ok(get_me(db, user).model_dump(mode="json"))


@router.post("/me/consent", response_model=Envelope[ConsentStatus])
def consent(body: ConsentIn, user: Account, db: Db) -> dict[str, Any]:
    return ok(record_consent(db, user, body).model_dump(mode="json"))
