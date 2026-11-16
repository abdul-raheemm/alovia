#!/usr/bin/env python3
"""Validate the Alovia knowledge base, build manifest.csv, print coverage.

Usage:
    python validate_kb.py path/to/alovia-knowledge-base

Requires: pip install pyyaml
Exit code is 1 if any error is found, so it can gate the final handoff.

Version 2 (patched). Changes from the original:
  - Malformed YAML is reported for that file instead of crashing the script.
  - A UTF-8 BOM is reported as its own error (instead of "no YAML front matter").
  - trimester must be quoted text; text fields must be non-empty text.
  - The first line must be a "# " heading that matches the title.
  - url must start with http:// or https://.
  - trimester must agree with the weeks (or the mismatch must be explained in notes).
  - attribution is required (every file is Tier A or B, and both need attribution).
  - Scheme and local-service files must have time_sensitive: true.
  - Duplicate doc_ids are caught even when the first file has other errors.
  - manifest.csv also carries attribution, part and notes.
  - Warnings (do not affect the exit code): contains_dosage is false but the
    text contains dosage-style words.

Version 2.1: a file under 100 words is accepted only if it has
"short_exception: true" AND a reason in notes; it is then listed as a warning.
"""
import codecs
import csv
import hashlib
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

REQUIRED = [
    "doc_id", "title", "source_org", "source_type", "licence_tier", "licence",
    "url", "date_accessed", "published_or_reviewed", "region", "country",
    "language", "doc_type", "audience", "topics", "trimester", "week_start",
    "week_end", "contains_treatment_advice", "contains_dosage",
    "time_sensitive", "priority", "raw_file",
]
OPTIONAL = ["attribution", "part", "notes"]
BOOL_FIELDS = ["contains_treatment_advice", "contains_dosage", "time_sensitive"]
STRING_FIELDS = [
    "doc_id", "title", "source_org", "licence", "url", "country", "raw_file",
]
ENUMS = {
    "source_type": {"government", "intergovernmental", "professional_body",
                    "nonprofit", "academic"},
    "licence_tier": {"A", "B"},
    "region": {"international", "india", "telangana", "hyderabad"},
    "language": {"en", "te", "hi", "ur"},
    "doc_type": {"patient_education", "guideline", "factsheet", "glossary",
                 "scheme_info", "faq", "myth_buster"},
    "audience": {"patient", "clinician", "both"},
    "trimester": {"1", "2", "3", "all", "postpartum"},
    "priority": {"P1", "P2", "P3"},
}
# Topic vocabulary and minimum number of files per primary topic.
MIN_PER_TOPIC = {
    "week-by-week": 80, "trimester-overview": 12, "fetal-development": 20,
    "nutrition": 40, "activity-lifestyle": 20, "common-symptoms": 40,
    "warning-signs": 25, "conditions": 100, "tests-scans": 40,
    "vitals-monitoring": 20, "antenatal-care": 25, "labour-birth": 40,
    "postpartum-newborn": 40, "mental-health": 15, "substances-medicines": 20,
    "india-schemes": 30, "local-telangana": 15, "myths": 15, "glossary": 3,
}
# Topics whose files describe schemes, helplines or local services.
TIME_SENSITIVE_TOPICS = {"india-schemes", "local-telangana"}
# Week ranges per trimester (gestational weeks from the last menstrual period).
TRIMESTER_WEEKS = {"1": (1, 13), "2": (14, 27), "3": (28, 42)}

MIN_WORDS = 100
REQUIRE_ATTRIBUTION = True

DOC_ID_RE = re.compile(r"^[A-Z0-9]+(-[A-Z0-9]+)*-\d{3,4}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REVIEWED_RE = re.compile(r"^(\d{4}(-\d{2}(-\d{2})?)?|unknown)$")
FRONT_RE = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n(.*))?\Z", re.DOTALL)
DOSAGE_RE = re.compile(
    r"\b(mg|mcg|µg|μg|iu|ml|milligrams?|micrograms?|tablets?|capsules?"
    r"|doses?|dosage|units)\b",
    re.IGNORECASE,
)


