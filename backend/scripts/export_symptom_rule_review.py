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

from app.modules.symptoms.review import COLUMNS, rows  # noqa: E402
from app.modules.symptoms.rules import parse_symptom_rules  # noqa: E402

OUT = (
    Path(__file__).resolve().parents[2] / "docs" / "modules" / "reviews" / "symptom_rule_review.csv"
)


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
