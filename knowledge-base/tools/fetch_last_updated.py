#!/usr/bin/env python3
"""Read the "Last updated" line at the bottom of each live MedlinePlus page and
fill the empty published_or_reviewed cells of the selection CSV.

Usage:
    py fetch_last_updated.py medlineplus_selection.csv medlineplus_selection_dates.csv

Politeness (rule R7):
  - it reads robots.txt first and skips any page that file disallows
  - one plain GET per page, 2 seconds apart, with a name that identifies it
  - it never logs in and never bypasses anything; it stops if the site blocks it

It only FILLS EMPTY dates. A date you typed is kept, and the script reports
whether the live page agrees with it (this is also a check that the script
reads the pages correctly: your pilot dates should show "agrees").
The first file is never changed; the result goes to the second file.
"""
import csv
import html
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from urllib.robotparser import RobotFileParser

ROBOTS_URL = "https://medlineplus.gov/robots.txt"
USER_AGENT = "AloviaKnowledgeBase/1.0 (student capstone project; polite, 1 request per 2 s)"
DELAY_SECONDS = 2
MONTHS = {name: number for number, name in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], start=1)}
LAST_UPDATED_RE = re.compile(
    r"last\s+updated:?\s+([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})", re.IGNORECASE)
META_RE = re.compile(
    r"""<meta[^>]+modified[^>]*content=["']([^"']+)["']""", re.IGNORECASE)


def visible_text(page):
    page = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", page)
    page = re.sub(r"<[^>]+>", " ", page)
    return re.sub(r"\s+", " ", html.unescape(page))


def parse_last_updated(page):
    """Return (ISO date from the visible 'Last updated' line or None,
    modified-date text from a <meta> tag or None). The last match is used,
    because the line sits at the bottom of the page."""
    matches = LAST_UPDATED_RE.findall(visible_text(page))
    iso = None
    if matches:
        month_name, day, year = matches[-1]
        month = MONTHS.get(month_name.lower())
        if month:
            iso = f"{int(year):04d}-{month:02d}-{int(day):02d}"
    meta = META_RE.search(page)
    return iso, (meta.group(1) if meta else None)


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def load_robots():
    parser = RobotFileParser()
    parser.set_url(ROBOTS_URL)
    parser.read()
    return parser


def plausible(iso):
    year = int(iso[:4])
    return 2000 <= year <= date.today().year and iso <= date.today().isoformat()


def main(source_csv, output_csv, fetch_page=fetch, robots=None, pause=time.sleep):
    with open(source_csv, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        rows = list(reader)

    if robots is None:
        try:
            robots = load_robots()
        except (urllib.error.URLError, OSError) as exc:
            sys.exit(f"Could not read robots.txt ({exc}). Nothing was fetched. "
                     "Check the internet connection, or read the dates by hand.")

    print(f"{'status':<14}{'date':<12}{'page'}")
    filled = 0
    for index, row in enumerate(rows):
        url = row["url"]
        slug = url.rsplit("/", 1)[-1]
        typed = row["published_or_reviewed"].strip()

        if not robots.can_fetch(USER_AGENT, url):
            print(f"{'ROBOTS-BLOCK':<14}{'-':<12}{slug}")
            continue
        try:
            page = fetch_page(url)
        except urllib.error.HTTPError as exc:
            print(f"{'HTTP ' + str(exc.code):<14}{'-':<12}{slug}")
            if exc.code in (403, 429):
                print("The site is refusing requests. Stopping (rule R7).")
                break
            continue
        except (urllib.error.URLError, OSError) as exc:
            print(f"{'NETWORK-ERROR':<14}{'-':<12}{slug}  {exc}")
            continue

        iso, meta = parse_last_updated(page)
        extra = f"   (meta modified: {meta})" if meta else ""
        if iso is None:
            print(f"{'NOT-FOUND':<14}{'-':<12}{slug}{extra}")
        elif not plausible(iso):
            print(f"{'IMPLAUSIBLE':<14}{iso:<12}{slug}{extra}")
        elif typed:
            word = "agrees" if typed == iso else "DIFFERS"
            suffix = "" if typed == iso else f"   (you typed {typed})"
            print(f"{word:<14}{iso:<12}{slug}{suffix}{extra}")
        else:
            row["published_or_reviewed"] = iso
            filled += 1
            print(f"{'filled':<14}{iso:<12}{slug}{extra}")
        if index < len(rows) - 1:
            pause(DELAY_SECONDS)

    with open(output_csv, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    empty = sum(1 for r in rows if not r["published_or_reviewed"].strip())
    print(f"\nFilled {filled} dates. {empty} rows still have no date. Written to {output_csv}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: py fetch_last_updated.py medlineplus_selection.csv "
                 "medlineplus_selection_dates.csv")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    sys.exit(main(sys.argv[1], sys.argv[2]))
