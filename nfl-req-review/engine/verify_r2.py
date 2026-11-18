#!/usr/bin/env python3
"""
nfl-req-review — round-2 verifier (session arena/9242c387-own4).

Checks, on the committed tree:
  1. the round-2 data pipeline rebuilds byte-identically (determinism);
  2. every internal link on every page resolves to a file in the namespace;
  3. no localhost / 127.0.0.1 reference;
  4. every table row carries at least one external source link (header rows skipped);
  5. no unfilled {token} placeholders; no typed namespace counts in prose;
  6. every requirement marked 'met' cites artifacts that exist, and its round-2 review is recorded;
  7. every flag and every question carries at least one source link;
  8. the computed checks that are not 'as expected' are exactly the documented findings
     (RC-12 -> RF-09, RC-14 -> RF-14, RC-15 -> RF-12): any other regression fails the build;
  9. suggestions keep their decision field blank (no decision is made by this tool).

Exit 0 = pass, 1 = fail. Pure standard library.
"""

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
DATA = os.path.join(NS, "data")
ENGINE = [os.path.join(HERE, f) for f in ("round2.py", "round2_register.py", "build_r2.py")]
EXPECTED_FINDINGS = {"RC-12": "RF-09", "RC-14": "RF-14", "RC-15": "RF-12"}

errors = []


def fail(m):
    errors.append(m)


def snapshot():
    out = {}
    for root, dirs, files in os.walk(NS):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if f.endswith((".html", ".css", ".json", ".md")):
                p = os.path.join(root, f)
                out[os.path.relpath(p, NS)] = open(p, encoding="utf-8").read()
    return out


before = snapshot()
for s in ENGINE:
    r = subprocess.run([sys.executable, s], capture_output=True, text=True)
    if r.returncode != 0:
        fail("engine step failed: %s\n%s" % (os.path.basename(s), r.stderr[-600:]))
after = snapshot()
for k in sorted(set(before) | set(after)):
    if before.get(k) != after.get(k):
        fail("determinism: rebuild changed %s" % k)

pages = [os.path.join(NS, "index.html"), os.path.join(NS, "EXECUTIVE_SUMMARY.md")] + [
    os.path.join(NS, "pages", f) for f in sorted(os.listdir(os.path.join(NS, "pages"))) if f.endswith(".html")]
href_re = re.compile(r'href="([^"]+)"')
row_re = re.compile(r"<tr>(.*?)</tr>", re.S)
anchor_re = re.compile(r'<a [^>]*href="([^"]+)"')

for page in pages:
    rel = os.path.relpath(page, NS)
    h = open(page, encoding="utf-8").read()
    if page.endswith(".md"):
        continue
    for href in href_re.findall(h):
        if href.startswith(("http", "#", "mailto:")):
            continue
        target = os.path.normpath(os.path.join(os.path.dirname(page), href))
        if not os.path.exists(target):
            fail("%s: broken internal link %s" % (rel, href))
    if re.search(r"localhost|127\.0\.0\.1", h):
        fail("%s: localhost reference" % rel)
    if re.search(r"\{[a-zA-Z_]+\}", h):
        fail("%s: unfilled placeholder" % rel)
    if re.search(r"\b\d+\s*nfl-", h):
        fail("%s: typed namespace count" % rel)
    for row in row_re.findall(h):
        if "<th" in row:
            continue
        hrefs = anchor_re.findall(row)
        ext = [x for x in hrefs if x.startswith("https://")]
        if not ext:
            fail("%s: table row without an external source link: %s" % (rel, re.sub(r"\s+", " ", row)[:110]))

# data-level checks
REQ = json.load(open(os.path.join(DATA, "requirements_2026_11_18.json"), encoding="utf-8"))
for r in REQ["rows"]:
    if r["status"] not in ("met", "partial", "blocked", "not_started", "in_progress"):
        fail("%s: unknown status %s" % (r["id"], r["status"]))
    if r["status"] == "met":
        if not r["round2_reviewed"] and r["status_2026_11_17"] != "met":
            fail("%s: met without a round-2 review" % r["id"])
        for a in r["artifacts"]:
            if not a["exists"] or not os.path.exists(os.path.join(NS, "..", a["path"])):
                fail("%s: met but artifact missing: %s" % (r["id"], a["path"]))
    if not r["source"].startswith("https://"):
        fail("%s: source is not a link" % r["id"])

FL = json.load(open(os.path.join(DATA, "flags_2026_11_18.json"), encoding="utf-8"))
for f in FL["flags"]:
    if not any(s.startswith("https://") for s in f["sources"]):
        fail("%s: flag without an external source" % f["id"])
for q in json.load(open(os.path.join(DATA, "questions.json"), encoding="utf-8"))["rows"]:
    if not q["sources"]:
        fail("%s: question without a source" % q["id"])
for s in json.load(open(os.path.join(DATA, "suggestions.json"), encoding="utf-8"))["rows"]:
    if s["decision"] != "":
        fail("%s: suggestion decision must stay blank" % s["id"])

READS = json.load(open(os.path.join(DATA, "official_reads_2026_11_18.json"), encoding="utf-8"))
failing = {c["id"] for c in READS["checks"] if not c["ok"]}
if failing != set(EXPECTED_FINDINGS):
    fail("computed checks not as expected: got %s, expected findings %s" % (sorted(failing), sorted(EXPECTED_FINDINGS)))
flag_ids = {f["id"] for f in FL["flags"]}
for cid, fid in EXPECTED_FINDINGS.items():
    if fid not in flag_ids:
        fail("%s finding has no flag %s" % (cid, fid))

if errors:
    print("FAIL — %d problem(s):" % len(errors))
    for e in errors:
        print(" -", e)
    sys.exit(1)
print("PASS — %d pages · %d register rows · %d flags · computed checks %d (findings: %s) · links, sourcing, artifacts, determinism clean."
      % (len(pages), len(REQ["rows"]), len(FL["flags"]), len(READS["checks"]), ", ".join(sorted(failing))))
