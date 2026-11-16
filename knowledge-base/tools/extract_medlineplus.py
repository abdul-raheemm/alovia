#!/usr/bin/env python3
"""Turn selected MedlinePlus health-topic summaries into draft knowledge-base files.

Usage:
    py extract_medlineplus.py alovia-knowledge-base medlineplus_selection.csv

What it does:
  - reads the official Health Topic XML saved under raw/medlineplus/
  - takes the English summary of each topic listed in the selection CSV
  - converts the summary's HTML to Markdown WITHOUT changing any wording
    (paragraphs, <h3> -> "## ", lists -> "- ", <strong> -> **bold**, links ->
    link text only, <br> -> line break)
  - checks that no text was lost or added (all text compared, ignoring spaces)
  - writes clean/international/<primary-topic>/<doc_id>.md with front matter

It never overwrites an existing file and never touches raw/.
Fields it cannot know are left as FILL_ME (contains_treatment_advice) so that
validate_kb.py refuses the file until a person has read the text and set them.
"""
import csv
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
import xml.etree.ElementTree as ET

# ---- facts about this source (from the MedlinePlus terms page and registry) ----
RAW_FILE = "raw/medlineplus/mplus_topics_2026-10-01.xml"
SOURCE = {
    "source_org": "MedlinePlus (US National Library of Medicine)",
    "source_type": "government",
    "licence_tier": "A",
    "licence": ("Public domain (US federal government work), per MedlinePlus "
                "'Linking to and Using Content from MedlinePlus'"),
    "attribution": "Source: MedlinePlus, National Library of Medicine.",
    "date_accessed": "2026-10-02",
    "region": "international",
    "country": "US",
    "language": "en",
    "doc_type": "patient_education",
    "audience": "patient",
}
TRIMESTERS = {"1", "2", "3", "all", "postpartum"}
PRIORITIES = {"P1", "P2", "P3"}
REVIEWED_RE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
DOSAGE_RE = re.compile(
    r"\b(mg|mcg|µg|μg|iu|ml|milligrams?|micrograms?|tablets?|capsules?"
    r"|doses?|dosage|units)\b",
    re.IGNORECASE,
)

# ---- HTML -> small tree ----
BLOCK_TAGS = {"p", "h3", "ul", "ol"}
KNOWN_TAGS = {"p", "h3", "ul", "ol", "li", "a", "strong", "b", "br"}


class Node:
    def __init__(self, tag, attrs=None):
        self.tag = tag
        self.attrs = dict(attrs or [])
        self.children = []


class TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("root")
        self.stack = [self.root]
        self.unknown_tags = set()
        self.p_classes = set()
        self.auto_closed = 0

    def handle_starttag(self, tag, attrs):
        if tag not in KNOWN_TAGS:
            self.unknown_tags.add(tag)
        if tag == "p":
            self.p_classes.add(dict(attrs).get("class", "(none)"))
        if tag in ("p", "li") and self.stack[-1].tag == tag:
            self.stack.pop()
            self.auto_closed += 1
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag != "br":
            self.stack.append(node)

    def handle_endtag(self, tag):
        if tag == "br":
            return
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def all_text(node):
    parts = []
    for child in node.children:
        parts.append(child if isinstance(child, str) else all_text(child))
    return "".join(parts)


# ---- Markdown rendering ----
BOLD_ON, BOLD_OFF, BREAK = "\x01", "\x02", "\x03"


def inline_node(node):
    parts = []
    for child in node.children:
        if isinstance(child, str):
            parts.append(child)
        elif child.tag == "br":
            parts.append(BREAK)
        elif child.tag in ("strong", "b"):
            parts.append(BOLD_ON + inline_node(child) + BOLD_OFF)
        else:  # a, and anything unknown: keep only the text
            parts.append(inline_node(child))
    return "".join(parts)


def finish_inline(items):
    raw = "".join(i if isinstance(i, str) else inline_node(i) for i in items)
    text = re.sub(r"[ \t\r\n]+", " ", raw)
    text = re.sub(r" ?" + BREAK + " ?", "  \n", text)
    text = re.sub(BOLD_ON + r"( *)", r"\1" + BOLD_ON, text)
    text = re.sub(r"( *)" + BOLD_OFF, BOLD_OFF + r"\1", text)
    text = text.replace(BOLD_ON + BOLD_OFF, "")
    text = text.replace(BOLD_ON, "**").replace(BOLD_OFF, "**")
    return text.strip()


