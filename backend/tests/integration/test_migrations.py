"""Phase 1 migration on a fresh, separate test database (DATABASE.md §11.3, TESTING.md §2).

Needs TEST_DATABASE_URL in backend/.env (the empty "alovia-test" Supabase project).
These tests drop and recreate every table, so they refuse to run against DATABASE_URL.
"""

import uuid
from collections.abc import Iterator

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from fastapi.testclient import TestClient
from sqlalchemy import Connection, Engine, inspect, text
from sqlalchemy.exc import IntegrityError

import app.models  # noqa: F401  (registers every table)
from app.core.database import Base
from app.main import create_app
from tests.conftest import alembic_config, project_ref
from tests.helpers import make_settings

PHASE1_TABLES = {
    "users",
    "consents",
    "doctors",
    "patients",
    "doctor_patient_assignments",
    "patient_invites",
    "audit_log",
    "fetal_results",
    "maternal_results",
}
PHASE2_TABLES = {  # migration 0002 (inbox_items moved forward, DEC-044)
    "pregnancy_date_history",
    "appointments",
    "notifications",
    "doctor_notes",
    "inbox_items",
}
PHASE3_TABLES = {"symptom_checkins", "symptom_logs"}  # migration 0003
PHASE4_TABLES = {"genetic_assessments"}  # migration 0004
PHASE5_TABLES = {"result_shares", "medical_records", "rule_signoffs"}  # migration 0005
TABLES = PHASE1_TABLES | PHASE2_TABLES | PHASE3_TABLES | PHASE4_TABLES | PHASE5_TABLES


def _app_tables(engine: Engine) -> set[str]:
    return set(inspect(engine).get_table_names()) & TABLES


def test_upgrade_downgrade_upgrade(test_db_url: str, engine: Engine) -> None:
    cfg = alembic_config(test_db_url)
    assert _app_tables(engine) == TABLES
    command.downgrade(cfg, "0004")  # 0005's downgrade removes its tables and result columns
    assert _app_tables(engine) == TABLES - PHASE5_TABLES
    columns = {c["name"] for c in inspect(engine).get_columns("fetal_results")}
    assert not {"entered_values", "range_warnings"} & columns
    command.downgrade(cfg, "0003")  # 0004's downgrade removes only its own table
    assert _app_tables(engine) == PHASE1_TABLES | PHASE2_TABLES | PHASE3_TABLES
    command.downgrade(cfg, "0002")  # 0003's downgrade removes only its own tables
    assert _app_tables(engine) == PHASE1_TABLES | PHASE2_TABLES
    command.downgrade(cfg, "0001")  # 0002's downgrade removes only its own tables
    assert _app_tables(engine) == PHASE1_TABLES
    command.downgrade(cfg, "base")
    assert _app_tables(engine) == set()
    command.upgrade(cfg, "head")
    assert _app_tables(engine) == TABLES


def test_database_matches_models(engine: Engine) -> None:
    with engine.connect() as conn:
        diffs = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    assert diffs == []


@pytest.fixture
def conn(engine: Engine) -> Iterator[Connection]:
    """Every constraint test runs inside a transaction that is rolled back."""
    with engine.connect() as connection:
        outer = connection.begin()
        yield connection
        outer.rollback()


def _rejects(conn: Connection, sql: str, **params: object) -> None:
    # the savepoint must see the error so it rolls back; pytest.raises then catches it
    with pytest.raises(IntegrityError), conn.begin_nested():
        conn.execute(text(sql), params)


def _user(conn: Connection, role: str = "doctor") -> uuid.UUID:
    uid = uuid.uuid4()
    conn.execute(
        text("INSERT INTO users (id, email, role) VALUES (:id, :email, :role)"),
        {"id": uid, "email": f"{uid}@example.test", "role": role},
    )
    return uid


