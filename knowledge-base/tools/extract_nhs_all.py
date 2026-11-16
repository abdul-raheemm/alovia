#!/usr/bin/env python3
"""Extract all kept NHS pages (nhs_pages.csv + raw/nhs/*.html) into clean/ files.

    py extract_nhs_all.py
Existing files whose flag is still FILL_ME are regenerated; files with a set flag are
never touched. A page whose cleaned text does not match the article text is not written.
"""
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup, Comment

ROOT = Path(".")  # run from knowledge-base/ (was "alovia-knowledge-base" in the old rag/ layout)
CATALOG = Path("nhs_pages.csv")


def ids(prefix, *numbers):
    return [f"NHS-{prefix}-{n:03d}" for n in numbers]


GROUPS = {
    "labour-birth": ids("LABOUR", 1, 3, 4, 6, 7, 8, 9, 13, 15) + ids("TESTS", 5, 15, 22, 24),
    "postpartum-newborn": (
        ids("LABOUR", 2, 5, 12, 14, 16) + ids("LGBT", 1) + ids("COND", 49, 55)
        + ids("BABY", 1, 2, 4, 5, 7, 8, 9, 10, 12, 13, 14, 16, 17, 18, 19, 20, 21, 22, 23)
    ),
    "common-symptoms": ids("SYMPTOMS", 1, 2, 4, 5, 6, 8, 9, 10, 11, 12, 14, 15) + ids("TRYING", 2),
    "warning-signs": ids("SYMPTOMS", 7, 13),
    "conditions": (
        ids("COMPLICATIONS", 1, 2) + ids("LABOUR", 10, 11) + ids("EXISTING", 1, 2, 3, 4, 5, 6)
        + ids("CARE", 4, 6, 11) + ids("WELL", 6, 8, 9)
        + ids("COND", 12, 13, 22, 23, 28, 29, 30, 31, 32, 35, 36, 37, 46, 47, 48, 50, 56, 57,
              59, 63, 65, 70, 71, 74, 76, 78, 81, 82, 84, 86, 89, 90,
              97, 98, 99, 100, 102, 104, 105, 106, 107, 109, 110)
        + ids("TESTS", 17, 18)
    ),
    "tests-scans": (
        ids("TRYING", 1) + ids("CARE", 1, 2, 5, 7, 8, 9, 10, 12)
        + ids("TESTS", 2, 9, 10, 23, 26, 28)
    ),
    "antenatal-care": (
        ids("TRYING", 3) + ids("FINDING", 2) + ids("LGBT", 3) + ids("CARE", 3, 13)
        + ids("WELL", 13, 15) + ids("COND", 60) + ids("VACC", 3, 4, 5, 6)
    ),
    "nutrition": ids("WELL", 3, 4, 10, 14) + ids("COND", 88),
    "substances-medicines": ids("WELL", 1, 5, 7, 11) + ids("LGBT", 2),
    "activity-lifestyle": ids("WELL", 2, 12),
    "fetal-development": ids("WELL", 16),
    "mental-health": ids("MENTAL", 1, 2, 3),
}
SECOND = {
    "NHS-LABOUR-001": "warning-signs",
    "NHS-SYMPTOMS-007": "common-symptoms", "NHS-SYMPTOMS-013": "common-symptoms",
    "NHS-COMPLICATIONS-001": "common-symptoms", "NHS-COMPLICATIONS-002": "common-symptoms",
    "NHS-EXISTING-006": "vitals-monitoring", "NHS-COND-036": "vitals-monitoring",
    "NHS-COND-065": "warning-signs", "NHS-WELL-016": "warning-signs",
}
TIME_SENSITIVE = set(ids("WELL", 9, 13, 15) + ids("VACC", 3, 4, 5, 6))
UK_SERVICES = set(ids("LABOUR", 15) + ids("BABY", 20, 22) + ids("CARE", 13))

TOPICS = {}
for primary, members in GROUPS.items():
    for doc_id in members:
        assert doc_id not in TOPICS, f"{doc_id} is in two groups"
        TOPICS[doc_id] = [primary] + ([SECOND[doc_id]] if doc_id in SECOND else [])

DOSAGE_RE = re.compile(
    r"\b(mg|mcg|µg|μg|iu|ml|milligrams?|micrograms?|tablets?|capsules?"
    r"|doses?|dosage|units)\b", re.IGNORECASE)
REMOVE_TAGS = ["script", "style", "video", "nav", "aside", "noscript", "iframe"]
DROP_SECTIONS = ("Sign up for", "Get Best Start in Life", "Start for Life",
                 "Get Start for Life")
LINK_SECTIONS = ("Find out more", "Further information", "More information")
INLINE = {"a", "span", "strong", "em", "b", "i", "abbr", "sup", "sub", "small", "cite",
          "mark", "u", "time", "q", "code", "label", "bdi", "button"}
