#!/usr/bin/env python3
"""Print the outline of <main> for the saved NHS pages (read-only, no network)."""
import re
from pathlib import Path

from bs4 import BeautifulSoup

RAW = Path("alovia-knowledge-base/raw/nhs")
LEAF = {"p", "li", "ul", "ol", "a", "strong", "em", "b", "i"}


def snippet(node, size=50):
    return " ".join(node.get_text(" ", strip=True).split())[:size]


def walk(node, depth):
    for child in node.find_all(True, recursive=False):
        if child.name in LEAF:
            continue
        classes = ".".join(child.get("class", []))
        extra = ""
        if child.name in ("section", "div", "article", "aside", "nav"):
            extra = f" [p={len(child.find_all('p'))}]"
        print(f"{'  ' * depth}{child.name}"
              f"{'.' + classes if classes else ''}{extra}: {snippet(child)}")
        walk(child, depth + 1)


def main():
    for path in sorted(RAW.glob("NHS-*.html")):
        print("=" * 70)
        print(path.name)
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
        main_tag = soup.find("main")
        walk(main_tag, 0)

        hit = main_tag.find(string=re.compile("Page last reviewed"))
        if hit:
            chain = []
            for parent in hit.parents:
                if parent.name == "main":
                    break
                classes = ".".join(parent.get("class", []))
                chain.append(parent.name + ("." + classes if classes else ""))
            print("\nreviewed-date sits in:", " < ".join(chain))


if __name__ == "__main__":
    main()