def load_doc(path):
    """Split a clean file into (metadata dict, body text, load problems).

    metadata is None when the file cannot be read as front matter plus text.
    """
    raw = path.read_bytes()
    problems = []
    if raw.startswith(codecs.BOM_UTF8):
        problems.append("file starts with a BOM; re-save it as UTF-8 without BOM")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None, None, ["file is not valid UTF-8; re-save it as UTF-8"]
    text = text.replace("\r\n", "\n")

    match = FRONT_RE.match(text)
    if not match:
        problems.append(
            "no YAML front matter (the file must start with a line containing only ---)"
        )
        return None, None, problems

    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        where = f" near line {mark.line + 2}" if mark else ""
        reason = getattr(exc, "problem", None) or "invalid syntax"
        problems.append(f"front matter is not valid YAML{where}: {reason}")
        return None, None, problems

    if not isinstance(meta, dict):
        problems.append("front matter must be 'key: value' lines")
        return None, None, problems
    return meta, (match.group(2) or "").strip(), problems


def check(meta, body, path, root):
    """Return (errors, warnings) for one file. No errors means the file is valid."""
    missing = [key for key in REQUIRED if key not in meta]
    if missing:
        return [f"missing fields: {', '.join(missing)}"], []

    errors, warnings = [], []

    for key in STRING_FIELDS:
        value = meta[key]
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{key} must be non-empty text")

    doc_id = str(meta["doc_id"])
    if not DOC_ID_RE.match(doc_id):
        errors.append(f"doc_id '{doc_id}' does not match SOURCE-TOPIC-NNN")
    if doc_id != path.stem:
        errors.append(f"doc_id '{doc_id}' does not match file name '{path.stem}'")

    if isinstance(meta["url"], str) and not re.match(r"^https?://\S+$", meta["url"]):
        errors.append("url must start with http:// or https://")

    for key, allowed in ENUMS.items():
        if str(meta[key]) not in allowed:
            errors.append(f"{key}='{meta[key]}' not in {sorted(allowed)}")
    if not isinstance(meta["trimester"], str):
        errors.append('trimester must be quoted text, e.g. trimester: "2"')

    for key in BOOL_FIELDS:
        if not isinstance(meta[key], bool):
            errors.append(f"{key} must be true or false")

    topics = meta["topics"]
    topic_set = set()
    if not isinstance(topics, list) or not topics:
        errors.append("topics must be a non-empty list")
    else:
        topic_set = {t for t in topics if isinstance(t, str)}
        unknown = [t for t in topics if not isinstance(t, str) or t not in MIN_PER_TOPIC]
        if unknown:
            errors.append(f"unknown topic slugs: {unknown}")
        parts = path.relative_to(root / "clean").parts
        if len(parts) != 3:
            errors.append("file must sit in clean/<region>/<primary-topic>/")
        elif parts[0] != str(meta["region"]) or parts[1] != topics[0]:
            errors.append(
                f"folder {parts[0]}/{parts[1]} does not match "
                f"region/primary topic {meta['region']}/{topics[0]}"
            )

    start, end = meta["week_start"], meta["week_end"]
    if (start is None) != (end is None):
        errors.append("week_start and week_end must both be set or both null")
    elif start is not None:
        valid = all(
            isinstance(w, int) and not isinstance(w, bool) and 1 <= w <= 42
            for w in (start, end)
        )
        if not valid or start > end:
            errors.append(f"invalid week range {start}-{end}")
        else:
            trimester = str(meta["trimester"])
            notes = str(meta.get("notes") or "").strip()
            if trimester in TRIMESTER_WEEKS and not notes:
                low, high = TRIMESTER_WEEKS[trimester]
                if start < low or end > high:
                    errors.append(
                        f"weeks {start}-{end} fall outside trimester {trimester} "
                        f"(weeks {low}-{high}); fix them or explain in notes"
                    )

    if not DATE_RE.match(str(meta["date_accessed"])):
        errors.append("date_accessed must be YYYY-MM-DD")
    if not REVIEWED_RE.match(str(meta["published_or_reviewed"])):
        errors.append("published_or_reviewed must be YYYY, YYYY-MM, YYYY-MM-DD or unknown")

    if REQUIRE_ATTRIBUTION and not str(meta.get("attribution") or "").strip():
        errors.append("attribution is required (every file is Tier A or B)")

    if (topic_set & TIME_SENSITIVE_TOPICS or meta["doc_type"] == "scheme_info") \
            and meta["time_sensitive"] is not True:
        errors.append("scheme/local-service files must have time_sensitive: true")

    if not (root / str(meta["raw_file"])).is_file():
        errors.append(f"raw_file not found: {meta['raw_file']}")

    first_line = next((ln.strip() for ln in body.splitlines() if ln.strip()), "")
    expected = "# " + " ".join(str(meta["title"]).split())
    if " ".join(first_line.split()) != expected:
        errors.append(f"first line must be the level-1 heading '{expected}'")

    words = len(body.split())
    is_glossary = isinstance(topics, list) and topics[:1] == ["glossary"]
    if words < MIN_WORDS and not is_glossary:
        has_reason = bool(str(meta.get("notes") or "").strip())
        if meta.get("short_exception") is True and has_reason:
            warnings.append(
                f"only {words} words; accepted because short_exception is true "
                "(reason is in notes)"
            )
        else:
            errors.append(
                f"only {words} words (minimum {MIN_WORDS}); if the source page is "
                "genuinely this short, set short_exception: true and explain in notes"
            )

    if meta["contains_dosage"] is False:
        found = DOSAGE_RE.search(body)
        if found:
            warnings.append(
                f"contains_dosage is false but the text contains '{found.group(0)}'; "
                "read the text and set the flag honestly"
            )
    return errors, warnings


