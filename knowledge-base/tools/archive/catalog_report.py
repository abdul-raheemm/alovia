#!/usr/bin/env python3
"""Read-only report on nhs_pages.csv and the saved NHS HTML (no network)."""
import csv
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

RAW = Path("alovia-knowledge-base/raw/nhs")

with open("nhs_pages.csv", encoding="utf-8", newline="") as handle:
    rows = list(csv.DictReader(handle))

print("== Rows that are not 'fetched' ==")
for row in rows:
    if row["status"] != "fetched":
        print(f"{row['doc_id']:<24}{row['status']:<15}{row['url']}")
        print(f"{'':<39}final: {row['final_url'] or '-'} | {row['note']}")

print("\n== doc_id | title (fetched) ==")
for row in sorted(rows, key=lambda r: r["doc_id"]):
    if row["status"] == "fetched":
        print(f"{row['doc_id']} | {row['title']}")

print("\n== Links in <main> that point outside /pregnancy/ ==")
targets = defaultdict(set)
files = list(RAW.glob("NHS-*.html")) + list((RAW / "hubs").glob("*.html"))
for path in files:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    main = soup.find("main")
    for anchor in (main.find_all("a", href=True) if main else []):
        parts = urlsplit(anchor["href"])
        if parts.netloc not in ("", "www.nhs.uk"):
            continue
        link = parts.path
        if not link.startswith("/") or link.startswith("/pregnancy/") or link == "/":
            continue
        targets[link.strip("/").split("/")[0]].add(link)
for segment, paths in sorted(targets.items(), key=lambda item: -len(item[1])):
    print(f"{len(paths):>4}  /{segment}/   e.g. {sorted(paths)[:3]}")