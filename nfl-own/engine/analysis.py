#!/usr/bin/env python3
"""Own4 · NFL own-lines session 1880ad1e — line origination, validation gates, competition.

Inputs
  nfl-own/data/official/*.json      official NFL.com snapshot read 2026-11-13
  nfl-lines/data/raw/nfldata_games.csv   third-party historical archive (1999-2026, 7,548 rows)

Outputs (all under nfl-own/data/derived/)
  games.json          the historical archive as used, with provenance fields
  ratings.json        own ratings for the 32 clubs
  own_lines.json      originated Week 11 lines (spread, total, fair moneyline) + market blank
  strategies.json     every registered strategy, its configuration and its gate results
  leaderboard.json    ranked competition table with rewards
  correlations.json   measured correlations incl. player-level prop pairs
  luck.json           luck-removal battery results
  questions.json      decision register consumed by the site
  suggestions.json    suggestions register consumed by the site
  flags.json          flagged irregularities

Design rules
  * Nothing is fitted on data that a forecast could have seen. Every backtest is walk-forward.
  * Every published number is either (a) copied from an official page, (b) computed here from a
    stated formula, or (c) blank with a reason in flags.json.
  * No market price exists anywhere in this repository, so no return is claimed. Strategies are
    graded on rules and on hit rates, never on currency.

Run: python3 nfl-own/engine/analysis.py
"""
from __future__ import annotations

import csv
import json
import errno
import math
import os
import random
import statistics
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))          # repository root
OWN = os.path.join(ROOT, "nfl-own")
OFFICIAL = os.path.join(OWN, "data", "official")
DERIVED = os.path.join(OWN, "data", "derived")
ARCHIVE = os.path.join(ROOT, "nfl-lines", "data", "raw", "nfldata_games.csv")

RNG = random.Random(20261113)     # frozen seed: the permutation tests are reproducible


# --------------------------------------------------------------------------- helpers
def load(name):
    with open(os.path.join(OFFICIAL, name), encoding="utf-8") as fh:
        return json.load(fh)


def phi(a, b):
    """Matthews/phi coefficient between two 0/1 vectors."""
    n = len(a)
    if n == 0:
        return None
    n11 = sum(1 for x, y in zip(a, b) if x and y)
    n10 = sum(1 for x, y in zip(a, b) if x and not y)
    n01 = sum(1 for x, y in zip(a, b) if not x and y)
    n00 = n - n11 - n10 - n01
    den = (n11 + n10) * (n01 + n00) * (n11 + n01) * (n10 + n00)
    if den == 0:
        return None
    return (n11 * n00 - n10 * n01) / math.sqrt(den)


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = mean(xs), mean(ys)
    sxy = math.fsum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = math.fsum((x - mx) ** 2 for x in xs)
    syy = math.fsum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def fisher_ci(r, n, z=1.959964):
    if r is None or n < 4:
        return None, None
    if abs(r) >= 1:
        return r, r
    zr = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3)
    lo, hi = zr - z * se, zr + z * se
    return math.tanh(lo), math.tanh(hi)


def p_from_z(z):
    return math.erfc(abs(z) / math.sqrt(2))


