"""Journey content provider (spec §8). Content comes only from files (now) or the knowledge
base (Phase 7); nothing is ever generated here (CLAUDE.md rule 5). The API and the frontend
never know which provider is active — switching is a config change (D8).
"""

from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Literal, Protocol

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

CONTENT_DIR = Path(__file__).resolve().parents[3] / "content"


class ContentSource(BaseModel):
    """Every item and size carries its source (§8.1); cards show it (D15, §13.1)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    publisher: str = Field(min_length=1)
    title: str = Field(min_length=1)
    url: str = Field(min_length=1)
    licence: str = Field(min_length=1)
    date_accessed: date
    kb_doc_id: str | None = None


class ContentItem(BaseModel):
    """One piece of stage content, exactly the §8.1 shape (same for every provider)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    granularity: Literal["month", "week", "week_range"]
    month: int | None = Field(None, ge=1, le=9)
    week_start: int | None = Field(None, ge=0, le=42)
    week_end: int | None = Field(None, ge=0, le=42)
    # §8.1: the final content_type list is [OPEN] and may grow without code change
    content_type: str = Field(min_length=1)
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)
    source: ContentSource
    review_status: Literal["unreviewed", "doctor_reviewed"]
    is_prototype: bool

    @model_validator(mode="after")
    def fields_match_granularity(self) -> ContentItem:
        if self.granularity == "month":
            if self.month is None or self.week_start is not None or self.week_end is not None:
                raise ValueError(f"item {self.id}: a month item has month and no week fields")
        else:
            if self.week_start is None or self.week_end is None or self.month is not None:
                raise ValueError(f"item {self.id}: a week item has week fields and no month")
            if self.granularity == "week" and self.week_start != self.week_end:
                raise ValueError(f"item {self.id}: a week item has week_start == week_end")
            if self.week_start > self.week_end:
                raise ValueError(f"item {self.id}: week_start must not exceed week_end")
        return self

    def covers_week(self, content_week: int) -> bool:
        if self.week_start is None or self.week_end is None:
            return False
        return self.week_start <= content_week <= self.week_end


class SizeReference(BaseModel):
    """A typical size for one week, with its source and comparison object (§7.2)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    week: int = Field(ge=0, le=42)
    length_cm: float | None = Field(None, gt=0)
    weight_g: float | None = Field(None, gt=0)
    object_icon_id: str = Field(min_length=1)
    object_name: str = Field(min_length=1)
    source: ContentSource
    review_status: Literal["unreviewed", "doctor_reviewed"]

    @model_validator(mode="after")
    def has_a_sourced_value(self) -> SizeReference:
        # §7.2: weeks without a sourced value get no row, never a guess
        if self.length_cm is None and self.weight_g is None:
            raise ValueError(f"week {self.week}: a size row needs a length or a weight")
        return self


class ContentProvider(Protocol):
    """§8.2 interface. items_for_week returns week/week_range items covering the week;
    items_for_month returns month items."""

    def items_for_week(
        self, content_week: int, types: list[str] | None = None
    ) -> list[ContentItem]: ...

    def items_for_month(self, month: int, types: list[str] | None = None) -> list[ContentItem]: ...

    def size_for_week(self, content_week: int) -> SizeReference | None: ...


class _ItemsFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ContentItem]


class _SizesFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sizes: list[SizeReference]


class PrototypeContentProvider:
    """Reads content/prototype_content.yaml and content/size_reference.yaml (§8.2).
    A broken file stops the backend at startup (ARCHITECTURE §12)."""

    def __init__(self, content_dir: Path = CONTENT_DIR) -> None:
        raw_items = yaml.safe_load((content_dir / "prototype_content.yaml").read_text("utf-8"))
        self._items = _ItemsFile.model_validate(raw_items).items
        ids = [item.id for item in self._items]
        if len(ids) != len(set(ids)):
            raise ValueError("prototype_content.yaml: item ids must be unique")
        raw_sizes = yaml.safe_load((content_dir / "size_reference.yaml").read_text("utf-8"))
        sizes = _SizesFile.model_validate(raw_sizes).sizes
        self._sizes = {size.week: size for size in sizes}
        if len(self._sizes) != len(sizes):
            raise ValueError("size_reference.yaml: one row per week")

    def items_for_week(
        self, content_week: int, types: list[str] | None = None
    ) -> list[ContentItem]:
        return [
            item
            for item in self._items
            if item.covers_week(content_week) and (types is None or item.content_type in types)
        ]

    def items_for_month(self, month: int, types: list[str] | None = None) -> list[ContentItem]:
        return [
            item
            for item in self._items
            if item.month == month and (types is None or item.content_type in types)
        ]

    def size_for_week(self, content_week: int) -> SizeReference | None:
        return self._sizes.get(content_week)


def select_for_home(
    provider: ContentProvider, content_week: int, month: int, types: list[str] | None = None
) -> list[ContentItem]:
    """§8.1 selection rule: week items for the content week plus month items for the current
    month; when both exist for one content_type, the home screen shows the week item (the
    month item stays in the month detail view)."""
    week_items = provider.items_for_week(content_week, types)
    covered = {item.content_type for item in week_items}
    month_items = [
        item for item in provider.items_for_month(month, types) if item.content_type not in covered
    ]
    return week_items + month_items


def provider_for(source: str, content_dir: Path = CONTENT_DIR) -> ContentProvider:
    if source == "prototype":
        return PrototypeContentProvider(content_dir)
    # KnowledgeBaseContentProvider reads journey_content/size_reference tables, which are
    # created in Phase 7 (DATABASE.md §3.3). Failing at startup is honest until then.
    raise ValueError("content_source 'knowledge_base' is not available until Phase 7 (spec §8.2)")


@lru_cache
def load_content_provider() -> ContentProvider:
    from app.modules.journey.config import load_journey_config

    return provider_for(load_journey_config().content_source)
