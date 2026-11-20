"""Doctor review sheet for the Pregnancy Journey (spec §16; R1-R4, messages, helplines).

Writes docs/review/journey_doctor_review.csv from the live rule and content files, so the
doctor reviews exactly what the app shows. Opens in Excel (UTF-8 with BOM). The doctor fills
`doctor_verdict` (OK / CHANGE) and `doctor_comment`; nothing is changed in the app until the
owner applies the verdicts. Re-run after any change:

  python scripts/export_review_sheet.py
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.modules.journey.review import COLUMNS, rows  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "docs" / "review" / "journey_doctor_review.csv"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data = rows()
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(data)
    print(f"wrote {len(data)} rows to {OUT}")


if __name__ == "__main__":
    main()
