"""Request and response shapes for the doctor home, patients and inbox (Dashboard spec §5-8,
API.md §4.6)."""

import uuid
from datetime import date, datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.modules.genetic.engine import Assessment
from app.modules.genetic.schemas import AssessmentIn
from app.modules.journey.schemas import DueDateIn, EndStatus, UltrasoundDatesIn

INBOX_TYPE = Literal[
    "symptom_l1",
    "symptom_l2",
    "pattern_p1",
    "pattern_p2",
    "pattern_p3",
    "pattern_p4",
    "pattern_p5",
    "genetic_pending",
    "genetic_high_priority",
    "pregnancy_ended",
    "record_uploaded",
    "ai_note_flag",
    "chat_urgent",
]


class PatientIn(BaseModel):
    """§8.1 create / edit: name, optional age and notes."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    # DEC-023: patients are 18+; the upper bound only stops typing mistakes
    age: int | None = Field(default=None, ge=18, le=120)
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("name")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name is required")
        return value.strip()


class LatestClass(BaseModel):
    predicted_class: str
    created_at: datetime


class GeneticStatus(BaseModel):
    review_status: str
    priority: str
    created_at: datetime


class SymptomLevel(BaseModel):
    level: str
    created_at: datetime


class PatientRow(BaseModel):
    """§6 patient list row. Model labels are returned as text; colour is only a help."""

    id: uuid.UUID
    name: str
    linked: bool
    ga_weeks: int | None
    ga_days: int | None
    due_date: date | None
    fetal: LatestClass | None
    maternal: LatestClass | None
    genetic: GeneticStatus | None
    symptom: SymptomLevel | None
    unseen_count: int
    pregnancy_status: str
    group: int  # §6 default order: 1-4


class AssignedDoctor(BaseModel):
    id: uuid.UUID
    name: str
    is_primary: bool


class PatientDetail(PatientRow):
    """§5.1 Overview tab (the AI-1 summary is Phase 6)."""

    age: int | None
    notes: str | None
    due_date_source: str | None
    doctors: list[AssignedDoctor]
    hba1c_note: bool  # §9.5 shown beside the HbA1c field


class InviteOut(BaseModel):
    """§8.2: the link is shown once; only the code's hash is stored."""

    link: str
    expires_at: datetime


class InboxItemOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    patient_name: str
    type: INBOX_TYPE
    ref_table: str
    ref_id: uuid.UUID
    created_at: datetime
    seen_by_name: str | None
    seen_at: datetime | None


# ---- §9-11 predictions, sharing, trends ----

ModelName = Literal["fetal", "maternal"]
FiniteFloat = Annotated[float, Field(allow_inf_nan=False)]


class UnitSwitch(BaseModel):
    """§9.3 a field with a unit switch: the model unit and the one other unit accepted."""

    name: str  # hba1c / glucose / temperature
    model_unit: str
    other_unit: str
    default: str


class FieldRange(BaseModel):
    min: float
    max: float


class SchemaField(BaseModel):
    feature: str
    label: str
    range: FieldRange  # §9.4 training range, in model units
    unit: UnitSwitch | None


class SchemaGroup(BaseModel):
    label: str
    fields: list[SchemaField]


class ConversionOut(BaseModel):
    """§9.3 model = entered * multiply / divide + add, for the form's preview."""

    multiply: float
    divide: float
    add: float


class PredictionSchema(BaseModel):
    """§9.1 form, built from the model's feature order and the config file."""

    model: ModelName
    groups: list[SchemaGroup]
    limitation_keys: list[str]  # §9.6, shown beside every prediction
    messages: dict[str, str | None]  # dashboard texts (null = pending doctor approval)
    conversions: dict[str, ConversionOut]


class PredictionIn(BaseModel):
    """§9.2: every model input as typed, plus the unit chosen on each switch."""

    model_config = ConfigDict(extra="forbid")

    values: dict[str, FiniteFloat]
    units: dict[str, str] = {}


