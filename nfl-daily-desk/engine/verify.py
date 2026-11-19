#!/usr/bin/env python3
"""Site verifier for the daily desk. Exits non-zero on any broken rule.

Rules enforced here are the ones the brief makes mechanical:
  1. every table row carries an https source link, and that link's host is official
     (nfl.com for a league value, github.com for a repository artifact, ncpgambling.org for the
     help line);
  2. every local href referenced by a page exists in this namespace;
  3. every figure the landing page prints equals the value in the data file it was rendered from;
  4. recorded sha256 digests match the bytes on disk, and no two captures share a digest;
  5. no banned vocabulary (depth ordered by jersey number/experience/salary, injury as a level,
     season-long ROI as the ranking), and no cell filled with a placeholder instead of a blank
     plus a reason;
  6. the build is deterministic: running engine/build.py again produces byte-identical files.
"""
import hashlib
import json
import os
import re
import subprocess
import sys

NS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(NS)
OFFICIAL = ("nfl.com", "ncpgambling.org", "github.com")
NEGATORS = ("never", "not ", "no ", "reject", "forbid", "banned", "instead of", "rather than",
            "avoid", "without", "refus")
BAD_CLAIMS = [
    (r"depth order(?:ed|ing)? from jersey number", "depth ordering must come from playing time, not jersey number"),
    (r"ranked by (?:player )?(?:jersey number|experience|salar\w+)", "banned ranking basis"),
    (r"injury (?:level|severity) score", "injury is a surprise, not a level"),
    (r"rank\w* strategies by season-long ROI", "ROI over a season is not the ranking"),
    (r"verified as accurate by an official source", "a value is only 'verified' with a link, never by this phrase"),
]
ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
HREF_RE = re.compile(r'href="([^"]+)"')
LINK_RE = re.compile(r'href="(https?://[^"]+)"')
COUNT_RE = re.compile(r'data-count="([^"]+)"')

failures, passed = [], []


def fail(rule, detail):
    failures.append("[FAIL] %s — %s" % (rule, detail))


def ok(rule, detail):
    passed.append("[ok] %s — %s" % (rule, detail))


def pages():
    names = sorted(set(["index.html"] + [f for f in os.listdir(NS) if f.endswith(".html")]))
    for rel in names:
        yield rel, os.path.join(NS, rel)


def sentences(text):
    return re.split(r"(?<=[.;:?!])\s+", text)


