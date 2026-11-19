"""Doctor rule-review sheet for Symptom Tracking (Symptom spec §16, D17).

Writes docs/modules/reviews/symptom_rule_review.csv from the live rule files: every red-flag
rule, the PUQE wording and bands, the pattern rules and their settings, every message, the
phone numbers and the assumptions A1-A4. The reviewing doctor fills `checked` (yes / no),
`comment`, `reviewer`, `date`; `rules_version` is filled in. Any rule change raises
rules_version and the changed rows are reviewed again (§16). Re-run after any change:

  python scripts/export_symptom_rule_review.py
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.modules.symptoms.rules import SymptomRules, parse_symptom_rules  # noqa: E402

OUT = (
    Path(__file__).resolve().parents[2] / "docs" / "modules" / "reviews" / "symptom_rule_review.csv"
)
COLUMNS = [
    "section",
    "item_id",
    "what_to_check",
    "current_value",
    "source",
    "checked",
    "comment",
    "reviewer",
    "date",
    "rules_version",
]
ASSUMPTIONS = {  # Symptom spec §16.1, word for word
    "A1": "Vision problems on their own (without headache) are L1.",
    "A2": "PUQE vomiting and retching answer wording matches the official sheet.",
    "A3": "Pattern defaults (7-day window, 5 of 7 days, 2 L2 check-ins) are sensible.",
    "A4": 'Labour pains at 37+ weeks under 12 hours are L2 ("contact your doctor"), not L1.',
}


def rows(rules: SymptomRules) -> list[dict[str, str]]:
    version = rules.settings.rules_version
    out: list[dict[str, str]] = []

    def add(section: str, item: str, check: str, value: str, source: str) -> None:
        out.append(
            dict.fromkeys(COLUMNS, "")
            | {
                "section": section,
                "item_id": item,
                "what_to_check": check,
                "current_value": value,
                "source": source,
                "rules_version": version,
            }
        )

    for r in rules.rules:
        add(
            "1 Red-flag rule",
            r.id,
            f"Rule correct at level {r.level} against its sources?",
            r.spec,
            ", ".join(r.sources) or "(no source in the spec)",
        )
    p = rules.puqe
    for q in p.questions:
        answers = "; ".join(f"{score}: {text}" for score, text in sorted(q.answers.items()))
        add(
            "2 PUQE question",
            q.id,
            "Wording matches the official sheet (A2)?",
            f"{q.text} | {answers}",
            f"{p.source.title} ({p.source.url})",
        )
    add(
        "2 PUQE bands",
        "puqe_bands",
        "Bands correct? The S5 sheet prints 4-6 for mild and no band for 3; the spec says 3-6.",
        "; ".join(f"{b.band} {b.min}-{b.max}" for b in p.bands),
        "Symptom spec §8 (S5, S6)",
    )
    for pattern in rules.patterns:
        values = ", ".join(f"{s} = {getattr(rules.settings, s)}" for s in pattern.settings)
        add(
            "3 Pattern rule (doctor only)",
            pattern.code,
            "Rule and its numbers sensible (A3)?",
            pattern.spec + (f" ({values})" if values else ""),
            "Symptom spec §9",
        )
    for name in ("movements_from_week", "never_felt_from_week", "preterm_before_week"):
        add(
            "4 Week setting",
            name,
            "Week number correct?",
            str(getattr(rules.settings, name)),
            "Symptom spec §13.2",
        )
    for key, msg in rules.messages.items():
        add(
            "5 Message",
            key,
            f"Write or approve the text. Intent: {msg.intent}",
            msg.text or "(no approved text yet)",
            "Symptom spec §11.2",
        )
    for h in rules.helplines:
        add(
            "6 Phone number",
            str(h.key),
            "Right number to show?",
            f"{h.label}: {', '.join(h.numbers)}",
            f"{h.source_title} ({h.source_url}), accessed {h.date_accessed}",
        )
    for aid, text in ASSUMPTIONS.items():
        add("7 Assumption", aid, "Confirm or change.", text, "Symptom spec §16.1")
    return out


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data = rows(parse_symptom_rules())
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(data)
    print(f"wrote {len(data)} rows to {OUT}")


if __name__ == "__main__":
    main()
