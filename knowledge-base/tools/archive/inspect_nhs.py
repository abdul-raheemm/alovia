#!/usr/bin/env python3
"""Save three NHS pages to raw/nhs/ and print their structure (read-only inspection)."""
import re
import sys
import time
import urllib.request
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path("alovia-knowledge-base")
PAGES = [
    ("NHS-LABOUR-001",
     "https://www.nhs.uk/pregnancy/labour-and-birth/signs-that-labour-has-begun/",
     "9 November 2023"),
    ("NHS-COMPLICATIONS-001",
     "https://www.nhs.uk/pregnancy/complications/severe-vomiting/",
     "11 January 2023"),
    ("NHS-SYMPTOMS-001",
     "https://www.nhs.uk/pregnancy/common-symptoms/common-health-problems/",
     "22 April 2024"),
]
HEADERS = {"User-Agent": "AloviaStudentProject/1.0 (college capstone; one-off manual copy)"}


class Inventory(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_main = False
        self.tags = Counter()
        self.headings = []
        self._heading = None

    def handle_starttag(self, tag, attrs):
        if tag == "main":
            self.in_main = True
        if self.in_main:
            self.tags[tag] += 1
            if tag in ("h1", "h2", "h3"):
                self._heading = [tag, ""]

    def handle_endtag(self, tag):
        if tag == "main":
            self.in_main = False
        if self._heading and tag == self._heading[0]:
            self.headings.append((self._heading[0], self._heading[1].strip()))
            self._heading = None

    def handle_data(self, data):
        if self._heading:
            self._heading[1] += data


def main():
    out_dir = ROOT / "raw" / "nhs"
    out_dir.mkdir(parents=True, exist_ok=True)
    for doc_id, url, expected in PAGES:
        print("=" * 70)
        print(doc_id)
        try:
            request = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=30) as response:
                final_url = response.geturl()
                html = response.read().decode("utf-8")
        except Exception as exc:
            print(f"  FAILED: {exc}")
            time.sleep(2)
            continue

        (out_dir / f"{doc_id}.html").write_text(html, encoding="utf-8")
        print(f"  asked for : {url}")
        print(f"  final URL : {final_url}")
        print(f"  size      : {len(html):,} characters")

        match = re.search(r"Page last reviewed:?[^<]{0,60}", html)
        print(f"  reviewed  : {match.group(0).strip() if match else 'NOT FOUND'}"
              f"  (you read: {expected})")

        inv = Inventory()
        inv.feed(html)
        print(f"  tags in <main>: {dict(inv.tags)}")
        for level, text in inv.headings:
            print(f"    {level}: {text}")
        time.sleep(2)


if __name__ == "__main__":
    sys.exit(main())