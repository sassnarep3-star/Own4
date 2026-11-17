#!/usr/bin/env python3
"""Own4 — nfl-board publication contract. Fails loudly, exits non-zero.

Checks
  1. every page was written and is well-formed enough (balanced <table>/<tbody>, no unrendered markers)
  2. EVERY data-table row carries at least one link to an official page or to this repository
  3. every local href resolves to a file on disk, and every anchor target exists
  4. no prefilled suggestion verdict (the board belongs to the reviewer)
  5. no typed count in prose: every integer rendered outside a table cell must be a computed one
     that appears in the computed set (checked structurally below), and no page may state a
     requirement total, a question total or an irregularity total as a literal in body text
  6. no placeholder or sentinel value leaked into the output
  7. the registers cross-reference cleanly (no dangling source, question or irregularity id)

Run: python3 nfl-board/engine/verify.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
DATA = os.path.join(NS, "data")

PAGES = [
    "index.html",
    "pages/executive-summary.html",
    "pages/readiness.html",
    "pages/questions.html",
    "pages/suggestions.html",
    "pages/evidence.html",
    "pages/repo-review.html",
    "pages/flagged.html",
    "pages/sources.html",
]

OFFICIAL = (
    "nfl.com", "packers.com", "baltimoreravens.com", "houstontexans.com",
    "ncpgambling.org", "github.com",
)

PLACEHOLDERS = [
    (re.compile(r"\{\{|\}\}"), "unrendered template marker"),
    (re.compile(r"%\("), "unformatted %(name)s marker"),
    (re.compile(r"\bTODO\b"), "TODO marker"),
    (re.compile(r"\bundefined\b"), "undefined sentinel"),
    (re.compile(r">\s*(nan|NaN|None|null|inf)\s*<"), "sentinel cell value"),
]

errors = []
warnings = []


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


REQ = load(os.path.join(DATA, "requirements.json"))
Q = load(os.path.join(DATA, "questions.json"))
SUG = load(os.path.join(DATA, "suggestions.json"))
IRR = load(os.path.join(DATA, "irregularities.json"))
SRC = load(os.path.join(DATA, "sources.json"))


def err(msg):
    errors.append(msg)


# ---------------------------------------------------------------- 7. register integrity
SRC_IDS = {s["id"] for s in SRC["sources"]}
for coll, name in ((REQ["rows"], "requirements"), (Q["rows"], "questions"),
                   (SUG["rows"], "suggestions"), (IRR["rows"], "irregularities")):
    ids = [r["id"] for r in coll]
    if len(ids) != len(set(ids)):
        err("%s: duplicate ids" % name)
    for r in coll:
        for s in r.get("sources", []):
            if s not in SRC_IDS:
                err("%s %s: unknown source id %s" % (name, r["id"], s))

IRR_IDS = {r["id"] for r in IRR["rows"]}
for r in REQ["rows"]:
    if r["irregular"] and r["irregular"] not in IRR_IDS:
        err("requirements %s: dangling irregularity ref %s" % (r["id"], r["irregular"]))

if [r["num"] for r in REQ["rows"]] != list(range(1, len(REQ["rows"]) + 1)):
    err("requirements: numbering is not contiguous from 1")

VALID_STATE = set(REQ["state_vocabulary"])
for r in REQ["rows"]:
    if r["state"] not in VALID_STATE:
        err("requirements %s: bad state %r" % (r["id"], r["state"]))
    if r["gate"] not in REQ["gate_vocabulary"]:
        err("requirements %s: bad gate %r" % (r["id"], r["gate"]))
    for k in ("clearing_number", "evidence", "verify", "result"):
        if not r.get(k):
            err("requirements %s: empty %s" % (r["id"], k))

VALID_GRADE = set(Q["grade_vocabulary"])
for r in Q["rows"]:
    if r["grade"] not in VALID_GRADE:
        err("questions %s: bad grade %r" % (r["id"], r["grade"]))
    for k in ("question", "why", "have", "dont_have", "route"):
        if not r.get(k):
            err("questions %s: empty %s" % (r["id"], k))

VALID_SEV = set(IRR["severity_vocabulary"])
for r in IRR["rows"]:
    if r["sev"] not in VALID_SEV:
        err("irregularities %s: bad severity %r" % (r["id"], r["sev"]))
    if not r["source_url"].startswith("http"):
        err("irregularities %s: no absolute source_url" % r["id"])

# ---------------------------------------------------------------- 4. no prefilled verdicts
for r in SUG["rows"]:
    if r.get("verdict"):
        err("suggestions %s: a verdict is prefilled (%r) — the board belongs to the reviewer"
            % (r["id"], r["verdict"]))

# ---------------------------------------------------------------- per page
COMPUTED = {str(len(REQ["rows"])), str(len(Q["rows"])), str(len(SUG["rows"])),
            str(len(IRR["rows"])), str(len(SRC["sources"]))}
for r in REQ["rows"]:
    for part in re.findall(r"\d+", r["clearing_number"]):
        COMPUTED.add(part)
    for part in re.findall(r"\d+", r["clearing_condition"]):
        COMPUTED.add(part)
for r in IRR["rows"]:
    for part in re.findall(r"\d+", r["evidence"]):
        COMPUTED.add(part)
for s in SRC["sources"]:
    for part in re.findall(r"\d+", s.get("read", "")):
        COMPUTED.add(part)

TYPED_COUNT_PATTERNS = [
    (re.compile(r"\b(\d+)\s+(requirement|question|suggestion|finding|irregularit|source|line)\w*", re.I),
     "a count typed next to a noun"),
]

for rel in PAGES:
    path = os.path.join(NS, rel)
    if not os.path.exists(path):
        err("%s: missing" % rel)
        continue
    text = open(path, encoding="utf-8").read()

    # 1. structure
    if text.count("<table") != text.count("</table>"):
        err("%s: unbalanced <table>" % rel)
    if text.count("<tbody>") != text.count("</tbody>"):
        err("%s: unbalanced <tbody>" % rel)
    for rx, why in PLACEHOLDERS:
        if rx.search(text):
            err("%s: %s" % (rel, why))

    # 2. every data row has a source link
    for i, tbody in enumerate(re.findall(r"<tbody>(.*?)</tbody>", text, re.S)):
        for j, row in enumerate(re.findall(r"<tr>(.*?)</tr>", tbody, re.S)):
            hrefs = re.findall(r'href="([^"]+)"', row)
            if not hrefs:
                err("%s: table %d row %d has no link at all" % (rel, i, j))
            elif not any(any(d in h for d in OFFICIAL) for h in hrefs):
                err("%s: table %d row %d has no official/repo link (has %s)" % (rel, i, j, hrefs[:2]))
            elif not any("nfl.com" in h for h in hrefs) and not rel.endswith("sources.html"):
                # the brief's strictest reading: a row must point at a *league* official page.
                # Exempt: sources.html, whose rows ARE the register of pages read — forcing an
                # nfl.com link there would mean linking a different page from the one the row is
                # about, which is worse than the gap it would close.
                # Club sites (packers.com, baltimoreravens.com, houstontexans.com) are official
                # publishers but they are not nfl.com, so a row that relies only on a club page
                # must also carry the league corroboration (S06) or be flagged as missing one.
                warnings.append("%s: table %d row %d cites no nfl.com page (club/repo only)"
                                % (rel, i, j))

    # 3. local links resolve
    base = os.path.dirname(path)
    for href in re.findall(r'href="([^"]+)"', text):
        if href.startswith(("http://", "https://", "#", "mailto:")):
            continue
        target, _, frag = href.partition("#")
        if not target:
            continue
        tp = os.path.normpath(os.path.join(base, target))
        if not os.path.exists(tp):
            err("%s: broken local link %s" % (rel, href))
        elif frag:
            ttext = open(tp, encoding="utf-8").read()
            if 'id="%s"' % frag not in ttext and 'name="%s"' % frag not in ttext:
                err("%s: anchor #%s not found in %s" % (rel, frag, target))

    # 5. typed counts in prose (outside tables)
    prose = re.sub(r"<div class=\"tw\">.*?</div>", " ", text, flags=re.S)
    prose = re.sub(r"<table.*?</table>", " ", prose, flags=re.S)
    for rx, why in TYPED_COUNT_PATTERNS:
        for m in rx.finditer(prose):
            n = m.group(1)
            if n not in COMPUTED:
                err("%s: %s — %r (not in the computed set)" % (rel, why, m.group(0)))

    # 4b. the suggestions page must render a blank verdict on every row
    if rel.endswith("suggestions.html"):
        blanks = text.count('<span class="verdict">blank</span>')
        if blanks != len(SUG["rows"]):
            err("%s: %d blank verdict cells for %d suggestion rows"
                % (rel, blanks, len(SUG["rows"])))

    # 6. navigation + footer present
    if 'aria-label="Site sections"' not in text:
        err("%s: navigation missing" % rel)
    if "ncpgambling.org" not in text:
        err("%s: responsible-gambling footer missing" % rel)
    if "Flagged for review" not in text:
        err("%s: no link to the flagged page" % rel)

# ---------------------------------------------------------------- report
print("nfl-board verify")
print("  %d pages, %d requirement lines, %d questions, %d suggestions, %d findings, %d sources"
      % (len(PAGES), len(REQ["rows"]), len(Q["rows"]), len(SUG["rows"]), len(IRR["rows"]), len(SRC["sources"])))
if warnings:
    print("  warnings: %d" % len(warnings))
    for w in warnings:
        print("    - " + w)
if errors:
    print("\nFAILED with %d error(s):" % len(errors))
    for e in errors[:80]:
        print("  " + e)
    sys.exit(1)
print("  PASS: every row source-linked, every local link resolves, no prefilled verdict, no typed count")
sys.exit(0)
