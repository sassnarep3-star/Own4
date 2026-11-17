#!/usr/bin/env python3
"""
Own4 · nfl-live-board · verify.py — the build gate.

Fails (exit 1) when any of the rules this namespace claims to hold is broken:

  V1 every table row on every page carries a link, and every link is https;
  V2 every internal link and anchor resolves to a real file, and every page links back to its
     navigation;
  V3 no page references localhost, 127.0.0.1 or a sandbox preview host at runtime;
  V4 the corpus reconciles: 192/192 standings checks pass and the games-played identity holds;
  V5 the pre-registration file's SHA-256 equals the value recorded in data/prereg.json, so a
     post-hoc edit to a rule cannot pass silently;
  V6 every correlation row with a value also carries a finite n, and every row without a value
     carries a non-empty blank reason;
  V7 the leaderboard's benchmark self-test holds (S3's Brier equals the benchmark Brier);
  V11 no page contains a double-escaped HTML entity, which renders as literal text;
  V8 no page contains a hand-typed count of NFL namespaces (the defect class peer sessions hit
     twice): the pattern "<integer> nfl-" outside a <table> fails the build;
  V9 the price store is consistently empty - a filled slot without a timestamp, a source or a
     hash fails the build;
  V10 the requirement register's own arithmetic matches its summary.

Run: python3 nfl-live-board/verify.py
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NS = HERE
DATA = os.path.join(NS, "data")
PAGES = [os.path.join(NS, "index.html")]
for f in sorted(os.listdir(os.path.join(NS, "pages"))):
    if f.endswith(".html"):
        PAGES.append(os.path.join(NS, "pages", f))

fails, notes = [], []


def fail(code, msg):
    fails.append("%s: %s" % (code, msg))


def load(p):
    with open(os.path.join(DATA, p)) as f:
        return json.load(f)


# ---------------------------------------------------------------- V1/V2/V3
for p in PAGES:
    rel = os.path.relpath(p, NS)
    text = open(p, encoding="utf-8").read()

    for i, tr in enumerate(re.finditer(r"<tr[^>]*>(.*?)</tr>", text, re.S | re.I), 1):
        body = tr.group(1)
        if "<th" in body:
            continue
        if "href=" not in body:
            fail("V1", "%s row %d has no link" % (rel, i))
        elif not re.search(r'href="https://', body):
            fail("V1", "%s row %d has no https link" % (rel, i))

    for m in re.finditer(r'(?:href|src)="([^"]+)"', text):
        h = m.group(1)
        if h.startswith(("http://", "https://", "mailto:", "data:")):
            if h.startswith("http://"):
                fail("V1", "%s has a non-https link: %s" % (rel, h))
            continue
        target = h.split("#")[0]
        if target and not os.path.exists(os.path.join(os.path.dirname(p), target)):
            fail("V2", "%s broken internal link: %s" % (rel, h))

    if 'class="layout"' not in text and "nfl-live-board" not in text:
        fail("V2", "%s has no site navigation" % rel)
    if "ncpgambling.org" not in text:
        fail("V2", "%s is missing the responsible-gambling footer" % rel)

    runtime = (r"""(?:href|src|action)\s*=\s*["'](?:https?:)?//(?:localhost|127\.0\.0\.1)"""
               r"""|(?:https?:)?//(?:localhost|127\.0\.0\.1)[:/"']"""
               r"""|\b(?:localhost|127\.0\.0\.1):\d+|https://\d+-[a-z0-9-]+\.e2b\.app""")
    if re.search(runtime, text, re.I):
        fail("V3", "%s references a local/preview host at runtime" % rel)

    # V11: a double-escaped entity renders as literal text in a browser. Peer sessions shipped
    # this defect twice; the check is cheap and the failure is embarrassing, so it is a gate.
    if re.search(r"&(?:amp|lt|gt|quot|#\d+);(?:mdash|ndash|middot|amp|lt|gt|quot);", text):
        fail("V11", "%s contains a double-escaped entity" % rel)

    # V8: no typed namespace counts in prose (the F2 / SG-H defect class)
    for m in re.finditer(r"<p[^>]*>(.*?)</p>", text, re.S):
        if re.search(r"\b\d+\s+nfl-", m.group(1)):
            fail("V8", "%s contains a typed namespace count: %s" % (rel, m.group(1)[:80]))

