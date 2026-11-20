"""Medical records (Dashboard spec §14, SECURITY.md §8): upload to the private bucket, list,
short-lived download links. Not deleted in v1; patients cannot see them in v1 ([OPEN])."""

import uuid
from pathlib import PureWindowsPath

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.storage import Storage
from app.modules.dashboard import service as dashboard
from app.modules.dashboard.models import MedicalRecord
from app.modules.dashboard.rules import DashboardSettings
from app.modules.dashboard.schemas import RecordOut
from app.modules.users.models import Doctor, DoctorPatientAssignment, Patient
from app.modules.users.service import DoctorAccount, add_audit, assigned_patient

# §14 formats: the file's first bytes must match its extension (SECURITY.md §8)
SIGNATURES: dict[str, tuple[bytes, str]] = {
    "pdf": (b"%PDF-", "application/pdf"),
    "png": (b"\x89PNG\r\n\x1a\n", "image/png"),
    "jpg": (b"\xff\xd8\xff", "image/jpeg"),
}
EXTENSIONS = {"pdf": "pdf", "png": "png", "jpg": "jpg", "jpeg": "jpg"}
NOT_ALLOWED = "Only PDF, JPG, PNG"


def file_format(filename: str, head: bytes, allowed: tuple[str, ...]) -> str:
    """The checked format, or 415: allowed extension AND matching file signature."""
    ext = EXTENSIONS.get(PureWindowsPath(filename).suffix.lower().lstrip("."))
    if ext is None or ext not in allowed or not head.startswith(SIGNATURES[ext][0]):
        raise AppError("UNSUPPORTED_FILE_TYPE", NOT_ALLOWED, status=415)
    return ext


def _out(row: MedicalRecord, names: dict[uuid.UUID, str]) -> RecordOut:
    return RecordOut(
        id=row.id,
        file_type=row.file_type,  # CHECK constraint keeps it to the four types
        original_filename=row.original_filename,
        note=row.note,
        uploaded_at=row.uploaded_at,
        uploaded_by_name=names.get(row.uploaded_by),
    )


def list_records(db: Session, patient: Patient) -> list[RecordOut]:
    rows = list(
        db.scalars(
            select(MedicalRecord)
            .where(MedicalRecord.patient_id == patient.id)
            .order_by(MedicalRecord.uploaded_at.desc())
        )
    )
    ids = {r.uploaded_by for r in rows}
    names = dict(db.execute(select(Doctor.id, Doctor.name).where(Doctor.id.in_(ids))).all())
    return [_out(r, names) for r in rows]


def upload(
    db: Session,
    storage: Storage,
    settings: DashboardSettings,
    account: DoctorAccount,
    patient: Patient,
    filename: str,
    data: bytes,
    file_type: str,
    note: str | None,
) -> RecordOut:
    """§14: checked file -> private bucket at patients/{patient_id}/{uuid}.{ext} -> one row.
    Other assigned doctors get a `record_uploaded` inbox item (§7.1).
    shortcut: if saving the row fails after the upload, the stored file is left unreferenced;
    add a clean-up when Phase 8 handles data deletion."""
    if len(data) > settings.record_max_mb * 1024 * 1024:
        raise AppError(
            "FILE_TOO_LARGE", f"File too large (max {settings.record_max_mb} MB)", status=413
        )
    ext = file_format(filename, data[:16], settings.record_formats)
    path = f"patients/{patient.id}/{uuid.uuid4()}.{ext}"
    storage.upload(path, data, SIGNATURES[ext][1])
    row = MedicalRecord(
        patient_id=patient.id,
        uploaded_by=account.doctor.id,
        file_type=file_type,
        storage_path=path,
        # PureWindowsPath splits on both \ and /, whatever system the server runs on
        original_filename=PureWindowsPath(filename).name[:255] or f"record.{ext}",
        note=note,
    )
    db.add(row)
    db.flush()
    others = db.scalar(
        select(DoctorPatientAssignment.id).where(
            DoctorPatientAssignment.patient_id == patient.id,
            DoctorPatientAssignment.removed_at.is_(None),
            DoctorPatientAssignment.doctor_id != account.doctor.id,
        )
    )
    if others is not None:
        dashboard.add_inbox_item(db, patient.id, "record_uploaded", "medical_records", row.id)
    add_audit(db, account.user, "record uploaded", "medical_record", row.id, patient.id)
    db.commit()
    db.refresh(row)
    return _out(row, {account.doctor.id: account.doctor.name})


def download_link(
    db: Session,
    storage: Storage,
    settings: DashboardSettings,
    account: DoctorAccount,
    record_id: uuid.UUID,
) -> str:
    """§14: a signed link valid `signed_url_minutes`; only for an assigned doctor."""
    row = db.get(MedicalRecord, record_id)
    if row is None:
        raise AppError("NOT_FOUND", "We couldn't find this.", status=404)
    assigned_patient(db, account.doctor.id, row.patient_id)
    url = storage.signed_url(row.storage_path, settings.signed_url_minutes * 60)
    add_audit(db, account.user, "record downloaded", "medical_record", row.id, row.patient_id)
    db.commit()
    return url
