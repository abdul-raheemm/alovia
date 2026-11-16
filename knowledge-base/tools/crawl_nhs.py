#!/usr/bin/env python3
"""Map and fetch the ordinary NHS pregnancy pages (www.nhs.uk/pregnancy/).

    py crawl_nhs.py discover   fetch the index and hub pages only; list their subpages
    py crawl_nhs.py fetch      fetch every listed page, save raw HTML, read review dates

Politeness: robots.txt is checked, 2 s between requests, stops if the site blocks us.
Writes: raw/nhs/<doc_id>.html, raw/nhs/hubs/<slug>.html, nhs_pages.csv (catalogue).
"""
import csv
import re
import sys
import time
import urllib.error
import urllib.request
import urllib.robotparser
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

ROOT = Path(".")  # run from knowledge-base/ (was "alovia-knowledge-base" in the old rag/ layout)
RAW = ROOT / "raw" / "nhs"
CATALOG = Path("nhs_pages.csv")
BASE = "https://www.nhs.uk"
UA = "AloviaStudentProject/1.0 (college capstone; polite, rate-limited)"
DELAY = 2
MAX_PAGES = 400
SHORT_WORDS = 150
ROUNDUP_H2 = 5

# hub slug -> doc_id label
HUBS = {
    "trying-for-a-baby": "TRYING",
    "having-a-baby-if-you-are-lgbt-plus": "LGBT",
    "finding-out": "FINDING",
    "your-pregnancy-care": "CARE",
    "keeping-well": "WELL",
    "mental-health-in-pregnancy-and-after-the-birth": "MENTAL",
    "common-symptoms": "SYMPTOMS",
    "existing-health-conditions": "EXISTING",
    "complications": "COMPLICATIONS",
    "labour-and-birth": "LABOUR",
}
PINNED = {
    BASE + "/pregnancy/labour-and-birth/signs-that-labour-has-begun/": "NHS-LABOUR-001",
    BASE + "/pregnancy/complications/severe-vomiting/": "NHS-COMPLICATIONS-001",
    BASE + "/pregnancy/common-symptoms/indigestion-and-heartburn/": "NHS-SYMPTOMS-001",
}
DEFERRED = {
    BASE + "/pregnancy/common-symptoms/common-health-problems/":
        "roundup page; split later",
}
# NHS tools are excluded by the NHS terms of use.
EXCLUDE = {BASE + "/pregnancy/finding-out/due-date-calculator/"}
FIELDS = ["doc_id", "hub", "url", "final_url", "title", "last_reviewed",
          "next_review_due", "review_overdue", "article_words", "h2_count",
          "status", "note"]

robots = urllib.robotparser.RobotFileParser(BASE + "/robots.txt")


class Blocked(Exception):
    pass


def setup_robots():
    robots.read()
    if not robots.can_fetch(UA, BASE + "/pregnancy/"):
        sys.exit("robots.txt does not allow /pregnancy/ for us. Stopping.")


def get(url):
    if not robots.can_fetch(UA, url):
        raise Blocked(f"robots.txt disallows {url}")
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.geturl(), response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code in (403, 429):
            raise Blocked(f"HTTP {exc.code} for {url}")
        raise


def norm(href, base):
    parts = urlsplit(urljoin(base, href))
    if parts.netloc != "www.nhs.uk" or parts.scheme not in ("http", "https"):
        return None
    path = parts.path
    if not path.startswith("/pregnancy/"):
        return None
    if "." in path.rstrip("/").rsplit("/", 1)[-1]:
        return None  # a file such as .pdf
    if not path.endswith("/"):
        path += "/"
    return BASE + path


def hub_of(url):
    segments = url[len(BASE):].strip("/").split("/")
    return segments[1] if len(segments) > 1 else ""


def page_links(soup, base):
    main = soup.find("main")
    found = set()
    for anchor in (main or soup).find_all("a", href=True):
        link = norm(anchor["href"], base)
        if link:
            found.add(link)
    return found


