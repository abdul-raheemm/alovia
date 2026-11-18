"""Owner-made admins (Dashboard spec §21, DEC-055): scripts/make_admin.py. Runs on alovia-test."""

import importlib.util
import uuid
from pathlib import Path
from types import ModuleType

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from app.modules.users.models import User


def load_script() -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "scripts" / "make_admin.py"
    spec = importlib.util.spec_from_file_location("make_admin", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_creates_an_admin_once(engine: Engine) -> None:
    script = load_script()
    uid = uuid.uuid4()
    with Session(engine) as db:
        assert script.make_admin(db, uid, f"{uid}@example.test") == "admin account created"
        db.commit()
        assert script.make_admin(db, uid, f"{uid}@example.test").startswith("already an admin")
        user = db.get(User, uid)
        assert user is not None and user.role == "admin"


def test_never_turns_another_role_into_an_admin(engine: Engine) -> None:
    script = load_script()
    uid = uuid.uuid4()
    with Session(engine) as db:
        db.add(User(id=uid, email=f"{uid}@example.test", role="patient"))
        db.commit()
        with pytest.raises(SystemExit, match="role 'patient'"):
            script.make_admin(db, uid, f"{uid}@example.test")
        user = db.get(User, uid)
        assert user is not None and user.role == "patient"
