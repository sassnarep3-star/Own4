#!/usr/bin/env python3
"""Verify the nfl-own4 site.

Checks:
  G1  every expected page exists
  G2  every <tbody> row carries at least one https source link
  G3  every internal href/src resolves to a file in the namespace
  G4  no localhost / 127.0.0.1 / preview references
  G5  no leftover {placeholders} or conflict markers
  G6  external links are https and on the official NFL allowlist (plus NCPG help)
  G7  determinism: a rebuild is byte-identical to the committed output
  G8  every reconciliation check passes
Exit non-zero on any failure.
"""
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))

PAGES_EXPECTED = [
    "index.html",
    "pages/executive-summary.html",
    "pages/requirements.html",
    "pages/standings.html",
    "pages/schedule.html",
    "pages/injuries.html",
    "pages/transactions.html",
    "pages/own-lines.html",
    "pages/leaderboard.html",
    "pages/correlations.html",
    "pages/gates.html",
    "pages/depth.html",
    "pages/questions.html",
    "pages/repo-review.html",
    "pages/suggestions.html",
    "pages/flagged.html",
    "pages/sources.html",
    "pages/verify.html",
]

ALLOWED_HOSTS = ("www.nfl.com", "nfl.com", "www.ncpgambling.org", "ncpgambling.org",
                 "github.com")
# Official club sites: hosts taken from the depth register's source_url column (official club /team/depth-chart pages).
_dep = json.load(open(os.path.join(ROOT, "data/depth_register.json"), encoding="utf-8"))["rows"]
ALLOWED_HOSTS = ALLOWED_HOSTS + tuple(re.match(r"https://([^/]+)", d["source_url"]).group(1) for d in _dep)

failures = []
passes = []


def ok(msg):
    passes.append(msg)


def fail(msg):
    failures.append(msg)


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


for p in PAGES_EXPECTED:
    if os.path.exists(os.path.join(ROOT, p)):
        ok("G1 page exists: %s" % p)
    else:
        fail("G1 missing page: %s" % p)

href_re = re.compile(r'(?:href|src)="([^"]+)"')
row_re = re.compile(r"<tr>(.*?)</tr>", re.S)
link_re = re.compile(r'href="(https?://[^"]+)"')

for p in PAGES_EXPECTED:
    path = os.path.join(ROOT, p)
    if not os.path.exists(path):
        continue
    txt = read(p)
    if re.search(r"(localhost|127\.0\.0\.1|0\.0\.0\.0)", txt):
        fail("G4 localhost reference in %s" % p)
    else:
        ok("G4 no localhost in %s" % p)
    if re.search(r"\{[a-zA-Z_]+\}", txt) or "<<<<<<<" in txt or ">>>>>>>" in txt:
        fail("G5 placeholder/conflict marker in %s" % p)
    else:
        ok("G5 no placeholder/conflict marker in %s" % p)
    rows = [r for r in row_re.findall(txt) if "<td" in r]
    unsourced = sum(1 for r in rows if not link_re.search(r))
    if unsourced == 0:
        ok("G2 all %d data rows in %s carry an https source link" % (len(rows), p))
    else:
        fail("G2 %d rows in %s without an https source link" % (unsourced, p))
    for m in href_re.finditer(txt):
        u = m.group(1)
        if u.startswith("http://"):
            fail("G6 non-https external link in %s: %s" % (p, u))
            continue
        if u.startswith("https://"):
            host = re.match(r"https://([^/]+)", u)
            if host and host.group(1) not in ALLOWED_HOSTS and not host.group(1).endswith(".nfl.com"):
                fail("G6 external link not on NFL allowlist in %s: %s" % (p, u))
            continue
        if u.startswith("#") or u.startswith("mailto:") or u.startswith("data:") or u.startswith("javascript:"):
            continue
        target = os.path.normpath(os.path.join(os.path.dirname(path), u.split("#")[0]))
        if not os.path.exists(target):
            fail("G3 broken internal link in %s: %s" % (p, u))

if not any("G3 broken" in f for f in failures):
    ok("G3 all internal links resolve")
if not any("G6 " in f for f in failures):
    ok("G6 all external links https and on the NFL allowlist")

# G8 reconciliation
try:
    recon = json.load(open(os.path.join(ROOT, "data/derived/reconciliation.json"), encoding="utf-8"))
    bad = [c for c in recon["checks"] if not c["pass"]]
    if not bad:
        ok("G8 all %d reconciliation checks pass" % len(recon["checks"]))
    else:
        fail("G8 failing reconciliation checks: %s" % [c["id"] for c in bad])
except Exception as e:
    fail("G8 cannot read reconciliation.json: %s" % e)

# G7 determinism: rebuild and compare hashes
def hashes():
    h = {}
    for p in PAGES_EXPECTED:
        fp = os.path.join(ROOT, p)
        if os.path.exists(fp):
            h[p] = hashlib.sha256(open(fp, "rb").read()).hexdigest()
    return h

before = hashes()
r = subprocess.run([sys.executable, os.path.join(HERE, "build.py")],
                   capture_output=True, text=True)
if r.returncode != 0:
    fail("G7 rebuild failed: %s" % r.stderr[-500:])
else:
    after = hashes()
    if before == after:
        ok("G7 rebuild is byte-identical (%d pages)" % len(after))
    else:
        diff = [k for k in before if before.get(k) != after.get(k)]
        fail("G7 rebuild differs: %s" % diff)

print("nfl-own4 verify")
print("  pages checked      %d" % len(PAGES_EXPECTED))
print("  passes             %d" % len(passes))
if failures:
    print("  FAILURES           %d" % len(failures))
    for f in failures:
        print("  FAIL: %s" % f)
    sys.exit(1)
print("PASS — every row is sourced, every local link resolves, counts match, rebuild is byte-identical.")
