"""Rule review screen (Dashboard spec §19): every row of the genetic, symptom and Journey
review sheets with its latest sign-off, saving a sign-off, the Markdown export (downloaded,
DEC-080), and the `require_signoff` start-up check (DEC-081).

The rows come from each module's `review.py`, the same code that writes the CSV sheets, so the
screen and the sheets always match (DEC-082, DEC-100). Sign-offs are stored per rules version;
the Journey has no version of its own, so its version is a short hash of its rows (DEC-099).
"""

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.dashboard.models import RuleSignoff
from app.modules.dashboard.schemas import RuleModuleOut, RuleRowOut, SignoffIn
from app.modules.genetic import review as genetic_review
from app.modules.genetic.rules import GeneticRules
from app.modules.journey import review as journey_review
from app.modules.symptoms import review as symptom_review
from app.modules.symptoms.rules import SymptomRules
from app.modules.users.models import Doctor
from app.modules.users.service import DoctorAccount, add_audit

Module = Literal["genetic", "symptom", "journey"]
MODULES: tuple[Module, ...] = ("genetic", "symptom", "journey")
FIELDS = ("section", "what_to_check", "current_value", "source")


@dataclass(frozen=True)
class Row:
    key: str  # "<section number>:<id>", unique within a module
    item_id: str
    section: str
    what_to_check: str
    current_value: str
    source: str


def _rows(raw: list[dict[str, str]], id_field: str) -> list[Row]:
    return [
        Row(
            key=f"{r['section'].split(' ')[0]}:{r[id_field]}",
            item_id=r[id_field],
            **{f: r[f] for f in FIELDS},
        )
        for r in raw
    ]


def module_rows(
    module: Module, genetic: GeneticRules, symptoms: SymptomRules
) -> tuple[str, list[Row]]:
    """(rules version, rows) for one module, from the live rule and content files."""
    if module == "genetic":
        return genetic.settings.rules_version, _rows(genetic_review.rows(genetic), "item_id")
    if module == "symptom":
        return symptoms.settings.rules_version, _rows(symptom_review.rows(symptoms), "item_id")
    rows = _rows(journey_review.rows(), "id")
    content = json.dumps([r.__dict__ for r in rows], sort_keys=True, ensure_ascii=False)
    return "j-" + hashlib.sha256(content.encode()).hexdigest()[:12], rows


def _latest(db: Session, module: Module, version: str) -> dict[str, RuleSignoff]:
    """Sign-offs are append-only: the newest row per item is its state."""
    latest: dict[str, RuleSignoff] = {}
    for s in db.scalars(
        select(RuleSignoff)
        .where(RuleSignoff.module == module, RuleSignoff.rules_version == version)
        .order_by(RuleSignoff.created_at.desc(), RuleSignoff.id)
    ):
        latest.setdefault(s.item_id, s)
    return latest


def _names(db: Session, ids: set[uuid.UUID]) -> dict[uuid.UUID, str]:
    if not ids:
        return {}
    rows = db.execute(select(Doctor.id, Doctor.name).where(Doctor.id.in_(ids)))
    return {doctor_id: name for doctor_id, name in rows}


def _row_out(row: Row, s: RuleSignoff | None, names: dict[uuid.UUID, str]) -> RuleRowOut:
    return RuleRowOut(
        key=row.key,
        item_id=row.item_id,
        section=row.section,
        what_to_check=row.what_to_check,
        current_value=row.current_value,
        source=row.source,
        checked=s.checked if s else None,
        comment=s.comment if s else None,
        doctor_name=names.get(s.doctor_id) if s else None,
        signed_at=s.created_at if s else None,
    )


def overview(db: Session, genetic: GeneticRules, symptoms: SymptomRules) -> list[RuleModuleOut]:
    out = []
    for module in MODULES:
        version, rows = module_rows(module, genetic, symptoms)
        latest = _latest(db, module, version)
        names = _names(db, {s.doctor_id for s in latest.values()})
        out.append(
            RuleModuleOut(
                module=module,
                rules_version=version,
                total=len(rows),
                checked=sum(1 for r in rows if (s := latest.get(r.key)) and s.checked),
                rows=[_row_out(r, latest.get(r.key), names) for r in rows],
            )
        )
    return out


def sign(
    db: Session,
    account: DoctorAccount,
    module: Module,
    body: SignoffIn,
    genetic: GeneticRules,
    symptoms: SymptomRules,
) -> RuleRowOut:
    """§19: any doctor ticks "checked" (or not) with an optional comment, for the current
    rules version; a new row each time (append-only)."""
    version, rows = module_rows(module, genetic, symptoms)
    row = next((r for r in rows if r.key == body.key), None)
    if row is None:
        raise AppError("NOT_FOUND", "We couldn't find this rule row.", status=404)
    s = RuleSignoff(
        module=module,
        rules_version=version,
        item_id=row.key,
        checked=body.checked,
        comment=body.comment,
        doctor_id=account.doctor.id,
    )
    db.add(s)
    db.flush()
    add_audit(db, account.user, "rule signed off", "rule_signoff", s.id, None)
    db.commit()
    db.refresh(s)
    return _row_out(row, s, {account.doctor.id: account.doctor.name})


def _cell(text: str | None) -> str:
    return (text or "").replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def export_markdown(
    db: Session, module: Module, genetic: GeneticRules, symptoms: SymptomRules
) -> str:
    """§19 "Export": the sign-off file for one module, saved by the owner into
    docs/modules/reviews/ (DEC-080)."""
    m = next(x for x in overview(db, genetic, symptoms) if x.module == module)
    lines = [
        f"# Rule review sign-off — {module}",
        "",
        f"Rules version: `{m.rules_version}` · checked {m.checked} of {m.total} · "
        f"exported {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')} from the doctor app "
        "(Dashboard spec §19).",
        "",
        "| Item | Section | What to check | Current value | Checked | By | When | Comment |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in m.rows:
        state = {True: "yes", False: "no", None: ""}[r.checked]
        when = r.signed_at.strftime("%Y-%m-%d") if r.signed_at else ""
        lines.append(
            "| "
            + " | ".join(
                _cell(v)
                for v in (
                    r.key,
                    r.section,
                    r.what_to_check,
                    r.current_value,
                    state,
                    r.doctor_name,
                    when,
                    r.comment,
                )
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def unsigned(engine: Engine, genetic: GeneticRules, symptoms: SymptomRules) -> dict[str, int]:
    """Rows not checked "yes" for each module's current rules version."""
    with Session(engine) as db:
        return {
            m.module: m.total - m.checked
            for m in overview(db, genetic, symptoms)
            if m.total - m.checked
        }


def require_signoff(engine: Engine, genetic: GeneticRules, symptoms: SymptomRules) -> None:
    """DEC-081: with `require_signoff = true` the backend refuses to start while any rule row
    of the current rules versions is unchecked."""
    missing = unsigned(engine, genetic, symptoms)
    if missing:
        detail = ", ".join(f"{m}: {n} rows" for m, n in missing.items())
        raise RuntimeError(f"require_signoff is on and rule rows are not signed off ({detail})")
