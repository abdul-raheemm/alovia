"""Doctor routes: patient list, patient records, invite links, inbox (Dashboard spec §5-8,
API.md §4.6). Every route needs an active doctor with consent; patient routes also need an
active assignment (users.service.get_doctor / get_assigned_patient)."""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, File, Form, Request, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.api import API_PREFIX
from app.common.responses import Envelope, ok
from app.core.database import get_db
from app.core.errors import AppError
from app.modules.dashboard import admin, care, predictions, records, rule_review
from app.modules.dashboard import patients as service
from app.modules.dashboard.rule_review import Module as RuleModule
from app.modules.dashboard.rules import load_ranges
from app.modules.dashboard.schemas import (
    AuditEntryOut,
    DoctorAssessmentOut,
    DoctorDatesIn,
    DoctorEndIn,
    DownloadOut,
    GeneticCorrectIn,
    GeneticReviewIn,
    InboxItemOut,
    InviteOut,
    ModelName,
    NoteIn,
    NoteOut,
    PatientDetail,
    PatientIn,
    PatientResultOut,
    PatientRow,
    PredictionIn,
    PredictionSchema,
    RecordOut,
    RecordType,
    ResultOut,
    RuleModuleOut,
    RuleRowOut,
    ShareIn,
    SignoffIn,
    TrendsOut,
)
from app.modules.journey import service as journey
from app.modules.journey.engine import local_today
from app.modules.journey.schemas import AppointmentIn, AppointmentOut, AppointmentsOut
from app.modules.symptoms import service as symptoms
from app.modules.symptoms.schemas import DoctorSymptomsOut
from app.modules.users.models import Patient
from app.modules.users.service import (
    DoctorAccount,
    assigned_patient,
    get_assigned_patient,
    get_doctor,
)
from app.modules.users.service import (
    get_patient as get_own_patient,
)

router = APIRouter(prefix=f"{API_PREFIX}/doctor")

Doc = Annotated[DoctorAccount, Depends(get_doctor)]
Assigned = Annotated[Patient, Depends(get_assigned_patient)]
Db = Annotated[Session, Depends(get_db)]
OwnPatient = Annotated[Patient, Depends(get_own_patient)]


def _detail(request: Request, db: Session, patient: Patient) -> dict[str, Any]:
    cfg = request.app.state.journey_config
    return ok(
        service.patient_detail(db, patient, cfg, local_today(cfg.timezone)).model_dump(mode="json")
    )


@router.get("/patients", response_model=Envelope[list[PatientRow]])
def list_patients(request: Request, account: Doc, db: Db) -> dict[str, Any]:
    cfg = request.app.state.journey_config
    rows = service.list_patients(db, account.doctor.id, cfg, local_today(cfg.timezone))
    return ok([r.model_dump(mode="json") for r in rows])


@router.post("/patients", status_code=201, response_model=Envelope[PatientDetail])
def create_patient(request: Request, body: PatientIn, account: Doc, db: Db) -> dict[str, Any]:
    return _detail(request, db, service.create_patient(db, account, body))


@router.get("/patients/{patient_id}", response_model=Envelope[PatientDetail])
def get_patient(request: Request, patient: Assigned, db: Db) -> dict[str, Any]:
    return _detail(request, db, patient)


@router.put("/patients/{patient_id}", response_model=Envelope[PatientDetail])
def update_patient(
    request: Request, body: PatientIn, patient: Assigned, account: Doc, db: Db
) -> dict[str, Any]:
    service.update_patient(db, account, patient, body)
    return _detail(request, db, patient)


@router.post("/patients/{patient_id}/invite", status_code=201, response_model=Envelope[InviteOut])
def create_invite(request: Request, patient: Assigned, account: Doc, db: Db) -> dict[str, Any]:
    url = request.app.state.settings.patient_app_url
    return ok(service.invite_link(db, account, patient, url).model_dump(mode="json"))


