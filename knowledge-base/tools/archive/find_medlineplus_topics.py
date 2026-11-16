#!/usr/bin/env python3
"""List English MedlinePlus health topics whose title or 'also called' names
match pregnancy-related keywords, with the word count of each summary.

Usage:
    python find_medlineplus_topics.py path/to/mplus_topics.xml [extra words ...]

Example with extra search words:
    python find_medlineplus_topics.py file.xml anemia thyroid "urinary tract"

It only reads the XML. It prints a table and writes candidates_medlineplus.csv
in the folder you run it from. It does not touch the knowledge base folder.
"""
import csv
import re
import sys
import xml.etree.ElementTree as ET

BASE_WORDS = [
    "pregnan", "prenatal", "perinatal", "birth", "fetal", "fetus", "newborn",
    "breastfe", "postpartum", "miscarriage", "ectopic", "gestational",
    "preeclampsia", "eclampsia", "folic", "cesarean", "lactation", "baby",
    "babies", "infant", "labor and delivery", "childbirth",
]
OUTPUT_CSV = "candidates_medlineplus.csv"


def build_pattern(words):
    parts = [r"\b" + re.escape(word) for word in words]
    return re.compile("|".join(parts), re.IGNORECASE)


def summary_words(topic):
    summary = topic.find("full-summary")
    if summary is None or not summary.text:
        return 0
    return len(re.sub(r"<[^>]+>", " ", summary.text).split())


def main(path, extra_words):
    pattern = build_pattern(BASE_WORDS + extra_words)
    rows = []
    for _, elem in ET.iterparse(path, events=("end",)):
        if elem.tag != "health-topic":
            continue
        if elem.attrib.get("language") == "English":
            title = elem.attrib.get("title", "")
            also = [a.text or "" for a in elem.findall("also-called")]
            haystack = " | ".join([title] + also)
            if pattern.search(haystack):
                rows.append({
                    "title": title,
                    "url": elem.attrib.get("url", ""),
                    "id": elem.attrib.get("id", ""),
                    "words": summary_words(elem),
                    "also_called": "; ".join(also),
                })
        elem.clear()

    rows.sort(key=lambda r: r["title"].lower())
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["title", "url", "id", "words", "also_called"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"{len(rows)} English topics matched. Written to {OUTPUT_CSV}\n")
    print(f"{'words':>5}  title  |  url")
    for row in rows:
        print(f"{row['words']:>5}  {row['title']}  |  {row['url']}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: python find_medlineplus_topics.py file.xml [extra words ...]")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    main(sys.argv[1], sys.argv[2:])
