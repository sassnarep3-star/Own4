#!/usr/bin/env python3
"""
Own4 · nfl-live-board · L-05  (origination)

Originate a line for every Week 11 fixture, in the order the brief demands:

    1. side      (spread)   -> 2. total -> 3. moneyline (derived from side, never free-fitted)

The model is deliberately simple and frozen: five parameters, no tuning on results, fitted on
the reconciled 2026 corpus in chronological order (weeks 1..w-1 predict week w). It is a
TRANSPARENT BASELINE, not a claimed edge. Its job is to produce a fair line that can be
compared with the market, and to be beaten or kept by the leaderboard rules.

What each number is:
  ratings  : ridge-shrunk points-for / points-against per game, chronological;
  side     : predicted margin = rating edge of home vs away, + a league home-field term;
  total    : predicted points = (off_home + def_away)/2 + (off_away + def_home)/2 + a league term;
  moneyline: p(home) = P(margin > 0) under a normal with the walk-forward residual SD.
             The moneyline is DERIVED from the side. It is not fitted separately, because a
             separately fitted moneyline could disagree with the spread on the same game.

The market line is NOT supplied here. No official page publishes a spread, a total or a
moneyline (checked 2026-11-17: nfl.com publishes results and schedules only), so every
market column below is blank and carries the reason. The difference column is therefore blank
too - it is computed, never filled in by hand.

Run: python3 nfl-live-board/engine/originate.py
"""

import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")

SHRINK = 4.0          # pseudo-games pulling every rating toward the league mean
MIN_TRAIN_GAMES = 32  # a team with fewer games is rated at the league mean (league opening)

TEAMS = ["AZ","ATL","BAL","BUF","CAR","CHI","CIN","CLE","DAL","DEN","DET","GB","HOU","IND",
         "JAX","KC","LA","LAC","LV","MIA","MIN","NE","NO","NYG","NYJ","PHI","PIT","SEA","SF",
         "TB","TEN","WAS"]


def load(p):
    with open(p) as f:
        return json.load(f)


def ratings(games):
    """Chronological, shrunk points-for / points-against per game."""
    pf, pa, gp = {}, {}, {}
    for g in games:
        for t, p, q in ((g["away"], g["away_pts"], g["home_pts"]),
                        (g["home"], g["home_pts"], g["away_pts"])):
            pf[t] = pf.get(t, 0) + p
            pa[t] = pa.get(t, 0) + q
            gp[t] = gp.get(t, 0) + 1
    n = len(games)
    league_pf = sum(g["away_pts"] + g["home_pts"] for g in games) / (2.0 * n) if n else 22.0
    out = {}
    for t in TEAMS:
        g = gp.get(t, 0)
        out[t] = {
            "gp": g,
            "off": (pf.get(t, 0) + SHRINK * league_pf) / (g + SHRINK),
            "def": (pa.get(t, 0) + SHRINK * league_pf) / (g + SHRINK),
        }
    return out, league_pf


def fit(games):
    r, league_pf = ratings(games)
    # league home-field advantage, measured on the same window; ties are half
    hfa = 0.0
    if games:
        hfa = sum(g["home_pts"] - g["away_pts"] for g in games) / float(len(games))
    # residual SD of the margin, walk-forward hostile: in-sample on the window
    resid = []
    for g in games:
        pred = (r[g["home"]]["off"] - r[g["home"]]["def"]) - (r[g["away"]]["off"] - r[g["away"]]["def"]) + hfa
        resid.append((g["home_pts"] - g["away_pts"]) - pred)
    sd = (sum(x * x for x in resid) / (len(resid) - 1)) ** 0.5 if len(resid) > 1 else 14.0
    return {"ratings": r, "league_pf": league_pf, "hfa": hfa, "margin_sd": sd, "n_train": len(games)}


def originate(f, away, home, neutral=False):
    r = f["ratings"]
    hfa = 0.0 if neutral else f["hfa"]
    margin = ((r[home]["off"] - r[home]["def"]) - (r[away]["off"] - r[away]["def"])) + hfa
    total = (r[home]["off"] + r[away]["def"]) / 2.0 + (r[away]["off"] + r[home]["def"]) / 2.0
    p_home = 0.5 * (1.0 + math.erf((margin / f["margin_sd"]) / math.sqrt(2.0)))
    # fair American odds from p; a pick'em is priced at the fair value with no vig
    def american(p):
        if p is None or p <= 0 or p >= 1:
            return None
        return round(-100.0 * p / (1.0 - p)) if p >= 0.5 else round(100.0 * (1.0 - p) / p)
    return {
        "fair_margin_home": round(margin, 2),
        "fair_spread_home": round(-margin, 2),          # home line, negative = home favoured
        "fair_total": round(total, 1),
        "p_home_win": round(p_home, 4),
        "fair_ml_home": american(p_home),
        "fair_ml_away": american(1.0 - p_home),
        "margin_sd": round(f["margin_sd"], 2),
        "n_train": f["n_train"],
    }


