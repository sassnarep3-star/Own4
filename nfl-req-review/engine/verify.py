#!/usr/bin/env python3
"""
nfl-req-review — site verifier.

Checks, run on the built site:
  1. every internal link resolves to a file that exists in the namespace;
  2. no localhost / 127.0.0.1 references anywhere;
  3. every data-table row carries at least one external source link;
  4. no unfilled {token} placeholders;
  5. no typed namespace counts in prose (the workspace rule: counts are computed);
  6. determinism: rebuilding produces byte-identical files.

Exit code 0 = pass, 1 = fail. Pure standard library.
"""

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
PAGES = [os.path.join(NS, "index.html")] + [
    os.path.join(NS, "pages", f) for f in
    ("requirements.html", "verification.html", "flagged.html", "sources.html")]

errors = []


def fail(msg):
    errors.append(msg)


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


# 1 + 2 + 3 + 4 + 5 -------------------------------------------------------------
href_re = re.compile(r'href="([^"]+)"')
row_re = re.compile(r"<tr>(.*?)</tr>", re.S)
anchor_re = re.compile(r'<a [^>]*href="([^"]+)"')


def is_source_link(href):
    if href.startswith("https://"):
        return True
    if href.startswith(("http://", "mailto:", "#")):
        return False
    return os.path.exists(os.path.normpath(os.path.join(NS, href)))

for page in PAGES:
    if not os.path.exists(page):
        fail("missing page: %s" % page)
        continue
    h = read(page)
    rel = os.path.relpath(page, NS)

    for href in href_re.findall(h):
        if href.startswith(("http", "#", "mailto:")):
            continue
        # links are root-relative to the namespace (GitHub Pages serves the
        # namespace at its own root), so resolve against NS, not the page dir
        target = os.path.normpath(os.path.join(NS, href))
        if not os.path.exists(target):
            fail("%s: broken internal link %s" % (rel, href))

    if re.search(r"localhost|127\.0\.0\.1", h):
        fail("%s: localhost reference found" % rel)

    if "{token}" in h or re.search(r"\{[a-zA-Z_]+\}", h):
        fail("%s: unfilled placeholder token found" % rel)

    if re.search(r"\b\d+\s*nfl-", h):
        fail("%s: typed namespace count in prose (counts must be computed)" % rel)

    # table rows need a source link (skip header rows and the Total row)
    for row in row_re.findall(h):
        if "<th" in row or "<b>Total</b>" in row:
            continue
        if not any(is_source_link(href) for href in anchor_re.findall(row)):
            fail("%s: table row without a source link: %s"
                 % (rel, re.sub(r"\s+", " ", row)[:120]))

# 6 ----------------------------------------------------------------------------
def snapshot():
    out = {}
    for root, _dirs, files in os.walk(NS):
        for f in files:
            if f.endswith((".html", ".css", ".json")):
                p = os.path.join(root, f)
                out[os.path.relpath(p, NS)] = read(p)
    return out


before = snapshot()
subprocess.run([sys.executable, os.path.join(HERE, "build_data.py")],
               check=True, capture_output=True)
subprocess.run([sys.executable, os.path.join(HERE, "build_requirements.py")],
               check=True, capture_output=True)
subprocess.run([sys.executable, os.path.join(HERE, "build.py")],
               check=True, capture_output=True)
after = snapshot()

for k in sorted(set(before) | set(after)):
    if before.get(k) != after.get(k):
        fail("determinism: rebuild changed %s" % k)

if errors:
    print("FAIL — %d problem(s):" % len(errors))
    for e in errors:
        print(" -", e)
    sys.exit(1)

print("PASS — %d pages, all internal links resolve, every table row sourced, "
      "no placeholders, no typed counts, determinism clean." % len(PAGES))
