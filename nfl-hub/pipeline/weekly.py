"""Originated (own) lines for the upcoming slate, plus look-ahead tests.

Lines are model estimates, not sportsbook quotes. They are labelled DERIVED
everywhere they appear. Market lines for 2026 are absent from the archive and
are therefore left blank rather than imputed.
"""
from __future__ import annotations

import copy
import json
import math
import os
import random

import model
from backtest import norm_cdf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def prob_to_american(p):
    if p is None:
        return None
    p = min(max(p, 0.001), 0.999)
    if p >= 0.5:
        return round(-100 * p / (1 - p))
    return round(100 * (1 - p) / p)


def own_line(margin):
    """Sportsbook notation from a home-perspective margin.

    margin > 0 means the home team is expected to win, so the home line is negative.
    """
    if margin >= 0:
        return f"HOME -{margin:.1f}", f"AWAY +{margin:.1f}"
    return f"HOME +{abs(margin):.1f}", f"AWAY -{abs(margin):.1f}"


def build(games, preds, slope, w_points, sigma, fixtures, ratings_official):
    state = model.new_state()
    by_week = {}
    for g in games:
        by_week.setdefault((g["season"], g["week"]), []).append(g)

    # Predictions are taken at the moment Week 10 opens: after Week 9 results,
    # before any Week 10 kickoff. Later results are applied afterwards so the UI
    # ratings table still reflects the full season, but cannot influence the lines.
    rows = []
    snapshot = None
    for (season, week) in sorted(by_week):
        model._season_rollover(state, season)
        if season == 2026 and week >= 10 and snapshot is None:
            snapshot = copy.deepcopy(state)
        for g in by_week[(season, week)]:
            model.update(state, g)
    if snapshot is None:
        snapshot = copy.deepcopy(state)
    state = snapshot

    for fx in fixtures["games"]:
        g = {
            "game_id": f"2026_10_{fx['away']}_{fx['home']}",
            "home": fx["home"], "away": fx["away"], "season": 2026, "week": 10,
            "date": fx["date"], "result": None,
        }
        raw = model.predict(state, g)
        margin = (1 - w_points) * slope * raw["elo_diff"] + w_points * raw["pts_margin"]
        total = raw["pts_total"]
        p_home = norm_cdf(margin / sigma)
        home_line, away_line = own_line(margin)
        home_rec = ratings_official.get(fx["home"], {})
        away_rec = ratings_official.get(fx["away"], {})
        rows.append({
            "game_id": g["game_id"],
            "date": fx["date"],
            "kickoff_et": fx["kickoff_et"],
            "tv": fx["tv"],
            "note": fx.get("note", ""),
            "away": fx["away"], "home": fx["home"],
            "away_record": f"{away_rec.get('w','')}-{away_rec.get('l','')}-{away_rec.get('t','')}",
            "home_record": f"{home_rec.get('w','')}-{home_rec.get('l','')}-{home_rec.get('t','')}",
            "own_margin_home": round(margin, 2),
            "own_spread_home": home_line,
            "own_spread_away": away_line,
            "own_total": round(total * 2) / 2,
            "own_home_win_prob": round(p_home, 4),
            "own_home_ml": prob_to_american(p_home),
            "own_away_ml": prob_to_american(1 - p_home),
            "market_spread": None,
            "market_total": None,
            "market_status": "BLANK — no official NFL odds publication; the 2026 archive contains no closing lines. Not imputed.",
            "game_url": fx["game_url"],
            "source": fx["source"],
        })
    return rows, state


def lookahead_tests(games, slope, w_points, sigma, fixtures):
    """G6 evidence: predictions must not change when future results change."""
    base_rows, _ = build(games, None, slope, w_points, sigma, fixtures, {})

    truncated = []
    for g in games:
        if g["season"] == 2026 and (g["week"] or 0) >= 10:
            continue
        truncated.append(g)
    trunc_rows, _ = build(truncated, None, slope, w_points, sigma, fixtures, {})

    rng = random.Random(20261112)
    perturbed = copy.deepcopy(games)
    for g in perturbed:
        if g["season"] == 2026 and (g["week"] or 0) >= 10:
            m = rng.choice([-21, -14, -7, 3, 10, 17])
            g["result"] = m
            g["total"] = rng.choice([31, 44, 55])
            g["home_score"] = (g["total"] + m) // 2
            g["away_score"] = g["total"] - g["home_score"]
    pert_rows, _ = build(perturbed, None, slope, w_points, sigma, fixtures, {})

    def key(rows):
        return [(r["game_id"], r["own_margin_home"], r["own_total"], r["own_home_win_prob"]) for r in rows]

    a, b, c = key(base_rows), key(trunc_rows), key(pert_rows)
    return {
        "test_truncate_future": {"identical": a == b, "n_games": len(a)},
        "test_rewrite_future_results": {"identical": a == c, "n_games": len(a)},
        "passed": a == b == c,
        "note": "Predictions for Week 10 are recomputed after deleting every post-Week-9 row and after rewriting post-Week-9 results with random values; all three runs must agree.",
    }


def ratings_table(state, official):
    rows = []
    for t in sorted(state["elo"], key=lambda x: -state["elo"][x]):
        rec = official.get(t, {})
        rows.append({
            "team": t,
            "name": rec.get("name", t),
            "elo": round(state["elo"][t], 1),
            "off_pts_above_avg": round(state["off"].get(t, 0.0), 2),
            "def_pts_above_avg": round(state["def"].get(t, 0.0), 2),
            "w": rec.get("w"), "l": rec.get("l"), "t": rec.get("t"),
            "pf": rec.get("pf"), "pa": rec.get("pa"),
            "source": rec.get("source"),
            "status": "DERIVED (Elo/points model) — record & points from NFL.com official standings",
        })
    return rows
