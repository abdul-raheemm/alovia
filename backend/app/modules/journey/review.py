"""Rows of the doctor review for this module (Journey spec §16): the same rows feed the CSV sheet
(scripts/) and the in-app rule review screen (Dashboard spec §19, DEC-082/100)."""

from app.modules.journey.config import (
    load_helplines,
    load_journey_config,
    load_journey_messages,
)
from app.modules.journey.content import CONTENT_DIR, PrototypeContentProvider

COLUMNS = [
    "section",
    "id",
    "applies_to",
    "what_to_check",
    "current_value",
    "source",
    "doctor_verdict",
    "doctor_comment",
]


def rows() -> list[dict[str, str]]:
    out: list[dict[str, str]] = []

    def add(section: str, id_: str, applies: str, check: str, value: str, source: str) -> None:
        out.append(
            {
                "section": section,
                "id": id_,
                "applies_to": applies,
                "what_to_check": check,
                "current_value": value,
                "source": source,
                "doctor_verdict": "",
                "doctor_comment": "",
            }
        )

    # 1. Message texts (DEC-041): the doctor writes or approves each one
    for key, msg in load_journey_messages().items():
        add(
            "1 Message text",
            key,
            "patient screens",
            f"Write or approve the text. Intent from the spec: {msg.intent}",
            msg.text or "(no approved text yet - the app shows [Text pending doctor approval])",
            "Journey spec §13.2",
        )

    # 2. Content items (R2 / §16): correct, suitable, fair excerpt
    provider = PrototypeContentProvider(CONTENT_DIR)
    every = [i for m in range(1, 10) for i in provider.items_for_month(m)]
    every += [i for w in range(0, 43) for i in provider.items_for_week(w)]
    for item in {i.id: i for i in every}.values():  # each item once, in file order of first use
        where = (
            f"month {item.month}"
            if item.granularity == "month"
            else f"weeks {item.week_start}-{item.week_end}"
        )
        add(
            "2 Content item",
            item.id,
            where,
            f"{item.content_type}: correct, suitable for India, fair to its source?",
            f"{item.title} — {item.body}",
            f"{item.source.publisher}: {item.source.title} ({item.source.url}), "
            f"{item.source.licence}, accessed {item.source.date_accessed}",
        )

    # 3. Size comparison objects (R2): values are WHO; the object is the agent's draft
    for week in range(0, 43):
        size = provider.size_for_week(week)
        if size is None:
            continue
        add(
            "3 Size object",
            f"week_{week}",
            f"week {week}",
            "Is the comparison object a fair, familiar picture of this typical weight?",
            f"{size.object_name} (typical {size.weight_g:g} g)",
            f"{size.source.publisher}, {size.source.title}",
        )

    cfg = load_journey_config()
    # 4. Week-to-month mapping (R1)
    for m in cfg.month_map:
        add(
            "4 Month mapping (R1)",
            f"month_{m.month}",
            f"month {m.month}",
            "Confirm the weeks for this month (no single official mapping exists).",
            f"weeks {m.weeks[0]}-{m.weeks[1]}",
            "Journey spec §6.3 (rules/journey/config.yaml)",
        )

    # 5. Suggested check-ups (R3)
    plan = cfg.suggested_checkups
    if plan is not None:
        add(
            "5 Suggested check-ups (R3)",
            "pmsma",
            f"from week {plan.from_week}",
            "Confirm this official schedule is right to show as a dashed 'suggested' marker.",
            f"{plan.label}: day {plan.day_of_month} of every month from week {plan.from_week}",
            f'{plan.source.publisher}, "{plan.source.title}" ({plan.source.url}), '
            f'accessed {plan.source.date_accessed}: "{plan.source.quote}"',
        )

    # 6. Safety message after pregnancy end (R4) and helplines (§13.3)
    add(
        "6 After-pregnancy safety (R4)",
        "msg_after_pregnancy_danger_signs",
        "ended home",
        "Confirm the danger signs and wording (also row in section 1).",
        load_journey_messages()["msg_after_pregnancy_danger_signs"].text or "(no text yet)",
        "MCP card danger signs after delivery (spec S4)",
    )
    for h in load_helplines():
        add(
            "6 Helpline (§13.3)",
            h.label,
            "support screen after a loss or 'prefer not to say'",
            "Is this the right number to show on the support screen?",
            f"{h.label}: {', '.join(h.numbers)}",
            f"{h.source_title} ({h.source_url}), accessed {h.date_accessed}",
        )
    return out
