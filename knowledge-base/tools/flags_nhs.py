#!/usr/bin/env python3
"""Flag helper for the NHS files.

    py flags_nhs.py                           report only (changes nothing)
    py flags_nhs.py apply                     contains_treatment_advice: true where medicine/
                                              procedure words appear (only replaces FILL_ME)
    py flags_nhs.py dosage-false ID [ID ...]  contains_dosage: false, only when 'units' is the
                                              only dosage word in the file
"""
import re
import sys
from pathlib import Path

CLEAN = Path("clean")  # run from knowledge-base/ (was "alovia-knowledge-base/clean" in the old rag/ layout)
FRONT_RE = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n(.*))?\Z", re.DOTALL)
PLACEHOLDER = re.compile(r"(?m)^contains_treatment_advice: FILL_ME(?=\r?\n)")
DOSAGE_TRUE = re.compile(r"(?m)^contains_dosage: true(?=\r?\n)")
DOSAGE_RE = re.compile(
    r"\b(mg|mcg|µg|μg|iu|ml|milligrams?|micrograms?|tablets?|capsules?"
    r"|doses?|dosage|units)\b", re.IGNORECASE)
STRONG_RE = re.compile(
    r"\b(medicines?|medications?|drugs?|tablets?|capsules?|doses?|dosage|injections?|"
    r"inject\w*|vaccines?|vaccinations?|vaccinated|immunisations?|immunised|antibiotics?|"
    r"supplements?|vitamins?|surgery|surgical|operations?|procedures?|treatments?|"
    r"treated|treat|therapy|therapies|creams?|ointments?|paracetamol|ibuprofen|aspirin|"
    r"insulin|steroids?|painkillers?|pain relief|antacids?|laxatives?|anti-\w+|epidurals?|"
    r"induc\w*|prescribed|prescription|iron|folic acid|stitches|sutures?|transfusions?)\b",
    re.IGNORECASE)
WEAK_RE = re.compile(
    r"\b(take|takes|taking|should|must|need|needs|call|see your|talk to|ask your)\b",
    re.IGNORECASE)


def load():
    items = []
    for path in sorted(CLEAN.rglob("NHS-*.md")):
        text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        match = FRONT_RE.match(text)
        if match:
            items.append((path, match.group(1), match.group(2) or ""))
    return items


def sentences(body):
    found = []
    for line in body.splitlines():
        if line.startswith("# "):
            continue
        line = re.sub(r"^(#+ |- |\d+\. )", "", line).strip()
        found.extend(s.strip() for s in re.split(r"(?<=[.!?])\s+", line) if s.strip())
    return found


def rewrite(path, pattern, replacement):
    with open(path, encoding="utf-8", newline="") as handle:
        text = handle.read()
    new = pattern.sub(replacement, text, count=1)
    if new == text:
        return False
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(new)
    return True


def report():
    todo = [i for i in load() if "contains_treatment_advice: FILL_ME" in i[1]]
    strong = [i for i in todo if STRONG_RE.search(i[2])]
    weak = [i for i in todo if not STRONG_RE.search(i[2])]
    print(f"Files with FILL_ME: {len(todo)}  (medicine/procedure words: {len(strong)}, "
          f"none: {len(weak)})")

    print("\n##### WEAK: no medicine/procedure words. Read these and decide true/false #####")
    for path, front, body in weak:
        print(f"\n=== {path.stem} ({len(body.split())} words)")
        for s in [s for s in sentences(body) if WEAK_RE.search(s)][:4]:
            print("   -", s[:200])

    print("\n##### UNITS-ONLY dosage hits: what are the units? #####")
    for path, front, body in load():
        if "contains_dosage: true" in front and {m.lower() for m in DOSAGE_RE.findall(body)} == {"units"}:
            print(f"\n=== {path.stem}")
            for s in [s for s in sentences(body) if re.search(r"\bunits\b", s, re.I)][:2]:
                print("   -", s[:200])

    print("\n##### STRONG: will become true with 'apply' #####")
    print(", ".join(f"{p.stem.replace('NHS-', '')}({len(STRONG_RE.findall(b))})"
                    for p, f, b in strong))


def apply():
    done = 0
    for path, front, body in load():
        if "contains_treatment_advice: FILL_ME" in front and STRONG_RE.search(body):
            done += rewrite(path, PLACEHOLDER, "contains_treatment_advice: true")
    print(f"Set contains_treatment_advice: true on {done} files.")


def dosage_false(doc_ids):
    by_id = {p.stem: (p, f, b) for p, f, b in load()}
    for doc_id in doc_ids:
        if doc_id not in by_id:
            print(f"  ERROR   {doc_id}: not found")
            continue
        path, front, body = by_id[doc_id]
        found = {m.lower() for m in DOSAGE_RE.findall(body)}
        if found != {"units"}:
            print(f"  REFUSED {doc_id}: dosage words present: {sorted(found)}")
        elif rewrite(path, DOSAGE_TRUE, "contains_dosage: false"):
            print(f"  SET     {doc_id}: contains_dosage: false")
        else:
            print(f"  SKIPPED {doc_id}: contains_dosage is not 'true'")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    args = sys.argv[1:]
    if not args:
        report()
    elif args[0] == "apply" and len(args) == 1:
        apply()
    elif args[0] == "dosage-false" and len(args) > 1:
        dosage_false(args[1:])
    else:
        sys.exit("Usage: py flags_nhs.py | apply | dosage-false ID [ID ...]")