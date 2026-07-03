#!/usr/bin/env python3
"""
Self-check: verify all <img src> and <a href> in generated HTML resolve to
existing local files. Run from the repository root: python3 tools/check.py
"""

import os
import re
import sys
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parent.parent

# Files to ignore for existence (external URLs, anchors)
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "#", "//")


class RefCollector(HTMLParser):
    def __init__(self, page_path: Path):
        super().__init__()
        self.page = page_path
        self.issues = []

    def resolve(self, href: str) -> Path:
        """Resolve href relative to the page's directory."""
        if href.startswith("/"):
            return REPO / href.lstrip("/")
        return (self.page.parent / href).resolve()

    def check(self, attr_name: str, val: str):
        if not val:
            return
        if any(val.startswith(p) for p in EXTERNAL_PREFIXES):
            return
        target = self.resolve(val)
        if not target.exists():
            rel_page = self.page.relative_to(REPO)
            rel_target = val
            self.issues.append(f"  [{rel_page}] {attr_name}=\"{rel_target}\" → NOT FOUND")

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "img":
            self.check("src", attrs.get("src", ""))
        elif tag == "a":
            href = attrs.get("href", "")
            # Only check if it looks like a local path (no query params for anchors)
            if href and not any(href.startswith(p) for p in EXTERNAL_PREFIXES):
                # Strip anchor fragment
                href_clean = href.split("#")[0]
                if href_clean:
                    self.check("href", href_clean)
        elif tag == "link":
            rel = attrs.get("rel", "")
            if "stylesheet" in rel or "icon" in rel:
                self.check("href", attrs.get("href", ""))
        elif tag == "script":
            self.check("src", attrs.get("src", ""))


def check_file(path: Path) -> list:
    content = path.read_text(encoding="utf-8", errors="replace")
    collector = RefCollector(path)
    collector.feed(content)
    return collector.issues


def main():
    html_files = list(REPO.rglob("*.html"))
    # Exclude any node_modules or hidden dirs
    html_files = [f for f in html_files if ".git" not in str(f) and "node_modules" not in str(f)]

    all_issues = []
    for path in sorted(html_files):
        issues = check_file(path)
        all_issues.extend(issues)

    total = len(html_files)
    bad = len(set(i.split("]")[0] for i in all_issues))

    print(f"Checked {total} HTML files.")
    print(f"Pages with broken refs: {bad}")
    print(f"Total broken refs: {len(all_issues)}")

    if all_issues:
        print("\nBroken references:")
        for issue in sorted(set(all_issues)):
            print(issue)
        sys.exit(1)
    else:
        print("\nAll references OK.")


if __name__ == "__main__":
    main()