def main():
    files = [f for f in pages() if os.path.exists(f[1])]
    if len(files) < 13:
        fail("page-coverage", "expected 13 pages, found %d: %s"
             % (len(files), ", ".join(r for r, _ in files)))

    # rule 0 — structural: every table's body rows must have exactly as many cells as
    # its header, or the page is misaligned and a reader is reading the wrong column.
    TBL_RE = re.compile(r"<table[^>]*>(.*?)</table>", re.S)
    tables = 0
    for rel, path in files:
        html = open(path, encoding="utf-8").read()
        for t in TBL_RE.findall(html):
            tables += 1
            head = re.search(r"<thead>.*?</thead>", t, re.S)
            body = re.findall(r"<tbody>(.*?)</tbody>", t, re.S)
            if not head:
                fail("table-shape", "%s has a table with no <thead>" % rel)
                continue
            ncol = len(re.findall(r"<th[ >]", head.group(0)))
            for chunk in body:
                for row in re.findall(r"<tr[^>]*>(.*?)</tr>", chunk, re.S):
                    ncell = len(re.findall(r"<td[ >]", row))
                    if ncell != ncol:
                        fail("table-shape", "%s: a row has %d cells against a %d-column header — %s"
                             % (rel, ncell, ncol, re.sub(r"<[^>]+>", " ", row)[:90]))
    ok("table-shape", "%d tables, every body row aligned to its header width" % tables)

    # rules 1 + 2 -------------------------------------------------------------
    total_rows = 0
    for rel, path in files:
        html = open(path, encoding="utf-8").read()
        rows = [r for r in ROW_RE.findall(html) if "<td" in r]
        total_rows += len(rows)
        for i, r in enumerate(rows):
            hrefs = LINK_RE.findall(r)
            if not hrefs:
                fail("row-has-source-link", "%s table row %d has no https source link: %s"
                     % (rel, i, re.sub(r"<[^>]+>", " ", r)[:120]))
            for u in hrefs:
                host = re.sub(r"^https?://", "", u).split("/")[0]
                if not any(host == d or host.endswith("." + d) for d in OFFICIAL):
                    fail("official-host-only", "%s links a non-approved host: %s" % (rel, u))
        for h in HREF_RE.findall(html):
            if h.startswith(("http://", "https://", "mailto:", "#", "javascript:")):
                continue
            target = os.path.normpath(os.path.join(os.path.dirname(path), h.split("#")[0]))
            if not os.path.exists(target):
                fail("local-href-exists", "%s -> missing %s" % (rel, h))
    ok("row-has-source-link", "%d data rows across %d pages carry an https source link on an approved host"
       % (total_rows, len(files)))

    # rule 3 — the printed figures must survive an INDEPENDENT re-derivation: the counts
    # are recomputed here from the capture text with a trivial parser that shares no code with
    # engine/parse.py, and from the standings table's own arithmetic.
    cap = os.path.join(NS, "captures", "2026-11-19", "injury-report-week11.md")
    lines = open(cap, encoding="utf-8").read().splitlines()
    rows = [l for l in lines if l.startswith("| ") and l.count("|") == 6
            and "---" not in l and not l.startswith("| Player")]
    clubs = set()
    cur = None
    designated = 0
    for l in lines:
        m = re.match(r"^##+\s+(.*?)(?:\s*[—-]\s*Injury Report)?\s*$", l)
        if m and "Report" not in l and "Week" not in l:
            cur = m.group(1).strip()
        if l.startswith("| ") and l.count("|") == 6 and "---" not in l and not l.startswith("| Player"):
            if cur:
                clubs.add(cur)
            if l.split("|")[5].strip():
                designated += 1
    av = json.load(open(os.path.join(NS, "data", "availability_delta.json"), encoding="utf-8"))
    truth = {"injury_rows": len(rows),
             "injury_clubs": len(clubs),
             "injury_designated": designated}
    sb = av["reads"]["capture_b"]["summary"]
    for key, got, want in [("report rows read today", truth["injury_rows"], sb["n_rows"]),
                           ("clubs with rows", truth["injury_clubs"], sb["n_clubs_with_rows"]),
                           ("rows carrying a game designation", truth["injury_designated"],
                            sb["n_rows_with_game_designation"])]:
        if got != want:
            fail("printed-count-recomputed-from-capture",
                 "%s: capture text gives %s, the published table gives %s" % (key, got, want))
    rcap = os.path.join(NS, "captures", "2026-11-19", "reserve-list-november-2026.md")
    HEADER_WORDS = {"Date", "Name", "Player", "From", "To", "Position", "Transaction", "Injuries",
                    "Status", "Club"}
    rlines = [l for l in open(rcap, encoding="utf-8").read().splitlines()
              if l.startswith("| ") and l.count("|") >= 5 and "---" not in l
              and not (HEADER_WORDS & {c.strip() for c in l.strip("|").split("|")})]
    res = json.load(open(os.path.join(NS, "data", "reserve_delta.json"), encoding="utf-8"))
    if len(rlines) != res["read_b"]["rows"]:
        fail("printed-count-recomputed-from-capture", "reserve ledger: capture text gives %d rows, "
             "the published table gives %d" % (len(rlines), res["read_b"]["rows"]))
    st = json.load(open(os.path.join(NS, "data", "standings.json"), encoding="utf-8"))
    games = sum(r["W"] + r["L"] + r["T"] for r in st["rows"]) // 2
    ext = json.load(open(os.path.join(NS, "data", "corpus_extension.json"), encoding="utf-8"))
    if games != ext["corpus_games_after_extension"]:
        fail("standings-identity-recomputed", "sum(W+L+T)/2 from the transcribed standings = %d but the "
             "corpus claims %d games" % (games, ext["corpus_games_after_extension"]))
    if sum(r["PF"] for r in st["rows"]) != ext["scoring"]["standings_pf_total"]:
        fail("scoring-identity-recomputed", "PF re-summed from the standings table disagrees with the "
             "published total")
    if ext["corpus_games_after_extension"] != ext["inherited_games"] + len(ext["added_games"]):
        fail("corpus-arithmetic", "inherited %d + added %d != published %d"
             % (ext["inherited_games"], len(ext["added_games"]), ext["corpus_games_after_extension"]))
    ok("printed-count-recomputed-from-capture",
       "%d report rows, %d clubs, %d designated rows and %d reserve rows re-derived from the capture text "
       "with an independent parser; standings identities re-summed (%d games)"
       % (len(rows), len(clubs), designated, len(rlines), games))

    # rule 4 ------------------------------------------------------------------
    seen = {}
    for label, read in av["reads"].items():
        p = read.get("path")
        if not p:
            fail("capture-provenance", "%s records no path for its read" % label)
            continue
        fp = os.path.join(ROOT, p)
        if not os.path.exists(fp):
            fail("capture-exists", "%s names a missing capture %s" % (label, p))
            continue
        b = open(fp, "rb").read()
        d = hashlib.sha256(b).hexdigest()
        if d != read["sha256"]:
            fail("capture-digest", "%s digest mismatch (recorded %s…, file %s…)"
                 % (label, read["sha256"][:12], d[:12]))
        if len(b) != read["bytes"]:
            fail("capture-bytes", "%s byte count differs (%d recorded, %d on disk)"
                 % (label, read["bytes"], len(b)))
        if d in seen:
            fail("capture-uniqueness", "%s and %s share a digest — a cached fetch, not a new read"
                 % (seen[d], label))
        seen[d] = label
    if len(seen) == len(av["reads"]):
        ok("capture-integrity", "%d dated captures: digests match the bytes on disk and no two are identical"
           % len(seen))
    if av["drift_alarm"]["status"] != "PASS":
        fail("drift-alarm", "parser drift alarm reports %s: %s"
             % (av["drift_alarm"]["status"], av["drift_alarm"]["problems"]))
    else:
        ok("drift-alarm", "raw-vs-rendered transcription check passes with an empty problem list")
    if av["row_level_delta"]["n_keys_in_both"] + av["row_level_delta"]["n_rows_only_in_later_read"] \
            != av["reads"]["capture_b"]["summary"]["n_rows"]:
        fail("delta-arithmetic", "shared + later-only rows do not add up to the later read's row count")
    else:
        ok("delta-arithmetic", "shared (%d) + later-only (%d) = %d rows read today"
           % (av["row_level_delta"]["n_keys_in_both"],
              av["row_level_delta"]["n_rows_only_in_later_read"],
              av["reads"]["capture_b"]["summary"]["n_rows"]))

    # rule 5 ------------------------------------------------------------------
    for rel, path in files:
        html = open(path, encoding="utf-8").read()
        txt = re.sub(r"<[^>]+>", " ", html)
        for sent in sentences(txt):
            low = sent.lower()
            for pat, why in BAD_CLAIMS:
                m = re.search(pat, low)
                if m and not any(n in low for n in NEGATORS):
                    fail("banned-claim", "%s asserts %r (%s)" % (rel, m.group(0)[:70], why))
        for bad in ("TBD", "TODO", "N/A", "FIXME"):
            if re.search(r">\s*%s\s*<" % re.escape(bad), html):
                fail("blank-not-guessed", "%s carries a literal %s cell instead of a blank with a reason"
                     % (rel, bad))
    ok("banned-claim", "no page asserts a banned ordering/ranking basis outside a rejection sentence")

    # rule 6 ------------------------------------------------------------------
    before = {rel: hashlib.sha256(open(p, "rb").read()).hexdigest() for rel, p in files}
    subprocess.run([sys.executable, os.path.join(NS, "engine", "build.py")], check=True,
                   stdout=subprocess.DEVNULL)
    after = {rel: hashlib.sha256(open(p, "rb").read()).hexdigest() for rel, p in files}
    if before != after:
        diff = [k for k in before if before[k] != after[k]]
        fail("determinism", "rebuild changed %d page(s): %s" % (len(diff), ", ".join(diff)))
    else:
        ok("determinism", "rebuild reproduces all %d pages byte-for-byte" % len(after))

    print("\n".join(passed))
    if failures:
        print("\n".join(failures))
        print("VERIFY: %d failure(s)" % len(failures))
        return 1
    print("VERIFY: all rules pass (%d pages, %d data rows)" % (len(files), total_rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
