"""Content provider (Journey spec §7.2, §8; §15 tests 5-7). Fixture items use obviously fake
test strings — never real medical content (CLAUDE.md rule 5)."""

from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from app.modules.journey.content import (
    CONTENT_DIR,
    ContentItem,
    ContentProvider,
    PrototypeContentProvider,
    SizeReference,
    provider_for,
    select_for_home,
)

SOURCE = """
      publisher: Test Publisher
      title: Test page
      url: https://example.test/page
      licence: CC0
      date_accessed: 2026-11-17
"""


def provider_with(tmp_path: Path, items: str = "items: []", sizes: str = "sizes: []") -> Any:
    (tmp_path / "prototype_content.yaml").write_text(items, encoding="utf-8")
    (tmp_path / "size_reference.yaml").write_text(sizes, encoding="utf-8")
    return PrototypeContentProvider(tmp_path)


FIXTURE_ITEMS = f"""
items:
  - id: week_20_dev
    granularity: week
    week_start: 20
    week_end: 20
    content_type: fetal_development
    title: Test week item
    body: Test body (week 20)
    source: {SOURCE}
    review_status: unreviewed
    is_prototype: true
  - id: range_18_22_body
    granularity: week_range
    week_start: 18
    week_end: 22
    content_type: body_changes
    title: Test range item
    body: Test body (weeks 18-22)
    source: {SOURCE}
    review_status: unreviewed
    is_prototype: true
  - id: month_5_dev
    granularity: month
    month: 5
    content_type: fetal_development
    title: Test month item (same type as the week item)
    body: Test body (month 5)
    source: {SOURCE}
    review_status: unreviewed
    is_prototype: true
  - id: month_5_nutrition
    granularity: month
    month: 5
    content_type: nutrition
    title: Test month item (own type)
    body: Test body (nutrition)
    source: {SOURCE}
    review_status: unreviewed
    is_prototype: true
"""

FIXTURE_SIZES = f"""
sizes:
  - week: 20
    weight_g: 300.0
    object_icon_id: test_icon
    object_name: test object
    source: {SOURCE}
    review_status: unreviewed
"""


def test_shipped_files_are_valid_and_empty_until_task_4() -> None:
    provider = PrototypeContentProvider(CONTENT_DIR)
    assert provider.items_for_week(20) == []
    assert provider.items_for_month(5) == []
    assert provider.size_for_week(20) is None


def test_selection_rule(tmp_path: Path) -> None:
    provider: ContentProvider = provider_with(tmp_path, FIXTURE_ITEMS, FIXTURE_SIZES)
    # week selection: every item whose range covers the content week (§8.1)
    assert {i.id for i in provider.items_for_week(20)} == {"week_20_dev", "range_18_22_body"}
    assert {i.id for i in provider.items_for_week(18)} == {"range_18_22_body"}
    assert provider.items_for_week(23) == []
    assert {i.id for i in provider.items_for_month(5)} == {"month_5_dev", "month_5_nutrition"}
    # type filter (§8.2)
    assert [i.id for i in provider.items_for_week(20, ["fetal_development"])] == ["week_20_dev"]
    # home: week item wins over the month item of the same content_type (§8.1)
    chosen = select_for_home(provider, 20, 5)
    assert {i.id for i in chosen} == {"week_20_dev", "range_18_22_body", "month_5_nutrition"}
    # at a week with no week item, the month item of that type appears
    assert {i.id for i in select_for_home(provider, 19, 5, ["fetal_development"])} == {
        "range_18_22_body"
    } - {"range_18_22_body"} | {"month_5_dev"}


def test_size_only_for_sourced_weeks(tmp_path: Path) -> None:
    provider = provider_with(tmp_path, FIXTURE_ITEMS, FIXTURE_SIZES)
    size = provider.size_for_week(20)
    assert size is not None and size.weight_g == 300.0 and size.object_name == "test object"
    assert provider.size_for_week(21) is None  # no sourced value -> no comparison (§15 test 7)


@pytest.mark.parametrize(
    ("broken", "match"),
    [
        ("granularity: week\n    week_start: 20\n    week_end: 21", "week_start == week_end"),
        ("granularity: week_range\n    week_start: 22\n    week_end: 18", "must not exceed"),
        ("granularity: month\n    month: 5\n    week_start: 20\n    week_end: 20", "no week"),
        ("granularity: week\n    week_start: 20", "week fields"),
    ],
)
def test_items_that_break_the_shape_are_refused(broken: str, match: str) -> None:
    item = f"""
    id: bad_item
    {broken}
    content_type: fetal_development
    title: Test
    body: Test
    source: {{publisher: P, title: T, url: U, licence: L, date_accessed: 2026-11-17}}
    review_status: unreviewed
    is_prototype: true
    """
    import yaml

    with pytest.raises(ValidationError, match=match):
        ContentItem.model_validate(yaml.safe_load(item))


def test_size_row_without_any_value_is_refused() -> None:
    with pytest.raises(ValidationError, match="length or a weight"):
        SizeReference.model_validate(
            {
                "week": 10,
                "object_icon_id": "x",
                "object_name": "x",
                "source": {
                    "publisher": "P",
                    "title": "T",
                    "url": "U",
                    "licence": "L",
                    "date_accessed": "2026-11-17",
                },
                "review_status": "unreviewed",
            }
        )


def test_duplicate_ids_are_refused(tmp_path: Path) -> None:
    two_same = FIXTURE_ITEMS.replace("id: range_18_22_body", "id: week_20_dev")
    with pytest.raises(ValueError, match="unique"):
        provider_with(tmp_path, two_same)


def test_two_size_rows_for_one_week_are_refused(tmp_path: Path) -> None:
    second_row = FIXTURE_SIZES.split("sizes:")[1].replace("test_icon", "other_icon")
    with pytest.raises(ValueError, match="one row per week"):
        provider_with(tmp_path, sizes=FIXTURE_SIZES + second_row)


def test_knowledge_base_source_is_refused_until_phase_7(tmp_path: Path) -> None:
    assert isinstance(provider_for("prototype", CONTENT_DIR), PrototypeContentProvider)
    with pytest.raises(ValueError, match="Phase 7"):
        provider_for("knowledge_base", tmp_path)