@router.get("/inbox", response_model=Envelope[list[InboxItemOut]])
def list_inbox(account: Doc, db: Db, seen: bool = False) -> dict[str, Any]:
    return ok([i.model_dump(mode="json") for i in service.list_inbox(db, account.doctor.id, seen)])


@router.post("/inbox/{item_id}/seen", response_model=Envelope[InboxItemOut])
def mark_seen(item_id: uuid.UUID, account: Doc, db: Db) -> dict[str, Any]:
    return ok(service.mark_seen(db, account, item_id).model_dump(mode="json"))


# ---- §9-11 predictions, sharing, trends ----


@router.get("/predictions/schema/{model}", response_model=Envelope[PredictionSchema])
def prediction_schema(request: Request, model: ModelName, account: Doc) -> dict[str, Any]:
    rules = request.app.state.dashboard_rules
    return ok(predictions.schema(model, rules, load_ranges()).model_dump(mode="json"))


@router.post(
    "/patients/{patient_id}/predictions/{model}",
    status_code=201,
    response_model=Envelope[ResultOut],
)
def run_prediction(
    request: Request,
    model: ModelName,
    body: PredictionIn,
    patient: Assigned,
    account: Doc,
    db: Db,
) -> dict[str, Any]:
    state = request.app.state
    out = predictions.run(
        db, account, patient, model, body, state.dashboard_rules, load_ranges(), state.models
    )
    return ok(out.model_dump(mode="json"))


@router.get("/patients/{patient_id}/predictions", response_model=Envelope[list[ResultOut]])
def prediction_history(model: ModelName, patient: Assigned, db: Db) -> dict[str, Any]:
    return ok([r.model_dump(mode="json") for r in predictions.history(db, patient, model)])


@router.get("/patients/{patient_id}/trends", response_model=Envelope[TrendsOut])
def prediction_trends(request: Request, patient: Assigned, db: Db) -> dict[str, Any]:
    features = request.app.state.dashboard_rules.settings.fetal_trend_features
    return ok(predictions.trends(db, patient, features).model_dump(mode="json"))


@router.post(
    "/predictions/{model}/{result_id}/share", status_code=201, response_model=Envelope[ResultOut]
)
def share_result(
    model: ModelName, result_id: uuid.UUID, body: ShareIn, account: Doc, db: Db
) -> dict[str, Any]:
    return ok(predictions.share(db, account, model, result_id, body).model_dump(mode="json"))


# ---- task 4: genetic review, symptoms, notes, appointments, dates, status ----


@router.get("/genetic/review-queue", response_model=Envelope[list[DoctorAssessmentOut]])
def genetic_queue(account: Doc, db: Db) -> dict[str, Any]:
    """Genetic §10.1: pending assessments of the doctor's patients, high priority first."""
    return ok([a.model_dump(mode="json") for a in care.review_queue(db, account.doctor.id)])


@router.get("/patients/{patient_id}/genetic", response_model=Envelope[list[DoctorAssessmentOut]])
def patient_genetic(patient: Assigned, db: Db) -> dict[str, Any]:
    return ok([a.model_dump(mode="json") for a in care.patient_assessments(db, patient)])


@router.post(
    "/genetic/assessments/{assessment_id}/review", response_model=Envelope[DoctorAssessmentOut]
)
def genetic_review(
    assessment_id: uuid.UUID, body: GeneticReviewIn, account: Doc, db: Db
) -> dict[str, Any]:
    return ok(care.confirm(db, account, assessment_id, body.doctor_note).model_dump(mode="json"))


@router.post(
    "/genetic/assessments/{assessment_id}/correct",
    status_code=201,
    response_model=Envelope[DoctorAssessmentOut],
)
def genetic_correct(
    request: Request, assessment_id: uuid.UUID, body: GeneticCorrectIn, account: Doc, db: Db
) -> dict[str, Any]:
    rules = request.app.state.genetic_rules
    return ok(care.correct(db, account, assessment_id, body, rules).model_dump(mode="json"))


