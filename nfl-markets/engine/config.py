"""nfl-markets engine — shared configuration, paths, and conventions.

Session: arena/65c4a22e-own4 (2026-11-14)

CONVENTIONS (fixed here once, referenced everywhere):
- SPREAD SIGN: home-margin convention, matching nflverse `spread_line`
  ("a positive number means the home team was favored by that many points,
  a negative number means the away team was favored" — nfldata DATASETS.md).
  So fair_spread > 0 = home expected to win by that many points.
- TOTAL: combined points of both teams.
- ML: American odds for a prob p: p>=0.5 -> -(p/(1-p))*100 ; else +((1-p)/p)*100.
- ORIGINATION ORDER: side (spread) = seq 1, total = seq 2, moneyline = seq 3.
  Rationale documented in docs; every snapshot row carries market_seq.
- ORIGINATION TIME: model lines are computed walk-forward with a state
  cutoff of (gameday - 1 day) — "day-before-kickoff origination". No future
  information is used for any model_fair_line.
- SOURCE LABELS (same policy as peer namespaces, e.g. nfl-arena/data/sources.json):
  OFFICIAL    = published by the NFL (nfl.com).
  THIRD-PARTY = trusted analyst/archive source (nflverse/nfldata, ESPN), always labelled.
  REPO        = this repository's committed files (with provenance back to OFFICIAL/THIRD-PARTY).
  Anything not confirmable from an official source stays in the table but is
  labelled and flagged — never silently mixed in as official.
"""
import csv, json, os, math

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root
NS = os.path.join(ROOT, "nfl-markets")
RAW = os.path.join(NS, "data", "raw")
OUT = os.path.join(NS, "data")

# ---- data availability window (documented) ----
FIRST_ORIGINATION_SEASON = 2011   # model warmup uses 1999-2010 (documented in model.py)
CLOSE_ARCHIVE_FIRST_SEASON = 2006 # closing_lines.csv coverage (per-file, verified below)
OPEN_ARCHIVE_SEASONS = {2013: "sc_lines.csv", 2014: "sc_lines.csv", 2015: "sc_lines.csv",
                        2016: "sc_lines.csv", 2017: "sc_lines.csv", 2018: "sc_lines.csv",
                        2019: "sc_lines.csv", 2020: "sc_lines.csv", 2021: "initial_lines.csv"}

# ---- sources (single registry; every row links through these) ----
SOURCES = {
    "nfl_schedules": {
        "label": "OFFICIAL", "url": "https://www.nfl.com/schedules/",
        "used_for": "Official game schedule, kickoff dates, final scores (per-week pages under /schedules/{season}/REG{week}/)"},
    "nfl_standings": {
        "label": "OFFICIAL", "url": "https://www.nfl.com/standings/",
        "used_for": "Official standings used to verify the results feed (32/32 recomputation)"},
    "nfl_injuries": {
        "label": "OFFICIAL", "url": "https://www.nfl.com/injuries/",
        "used_for": "Official injury report: game status, practice status per player"},
    "nfl_data": {
        "label": "THIRD-PARTY", "url": "https://github.com/nflverse/nfldata",
        "used_for": "Machine-readable mirror of schedules/results (games.csv), archive lines (closing_lines.csv, initial_lines.csv, sc_lines.csv), standings, teams"},
    "nfl_data_games": {
        "label": "THIRD-PARTY", "url": "https://github.com/nflverse/nfldata/blob/master/data/games.csv",
        "used_for": "game rows: scores (official-origin), spread_line/total_line/moneylines (THIRD-PARTY market numbers)"},
    "nfl_data_closing": {
        "label": "THIRD-PARTY", "url": "https://github.com/nflverse/nfldata/blob/master/data/closing_lines.csv",
        "used_for": "Archived closing spread/total/ML with odds+outcome, seasons 2006-2018"},
    "nfl_data_initial": {
        "label": "THIRD-PARTY", "url": "https://github.com/nflverse/nfldata/blob/master/data/initial_lines.csv",
        "used_for": "Westgate (WSGT) opening spread+total, season 2021"},
    "nfl_data_sc": {
        "label": "THIRD-PARTY", "url": "https://github.com/nflverse/nfldata/blob/master/data/sc_lines.csv",
        "used_for": "Per-team spread archive, seasons 2013-2020 (capture time not published by the source — flagged)"},
    "espn_depth": {
        "label": "THIRD-PARTY", "url": "https://www.espn.com/nfl/depth",
        "used_for": "Depth-chart strings s1-s4 (replacement-depth computation); not published by the NFL — flagged"},
    "repo_nfl_arena_injuries": {
        "label": "REPO", "url": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-arena/data/raw/nfl_injuries_week10_2026.md",
        "used_for": "Verbatim capture of the official nfl.com Week-10 2026 injury report (peer session arena/d6c72eb4-own4, read-only reuse)"},
    "repo_nfl_arena_depth": {
        "label": "REPO", "url": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-arena/data/raw/espn_depth_week10.json",
        "used_for": "Verbatim capture of ESPN depth charts for 8 teams (peer session, read-only reuse)"},
    "repo_engine": {
        "label": "REPO", "url": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-markets/engine/model.py",
        "used_for": "This namespace's walk-forward origination model (model fair lines are this repository's own outputs)"},
}

def w(path, rows, fields):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=fields)
        wr.writeheader()
        for r in rows:
            wr.writerow({k: r.get(k, "") for k in fields})

def r(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))

def j(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, sort_keys=False)

def jl(path):
    with open(path) as f:
        return json.load(f)

def american_odds(p):
    """Fair American odds for win probability p in [0,1]."""
    p = min(max(p, 1e-6), 1 - 1e-6)
    if p >= 0.5:
        return -int(round(p / (1 - p) * 100))
    return int(round((1 - p) / p * 100))

def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def fisher_ci(rv, n):
    """95% CI for a Pearson/phi correlation via Fisher z (needs n>3)."""
    if n < 4 or abs(rv) >= 1:
        return None
    z = 0.5 * math.log((1 + rv) / (1 - rv))
    se = 1 / math.sqrt(n - 3)
    lo = math.tanh(z - 1.959964 * se)
    hi = math.tanh(z + 1.959964 * se)
    return [round(lo, 4), round(hi, 4)]

def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None, n
    mx = sum(xs) / n; my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx <= 0 or syy <= 0:
        return None, n
    return sxy / math.sqrt(sxx * syy), n
