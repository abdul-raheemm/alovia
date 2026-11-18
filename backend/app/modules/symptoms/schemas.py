"""Request and response shapes for the patient symptom routes (docs/API.md §4.3).

The shape of an entry is checked here; whether its values are allowed for its symptom (§6 V1/V2)
is checked by the engine against the rule files, so the vocabulary lives in one place."""

import uuid
from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt

Level = Literal["L0", "L1", "L2"]


class EntryIn(BaseModel):
    """One symptom entry (§5). Only the details its symptom asks for may be sent."""

    model_config = ConfigDict(extra="forbid")

    symptom: str
    severity: str | None = None
    duration: str | None = None
    body_area: str | None = None
    with_vision_problems: StrictBool | None = None
    with_swelling: StrictBool | None = None
    unable_to_keep_fluids: StrictBool | None = None
    puqe_answers: list[StrictInt] | None = None
    food: str | None = None  # food_craving
    name: str | None = None  # other
    appetite: str | None = None  # appetite_change
    occurred_at: time | None = None
    notes: str | None = None  # never read by the rules (§1.2)


class CheckinIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Literal["form", "urgent_button"]
    entries: list[EntryIn] = Field(max_length=25)  # §5 has 25 symptoms


class CheckinOut(BaseModel):
    """POST reply (API.md §5). Never includes pattern changes (doctor only, §9)."""

    checkin_id: uuid.UUID
    created_at: datetime
    pregnancy_week: int | None
    red_flag_level: Level
    matched_rules: list[str]
    message_keys: list[str]


class EntryOut(BaseModel):
    symptom: str
    severity: str | None
    duration: str | None
    body_area: str | None
    details: dict[str, object] | None
    occurred_at: time | None
    notes: str | None


class CheckinHistoryOut(CheckinOut):
    """Own history (patient view): the check-in and its entries, no pattern changes."""

    source: Literal["form", "urgent_button"]
    local_date: date
    entries: list[EntryOut]


class SymptomPoint(BaseModel):
    local_date: date
    pregnancy_week: int | None
    severity: str | None
    duration: str | None


class SymptomSeries(BaseModel):
    symptom: str
    label: str
    points: list[SymptomPoint]


class PuqePoint(BaseModel):
    local_date: date
    pregnancy_week: int | None
    score: int
    band: str


class ChartsOut(BaseModel):
    """§4.3 history charts: per symptom (how often, severity, duration) and PUQE over time."""

    symptoms: list[SymptomSeries]
    puqe: list[PuqePoint]
