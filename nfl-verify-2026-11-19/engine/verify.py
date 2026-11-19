#!/usr/bin/env python3
"""Verify the nfl-verify-2026-11-19 site.

Checks:
  G1  every expected page exists
  G2  every <tbody> row carries at least one https source link
  G3  every internal href/src resolves to a file in the namespace
  G4  no localhost / 127.0.0.1 / preview references
  G5  no leftover {placeholders} or conflict markers
  G6  external links are https and on the official NFL allowlist
  G7  determinism: a rebuild is byte-identical to the committed output
Exit non-zero on any failure.
"""
import os
import re
import sys
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
PAGES = os.path.join(ROOT, "pages")
ASSETS = os.path.join(ROOT, "assets")

PAGES_EXPECTED = [
    "index.html",
    "pages/requirements.html",
    "pages/verification.html",
    "pages/standings.html",
    "pages/schedule.html",
    "pages/injuries.html",
    "pages/transactions.html",
    "pages/questions.html",
    "pages/repo-review.html",
    "pages/suggestions.html",
    "pages/flagged.html",
    "pages/sources.html",
]

ALLOWED_HOSTS = ("www.nfl.com", "nfl.com")

failures = []
passes = []


def ok(msg):
    passes.append(msg)


def fail(msg):
    failures.append(msg)


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


# G1 page existence
for p in PAGES_EXPECTED:
    if os.path.exists(os.path.join(ROOT, p)):
        ok("G1 page exists: %s" % p)
    else:
        fail("G1 missing page: %s" % p)

# G2/G3/G4/G5/G6 across all pages
href_re = re.compile(r'(?:href|src)="([^"]+)"')
row_re = re.compile(r"<tr>(.*?)</tr>", re.S)
link_re = re.compile(r'href="(https?://[^"]+)"')

all_html = {}
for p in PAGES_EXPECTED:
    path = os.path.join(ROOT, p)
    if not os.path.exists(path):
        continue
    txt = read(p)
    all_html[p] = txt
    # G4 localhost
    if re.search(r"(localhost|127\.0\.0\.1|0\.0\.0\.0)", txt):
        fail("G4 localhost reference in %s" % p)
    else:
        ok("G4 no localhost in %s" % p)
    # G5 placeholders / conflict markers
    if re.search(r"\{[a-zA-Z_]+\}", txt) or "<<<<<<<" in txt or ">>>>>>>" in txt or "=======" in txt:
        fail("G5 placeholder/conflict marker in %s" % p)
    else:
        ok("G5 no placeholder/conflict marker in %s" % p)
    # G2 row source links
    rows = row_re.findall(txt)
    rows = [r for r in rows if "<td" in r]
    unsourced = 0
    for r in rows:
        if not link_re.search(r):
            unsourced += 1
    if unsourced == 0:
        ok("G2 all %d data rows in %s carry an https source link" % (len(rows), p))
    else:
        fail("G2 %d rows in %s without an https source link" % (unsourced, p))
    # G3 internal links resolve + G6 external https/allowlist
    for m in href_re.finditer(txt):
        u = m.group(1)
        if u.startswith("http://") or (u.startswith("https://") and not u.startswith("https://")):
            fail("G6 non-https/disallowed external link in %s: %s" % (p, u))
            continue
        if u.startswith("https://"):
            host = re.match(r"https://([^/]+)", u)
            if host and host.group(1) not in ALLOWED_HOSTS and not host.group(1).endswith(".nfl.com"):
                fail("G6 external link not on NFL allowlist in %s: %s" % (p, u))
            continue
        if u.startswith("#") or u.startswith("mailto:") or u.startswith("data:") or u.startswith("javascript:"):
            continue
        # internal relative link
        target = os.path.normpath(os.path.join(os.path.dirname(path), u.split("#")[0]))
        if not os.path.exists(target):
            fail("G3 broken internal link in %s: %s" % (p, u))

if not any("G3 broken" in f for f in failures):
    ok("G3 all internal links resolve")
if not any("G6 " in f for f in failures):
    ok("G6 all external links https and on the NFL allowlist")

# G7 determinism
before = {p: read(p) for p in PAGES_EXPECTED if os.path.exists(os.path.join(ROOT, p))}
r = subprocess.run([sys.executable, os.path.join(HERE, "build.py")],
                   capture_output=True, text=True)
if r.returncode != 0:
    fail("G7 build.py failed: %s" % r.stderr[-400:])
else:
    after = {p: read(p) for p in PAGES_EXPECTED if os.path.exists(os.path.join(ROOT, p))}
    if before == after:
        ok("G7 deterministic rebuild (byte-identical)")
    else:
        diff = [p for p in before if before[p] != after.get(p)]
        fail("G7 rebuild changed files: %s" % diff)

print("PASS %d" % len(passes))
for p in passes:
    print("  ok  " + p)
if failures:
    print("\nFAIL %d" % len(failures))
    for f in failures:
        print("  FAIL " + f)
    sys.exit(1)
print("\nALL CHECKS PASS")
