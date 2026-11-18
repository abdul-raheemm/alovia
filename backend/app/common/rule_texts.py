"""Patient-facing texts and phone numbers kept in each module's messages.yaml (Journey §13,
Symptom §11). Shared by the modules' rule loaders."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    intent: str = Field(min_length=1)  # from the spec, for reviewers; never shown to patients
    text: str | None  # None until a doctor approves the wording (DEC-041)


class Helpline(BaseModel):
    """A phone number copied from an official Government of India or Telangana page, with its
    URL and date (Journey §13.3, Symptom §11.3). Never typed from memory."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    key: str | None = None  # what the number is for, when a module needs to pick one
    label: str = Field(min_length=1)
    numbers: tuple[str, ...] = Field(min_length=1)
    source_title: str = Field(min_length=1)
    source_url: str = Field(pattern=r"^https://")
    date_accessed: date

    @field_validator("numbers")
    @classmethod
    def digits_only(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not all(n.isdigit() for n in value):
            raise ValueError("helpline numbers are digits only")
        return value
