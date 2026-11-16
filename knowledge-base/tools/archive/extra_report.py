#!/usr/bin/env python3
"""Read-only report on the extra NHS pages (no network)."""
import csv
from pathlib import Path
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

RAW = Path("alovia-knowledge-base/raw/nhs")
EXTRA = {"conditions", "tests-and-treatments", "baby", "vaccinations"}
SITE = "https://www.nhs.uk"

with open("nhs_pages.csv", encoding="utf-8", newline="") as handle:
    extra = [r for r in csv.DictReader(handle) if r["hub"] in EXTRA]

print("== Extra pages NOT kept ==")
for row in sorted(extra, key=lambda r: (r["status"], r["doc_id"])):
    if row["status"] == "fetched":
        continue
    final = f" -> {row['final_url'].replace(SITE, '')}" if row["final_url"] else ""
    print(f"{row['status']:<15}{row['doc_id']:<15}{(row['title'] or '-')[:48]:<50}"
          f"{row['url'].replace(SITE, '')}{final}")

print("\n== Sub-pages linked from kept condition/test pages ==")
all_children = set()
for row in extra:
    if row["status"] != "fetched" or row["hub"] not in ("conditions", "tests-and-treatments"):
        continue
    path = RAW / f"{row['doc_id']}.html"
    if not path.exists():
        continue
    main = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser").find("main")
    base = urlsplit(row["url"]).path.strip("/").split("/")
    children = set()
    for anchor in (main.find_all("a", href=True) if main else []):
        parts = urlsplit(anchor["href"])
        if parts.netloc not in ("", "www.nhs.uk"):
            continue
        segments = parts.path.strip("/").split("/")
        if segments[:len(base)] == base and len(segments) > len(base):
            children.add(segments[len(base)])
            all_children.add("/".join(segments[:len(base) + 1]))
    if children:
        print(f"{row['doc_id']:<14}{len(children):>3}  {row['title'][:38]:<40}{sorted(children)}")
print(f"\nTotal distinct sub-pages: {len(all_children)}")