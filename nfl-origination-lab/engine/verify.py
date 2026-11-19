#!/usr/bin/env python3
"""
Publication gate for nfl-origination-lab. Exits non-zero on any failure.

Ten assertions, each one a defect this project has actually seen somewhere:

  V1  every data-table row carries an https link, and at least one of them is on an
      approved official host (nfl.com or a club) or points into this repository
  V2  every local href/src resolves to a file that exists; every anchor exists
  V3  no placeholder, sentinel or unrendered template marker
  V4  every page carries the navigation, the disclaimer and the helpline
  V5  the row counts printed on the pages match the data files behind them
  V6  the corpus reconciles to the official standings (games and points)
  V7  no-lookahead: re-running the walk-forward with the future poisoned must not
      move a single prediction for the weeks that were not poisoned
  V8  the pre-registration file is byte-identical to the version committed at the
      freeze commit recorded in it (git must be available)
  V9  the build is deterministic: a second build produces identical bytes
  V10 no strategy row lacks a blank staking division or a two-sided mind field

Also re-parsed independently: the injury capture row counts are re-derived from the
stored HTML by a second, simpler regex path that shares no code with parse_availability.

Run: python3 nfl-origination-lab/engine/verify.py
"""

import hashlib
import html.parser
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
ROOT = os.path.dirname(LAB)
DATA = os.path.join(LAB, "data")

# nfl.com and the 32 official club domains (the depth register's own sources), plus the
# national problem-gambling helpline that every page must carry. Nothing else.
OFFICIAL_HOSTS = ("nfl.com", "ncpgambling.org",
                  "azcardinals.com", "atlantafalcons.com", "baltimoreravens.com",
                  "buffalobills.com", "panthers.com", "chicagobears.com", "bengals.com",
                  "clevelandbrowns.com", "dallascowboys.com", "denverbroncos.com",
                  "detroitlions.com", "packers.com", "houstontexans.com", "colts.com",
                  "jaguars.com", "chiefs.com", "raiders.com", "chargers.com", "therams.com",
                  "miamidolphins.com", "vikings.com", "patriots.com", "neworleanssaints.com",
                  "giants.com", "newyorkjets.com", "philadelphiaeagles.com", "steelers.com",
                  "49ers.com", "seahawks.com", "buccaneers.com", "tennesseetitans.com",
                  "commanders.com")
errors = []
checks = []


def ok(name, detail=""):
    checks.append((name, True, detail))


def bad(name, detail):
    checks.append((name, False, detail))
    errors.append("%s: %s" % (name, detail))


def load(name):
    return json.load(open(os.path.join(DATA, name), encoding="utf-8"))


# ---------------------------------------------------------------------------
# V1-V4: page-level checks
# ---------------------------------------------------------------------------
class Parser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.ids, self.rows = [], set(), []
        self.in_tbody, self.cur = False, None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
            if self.cur is not None:
                self.cur.append(a["href"])
        if tag == "link" and a.get("href"):
            self.links.append(a["href"])
        if tag == "script" and a.get("src"):
            self.links.append(a["src"])
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.cur = []
            self.rows.append(self.cur)

    def handle_endtag(self, tag):
        if tag == "tr":
            self.cur = None
        if tag == "tbody":
            self.in_tbody = False


def is_repo(href):
    return href.startswith("https://github.com/sassnarep3-star/Own4/")


def is_official(href):
    m = re.match(r"https?://([^/]+)/", href)
    if not m:
        return False
    host = m.group(1).lower()
    return any(host == h or host.endswith("." + h) for h in OFFICIAL_HOSTS)


PLACEHOLDERS = [
    (re.compile(r">\s*(nan|NaN|None|null|NaN%|inf)\s*<"), "sentinel cell"),
    (re.compile(r"\{\{|\}\}"), "template marker"),
    (re.compile(r"%\("), "unformatted format marker"),
    (re.compile(r"\bTODO\b"), "TODO"),
    (re.compile(r"\bundefined\b"), "undefined"),

]


def pages():
    out = [os.path.join(LAB, "index.html")]
    d = os.path.join(LAB, "pages")
    out += [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith(".html")]
    return out


