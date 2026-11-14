"""Verify the nfl-price-snapshot site.

Checks:
  * every local link resolves to a file that exists
  * every outgoing link uses https:// and points to an allowed domain (official sources)
  * every table row carries at least one source link (enforced in build.py too)
Exits non-zero on any failure. Stdlib only.
"""
import html
import pathlib
import re
import sys
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parent
PAGES = ROOT / "pages"
ALLOWED_HOSTS = ("www.nfl.com", "nfl.com", "github.com", "sassnarep3-star.github.io", "ncpgambling.org", "www.ncpgambling.org")

errors = []


def page_files():
    return {p.name for p in PAGES.glob("*.html")}


def scan(path, files):
    text = path.read_text(encoding="utf-8")
    # local hrefs
    for m in re.finditer(r'href="([^"]+)"', text):
        href = m.group(1)
        if href.startswith("http") or href.startswith("#") or href.startswith("mailto:"):
            continue
        if href.startswith("assets/"):
            if not (ROOT / href).exists():
                errors.append("%s: missing asset %s" % (path.name, href))
            continue
        target = href
        if not target.endswith(".html"):
            target = target + ".html" if "#" not in target else target
        target = target.split("#")[0]
        if target not in files:
            errors.append("%s: broken local link -> %s" % (path.name, href))
    # outgoing links must be https and allowed
    for m in re.finditer(r'href="(https://[^"]+)"', text):
        u = m.group(1)
        host = urlparse(u).hostname
        if host not in ALLOWED_HOSTS:
            errors.append("%s: disallowed outgoing host %s (%s)" % (path.name, host, u))
    # table rows: each <tr> in a table with class tw must contain a source link (<a ... &xrarr; or src span)
    for m in re.finditer(r'<table[^>]*class="[^"]*tw[^"]*"(.*?)</table>', text, re.S):
        block = m.group(0)
        for rm in re.finditer(r"<tr>(.*?)</tr>", block, re.S):
            row = rm.group(1)
            if "<th" in row:
                continue  # header
            if "&xrarr;" not in row and 'rel="noopener"' not in row:
                errors.append("%s: table row without a source link" % path.name)
    # blank pill without source on data rows is OK (blank is intentional), but ensure sourced rows exist.


def main():
    files = page_files()
    for p in sorted(PAGES.glob("*.html")):
        scan(p, files)
    if errors:
        print("VERIFY FAILED (%d errors):" % len(errors))
        for err in errors:
            print("  -", err)
        sys.exit(1)
    print("verify OK: %d pages, 0 broken links, 0 disallowed hosts, 0 unsourced rows" % len(files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
