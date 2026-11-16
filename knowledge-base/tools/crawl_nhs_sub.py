#!/usr/bin/env python3
"""Apply skip/rescue decisions, then fetch sub-pages of kept condition/test pages.

    py crawl_nhs_sub.py
"""
import sys
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

import crawl_nhs as c
import crawl_nhs_extra as e

SKIP = [
    "NHS-BABY-003", "NHS-BABY-006", "NHS-BABY-015",
    "NHS-COND-003", "NHS-COND-014", "NHS-COND-040", "NHS-COND-080",
]
DEAD = ["NHS-COND-064"]
RESCUE = [
    "NHS-COND-012", "NHS-COND-049", "NHS-COND-055",
    "NHS-TESTS-015", "NHS-TESTS-022",
]
NO_SUBPAGES = ("national-fgm-support-clinics",)


def mark(cat, doc_ids, status, note, expected):
    by_id = {row["doc_id"]: row for row in cat.values()}
    for doc_id in doc_ids:
        row = by_id.get(doc_id)
        if row is None:
            print(f"  CHECK {doc_id}: not found in the catalogue")
            continue
        flag = "" if row["status"] == expected else f"  (CHECK: was {row['status']})"
        print(f"  {status:<11}{doc_id:<15}{(row['title'] or '-')[:40]:<42}"
              f"{row['url'].replace(c.BASE, '')}{flag}")
        row.update(status=status, note=note)


def collect_sub(cat):
    added = 0
    for row in list(cat.values()):
        if row["status"] != "fetched" or row["hub"] not in ("conditions", "tests-and-treatments"):
            continue
        path = c.RAW / f"{row['doc_id']}.html"
        if not path.exists():
            continue
        parent = urlsplit(row["final_url"] or row["url"]).path.strip("/").split("/")
        main = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser").find("main")
        for anchor in (main.find_all("a", href=True) if main else []):
            link = e.norm2(anchor["href"], c.BASE + "/" + "/".join(parent) + "/")
            if not link or link in cat:
                continue
            parts = urlsplit(link).path.strip("/").split("/")
            if (parts[:len(parent)] == parent and len(parts) == len(parent) + 1
                    and parts[-1] not in NO_SUBPAGES):
                new = c.new_row(link, "subpage of " + row["doc_id"])
                new["hub"] = parts[0]
                new["status"] = "extra_listed"
                cat[link] = new
                added += 1
    return added


def main():
    cat = c.load_catalog()
    if not cat:
        sys.exit("nhs_pages.csv not found.")
    print("Decisions:")
    mark(cat, SKIP, "skipped", "skipped by decision", "fetched")
    mark(cat, DEAD, "dead_link", "404 when fetched", "extra_error")
    mark(cat, RESCUE, "extra_listed", "rescued: kept although few pregnancy mentions",
         "not_relevant")
    c.save_catalog(cat)

    print("\n--- Pass 1: rescued pages (relevance filter off) ---")
    saved = e.NEEDS_PREGNANCY_WORD
    e.NEEDS_PREGNANCY_WORD = set()
    e.run()
    e.NEEDS_PREGNANCY_WORD = saved

    cat = c.load_catalog()
    added = collect_sub(cat)
    c.assign_ids(cat)
    c.save_catalog(cat)
    print(f"\n--- Pass 2: {added} sub-pages listed ---")
    e.run()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    main()