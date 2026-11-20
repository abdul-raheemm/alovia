# ruff: noqa: E501  -- the assumptions are copied word for word from the spec
"""Rows of the doctor review for this module (Genetic spec §13): the same rows feed the CSV sheet
(scripts/) and the in-app rule review screen (Dashboard spec §19, DEC-082/100)."""

from app.modules.genetic.rules import GeneticRules, Outcome

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
