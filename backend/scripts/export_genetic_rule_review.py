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

from app.modules.genetic.review import COLUMNS, rows  # noqa: E402
from app.modules.genetic.rules import parse_genetic_rules  # noqa: E402

OUT = (
    Path(__file__).resolve().parents[2] / "docs" / "modules" / "reviews" / "genetic_rule_review.csv"
)


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