LEAFBLOCK = {"summary", "dt", "dd", "figcaption", "caption", "legend"}


def clean(text):
    return " ".join(text.split())


def is_list(marker):
    return marker == "- " or bool(re.match(r"\d+\. $", marker))


def convert(node, lines):
    run = []

    def flush():
        text = clean("".join(run))
        run.clear()
        if text:
            lines.append(("", text, text))

    for child in node.children:
        name = getattr(child, "name", None)
        if name is None:
            if not isinstance(child, Comment):
                run.append(str(child))
            continue
        if name in INLINE:
            run.append(child.get_text(""))
            continue
        flush()
        if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            text = clean(child.get_text(" "))
            text = re.sub(r":(?=[A-Za-z])", ": ", text)
            if text:
                lines.append(("#" * int(name[1]) + " ", text, text))
        elif name == "p":
            text = clean(child.get_text(""))
            if text:
                lines.append(("", text, text))
        elif name in ("ul", "ol"):
            for number, item in enumerate(child.find_all("li", recursive=False), 1):
                text = clean(item.get_text(""))
                if text:
                    marker = "- " if name == "ul" else f"{number}. "
                    lines.append((marker, text, text))
        elif name == "table":
            caption = child.find("caption")
            if caption and clean(caption.get_text("")):
                text = clean(caption.get_text(""))
                lines.append(("", text, text))
            for index, row in enumerate(child.find_all("tr")):
                cells = [clean(c.get_text("")) for c in row.find_all(["th", "td"])]
                if not cells:
                    continue
                lines.append(("|", "| " + " | ".join(cells) + " |", "".join(cells)))
                if index == 0:
                    lines.append(("|", "| " + " | ".join("---" for _ in cells) + " |", ""))
        elif name in LEAFBLOCK:
            text = clean(child.get_text(""))
            if text:
                lines.append(("", text, text))
        else:
            convert(child, lines)
    flush()


def render(lines):
    out, previous = "", None
    for marker, text, _ in lines:
        if previous is not None:
            tight = (is_list(marker) and is_list(previous)) or (marker == "|" and previous == "|")
            out += "\n" if tight else "\n\n"
        out += text if marker == "|" else marker + text
        previous = marker
    return out


def first_diff(expected, got):
    limit = min(len(expected), len(got))
    i = next((k for k in range(limit) if expected[k] != got[k]), limit)
    return (f"first difference at char {i} of {len(expected)} (spaces removed): "
            f"page has '{expected[max(0, i - 30):i + 70]}' | file has "
            f"'{got[max(0, i - 30):i + 70]}'")


def q(value):
    return json.dumps(value, ensure_ascii=False)


def make_notes(row, doc_id):
    notes = []
    if row["review_overdue"] == "yes" and row["next_review_due"]:
        due = datetime.strptime(row["next_review_due"], "%Y-%m-%d")
        notes.append(f"The page's 'Next review due' date ({due.day} {due:%B %Y}) "
                     "had passed when it was copied.")
    if row["last_reviewed"] and int(row["last_reviewed"][:4]) <= 2021:
        notes.append(f"Last reviewed in {row['last_reviewed'][:4]}.")
    if doc_id in UK_SERVICES:
        notes.append("Describes NHS services in England.")
    return " ".join(notes)


