#!/usr/bin/env python3
"""Add NHS pages outside /pregnancy/ that saved pregnancy pages link to.

    py crawl_nhs_extra.py

Lists links (from saved files, no network), then fetches them politely using the
same rules as crawl_nhs.py (robots.txt, 2 s delay, stop if blocked). Resumable.
"""
import re
import sys
import time
from datetime import date
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

import crawl_nhs as c

ALLOWED = {
    "conditions": "COND",
    "tests-and-treatments": "TESTS",
    "baby": "BABY",
    "vaccinations": "VACC",
}
NEEDS_PREGNANCY_WORD = {"conditions", "tests-and-treatments", "vaccinations"}
MIN_MENTIONS = 3
c.HUBS.update(ALLOWED)


def norm2(href, base):
    parts = urlsplit(urljoin(base, href))
    if parts.netloc != "www.nhs.uk" or parts.scheme not in ("http", "https"):
        return None
    segments = [s for s in parts.path.split("/") if s]
    if len(segments) < 2 or segments[0] not in ALLOWED or "." in segments[-1]:
        return None
    return c.BASE + "/" + "/".join(segments) + "/"


def collect(cat):
    sources = [
        c.RAW / f"{row['doc_id']}.html"
        for row in cat.values()
        if row["url"].startswith(c.BASE + "/pregnancy/") and row["status"] == "fetched"
    ]
    sources += list((c.RAW / "hubs").glob("*.html"))
    added = 0
    for path in sources:
        if not path.exists():
            continue
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
        main = soup.find("main")
        for anchor in (main.find_all("a", href=True) if main else []):
            link = norm2(anchor["href"], c.BASE + "/pregnancy/")
            if link and link not in cat:
                row = c.new_row(link, "extra")
                row["hub"] = urlsplit(link).path.strip("/").split("/")[0]
                row["status"] = "extra_listed"
                cat[link] = row
                added += 1
    return added


def run():
    c.setup_robots()
    cat = c.load_catalog()
    if not cat:
        sys.exit("nhs_pages.csv not found. Run crawl_nhs.py first.")
    added = collect(cat)
    c.assign_ids(cat)
    c.save_catalog(cat)
    todo = sorted(u for u, r in cat.items() if r["status"] in ("extra_listed", "extra_error"))
    per_hub = {}
    for url in todo:
        per_hub[cat[url]["hub"]] = per_hub.get(cat[url]["hub"], 0) + 1
    print(f"New links listed: {added}.  To fetch now: {len(todo)}  {per_hub}")

    errors = 0
    for url in todo:
        row = cat[url]
        try:
            final, html = c.get(url)
        except c.Blocked as exc:
            print(f"STOPPED: {exc}")
            break
        except Exception as exc:
            row.update(status="extra_error", note=str(exc)[:80])
            c.save_catalog(cat)
            errors += 1
            print(f"  ERROR {row['doc_id']}: {exc}")
            if errors >= 3:
                print("STOPPED: 3 errors in a row.")
                break
            time.sleep(c.DELAY)
            continue
        errors = 0
        time.sleep(c.DELAY)

        final_norm = norm2(final, final)
        if final_norm is None:
            row.update(status="redirected_out", final_url=final)
            c.save_catalog(cat)
            continue
        if final_norm != url:
            row["final_url"] = final_norm
            if final_norm in cat:
                row.update(status="duplicate", note=f"same as {cat[final_norm]['doc_id']}")
                c.save_catalog(cat)
                continue

        soup = BeautifulSoup(html, "html.parser")
        main = soup.find("main")
        if main is None or main.find("h1") is None:
            row.update(status="no_main")
            c.save_catalog(cat)
            continue
        mentions = len(re.findall(r"pregnan", main.get_text(" "), re.IGNORECASE))
        if row["hub"] in NEEDS_PREGNANCY_WORD and mentions < MIN_MENTIONS:
            row.update(status="not_relevant", note=f"{mentions} mentions of pregnancy",
                       title=" ".join(main.find("h1").get_text(" ").split()))
            c.save_catalog(cat)
            continue

        (c.RAW / f"{row['doc_id']}.html").write_text(html, encoding="utf-8")
        article = main.find("article")
        body = article or main
        reviewed, due = c.read_dates(soup.get_text(" "))
        words = len(body.get_text(" ").split())
        notes = []
        if not reviewed:
            notes.append("NO_DATE")
        if article is None:
            notes.append("NO_ARTICLE")
        if words < c.SHORT_WORDS:
            notes.append("SHORT?")
        row.update(
            title=" ".join(main.find("h1").get_text(" ").split()),
            last_reviewed=reviewed, next_review_due=due,
            review_overdue=("yes" if due and due < date.today().isoformat() else "no"),
            article_words=words, h2_count=len(body.find_all("h2")),
            status="fetched" if reviewed else "no_date",
            note=" ".join(notes + [f"{mentions} pregnancy mentions"]),
        )
        c.save_catalog(cat)
        print(f"  {row['doc_id']:<18}{reviewed or 'NO DATE':<11}{words:>5} words  "
              f"{mentions:>3} mentions  {row['title'][:45]}")

    extra = [r for r in cat.values() if r["hub"] in ALLOWED]
    by_status = {}
    for row in extra:
        by_status[row["status"]] = by_status.get(row["status"], 0) + 1
    print(f"\nExtra pages by status: {by_status}")
    for status in ("fetched", "not_relevant"):
        per = {}
        for row in extra:
            if row["status"] == status:
                per[row["hub"]] = per.get(row["hub"], 0) + 1
        print(f"  {status}: {per}")
    for title, test in [
        ("No date", lambda r: r["status"] == "no_date"),
        ("No <article>", lambda r: "NO_ARTICLE" in r["note"]),
        ("Short pages", lambda r: "SHORT?" in r["note"]),
        ("Review overdue", lambda r: r["review_overdue"] == "yes"),
    ]:
        hits = [r for r in extra if test(r)]
        print(f"\n{title}: {len(hits)}")
        for row in hits[:15]:
            print(f"   {row['doc_id']}  {row['url']}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    run()