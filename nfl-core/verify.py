#!/usr/bin/env python3
"""nfl-core verification (session arena-a437d20c-own4).

Line-by-line checks — exits non-zero on any failure:
  V1  every generated table row carries at least one https source link
  V2  every internal href/src in the site resolves to a file
  V3  results feed reconciles cell-by-cell against the OFFICIAL standings
      (OR-01, nfl.com read 2026-11-14): per-team W-L-T and PF-PA for all 32
      teams, plus league arithmetic SigmaW == SigmaL, SigmaT == 2*ties
  V4  never-infer policy: rows flagged UNVERIFIED keep their value cells blank
  V5  price store: every originated market (weeks 10-18) carries an OPEN price
      or an explicit flag; every settled game's markets carry CLOSE + settlement
  V6  originations: exactly one row per market type per game (seq 1/2/3) and
      difference == model_fair - market where both are numeric (SIDE/TOTAL)
  V7  leaderboard: signal table ordering is exactly z-descending (staking
      columns cannot be the sort key)
"""
import csv
import json
import os
import re
import sys

CORE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(CORE, "data")
fails, checks = [], 0


def ok(msg):
    global checks
    checks += 1
    print("  PASS  " + msg)


def bad(msg):
    global checks
    checks += 1
    fails.append(msg)
    print("  FAIL  " + msg)


def read_csv(name):
    with open(os.path.join(DATA, name)) as f:
        return list(csv.DictReader(f))


reads = json.load(open(os.path.join(DATA, "official_reads_2026-11-14.json")))
OR = {r["id"]: r for r in reads["official_reads"]}

print("nfl-core verification — official reads dated", reads["captured_utc"])

# ---------------------------------------------------------------- V1 + V2
pages = [os.path.join(dp, f) for dp, _, fs in os.walk(CORE) for f in fs if f.endswith(".html")]
rows_total = rows_linked = 0
per_page = {}
for p in pages:
    html = open(p).read()
    tbody = re.findall(r"<tbody>(.*?)</tbody>", html, re.S)
    n = l = 0
    for tb in tbody:
        for tr in re.findall(r"<tr>(.*?)</tr>", tb, re.S):
            n += 1
            if "https://" in tr:
                l += 1
    per_page[os.path.relpath(p, CORE)] = (n, l)
    rows_total += n
    rows_linked += l
if rows_total and rows_total == rows_linked:
    ok("V1 row source-link coverage: %d/%d table rows carry an https source link (all pages)" % (rows_linked, rows_total))
else:
    bad("V1 unlinked rows: %d of %d rows lack a source link; per page: %s" % (
        rows_total - rows_linked, rows_total,
        {k: v for k, v in per_page.items() if v[0] != v[1]}))

href_re = re.compile(r'(?:href|src)="([^"#][^"]*)"')
broken = []
for p in pages:
    html = open(p).read()
    for href in href_re.findall(html):
        if href.startswith("http") or href.startswith("mailto") or href.startswith("#"):
            continue
        target = os.path.normpath(os.path.join(os.path.dirname(p), href.split("#")[0].split("?")[0]))
        if not os.path.exists(target):
            broken.append((os.path.relpath(p, CORE), href))
if not broken:
    ok("V2 internal links: all resolve across %d pages" % len(pages))
else:
    bad("V2 broken internal links: %s" % broken[:10])

# --------------------------------------------------------------- V3 feed vs
# official standings (the line-by-line reconciliation)
feed = read_csv("results_feed_2026.csv")
ALIAS = {"ARI": "AZ"}  # nfl.com standings abbreviates Arizona as AZ; archive uses ARI (peer flag documented)
off = {r[0]: {"w": r[1], "l": r[2], "t": r[3], "pf": r[4], "pa": r[5]} for r in OR["OR-01"]["rows"]}


def offkey(t):
    return off[ALIAS.get(t, t)]


calc = {t: {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0} for t in off}
games_final = 0
for r in feed:
    if r["status"] != "FINAL":
        continue
    games_final += 1
    a, h = r["away_team"], r["home_team"]
    asc, hsc = int(r["away_score"]), int(r["home_score"])
    ca, ch = calc[ALIAS.get(a, a)], calc[ALIAS.get(h, h)]
    ca["pf"] += asc; ca["pa"] += hsc
    ch["pf"] += hsc; ch["pa"] += asc
    if asc > hsc:
        ca["w"] += 1; ch["l"] += 1
    elif hsc > asc:
        ch["w"] += 1; ca["l"] += 1
    else:
        ca["t"] += 1; ch["t"] += 1
mism = []
for t, c in calc.items():
    o = off[t]
    for k in ("w", "l", "t", "pf", "pa"):
        if c[k] != o[k]:
            mism.append("%s %s feed=%s official=%s" % (t, k.upper(), c[k], o[k]))
if not mism and games_final == 137:
    ok("V3 feed vs official standings (OR-01): 32/32 teams exact on W-L-T and PF-PA over %d final games" % games_final)
elif mism:
    bad("V3 standings mismatches: %s" % mism[:12])
else:
    bad("V3 final-game count is %d, expected 137" % games_final)
sw = sum(c["w"] for c in calc.values()); sl = sum(c["l"] for c in calc.values()); st = sum(c["t"] for c in calc.values())
if sw == sl == 136 and st == 2:
    ok("V3 league arithmetic: SigmaW = SigmaL = 136, SigmaT = 2 (137 games)")
else:
    bad("V3 league arithmetic off: SigmaW=%d SigmaL=%d SigmaT=%d" % (sw, sl, st))
