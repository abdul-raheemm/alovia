"""Request and response shapes for /me (docs/API.md §4.1)."""

import uuid

from pydantic import BaseModel, ConfigDict, Field, StrictBool


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    role: str


class PatientRef(BaseModel):
    id: uuid.UUID
    name: str  # never patients.notes: those are doctor-private


class DoctorRef(BaseModel):
    id: uuid.UUID
    name: str
    specialty: str | None


class ConsentStatus(BaseModel):
    current_version: str
    accepted: bool


class MeOut(BaseModel):
    user: UserOut
    patient: PatientRef | None
    doctor: DoctorRef | None
    consent: ConsentStatus


class InviteCheckOut(BaseModel):
    valid: bool


class LinkIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=64)


class ConsentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    consent_version: str
    age_confirmed_18_plus: StrictBool