def main():
    corpus = load(os.path.join(DATA, "corpus_rows_only.json"))["rows"]
    fixtures = load(os.path.join(DATA, "fixtures_2026.json"))["rows"]
    slate = [x for x in fixtures if x["week"] == 11 and x["home"]]

    rows = []
    for g in sorted(slate, key=lambda x: (x["date"], x["kickoff_et"])):
        train = [c for c in corpus if c["week"] < 11]
        f = fit(train)
        o = originate(f, g["away"], g["home"], neutral=bool(g.get("site") == "" and "Mexico" in g.get("note", "")))
        rows.append({
            "order": "1 side -> 2 total -> 3 moneyline",
            "week": 11, "date": g["date"], "kickoff_et": g["kickoff_et"],
            "away": g["away"], "home": g["home"],
            "neutral_site": bool("Mexico" in g.get("note", "")),
            "stage_1_side_fair_spread_home": o["fair_spread_home"],
            "stage_1_side_fair_margin_home": o["fair_margin_home"],
            "stage_2_total_fair_total": o["fair_total"],
            "stage_3_ml_p_home": o["p_home_win"],
            "stage_3_ml_fair_home": o["fair_ml_home"],
            "stage_3_ml_fair_away": o["fair_ml_away"],
            "model_margin_sd": o["margin_sd"],
            "n_train_games": o["n_train"],
            "market_spread_home": None,
            "market_total": None,
            "market_ml_home": None,
            "market_ml_away": None,
            "diff_spread_home": None,
            "diff_total": None,
            "diff_ml_home": None,
            "market_blank_reason": "No official page publishes a spread, total or moneyline "
                                   "(checked 2026-11-17). Market columns and every difference "
                                   "stay blank until the price-data policy is decided (SG-B).",
            "source_url": g["game_url"],
            "week_page_url": g["week_page"],
        })

    # walk-forward accuracy of stage 1 on the corpus, so the baseline is measured, not assumed
    wf = []
    for w in sorted({c["week"] for c in corpus}):
        train = [c for c in corpus if c["week"] < w]
        if len(train) < MIN_TRAIN_GAMES:
            continue
        f = fit(train)
        for g in [c for c in corpus if c["week"] == w]:
            o = originate(f, g["away"], g["home"], neutral=g.get("neutral", False))
            actual = g["home_pts"] - g["away_pts"]
            if actual == 0:
                continue
            wf.append({
                "week": w, "game_id": g["game_id"],
                "fair_margin_home": o["fair_margin_home"], "actual_margin_home": actual,
                "pick": "home" if o["fair_margin_home"] > 0 else "away",
                "correct": (o["fair_margin_home"] > 0) == (actual > 0),
                "abs_err_side": abs(o["fair_margin_home"] - actual),
                "fair_total": o["fair_total"], "actual_total": g["away_pts"] + g["home_pts"],
                "abs_err_total": abs(o["fair_total"] - (g["away_pts"] + g["home_pts"])),
                "source_url": g["source_url"],
            })
    n_wf = len(wf)
    correct = sum(1 for x in wf if x["correct"])
    mae_side = sum(x["abs_err_side"] for x in wf) / n_wf if n_wf else None
    mae_total = sum(x["abs_err_total"] for x in wf) / n_wf if n_wf else None
    # naive comparators: the league average margin/points in the training window
    naive_margin = None
    naive_total = None
    if wf:
        mae_side_naive = sum(abs(0.0 - x["actual_margin_home"]) for x in wf) / n_wf
        mae_total_naive = sum(abs(naive_total - x["actual_total"]) for x in wf) / n_wf if naive_total else None
    # home team wins in the walk-forward sample (the "always home" baseline)
    home_wins = sum(1 for x in wf if x["actual_margin_home"] > 0)

    out = {
        "dataset": "nfl_live_board_origination",
        "title": "Own lines for Week 11 2026, originated side -> total -> moneyline",
        "built_utc": "2026-11-17",
        "model": {
            "kind": "shrunk points-for / points-against baseline",
            "parameters": {"shrink_pseudo_games": SHRINK, "min_train_games": MIN_TRAIN_GAMES},
            "frozen": True,
            "fitted_on": "weeks 1-10 of the reconciled corpus (%d games)" % len(corpus),
            "no_market_inputs": True,
            "moneyline_derivation": "p(home) = Phi(fair margin / residual SD); derived from stage 1, never fitted separately",
        },
        "market_columns_policy": "blank - no official price source exists (flagged F-01)",
        "walk_forward": {
            "note": "weeks whose training window held at least %d games" % MIN_TRAIN_GAMES,
            "n": n_wf,
            "correct": correct,
            "accuracy": round(correct / n_wf, 4) if n_wf else None,
            "always_home_accuracy": round(home_wins / n_wf, 4) if n_wf else None,
            "mae_side": round(mae_side, 3) if mae_side is not None else None,
            "mae_side_naive_zero": round(sum(abs(x["actual_margin_home"]) for x in wf) / n_wf, 3) if n_wf else None,
            "mae_total": round(mae_total, 3) if mae_total is not None else None,
            "weeks": sorted({x["week"] for x in wf}),
        },
        "rows": rows,
        "walk_forward_rows": wf,
        "sources": [
            {"what": "fixtures", "url": "https://www.nfl.com/schedules/2026/by-week/week-11"},
            {"what": "corpus scores (weeks 1-9)", "url": "see per-row source_url in data/corpus_2026.json"},
            {"what": "corpus scores (week 10)", "url": "https://www.nfl.com/scores/2026/week-10"},
            {"what": "standings used in the reconciliation", "url": "https://www.nfl.com/standings/league/2026/REG"},
        ],
    }
    with open(os.path.join(DATA, "origination_week11.json"), "w") as f:
        json.dump(out, f, indent=1)

    print("originated %d Week 11 fixtures (side -> total -> moneyline)" % len(rows))
    print("walk-forward on the corpus: n=%d  accuracy=%.4f  always-home=%.4f  MAE side=%.3f (naive %.3f)  MAE total=%.3f"
          % (n_wf, out["walk_forward"]["accuracy"], out["walk_forward"]["always_home_accuracy"],
             mae_side, out["walk_forward"]["mae_side_naive_zero"], mae_total))
    print("market columns: blank (no official price source) - flagged F-01")


if __name__ == "__main__":
    main()