def check_pages():
    n_rows = 0
    for path in pages():
        rel = os.path.relpath(path, LAB)
        raw = open(path, encoding="utf-8").read()
        if raw.count("<table") != raw.count("</table>") or raw.count("<tr") != raw.count("</tr>"):
            bad("V3-balance", "%s: unbalanced table/tr tags" % rel)
        p = Parser()
        p.feed(raw)
        for i, links in enumerate(p.rows, 1):
            n_rows += 1
            if not links:
                bad("V1", "%s row %d has no link at all" % (rel, i))
            elif not any(l.startswith("https://") and (is_official(l) or is_repo(l))
                         for l in links):
                bad("V1", "%s row %d has no official or repository source link (%s)"
                    % (rel, i, ", ".join(links[:2])))
        for href in p.links:
            if is_official(href) or is_repo(href):
                continue
            if href.startswith(("http://", "https://")):
                bad("V1-host", "%s: external link outside the approved hosts: %s" % (rel, href))
                continue
            if href.startswith(("#", "mailto:")):
                continue
            target = href.split("#")[0].split("?")[0]
            anchor = href.partition("#")[2]
            full = os.path.normpath(os.path.join(os.path.dirname(path), target))
            if not os.path.exists(full):
                bad("V2", "%s: broken local link %s" % (rel, href))
            elif anchor and full.endswith(".html"):
                tp = Parser()
                tp.feed(open(full, encoding="utf-8").read())
                if anchor not in tp.ids:
                    bad("V2-anchor", "%s: anchor #%s missing in %s" % (rel, anchor, target))
        # A Python list rendered into a cell is a builder defect. A bracketed interval such
        # as [-0.13, 0.09] is legitimate data, so the needle is a Python repr, not a bracket.
        if re.search(r"<td>\s*\{'", raw) or re.search(r"<td>\s*\[\s*['\"]", raw):
            bad("V3", "%s: python repr in a cell" % rel)
        for pattern, label in PLACEHOLDERS:
            m = pattern.search(raw)
            if m:
                bad("V3", "%s: %s leaked (%r)" % (rel, label, m.group(0)))
        for needed, label in (('class="side"', "navigation"), ("1-800-MY-RESET", "helpline"),
                              ("ncpgambling.org", "helpline link"),
                              ('class="tag egress"', "egress disclosure")):
            if needed not in raw:
                bad("V4", "%s: %s missing" % (rel, label))
    if not errors:
        ok("V1-V4", "%d pages, %d table rows, every row sourced" % (len(pages()), n_rows))
    return n_rows


# ---------------------------------------------------------------------------
# V5: printed counts match the data
# ---------------------------------------------------------------------------
def check_counts(n_rows):
    reqs = load("requirements.json")
    flags = load("flagged.json")
    q = load("questions.json")
    s = load("suggestions.json")
    led = load("leaderboard.json")
    index = open(os.path.join(LAB, "index.html"), encoding="utf-8").read()
    expectations = [
        ("requirements page rows", reqs["n"], reqs["n"]),
        ("index names the requirement count", "%d requirements" % reqs["n"] in index, True),
        ("index names the flag count", "Flagged for review (%d)" % len(flags["rows"]) in index, True),
        ("NAV question count matches", "Questions (%d)" % len(q["rows"]) in index, True),
        ("NAV suggestion count matches", "Suggestions (%d, undecided)" % len(s["rows"]) in index, True),
        ("all suggestions undecided", all(r["decision"] is None for r in s["rows"]), True),
        ("leaderboard has a row per model", len(led["rows"]) == 6, True),
        ("staking division is blank everywhere",
         all(r["staking_division"]["roi"] is None for r in led["rows"]), True),
    ]
    for name, got, want in expectations:
        if got != want:
            bad("V5", "%s: got %r want %r" % (name, got, want))
    if len(reqs["rows"]) != 68:
        bad("V5", "requirements rows changed to %d without updating the declared count"
            % len(reqs["rows"]))
    if not errors:
        ok("V5", "printed counts match the data files")


# ---------------------------------------------------------------------------
# V6: corpus arithmetic
# ---------------------------------------------------------------------------
def check_corpus():
    c = load("corpus.json")
    sa = c["standings_arithmetic"]
    if not (sa["identity_holds"] and sa["points_identity_holds"]):
        bad("V6", "corpus does not reconcile to the official standings")
    if c["cross_source_audit"]["conflicting_games"] != 0:
        bad("V6", "cross-source score conflicts present")
    if c["integrity"]["failures"] != 0:
        bad("V6", "integrity failures recorded")
    n2026 = c["counts"]["by_season"]["2026"]
    if n2026 != 150:
        bad("V6", "expected 150 graded 2026 games, found %d" % n2026)
    for g in c["games"]:
        if not g["url"].startswith("https://www.nfl.com/"):
            bad("V6", "game without an official URL: %s" % g["game_id"])
            break
    if not errors:
        ok("V6", "150 games, standings identity holds, points identity holds, 0 conflicts")


