#!/usr/bin/env python3
"""List which HTML tags and special characters appear in the summaries of the
37 selected MedlinePlus topics, so the Markdown conversion can be built on the
real structure.

Usage:
    py inspect_summary_tags.py path/to/mplus_topics.xml

It only reads the XML. It prints a short report and writes nothing.
"""
import sys
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from html.parser import HTMLParser

BASE = "https://medlineplus.gov/"
SLUGS = [
    # antenatal-care
    "pregnancy", "prenatalcare", "teenagepregnancy",
    # tests-scans
    "prenataltesting",
    # nutrition
    "pregnancyandnutrition", "folicacid",
    # substances-medicines
    "pregnancyandmedicines", "pregnancyandsubstanceuse", "pregnancyandopioids",
    "fetalalcoholspectrumdisorders",
    # fetal-development
    "fetalhealthanddevelopment",
    # labour-birth
    "childbirth", "childbirthproblems", "cesareandelivery",
    # conditions
    "birthdefects", "miscarriage", "ectopicpregnancy", "healthproblemsinpregnancy",
    "highbloodpressureinpregnancy", "diabetesandpregnancy", "hivandpregnancy",
    "infectionsandpregnancy", "tumorsandpregnancy", "twinstripletsmultiplebirths",
    "rhincompatibility", "pretermlabor",
    # mental-health
    "postpartumdepression",
    # postpartum-newborn
    "breastfeeding", "postpartumcare", "newbornscreening",
    "infantandnewbornnutrition", "babyhealthcheckup", "prematurebabies",
    "suddeninfantdeathsyndrome", "infantandnewborncare",
    "commoninfantandnewbornproblems", "uncommoninfantandnewbornproblems",
]
SELECTED = {f"{BASE}{slug}.html" for slug in SLUGS}
COMMON_TAGS = {"p", "a", "ul", "li", "b", "strong", "i", "em"}


class TagCollector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = Counter()
        self.attrs = defaultdict(set)

    def handle_starttag(self, tag, attrs):
        self.tags[tag] += 1
        for name, _ in attrs:
            self.attrs[tag].add(name)


def main(path):
    tag_counts = Counter()
    tag_topics = defaultdict(set)
    tag_attrs = defaultdict(set)
    chars = Counter()
    found = set()

    for _, elem in ET.iterparse(path, events=("end",)):
        if elem.tag != "health-topic":
            continue
        url = elem.attrib.get("url")
        if elem.attrib.get("language") == "English" and url in SELECTED:
            found.add(url)
            title = elem.attrib.get("title", url)
            summary = elem.find("full-summary")
            html = summary.text if summary is not None and summary.text else ""
            parser = TagCollector()
            parser.feed(html)
            for tag, count in parser.tags.items():
                tag_counts[tag] += count
                tag_topics[tag].add(title)
            for tag, names in parser.attrs.items():
                tag_attrs[tag] |= names
            for ch in html:
                if ord(ch) > 127:
                    chars[ch] += 1
        elem.clear()

    print(f"Found {len(found)} of {len(SELECTED)} selected topics in the file.")
    missing = sorted(SELECTED - found)
    if missing:
        print("NOT FOUND:")
        for url in missing:
            print(f"   {url}")

    print("\nHTML tags used in the summaries (total count, number of topics):")
    for tag, count in tag_counts.most_common():
        print(f"   <{tag}>  {count}  in {len(tag_topics[tag])} topics")

    print("\nAttribute names seen on each tag:")
    for tag in sorted(tag_attrs):
        print(f"   <{tag}>: {sorted(tag_attrs[tag])}")

    print("\nTopics that use less common tags:")
    for tag in sorted(set(tag_counts) - COMMON_TAGS):
        names = sorted(tag_topics[tag])
        shown = ", ".join(names[:6]) + (" ..." if len(names) > 6 else "")
        print(f"   <{tag}>: {shown}")

    print("\nNon-ASCII characters in the summaries:")
    for ch, count in chars.most_common():
        name = unicodedata.name(ch, "unknown")
        print(f"   U+{ord(ch):04X}  {name}  x{count}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: py inspect_summary_tags.py path/to/mplus_topics.xml")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    main(sys.argv[1])
