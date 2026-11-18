"""Give an existing Supabase sign-in the admin role (Dashboard spec §21; owner decision
2026-11-18, DEC-055). Admins are created only by the owner: first add the user in the Supabase
dashboard (Authentication -> Users -> Add user), then run, from backend/ with backend/.env:

  python scripts/make_admin.py --user-id <Supabase user UID> --email <their email>

Refuses to change an existing account of another role (a patient or doctor is never turned
into an admin by accident). Running it again for the same admin changes nothing.
"""

import argparse
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy.orm import Session  # noqa: E402

from app.modules.users.models import User  # noqa: E402


def make_admin(db: Session, user_id: uuid.UUID, email: str) -> str:
    """Create the admin's users row. Returns what happened; the caller commits."""
    existing = db.get(User, user_id)
    if existing is not None:
        if existing.role != "admin":
            raise SystemExit(f"Refusing: this account already exists with role {existing.role!r}.")
        return "already an admin; nothing changed"
    db.add(User(id=user_id, email=email.strip(), role="admin"))
    return "admin account created"


def main() -> None:
    from app.core.config import get_settings
    from app.core.database import make_engine

    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--user-id", type=uuid.UUID, required=True)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    engine = make_engine(get_settings().database_url)
    try:
        with Session(engine) as db:
            result = make_admin(db, args.user_id, args.email)
            db.commit()
    finally:
        engine.dispose()
    print(result)


if __name__ == "__main__":
    main()
