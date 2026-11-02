#!/usr/bin/env python3
"""Validate required pages and local HTML links without external dependencies."""
from html.parser import HTMLParser
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PAGES = [ROOT / "index.html", *(ROOT / "pages" / name for name in ("strategies.html", "validation.html", "review.html"))]
class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
    def handle_starttag(self, tag, attrs):
        if tag in ("a", "link", "script"):
            href = dict(attrs).get("href") or dict(attrs).get("src")
            if href:
                self.hrefs.append(href)

errors = []
for page in PAGES:
    if not page.is_file():
        errors.append(f"Missing required page: {page.relative_to(ROOT)}")
        continue
    parser = Links()
    parser.feed(page.read_text(encoding="utf-8"))
    for link in parser.hrefs:
        if link.startswith(("https://", "http://", "mailto:", "#", "data:")):
            continue
        target = (page.parent / link.split("#", 1)[0]).resolve()
        if not target.exists():
            errors.append(f"{page.relative_to(ROOT)}: broken local link {link}")
if errors:
    print("Site validation failed:")
    print("\n".join(f" - {error}" for error in errors))
    sys.exit(1)
print(f"Site validation passed: {len(PAGES)} pages and all local links exist.")