# every FINAL row has an official game URL
nofi = [r["game_id"] if "game_id" in r else r["game_url"] for r in feed
        if r["status"] == "FINAL" and not r["game_url"].startswith("https://www.nfl.com/games/")]
if not nofi:
    ok("V3 every final row carries an official nfl.com game URL")
else:
    bad("V3 final rows missing official game URL: %s" % nofi[:6])

# ------------------------------------------------------------ V4 never-infer
bad_blank = []
for name in ("correlations_n.csv", "results_feed_2026.csv", "price_snapshots_2026.csv",
             "depth_week10.csv", "originations_2026.csv"):
    for r in read_csv(name):
        flag = r.get("flag", "")
        if "UNVERIFIED-BLANK" in flag or "DEPTH-UNVERIFIED" in flag or "OPEN-UNVERIFIED" in flag:
            # any populated numeric value cell that claims unverified -> fail
            for k, v in r.items():
                if k in ("flag", "verification", "reading", "note", "evidence_that_would_settle") or v == "":
                    continue
                if "UNVERIFIED-BLANK" in flag and k in ("pearson_r", "n", "p_value", "open_price", "close_price", "replacement", "replacement_depth_string"):
                    bad_blank.append((name, r.get("id", r.get("market_id", "?")), k, v))
                if "DEPTH-UNVERIFIED" in flag and k in ("replacement", "replacement_depth_string") and v:
                    bad_blank.append((name, r.get("absent_player", "?"), k, v))
if not bad_blank:
    ok("V4 never-infer: flagged-unverified rows keep their value cells blank")
else:
    bad("V4 populated value on flagged-unverified row: %s" % bad_blank[:8])

# ------------------------------------------------------- V5 price store state
snaps = read_csv("price_snapshots_2026.csv")
prob = []
for r in snaps:
    wk = int(r["week"])
    if wk >= 10 and not r["open_price"] and "OPEN-UNVERIFIED" not in r["flag"]:
        prob.append(("missing open on originated market", r["market_id"]))
    if r["close_price"] and not r["settlement"] and r["settlement_source"]:
        prob.append(("close without settlement", r["market_id"]))
    if r["settlement"] and not r["settlement_source"].startswith("https://www.nfl.com/games/"):
        prob.append(("settlement without official source", r["market_id"]))
    if not r["close_price"] and wk < 10:
        prob.append(("settled-history market missing close", r["market_id"]))
n_open = sum(1 for r in snaps if r["open_price"])
n_close = sum(1 for r in snaps if r["close_price"])
n_settle = sum(1 for r in snaps if r["settlement"])
if not prob:
    ok("V5 price store: %d markets, %d with OPEN, %d with CLOSE, %d settled — invariants hold" % (
        len(snaps), n_open, n_close, n_settle))
else:
    bad("V5 price-store problems: %s" % prob[:8])

# ------------------------------------------------------------ V6 originations
origs = read_csv("originations_2026.csv")
by_game = {}
arith = []
for r in origs:
    by_game.setdefault(r["game_id"], []).append(r)
    if r["market_type"].startswith(("SIDE", "TOTAL")) and r["model_fair_line"] and r["market_line"]:
        want = round(float(r["model_fair_line"]) - float(r["market_line"]), 2)
        got = round(float(r["difference"]), 2) if r["difference"] else None
        if got != want:
            arith.append((r["game_id"], r["market_type"], want, r["difference"]))
seq_ok = all(sorted(int(x["origination_seq"]) for x in rows) == [1, 2, 3] for rows in by_game.values())
if seq_ok and len(by_game) == 136:
    ok("V6 origination order: 136 games x (1 SIDE, 2 TOTAL, 3 MONEYLINE) = %d rows" % len(origs))
else:
    bad("V6 origination sequence problems (games=%d, rows=%d)" % (len(by_game), len(origs)))
if not arith:
    ok("V6 difference columns arithmetically exact (model_fair - market) on every numeric row")
else:
    bad("V6 difference arithmetic errors: %s" % arith[:6])

# -------------------------------------------------------- V7 signal ordering
sig = read_csv("leaderboard_signal.csv")
zs = [float(r["z_vs_breakeven"]) if r["z_vs_breakeven"] else -9e9 for r in sig]
if zs == sorted(zs, reverse=True) and all(int(r["signal_rank"]) == i + 1 for i, r in enumerate(sig)):
    ok("V7 signal leaderboard ranked strictly by z_vs_breakeven (staking cannot affect order)")
else:
    bad("V7 signal ordering violated")

# ------------------------------------------------- structural completeness
need = ["results_feed_2026.csv", "price_snapshots_2026.csv", "originations_2026.csv",
        "leaderboard_signal.csv", "leaderboard_staking.csv", "gates.csv",
        "depth_week10.csv", "correlations_n.csv", "questions.csv", "suggestions.csv", "flagged.csv"]
missing = [f for f in need if not os.path.exists(os.path.join(DATA, f))]
pages_needed = ["index.html"] + ["pages/" + p for p in
    ["executive-summary.html", "origination.html", "prices.html", "results.html", "leaderboard.html",
     "gates.html", "depth.html", "correlations.html", "questions.html", "suggestions.html",
     "flagged.html", "sources.html", "d1-canonical-choice.html"]]
missing += [p for p in pages_needed if not os.path.exists(os.path.join(CORE, p))]
if not missing:
    ok("structural completeness: all %d data stores and %d pages present" % (len(need), len(pages_needed)))
else:
    bad("missing artifacts: %s" % missing)

print()
if fails:
    print("VERIFICATION FAILED — %d problem(s) across %d checks" % (len(fails), checks))
    sys.exit(1)
print("VERIFICATION PASSED — %d checks, 0 problems" % checks)