class Factor(BaseModel):
    feature: str
    impact: float
    direction: str


class ShareOut(BaseModel):
    shared_at: datetime
    shared_by_name: str | None
    template_key: str
    doctor_message: str | None


class ResultOut(BaseModel):
    """§9.7 everything the doctor sees for one prediction. Never editable (§1.3)."""

    id: uuid.UUID
    model: ModelName
    created_at: datetime
    predicted_class: str
    confidence: float
    class_probabilities: dict[str, float]
    top_contributing_factors: list[Factor]
    input_values: dict[str, float]  # model units
    entered_values: dict[str, Any] | None  # {feature: {value, unit}} as typed
    range_warnings: list[str]
    model_version: str | None
    entered_by_name: str | None
    hba1c_note: bool  # §9.5, maternal only
    share: ShareOut | None


class ShareIn(BaseModel):
    """§10 step 2: an optional doctor message (the AI-2 draft is Phase 6)."""

    model_config = ConfigDict(extra="forbid")

    doctor_message: str | None = Field(default=None, max_length=1000)


class TrendPoint(BaseModel):
    result_id: uuid.UUID
    created_at: datetime
    ga_week: int | None  # gestational week on that day, when the due date is known
    predicted_class: str
    values: dict[str, float]  # model units


class TrendsOut(BaseModel):
    """§11: raw values over time, in model units; no arrows, scores or interpretations."""

    maternal_features: list[str]
    fetal_features: list[str]
    maternal: list[TrendPoint]
    fetal: list[TrendPoint]


class PatientResultOut(BaseModel):
    """§10 step 4 / UX P10: the class in plain words (doctor-approved template) and the
    doctor's message only."""

    id: uuid.UUID
    result_type: ModelName
    result_date: datetime
    shared_at: datetime
    template_key: str
    template_text: str | None  # null = pending doctor approval (DEC-041)
    doctor_message: str | None
    doctor_name: str | None


# ---- task 4: genetic review, notes, dates and status (Dashboard §8.3, §12, §15, §17) ----

NoteText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class GeneticReviewIn(BaseModel):
    """Genetic §10.3 Confirm: the note is required."""

    model_config = ConfigDict(extra="forbid")

    doctor_note: NoteText


class GeneticCorrectIn(BaseModel):
    """Genetic §10.3 Correct inputs: the corrected answers and the doctor's note."""

    model_config = ConfigDict(extra="forbid")

    inputs: AssessmentIn
    doctor_note: NoteText


class DoctorAssessmentOut(BaseModel):
    """The doctor's view of one assessment: everything, including numbers and priority."""

    id: uuid.UUID
    patient_id: uuid.UUID
    patient_name: str
    created_at: datetime
    rules_version: str
    review_status: Literal["pending_review", "reviewed"]
    priority: Literal["normal", "high"]
    risk_indicated: bool
    result: Assessment
    inputs: dict[str, Any]
    doctor_note: str | None
    reviewed_at: datetime | None
    reviewed_by_name: str | None
    supersedes_id: uuid.UUID | None
    replaced: bool  # a correction replaced this one
    by_doctor: bool  # submitted by a doctor (a correction), not the patient


class NoteIn(BaseModel):
    """Dashboard §15: private (doctors only) or shared, chosen when writing."""

    model_config = ConfigDict(extra="forbid")

    body: NoteText
    visible_to_patient: bool


class NoteOut(BaseModel):
    id: uuid.UUID
    body: str
    visible_to_patient: bool
    doctor_name: str
    created_at: datetime
    related_ref: str | None


class DoctorEndIn(BaseModel):
    """Dashboard §17: the same three choices; the patient's inform-the-doctor question does
    not apply."""

    model_config = ConfigDict(extra="forbid")

    status: EndStatus


# §8.3: a doctor sets a clinician-confirmed (option B) or ultrasound (option C) date
DoctorDatesIn = Annotated[DueDateIn | UltrasoundDatesIn, Field(discriminator="option")]