def main():
    with open(CATALOG, encoding="utf-8", newline="") as handle:
        rows = {r["doc_id"]: r for r in csv.DictReader(handle)}
    written, rewritten, kept, failed, short, dosage_hits = [], [], [], [], [], {}
    headings, dropped, videos = {}, {}, 0

    for doc_id in sorted(TOPICS):
        topics = TOPICS[doc_id]
        row = rows.get(doc_id)
        if row is None or row["status"] != "fetched":
            failed.append((doc_id, "not a fetched page in nhs_pages.csv"))
            continue
        out_path = ROOT / "clean" / "international" / topics[0] / f"{doc_id}.md"
        raw_path = ROOT / "raw" / "nhs" / f"{doc_id}.html"
        existed = out_path.exists()
        if existed and "contains_treatment_advice: FILL_ME" not in out_path.read_text(
                encoding="utf-8"):
            kept.append(doc_id)
            continue
        if not raw_path.is_file():
            failed.append((doc_id, "raw file missing"))
            continue

        soup = BeautifulSoup(raw_path.read_text(encoding="utf-8"), "html.parser")
        main_tag = soup.find("main")
        article = main_tag.find("article") if main_tag else None
        if article is None or main_tag.find("h1") is None:
            failed.append((doc_id, "no <main>/<article>/<h1>"))
            continue
        title = clean(main_tag.find("h1").get_text(" "))

        for br in article.find_all("br"):
            br.replace_with(" ")
        for element in article.find_all(class_=lambda c: c and "app-brightcove" in c):
            element.decompose()
            videos += 1
        for tag in article.find_all(REMOVE_TAGS):
            tag.decompose()
        for section in article.find_all("section"):
            heading = section.find("h2")
            if not heading:
                continue
            key = clean(heading.get_text(" "))
            if key.startswith(DROP_SECTIONS):
                dropped[key] = dropped.get(key, 0) + 1
                section.decompose()
            elif key in LINK_SECTIONS:
                links = sum(len(a.get_text(" ").split()) for a in section.find_all("a"))
                if len(section.get_text(" ").split()) - links <= 25:
                    dropped[key] = dropped.get(key, 0) + 1
                    section.decompose()
        for tag in article.find_all(["p", "ul", "ol", "div", "table"]):
            tag.insert_before(" ")
            tag.insert_after(" ")
        for tag in article.find_all("li"):
            tag.insert_after(" ")
        for heading in article.find_all("h2"):
            text = clean(heading.get_text(" "))
            entry = headings.setdefault(text, [0, doc_id, ""])
            entry[0] += 1
            if not entry[2]:
                section = heading.find_parent("section")
                entry[2] = (clean(section.get_text(" "))[len(text):len(text) + 110]
                            if section else "")

        expected = "".join(article.get_text("").split())
        lines = [("# ", title, title)]
        convert(article, lines)
        got = "".join("".join(plain for _, _, plain in lines[1:]).split())
        if got != expected:
            failed.append((doc_id, "text-equality check failed; " + first_diff(expected, got)))
            continue
        body = render(lines)

        accessed = datetime.fromtimestamp(raw_path.stat().st_mtime)
        ddmmyy = accessed.strftime("%d%m%y")
        attribution = (f"Information from the NHS website as at {ddmmyy}. "
                       "Information from the NHS website is licensed under the "
                       "Open Government Licence v3.0.")
        found = sorted({m.lower() for m in DOSAGE_RE.findall(body)})
        trimester = "postpartum" if topics[0] == "postpartum-newborn" else "all"
        front = [
            "---",
            f"doc_id: {doc_id}",
            f"title: {q(title)}",
            'source_org: "NHS (UK)"',
            "source_type: government",
            "licence_tier: A",
            'licence: "Open Government Licence v3.0"',
            f"attribution: {q(attribution)}",
            f"url: {q(row['final_url'] or row['url'])}",
            f"date_accessed: {accessed.strftime('%Y-%m-%d')}",
            f"published_or_reviewed: {q(row['last_reviewed'])}",
            "region: international",
            "country: UK",
            "language: en",
            "doc_type: patient_education",
            "audience: patient",
            f"topics: [{', '.join(topics)}]",
            f"trimester: {q(trimester)}",
            "week_start: null",
            "week_end: null",
            "contains_treatment_advice: FILL_ME",
            f"contains_dosage: {'true' if found else 'false'}",
            f"time_sensitive: {'true' if doc_id in TIME_SENSITIVE else 'false'}",
            "priority: P1",
            f"raw_file: raw/nhs/{doc_id}.html",
            "part: null",
            f"notes: {q(make_notes(row, doc_id))}",
            "---",
            "",
        ]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(front) + "\n" + body + "\n")

        words = len(body.split())
        (rewritten if existed else written).append(doc_id)
        if words < 100:
            short.append((doc_id, words))
        if found:
            dosage_hits[doc_id] = found

    print("=" * 70)
    print(f"Summary: new {len(written)}, regenerated {len(rewritten)}, "
          f"left alone (flag already set) {len(kept)} {kept}, failed {len(failed)}")
    for doc_id, reason in failed:
        print(f"  FAILED {doc_id}: {reason}")
    unassigned = [d for d, r in rows.items() if r["status"] == "fetched" and d not in TOPICS]
    print(f"Fetched pages with no topic assigned (not extracted): {unassigned}")
    print(f"Video blocks removed: {videos}; promo sections dropped: {dropped}")
    print(f"Under 100 words (need short_exception): {short or 'none'}")
    print("\nH2 headings repeated on 3+ pages (check for leftover boilerplate):")
    for text, (count, example, snippet) in sorted(headings.items(), key=lambda kv: -kv[1][0])[:15]:
        if count >= 3:
            print(f"  {count:>3}  {text}  [e.g. {example}: {snippet}]")
    print(f"\ncontains_dosage set to true on {len(dosage_hits)} files "
          "(read these; 'units' can mean alcohol or hospital units):")
    for doc_id, found in sorted(dosage_hits.items()):
        print(f"  {doc_id:<24}{found}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    main()