@router.get("/patients/{patient_id}/symptoms", response_model=Envelope[DoctorSymptomsOut])
def patient_symptoms(request: Request, patient: Assigned, db: Db) -> dict[str, Any]:
    """Symptom §12 / Dashboard §13, read-only."""
    tz = request.app.state.journey_config.timezone
    out = symptoms.doctor_view(db, patient, request.app.state.symptom_rules, tz)
    return ok(out.model_dump(mode="json"))


@router.get("/patients/{patient_id}/notes", response_model=Envelope[list[NoteOut]])
def list_notes(patient: Assigned, db: Db) -> dict[str, Any]:
    return ok([n.model_dump(mode="json") for n in care.list_notes(db, patient)])


@router.post("/patients/{patient_id}/notes", status_code=201, response_model=Envelope[NoteOut])
def write_note(body: NoteIn, patient: Assigned, account: Doc, db: Db) -> dict[str, Any]:
    return ok(care.write_note(db, account, patient, body).model_dump(mode="json"))


@router.post("/notes/{note_id}/share", response_model=Envelope[NoteOut])
def share_note(note_id: uuid.UUID, account: Doc, db: Db) -> dict[str, Any]:
    return ok(care.share_note(db, account, note_id).model_dump(mode="json"))


@router.get("/patients/{patient_id}/appointments", response_model=Envelope[AppointmentsOut])
def list_appointments(request: Request, patient: Assigned, db: Db) -> dict[str, Any]:
    """Dashboard §16: all her appointments; `can_edit` marks the doctor-added ones."""
    tz = request.app.state.journey_config.timezone
    out = journey.list_appointments(db, patient, tz, local_today(tz), viewer="doctor")
    return ok(out.model_dump(mode="json"))


@router.post(
    "/patients/{patient_id}/appointments", status_code=201, response_model=Envelope[AppointmentOut]
)
def add_appointment(
    request: Request, body: AppointmentIn, patient: Assigned, account: Doc, db: Db
) -> dict[str, Any]:
    tz = request.app.state.journey_config.timezone
    out = journey.create_appointment(db, account.user, patient, body, tz, editor="doctor")
    return ok(out.model_dump(mode="json"))


def _appointment_patient(db: Session, account: DoctorAccount, appointment_id: uuid.UUID) -> Patient:
    patient_id = journey.appointment_patient_id(db, appointment_id)
    if patient_id is None:
        raise AppError("NOT_FOUND", "We couldn't find this.", status=404)
    return assigned_patient(db, account.doctor.id, patient_id)


@router.put("/appointments/{appointment_id}", response_model=Envelope[AppointmentOut])
def edit_appointment(
    request: Request, appointment_id: uuid.UUID, body: AppointmentIn, account: Doc, db: Db
) -> dict[str, Any]:
    patient = _appointment_patient(db, account, appointment_id)
    tz = request.app.state.journey_config.timezone
    out = journey.update_appointment(
        db, account.user, patient, appointment_id, body, tz, editor="doctor"
    )
    return ok(out.model_dump(mode="json"))


@router.delete("/appointments/{appointment_id}", response_model=Envelope[None])
def remove_appointment(appointment_id: uuid.UUID, account: Doc, db: Db) -> dict[str, Any]:
    patient = _appointment_patient(db, account, appointment_id)
    journey.delete_appointment(db, account.user, patient, appointment_id, editor="doctor")
    return ok(None)


@router.put("/patients/{patient_id}/dates", response_model=Envelope[PatientDetail])
def set_dates(
    request: Request,
    body: Annotated[DoctorDatesIn, Body()],
    patient: Assigned,
    account: Doc,
    db: Db,
) -> dict[str, Any]:
    """Dashboard §8.3: a clinician-confirmed or ultrasound date (Journey §5 rules, incl. D2);
    logged; the patient gets a dates_updated notification."""
    today = local_today(request.app.state.journey_config.timezone)
    journey.set_dates(db, account.user, patient, body, today)
    return _detail(request, db, patient)


