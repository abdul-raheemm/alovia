"""Request and response shapes for the Journey routes (docs/API.md §4.2)."""

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool

from app.modules.journey.engine import DateSource, HomeState


class _DatesBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # §5.3: required to replace a clinician or scan date with an LMP estimate
    confirm_override: StrictBool = False


class LmpDatesIn(_DatesBase):
    """Option A: first day of the last period."""

    option: Literal["lmp"]
    lmp_date: date


class DueDateIn(_DatesBase):
    """Option B: due date given by her doctor."""

    option: Literal["due_date"]
    due_date: date


class UltrasoundDatesIn(_DatesBase):
    """Option C: gestational age from an ultrasound, and the scan date."""

    option: Literal["ultrasound"]
    scan_date: date
    ga_weeks: int
    ga_days: int = Field(ge=0, le=6)


DatesIn = Annotated[LmpDatesIn | DueDateIn | UltrasoundDatesIn, Field(discriminator="option")]


class DatesOut(BaseModel):
    due_date: date | None
    lmp_date: date | None
    due_date_source: DateSource | None


class PregnancyOut(BaseModel):
    """Derived from the due date on every request; never stored (DEC-002)."""

    completed_weeks: int
    days: int
    days_to_go: int | None
    content_week: int  # stops at 42 (§4.5)
    trimester: int
    month: int
    is_estimate: bool  # true when the due date comes from the last period (§4.3 header)


class NavItemOut(BaseModel):
    key: str
    label: str


class HomeOut(BaseModel):
    """GET /patient/journey/home. Task 5 adds the baby card, content and status cards."""

    state: HomeState
    dates: DatesOut
    pregnancy: PregnancyOut | None  # only while the pregnancy is active and has a due date
    nav_items: list[NavItemOut]
    show_prototype_banner: bool
    # message key -> approved text, or null while a doctor has not approved it (DEC-041)
    messages: dict[str, str | None]
    # message keys to show right after a change (e.g. msg_dates_updated_by_clinician)
    notices: list[str] = []
