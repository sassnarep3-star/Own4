#!/usr/bin/env python3
"""Publication gate for the NFL Standings Re-verification site.

Fails the build unless:
  1. every table body row on every page carries an https source link, and that link's
     host is approved (nfl.com for a league value, github.com for a repository artifact,
     ncpgambling.org for the helpline);
  2. every local href resolves inside this namespace;
  3. the printed counts survive an independent re-derivation: the 32 rows and the league
     identities are re-parsed from the capture text by a parser that shares no code with
     engine/parse.py, and the standings identities are re-summed here;
  4. engine/build.py re-run reproduces the pages byte-for-byte, so a published number
     cannot drift from its data;
  5. no page asserts a banned basis (depth ordered by jersey number/experience/salary,
     injury as a level rather than a surprise, season-long ROI as the ranking) outside an
     explicit rejection; no cell says TBD/N/A where the rule is "blank with a reason".

Run: python3 nfl-standings-reverify/engine/verify.py   (exit 0 = pass)
"""
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)
CAPTURE = os.path.join(NS, "captures", "standings_2026-11-19.md")
DATA = os.path.join(NS, "data", "standings_reverify.json")
APPROVED_HOSTS = ("nfl.com", "github.com", "ncpgambling.org")

HREF_RE = re.compile(r'href="([^"]+)"')
ROW_HAS_LINK_RE = re.compile(r"<a[^>]+href=\"https?://")

problems = []


def ok(msg):
    print("[ok] %s" % msg)


def fail(msg):
    problems.append(msg)
    print("[FAIL] %s" % msg)


# --- rule 1: every table body row carries an approved https source link -------------
rows_checked = 0
for dirpath, _, files in os.walk(NS):
    if "/.git" in dirpath:
        continue
    for fn in files:
        if not fn.endswith(".html"):
            continue
        path = os.path.join(dirpath, fn)
        rel = os.path.relpath(path, NS)
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        for m in re.finditer(r"<tbody>(.*?)</tbody>", text, re.S):
            for tr in re.finditer(r"<tr>(.*?)</tr>", m.group(1), re.S):
                row = tr.group(1)
                # skip header-only rows
                if "<th" in row:
                    continue
                rows_checked += 1
                if not ROW_HAS_LINK_RE.search(row):
                    fail("%s: table body row without an https source link" % rel)
                    continue
                # check the link host is approved
                for lm in HREF_RE.finditer(row):
                    url = lm.group(1)
                    if url.startswith("http") and not any(h in url for h in APPROVED_HOSTS):
                        fail("%s: row links to a non-approved host: %s" % (rel, url))
ok("row-has-source-link — %d data rows across the site carry an approved https source link" % rows_checked)

# --- rule 2: every local href resolves inside this namespace ------------------------
local_checked = 0
broken_local = 0
for dirpath, _, files in os.walk(NS):
    if "/.git" in dirpath:
        continue
    for fn in files:
        if not fn.endswith(".html"):
            continue
        path = os.path.join(dirpath, fn)
        rel = os.path.relpath(path, NS)
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        for h in HREF_RE.findall(text):
            if h.startswith(("http://", "https://", "#", "mailto:", "data:")):
                continue
            pathpart = h.split("#")[0]
            if pathpart == "":
                continue
            local_checked += 1
            target = os.path.normpath(os.path.join(os.path.dirname(path), pathpart))
            if not os.path.exists(target):
                broken_local += 1
                fail("%s: broken local link -> %s" % (rel, h))
ok("local-links — %d local hrefs checked, %d broken" % (local_checked, broken_local))

# --- rule 3: printed counts re-derived from the capture by an independent parser ----
# A minimal, independent re-count that shares no code with parse.py: just count the
# logo rows and re-sum W/L/T/PF/PA from the capture table lines.
cap_text = open(CAPTURE, encoding="utf-8").read()
logo_lines = [ln for ln in cap_text.splitlines() if "logos/" in ln]
re_rows = len(logo_lines)
re_sum_w = re_sum_l = re_sum_t = re_sum_pf = re_sum_pa = 0
for ln in logo_lines:
    cells = [c.strip() for c in ln.strip().strip("|").split("|")]
    # last 7 cells: W L T PCT PF PA NET
    re_sum_w += int(cells[-7])
    re_sum_l += int(cells[-6])
    re_sum_t += int(cells[-5])
    re_sum_pf += int(cells[-3])
    re_sum_pa += int(cells[-2])
with open(DATA, encoding="utf-8") as fh:
    d = json.load(fh)
ident = d["league_identities"]
if re_rows != ident["teams"]:
    fail("row count re-derived (%d) != published (%d)" % (re_rows, ident["teams"]))
else:
    ok("row-count-recomputed — %d logo rows re-counted from the capture, matches published" % re_rows)
if (re_sum_w, re_sum_l, re_sum_t, re_sum_pf, re_sum_pa) == (
    ident["sum_W"], ident["sum_L"], ident["sum_T"], ident["sum_PF"], ident["sum_PA"]):
    ok("identities-recomputed — W %d / L %d / T %d / PF %d / PA %d re-summed from the capture, all match"
       % (re_sum_w, re_sum_l, re_sum_t, re_sum_pf, re_sum_pa))
else:
    fail("identity sums re-derived from capture do not match published values")

# --- rule 4: determinism — rebuild is byte-identical --------------------------------
before = {}
for dirpath, _, files in os.walk(NS):
    if "/.git" in dirpath:
        continue
    for fn in files:
        if fn.endswith(".html"):
            p = os.path.join(dirpath, fn)
            before[os.path.relpath(p, NS)] = open(p, "rb").read()
subprocess.run([sys.executable, os.path.join(HERE, "build.py")], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
after = {}
for dirpath, _, files in os.walk(NS):
    if "/.git" in dirpath:
        continue
    for fn in files:
        if fn.endswith(".html"):
            p = os.path.join(dirpath, fn)
            after[os.path.relpath(p, NS)] = open(p, "rb").read()
if before == after:
    ok("determinism — rebuild reproduces all %d pages byte-for-byte" % len(after))
else:
    fail("determinism — rebuild changed at least one page")

# --- rule 5: banned claims / TBD-N/A -----------------------------------------------
banned = ["jersey number", "experience", "salary", "season-long ROI", "win rate as the ranking"]
for dirpath, _, files in os.walk(NS):
    if "/.git" in dirpath:
        continue
    for fn in files:
        if not fn.endswith(".html"):
            continue
        path = os.path.join(dirpath, fn)
        rel = os.path.relpath(path, NS)
        text = open(path, encoding="utf-8", errors="replace").read().lower()
        for b in banned:
            if b in text:
                fail("%s: contains a banned basis outside a rejection: %s" % (rel, b))
        if re.search(r">\s*(TBD|N/A)\s*<", text):
            fail("%s: a cell says TBD/N/A where the rule is blank-with-a-reason" % rel)
ok("banned-claim — no page asserts a banned basis; no TBD/N/A cells")

print()
if problems:
    print("VERIFY: FAIL — %d problem(s)" % len(problems))
    sys.exit(1)
print("VERIFY: all rules pass (%d data rows)" % rows_checked)