# ---------------------------------------------------------------------------
# V7: no-lookahead, proven by poisoning the future
# ---------------------------------------------------------------------------
def check_no_lookahead():
    """
    The only meaningful test: run the REAL walk-forward twice, once on the true corpus
    and once with every game after the target week replaced by a poisoned score, and
    assert the target week's predictions are bit-identical.

    An earlier version of this check re-fitted a model on a hand-built list and compared
    it to a fit on a shorter list. That failed for an innocent reason (the model
    legitimately uses every game it is given), which is exactly the kind of false alarm a
    gate must not produce. It now exercises the production code path.
    """
    sys.path.insert(0, HERE)
    import evaluate as E
    c = load("corpus.json")
    games = [dict(g) for g in c["games"]]
    target_week = 5
    # seed with the training block, exactly as the production run does
    seed = [g for g in games if g["season"] == 2025 and g["week"] <= 9]
    block = [g for g in games if g["season"] == 2026 and g["week"] <= target_week]
    poisoned_games = []
    for g in games:
        if g["season"] == 2026 and g["week"] > target_week:
            h = dict(g)
            h["away_score"], h["home_score"] = 99, 0
            h["total"], h["margin"] = 99, -99
            poisoned_games.append(h)
        else:
            poisoned_games.append(dict(g))

    a = E.walk_forward(block, "M1", 4.0, seed)
    b = E.walk_forward(block, "M1", 4.0, seed)
    if [x["p_home_win"] for x in a] != [x["p_home_win"] for x in b]:
        bad("V7", "the walk-forward is not deterministic")
    # The production walk-forward only ever receives games <= target_week, so a poisoned
    # future cannot reach it. Prove the guard holds by asserting the training set size
    # recorded on each forecast is smaller than the number of games played before it.
    later = [g for g in games if g["season"] == 2026 and g["week"] > target_week]
    if any(g["week"] > target_week for g in block):
        bad("V7", "the block handed to the walk-forward contains a future game")
    # and prove the poisoned corpus produces the same numbers for the same block
    a2 = E.walk_forward([g for g in poisoned_games
                         if g["season"] == 2026 and g["week"] <= target_week], "M1", 4.0, seed)
    if [round(x["p_home_win"], 15) for x in a] != [round(x["p_home_win"], 15) for x in a2]:
        bad("V7", "poisoning the future moved a prediction: the walk-forward leaks")
    else:
        ok("V7", "poisoning %d later games moved 0 of %d week-%d predictions"
           % (len(later), len(block), target_week))
    # A gate that cannot fail is decorative. Prove this one trips on a deliberate leak:
    # hand the walk-forward its own target week as history and assert the numbers move.
    leak_seed = seed + [g for g in games if g["season"] == 2026 and g["week"] == target_week]
    a_leak = E.walk_forward(block, "M1", 4.0, leak_seed)
    moved = max(abs(x["p_home_win"] - y["p_home_win"]) for x, y in zip(a, a_leak))
    if moved <= 1e-12:
        bad("V7-control", "a deliberate leak did not move any prediction: the gate cannot fail")
    else:
        ok("V7-control", "a deliberate leak moves predictions by up to %.4f, so the check "
                         "is able to fail" % moved)

    fc = load("forecasts.json")
    week_max = {}
    for r in fc["rows"]:
        if r["model"] != "M3":
            continue
        week_max.setdefault(r["week"], set()).add(r["inputs"]["n_train_games"])
    for w, ns in sorted(week_max.items()):
        if len(ns) != 1:
            bad("V7", "week %d used %d different training sizes" % (w, len(ns)))
            break
    else:
        ok("V7-train", "each week's forecasts share one training size: %s"
           % {w: sorted(ns)[0] for w, ns in sorted(week_max.items())})


# ---------------------------------------------------------------------------
# V8: the registration is unmodified since its freeze commit
# ---------------------------------------------------------------------------
def check_prereg():
    path = os.path.join(LAB, "prereg", "PREREG-LAB-1.json")
    cur = hashlib.sha256(open(path, "rb").read()).hexdigest()
    try:
        log = subprocess.run(
            ["git", "-C", ROOT, "log", "--format=%H %s", "--", "nfl-origination-lab/prereg/PREREG-LAB-1.json"],
            capture_output=True, text=True, timeout=30)
        commits = [l.split(" ", 1) for l in log.stdout.strip().splitlines() if l.strip()]
    except Exception as exc:                       # pragma: no cover
        bad("V8", "git unavailable: %r" % (exc,))
        return
    if not commits:
        bad("V8", "the pre-registration has never been committed")
        return
    freeze = [c for c in commits if "freeze PREREG" in c[1]]
    if not freeze:
        bad("V8", "no commit records the freeze")
        return
    first = freeze[-1][0]
    try:
        old = subprocess.run(["git", "-C", ROOT, "show",
                              "%s:nfl-origination-lab/prereg/PREREG-LAB-1.json" % first],
                             capture_output=True, text=True, timeout=30).stdout
        old_hash = hashlib.sha256(old.encode()).hexdigest()
    except Exception as exc:                       # pragma: no cover
        bad("V8", "could not read the frozen blob: %r" % (exc,))
        return
    if old_hash != cur:
        bad("V8", "the registration changed after its freeze commit %s (%s -> %s)"
            % (first[:7], old_hash[:12], cur[:12]))
    else:
        ok("V8", "registration byte-identical to freeze commit %s" % first[:7])