def write_manifest(rows, root):
    columns = REQUIRED + OPTIONAL + ["word_count", "path"]
    with open(root / "manifest.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def print_coverage(rows):
    primary = Counter(row["topics"].split(";")[0] for row in rows)
    print(f"\n{'topic':<24}{'min':>5}{'have':>7}  status")
    for topic, minimum in MIN_PER_TOPIC.items():
        have = primary[topic]
        status = "OK" if have >= minimum else "SHORT"
        print(f"{topic:<24}{minimum:>5}{have:>7}  {status}")

    total = len(rows)
    print(f"\nTotal files : {total} (minimum 600)")
    print(f"Total words : {sum(int(r['word_count']) for r in rows):,}")
    print(f"Regions     : {dict(Counter(r['region'] for r in rows))}")
    print(f"Audience    : {dict(Counter(r['audience'] for r in rows))}")
    print(f"Priority    : {dict(Counter(r['priority'] for r in rows))}")
    if total:
        patient_share = sum(r["audience"] in ("patient", "both") for r in rows) / total
        international = sum(r["region"] == "international" for r in rows) / total
        india = sum(r["region"] == "india" for r in rows) / total
        print(f"Patient/both: {patient_share:.0%} (aim for at least 70%)")
        print(f"International share: {international:.0%} (aim for at least 40%)")
        print(f"India share  : {india:.0%} (aim for at least 35%)")


def main(root):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    root = Path(root)
    files = sorted((root / "clean").rglob("*.md"))
    if not files:
        print("No files found under clean/")
        return 1

    rows, problems, warned = [], [], []
    seen_ids, seen_hashes = {}, {}
    for path in files:
        meta, body, load_errors = load_doc(path)
        if meta is None:
            problems.append((path, load_errors))
            continue

        errors, warnings = check(meta, body, path, root)
        errors = load_errors + errors

        doc_id = str(meta.get("doc_id"))
        if doc_id in seen_ids:
            errors.append(f"duplicate doc_id (also in {seen_ids[doc_id]})")
        else:
            seen_ids[doc_id] = path.name

        digest = hashlib.sha256(" ".join(body.lower().split()).encode()).hexdigest()
        if digest in seen_hashes:
            errors.append(f"identical text to {seen_hashes[digest]}")
        else:
            seen_hashes[digest] = path.name

        if warnings:
            warned.append((path, warnings))
        if errors:
            problems.append((path, errors))
            continue

        row = {key: meta[key] for key in REQUIRED}
        row["topics"] = ";".join(meta["topics"])
        for key in OPTIONAL:
            row[key] = meta.get(key)
        row["word_count"] = len(body.split())
        row["path"] = str(path.relative_to(root))
        rows.append(row)

    write_manifest(rows, root)
    print(f"Checked {len(files)} files: {len(rows)} valid, {len(problems)} with errors")
    for path, errors in problems:
        print(f"\nERROR {path.relative_to(root)}")
        for message in errors:
            print(f"   - {message}")
    if warned:
        print(f"\n{len(warned)} file(s) with warnings (these do not fail the run):")
        for path, messages in warned:
            print(f"\nWARNING {path.relative_to(root)}")
            for message in messages:
                print(f"   - {message}")
    print_coverage(rows)
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python validate_kb.py path/to/alovia-knowledge-base")
    sys.exit(main(sys.argv[1]))