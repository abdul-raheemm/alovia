"""Dashboard data that other modules read (ARCHITECTURE §8: through this service, never the
models). Phase 2: shared doctor notes for the patient app (Journey §10.3)."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.dashboard.models import DoctorNote, InboxItem
from app.modules.users.models import Doctor


@dataclass(frozen=True)
class SharedNote:
    id: uuid.UUID
    body: str
    doctor_name: str
    created_at: datetime
    related_ref: str | None


def shared_notes(db: Session, patient_id: uuid.UUID) -> list[SharedNote]:
    """Notes her doctors chose to share (visible_to_patient), newest first."""
    rows = db.execute(
        select(DoctorNote, Doctor.name)
        .join(Doctor, Doctor.id == DoctorNote.doctor_id)
        .where(DoctorNote.patient_id == patient_id, DoctorNote.visible_to_patient.is_(True))
        .order_by(DoctorNote.created_at.desc())
    )
    return [
        SharedNote(note.id, note.body, name, note.created_at, note.related_ref)
        for note, name in rows
    ]


def add_inbox_item(
    db: Session, patient_id: uuid.UUID, type_: str, ref_table: str, ref_id: uuid.UUID
) -> None:
    """Add a needs-attention item to the doctor inbox. The caller commits, so the item is
    saved in the same transaction as the event it points to."""
    db.add(InboxItem(patient_id=patient_id, type=type_, ref_table=ref_table, ref_id=ref_id))