# ---------------------------------------------------------------- V4
corp = load("corpus_2026.json")["summary"]
if corp["fail"]:
    fail("V4", "%d standings checks fail" % corp["fail"])
if not corp["identity_holds"]:
    fail("V4", "games-played identity does not hold: %d corpus vs %d official"
         % (corp["corpus_games"], corp["official_games_played"]))
notes.append("V4 corpus: %d games, %d/%d checks pass, identity=%s"
             % (corp["corpus_games"], corp["pass"], corp["checks"], corp["identity_holds"]))

# ---------------------------------------------------------------- V5
prereg_path = os.path.join(NS, "prereg", "PREREG-LB.md")
digest = hashlib.sha256(open(prereg_path, "rb").read()).hexdigest()
recorded = load("prereg.json")
if recorded["prereg_sha256"] != digest:
    fail("V5", "PREREG-LB.md changed after registration: recorded %s, actual %s"
         % (recorded["prereg_sha256"][:12], digest[:12]))
notes.append("V5 prereg sha256 %s..." % digest[:16])

# ---------------------------------------------------------------- V6
cor = load("correlations.json")
for r in cor["rows"]:
    if r["r"] is not None and (r["n"] is None or r["n"] < 3):
        fail("V6", "%s has r without a usable n" % r["id"])
    if r["r"] is None and not r["blank_reason"]:
        fail("V6", "%s is blank without a reason" % r["id"])
notes.append("V6 correlations: %d with values, %d blank, all reasoned"
             % (cor["n_computed"], cor["n_blank"]))

# ---------------------------------------------------------------- V7
lb = load("leaderboard.json")
s3 = [r for r in lb["rows"] if r["id"].startswith("S3")][0]
if abs(s3["proper_score"]["brier"] - s3["proper_score"]["benchmark_brier"]) > 1e-12:
    fail("V7", "benchmark self-test broken: Brier %s vs benchmark %s"
         % (s3["proper_score"]["brier"], s3["proper_score"]["benchmark_brier"]))
if lb["points_awarded"] != 0 and lb["qualifiers"] == 0:
    fail("V7", "points awarded to no qualifiers")
notes.append("V7 leaderboard: %d strategies, %d qualifiers, %d points"
             % (len(lb["rows"]), lb["qualifiers"], lb["points_awarded"]))

# ---------------------------------------------------------------- V9
ps = load("price_snapshots.json")
filled = 0
for r in ps["rows"]:
    for stage in ("open", "close"):
        v = r[stage]
        if v is None:
            continue
        filled += 1
        for fld in ("%s_captured_utc" % stage, "%s_source_url" % stage, "%s_sha256" % stage):
            if not r.get(fld):
                fail("V9", "%s %s %s has a value but no %s" % (r["game"], r["market"], stage, fld))
notes.append("V9 price store: %d slots, %d filled" % (len(ps["rows"]), filled))

# ---------------------------------------------------------------- V10
req = load("requirements.json")
s = req["summary"]
if s["total"] != len(req["rows"]):
    fail("V10", "summary total %d != %d rows" % (s["total"], len(req["rows"])))
counted = sum(s[k] for k in ("met", "partial", "blocked", "rejected", "process"))
if counted != s["total"]:
    fail("V10", "status counts sum to %d, total is %d" % (counted, s["total"]))
for r in req["rows"]:
    if not r.get("gate") or not r.get("clearing_number"):
        fail("V10", "%s lacks a gate or a clearing number" % r["id"])
    if not str(r.get("evidence_url", "")).endswith(".html"):
        fail("V10", "%s has no page to review it on" % r["id"])
notes.append("V10 requirements: %d rows, %d met / %d partial / %d blocked / %d rejected / %d process"
             % (s["total"], s["met"], s["partial"], s["blocked"], s["rejected"], s["process"]))

# ---------------------------------------------------------------- report
for n in notes:
    print("  " + n)
if fails:
    print("\nFAIL (%d)" % len(fails))
    for f in fails[:40]:
        print("  " + f)
    sys.exit(1)
print("\nall checks passed: %d pages, every row source-linked, every local link resolves, "
      "corpus reconciled, prereg hash matches." % len(PAGES))
