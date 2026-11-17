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
from urllib.parse import urlsplit

ROOT = pathlib.Path(__file__).resolve().parent
PAGES = ROOT / "pages"
ALLOWED_HOSTS = ("www.nfl.com", "nfl.com", "github.com", "sassnarep3-star.github.io", "ncpgambling.org", "www.ncpgambling.org")

errors = []


def scan(path):
    text = path.read_text(encoding="utf-8")
    # Resolve local links and assets relative to the document that contains them.
    # This covers links from pages/*.html to ../assets/* as well as page-to-page
    # navigation; checking only filenames in PAGES falsely rejects valid assets.
    for m in re.finditer(r'(?:href|src)="([^"]+)"', text):
        value = html.unescape(m.group(1))
        parts = urlsplit(value)
        if parts.scheme or parts.netloc or value.startswith(("#", "mailto:")):
            continue
        if not parts.path:
            continue
        target = (path.parent / parts.path).resolve()
        root = ROOT.resolve()
        if root not in target.parents and target != root:
            errors.append("%s: local link escapes site root -> %s" % (path.name, value))
            continue
        if not target.exists() and not target.suffix:
            target = target.with_suffix(".html")
        if not target.exists():
            errors.append("%s: broken local link -> %s" % (path.name, value))
    # Every outgoing link (including protocol-relative and plain-http forms)
    # must use HTTPS and an approved source host.
    for m in re.finditer(r'href="([^"]+)"', text):
        u = html.unescape(m.group(1))
        parts = urlsplit(u)
        if u.startswith(("#", "mailto:")) or not (parts.scheme or parts.netloc):
            continue
        host = parts.hostname
        if parts.scheme != "https":
            errors.append("%s: outgoing link is not https (%s)" % (path.name, u))
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
    for p in sorted(PAGES.glob("*.html")):
        scan(p)
    if errors:
        print("VERIFY FAILED (%d errors):" % len(errors))
        for err in errors:
            print("  -", err)
        sys.exit(1)
    print("verify OK: %d pages, 0 broken links, 0 disallowed hosts, 0 unsourced rows" %
          len(list(PAGES.glob("*.html"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
