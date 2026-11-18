"""Symptom check-ins: validate, run the rules, save, notify the doctor's inbox, and read history
(Symptom spec §4-10; API.md §4.3)."""

import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.logging import logger
from app.modules.dashboard import service as dashboard
from app.modules.symptoms import engine
from app.modules.symptoms.models import SymptomCheckin, SymptomLog
from app.modules.symptoms.rules import SymptomRules
from app.modules.symptoms.schemas import (
    ChartsOut,
    CheckinHistoryOut,
    CheckinIn,
    CheckinOut,
    EntryOut,
    PuqePoint,
    SymptomPoint,
    SymptomSeries,
)
from app.modules.users.models import Patient

INBOX_FOR_LEVEL = {"L1": "symptom_l1", "L2": "symptom_l2"}


def logging_open(patient: Patient) -> bool:
    """DEC-064: postpartum is out of scope (D1); after the end the screens show the
    after-pregnancy safety message instead of the pregnancy form."""
    return patient.pregnancy_status == "active"


def _details(e: engine.Entry, rules: SymptomRules) -> dict[str, Any] | None:
    details: dict[str, Any] = {flag: True for flag in sorted(e.flags)}
    if e.puqe_answers:
        details |= {
            "puqe_answers": list(e.puqe_answers),
            "puqe_score": e.puqe_score,
            "puqe_band": engine.puqe_band(e, rules),
        }
    if e.text is not None:
        details["name" if e.symptom == "other" else "food"] = e.text
    if e.choice is not None:
        details["appetite"] = e.choice
    return details or None


def _history(db: Session, patient: Patient, tz: ZoneInfo, since: datetime) -> engine.History:
    """Everything the §9 pattern rules need: every earlier entry (P1 is "first time ever") and
    the L2 check-ins inside the window."""
    rows = db.execute(
        select(SymptomLog, SymptomCheckin.created_at)
        .join(SymptomCheckin, SymptomCheckin.id == SymptomLog.checkin_id)
        .where(SymptomLog.patient_id == patient.id)
        .order_by(SymptomCheckin.created_at)
    )
    entries = []
    for log, created in rows:
        d = log.details or {}
        name = d.get("name") if log.symptom == "other" else None
        key = f"other:{str(name).strip().lower()}" if name else log.symptom
        entries.append(
            engine.PastEntry(
                key, log.severity, d.get("puqe_band"), created, created.astimezone(tz).date()
            )
        )
    l2 = db.scalars(
        select(SymptomCheckin.created_at).where(
            SymptomCheckin.patient_id == patient.id,
            SymptomCheckin.red_flag_level == "L2",
            SymptomCheckin.created_at >= since,
        )
    )
    return engine.History(entries=entries, l2_checkins=list(l2))


def create_checkin(
    db: Session,
    patient: Patient,
    body: CheckinIn,
    rules: SymptomRules,
    week: int | None,
    timezone: str,
) -> CheckinOut:
    """§4.1: validate (V1/V2: nothing saved), run the rules, save, then add the doctor's inbox
    items, all in one transaction. Any unexpected engine failure saves the check-in as L2 with
    `ERR` and the safe fallback message (V3), and is logged."""
    if not logging_open(patient):
        raise AppError("CONFLICT", "Symptom logging is for an active pregnancy.", status=409)
    raw = [e.model_dump(exclude_none=True) for e in body.entries]
    try:
        entries = engine.validate(raw, body.source, rules, week)
    except engine.CheckinError as exc:
        raise AppError(
            "VALIDATION_ERROR", "Please check your entries.", fields={exc.field: exc.code}
        ) from exc
    tz = ZoneInfo(timezone)
    now = datetime.now(UTC)
    try:
        result = engine.assess(entries, week, rules)
        history = _history(
            db, patient, tz, now - timedelta(days=rules.settings.pattern_window_days)
        )
        patterns = engine.pattern_changes(
            entries, result.level, history, now, now.astimezone(tz).date(), rules
        )
    except Exception:  # §6 V3: never lose the check-in, never hide advice
        logger.exception("symptom engine failed", extra={"reason": "V3 fallback"})
        result, patterns = engine.FALLBACK, []
    checkin = SymptomCheckin(
        patient_id=patient.id,
        source=body.source,
        pregnancy_week=week,
        red_flag_level=result.level,
        matched_rules=result.matched_rules,
        message_keys=result.message_keys,
        pattern_changes=patterns,
        rules_version=rules.settings.rules_version,
    )
    db.add(checkin)
    db.flush()
    for e in entries:
        db.add(
            SymptomLog(
                checkin_id=checkin.id,
                patient_id=patient.id,
                symptom=e.symptom,
                severity=e.severity,
                duration=e.duration,
                body_area=e.body_area,
                details=_details(e, rules),
                occurred_at=e.occurred_at,
                notes=e.notes,
            )
        )
    inbox = [INBOX_FOR_LEVEL[result.level]] if result.level in INBOX_FOR_LEVEL else []
    inbox += sorted({f"pattern_{p['code']}".lower() for p in patterns})
    for type_ in inbox:
        dashboard.add_inbox_item(db, patient.id, type_, "symptom_checkins", checkin.id)
    db.commit()
    db.refresh(checkin)
    return CheckinOut(
        checkin_id=checkin.id,
        created_at=checkin.created_at,
        pregnancy_week=checkin.pregnancy_week,
        red_flag_level=result.level,
        matched_rules=result.matched_rules,
        message_keys=result.message_keys,
    )