def read_dates(text):
    out = []
    for label in ("Page last reviewed", "Next review due"):
        match = re.search(label + r":\s*(\d{1,2} \w+ \d{4})", text)
        value = ""
        if match:
            try:
                value = datetime.strptime(match.group(1), "%d %B %Y").date().isoformat()
            except ValueError:
                value = ""
        out.append(value)
    return out


def load_catalog():
    if not CATALOG.exists():
        return {}
    with open(CATALOG, encoding="utf-8", newline="") as handle:
        return {row["url"]: row for row in csv.DictReader(handle)}


def save_catalog(cat):
    with open(CATALOG, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for url in sorted(cat):
            writer.writerow(cat[url])


def new_row(url, note=""):
    row = {key: "" for key in FIELDS}
    row.update(url=url, hub=hub_of(url), doc_id=PINNED.get(url, ""),
               status="listed", note=note)
    if url in DEFERRED:
        row["status"] = "deferred"
        row["note"] = DEFERRED[url]
    return row


def assign_ids(cat):
    used = {}
    for row in cat.values():
        if row["doc_id"]:
            prefix, number = row["doc_id"].rsplit("-", 1)
            used.setdefault(prefix, set()).add(int(number))
    for url in sorted(cat):
        row = cat[url]
        if row["doc_id"]:
            continue
        prefix = "NHS-" + HUBS[row["hub"]]
        taken = used.setdefault(prefix, set())
        number = 1
        while number in taken:
            number += 1
        taken.add(number)
        row["doc_id"] = f"{prefix}-{number:03d}"


def discover():
    setup_robots()
    (RAW / "hubs").mkdir(parents=True, exist_ok=True)
    seeds = {"index": BASE + "/pregnancy/"}
    seeds.update({slug: f"{BASE}/pregnancy/{slug}/" for slug in HUBS})
    seed_urls = set(seeds.values())
    cat = load_catalog()
    unknown, excluded = set(), set()

    for slug, url in seeds.items():
        path = RAW / "hubs" / f"{slug}.html"
        try:
            if path.exists():
                html, final = path.read_text(encoding="utf-8"), url
            else:
                final, html = get(url)
                path.write_text(html, encoding="utf-8")
                time.sleep(DELAY)
        except Blocked as exc:
            sys.exit(f"STOPPED: {exc}")
        except Exception as exc:
            print(f"  FAILED {url}: {exc}")
            continue
        print(f"  read {slug}: {final}")
        for link in page_links(BeautifulSoup(html, "html.parser"), final):
            if link in seed_urls:
                continue
            if link in EXCLUDE:
                excluded.add(link)
            elif hub_of(link) in HUBS:
                cat.setdefault(link, new_row(link))
            else:
                unknown.add(link)

    assign_ids(cat)
    save_catalog(cat)
    counts = {slug: 0 for slug in HUBS}
    for row in cat.values():
        counts[row["hub"]] += 1
    print("\nPages listed per hub:")
    for slug, number in counts.items():
        print(f"  {number:>4}  {slug}")
    print(f"  {sum(counts.values()):>4}  TOTAL (saved to {CATALOG})")
    print("\nPilot pages in the map:")
    for url, doc_id in PINNED.items():
        print(f"  {'OK     ' if url in cat else 'MISSING'} {doc_id} {url}")
    print(f"\nExcluded as NHS tools: {sorted(excluded) or 'none'}")
    print(f"Links under /pregnancy/ in an unexpected hub: {sorted(unknown) or 'none'}")
    print("\nNext: py crawl_nhs.py fetch")


def fetch():
    setup_robots()
    RAW.mkdir(parents=True, exist_ok=True)
    cat = load_catalog()
    if not cat:
        sys.exit("nhs_pages.csv not found. Run: py crawl_nhs.py discover")
    todo = [url for url in sorted(cat) if cat[url]["status"] in ("listed", "error")]
    errors, fetched = 0, 0

    while todo:
        if len(cat) > MAX_PAGES:
            print(f"STOPPED: more than {MAX_PAGES} pages listed; check the map.")
            break
        url = todo.pop(0)
        row = cat[url]
        path = RAW / f"{row['doc_id']}.html"
        if path.exists():
            html, final = path.read_text(encoding="utf-8"), url
        else:
            try:
                final, html = get(url)
            except Blocked as exc:
                print(f"STOPPED: {exc}")
                break
            except Exception as exc:
                row.update(status="error", note=str(exc)[:80])
                errors += 1
                save_catalog(cat)
                print(f"  ERROR {row['doc_id']}: {exc}")
                if errors >= 3:
                    print("STOPPED: 3 errors in a row.")
                    break
                time.sleep(DELAY)
                continue
            errors = 0
            time.sleep(DELAY)

        final_norm = norm(final, final)
        if final_norm is None:
            row.update(status="redirected_out", final_url=final)
            save_catalog(cat)
            continue
        if final_norm != url:
            row["final_url"] = final_norm
            if final_norm in cat:
                row.update(status="duplicate", note=f"same as {cat[final_norm]['doc_id']}")
                save_catalog(cat)
                continue

        soup = BeautifulSoup(html, "html.parser")
        main = soup.find("main")
        if main is None or main.find("h1") is None:
            row.update(status="no_main")
            save_catalog(cat)
            continue
        if not path.exists():
            path.write_text(html, encoding="utf-8")

        article = main.find("article")
        reviewed, due = read_dates(soup.get_text(" "))
        words = len(article.get_text(" ").split()) if article else 0
        notes = []
        if not reviewed:
            notes.append("NO_DATE")
        if words < SHORT_WORDS:
            notes.append("SHORT?")
        h2s = len(article.find_all("h2")) if article else 0
        if h2s >= ROUNDUP_H2:
            notes.append("ROUNDUP?")
        row.update(
            title=" ".join(main.find("h1").get_text(" ").split()),
            last_reviewed=reviewed, next_review_due=due,
            review_overdue=("yes" if due and due < date.today().isoformat() else "no"),
            article_words=words, h2_count=h2s,
            status="fetched" if reviewed else "no_date",
            note=" ".join(notes),
        )
        fetched += 1
        print(f"  {row['doc_id']:<26} {reviewed or 'NO DATE':<11} {words:>5} words")

        for link in page_links(soup, final):
            if link in cat or link in EXCLUDE or link in {BASE + "/pregnancy/"}:
                continue
            if hub_of(link) in HUBS and link != f"{BASE}/pregnancy/{hub_of(link)}/":
                cat[link] = new_row(link, "new_in_fetch")
                assign_ids(cat)
                todo.append(link)
        save_catalog(cat)

    rows = list(cat.values())
    by_status = {}
    for row in rows:
        by_status[row["status"]] = by_status.get(row["status"], 0) + 1
    print(f"\nFetched this run: {fetched}.  Status counts: {by_status}")
    for title, test in [
        ("No review date", lambda r: r["status"] == "no_date"),
        ("Review overdue", lambda r: r["review_overdue"] == "yes"),
        ("Short pages (hub or stub?)", lambda r: "SHORT?" in r["note"]),
        ("Roundups (split needed?)", lambda r: "ROUNDUP?" in r["note"]),
        ("Found only during fetch", lambda r: "new_in_fetch" in r["note"]),
    ]:
        hits = [r for r in rows if test(r)]
        print(f"\n{title}: {len(hits)}")
        for r in hits[:40]:
            print(f"   {r['doc_id']}  {r['url']}")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("discover", "fetch"):
        sys.exit("Usage: py crawl_nhs.py discover | fetch")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    {"discover": discover, "fetch": fetch}[sys.argv[1]]()