def _doctor(conn: Connection) -> uuid.UUID:
    new_id: uuid.UUID = conn.execute(
        text("INSERT INTO doctors (user_id, name) VALUES (:u, 'Test Doctor') RETURNING id"),
        {"u": _user(conn)},
    ).scalar_one()
    return new_id


def _patient(conn: Connection) -> uuid.UUID:
    new_id: uuid.UUID = conn.execute(
        text("INSERT INTO patients (name) VALUES ('Test Patient 1') RETURNING id")
    ).scalar_one()
    return new_id


def test_enumerations_are_checked(conn: Connection) -> None:
    uid = uuid.uuid4()
    _rejects(
        conn, "INSERT INTO users (id, email, role) VALUES (:id, 'x@example.test', 'nurse')", id=uid
    )
    _rejects(conn, "INSERT INTO patients (name, pregnancy_status) VALUES ('P', 'paused')")
    _rejects(conn, "INSERT INTO patients (name, due_date_source) VALUES ('P', 'guess')")
    patient = _patient(conn)
    for table, bad in (("fetal_results", "Low"), ("maternal_results", "Normal")):
        _rejects(
            conn,
            f"INSERT INTO {table} (patient_id, input_values, predicted_class, confidence, "
            "class_probabilities, top_contributing_factors) "
            "VALUES (:p, '{}', :c, 0.5, '{}', '[]')",
            p=patient,
            c=bad,
        )


def test_defaults(conn: Connection) -> None:
    row = conn.execute(
        text("SELECT pregnancy_status, created_at, updated_at FROM patients WHERE id = :id"),
        {"id": _patient(conn)},
    ).one()
    assert row.pregnancy_status == "active"
    assert row.created_at is not None and row.updated_at is not None


def test_unique_rules(conn: Connection) -> None:
    uid = _user(conn)
    _rejects(
        conn,
        "INSERT INTO users (id, email, role) VALUES (:id, :e, 'doctor')",
        id=uuid.uuid4(),
        e=f"{uid}@example.test",
    )
    conn.execute(text("INSERT INTO doctors (user_id, name) VALUES (:u, 'D')"), {"u": uid})
    _rejects(conn, "INSERT INTO doctors (user_id, name) VALUES (:u, 'D2')", u=uid)
    patient = _patient(conn)
    conn.execute(
        text(
            "INSERT INTO patient_invites (patient_id, code_hash, created_by, expires_at) "
            "VALUES (:p, 'h1', :u, now())"
        ),
        {"p": patient, "u": uid},
    )
    _rejects(
        conn,
        "INSERT INTO patient_invites (patient_id, code_hash, created_by, expires_at) "
        "VALUES (:p, 'h1', :u, now())",
        p=patient,
        u=uid,
    )


ASSIGN = (
    "INSERT INTO doctor_patient_assignments "
    "(doctor_id, patient_id, is_primary, assigned_by, assigned_at, removed_at) "
    "VALUES (:d, :p, :primary, :by, now(), :removed)"
)


def test_assignment_partial_unique_indexes(conn: Connection) -> None:
    by, patient = _user(conn, "admin"), _patient(conn)
    doc_a, doc_b, doc_c = _doctor(conn), _doctor(conn), _doctor(conn)
    row = {"by": by, "p": patient, "removed": None}
    conn.execute(text(ASSIGN), {**row, "d": doc_a, "primary": True})
    # one active row per (doctor, patient)
    _rejects(conn, ASSIGN, **row, d=doc_a, primary=False)
    # one primary doctor per patient among active rows
    _rejects(conn, ASSIGN, **row, d=doc_b, primary=True)
    conn.execute(text(ASSIGN), {**row, "d": doc_b, "primary": False})
    # removed rows are kept for history and do not block a new active row
    conn.execute(text(ASSIGN), {**row, "d": doc_c, "primary": True, "removed": "2026-01-01"})
    conn.execute(text(ASSIGN), {**row, "d": doc_c, "primary": False})


