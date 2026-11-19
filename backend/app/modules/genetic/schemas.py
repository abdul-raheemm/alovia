"""Request and response shapes for the patient genetic routes (docs/API.md §4.4).

The shape is checked here; whether each answer is allowed (§6.1 E1/E2) is checked by the engine
against the rule files, so the vocabulary lives in one place."""

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from app.modules.genetic.engine import ConditionResult, Flags


class ParentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str | None = None
    evidence: str | None = None


class SectionIn(BaseModel):
    """One condition section (§4.1). `entry` is asked for haemophilia and Marfan only."""

    model_config = ConfigDict(extra="forbid")

    entry: str | None = None
    mother: ParentIn | None = None
    father: ParentIn | None = None
    previous_child: str | None = None


class AssessmentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    haemoglobin_group: SectionIn | None = None
    haemophilia: SectionIn | None = None
    marfan: SectionIn | None = None
    consanguinity: str | None = None


class AssessmentOut(BaseModel):
    """The patient's view of one assessment (§8.2, §10.4). Numbers are left out while
    `show_numbers_to_patient` is false; the doctor-only priority is not included."""

    assessment_id: uuid.UUID
    created_at: datetime
    rules_version: str
    review_status: Literal["pending_review", "reviewed"]
    show_numbers_to_patient: bool
    conditions: list[ConditionResult]
    flags: Flags
    message_keys: list[str]
    disclaimer_key: str
    doctor_note: str | None
    reviewed_at: datetime | None
    inputs: dict[str, Any]  # her own answers, as submitted
