"""Walk-forward backtest that originates a line for every game and grades it.

Protocol
--------
1. Games are ordered by kick-off date.
2. For every distinct kick-off date in the evaluation universe, the two models are
   refitted using ONLY games with an earlier date. Nothing from the same day or later
   can leak in.
3. The refitted model emits its own spread, total, team totals and moneyline for every
   game on that date. Those are the "own lines".
4. The own line is compared with the third-party closing line recorded in the archive.
5. Bets are graded against the official final score at the recorded price.

The archive's closing lines are THIRD-PARTY (the NFL publishes no official odds), so
every market-derived number on the site is labelled as such.
"""
from __future__ import annotations

import datetime as dt
import math
import os

import numpy as np

import dataset as D
import model as M

HERE = os.path.dirname(os.path.abspath(__file__))


def _ord(s):
    y, m, d = (int(x) for x in s.split("-"))
    return dt.date(y, m, d).toordinal()


def prepare(games):
    """Return REG games sorted by date with an ordinal day index attached."""
    reg = [g for g in games if g["game_type"] == "REG"]
    for g in reg:
        g["_ord"] = _ord(g["gameday"])
    reg.sort(key=lambda g: (g["_ord"], g["game_id"]))
    return reg


def run(reg, params, season_from=None, season_to=None):
    p = params
    ev = p["evaluation"]
    season_from = season_from if season_from is not None else ev["eval_start_season"]
    season_to = season_to if season_to is not None else 9999

    universe = [g for g in reg
                if g["season"] >= season_from and g["season"] <= season_to
                and g["margin"] is not None
                and g["spread_line"] is not None
                and g["total_line"] is not None]
    if not universe:
        return []

    margin_model = M.MarginModel(p["model"])
    total_model = M.TotalModel(p["model"])

    # pre-seed the team index with every club that appears, so column order is stable
    all_teams = sorted({M.franchise(g["home"]) for g in reg} | {M.franchise(g["away"]) for g in reg})
    margin_model._ensure_index(all_teams)
    total_model._ensure_index(all_teams)

    dates = sorted({g["_ord"] for g in universe})
    out = []
    # pointer into the chronologically sorted game list
    for day in dates:
        train = [g for g in reg if g["_ord"] < day and g["margin"] is not None]
        if len(train) < p["model"]["min_train_games"]:
            continue
        # cap the training window for speed: 14 seasons of history is plenty
        cutoff = day - int(365.25 * 14)
        train = [g for g in train if g["_ord"] >= cutoff]
        margin_model.fit(train, day)
        total_model.fit(train, day)
        if margin_model.coef is None or total_model.coef is None:
            continue
        for g in [x for x in universe if x["_ord"] == day]:
            own_spread = margin_model.predict(g)          # +ve => home favoured
            own_total = total_model.predict(g)
            if own_spread is None or own_total is None:
                continue
            prob = margin_model.home_win_prob(g)
            row = dict(g)
            row.update({
                "own_spread_line": round(own_spread, 2),
                "own_total_line": round(own_total, 2),
                "model_home_win_prob": round(prob, 4),
                "model_sigma_margin": round(margin_model.sigma, 3),
                "model_sigma_total": round(total_model.sigma, 3),
                "spread_edge": round(own_spread - g["spread_line"], 2),
                "total_edge": round(own_total - g["total_line"], 2),
            })
            # ---- outcomes
            mkt = g["spread_line"]
            row["home_cover"] = None
            if g["margin"] is not None:
                diff = g["margin"] - mkt          # home margin minus home spread handicap
                row["home_cover_margin"] = round(diff, 2)
                row["home_cover"] = 1 if diff > 0 else (0 if diff < 0 else None)
                row["away_cover"] = 1 if diff < 0 else (0 if diff > 0 else None)
                row["over_result"] = 1 if g["total"] > g["total_line"] else (0 if g["total"] < g["total_line"] else None)
                row["under_result"] = 1 if g["total"] < g["total_line"] else (0 if g["total"] > g["total_line"] else None)
            row["home_win"] = 1 if g["margin"] > 0 else (0 if g["margin"] < 0 else None)
            out.append(row)
    return out


# ------------------------------------------------------------------------- pricing

def price_for(row, side):
    """Recorded price for a bet, falling back to the documented default."""
    d = M.load_params()["evaluation"]["default_price_when_missing"]
    key = {
        "home": row.get("home_spread_odds"),
        "away": row.get("away_spread_odds"),
        "over": row.get("over_odds"),
        "under": row.get("under_odds"),
        "home_ml": row.get("home_moneyline"),
        "away_ml": row.get("away_moneyline"),
    }[side]
    return key if key else d


def payoff(american, won, stake=1.0):
    if won is None:      # push
        return 0.0
    if won:
        return stake * (american / 100.0 if american > 0 else 100.0 / abs(american))
    return -stake


def mean_implied_prob(bets):
    """Average implied probability across bets.

    American odds are NOT on a linear scale, so they must never be averaged
    arithmetically. Each price is converted to an implied probability first and the
    probabilities are then averaged. This average is the win rate a bettor with no
    skill should expect if the recorded prices are efficient, so it is the correct
    null for the significance test.
    """
    ps = [M.implied_prob(b["price"]) for b in bets]
    ps = [p for p in ps if p is not None]
    return sum(ps) / len(ps) if ps else None


def summarise(bets):
    """bets: list of dicts with keys won (1/0/None), price, season."""
    n = len(bets)
    if n == 0:
        return {"n": 0}
    wins = sum(1 for b in bets if b["won"] == 1)
    pushes = sum(1 for b in bets if b["won"] is None)
    decided = n - pushes
    pnl = sum(b["pnl"] for b in bets)
    staked = sum(b["stake"] for b in bets)
    win_rate = (wins / decided) if decided else None
    roi = (pnl / staked) if staked else None
    be = mean_implied_prob(bets)
    pval = None
    if decided and be is not None:
        pval = binom_two_sided(wins, decided, be)
    prices = sorted(b["price"] for b in bets)
    med = prices[n // 2] if n % 2 else (prices[n // 2 - 1] + prices[n // 2]) / 2.0
    return {
        "n": n, "decided": decided, "wins": wins, "pushes": pushes,
        "win_rate": None if win_rate is None else round(win_rate, 4),
        "pnl_units": round(pnl, 3), "staked_units": round(staked, 3),
        "roi": None if roi is None else round(roi, 4),
        "break_even_rate": None if be is None else round(be, 4),
        "median_price": round(med, 1),
        "mean_decimal_odds": round(
            sum(M.american_to_decimal(b["price"]) for b in bets) / n, 4),
        "p_value_vs_breakeven": None if pval is None else round(pval, 6),
    }


def binom_two_sided(k, n, p):
    """Exact two-sided binomial test (normal approximation with continuity correction
    for large n, exact sum for small n)."""
    if n == 0:
        return None
    if n <= 200:
        from math import comb
        pmf = [comb(n, i) * (p ** i) * ((1 - p) ** (n - i)) for i in range(n + 1)]
        obs = pmf[k]
        lo = sum(x for x in pmf if x <= obs * (1 + 1e-12))
        return min(1.0, lo)
    mu = n * p
    sd = math.sqrt(n * p * (1 - p))
    z = (abs(k - mu) - 0.5) / sd
    return math.erfc(z / math.sqrt(2.0))