def test_foreign_keys_restrict(conn: Connection) -> None:
    _rejects(conn, "INSERT INTO doctors (user_id, name) VALUES (:u, 'D')", u=uuid.uuid4())
    uid = _user(conn)
    conn.execute(
        text(
            "INSERT INTO consents (user_id, consent_version, accepted_at) "
            "VALUES (:u, '2026-11-v1', now())"
        ),
        {"u": uid},
    )
    _rejects(conn, "DELETE FROM users WHERE id = :u", u=uid)


def test_health_reports_db_ok(test_db_url: str, engine: Engine) -> None:
    app = create_app(make_settings(database_url=test_db_url))
    try:
        assert TestClient(app).get("/api/v1/health").json()["data"]["db"] == "ok"
    finally:
        app.state.engine.dispose()


@pytest.mark.parametrize(
    ("url", "ref"),
    [
        (
            "postgresql://postgres.abc123:pw@aws-0-ap-south-1.pooler.supabase.com:5432/postgres",
            "abc123",
        ),
        ("postgresql://postgres:pw@db.abc123.supabase.co:5432/postgres", "abc123"),
        ("postgresql://alovia:pw@localhost:5432/alovia", None),
    ],
)
def test_project_ref_same_for_direct_and_pooler(url: str, ref: str | None) -> None:
    # the safety check depends on this: both connection styles of one project give one id
    assert project_ref(url) == ref


def test_phase2_enumerations_and_lengths(conn: Connection) -> None:
    patient, user = _patient(conn), _user(conn)
    appointment = (
        "INSERT INTO appointments (patient_id, appointment_at, has_time, title, note, "
        "created_by, source) VALUES (:p, now(), false, :title, :note, :u, :source)"
    )
    ok = {"p": patient, "u": user, "title": "x" * 100, "note": "n" * 500, "source": "patient"}
    conn.execute(text(appointment), ok)  # the limits themselves are allowed
    _rejects(conn, appointment, **{**ok, "title": "x" * 101})
    _rejects(conn, appointment, **{**ok, "note": "n" * 501})
    _rejects(conn, appointment, **{**ok, "source": "admin"})
    history = (
        "INSERT INTO pregnancy_date_history (patient_id, changed_by, new_source, new_status) "
        "VALUES (:p, :u, :source, :status)"
    )
    conn.execute(
        text(history), {"p": patient, "u": user, "source": "ultrasound", "status": "active"}
    )
    _rejects(conn, history, p=patient, u=user, source="guess", status="active")
    _rejects(conn, history, p=patient, u=user, source="ultrasound", status="paused")
    _rejects(
        conn,
        "INSERT INTO notifications (patient_id, type) VALUES (:p, 'push')",
        p=patient,
    )
    _rejects(
        conn,
        "INSERT INTO inbox_items (patient_id, type, ref_table, ref_id) "
        "VALUES (:p, 'unknown', 'patients', :p)",
        p=patient,
    )


def test_notifications_never_duplicate(conn: Connection) -> None:
    patient = _patient(conn)
    add = "INSERT INTO notifications (patient_id, type, target_ref) VALUES (:p, :type, :ref)"
    conn.execute(text(add), {"p": patient, "type": "new_week", "ref": "24"})
    _rejects(conn, add, p=patient, type="new_week", ref="24")
    conn.execute(text(add), {"p": patient, "type": "new_week", "ref": "25"})
    # an empty target counts as the same target (NULLS NOT DISTINCT)
    conn.execute(text(add), {"p": patient, "type": "dates_updated", "ref": None})
    _rejects(conn, add, p=patient, type="dates_updated", ref=None)


def test_phase2_defaults(conn: Connection) -> None:
    patient = _patient(conn)
    note = conn.execute(
        text(
            "INSERT INTO doctor_notes (patient_id, doctor_id, body) "
            "VALUES (:p, :d, 'Test note') RETURNING visible_to_patient"
        ),
        {"p": patient, "d": _doctor(conn)},
    ).scalar_one()
    assert note is False  # private until the doctor shares it
    item = conn.execute(
        text(
            "INSERT INTO inbox_items (patient_id, type, ref_table, ref_id) "
            "VALUES (:p, 'pregnancy_ended', 'patients', :p) RETURNING seen_at"
        ),
        {"p": patient},
    ).scalar_one()
    assert item is None