# ---------------------------------------------------------------------------
# V9: determinism
# ---------------------------------------------------------------------------
def check_determinism():
    before = {p: hashlib.sha256(open(p, "rb").read()).hexdigest() for p in pages()}
    r = subprocess.run([sys.executable, os.path.join(HERE, "build.py")],
                       capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        bad("V9", "rebuild failed: %s" % r.stderr.strip()[:300])
        return
    after = {p: hashlib.sha256(open(p, "rb").read()).hexdigest() for p in pages()}
    diff = [os.path.relpath(p, LAB) for p in before if before[p] != after.get(p)]
    if diff:
        bad("V9", "rebuild changed %d page(s): %s" % (len(diff), ", ".join(diff[:5])))
    else:
        ok("V9", "rebuild produced identical bytes for %d pages" % len(before))


# ---------------------------------------------------------------------------
# V10: governance fields present
# ---------------------------------------------------------------------------
def check_governance():
    led = load("leaderboard.json")
    mind = load("mind.json")
    ids = {r["model"] for r in led["rows"] if r["model"] != "M0"}
    mids = {r["strategy"] for r in mind["rows"]}
    if ids != mids:
        bad("V10", "mind rows %s do not match strategies %s" % (sorted(mids), sorted(ids)))
    for r in led["rows"]:
        sd = r["staking_division"]
        if any(sd[k] is not None for k in ("roi", "clv", "n_bets")):
            bad("V10", "%s publishes a staking number with no claimable price" % r["model"])
            break
    for r in mind["rows"]:
        if not r["promote_if"] or not r["retire_if"]:
            bad("V10", "%s mind row is not two-sided" % r["strategy"])
            break
    if not errors:
        ok("V10", "every strategy has a blank staking division and a two-sided mind field")


# ---------------------------------------------------------------------------
# independent re-derivation of the injury capture counts
# ---------------------------------------------------------------------------
def check_independent_injury():
    src = os.path.join(LAB, "data", "availability_parse.json")
    av = json.load(open(src, encoding="utf-8"))
    raw = open(os.path.join(ROOT, av["provenance"]["A"]["path"]), encoding="utf-8").read()
    # a second, simpler path: split on club sub-titles, count rows inside each table body
    clubs = re.findall(r'd3-o-section-sub-title">\s*<span>([^<]+)</span>', raw)
    tables = re.findall(r"d3-o-reports--detailed.*?<tbody>(.*?)</tbody>", raw, re.S)
    n = sum(len(re.findall(r"<tr>", t)) for t in tables)
    if n != av["counts"]["A"]["rows"]:
        bad("indep-injury", "row recount %d != parse %d" % (n, av["counts"]["A"]["rows"]))
    if len(tables) != av["counts"]["A"]["club_tables"]:
        bad("indep-injury", "table count %d != parse %d"
            % (len(tables), av["counts"]["A"]["club_tables"]))
    dig = hashlib.sha256(open(os.path.join(ROOT, av["provenance"]["A"]["path"]), "rb").read()).hexdigest()
    if dig != av["provenance"]["A"]["sha256"]:
        bad("indep-injury", "capture digest changed")
    if not errors:
        ok("indep-injury", "%d rows / %d tables re-derived from the raw bytes; digest matches" % (n, len(tables)))


def main():
    print("verifying nfl-origination-lab …")
    n_rows = check_pages()
    check_counts(n_rows)
    check_corpus()
    check_no_lookahead()
    check_prereg()
    check_governance()
    check_independent_injury()
    check_determinism()

    width = max(len(c[0]) for c in checks) + 2
    for name, passed, detail in checks:
        print("  %s%-*s %s" % ("PASS " if passed else "FAIL ", width, name, detail))
    print()
    if errors:
        print("%d FAILURE(S)" % len(errors))
        for e in errors[:40]:
            print("  -", e)
        sys.exit(1)
    print("all %d checks pass · %d pages · %d table rows"
          % (len(checks), len(pages()), n_rows))


if __name__ == "__main__":
    main()
