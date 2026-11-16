#!/usr/bin/env python3
"""Publication contract for the Decision Console.  FAIL exits 1.

  1. register vocabulary   — every row uses a declared status/priority/severity/grade;
  2. row-level sourcing    — every data row carries an https source link or an explicit blank marker;
  3. index/artefact agreement — the number of rows rendered on a page equals the register it is built from;
  4. link resolution       — every local href resolves to a file that exists in this namespace;
  5. no-price rule         — a price-shaped value (American odds, a spread, a money amount) is a build
                             failure, because no official price source exists (see QA-01 / CD-02);
  6. determinism support   — nothing in the rendered HTML may be a path that only exists at build time.

Run: python3 nfl-decision-console/engine/verify_site.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(NS))
DATA = os.path.join(NS, "data")

SEVERITY = {"high", "medium", "low"}
PRIORITY = {"P1", "P2", "P3"}
SUG_STATUS = {"proposed-for-review", "decided", "rejected", "deferred"}
BLOCKS = {"blocking", "shaping"}
GAP_STATUS = {"owner-blocked", "official-blocked until swept", "open-needs-new-source"}
PRICE_CELL = re.compile(r'^\s*\(?(?:[+-]\d{2,4}(?:\.\d)?|O/U.*|\$\s?\d+)\)?\s*$')
BLANKISH = ("blank — unverified", "no source — not published")

fails = []
notes = []


def load(name, derived=False):
    return json.load(open(os.path.join(DATA, "derived", name) if derived else os.path.join(DATA, name),
                          encoding="utf-8"))


def fail(msg):
    fails.append(msg)


def check_vocab():
    sug = load("suggestions.json")
    for r in sug["rows"]:
        if r["priority"] not in PRIORITY:
            fail("suggestions %s: bad priority %r" % (r["id"], r["priority"]))
        if r["status"] not in SUG_STATUS:
            fail("suggestions %s: bad status %r" % (r["id"], r["status"]))
        if not r["options"] or any(not o.get("cost") or not o.get("locks") for o in r["options"]):
            fail("suggestions %s: every option needs cost + locks" % r["id"])
        for k in ("title", "decision", "evidence", "unblocks", "recommended", "basis",
                  "risk_if_deferred", "effort", "sources"):
            if not r.get(k):
                fail("suggestions %s: missing %s" % (r["id"], k))
        if r["verdict"].strip():
            if not r["decided_by"] or not r["decided_utc"]:
                fail("suggestions %s: a verdict needs decided_by and decided_utc" % r["id"])
            notes.append("%s has a verdict: %s" % (r["id"], r["verdict"]))
    que = load("questions.json")
    for r in que["rows"]:
        if r["blocks"] not in BLOCKS:
            fail("questions %s: bad blocks %r" % (r["id"], r["blocks"]))
        if r["answer_grade"] not in que["grades"]:
            fail("questions %s: answer_grade %r not in the declared vocabulary" % (r["id"], r["answer_grade"]))
        if not r["discovery"].strip():
            fail("questions %s: every row needs a discovery action" % r["id"])
        if r["answer"].strip() and not r["sources"]:
            fail("questions %s: an answer without a source is not an answer" % r["id"])
        if not r["answer"].strip() and r["answer_grade"] not in ("owner-decision-only", "open-needs-new-source"):
            fail("questions %s: blank answer must be graded owner/open" % r["id"])
    fl = load("flags.json")
    for r in fl["rows"]:
        if r["severity"] not in SEVERITY:
            fail("flags %s: bad severity" % r["id"])
        if not r["sources"]:
            fail("flags %s: a flag without a link is an anecdote" % r["id"])
    gp = load("gaps.json")
    for r in gp["rows"]:
        if r["status"] not in GAP_STATUS:
            fail("gaps %s: unrecognised status %r" % (r["id"], r["status"]))
        if not r["route"] or not r["owner"]:
            fail("gaps %s: a gap needs a route and an owner" % r["id"])
    for name, key in (("site_findings.json", "decision_required"), ("paths.json", "clearing_number"),
                      ("sources.json", "grade"), ("official_reads.json", "coverage")):
        d = load(name)
        rows = d.get("rows", [d])
        if not rows:
            fail("%s: empty" % name)
        for r in rows:
            if key not in json.dumps(r):
                fail("%s: a row is missing %r" % (name, key))
    # file-level provenance keys on the two transcription artefacts every number rests on
    for name in ("standings_2026-11-16.json", "gamebook_evidence.json"):
        d = load(name)
        if not d.get("source_url", "").startswith("https://"):
            fail("%s: no https source_url at file level" % name)
        if not (d.get("read_utc") or d.get("read")):
            fail("%s: no read time recorded" % name)
    grades = {r["grade"] for r in load("sources.json")["rows"]}
    if not grades <= {"official", "repo", "third-party"}:
        fail("sources.json: unknown grade in %r" % grades)
    print("vocabulary: %d suggestions / %d questions / %d flags / %d gaps checked"
          % (len(sug["rows"]), len(que["rows"]), len(fl["rows"]), len(gp["rows"])))
    return {"suggestions": len(sug["rows"]), "questions": len(que["rows"]), "gaps": len(gp["rows"]),
            "flags": len(fl["rows"]), "sources": len(load("sources.json")["rows"]),
            "site": len(load("site_findings.json")["rows"]), "paths": len(load("paths.json")["rows"]),
            "reads": len(load("official_reads.json")["rows"]) + 1}


PAGE_ROWS = {"pages/suggestions.html": "suggestions", "pages/questions.html": "questions",
             "pages/gaps.html": "gaps", "pages/flagged.html": "flags", "pages/sources.html": "sources",
             "pages/site-improvements.html": "site", "pages/evidence.html": "reads"}
PAGE_CARDS = {"pages/paths.html": "paths"}


def check_pages(counts):
    pages = ["index.html"] + [p for p, _, _ in
                              [("pages/%s" % f, None, None) for f in sorted(os.listdir(os.path.join(NS, "pages")))]]
    html_cache = {}
    for p in pages:
        fp = os.path.join(NS, p)
        if not os.path.isfile(fp):
            fail("missing page %s" % p)
            continue
        txt = open(fp, encoding="utf-8").read()
        html_cache[p] = txt
        if "assets/console.css" not in txt:
            fail("%s: no stylesheet link" % p)
        if "Provenance rule" not in txt:
            fail("%s: no provenance footer" % p)
        # cards vs register counts (paths render as cards, not rows)
        for name, key in PAGE_CARDS.items():
            if p == name:
                n_cards = len(re.findall(r'class="pathcard"', txt))
                if n_cards != counts[key]:
                    fail("%s: renders %d path cards but paths.json has %d" % (p, n_cards, counts[key]))
        # rows vs register counts
        for name, key in PAGE_ROWS.items():
            if p == name and counts.get(key) is not None:
                n_tr = len(re.findall(r"<tr><td>", txt))
                if n_tr != counts[key]:
                    fail("%s: renders %d data rows but %s.json has %d" % (p, n_tr, key, counts[key]))
        # row-level sourcing + no-price
        for tr in re.findall(r"<tr><td>.*?</tr>", txt, re.S):
            tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
            if not tds:
                continue
            for cell in tds:
                plain = re.sub(r"<[^>]+>", "", cell).strip()
                if PRICE_CELL.match(plain):
                    fail("%s: price-shaped value %r (no official price source exists)" % (p, plain))
            if 'href="https://' not in tr and not any(b in tr for b in BLANKISH):
                fail("%s: a data row carries neither a source link nor a blank marker" % p)
        # link resolution
        for href in re.findall(r'href="([^"]+)"', txt):
            if href.startswith(("http", "mailto", "#")):
                continue
            target = os.path.normpath(os.path.join(os.path.dirname(fp), href.split("#")[0]))
            if not os.path.exists(target):
                fail("%s: broken local link %s" % (p, href))
        if "localhost" in txt or "127.0.0.1" in txt:
            fail("%s: references a local server" % p)
    print("pages: %d checked · rows sourced · links resolved · no price-shaped value" % len(pages))
    # navigation completeness
    idx = html_cache.get("index.html", "")
    for p, title, _ in json.load(open(os.path.join(NS, "engine", "pages.json"), encoding="utf-8")):
        if p != "index.html" and p not in idx:
            fail("index.html has no link to %s" % p)


def check_derived():
    cor = load("corpus.json", True)
    for i in cor["identities"]:
        if not i["holds"]:
            fail("corpus identity failed: %s (%s vs %s)" % (i["name"], i["left"], i["right"]))
    st = load("standings_2026-11-16.json")
    if len(st["rows"]) != 32:
        fail("standings transcription is %d rows, not 32" % len(st["rows"]))
    lj = load("label_join.json", True)
    tot = sum(r["report_rows"] for r in lj["by_status"])
    if tot != lj["counts"]["report_rows"]:
        fail("label join: %d rows in by_status vs %d report rows" % (tot, lj["counts"]["report_rows"]))
    states = sum(lj["counts"]["join_states"].values())
    if states != lj["counts"]["report_rows"]:
        fail("label join: %d classified vs %d rows" % (states, lj["counts"]["report_rows"]))
    inv = load("namespace_inventory.json")
    if not re.match(r"^[0-9a-f]{7}$", inv["captured_at_commit"]):
        fail("inventory does not state the commit it describes")
    print("derived: corpus identities hold; join rows reconcile (%d); inventory pinned to %s"
          % (lj["counts"]["report_rows"], inv["captured_at_commit"]))


def main():
    counts = check_vocab()
    check_pages(counts)
    check_derived()
    for n in notes:
        print("note:", n)
    if fails:
        print("\nFAIL (%d):" % len(fails))
        for f in fails:
            print(" -", f)
        return 1
    print("\nPASS — publication contract holds for the Decision Console")
    return 0


if __name__ == "__main__":
    sys.exit(main())