def test_symptom_tables_check_their_values(conn: Connection) -> None:
    """Migration 0003 (Symptom spec §13.3): levels, sources and entry values are checked."""
    patient = _patient(conn)
    checkin = (
        "INSERT INTO symptom_checkins (patient_id, source, red_flag_level, matched_rules, "
        "message_keys, pattern_changes, rules_version) "
        "VALUES (:p, :s, :l, '[]', '[]', '[]', '1.0.0') RETURNING id"
    )
    _rejects(conn, checkin, p=patient, s="form", l="L3")
    _rejects(conn, checkin, p=patient, s="sms", l="L0")
    checkin_id = conn.execute(text(checkin), {"p": patient, "s": "form", "l": "L0"}).scalar_one()
    log = (
        "INSERT INTO symptom_logs (checkin_id, patient_id, symptom, severity, duration, "
        "body_area, notes) VALUES (:c, :p, 'fatigue', :sev, :dur, :area, :n)"
    )
    ok = {"c": checkin_id, "p": patient, "sev": "mild", "dur": "under_1_hour", "area": None}
    conn.execute(text(log), {**ok, "n": "x" * 500})
    _rejects(conn, log, **{**ok, "sev": "extreme", "n": None})
    _rejects(conn, log, **{**ok, "dur": "a_week", "n": None})
    _rejects(conn, log, **{**ok, "area": "elbow", "n": None})
    _rejects(conn, log, **{**ok, "n": "x" * 501})


def test_genetic_assessments_check_their_values(conn: Connection) -> None:
    """Migration 0004 (Genetic spec §12.3): priority and review status are checked."""
    patient = _patient(conn)
    user = _user(conn, "patient")
    sql = (
        "INSERT INTO genetic_assessments (patient_id, submitted_by, inputs, results, "
        "rules_version, show_numbers_to_patient, risk_indicated, priority, review_status) "
        "VALUES (:p, :u, '{}', '{}', '1.0.0', true, false, :pr, :rs)"
    )
    conn.execute(text(sql), {"p": patient, "u": user, "pr": "normal", "rs": "pending_review"})
    _rejects(conn, sql, p=patient, u=user, pr="urgent", rs="pending_review")
    _rejects(conn, sql, p=patient, u=user, pr="high", rs="approved")


def test_phase5_enumerations_and_unique_share(conn: Connection) -> None:
    doctor, patient = _doctor(conn), _patient(conn)
    share = (
        "INSERT INTO result_shares (result_type, result_id, shared_by, template_key) "
        "VALUES (:t, :r, :d, 'k')"
    )
    _rejects(conn, share, t="genetic", r=uuid.uuid4(), d=doctor)
    result = uuid.uuid4()
    conn.execute(text(share), {"t": "fetal", "r": result, "d": doctor})
    _rejects(conn, share, t="fetal", r=result, d=doctor)  # a result is shared once
    record = (
        "INSERT INTO medical_records (patient_id, uploaded_by, file_type, storage_path, "
        "original_filename) VALUES (:p, :d, :t, :s, 'f.pdf')"
    )
    _rejects(conn, record, p=patient, d=doctor, t="xray", s="a")
    conn.execute(text(record), {"p": patient, "d": doctor, "t": "other", "s": "b"})
    _rejects(conn, record, p=patient, d=doctor, t="other", s="b")  # storage_path unique
    _rejects(
        conn,
        "INSERT INTO rule_signoffs (module, rules_version, item_id, checked, doctor_id) "
        "VALUES ('dashboard', '1.0.0', 'x', true, :d)",
        d=doctor,
    )
