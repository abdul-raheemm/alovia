# ruff: noqa: E501  -- the A1-A4 assumptions are copied word for word from the spec
"""Doctor rule-review sheet for Genetic Risk (Genetic spec §13, D7).

Writes docs/modules/reviews/genetic_rule_review.csv from the live rule files: every rule row
(§7), every evidence rule (§6.2), every conflict and error (§6.3), every message (§11.4) and the
assumptions A1-A4 (§13.1). The reviewing doctor fills `checked` (yes / no), `comment`,
`reviewer`, `date`; `rules_version` is filled in. The module is not released until every row is
checked "yes" (§13). Re-run after any change:

  python scripts/export_genetic_rule_review.py
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.modules.genetic.rules import GeneticRules, Outcome, parse_genetic_rules  # noqa: E402

OUT = (
    Path(__file__).resolve().parents[2] / "docs" / "modules" / "reviews" / "genetic_rule_review.csv"
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
ASSUMPTIONS = {  # Genetic spec §13.1, word for word
    "A1": 'A "normal" sickle cell status card does not rule out β-thalassaemia carrier status, so it is treated as `unknown` for the haemoglobin group.',
    "A2": "HbE or HbD carrier × tested-negative partner: no affected child expected; 1 in 2 carrier.",
    "A3": "Haemophilia A and B follow the same rules in this module.",
    "A4": "β-thalassaemia major or sickle cell disease parent × tested-negative partner: all children are carriers, no affected child expected.",
}


def _outcomes(rules: GeneticRules, items: tuple[Outcome, ...] | None) -> str:
    return "; ".join(
        f"{rules.labels.outcomes[o.outcome]}: {rules.labels.chances[o.chance]}" for o in items or ()
    )


def rows(rules: GeneticRules) -> list[dict[str, str]]:
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

    for r in rules.haemoglobin.rules:
        pairs = ", ".join(f"{a}+{b}" for a, b in r.pairs)
        value = f"{pairs} -> {r.status}"
        if r.outcomes:
            value += f" | {_outcomes(rules, r.outcomes)}"
        add(
            "1 Haemoglobin rule",
            r.id,
            "Correct against its sources?" + (f" ({r.confirm})" if r.confirm else ""),
            value,
            ", ".join(r.sources) or "(no source in the spec)",
        )
    for hem in rules.haemophilia.rules:
        value = f"mother {hem.mother} + father {hem.father} -> {hem.status}"
        if hem.if_boy:
            value += (
                f" | boy: {_outcomes(rules, hem.if_boy)} | girl: {_outcomes(rules, hem.if_girl)}"
            )
        add(
            "2 Haemophilia rule",
            hem.id,
            "Correct against its sources? (A3)",
            value,
            ", ".join(hem.sources) or "(no source in the spec)",
        )
    for mar in rules.marfan.rules:
        value = f"{mar.pair[0]} + {mar.pair[1]} -> {mar.status}"
        if mar.outcomes:
            value += f" | {_outcomes(rules, mar.outcomes)}"
        add(
            "3 Marfan rule",
            mar.id,
            "Correct against its sources?",
            value,
            ", ".join(mar.sources) or "(no source in the spec)",
        )
    for h in rules.evidence.handling:
        scope = f" with {h.status}" if h.status else ""
        add(
            "4 Evidence rule",
            f"{h.evidence}{scope}",
            "Treat as unknown?" + (" (A1)" if h.status else ""),
            f"{h.evidence}{scope} -> {h.treat_as}, warning {h.warning}",
            "Genetic spec §6.2",
        )
    for c in rules.conflicts.conflicts:
        add("5 Conflict", c.id, "Correct?", f"{c.spec} -> {c.status}", "Genetic spec §6.3")
    for code, text in rules.conflicts.errors.items():
        add("5 Error", code, "Correct?", f"{text} -> error", "Genetic spec §6.3")
    for key, msg in rules.messages.items():
        add(
            "6 Message",
            key,
            f"Write or approve the text. Intent: {msg.intent}",
            msg.text or "(no approved text yet)",
            "Genetic spec §11.4",
        )
    for aid, text in ASSUMPTIONS.items():
        add("7 Assumption", aid, "Confirm or change.", text, "Genetic spec §13.1")
    return out


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data = rows(parse_genetic_rules())
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(data)
    print(f"wrote {len(data)} rows to {OUT}")


if __name__ == "__main__":
    main()