@router.post("/patients/{patient_id}/pregnancy-end", response_model=Envelope[PatientDetail])
def end_pregnancy(
    request: Request, body: DoctorEndIn, patient: Assigned, account: Doc, db: Db
) -> dict[str, Any]:
    """Dashboard §17: the same three choices; no pregnancy_ended inbox item."""
    journey.end_pregnancy(db, account.user, patient, body.status, None)
    return _detail(request, db, patient)


# ---- task 6: rule review (§19) and the patient's activity log (§20) ----


@router.get("/rules", response_model=Envelope[list[RuleModuleOut]])
def rules_overview(request: Request, account: Doc, db: Db) -> dict[str, Any]:
    state = request.app.state
    out = rule_review.overview(db, state.genetic_rules, state.symptom_rules)
    return ok([m.model_dump(mode="json") for m in out])


@router.post("/rules/{module}/signoff", status_code=201, response_model=Envelope[RuleRowOut])
def rule_signoff(
    request: Request, module: RuleModule, body: SignoffIn, account: Doc, db: Db
) -> dict[str, Any]:
    state = request.app.state
    out = rule_review.sign(db, account, module, body, state.genetic_rules, state.symptom_rules)
    return ok(out.model_dump(mode="json"))


@router.get("/rules/{module}/export", response_class=PlainTextResponse)
def rule_export(request: Request, module: RuleModule, account: Doc, db: Db) -> PlainTextResponse:
    """§19 Export as a Markdown file download (DEC-080)."""
    state = request.app.state
    text = rule_review.export_markdown(db, module, state.genetic_rules, state.symptom_rules)
    return PlainTextResponse(
        text,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="rule_review_signoff_{module}.md"'},
    )


@router.get("/patients/{patient_id}/audit", response_model=Envelope[list[AuditEntryOut]])
def patient_audit(patient: Assigned, db: Db) -> dict[str, Any]:
    """§4 / §20: the log entries of an assigned patient (no clinical values)."""
    return ok([e.model_dump(mode="json") for e in admin.patient_audit(db, patient.id)])


patient_router = APIRouter(prefix=f"{API_PREFIX}/patient")


@patient_router.get("/results", response_model=Envelope[list[PatientResultOut]])
def my_results(request: Request, patient: OwnPatient, db: Db) -> dict[str, Any]:
    """API.md §4.5: shared fetal/maternal results only (template + doctor message)."""
    rules = request.app.state.dashboard_rules
    return ok([r.model_dump(mode="json") for r in predictions.patient_results(db, patient, rules)])


# ---- task 5: medical records (§14) ----


@router.get("/patients/{patient_id}/records", response_model=Envelope[list[RecordOut]])
def list_records(patient: Assigned, db: Db) -> dict[str, Any]:
    return ok([r.model_dump(mode="json") for r in records.list_records(db, patient)])


@router.post("/patients/{patient_id}/records", status_code=201, response_model=Envelope[RecordOut])
def upload_record(
    request: Request,
    file: Annotated[UploadFile, File()],
    file_type: Annotated[RecordType, Form()],
    patient: Assigned,
    account: Doc,
    db: Db,
    note: Annotated[str | None, Form(max_length=500)] = None,
) -> dict[str, Any]:
    """multipart/form-data: file, file_type, optional note (API.md §2)."""
    settings = request.app.state.dashboard_rules.settings
    # read one byte past the limit, so an oversized file is refused without reading it all
    data = file.file.read(settings.record_max_mb * 1024 * 1024 + 1)
    out = records.upload(
        db,
        request.app.state.storage,
        settings,
        account,
        patient,
        file.filename or "",
        data,
        file_type,
        (note or "").strip() or None,
    )
    return ok(out.model_dump(mode="json"))


@router.get("/records/{record_id}/download", response_model=Envelope[DownloadOut])
def download_record(request: Request, record_id: uuid.UUID, account: Doc, db: Db) -> dict[str, Any]:
    settings = request.app.state.dashboard_rules.settings
    url = records.download_link(db, request.app.state.storage, settings, account, record_id)
    return ok(DownloadOut(url=url, expires_in=settings.signed_url_minutes * 60).model_dump())
