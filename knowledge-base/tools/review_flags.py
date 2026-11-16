#!/usr/bin/env python3
"""Reading aid for setting contains_treatment_advice. It decides NOTHING.

Usage:
    py review_flags.py alovia-knowledge-base          (files still at FILL_ME)
    py review_flags.py alovia-knowledge-base --all    (every file in clean/)

For each file it prints the title, word count, the current flags, and the
sentences that contain words such as take, should, treatment, medicine,
supplement, surgery. Read the whole text yourself: a sentence without these
words can still tell the reader to do something, and a sentence with them can
be plain explanation.

Rule from the guide: contains_treatment_advice is true if the text tells the
reader to take a medicine, supplement or procedure as treatment.
It only reads files; it changes nothing.
"""
import re
import sys
from pathlib import Path

FRONT_RE = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n(.*))?\Z", re.DOTALL)
KEYWORD_RE = re.compile(
    r"\b(take|takes|taking|took|should|must|need|needs|treat|treated|treats|"
    r"treatment|treatments|medicine|medicines|medication|medications|drug|drugs|"
    r"supplement|supplements|vitamin|vitamins|surgery|surgeries|operation|"
    r"procedure|procedures|therapy|therapies|prescribe|prescribed|prescription|"
    r"vaccine|vaccines|vaccination|vaccinations|immunization|immunizations|shot|shots|"
    r"injection|injections|inject|antibiotic|antibiotics|pill|pills|aspirin|insulin|"
    r"inhaler|iron|calcium|"
    r"talk to|ask your|call your|see your|get tested)\b",
    re.IGNORECASE,
)
MAX_WIDTH = 240


def field(front, name):
    match = re.search(rf"(?m)^{name}:\s*(.*?)\s*$", front)
    return match.group(1).strip('"') if match else "(missing)"


def sentences(body):
    """Split into sentences, treating every line (paragraph, heading, list item)
    as its own unit so list items without a final full stop stay separate."""
    found = []
    for line in body.splitlines():
        if line.startswith("# "):  # the file's own title line, not text of the source
            continue
        line = re.sub(r"^[ ]*(## |- |\d+\. )", "", line).strip()
        line = re.sub(r"\s+", " ", line)
        if line:
            found.extend(s.strip() for s in re.split(r"(?<=[.!?])\s+", line) if s.strip())
    return found


def main(root, show_all):
    files = sorted((Path(root) / "clean").rglob("*.md"))
    shown = 0
    for path in files:
        text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
        match = FRONT_RE.match(text)
        if not match:
            print(f"=== {path.name}: no front matter, skipped")
            continue
        front, body = match.group(1), (match.group(2) or "").strip()
        flag = field(front, "contains_treatment_advice")
        if flag != "FILL_ME" and not show_all:
            continue
        shown += 1
        hits = [s for s in sentences(body) if KEYWORD_RE.search(s)]
        print(f"\n=== {field(front, 'doc_id')}  {field(front, 'title')}  "
              f"({len(body.split())} words)")
        print(f"    treatment_advice: {flag}   dosage: {field(front, 'contains_dosage')}"
              f"   topics: {field(front, 'topics')}")
        print(f"    sentences with keywords: {len(hits)}")
        for number, sentence in enumerate(hits, 1):
            clipped = sentence if len(sentence) <= MAX_WIDTH else sentence[:MAX_WIDTH] + " ..."
            print(f"      {number}. {clipped}")
    print(f"\n{shown} file(s) listed.")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--all"]
    if len(args) != 1:
        sys.exit("Usage: py review_flags.py alovia-knowledge-base [--all]")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    main(args[0], "--all" in sys.argv)
