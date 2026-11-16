#!/usr/bin/env python3
"""Set contains_treatment_advice in the front matter of one or more files.

Usage:
    py set_flag.py alovia-knowledge-base false MLP-CONDITIONS-001 MLP-CONDITIONS-002
    py set_flag.py alovia-knowledge-base true  MLP-NUTRITION-002

Only the line "contains_treatment_advice: FILL_ME" is changed, and only in the
file whose doc_id you name. The text of the document is never touched, and a
flag you already set is never overwritten. Run it only AFTER you have read the
text of each file.
"""
import re
import sys
from pathlib import Path

PLACEHOLDER = re.compile(r"(?m)^contains_treatment_advice: FILL_ME(?=\r?\n)")


def set_flag(root, value, doc_id):
    matches = list((Path(root) / "clean").rglob(f"{doc_id}.md"))
    if len(matches) != 1:
        return f"ERROR   {doc_id}: expected exactly one file, found {len(matches)}"
    path = matches[0]
    with open(path, encoding="utf-8", newline="") as handle:
        text = handle.read()
    if not PLACEHOLDER.search(text):
        return f"SKIPPED {doc_id}: contains_treatment_advice is not FILL_ME (left as it is)"
    new_text = PLACEHOLDER.sub(f"contains_treatment_advice: {value}", text, count=1)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(new_text)
    return f"SET     {doc_id}: contains_treatment_advice: {value}"


if __name__ == "__main__":
    if len(sys.argv) < 4 or sys.argv[2] not in ("true", "false"):
        sys.exit("Usage: py set_flag.py alovia-knowledge-base true|false DOC_ID [DOC_ID ...]")
    for doc in sys.argv[3:]:
        print(set_flag(sys.argv[1], sys.argv[2], doc))