def render_list(node, depth, stats):
    lines = []
    pad = "  " * depth
    number = 0
    for item in node.children:
        if isinstance(item, str):
            if item.strip():
                stats["stray_text_in_list"] += 1
                lines.append(f"{pad}- {finish_inline([item])}")
            continue
        if item.tag != "li":
            stats["stray_text_in_list"] += 1
            lines.append(f"{pad}- {finish_inline([item])}")
            continue
        number += 1
        marker = f"{number}." if node.tag == "ol" else "-"
        text_items, nested = [], []
        for child in item.children:
            if isinstance(child, Node) and child.tag in ("ul", "ol"):
                stats["nested_lists"] += 1
                nested.append(render_list(child, depth + 1, stats))
            elif isinstance(child, Node) and child.tag == "p":
                stats["p_inside_li"] += 1
                text_items.extend([" ", child, " "])
            else:
                text_items.append(child)
        lines.append(f"{pad}{marker} {finish_inline(text_items)}")
        lines.extend(nested)
    return "\n".join(lines)


def render_blocks(root, stats):
    blocks, loose = [], []

    def flush():
        text = finish_inline(loose)
        if text:
            blocks.append(text)
        loose.clear()

    for child in root.children:
        if isinstance(child, Node) and child.tag in BLOCK_TAGS:
            flush()
            if child.tag == "p":
                text = finish_inline([child])
                if text:
                    blocks.append(text)
            elif child.tag == "h3":
                text = finish_inline([child])
                if text:
                    blocks.append("## " + text)
            else:
                blocks.append(render_list(child, 0, stats))
        else:
            loose.append(child)
    flush()
    return "\n\n".join(blocks)


def words_from_markdown(markdown):
    text = re.sub(r"(?m)^[ ]*(## |- |\d+\. )", "", markdown)
    return "".join(text.replace("**", "").split())


# ---- front matter ----
def quote(value):
    return json.dumps(value, ensure_ascii=False)


def front_matter(row, title, url, treatment, dosage, topics):
    lines = [
        "---",
        f"doc_id: {row['doc_id']}",
        f"title: {quote(title)}",
        f"source_org: {quote(SOURCE['source_org'])}",
        f"source_type: {SOURCE['source_type']}",
        f"licence_tier: {SOURCE['licence_tier']}",
        f"licence: {quote(SOURCE['licence'])}",
        f"attribution: {quote(SOURCE['attribution'])}",
        f"url: {quote(url)}",
        f"date_accessed: {SOURCE['date_accessed']}",
        f"published_or_reviewed: {quote(row['published_or_reviewed'])}",
        f"region: {SOURCE['region']}",
        f"country: {SOURCE['country']}",
        f"language: {SOURCE['language']}",
        f"doc_type: {SOURCE['doc_type']}",
        f"audience: {SOURCE['audience']}",
        f"topics: [{', '.join(topics)}]",
        f"trimester: {quote(row['trimester'])}",
        f"week_start: {row['week_start'] or 'null'}",
        f"week_end: {row['week_end'] or 'null'}",
        f"contains_treatment_advice: {treatment}",
        f"contains_dosage: {'true' if dosage else 'false'}",
        "time_sensitive: false",
        f"priority: {row['priority']}",
        f"raw_file: {RAW_FILE}",
        "part: null",
        f"notes: {quote(row['notes'])}",
    ]
    if row["short_exception"] == "true":
        lines.append("short_exception: true")
    lines.append("---")
    return "\n".join(lines)


def check_row(row):
    problems = []
    for key in ("url", "doc_id", "topics", "trimester", "published_or_reviewed", "priority"):
        if not row[key]:
            problems.append(f"{key} is empty")
    if row["trimester"] and row["trimester"] not in TRIMESTERS:
        problems.append(f"trimester '{row['trimester']}' not in {sorted(TRIMESTERS)}")
    if row["priority"] and row["priority"] not in PRIORITIES:
        problems.append(f"priority '{row['priority']}' not P1/P2/P3")
    if row["published_or_reviewed"] and not REVIEWED_RE.match(row["published_or_reviewed"]):
        problems.append("published_or_reviewed must be YYYY, YYYY-MM or YYYY-MM-DD")
    if row["contains_treatment_advice"] not in ("", "true", "false"):
        problems.append("contains_treatment_advice must be blank, true or false")
    if row["short_exception"] not in ("", "true"):
        problems.append("short_exception must be blank or true")
    if row["short_exception"] == "true" and not row["notes"]:
        problems.append("short_exception needs a reason in notes")
    for key in ("week_start", "week_end"):
        if row[key] and not row[key].isdigit():
            problems.append(f"{key} must be a number or blank")
    return problems


