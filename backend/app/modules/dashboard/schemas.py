"""Request and response shapes for the doctor home, patients and inbox (Dashboard spec §5-8,
API.md §4.6)."""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

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
