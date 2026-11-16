#!/usr/bin/env python3
"""Extract saved NHS pages (raw/nhs/*.html) into clean/ files with front matter."""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path("alovia-knowledge-base")
PAGES = [
    {
        "id": "NHS-LABOUR-001",
        "url": "https://www.nhs.uk/pregnancy/labour-and-birth/signs-that-labour-has-begun/",
        "topics": ["labour-birth", "warning-signs"],
        "trimester": "all",
        "notes": "",
    },
    {
        "id": "NHS-COMPLICATIONS-001",
        "url": "https://www.nhs.uk/pregnancy/complications/severe-vomiting/",
        "topics": ["conditions", "common-symptoms"],
        "trimester": "all",
        "notes": "The page's 'Next review due' date (11 January 2026) had passed "
                 "when it was copied.",
    },
]
REMOVE_TAGS = ["script", "style", "video", "nav", "aside"]
DROP_SECTIONS = ("Sign up for Best Start in Life",)


def clean(text):
    return " ".join(text.split())


def convert(node, lines):
    for child in node.children:
        name = getattr(child, "name", None)
        if not name:
            continue
        if name in ("h1", "h2", "h3", "h4"):
            text = clean(child.get_text(" "))
            text = re.sub(r":(?=[A-Za-z])", ": ", text)
            if text:
                lines.append(("#" * int(name[1]) + " ", text))
        elif name == "p":
            text = clean(child.get_text(""))
            if text:
                lines.append(("", text))
        elif name in ("ul", "ol"):
            for item in child.find_all("li", recursive=False):
                text = clean(item.get_text(""))
                if text:
                    lines.append(("- ", text))
        else:
            convert(child, lines)


def render(lines):
    out, previous = "", None
    for marker, text in lines:
        if previous is not None:
            out += "\n" if (marker == "- " and previous == "- ") else "\n\n"
        out += marker + text
        previous = marker
    return out


def q(value):
    return json.dumps(value, ensure_ascii=False)


def process(page):
    doc_id = page["id"]
    raw_path = ROOT / "raw" / "nhs" / f"{doc_id}.html"
    out_path = ROOT / "clean" / "international" / page["topics"][0] / f"{doc_id}.md"
    print("=" * 70)
    print(doc_id)
    if out_path.exists():
        print(f"  SKIPPED: {out_path} already exists (never overwritten)")
        return
    if not raw_path.is_file():
        print(f"  SKIPPED: {raw_path} not found")
        return

    soup = BeautifulSoup(raw_path.read_text(encoding="utf-8"), "html.parser")
    main_tag = soup.find("main")
    title = clean(main_tag.find("h1").get_text(" "))
    match = re.search(r"Page last reviewed:\s*(\d{1,2} \w+ \d{4})", soup.get_text(" "))
    if not match:
        print("  FAILED: 'Page last reviewed' date not found")
        return
    reviewed = datetime.strptime(match.group(1), "%d %B %Y").strftime("%Y-%m-%d")

    article = main_tag.find("article")
    for br in article.find_all("br"):
        br.replace_with(" ")
    for tag in article.find_all(REMOVE_TAGS):
        tag.decompose()
    for section in article.find_all("section"):
        heading = section.find("h2")
        if heading and clean(heading.get_text(" ")).startswith(DROP_SECTIONS):
            print(f"  removed section: {clean(heading.get_text(' '))}")
            section.decompose()

    expected = "".join(article.get_text("").split())
    lines = [("# ", title)]
    convert(article, lines)
    got = "".join("".join(text for _, text in lines[1:]).split())
    if got != expected:
        print("  FAILED: text-equality check (text lost or changed); nothing written")
        return
    body = render(lines)

    accessed = datetime.fromtimestamp(raw_path.stat().st_mtime)
    ddmmyy = accessed.strftime("%d%m%y")
    attribution = (f"Information from the NHS website as at {ddmmyy}. "
                   "Information from the NHS website is licensed under the "
                   "Open Government Licence v3.0.")
    front = [
        "---",
        f"doc_id: {doc_id}",
        f"title: {q(title)}",
        'source_org: "NHS (UK)"',
        "source_type: government",
        "licence_tier: A",
        'licence: "Open Government Licence v3.0"',
        f"attribution: {q(attribution)}",
        f"url: {q(page['url'])}",
        f"date_accessed: {accessed.strftime('%Y-%m-%d')}",
        f"published_or_reviewed: {q(reviewed)}",
        "region: international",
        "country: UK",
        "language: en",
        "doc_type: patient_education",
        "audience: patient",
        f"topics: [{', '.join(page['topics'])}]",
        f"trimester: {q(page['trimester'])}",
        "week_start: null",
        "week_end: null",
        "contains_treatment_advice: FILL_ME",
        "contains_dosage: FILL_ME",
        "time_sensitive: false",
        "priority: P1",
        f"raw_file: raw/nhs/{doc_id}.html",
        "part: null",
        f"notes: {q(page['notes'])}",
        "---",
        "",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(front) + "\n" + body + "\n")

    print(f"  written   : {out_path}")
    print(f"  copy date : {accessed.strftime('%Y-%m-%d')} (DDMMYY {ddmmyy})")
    print(f"  reviewed  : {reviewed}")
    print(f"  words     : {len(body.split())}")
    print(f"  FIRST: {lines[1][1][:90]}")
    print(f"  LAST : {lines[-1][1][-90:]}")


if __name__ == "__main__":
    for page in PAGES:
        process(page)
    sys.exit(0)