def read_selection(path):
    columns = ["url", "doc_id", "topics", "trimester", "week_start", "week_end",
               "published_or_reviewed", "priority", "contains_treatment_advice",
               "short_exception", "notes"]
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in columns if c not in (reader.fieldnames or [])]
        if missing:
            sys.exit(f"Selection file is missing columns: {missing}")
        return [{c: (r.get(c) or "").strip() for c in columns} for r in reader]


def load_topics(xml_path, wanted_urls):
    found = {}
    for _, elem in ET.iterparse(xml_path, events=("end",)):
        if elem.tag != "health-topic":
            continue
        url = elem.attrib.get("url")
        if elem.attrib.get("language") == "English" and url in wanted_urls:
            summary = elem.find("full-summary")
            found[url] = (elem.attrib.get("title", ""),
                          summary.text if summary is not None and summary.text else "")
        elem.clear()
    return found


def main(root, selection_path):
    root = Path(root)
    xml_path = root / RAW_FILE
    if not xml_path.is_file():
        sys.exit(f"XML not found: {xml_path}")
    rows = read_selection(selection_path)
    topics_by_url = load_topics(xml_path, {r["url"] for r in rows})

    written = failed = skipped = 0
    seen_classes, unknown_tags, stats_total = set(), set(), {}
    for row in rows:
        label = row["doc_id"] or row["url"]
        problems = check_row(row)
        if problems:
            print(f"FAILED {label}: " + "; ".join(problems))
            failed += 1
            continue
        if row["url"] not in topics_by_url:
            print(f"FAILED {label}: English topic not found in the XML for {row['url']}")
            failed += 1
            continue

        title, html = topics_by_url[row["url"]]
        topics = [t for t in row["topics"].split("|") if t]
        target = root / "clean" / SOURCE["region"] / topics[0] / f"{row['doc_id']}.md"
        if target.exists():
            print(f"SKIPPED {label}: file already exists, not overwritten")
            skipped += 1
            continue

        builder = TreeBuilder()
        builder.feed(html)
        builder.close()
        stats = {"nested_lists": 0, "p_inside_li": 0, "stray_text_in_list": 0}
        body = render_blocks(builder.root, stats)

        same_text = "".join(all_text(builder.root).split()) == words_from_markdown(body)
        if not same_text:
            print(f"FAILED {label}: the converted text does not match the source text; "
                  "nothing was written")
            failed += 1
            continue

        seen_classes |= builder.p_classes
        unknown_tags |= builder.unknown_tags
        for key, value in stats.items():
            stats_total[key] = stats_total.get(key, 0) + value
        stats_total["auto_closed_tags"] = stats_total.get("auto_closed_tags", 0) + builder.auto_closed

        match = DOSAGE_RE.search(body)
        treatment = row["contains_treatment_advice"] or "FILL_ME"
        text = (front_matter(row, title, row["url"], treatment, bool(match), topics)
                + f"\n\n# {title}\n\n{body}\n")
        words = len(f"# {title} {body}".split())

        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        written += 1
        notes = []
        if match:
            notes.append(f"dosage word found: '{match.group(0)}' -> contains_dosage: true")
        if treatment == "FILL_ME":
            notes.append("set contains_treatment_advice after reading")
        if words < 100:
            notes.append(f"under 100 words ({words})")
        print(f"WROTE {target.relative_to(root)}  ({words} words, text check passed)"
              + ("".join(f"\n      - {n}" for n in notes)))

    print(f"\nDone: {written} written, {skipped} skipped, {failed} failed.")
    print(f"<p> class values seen: {sorted(seen_classes)}")
    print(f"Unknown tags (kept as plain text): {sorted(unknown_tags) or 'none'}")
    print(f"Structure counts: {stats_total}")
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: py extract_medlineplus.py alovia-knowledge-base medlineplus_selection.csv")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    sys.exit(main(sys.argv[1], sys.argv[2]))
