"""T09 — Build check: no broken links, and every table row has an official source link.

Also enforces the project's verification rule: any <tr> containing data cells must contain at
least one anchor to an allowlisted official host. Exits non-zero on any failure.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, read_json  # noqa: E402

ALLOW = set(read_json(ROOT / "data" / "sources.json")["official_host_allowlist"])
HTML_FILES = [ROOT / "index.html"] + sorted((ROOT / "pages").glob("*.html"))
HREF = re.compile(r'href="([^"]+)"')
TR = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.S | re.I)
TD = re.compile(r"<td\b", re.I)
ANCHOR = re.compile(r'href="(https?://[^"]+)"')
SRC_ATTR = re.compile(r'(?:src|href)="([^"]+)"')


def host_of(url):
    m = re.match(r"https?://([^/]+)", url)
    return (m.group(1).lower() if m else "")


def is_official(url):
    h = host_of(url)
    return any(h == a or h.endswith("." + a) for a in ALLOW)


errors = []
warnings = []
checked_links = 0
checked_rows = 0

for f in HTML_FILES:
    if not f.exists():
        errors.append(f"missing page: {f}")
        continue
    text = f.read_text(encoding="utf-8")
    # internal links / asset references
    for url in SRC_ATTR.findall(text):
        if url.startswith(("http://", "https://", "mailto:", "#")):
            continue
        checked_links += 1
        target = (f.parent / url.split("#")[0].split("?")[0]).resolve()
        if not target.exists():
            errors.append(f"{f.relative_to(ROOT)}: broken local link '{url}' -> {target}")
    for url in HREF.findall(text):
        if url == "" or url == "#":
            errors.append(f"{f.relative_to(ROOT)}: empty or placeholder href")
        if url.startswith("http://") and "nba.com" not in url and "github.com" not in url:
            warnings.append(f"{f.relative_to(ROOT)}: non-https external link {url}")
    # every data row must have official source link
    for m in TR.finditer(text):
        block = m.group(1)
        if not TD.search(block):
            continue  # header row
        checked_rows += 1
        urls = ANCHOR.findall(block)
        if not any(is_official(u) for u in urls):
            snippet = re.sub(r"<[^>]+>", " ", block)[:120].strip()
            errors.append(f"{f.relative_to(ROOT)}: table row without official source: '{snippet}'")

# structural checks
for p in ("assets/css/style.css", "assets/js/app.js", "site-data/site.json", ".nojekyll"):
    if not (ROOT / p).exists():
        errors.append(f"missing build artifact: {p}")

nav_paths = [it["path"] for g in read_json(ROOT / "site-data" / "site.json")["nav"] for it in g["items"]]
for p in nav_paths:
    if not (ROOT / p).exists():
        errors.append(f"nav points to missing page: {p}")

print(f"checked {len(HTML_FILES)} HTML pages, {checked_links} local links, {checked_rows} data rows")
print(f"errors={len(errors)} warnings={len(warnings)}")
for e in errors[:40]:
    print("  ERROR", e)
for w in warnings[:10]:
    print("  WARN ", w)
sys.exit(1 if errors else 0)
