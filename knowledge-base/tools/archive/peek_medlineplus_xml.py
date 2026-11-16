#!/usr/bin/env python3
"""Show how the English 'Pregnancy' health topic is stored in the MedlinePlus
Health Topic XML (attribute names, child element names, summary length).

Usage:
    python peek_medlineplus_xml.py path/to/the-unzipped-file.xml

It only reads the file. It does not change anything and uses no internet.
"""
import re
import sys
import xml.etree.ElementTree as ET

TARGET = "https://medlineplus.gov/pregnancy.html"


def describe(elem, label):
    print(f"\n--- {label} ---")
    for key, value in elem.attrib.items():
        print(f"   attribute {key} = {value[:80]}")
    names = [child.tag for child in elem]
    print(f"   child element names (in order) = {names}")
    print(f"   distinct child names = {sorted(set(names))}")


def summary_words(elem):
    summary = elem.find("full-summary")
    if summary is None or not summary.text:
        return None
    plain = re.sub(r"<[^>]+>", " ", summary.text)
    return len(plain.split())


def main(path):
    first = None
    target = None
    topic_count = 0
    english = 0
    for _, elem in ET.iterparse(path, events=("end",)):
        if elem.tag != "health-topic":
            continue
        topic_count += 1
        if elem.attrib.get("language") == "English":
            english += 1
        if first is None:
            first = ET.fromstring(ET.tostring(elem))
        if elem.attrib.get("url") == TARGET and target is None:
            target = ET.fromstring(ET.tostring(elem))
    print(f"health-topic records: {topic_count} (English: {english})")
    if first is not None:
        describe(first, "FIRST health-topic record in the file")
    if target is None:
        print("\nNo health-topic record has the Pregnancy URL as its url attribute.")
        return
    describe(target, "the Pregnancy health-topic record")
    print(f"   words in full-summary (tags removed) = {summary_words(target)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python peek_medlineplus_xml.py path/to/file.xml")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    main(sys.argv[1])
