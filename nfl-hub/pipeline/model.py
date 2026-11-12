"""Walk-forward NFL margin/total model.

Two independent estimates are produced for every game:

1. Elo — sequential team strength, updated only AFTER the whole week has been
   played, so no game in week W sees any result from week W.
2. Points — exponentially weighted offence/defence in points above league
   average, with a running home-field estimate.

The blend weight, the Elo->points slope and the residual sigma are fitted on
the dev/validation seasons only and frozen before the holdout is scored.
"""
from __future__ import annotations

import math

ELO_START = 1500.0
ELO_K = 20.0
ELO_HFA = 48.0
SEASON_ELO_RETENTION = 0.75
SEASON_POINTS_RETENTION = 0.65
EWMA_ALPHA = 0.25


def _season_rollover(state, season):
    if state["season"] == season:
        return
    state["season"] = season
    for t in list(state["elo"]):
        state["elo"][t] = ELO_START + SEASON_ELO_RETENTION * (state["elo"][t] - ELO_START)
        state["off"][t] *= SEASON_POINTS_RETENTION
        state["def"][t] *= SEASON_POINTS_RETENTION


def new_state(season=1999):
    return {
        "season": season,
        "elo": {},
        "off": {},
        "def": {},
        "lg_avg": 21.0,
        "lg_n": 0,
        "hfa": 2.0,
        "hfa_n": 0,
    }


def predict(state, game):
    home, away = game["home"], game["away"]
    eh = state["elo"].get(home, ELO_START)
    ea = state["elo"].get(away, ELO_START)
    elo_diff = (eh + ELO_HFA) - ea
    p_home_elo = 1.0 / (1.0 + 10 ** (-elo_diff / 400.0))

    lg = state["lg_avg"]
    hfa = state["hfa"]
    hs = lg + state["off"].get(home, 0.0) + state["def"].get(away, 0.0) + hfa / 2.0
    as_ = lg + state["off"].get(away, 0.0) + state["def"].get(home, 0.0) - hfa / 2.0
    return {
        "elo_diff": elo_diff,
        "p_home_elo": p_home_elo,
        "pts_home": hs,
        "pts_away": as_,
        "pts_margin": hs - as_,
        "pts_total": hs + as_,
    }


def update(state, game):
    """Update state with one completed game (called after the week is predicted)."""
    if game["result"] is None:
        return
    home, away = game["home"], game["away"]
    margin = game["result"]
    eh = state["elo"].get(home, ELO_START)
    ea = state["elo"].get(away, ELO_START)
    exp_h = 1.0 / (1.0 + 10 ** (-((eh + ELO_HFA) - ea) / 400.0))
    actual_h = 1.0 if margin > 0 else (0.0 if margin < 0 else 0.5)
    delta = ELO_K * (actual_h - exp_h)
    state["elo"][home] = eh + delta
    state["elo"][away] = ea - delta

    pts = game["home_score"] + game["away_score"]
    lg = state["lg_avg"]
    state["lg_avg"] = (lg * state["lg_n"] + pts / 2.0) / (state["lg_n"] + 1)
    state["lg_n"] += 1
    state["hfa"] = (state["hfa"] * state["hfa_n"] + margin) / (state["hfa_n"] + 1)
    state["hfa_n"] += 1

    lg = state["lg_avg"]
    for team, scored, allowed in (
        (home, game["home_score"], game["away_score"]),
        (away, game["away_score"], game["home_score"]),
    ):
        o = state["off"].get(team, 0.0)
        d = state["def"].get(team, 0.0)
        state["off"][team] = (1 - EWMA_ALPHA) * o + EWMA_ALPHA * (scored - lg)
        state["def"][team] = (1 - EWMA_ALPHA) * d + EWMA_ALPHA * (allowed - lg)


def walk_forward(games):
    """Return one prediction row per game, using only pre-week information."""
    state = new_state()
    preds = []
    by_week = {}
    for g in games:
        by_week.setdefault((g["season"], g["week"]), []).append(g)
    for (season, week) in sorted(by_week):
        _season_rollover(state, season)
        week_games = by_week[(season, week)]
        for g in week_games:
            if g["result"] is None:
                continue
            p = predict(state, g)
            p.update({
                "game_id": g["game_id"],
                "season": season,
                "week": week,
                "date": g["date"],
                "home": g["home"],
                "away": g["away"],
                "actual_margin": g["result"],
                "actual_total": g["total"],
                # nflverse convention: spread_line is the HOME team's line, positive = home favoured.
                "market_margin": g["spread"],
                "market_total": g["total_line"],
                "home_ml": g["home_ml"],
                "away_ml": g["away_ml"],
                "home_spread_odds": g["home_spread_odds"],
                "away_spread_odds": g["away_spread_odds"],
                "over_odds": g["over_odds"],
                "under_odds": g["under_odds"],
            })
            preds.append(p)
        for g in week_games:
            update(state, g)
    return preds, state


def fit_slope(preds):
    """Least-squares slope through the origin: actual margin = a * elo_diff."""
    num = sum(p["elo_diff"] * p["actual_margin"] for p in preds)
    den = sum(p["elo_diff"] ** 2 for p in preds)
    return num / den if den else 0.0


def blend(preds, slope, w_points):
    for p in preds:
        m_elo = slope * p["elo_diff"]
        p["model_margin"] = (1 - w_points) * m_elo + w_points * p["pts_margin"]
        p["model_total"] = p["pts_total"]


def mae(preds, key_pred, key_actual):
    rows = [p for p in preds if p.get(key_pred) is not None and p.get(key_actual) is not None]
    if not rows:
        return None, 0
    return sum(abs(p[key_pred] - p[key_actual]) for p in rows) / len(rows), len(rows)


def rmse(preds, key_pred, key_actual):
    rows = [p for p in preds if p.get(key_pred) is not None and p.get(key_actual) is not None]
    if not rows:
        return None, 0
    return math.sqrt(sum((p[key_pred] - p[key_actual]) ** 2 for p in rows) / len(rows)), len(rows)


def residual_sigma(preds):
    rows = [p for p in preds if p.get("model_margin") is not None]
    if len(rows) < 2:
        return 13.9
    mu = sum(p["actual_margin"] - p["model_margin"] for p in rows) / len(rows)
    var = sum((p["actual_margin"] - p["model_margin"] - mu) ** 2 for p in rows) / (len(rows) - 1)
    return math.sqrt(var)
