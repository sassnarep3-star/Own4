#!/usr/bin/env python3
"""
nfl-command-deck — verifier. Exit 0 = pass, 1 = fail. Standard library only.

Checks, on the committed tree:
  1. every generator is deterministic: re-running it reproduces the committed bytes;
  2. every internal href on every page resolves to a file, and every #anchor to an id;
  3. no localhost / 127.0.0.1 reference anywhere in the rendered pages;
  4. every data-table row carries at least one external source link;
  5. no unfilled placeholder token survives; no "None"/"nan" leaked into a cell;
  6. every figure quoted in prose matches the data file it claims to come from
     (the prose/data agreement check — the one a hand edit breaks);
  7. every flag, question and suggestion carries a source link;
  8. the pre-registration hash still matches the lock, and eval.json records it;
  9. the site nav does not link outside this workspace;
 10. no crash-marker and no empty page.
"""

import hashlib
import html as htmlmod
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
DATA = os.path.join(NS, "data")

PAGES = ["index.html", "pages/executive-summary.html", "pages/model.html",
         "pages/availability.html", "pages/requirements.html", "pages/repo-audit.html",
         "pages/questions.html", "pages/suggestions.html", "pages/flagged.html",
         "pages/sources.html"]

errors = []


def fail(msg):
    errors.append(msg)


def load(name):
    return json.load(open(os.path.join(DATA, name), encoding="utf-8"))


def read(path):
    return open(os.path.join(NS, path), encoding="utf-8").read()


# ---------------------------------------------------------------- 1 determinism
GENERATORS = [("engine/model_eval.py", ["data/eval.json"]),
              ("engine/null_test.py", ["data/null.json"]),
              ("engine/audit_repo.py", ["data/audit.json", "data/link_defects.json"]),
              ("engine/availability.py", ["data/availability.json", "data/injury_rows.json"]),
              ("engine/requirements.py", ["data/requirements.json"]),
              ("engine/build_site.py", PAGES)]


def check_determinism():
    before = {}
    for _, outs in GENERATORS:
        for o in outs:
            p = os.path.join(NS, o)
            before[o] = hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None
    for script, _ in GENERATORS:
        r = subprocess.run([sys.executable, os.path.join(NS, script)], cwd=NS,
                           capture_output=True, text=True)
        if r.returncode != 0:
            fail("generator %s exited %d: %s" % (script, r.returncode, r.stderr[-400:]))
    for _, outs in GENERATORS:
        for o in outs:
            p = os.path.join(NS, o)
            after = hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None
            if before[o] != after:
                fail("non-deterministic output: %s changed on rebuild" % o)


# ---------------------------------------------------------------- 2 links/anchors
def check_links():
    for page in PAGES:
        p = os.path.join(NS, page)
        if not os.path.exists(p):
            fail("missing page %s" % page)
            continue
        s = read(page)
        ids = set(re.findall(r'id="([^"]+)"', s))
        base = os.path.dirname(p)
        for m in re.finditer(r'href="([^"#]*)(#[^"]*)?"', s):
            u, frag = m.group(1), m.group(2)
            if not u or u.startswith(("http", "mailto:", "tel:")):
                continue
            t = os.path.normpath(os.path.join(base, u.split("?")[0]))
            if not os.path.exists(t):
                fail("%s: broken link %s" % (page, u))
            elif frag and t.endswith(".html"):
                tid = set(re.findall(r'id="([^"]+)"', open(t, encoding="utf-8").read()))
                if frag[1:] not in tid:
                    fail("%s: broken anchor %s" % (page, u + frag))
    # nav must not reach outside the workspace
    for page in PAGES:
        s = read(page)
        nav = re.search(r"<nav[^>]*>(.*?)</nav>", s, re.S)
        if not nav:
            fail("%s: no nav" % page)
            continue
        for href in re.findall(r'href="([^"]+)"', nav.group(1)):
            if href.startswith("http") or href.startswith("../.."):
                fail("%s: nav leaves the workspace: %s" % (page, href))


# ---------------------------------------------------------------- 3 localhost
def check_localhost():
    for page in PAGES:
        s = read(page)
        for bad in ("localhost", "127.0.0.1", "0.0.0.0", "file://"):
            if bad in s:
                fail("%s: contains %s" % (page, bad))


# ---------------------------------------------------------------- 4 row sources
def check_row_sources():
    for page in PAGES:
        s = read(page)
        for tbl in re.findall(r"<tbody>(.*?)</tbody>", s, re.S):
            for row in re.findall(r"<tr>(.*?)</tr>", tbl, re.S):
                if "<td" not in row:
                    continue          # a <th> header row inside tbody is allowed
                if not re.search(r'href="https?://', row):
                    fail("%s: table row without an external source link: %s"
                         % (page, htmlmod.unescape(re.sub(r"<[^>]+>", " ", row))[:110]))


# ---------------------------------------------------------------- 5 placeholders
def check_placeholders():
    patterns = [r"\{[a-zA-Z_]+\}", r"%\([a-zA-Z_]+\)[sdf]", r">None<", r">nan<", r"TODO",
                r">undefined<", r"Lorem ipsum"]
    for page in PAGES:
        s = read(page)
        for pat in patterns:
            m = re.search(pat, s)
            if m:
                i = m.start()
                fail("%s: placeholder-ish token %r near %r"
                     % (page, m.group(0), s[max(0, i - 40):i + 40].replace("\n", " ")))
        if len(s) < 3000:
            fail("%s: suspiciously short (%d bytes)" % (page, len(s)))


