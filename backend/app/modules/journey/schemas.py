"""Request and response shapes for the Journey routes (docs/API.md §4.2)."""

import datetime as dt
import uuid
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StringConstraints, field_validator

from app.modules.journey.content import ContentItem, SizeReference
from app.modules.journey.engine import DateSource, HomeState, MilestoneKind


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


class MonthSummary(BaseModel):
    """One of the 9 month cards (§4.4); week ranges come from the config month map."""

    month: int
    week_start: int
    week_end: int


class AppointmentIn(BaseModel):
    """Create or edit an appointment (§9.3): date, optional time, title (max 100 characters),
    optional note (max 500). Date and time are the patient's local time (config timezone)."""

    model_config = ConfigDict(extra="forbid")

    date: dt.date
    time: dt.time | None = None
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    note: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] | None = None

    @field_validator("note")
    @classmethod
    def _empty_note_is_none(cls, value: str | None) -> str | None:
        return value or None


class AppointmentOut(BaseModel):
    """One appointment (§9.3), used by the home block, the list and the calendar.

    `date` and `time` are already in the patient's local time (config timezone), so the apps
    show them as they are; a date-only appointment has `time` null."""

    id: uuid.UUID
    appointment_at: datetime
    has_time: bool
    date: dt.date
    time: dt.time | None
    title: str
    note: str | None
    source: Literal["patient", "doctor"]  # "doctor" -> "Added by your doctor"
    can_edit: bool  # the patient edits and deletes only her own (§9.3)


class AppointmentsOut(BaseModel):
    """GET /patient/appointments: upcoming soonest first, past most recent first (UX P8)."""

    upcoming: list[AppointmentOut]
    past: list[AppointmentOut]


class MilestoneOut(BaseModel):
    """A §6.4 calendar marker, derived from the due date (never stored)."""

    date: dt.date
    kind: MilestoneKind
    value: int  # week, month or trimester number; 0 for the due date


class CalendarOut(BaseModel):
    """GET /patient/journey/calendar (§9.1-9.2) for the requested days.

    TODO(Phase 3): symptom-day dots and red-flag icons (Module 7). Suggested check-ups stay
    off while `suggested_checkups_enabled` is false (R3, [OPEN])."""

    start: dt.date | None  # §9.1 navigation: pregnancy start ... due date + 2 weeks
    end: dt.date | None  # both null without an active, dated pregnancy
    milestones: list[MilestoneOut]
    appointments: list[AppointmentOut]


EndStatus = Literal["ended_birth", "ended_loss", "ended_not_specified"]


class PregnancyEndIn(BaseModel):
    """§11.2: her choice and whether her doctor should be informed. The question has no
    default, so `inform_doctor` must be sent as a real true/false."""

    model_config = ConfigDict(extra="forbid")

    status: EndStatus
    inform_doctor: StrictBool


class EndedOut(BaseModel):
    """§11.4-11.6: which ended screens to show, and the undo window."""

    status: EndStatus
    ended_at: datetime
    undo_until: datetime | None  # null once `resume_window_days` have passed


class HomeOut(BaseModel):
    """GET /patient/journey/home (shape in docs/API.md §4.2).

    Still to come: quick-log state and weekly summary (Phase 3), result and genetic status
    cards (Phases 4-5), notification bar (task 7).
    """

    state: HomeState
    dates: DatesOut
    pregnancy: PregnancyOut | None  # only while the pregnancy is active and has a due date
    nav_items: list[NavItemOut]
    show_prototype_banner: bool
    # message key -> approved text, or null while a doctor has not approved it (DEC-041)
    messages: dict[str, str | None]
    # message keys to show right after a change (e.g. msg_dates_updated_by_clinician)
    notices: list[str] = []
    # §4.3 blocks (empty/null until there is data; content arrives with task 4)
    months: list[MonthSummary] = []  # empty when there is no active dated pregnancy (§4.5, §11.3)
    stage_items: list[ContentItem] = []  # "This stage": fetal_development + body_changes
    size: SizeReference | None = None  # no sourced value -> no size comparison (§7.2)
    next_appointment: AppointmentOut | None = None
    ended: EndedOut | None = None  # only when state is ended (§11)


class MonthDetailOut(BaseModel):
    """GET /patient/journey/months/{month} (§4.4 detail view)."""

    month: int
    week_start: int
    week_end: int
    is_current: bool
    items: list[ContentItem]  # all content types for this month; empty until task 4


NotificationType = Literal[
    "new_week",
    "new_month",
    "appointment_soon",
    "doctor_note",
    "result_available",
    "genetic_reviewed",
    "dates_updated",
]


class NotificationOut(BaseModel):
    """One unread notification for the bar (§4.2, §10.1). `target_ref`: the week or month
    number for new_week/new_month, the appointment or note id for the others."""

    id: uuid.UUID
    type: NotificationType
    target_ref: str | None
    created_at: datetime


class DoctorNoteOut(BaseModel):
    """A note her doctor shared (§10.3); read-only for the patient."""

    id: uuid.UUID
    body: str
    doctor_name: str
    created_on: dt.date  # in the patient's time zone (config)
    related_ref: str | None  # e.g. a genetic assessment id (Phase 4)