def list_checkins(
    db: Session, patient: Patient, rules: SymptomRules, timezone: str
) -> list[CheckinHistoryOut]:
    """Her own check-ins, newest first, with their entries in form order (warning signs, then
    everyday symptoms; entries of one check-in share a timestamp). Pattern changes are never
    returned to the patient (§9, §14 test 8)."""
    tz = ZoneInfo(timezone)
    form_order = [s.id for s in rules.vocabulary.warning] + [s.id for s in rules.vocabulary.common]
    position = {symptom: i for i, symptom in enumerate(form_order)}
    checkins = list(
        db.scalars(
            select(SymptomCheckin)
            .where(SymptomCheckin.patient_id == patient.id)
            .order_by(SymptomCheckin.created_at.desc())
        )
    )
    logs: dict[uuid.UUID, list[SymptomLog]] = {c.id: [] for c in checkins}
    for log in db.scalars(
        select(SymptomLog)
        .where(SymptomLog.patient_id == patient.id)
        .order_by(SymptomLog.created_at, SymptomLog.id)
    ):
        logs.setdefault(log.checkin_id, []).append(log)
    return [
        CheckinHistoryOut(
            checkin_id=c.id,
            created_at=c.created_at,
            local_date=c.created_at.astimezone(tz).date(),
            pregnancy_week=c.pregnancy_week,
            source=c.source,
            red_flag_level=c.red_flag_level,
            matched_rules=c.matched_rules,
            message_keys=c.message_keys,
            entries=[
                EntryOut(
                    symptom=log.symptom,
                    severity=log.severity,
                    duration=log.duration,
                    body_area=log.body_area,
                    details=log.details,
                    occurred_at=log.occurred_at,
                    notes=log.notes,
                )
                for log in sorted(logs[c.id], key=lambda g: position.get(g.symptom, 99))
            ],
        )
        for c in checkins
    ]


def charts(db: Session, patient: Patient, rules: SymptomRules, timezone: str) -> ChartsOut:
    """§4.3 chart data: every entry of each symptom (date, week, severity, duration) and every
    PUQE score with its band, oldest first. The app counts and draws them."""
    tz = ZoneInfo(timezone)
    labels = {s.id: s.label for s in rules.vocabulary.common}
    labels |= {s.id: s.label for s in rules.vocabulary.warning}
    series: dict[str, list[SymptomPoint]] = {}
    puqe: list[PuqePoint] = []
    rows = db.execute(
        select(SymptomLog, SymptomCheckin.created_at, SymptomCheckin.pregnancy_week)
        .join(SymptomCheckin, SymptomCheckin.id == SymptomLog.checkin_id)
        .where(SymptomLog.patient_id == patient.id)
        .order_by(SymptomCheckin.created_at)
    )
    for log, created, week in rows:
        day: date = created.astimezone(tz).date()
        series.setdefault(log.symptom, []).append(
            SymptomPoint(
                local_date=day, pregnancy_week=week, severity=log.severity, duration=log.duration
            )
        )
        d = log.details or {}
        if "puqe_score" in d:
            puqe.append(
                PuqePoint(
                    local_date=day,
                    pregnancy_week=week,
                    score=int(d["puqe_score"]),
                    band=str(d["puqe_band"]),
                )
            )
    return ChartsOut(
        symptoms=[
            SymptomSeries(symptom=s, label=labels.get(s, s), points=points)
            for s, points in series.items()
        ],
        puqe=puqe,
    )