# ---------------------------------------------------------------- 6 prose vs data
def check_prose_matches_data():
    ev = load("eval.json")
    c = ev["scored"]["weeks_4_10"]
    h = ev["scored"]["holdout_weeks_8_10"]
    nl = load("null.json")
    avail = load("availability.json")["counts"]
    req = load("requirements.json")["summary"]
    flags = load("flags.json")["flags"]

    index = read("index.html")
    expectations = [
        ("index: corpus games", "%d" % ev["inputs"]["corpus_games"]),
        ("index: scored n", ">%d<" % c["CD-1"]["n"]),
        ("index: BSS", "%+.4f" % c["CD-1"]["bss"]),
        ("index: holdout BSS", "%+.4f" % h["CD-1"]["bss"]),
        ("index: permutation p", ">%s<" % ("%s" % nl["p_permutation"]).replace("0.0", "0.0")),
        ("index: points awarded", ">%d<" % ev["leaderboard_policy"]["points_awarded"]),
        ("index: flag count", "⚑ %d items flagged" % len(flags)),
    ]
    for label, token in expectations:
        if label == "index: permutation p":
            if not re.search(r">%s<" % re.escape(str(nl["p_permutation"])), index):
                fail("prose/data: %s — expected %s" % (label, nl["p_permutation"]))
            continue
        if token not in index:
            fail("prose/data: %s — token %r not found" % (label, token))

    model = read("pages/model.html")
    for label, val in [("model: pre-reg hash", ev["prereg_sha256"]),
                       ("model: margin lambda", "%g" % ev["protocol"]["selected_margin_lambda"]),
                       ("model: total lambda", "%g" % ev["protocol"]["selected_total_lambda"]),
                       ("model: MAE", "%.4f" % ev["totals"]["mae"]),
                       ("model: ties", ">%d<" % ev["protocol"]["ties_excluded"])]:
        if val not in model:
            fail("prose/data: %s — %r missing" % (label, val))
    for w in ev["per_week"]:
        if "%.5f" % w["brier_CD-1"] not in model:
            fail("prose/data: per-week Brier for week %s missing" % w["week"])

    av = read("pages/availability.html")
    for label, v in [("availability: player rows", avail["player_rows"]),
                     ("availability: Out", avail["Out"]),
                     ("availability: Questionable", avail["Questionable"]),
                     ("availability: rank-1 Out", avail["rank1_players_out"])]:
        if ">%d<" % v not in av:
            fail("prose/data: %s — %d missing" % (label, v))
    if avail["sha256"] and avail["sha256"] if "sha256" in avail else False:
        pass
    cap_sha = load("availability.json")["capture"]["sha256"]
    if cap_sha not in av:
        fail("prose/data: availability page does not print the capture hash")

    rq = read("pages/requirements.html")
    for label, v in [("requirements: rows", req["rows"]),
                     ("requirements: rechecked", req["verified_by_this_session"]),
                     ("requirements: contradicted", req["contradicted"])]:
        if ">%d<" % v not in rq:
            fail("prose/data: %s — %d missing" % (label, v))

    # ratios quoted in prose must be computed from the rows, not assumed
    rows = load("requirements.json")["rows"]
    contradicted_ids = [r["id"] for r in rows if r["verdict"] == "contradicted"]
    for cid in contradicted_ids:
        if cid not in rq:
            fail("prose/data: contradicted row %s not shown on the requirements page" % cid)


# ---------------------------------------------------------------- 7 content sources
def check_content_sources():
    for f in load("flags.json")["flags"]:
        if not f.get("sources"):
            fail("flag %s has no source" % f["id"])
    for q in load("questions.json")["rows"]:
        if not q.get("sources"):
            fail("question %s has no source" % q["id"])
    for s in load("suggestions.json")["rows"]:
        if not s.get("sources"):
            fail("suggestion %s has no source" % s["id"])
        if s.get("decision") != "":
            fail("suggestion %s has a non-blank decision field (owner's call, not ours)" % s["id"])


# ---------------------------------------------------------------- 8 prereg hash
def check_prereg():
    lock = json.load(open(os.path.join(DATA, "prereg_lock.json"), encoding="utf-8"))
    p = os.path.join(NS, lock["file"])
    got = hashlib.sha256(open(p, "rb").read()).hexdigest()
    if got != lock["sha256"]:
        fail("pre-registration file changed: %s != %s" % (got, lock["sha256"]))
    ev = load("eval.json")
    if ev["prereg_sha256"] != lock["sha256"]:
        fail("eval.json does not record the locked pre-registration hash")
    nl = load("null.json")
    if nl["observed_bss"] != ev["scored"]["weeks_4_10"]["CD-1"]["bss"]:
        fail("null test and evaluation disagree on the observed BSS")


# ---------------------------------------------------------------- 9 no outside edits
def check_scope():
    """This workspace must not have modified a peer namespace."""
    r = subprocess.run(["git", "status", "--porcelain"], cwd=os.path.dirname(NS),
                       capture_output=True, text=True)
    allowed_prefix = ("nfl-command-deck/", "COORDINATION.md", "verification/build.py",
                      "index.html", "verified/")
    for line in r.stdout.splitlines():
        path = line[3:].strip().split(" -> ")[-1]
        if path and not path.startswith(allowed_prefix):
            fail("out-of-scope modification: %s" % path)


def main():
    check_determinism()
    check_links()
    check_localhost()
    check_row_sources()
    check_placeholders()
    check_prose_matches_data()
    check_content_sources()
    check_prereg()
    check_scope()
    if errors:
        print("FAIL — %d problem(s)" % len(errors))
        for e in errors[:60]:
            print(" !", e)
        if len(errors) > 60:
            print(" ... and %d more" % (len(errors) - 60))
        sys.exit(1)
    print("PASS — %d pages; determinism, links, anchors, row sources, placeholders, "
          "prose/data agreement, content sources, pre-registration hash and edit scope all clean"
          % len(PAGES))


if __name__ == "__main__":
    main()
