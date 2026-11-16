#!/usr/bin/env python3
"""Check every MedlinePlus file in clean/ against its LIVE page.

Usage:
    py verify_against_live.py alovia-knowledge-base

For each file whose front matter has source_org "MedlinePlus ...", it fetches the
page named in the file's url, then checks that every line of the file's text
(paragraph, heading, list item) appears in the visible text of the live page.
Spaces and line breaks are ignored, so link boundaries do not matter.

Lines that are NOT found are printed. Typical causes: the live page was updated
since the XML snapshot, or the XML carries a stale link label (as happened with
the Postpartum Depression bullet). The published page is the authority.

Politeness (rule R7): reads robots.txt first, one plain GET per page, 2 seconds
apart, identifies itself, stops if the site refuses requests. It only READS your
files and never changes them.

Exit code is 1 if any file has a line that was not found, or a page could not
be checked.
"""
import html
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.robotparser import RobotFileParser

ROBOTS_URL = "https://medlineplus.gov/robots.txt"
USER_AGENT = "AloviaKnowledgeBase/1.0 (student capstone project; polite, 1 request per 2 s)"
DELAY_SECONDS = 2
FRONT_RE = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n(.*))?\Z", re.DOTALL)


def visible_text(page):
    page = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", page)
    page = re.sub(r"<[^>]+>", " ", page)
    return html.unescape(page)


def squash(text):
    """Remove all whitespace so tag boundaries and line breaks do not matter."""
    return re.sub(r"\s+", "", text)


def body_lines(body):
    """Text lines of a converted file: markdown markers removed, title line skipped."""
    lines = []
    for line in body.splitlines():
        if line.startswith("# "):
            continue
        line = re.sub(r"^[ ]*(## |- |\d+\. )", "", line)
        line = line.replace("**", "").strip()
        if line:
            lines.append(line)
    return lines


def read_file(path):
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    match = FRONT_RE.match(text)
    if not match:
        return None, None, None
    front, body = match.group(1), (match.group(2) or "").strip()
    url = re.search(r'(?m)^url:\s*"?([^"\n]+)"?\s*$', front)
    org = re.search(r'(?m)^source_org:\s*"?([^"\n]+)"?\s*$', front)
    return (url.group(1).strip() if url else None,
            org.group(1).strip() if org else "", body)


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def load_robots():
    parser = RobotFileParser()
    parser.set_url(ROBOTS_URL)
    parser.read()
    return parser


def main(root, fetch_page=fetch, robots=None, pause=time.sleep):
    files = sorted((Path(root) / "clean").rglob("*.md"))
    targets = []
    for path in files:
        url, org, body = read_file(path)
        if url and org.startswith("MedlinePlus"):
            targets.append((path, url, body))
    if not targets:
        print("No MedlinePlus files found under clean/.")
        return 1

    if robots is None:
        try:
            robots = load_robots()
        except (urllib.error.URLError, OSError) as exc:
            sys.exit(f"Could not read robots.txt ({exc}). Nothing was fetched.")

    clean = problem = 0
    for index, (path, url, body) in enumerate(targets):
        name = path.stem
        if not robots.can_fetch(USER_AGENT, url):
            print(f"ROBOTS-BLOCK  {name}  {url}")
            problem += 1
            continue
        try:
            page = fetch_page(url)
        except urllib.error.HTTPError as exc:
            print(f"HTTP {exc.code}      {name}  {url}")
            problem += 1
            if exc.code in (403, 429):
                print("The site is refusing requests. Stopping (rule R7).")
                break
            continue
        except (urllib.error.URLError, OSError) as exc:
            print(f"NETWORK-ERROR {name}  {exc}")
            problem += 1
            continue

        page_text = squash(visible_text(page))
        lines = body_lines(body)
        missing = [ln for ln in lines if squash(ln) not in page_text]
        if missing:
            problem += 1
            print(f"DIFFERS       {name}  ({len(missing)} of {len(lines)} lines not found)  {url}")
            for line in missing:
                clipped = line if len(line) <= 200 else line[:200] + " ..."
                print(f"      - {clipped}")
        else:
            clean += 1
            print(f"OK            {name}  ({len(lines)} lines all found)")
        if index < len(targets) - 1:
            pause(DELAY_SECONDS)

    print(f"\n{clean} file(s) fully matched, {problem} need attention, {len(targets)} checked.")
    return 1 if problem else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: py verify_against_live.py alovia-knowledge-base")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    sys.exit(main(sys.argv[1]))
