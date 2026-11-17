"""Loads and checks rules/journey/config.yaml (Journey spec §14.4). Wrong settings stop the
backend at startup (ARCHITECTURE.md §12), so a bad month map can never reach a patient."""

from functools import lru_cache
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

CONFIG_FILE = Path(__file__).resolve().parents[3] / "rules" / "journey" / "config.yaml"
MESSAGES_FILE = CONFIG_FILE.with_name("messages.yaml")
MAX_WEEKS = 42  # §4.5: the week counter stops at 42


class MonthRange(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    month: int = Field(ge=1, le=9)
    weeks: tuple[int, int]


class NavItem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    key: str = Field(min_length=1)
    label: str = Field(min_length=1)


class JourneyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    content_source: Literal["prototype", "knowledge_base"]
    show_prototype_banner: bool
    assistant_enabled: bool
    suggested_checkups_enabled: bool
    timezone: str
    month_map: tuple[MonthRange, ...]
    term_from_week: int = Field(ge=0, le=MAX_WEEKS)
    appointment_notice_hours: int = Field(gt=0)
    resume_window_days: int = Field(gt=0)
    nav_items: tuple[NavItem, ...] = Field(min_length=1)

    @field_validator("timezone")
    @classmethod
    def known_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"unknown timezone {value!r}") from exc
        return value

    @field_validator("month_map")
    @classmethod
    def months_cover_every_week_once(cls, value: tuple[MonthRange, ...]) -> tuple[MonthRange, ...]:
        """Months 1-9 in order, each a non-empty week range, together covering weeks 0-42
        with no gap and no overlap."""
        if [m.month for m in value] != list(range(1, 10)):
            raise ValueError("month_map must list months 1 to 9 in order")
        expected_start = 0
        for m in value:
            start, end = m.weeks
            if start != expected_start or end < start:
                raise ValueError(f"month {m.month}: weeks must start at {expected_start}")
            expected_start = end + 1
        if expected_start != MAX_WEEKS + 1:
            raise ValueError(f"month_map must end at week {MAX_WEEKS}")
        return value

    @model_validator(mode="after")
    def nav_keys_unique(self) -> JourneyConfig:
        keys = [item.key for item in self.nav_items]
        if len(keys) != len(set(keys)):
            raise ValueError("nav_items keys must be unique")
        return self


def parse_journey_config(text: str) -> JourneyConfig:
    return JourneyConfig.model_validate(yaml.safe_load(text))


@lru_cache
def load_journey_config() -> JourneyConfig:
    return parse_journey_config(CONFIG_FILE.read_text(encoding="utf-8"))


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    intent: str = Field(min_length=1)  # from the spec, for reviewers; never shown to patients
    text: str | None  # None until a doctor approves the wording (DEC-041)


class _MessagesFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    messages: dict[str, Message] = Field(min_length=1)


def parse_journey_messages(text: str) -> dict[str, Message]:
    return _MessagesFile.model_validate(yaml.safe_load(text)).messages


@lru_cache
def load_journey_messages() -> dict[str, Message]:
    return parse_journey_messages(MESSAGES_FILE.read_text(encoding="utf-8"))