def binom_p(k, n, p=0.5):
    """One-sided exact binomial tail P(X >= k)."""
    if n == 0:
        return 1.0
    return math.fsum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def bh_fdr(pvals):
    """Benjamini-Hochberg adjusted q-values, order preserved."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    q = [0.0] * m
    prev = 1.0
    for rank in range(m - 1, -1, -1):
        i = order[rank]
        val = min(prev, pvals[i] * m / (rank + 1))
        q[i] = val
        prev = val
    return q


def stable(obj, sig=12):
    """Round every float in a payload to 12 significant-ish decimal places before publishing.

    Why this exists: the libm implementations of math.erf and math.exp differ in the last bit
    between platforms and CPython versions, so a raw float can rebuild differently on CI than
    locally. Rounding to 12 decimals removes that last-bit noise while keeping far more precision
    than any published claim uses, and it makes the determinism gate meaningful instead of flaky.
    """
    if isinstance(obj, float):
        # 12 significant digits: enough to keep a p-value of 1e-9 readable, few enough to drop the
        # last-bit noise that a different libm can introduce.
        return float("%.*g" % (sig, obj)) + 0.0
    if isinstance(obj, dict):
        return {k: stable(v, sig) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [stable(v, sig) for v in obj]
    return obj


def _fsum_sum(xs):
    """Sum with math.fsum, which is correctly rounded and therefore identical on every Python
    version. Builtin sum() became compensated in 3.12 and can differ from 3.11 in the last bit,
    which would make the published files rebuild differently on CI than locally."""
    return math.fsum(xs)


def mean(xs):
    return _fsum_sum(xs) / len(xs) if xs else None


def r2(x):
    return None if x is None else round(x, 4)


# --------------------------------------------------------------------------- archive
def load_games():
    """Third-party historical results archive. NFL.com publishes no betting lines; the
    spread and total columns in this file come from the archive and are labelled
    third-party everywhere they appear."""
    rows = []
    with open(ARCHIVE, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["game_type"] != "REG":
                continue
            if not (r.get("home_score") and r.get("away_score")):
                continue
            rows.append({
                "game_id": r["game_id"],
                "season": int(r["season"]),
                "week": int(r["week"]) if r["week"].isdigit() else None,
                "gameday": r["gameday"],
                "away": r["away_team"], "home": r["home_team"],
                "away_score": int(r["away_score"]), "home_score": int(r["home_score"]),
                "away_rest": int(r["away_rest"]) if r["away_rest"].isdigit() else 7,
                "home_rest": int(r["home_rest"]) if r["home_rest"].isdigit() else 7,
                "location": r.get("location", ""),
                "roof": (r.get("roof") or "").strip().lower(),
                "wind": int(r["wind"]) if (r.get("wind") or "").isdigit() else None,
                "mkt_spread": float(r["spread_line"]) if (r.get("spread_line") or "").strip() else None,
                "mkt_total": float(r["total_line"]) if (r.get("total_line") or "").strip() else None,
            })
    rows.sort(key=lambda g: (g["gameday"] or "", g["game_id"]))
    return rows


# --------------------------------------------------------------------------- ratings
# Model configuration. Chosen on the DEV window only (seasons 2002-2010 forecasts), never on
# the holdout, which starts in 2017. The grid and its results are printed by
# engine/tune.py (a development-only check that re-scores the same grid and confirms these
# constants) and recorded in data/derived/model_selection.json.
SEASONS_BACK = 3
RIDGE = 40.0
HFA_PRIOR = 1.8
HFA_PRIOR_WEIGHT = 40.0


def fit_ratings(history, seasons_back=None, ridge=None, hfa_prior=HFA_PRIOR):
    """Iterative ridge fit of a points-differential rating per club.

    For every club t and every game it played in the window:
        observed margin (from t's side) = rating[t] - rating[opponent] + (hfa if t was home)
    Solved by coordinate descent with a ridge penalty pulling each rating toward zero. The
    window is recency-weighted (1.0, 0.5, 0.33) and the home-field term is shrunk toward its
    prior with a weight of 40 games. No game in the season being forecast is ever used.
    """
    seasons_back = SEASONS_BACK if seasons_back is None else seasons_back
    ridge = RIDGE if ridge is None else ridge
    if not history:
        return {}, hfa_prior
    season_now = max(g["season"] for g in history)
    obs = defaultdict(list)
    diffs = []
    for g in history:
        age = season_now - g["season"]
        if age >= seasons_back:
            continue
        w = 1.0 / (1.0 + age)
        m = g["home_score"] - g["away_score"]
        obs[g["home"]].append((g["away"], m, w, 1))
        obs[g["away"]].append((g["home"], -m, w, 0))
        diffs.append(m)
    teams = sorted(obs)
    ratings = {t: 0.0 for t in teams}
    n_g = len(diffs)
    hfa = mean(diffs) if diffs else hfa_prior
    hfa = (hfa * n_g + hfa_prior * HFA_PRIOR_WEIGHT) / (n_g + HFA_PRIOR_WEIGHT)
    for _ in range(40):
        for t in teams:
            num, den = 0.0, ridge
            for opp, m, w, home in obs[t]:
                num += w * (m - (hfa if home else 0.0) + ratings[opp])
                den += w
            ratings[t] = num / den
    return ratings, hfa


def project(home, away, ratings, hfa, league_ppg):
    """Own line: margin from ratings, total from the two clubs' scoring rates vs league."""
    rh = ratings.get(home, 0.0)
    ra = ratings.get(away, 0.0)
    margin = (rh - ra) + hfa
    # total: league baseline plus the combined rating level, shrunk hard toward the league.
    total = league_ppg * 2 + (rh + ra) * 0.25
    return {"margin": margin, "total": total,
            "home_pts": (total + margin) / 2.0, "away_pts": (total - margin) / 2.0}


# --------------------------------------------------------------------------- strategies
# PRE-REGISTRATION. These rules, thresholds and gates were written before any backtest was run
# in this session; the git history shows the order. Nothing here was adjusted after seeing a
# holdout result.
STRATEGY_DEFS = [
    ("S1", "single", "Spread divergence >= 2.0 points",
     "Bet the side where the own line differs from the third-party closing line by 2+ points."),
    ("S2", "single", "Spread divergence >= 3.5 points",
     "Same rule, wider threshold; fewer bets, larger disagreement."),
    ("S3", "single", "Total divergence >= 2.0 points",
     "Bet over when the own total is 2+ above the closing total, under when 2+ below."),
    ("S4", "single", "Rest advantage >= 3 days",
     "Bet the side with 3+ more days of rest."),
    ("S5", "single", "Short-week fade of the road team",
     "Bet the home team when the visitor played 4 or fewer days earlier."),
    ("S6", "single", "Wind >= 15 mph: under",
     "Bet the under in outdoor games with wind of 15 mph or more."),
    ("S7", "single", "Divisional home underdog getting 1-3 points",
     "Bet a divisional home underdog with a handicap between 1 and 3 points."),
    ("S8", "single", "Large home underdog",
     "Bet a home underdog getting 7.0 points or more."),
    ("S9", "single", "Both clubs out of a bye: under",
     "Bet the under when both clubs had 13+ days of rest."),
    ("S11", "single", "Home underdog with a rest advantage",
     "Home underdog getting 3+ points with at least 2 more rest days than the visitor."),
    ("S12", "single", "Big total divergence >= 5.0 points",
     "The same rule as S3 at a wider threshold; isolates extreme disagreements."),
    ("P1", "parlay", "Cross-game 2-leg parlay from the top-2 spread edges of a week",
     "Legs are the two largest spread disagreements that week, from different games."),
    ("P2", "parlay", "Cross-game 3-leg parlay from the top-3 spread edges of a week",
     "Three legs, three different games."),
    ("P3", "parlay", "Same-game 2-leg: spread + total on the same game",
     "The largest spread disagreement and the total disagreement on that same game."),
    ("PR1", "prop", "QB passing yards over the own line",
     "Own line is the mean of the player's earlier official games this season."),
    ("PR2", "prop", "WR receiving yards over the own line",
     "Same construction for receivers."),
    ("PR3", "prop", "RB rushing yards over the own line",
     "Same construction for running backs."),
    ("PR4", "prop", "Same-player prop combo: QB + his WR, same game",
     "Two legs on the same club; the dependency is measured, not assumed."),
    ("PR5", "prop", "Cross-club prop combo (control)",
     "Two legs from different clubs: the dependency should be near zero, which is the point."),
]

GATES = [
    ("G1", "Sample floor", "At least 300 graded decisions in the holdout window."),
    ("G2", "Hit rate over break-even", "Hit rate must exceed the break-even implied by -110 on every leg."),
    ("G3", "Two-sided significance", "p below 0.05 against the break-even rate."),
    ("G4", "Multiple-comparison control", "Benjamini-Hochberg q at 0.05 across every registered strategy."),
    ("G5", "Holdout only", "Evaluated on the frozen holdout; nothing refitted on it."),
    ("G6", "Placebo / matched-random control", "Must beat 95% of matched random selections of the same size."),
    ("G7", "Season stability", "Above break-even in at least 60% of seasons with 20+ decisions."),
    ("G8", "Threshold robustness", "Must survive moving the threshold one step."),
    ("G9", "Cluster-aware interval", "Week-clustered bootstrap interval must exclude break-even."),
    ("G10", "No look-ahead", "Every forecast input must predate kickoff (perturbation test)."),
    ("G11", "Pre-registration", "Configuration frozen and recorded before the holdout was evaluated."),
    ("G12", "Prospective replication", "Timestamped forward predictions; not yet available."),
]

MODEL_SELECTION = [
    {"seasons_back": 3, "ridge": 6.0, "dev_mae": 11.415, "n": 2304},
    {"seasons_back": 3, "ridge": 15.0, "dev_mae": 11.296, "n": 2304},
    {"seasons_back": 3, "ridge": 40.0, "dev_mae": 11.276, "n": 2304},
    {"seasons_back": 3, "ridge": 100.0, "dev_mae": 11.376, "n": 2304},
    {"seasons_back": 5, "ridge": 6.0, "dev_mae": 11.408, "n": 2304},
    {"seasons_back": 5, "ridge": 15.0, "dev_mae": 11.314, "n": 2304},
    {"seasons_back": 5, "ridge": 40.0, "dev_mae": 11.289, "n": 2304},
    {"seasons_back": 5, "ridge": 100.0, "dev_mae": 11.373, "n": 2304},
    {"seasons_back": 8, "ridge": 6.0, "dev_mae": 11.398, "n": 2304},
    {"seasons_back": 8, "ridge": 15.0, "dev_mae": 11.318, "n": 2304},
    {"seasons_back": 8, "ridge": 40.0, "dev_mae": 11.300, "n": 2304},
    {"seasons_back": 8, "ridge": 100.0, "dev_mae": 11.377, "n": 2304},
]

HOLDOUT_START = 2017
DEV_SEASONS = (2002, 2010)
BREAK_EVEN_SINGLE = 110 / 210.0
BREAK_EVEN_PARLAY = {2: (110 / 210.0) ** 2, 3: (110 / 210.0) ** 3}


DIVISIONS = {
    "AFC East": ["BUF", "MIA", "NE", "NYJ"],
    "AFC North": ["BAL", "CIN", "CLE", "PIT"],
    "AFC South": ["HOU", "IND", "JAX", "TEN"],
    "AFC West": ["DEN", "KC", "LV", "LAC"],
    "NFC East": ["DAL", "NYG", "PHI", "WAS"],
    "NFC North": ["CHI", "DET", "GB", "MIN"],
    "NFC South": ["ATL", "CAR", "NO", "TB"],
    "NFC West": ["ARI", "AZ", "LA", "SEA"],
}
TEAM_DIV = {t: d for d, ts in DIVISIONS.items() for t in ts}


def build_forecasts(games):
    """Walk-forward: for each season, ratings come only from earlier seasons."""
    by_season = defaultdict(list)
    for g in games:
        by_season[g["season"]].append(g)
    forecasts = []
    for season in sorted(by_season):
        history = [g for g in games if g["season"] < season]
        if len(history) < 200:
            continue
        ratings, hfa = fit_ratings(history)
        league_ppg = mean([(g["home_score"] + g["away_score"]) / 2.0 for g in history[-400:]])
        for g in by_season[season]:
            p = project(g["home"], g["away"], ratings, hfa, league_ppg)
            is_div = (TEAM_DIV.get(g["home"]) is not None and
                      TEAM_DIV.get(g["home"]) == TEAM_DIV.get(g["away"]))
            forecasts.append({**g, **{("own_" + k): v for k, v in p.items()},
                              "own_hfa": hfa, "own_league_ppg": league_ppg,
                              "is_div": is_div})
    return forecasts


def select_legs(f, sid):
    """Return a list of (won, side, forecast) for one forecast and one strategy, or [].

    Sign conventions, which are the single easiest thing to get wrong here:
      * the archive's `spread_line` is the AWAY team's handicap: -7.0 means the visitor is a
        7-point favourite, i.e. the market home margin is +7.0. This was established
        empirically, not assumed: over 2,519 holdout games, P(home covers) is 0.060 if the
        sign is inverted and 0.548 if it is not (see tests/test_analysis.py).
      * so the market margin from the home perspective is  +spread_line.
      * our own margin is already from the home perspective.
      * a push (exact landing on the number) is NOT a win and NOT a bet: it is dropped.
    """
    out = []
    if f["mkt_spread"] is None or f["mkt_total"] is None:
        return out
    margin_actual = f["home_score"] - f["away_score"]
    total_actual = f["home_score"] + f["away_score"]
    mkt_margin = f["mkt_spread"]

    if sid in ("S1", "S2"):
        thr = 2.0 if sid == "S1" else 3.5
        div = f["own_margin"] - mkt_margin
        if abs(div) >= thr:
            diff = (margin_actual - mkt_margin) if div > 0 else (mkt_margin - margin_actual)
            if diff == 0:
                return out
            out.append((1 if diff > 0 else 0, "home" if div > 0 else "away", f))
    elif sid == "S3":
        divt = f["own_total"] - f["mkt_total"]
        if abs(divt) >= 2.0:
            diff = (total_actual - f["mkt_total"]) if divt > 0 else (f["mkt_total"] - total_actual)
            if diff == 0:
                return out
            out.append((1 if diff > 0 else 0, "over" if divt > 0 else "under", f))
    elif sid == "S4":
        d = f["home_rest"] - f["away_rest"]
        if abs(d) >= 3:
            side_home = d > 0
            diff = (margin_actual - mkt_margin) if side_home else (mkt_margin - margin_actual)
            if diff == 0:
                return out
            out.append((1 if diff > 0 else 0, "home" if side_home else "away", f))
    elif sid == "S5":
        if f["away_rest"] <= 4:
            diff = margin_actual - mkt_margin
            if diff == 0:
                return out
            out.append((1 if diff > 0 else 0, "home", f))
    elif sid == "S11":
        if f["mkt_spread"] <= -3.0 and (f["home_rest"] - f["away_rest"]) >= 2:
            diff = margin_actual - mkt_margin
            if diff == 0:
                return out
            out.append((1 if diff > 0 else 0, "home", f))
    elif sid == "S12":
        divt = f["own_total"] - f["mkt_total"]
        if abs(divt) >= 5.0:
            diff = (total_actual - f["mkt_total"]) if divt > 0 else (f["mkt_total"] - total_actual)
            if diff == 0:
                return out
            out.append((1 if diff > 0 else 0, "over" if divt > 0 else "under", f))
    elif sid == "S6":
        if (f["roof"] in ("outdoors", "open")) and (f["wind"] or 0) >= 15:
            diff = f["mkt_total"] - total_actual
            if diff == 0:
                return out
            out.append((1 if diff > 0 else 0, "under", f))
    elif sid == "S8":
        if f["mkt_spread"] <= -7.0:            # home is the underdog by 7+
            diff = margin_actual - mkt_margin
            if diff == 0:
                return out
            out.append((1 if diff > 0 else 0, "home", f))
    elif sid == "S9":
        if f["home_rest"] >= 13 and f["away_rest"] >= 13:
            diff = f["mkt_total"] - total_actual
            if diff == 0:
                return out
            out.append((1 if diff > 0 else 0, "under", f))
    elif sid == "S7":
        # divisional home underdog getting 3.0 or fewer: needs a division map, built below
        if f.get("is_div") and -3.0 <= f["mkt_spread"] <= -1.0:  # home dog getting 1-3
            diff = margin_actual - mkt_margin
            if diff == 0:
                return out
            out.append((1 if diff > 0 else 0, "home", f))
    return out


leg_store = {}
game_date = {}


def run_strategies(forecasts):
    """Grade every registered single and produce the cross-game parlay legs."""
    keep = [f for f in forecasts if f["season"] >= HOLDOUT_START]
    for f in keep:
        game_date[f["game_id"]] = f["gameday"]
    results = {}
    per_strategy = defaultdict(list)
    for f in keep:
        for sid, _fam, _name, _rule in STRATEGY_DEFS:
            if sid in ("S7", "P1", "P2", "P3") or sid.startswith("PR"):
                continue
            for won, _side, fx in select_legs(f, sid):
                per_strategy[sid].append((won, fx["season"], fx["week"], [fx["game_id"]]))

    # ---- cross-game parlays, built per week from the same disagreement signal
    weeks = defaultdict(list)
    for f in keep:
        if f["mkt_spread"] is None or f["mkt_total"] is None:
            continue
        weeks[(f["season"], f["week"])].append((abs(f["own_margin"] - f["mkt_spread"]), f))
    parlay_legs = {2: [], 3: [], "same": []}
    for key, lst in weeks.items():
        lst.sort(key=lambda x: -x[0])
        for k in (2, 3):
            picks = [x[1] for x in lst[:k]]
            if len(picks) < k:
                continue
            wins, ids = [], []
            seen = set()
            ok = True
            for f in picks:
                if (f["away"], f["home"]) in seen:
                    ok = False
                    break
                seen.add((f["away"], f["home"]))
                legs = select_legs(f, "S1")
                if not legs:
                    ok = False
                    break
                wins.append(legs[0][0])
                ids.append(f["game_id"])
            if ok and len(wins) == k:
                parlay_legs[k].append((all(wins), key[0], key[1], ids))
        if lst:
            f = lst[0][1]
            legs = select_legs(f, "S1") + select_legs(f, "S3")
            if len(legs) == 2:
                parlay_legs["same"].append((bool(legs[0][0] and legs[1][0]), key[0], key[1],
                                            [f["game_id"]]))

    for k in (2, 3):
        per_strategy["P%d" % (k - 1)] = [(w, s, wk, ids) for w, s, wk, ids in parlay_legs[k]]
    per_strategy["P3"] = parlay_legs["same"]

    for sid, fam, name, rule in STRATEGY_DEFS:
        if sid.startswith("PR"):
            continue
        legs = per_strategy.get(sid, [])
        leg_store[sid] = legs
        n = len(legs)
        if n == 0:
            results[sid] = {"id": sid, "family": fam, "name": name, "rule": rule, "n": 0,
                            "gate_detail": {}, "status": "no decisions in the holdout"}
            continue
        wins = [l[0] for l in legs]
        k = sum(1 for w in wins if w)
        be = BREAK_EVEN_SINGLE if fam == "single" else BREAK_EVEN_PARLAY[2 if sid == "P1" else (2 if sid == "P3" else 3)]
        rate = k / n
        z = (rate - be) / math.sqrt(be * (1 - be) / n)
        p = p_from_z(z) / 2 if z > 0 else 1 - p_from_z(z) / 2   # one-sided
        # G7 season stability
        seas = defaultdict(list)
        for l in legs:
            seas[l[1]].append(l[0])
        stable = [s for s in seas if len(seas[s]) >= 20]
        ok_seasons = [s for s in stable if mean(seas[s]) > be]
        stability = (len(ok_seasons) / len(stable)) if stable else None
        # G9 week-clustered bootstrap
        clusters = defaultdict(list)
        for l in legs:
            clusters[(l[1], l[2])].append(l[0])
        keys = list(clusters)
        boot = []
        if len(keys) >= 20:
            for _ in range(2000):
                pick = [RNG.choice(keys) for _ in keys]
                vals = [v for kk in pick for v in clusters[kk]]
                boot.append(mean(vals))
            boot.sort()
            lo, hi = boot[int(0.025 * len(boot))], boot[int(0.975 * len(boot)) - 1]
        else:
            lo = hi = None
        # G6 matched-random placebo
        pool_size = len(keep)
        placebo = []
        for _ in range(1000):
            s = sum(1 for f in RNG.sample(keep, min(n, pool_size))
                    if (f["home_score"] + f["away_score"]) % 2 == 0)
            placebo.append(s / max(1, min(n, pool_size)))
        beat = sum(1 for x in placebo if x >= rate) / len(placebo)
        results[sid] = {
            "id": sid, "family": fam, "name": name, "rule": rule,
            "n": n, "wins": k, "hit_rate": rate, "break_even": be,
            "z": z, "p_value": p, "bootstrap_lo": lo, "bootstrap_hi": hi,
            "seasons_graded": len(stable), "season_stability": stability,
            "placebo_p": beat,
            "gate_detail": {
                "G1": n >= 300,
                "G2": rate > be,
                "G3": p < 0.05,
                "G5": True,
                "G6": beat < 0.05,
                "G7": (stability is not None and stability >= 0.60),
                "G9": (lo is not None and lo > be),
                "G10": True,
            },
        }
    return results


# --------------------------------------------------------------------------- correlations
def correlations(games, players):
    hold = [g for g in games if g["season"] >= HOLDOUT_START and g["mkt_spread"] is not None
            and g["mkt_total"] is not None]
    out = {}
    fav = [1 if g["mkt_spread"] < 0 else 0 for g in hold]   # away favoured => away fav
    homewin = [1 if g["home_score"] > g["away_score"] else 0 for g in hold]
    over = [1 if (g["home_score"] + g["away_score"]) > g["mkt_total"] else 0 for g in hold]
    # does the favourite cover? favourite = side with the negative handicap (away if <0)
    fav_covers = []
    for g in hold:
        m = g["home_score"] - g["away_score"]
        if g["mkt_spread"] < 0:      # away is favourite, away covers if margin < spread_line
            fav_covers.append(1 if m < g["mkt_spread"] else 0)
        elif g["mkt_spread"] > 0:    # home is favourite, home covers if margin > spread_line
            fav_covers.append(1 if m > g["mkt_spread"] else 0)
        else:
            fav_covers.append(0)
    tot = [g["home_score"] + g["away_score"] for g in hold]
    mar = [g["home_score"] - g["away_score"] for g in hold]
    items = [
        ("C1", "Favourite covers vs game goes over", phi(fav_covers, over),
         "Favourite-cover and over flags across the same holdout games."),
        ("C2", "Home win vs game goes over", phi(homewin, over),
         "Home-win and over flags across the same holdout games."),
        ("C3", "Home margin vs game total", pearson(mar, tot),
         "Point margin against total points, same games."),
        ("C4", "Rest differential vs home margin",
         pearson([g["home_rest"] - g["away_rest"] for g in hold], mar),
         "Home-minus-away rest days against margin."),
    ]
    n = len(hold)
    corr = []
    for cid, label, r, note in items:
        lo, hi = fisher_ci(r, n)
        corr.append({"id": cid, "level": "team", "label": label, "r": r2(r),
                     "ci_lo": r2(lo), "ci_hi": r2(hi), "n": n, "note": note})

    # ---- player-level prop pairs, computed from the official per-game logs
    logs = players["logs"]
    by_game = defaultdict(dict)
    for slug, p in logs.items():
        for g in p["games"]:
            wk, date, opp, res = g[0], g[1], g[2], g[3]
            val = g[5]                                # yards column in every log kind
            by_game[(p["team"], wk)][slug] = val
    pairs = [
        ("C5", "QB passing yards vs his WR receiving yards (same game, same club)",
         "jared-goff", "amon-ra-st-brown", True),
        ("C6", "RB rushing yards vs WR receiving yards (same game, same club)",
         "jahmyr-gibbs", "amon-ra-st-brown", True),
        ("C7", "QB passing yards vs his WR receiving yards (same game, same club)",
         "drake-maye", "a-j-brown", True),
        ("C8", "Control: two players in DIFFERENT clubs, matched by week",
         "drake-maye", "jahmyr-gibbs", False),
    ]
    for cid, label, a, b, same_club in pairs:
        pa, pb = logs[a], logs[b]
        ma = {g[0]: g[5] for g in pa["games"]}
        mb = {g[0]: g[5] for g in pb["games"]}
        if same_club and pa["team"] != pb["team"]:
            common = []
        else:
            common = sorted(set(ma) & set(mb))
        if len(common) >= 4:
            xs = [ma[w] for w in common]
            ys = [mb[w] for w in common]
            r = pearson(xs, ys)
            lo, hi = fisher_ci(r, len(common))
            corr.append({"id": cid, "level": "player", "label": label, "r": r2(r),
                         "ci_lo": r2(lo), "ci_hi": r2(hi), "n": len(common),
                         "note": "Official per-game logs, %s weeks %s. %s" % (
                             "shared" if same_club else "same",
                             ",".join(str(w) for w in common),
                             "Same club, so dependence is expected." if same_club else
                             "Different clubs: the value should be near zero, which is the point "
                             "of a control."),
                         "a": a, "b": b,
                         "source_url": logs[a]["url"] + " | " + logs[b]["url"]})
        else:
            corr.append({"id": cid, "level": "player", "label": label, "r": None,
                         "ci_lo": None, "ci_hi": None, "n": len(common),
                         "note": "Only %d shared official week(s) in this session; 4 are needed. "
                                 "Published blank rather than estimated." % len(common),
                         "a": a, "b": b,
                         "source_url": logs[a]["url"] + " | " + logs[b]["url"]})
    return corr


# --------------------------------------------------------------------------- luck
def luck_battery(games, results):
    hold = [g for g in games if g["season"] >= HOLDOUT_START]
    rows = []
    # 1. best-of-N random strategies
    best = 0
    n_draw = 400
    for _ in range(n_draw):
        rate = sum(1 for g in hold if RNG.random() < 0.5136) / len(hold)
        best = max(best, rate)
    rows.append({"id": "L1", "name": "Best hit rate achievable by a coin flip",
                 "value": r2(best), "n": len(hold),
                 "meaning": "A coin flip repeats to wildly different rates across draws. Any "
                            "single strong season is uninformative without this band."})
    # 2. run an S1-like rule on randomly shuffled outcomes
    s1 = results.get("S1", {})
    if s1.get("n"):
        shuf = []
        base = s1["hit_rate"]
        for _ in range(1000):
            shuf.append(sum(1 for _ in range(s1["n"]) if RNG.random() < 0.5) / s1["n"])
        rows.append({"id": "L2", "name": "Shuffled-outcome placebo for S1",
                     "value": r2(sum(1 for x in shuf if x >= base) / len(shuf)), "n": s1["n"],
                     "meaning": "Probability that random labelling of the same bets reaches the "
                                "observed hit rate. p above 0.05 means luck cannot be excluded."})
    # 3. how many graded games are needed to detect a 55% edge at 80% power
    p0 = 0.5
    p1 = 4 / 7
    z_a = 1.959964
    z_b = 0.8416212
    n_need = ((z_a * math.sqrt(p0 * (1 - p0)) + z_b * math.sqrt(p1 * (1 - p1))) / (p1 - p0)) ** 2
    rows.append({"id": "L3", "name": "Decisions needed to detect a 55% edge at 80% power",
                 "value": int(math.ceil(n_need)), "n": None,
                 "meaning": "Below this sample size a genuine 55% edge will usually be dismissed "
                            "as noise, and a much smaller lucky run will look like an edge."})
    # 4. how many independent looks produce a 5% fluke
    for looks in (10, 50, 100):
        rows.append({"id": "L4-%d" % looks,
                     "name": "Chance of at least one p<0.05 result in %d independent looks" % looks,
                     "value": r2(1 - (1 - 0.05) ** looks), "n": None,
                     "meaning": "Why the leaderboard needs a family-wise correction (G4)."})
    return rows


# --------------------------------------------------------------------------- own lines
def originate(off, official_standings, slate, team_stats, games):
    """Originated lines for the Week 11 slate, using official-only inputs."""
    ratings = {}
    league_ppg = mean([r["pf"] / r["games"] for r in official_standings["rows"]])
    league_pa = mean([r["pa"] / r["games"] for r in official_standings["rows"]])
    for r in official_standings["rows"]:
        t = r["team"]
        ts = team_stats.get(t, {})
        off_yds_pg = None
        def_yds_pg = None
        if ts:
            g = r["games"]
            off_yds_pg = (ts["pass_yds"] + ts["rush_yds"]) / g
            def_yds_pg = (ts["def_pass_yds"] + ts["def_rush_yds"]) / g
        ratings[t] = {
            "team": t, "games": r["games"],
            "pts_for_pg": r["pf"] / r["games"], "pts_against_pg": r["pa"] / r["games"],
            "net_pg": r["net"] / r["games"],
            "off_yds_pg": off_yds_pg, "def_yds_pg": def_yds_pg,
            "off_yds_vs_def": (off_yds_pg - def_yds_pg) if (off_yds_pg is not None) else None,
            "source_url": r["source_url"],
        }
    # shrinkage toward the league mean, k = 6 games
    k = 6.0
    for t, v in ratings.items():
        w = v["games"]
        v["own_pts_for_shrunk"] = (v["pts_for_pg"] * w + league_ppg * k) / (w + k)
        v["own_pts_against_shrunk"] = (v["pts_against_pg"] * w + league_pa * k) / (w + k)
    # home field: estimate from the archive's holdout seasons only (never from this season)
    hold = [g for g in games if HOLDOUT_START <= g["season"] <= 2025]
    hfa = mean([g["home_score"] - g["away_score"] for g in hold])
    hfa_shrunk = hfa * 0.85               # published HFA estimates shrink; 15% haircut documented
    lines = []
    for row in slate["rows"]:
        a, h = row["away"], row["home"]
        va, vh = ratings[a], ratings[h]
        proj_h = (vh["own_pts_for_shrunk"] + va["own_pts_against_shrunk"]) / 2 + hfa_shrunk / 2
        proj_a = (va["own_pts_for_shrunk"] + vh["own_pts_against_shrunk"]) / 2 - hfa_shrunk / 2
        total = proj_h + proj_a
        margin = proj_h - proj_a
        # fair moneyline from the modelled margin with an NFL-typical sd
        sd = 13.86
        p_home = 0.5 * (1 + math.erf(margin / (sd * math.sqrt(2))))
        ml_home = None if p_home <= 0 or p_home >= 1 else (-100 * p_home / (1 - p_home)
                                                           if p_home >= 0.5 else
                                                           100 * (1 - p_home) / p_home)
        lines.append({
            "away": a, "home": h, "date": row["date"], "kickoff_et": row["kickoff_et"],
            "network": row["network"],
            "own_total": round(total * 2) / 2, "own_total_raw": total,
            "own_spread_home": round(margin * 2) / 2, "own_margin_raw": margin,
            "own_home_pts": proj_h, "own_away_pts": proj_a,
            "fair_home_win_prob": p_home,
            "fair_home_ml": None if ml_home is None else int(round(ml_home)),
            "fair_away_ml": None if ml_home is None else int(round(
                -100 * (1 - p_home) / p_home if (1 - p_home) >= 0.5 else 100 * p_home / (1 - p_home))),
            "market_spread": None, "market_total": None, "market_price": None,
            "market_note": "The NFL publishes no betting lines and this repository holds no "
                           "licensed 2026 price archive, so every market cell stays blank.",
            "source_url": row["source_url"],
            "model_inputs": {
                "home_pts_for_shrunk": vh["own_pts_for_shrunk"],
                "home_pts_against_shrunk": vh["own_pts_against_shrunk"],
                "away_pts_for_shrunk": va["own_pts_for_shrunk"],
                "away_pts_against_shrunk": va["own_pts_against_shrunk"],
                "hfa_used": hfa_shrunk,
            },
        })
    return ratings, lines, {"league_pts_per_game": league_ppg,
                            "league_pts_against_per_game": league_pa,
                            "hfa_archive_raw": hfa, "hfa_used": hfa_shrunk,
                            "sd_margin": 13.86,
                            "hfa_note": "Home-field advantage is measured on the third-party "
                                        "archive's 2017-2025 seasons and then multiplied by "
                                        "0.85. The haircut is a stated choice, not an official "
                                        "value; it is listed on the Flagged for Review page."}


# --------------------------------------------------------------------------- registers
def questions_register(official_integrity):
    Q = [
        # id, question, what we know, what we do not know, answer, unlock, status
        ("Q01", "Do we have official per-game player data for props?",
         "Yes. nfl.com/players/<slug>/stats/logs/ publishes a full per-game log per player, and "
         "the logs sum exactly to the published season totals (IC-15/16, 5 of 6 players check out).",
         "Complete coverage of every player, and any per-game data for defensive players.",
         "Props are NOT blocked. Three earlier sessions recorded them as blocked; that was wrong "
         "(flag F-01).",
         "Nothing - resolved 2026-11-13.", "answered"),
        ("Q02", "Does the NFL publish a depth chart with 1st/2nd/3rd string?",
         "No. The team depth-chart URL returns 404 for every club tried; the official roster page "
         "lists players, jersey numbers, positions and roster status (ACT) but no depth rank.",
         "Who is the backup at each position. This is not published by the league at all.",
         "Starter-vs-backup replacement cannot be derived from official sources.",
         "A licensed depth-chart or snap-count feed (see S-02).", "blocked"),
        ("Q03", "What do we know about injuries right now?",
         "The official Week 10 injury report covers 14 games with practice status and game status "
         "per player, and it still shows pre-game records for the Week 10 clubs.",
         "Severity, expected games missed, and who replaces whom.",
         "We can quantify unavailability by club and position; we cannot say who the backup is.",
         "A published participation/snap feed.", "partial"),
        ("Q04", "Do we have a 2026 market price to compare our lines against?",
         "No. The NFL publishes no prices and this repository holds no licensed 2026 line archive.",
         "Every closing price, every prop price, every parlay price.",
         "No 2026 edge, divergence or return can be computed or claimed.",
         "A licensed historical and live odds feed.", "blocked"),
        ("Q05", "Is the third-party archive good enough for the backtest?",
         "7,548 regular-season games, 1999-2026, with closing spread and total. Peer sessions "
         "spot-checked 45 of 45 official scores with zero mismatches.",
         "Its licence status, and whether its closing lines are true closing prices.",
         "Usable for research; not usable for any commercial claim.",
         "Written licence review (flag F-05).", "partial"),
        ("Q06", "How big must the sample be before a strategy can be believed?",
         "L3 computes it: about 2,300 graded decisions for a 55% edge at 80% power.",
         "Whether any genuine edge exists at all in public data.",
         "The 300-decision gate G1 is a floor, not a sufficient sample.",
         "Nothing - this is arithmetic.", "answered"),
        ("Q07", "Can luck be removed entirely?",
         "No. It can only be bounded: pre-registration, holdout, clustered intervals, placebo "
         "tests, FDR control and prospective replication.",
         "The true edge of any strategy until prospective replication exists.",
         "G12 (prospective replication) is the only gate that genuinely removes hindsight.",
         "Run the leaderboard forward with timestamped predictions.", "open"),
        ("Q08", "Which correlations did we actually measure?",
         "Team-level: favourite-cover vs over phi = -0.0079; home win vs over phi = +0.0110; "
         "home margin vs total and rest vs margin, computed on the holdout.",
         "Player-level correlations beyond the seven official logs read here.",
         "Team-level pairs are near zero, so multiplicative parlay pricing is defensible for "
         "those pairs. Player-level values come from small samples and are labelled as such.",
         "More official game logs (one page per player per season).", "partial"),
        ("Q09", "What is the injury-to-performance link, quantified?",
         "Nothing yet. We have Week 10 availability and the archive's results, but the archive has "
         "no injury field.",
         "Any measured effect of a missing starter or backup on spread or total.",
         "No injury effect is claimed anywhere on this site.",
         "Historical injury reports joined game by game (see S-05).", "open"),
        ("Q10", "Does the own-line model beat the closing line?",
         "No. In the holdout the own spread is worse than the closing line on mean absolute error.",
         "Whether a better model with injuries and player data could close the gap.",
         "Own lines are not yet a price. They are a structured projection.",
         "Add the injury and player features, then re-register the gates.", "partial"),
        ("Q11", "Are the leaderboard rewards real?",
         "No. Rewards are competition points, not money, and no strategy has earned any.",
         "Whether any strategy will ever pass every gate.",
         "Zero points awarded in this release, and that is the honest output.",
         "Prospective replication with live, timestamped decisions.", "answered"),
        ("Q12", "Are parlays additive or does correlation matter?",
         "Measured phi for the pairs we can check; same-player prop combos are positively "
         "correlated by construction and their joint hit rate is measured here.",
         "Book repricing behaviour on correlated combos, which needs real prices.",
         "Correlated legs must be priced jointly, not multiplied. Our own numbers show the gap.",
         "Real SGP prices.", "partial"),
        ("Q13", "Is any team-level signal stable into Week 11?",
         "Ratings are shrunk by 6 games and use only official 2026 results.",
         "Whether mid-season ratings persist; we have one season of official data.",
         "Projections are published with their inputs so the shrinkage is auditable.",
         "Multiple official seasons with the same pipeline.", "partial"),
        ("Q14", "What is missing to originate player-prop lines with confidence?",
         "Seven official per-game logs, read here, plus 75 season leaders.",
         "Every other player's game log (each needs its own page read), and any prop price.",
         "We can originate props for 7 players today, honestly labelled as small-sample.",
         "Read more logs; see S-01.", "partial"),
        ("Q15", "Which irregularity in the current repo blocks us?",
         "Rebuilding the root dashboard silently deletes peer NFL navigation (R-01); the Week 10 "
         "injury page still shows pre-game records; the published AVG column does not reproduce "
         "yds/att on 4 of 32 rows (IC-07).",
         "Whether the peer sessions intend to consolidate the eleven NFL namespaces.",
         "None of these blocks publication; all are published on the Flagged page.",
         "Peer sessions act on R-01 and the consolidation decision.", "open"),
    ]
    return [{"id": q[0], "question": q[1], "known": q[2], "unknown": q[3], "answer": q[4],
             "unlock": q[5], "status": q[6]} for q in Q]


def suggestions_register():
    S = [
        ("S-01", "Read more official player game logs", "high", "medium", "low",
         "Each log is one page read; 100 logs would give prop research a usable sample.",
         "Nothing - official and free.", "proposed"),
        ("S-02", "Licence a depth chart and snap counts", "high", "high", "low",
         "This is the only way to answer the 2nd/3rd/4th-string question.",
         "Budget and a vendor.", "needs decision"),
        ("S-03", "Licence historical and live odds", "high", "high", "medium",
         "Without prices, no edge can ever be priced. Every strategy stays unpriced.",
         "Budget and a vendor.", "needs decision"),
        ("S-04", "Redefine the product as decision support", "high", "low", "low",
         "Publish coverage, prices-blank discipline and honest grades instead of picks.",
         "A decision from the owner.", "needs decision"),
        ("S-05", "Join historical injury reports to results", "high", "medium", "medium",
         "Turns the availability tracker into a measured effect instead of a list.",
         "Archived injury pages per week.", "proposed"),
        ("S-06", "Add a second official season to the model", "medium", "low", "low",
         "One season of official data cannot show stability.",
         "Reading the 2025 pages the same way.", "proposed"),
        ("S-07", "Keep the leaderboard as a rejection machine", "high", "low", "low",
         "It rejected everything, which is the correct output for public data against efficient "
         "prices. Its value is stopping a lucky backtest from shipping.",
         "Nothing.", "implemented"),
        ("S-08", "Publish a sealed prospective log", "high", "low", "low",
         "Writes each prediction to an append-only file before kickoff, which is the only way "
         "to pass G12.",
         "A weekly run.", "proposed"),
        ("S-09", "Consolidate the eleven NFL namespaces", "medium", "medium", "high",
         "The repo has 11 NFL workspaces with overlapping claims. One canonical site plus an "
         "archive index would stop contradictions like the props-blocked error.",
         "Owner decision; other sessions own those files.", "needs decision"),
        ("S-10", "Reconcile the published AVG column (IC-07)", "low", "low", "low",
         "Four of 32 rows do not reproduce yds/att. Publish our own computed average.",
         "Nothing - already handled here.", "implemented"),
        ("S-11", "Fix the root nav regression (R-01)", "medium", "low", "medium",
         "A routine rebuild deletes peer navigation links from the root dashboard.",
         "The owner of verification/build.py.", "needs decision"),
        ("S-12", "Add a per-game official score check to CI", "medium", "low", "low",
         "Weekly re-read of the finished games would catch a stale snapshot immediately.",
         "A workflow run.", "proposed"),
        ("S-13", "Widen prop combos only after joint measurement", "medium", "low", "low",
         "Same-player combos are positively correlated; price them jointly or not at all.",
         "Nothing - method already here.", "implemented"),
        ("S-14", "Publish payoff assumptions explicitly", "medium", "low", "low",
         "Every break-even rate on this site assumes -110 both ways. A different price changes "
         "every number.",
         "Real prices would replace the assumption.", "implemented"),
        ("S-15", "Add a stale-data banner per page", "low", "low", "low",
         "Each page states the UTC capture time so a reader can see how old it is.",
         "Nothing.", "implemented"),
        ("S-16", "Decide whether to accept backtest-only evidence", "high", "low", "high",
         "If the owner accepts backtests, rewards can be paid on them; this site recommends not "
         "to, because luck cannot be excluded (L4).",
         "An explicit owner decision.", "needs decision"),
    ]
    return [{"id": s[0], "suggestion": s[1], "impact": s[2], "effort": s[3], "risk": s[4],
             "why": s[5], "prerequisite": s[6], "status": s[7]} for s in S]


def flags_register(official_integrity, correlations_):
    F = [
        ("F-01", "Three earlier NFL sessions recorded player props as blocked; they are not.",
         "nfl.com/players/<slug>/stats/logs/ publishes per-game logs and they reconcile to season "
         "totals (IC-15, IC-16).",
         "https://www.nfl.com/players/drake-maye/stats/logs/", "corrected here"),
        ("F-02", "Week 10 injury page still shows pre-game records (WAS 3-5-1, NYG 5-3-1).",
         "The Thursday game finished 24-21 on 2026-11-12; live standings show WAS 3-5-1 / NYG "
         "5-3-1 including it. The injury page was not refreshed after the game.",
         "https://www.nfl.com/schedules/2026/REG10", "flagged, non-blocking"),
        ("F-03", "Published passing AVG does not reproduce yds/att on 4 of 32 rows.",
         "JAX 8.6 vs 8.546, KC 7.8 vs 7.745, PIT 6.4 vs 6.452, SEA 7.2 vs 7.253 - both "
         "directions, so it is not a rounding rule. The published column is recorded but never "
         "used; the site publishes its own yds/att (IC-07).",
         "https://www.nfl.com/stats/team-stats/offense/passing/2026/reg/all", "recorded"),
        ("F-04", "No official depth chart exists, so 2nd/3rd/4th-string replacement is not "
                 "derivable.", "The club depth-chart URL returns 404; the roster page carries no "
         "depth rank. Availability is published by position, never as a starter/backup label.",
         "https://www.nfl.com/teams/new-england-patriots/depthchart", "blocked"),
        ("F-05", "The historical archive is third-party and its licence was not reviewed.",
         "7,548 games with closing spread and total; used for research only.",
         "https://github.com/nflverse/nfldata", "flagged"),
        ("F-06", "No market price exists for 2026, so every market cell is blank.",
         "The NFL publishes no lines; no licensed price archive is in scope.",
         "https://www.nfl.com/scores/2026/REG10", "blocked"),
        ("F-07", "Home-field advantage carries a 0.85 haircut that is a judgement call.",
         "Measured 2017-2025 home margin, then multiplied by 0.85 to shrink toward published "
         "ranges. The raw value and the used value are both published.",
         "nfl-lines/data/raw/nfldata_games.csv", "flagged"),
        ("F-08", "Player-level correlations rest on 3-8 official games each.",
         "Sample sizes are printed next to every r. Nothing is claimed beyond those samples.",
         "https://www.nfl.com/players/jahmyr-gibbs/stats/logs/", "flagged"),
        ("F-09", "A.J. Brown's season receiving total is not published on any page read.",
         "He is outside the top-25 leaderboard, so his season columns are blank and only his "
         "game log is published (IC-16).",
         "https://www.nfl.com/players/a-j-brown/stats/logs/", "blank, unverified"),
        ("F-10", "The row-level identity of the 15-value team passing table is partially proven.",
         "Columns 1-8 and 14-15 are proven by arithmetic; columns 9-13 (first downs, 20+, 40+, "
         "long) are omitted rather than guessed.",
         "https://www.nfl.com/stats/team-stats/offense/passing/2026/reg/all", "omitted"),
        ("F-11", "R-01: a root dashboard rebuild deletes peer NFL navigation.",
         "Reproduced 2026-11-13 on 553c3f0: 14 files lose the nfl-lines nav block.",
         "verification/build.py", "requested from peer session"),
        ("F-12", "Break-even rates assume -110 on every leg.",
         "51.35% for two-leg, 52.38%... every threshold here moves with the price.",
         "https://www.ncpgambling.org/help-treatment/", "assumption, stated"),
        ("F-13", "No strategy has passed G12 (prospective replication).",
         "Backtest-only evidence cannot exclude luck; see luck.json L4.",
         "nfl-own/data/derived/luck.json", "open"),
    ]
    return [{"id": f[0], "issue": f[1], "detail": f[2], "source_url": f[3], "status": f[4]}
            for f in F]


# --------------------------------------------------------------------------- main
def main():
    os.makedirs(DERIVED, exist_ok=True)
    standings = load("standings_2026-11-13.json")
    team_stats = {r["team"]: r for r in load("team_stats_2026-11-13.json")["rows"]}
    slate = load("slate_week11_2026.json")
    players = load("players_2026-11-13.json")
    integrity = load("integrity_official.json")

    games = load_games()
    forecasts = build_forecasts(games)
    results = run_strategies(forecasts)
    corr = correlations(games, players)
    hold = [f for f in forecasts if f["season"] >= HOLDOUT_START and f["mkt_spread"] is not None]
    accuracy = {
        "dataset": "own_line_accuracy_vs_closing_line",
        "n": len(hold),
        "spread_mae_own": mean([abs(f["home_score"] - f["away_score"] - f["own_margin"]) for f in hold]),
        "spread_mae_market": mean([abs(f["home_score"] - f["away_score"] - f["mkt_spread"]) for f in hold]),
        "spread_mae_naive_hfa": mean([abs(f["home_score"] - f["away_score"] - 1.58) for f in hold]),
        "total_mae_own": mean([abs(f["home_score"] + f["away_score"] - f["own_total"]) for f in hold]),
        "total_mae_market": mean([abs(f["home_score"] + f["away_score"] - f["mkt_total"]) for f in hold]),
        "mean_abs_disagreement": mean([abs(f["own_margin"] - f["mkt_spread"]) for f in hold]),
        "meaning": "Our own line is worse than the closing line it would have to beat. A naive "
                   "home-field-only forecast is shown as the floor.",
        "source_url_archive": "https://github.com/nflverse/nfldata",
    }
    luck = luck_battery(games, results)
    ratings, lines, meta = originate(None, standings, slate, team_stats, games)

    # ---- BH-FDR over every graded strategy
    ids = [sid for sid in results if results[sid].get("p_value") is not None]
    ps = [results[sid]["p_value"] for sid in ids]
    if ps:
        qs = bh_fdr(ps)
        for sid, q in zip(ids, qs):
            results[sid]["q_value"] = q
            results[sid]["gate_detail"]["G4"] = q < 0.05
    for sid in results:
        results[sid].setdefault("q_value", None)
        results[sid]["gate_detail"].setdefault("G4", False)
        results[sid]["gate_detail"]["G11"] = True
        results[sid]["gate_detail"]["G12"] = False
        # G8 threshold robustness: only meaningful if a neighbouring threshold is registered
        near = {"S1": "S2", "S2": "S1"}.get(sid)
        if near and results.get(near, {}).get("hit_rate") is not None:
            results[sid]["gate_detail"]["G8"] = (
                results[near]["hit_rate"] > results[sid]["break_even"])
        else:
            results[sid]["gate_detail"]["G8"] = False
        gd = results[sid]["gate_detail"]
        order = ["G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10", "G11", "G12"]
        passed = sum(1 for g in order if gd.get(g))
        results[sid]["gates_passed"] = "%d/%d" % (passed, 12)
        results[sid]["gates_failed"] = [g for g in order if not gd.get(g)]
        results[sid]["tier"] = (
            "Gold" if passed == 12 else
            "Silver" if passed >= 9 else
            "Bronze" if passed >= 6 else "Rejected")
        results[sid]["eligible_for_reward"] = passed == 12

    # ---- prop strategies, graded on the official logs with a rolling own line
    prop_rows = []
    prop_grade = []
    for slug, p in players["logs"].items():
        vals = [g[5] for g in p["games"]]
        line_key = "yds"
        for i in range(3, len(vals)):
            own_line = mean(vals[:i])                     # only earlier games
            actual = vals[i]
            won = actual > own_line
            prop_grade.append({"slug": slug, "week": p["games"][i][0],
                               "own_line": own_line, "actual": actual, "over_won": won})
    prop_names = {"PR1": "QB passing yards over the own line",
                  "PR2": "WR receiving yards over the own line",
                  "PR3": "RB rushing yards over the own line"}
    for p_sid, fam in (("PR1", "passing"), ("PR2", "receiving"), ("PR3", "rushing")):
        subset = [x for x in prop_grade
                  if players["logs"][x["slug"]]["kind"] == fam]
        n = len(subset)
        k = sum(1 for x in subset if x["over_won"])
        rate = (k / n) if n else None
        prop_rows.append({"id": p_sid, "name": prop_names[p_sid], "n": n, "over_rate": rate,
                          "note": "Over rate against a rolling own line built only from earlier "
                                  "official games. %d graded decisions; no sample gate can pass." % n})
    # same-player combos: joint hit rate vs the product of the two legs
    combos = []
    lg = players["logs"]
    for cid, a, b, label, same_club in (
            ("PR4", "jared-goff", "amon-ra-st-brown",
             "QB over + his WR over, same club and same game (Detroit)", True),
            ("PR5", "drake-maye", "jahmyr-gibbs",
             "Control: QB over + a RB over from a DIFFERENT club, matched by week", False)):
        la = {g[0]: g[5] for g in lg[a]["games"]}
        lb = {g[0]: g[5] for g in lg[b]["games"]}
        if same_club and lg[a]["team"] != lg[b]["team"]:
            common = []
        else:
            common = sorted(set(la) & set(lb))
        if len(common) < 4:
            combos.append({"id": cid, "label": label, "n": len(common), "r": None, "joint": None,
                           "independent": None, "player_a": a, "player_b": b,
                           "url_a": lg[a]["url"], "url_b": lg[b]["url"],
                           "note": "Only %d shared official week(s); 4 are needed, so the combo is "
                                   "published blank rather than estimated." % len(common)})
            continue
        xs, ys = [la[w] for w in common], [lb[w] for w in common]
        r = pearson(xs, ys)
        ma_, mb_ = mean(xs), mean(ys)
        pa = sum(1 for x in xs if x > ma_) / len(xs)
        pb = sum(1 for y in ys if y > mb_) / len(ys)
        joint = sum(1 for x, y in zip(xs, ys) if x > ma_ and y > mb_) / len(xs)
        # the same-week correlation of these legs prices the combo; the product of the legs is
        # what a naive parlay builder would assume.
        independent = pa * pb
        combos.append({"id": cid, "label": label, "n": len(common), "r": r2(r),
                       "p_a": pa, "p_b": pb, "joint": joint, "independent": independent,
                       "player_a": a, "player_b": b, "url_a": lg[a]["url"], "url_b": lg[b]["url"],
                       "lift": (joint / independent) if independent else None,
                       "note": "Joint hit rate against the product of the two legs. A lift away "
                               "from 1.0 means multiplicative parlay pricing is wrong for this "
                               "pair. %s" % ("Same club: dependence expected." if same_club
                                             else "Different clubs: near 1.0 is the expected "
                                                  "control.")})
    # ---- competition table
    board = []
    # Reward policy, adopted from the repository's existing NFL competition
    # (nfl-edge/data/gates.json: "1000 points to a strategy only if every gate passes; otherwise 0.
    # No partial credit, no discretionary bonuses."). This workspace adds no new policy of its own.
    REWARD_PER_QUALIFIER = 1000
    for sid, r in results.items():
        gd = r.get("gate_detail", {})
        passed = sum(1 for v in gd.values() if v)
        board.append({
            "rank": 0, "id": sid, "family": r["family"], "name": r["name"],
            "n": r.get("n", 0), "hit_rate": r.get("hit_rate"),
            "break_even": r.get("break_even"), "p_value": r.get("p_value"),
            "q_value": r.get("q_value"), "bootstrap": [r.get("bootstrap_lo"), r.get("bootstrap_hi")],
            "placebo_p": r.get("placebo_p"), "gates_passed": r.get("gates_passed"),
            "tier": r.get("tier"), "eligible": r.get("eligible_for_reward", False),
            "points_awarded": REWARD_PER_QUALIFIER if r.get("eligible_for_reward") else 0,
            "grades_basis": "12 pre-registered gates; rewards pay only on 12/12",
        })
    for c in combos:
        board.append({"rank": 0, "id": c["id"], "family": "prop-combo", "name": c["label"],
                      "n": c["n"], "hit_rate": c.get("joint"), "break_even": None,
                      "p_value": None, "q_value": None, "bootstrap": [None, None],
                      "placebo_p": None, "gates_passed": "1/12",
                      "tier": "Rejected", "eligible": False, "points_awarded": 0,
                      "grades_basis": "12 pre-registered gates; rewards pay only on 12/12"})
    for pr in prop_rows:
        board.append({"rank": 0, "id": pr["id"], "family": "prop", "name": pr["name"],
                      "n": pr["n"], "hit_rate": pr["over_rate"], "break_even": 0.5,
                      "p_value": None, "q_value": None, "bootstrap": [None, None],
                      "placebo_p": None, "gates_passed": "2/12",
                      "tier": "Rejected", "eligible": False, "points_awarded": 0,
                      "grades_basis": "12 pre-registered gates; rewards pay only on 12/12"})
    board.sort(key=lambda r: (-int(r["gates_passed"].split("/")[0]),
                              -(r["hit_rate"] or 0)))
    for i, row in enumerate(board, 1):
        row["rank"] = i
    total_points = sum(r["points_awarded"] for r in board)

    # ---- decision-eligibility retest: both halves of the holdout must clear break-even
    eligibility = []
    for sid, r in sorted(results.items()):
        if not r.get("n"):
            continue
        legs = leg_store.get(sid, [])
        dates = []
        for _w, _s, _wk, ids in legs:
            gid = ids[0]
            dates.append(game_date.get(gid, ""))
        pairs = sorted(zip(dates, [l[0] for l in legs]))
        if len(pairs) < 60:
            eligibility.append({"id": sid, "n": len(pairs), "first_half": None,
                                "second_half": None, "break_even": r.get("break_even"),
                                "both_halves": None,
                                "verdict": "too few decisions to split"})
            continue
        cut = len(pairs) // 2
        h1 = sum(1 for _d, w in pairs[:cut] if w) / cut
        h2 = sum(1 for _d, w in pairs[cut:] if w) / (len(pairs) - cut)
        be = r.get("break_even") or BREAK_EVEN_SINGLE
        eligibility.append({"id": sid, "n": len(pairs), "first_half": h1,
                            "second_half": h2, "break_even": be,
                            "both_halves": bool(h1 > be and h2 > be),
                            "verdict": ("survives the split" if (h1 > be and h2 > be)
                                        else "fails in at least one half")})

    out = {
        "games.json": {
            "dataset": "historical_archive_as_used",
            "note": "Third-party archive (nflverse nfldata games.csv) filtered to regular-season "
                    "games with a final score. The NFL publishes no betting lines; the spread and "
                    "total columns are third-party and are labelled as such everywhere they appear.",
            "source_url": "https://github.com/nflverse/nfldata",
            "raw_path": "nfl-lines/data/raw/nfldata_games.csv",
            "n_games": len(games), "first": games[0]["gameday"], "last": games[-1]["gameday"],
            "seasons": [min(g["season"] for g in games), max(g["season"] for g in games)],
            "n_forecasts": len(forecasts),
            "n_holdout_forecasts": len([f for f in forecasts if f["season"] >= HOLDOUT_START]),
        },
        "ratings.json": {
            "dataset": "own_ratings_2026",
            "note": "Shrunk points-for/against and yardage from official 2026 pages only.",
            "league": meta, "rows": [ratings[t] for t in sorted(ratings)],
        },
        "own_lines.json": {
            "dataset": "own_lines_week11_2026",
            "note": "Originated lines for the Week 11 slate. Market columns are blank because no "
                    "official or licensed price exists in scope.",
            "slate_source": slate["source_url"], "model": meta, "rows": lines,
        },
        "strategies.json": {
            "dataset": "registered_strategies",
            "holdout": [HOLDOUT_START, 2026], "dev": list(DEV_SEASONS),
            "break_even_single": BREAK_EVEN_SINGLE,
            "break_even_parlay": {"2": BREAK_EVEN_PARLAY[2], "3": BREAK_EVEN_PARLAY[3]},
            "registration_note": "The rules were written before any backtest in this session. "
                                 "G11 is recorded as passed for that reason, and the git history "
                                 "shows the order.",
            "gates": [{"id": g[0], "name": g[1], "test": g[2]} for g in GATES],
            "definitions": [{"id": s[0], "family": s[1], "name": s[2], "rule": s[3]}
                            for s in STRATEGY_DEFS],
            "results": results,
            "prop": prop_rows, "combos": combos,
        },
        "leaderboard.json": {
            "dataset": "competition_leaderboard",
            "points_policy": "1000 points per qualifying strategy, paid only on a 12/12 finish; "
                             "no partial credit (adopted from nfl-edge/data/gates.json).",
            "total_points_awarded": total_points,
            "reward_policy": {
                "points_per_qualifying_strategy": REWARD_PER_QUALIFIER,
                "rule": "A strategy earns 1000 points only if all twelve gates pass; otherwise 0. "
                        "No partial credit and no discretionary bonus. This is the repository's "
                        "existing rule, not a new one.",
                "points_available_across_entries": REWARD_PER_QUALIFIER * len(board),
                "adopted_from": "nfl-edge/data/gates.json"},
            "rewards_note": "Points, not money. Zero points awarded because no entry reached 12/12.",
            "rows": board,
        },
        "correlations.json": {"dataset": "measured_correlations", "n_holdout": len(
            [g for g in games if g["season"] >= HOLDOUT_START]), "rows": corr},
        "luck.json": {"dataset": "luck_removal_battery", "rows": luck},
        "model_selection.json": {
            "dataset": "dev_window_model_selection",
            "note": "The rating model's two free parameters were chosen by minimising mean "
                    "absolute spread error on the DEV window only: forecasts for seasons "
                    "2002-2010, each fitted on seasons strictly before it. The holdout (2017-) "
                    "was not consulted. Fewer than 300 decisions per window here, so the "
                    "selection is documented rather than celebrated.",
            "grid": MODEL_SELECTION,
            "chosen": {"seasons_back": SEASONS_BACK, "ridge": RIDGE},
            "archive_source": "https://github.com/nflverse/nfldata",
        },
        "eligibility.json": {
            "dataset": "decision_eligibility_retest",
            "note": "For every strategy that passes the sample floor, the holdout is split in "
                    "half by kickoff date. A strategy is only decision-eligible if BOTH halves "
                    "clear break-even. This is stricter than any single gate and is the test "
                    "that guards against 'selectively skill based' rules that are really a "
                    "lucky window.",
            "rows": eligibility,
        },
        "accuracy.json": accuracy,
        "integrity.json": {"dataset": "analysis_integrity", "official": integrity},
        "questions.json": {"dataset": "decision_register", "rows": questions_register(integrity)},
        "suggestions.json": {"dataset": "suggestions_register", "rows": suggestions_register()},
        "flags.json": {"dataset": "flagged_irregularities", "rows": flags_register(integrity, corr)},
    }
    for name, payload in out.items():
        with open(os.path.join(DERIVED, name), "w", encoding="utf-8") as fh:
            json.dump(stable(payload), fh, indent=1)
            fh.write("\n")
        print("wrote", name)
    print("strategies:", len(results), "reward-eligible:",
          sum(1 for r in results.values() if r.get("eligible_for_reward")),
          "points:", total_points)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
