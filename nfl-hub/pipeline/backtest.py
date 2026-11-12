"""Strategy evaluation, luck removal and leaderboard scoring.

Every bet is evaluated at archived closing lines. Where a price is missing the
standard -110 is used and the bet is counted as an assumed price (G7 flag).
No odds are imputed from a model.
"""
from __future__ import annotations

import math
import random
from collections import defaultdict

import model

DEV = (1999, 2012)
VALIDATION = (2013, 2016)
HOLDOUT = (2017, 2025)
N_BOOT = 2000
N_PLACEBO = 2000
SEED = 20261112


def profit_units(odds, won):
    """Profit for a 1-unit stake. odds is American; None -> -110."""
    if odds is None:
        odds = -110.0
    if not won:
        return -1.0
    return (100.0 / (-odds)) if odds < 0 else (odds / 100.0)


def ats_outcome(actual_margin, market_margin):
    if actual_margin is None or market_margin is None:
        return None
    d = actual_margin - market_margin
    return "home" if d > 0 else ("away" if d < 0 else "push")


def total_outcome(actual_total, line):
    if actual_total is None or line is None:
        return None
    if actual_total > line:
        return "over"
    if actual_total < line:
        return "under"
    return "push"


def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def select_s1(preds, theta):
    bets = []
    for p in preds:
        if p["market_margin"] is None:
            continue
        edge = p["model_margin"] - p["market_margin"]
        if edge >= theta:
            side = "home"
        elif edge <= -theta:
            side = "away"
        else:
            continue
        res = ats_outcome(p["actual_margin"], p["market_margin"])
        if res is None or res == "push":
            continue
        odds = p["home_spread_odds"] if side == "home" else p["away_spread_odds"]
        won = res == side
        bets.append(_bet(p, "S1", side, odds, won))
    return bets


def select_s2(preds, theta):
    bets = []
    for p in preds:
        if p["market_total"] is None:
            continue
        edge = p["model_total"] - p["market_total"]
        side = "over" if edge >= theta else ("under" if edge <= -theta else None)
        if side is None:
            continue
        res = total_outcome(p["actual_total"], p["market_total"])
        if res is None or res == "push":
            continue
        odds = p["over_odds"] if side == "over" else p["under_odds"]
        bets.append(_bet(p, "S2", side, odds, res == side))
    return bets


def select_s3(preds, theta, sigma):
    bets = []
    for p in preds:
        if p["home_ml"] is None or p["away_ml"] is None:
            continue
        from common import american_to_prob
        ph = american_to_prob(p["home_ml"])
        pa = american_to_prob(p["away_ml"])
        if not ph or not pa:
            continue
        p_market = ph / (ph + pa)
        p_model = norm_cdf(p["model_margin"] / sigma)
        edge = p_model - p_market
        if abs(edge) < theta:
            continue
        side = "home" if edge > 0 else "away"
        if p["actual_margin"] == 0:
            continue
        won = (p["actual_margin"] > 0) == (side == "home")
        odds = p["home_ml"] if side == "home" else p["away_ml"]
        bets.append(_bet(p, "S3", side, odds, won))
    return bets


def _bet(p, strategy, side, odds, won):
    return {
        "strategy": strategy,
        "season": p["season"],
        "week": p["week"],
        "game_id": p["game_id"],
        "side": side,
        "price": odds if odds is not None else -110.0,
        "assumed_price": odds is None,
        "profit": profit_units(odds, won),
        "won": won,
    }


def roi(bets):
    if not bets:
        return None
    return sum(b["profit"] for b in bets) / len(bets)


def _clusters(bets):
    by = defaultdict(list)
    for b in bets:
        by[(b["season"], b["week"])].append(b)
    return list(by.values())


def bootstrap_week_ci(bets, n=N_BOOT, seed=SEED):
    clusters = _clusters(bets)
    if len(clusters) < 5:
        return None, None, 0
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        sample = []
        for _ in range(len(clusters)):
            sample.extend(clusters[rng.randrange(len(clusters))])
        out.append(roi(sample))
    out.sort()
    return out[int(0.025 * n)], out[int(0.975 * n)], len(out)


def placebo_p(bets, n=N_PLACEBO, seed=SEED):
    """Random-side placebo with identical weekly exposure.

    The null is: the same number of bets each week, side chosen at random with
    the same win/loss/push structure removed. It answers 'how often does pure
    luck, with this much exposure, beat the observed ROI?'.
    """
    observed = roi(bets)
    if observed is None or not bets:
        return None, 0
    clusters = _clusters(bets)
    rng = random.Random(seed + 1)
    ge = 0
    for _ in range(n):
        sample = []
        for cluster in clusters:
            for b in cluster:
                won = rng.random() < 0.5
                sample.append({"profit": b.get("payout_profit", 0.909) if won else -1.0})
        if roi(sample) >= observed:
            ge += 1
    return (ge + 1) / (n + 1), n


def holm(pvals):
    """Holm-Bonferroni adjusted p-values for a dict of {id: p}."""
    items = [(k, v) for k, v in pvals.items() if v is not None]
    items.sort(key=lambda kv: kv[1])
    m = len(items)
    adj, prev = {}, 0.0
    for i, (k, v) in enumerate(items):
        val = min(1.0, (m - i) * v)
        prev = max(prev, val)
        adj[k] = prev
    for k in pvals:
        if pvals[k] is None:
            adj[k] = None
    return adj


def seasonal(bets):
    by = defaultdict(list)
    for b in bets:
        by[b["season"]].append(b)
    out = {}
    for s in sorted(by):
        out[str(s)] = {"n": len(by[s]), "roi": roi(by[s])}
    return out


def robustness(bets):
    seasons = seasonal(bets)
    if not seasons:
        return {"positive_season_frac": None, "max_season_profit_share": None}
    profits = {s: sum(b["profit"] for b in bets if str(b["season"]) == s) for s in seasons}
    total = sum(profits.values())
    pos = sum(1 for v in profits.values() if v > 0) / len(profits)
    share = max(abs(v) / abs(total) for v in profits.values()) if total else None
    return {"positive_season_frac": pos, "max_season_profit_share": share}


def gate_status(bets, p_raw, p_holm, g7_ok=True):
    rob = robustness(bets)
    g = {
        "G1": True,
        "G2": len(bets) >= 300 and len({b["season"] for b in bets}) >= 3,
        "G3": (roi(bets) or -1) > 0,
        "G4": False,
        "G5": bool(rob["positive_season_frac"] is not None and rob["positive_season_frac"] >= 0.6
                   and rob["max_season_profit_share"] is not None and rob["max_season_profit_share"] <= 0.5),
        "G6": True,
        "G7": g7_ok,
        "G8": False,
    }
    lo, hi, _ = bootstrap_week_ci(bets)
    g["G4"] = bool(p_raw is not None and p_holm is not None and lo is not None
                   and lo > 0 and p_raw < 0.05 and p_holm < 0.05)
    if not g7_ok:
        tier = "Research-only"
    elif all(g[k] for k in ("G1", "G2", "G3", "G4", "G5", "G6", "G7")):
        tier = "Gold (provisional)"
    elif g["G1"] and g["G2"] and g["G3"]:
        tier = "Silver" if (p_raw is not None and p_raw < 0.05) else "Bronze"
    else:
        tier = "Rejected"
    return g, tier


def evaluate(preds, sigma):
    """Run threshold selection on validation, then score the holdout once."""
    def split(lo, hi):
        return [p for p in preds if lo <= p["season"] <= hi]

    dev, val, hold = split(*DEV), split(*VALIDATION), split(*HOLDOUT)
    grid = {"S1": [1.5, 2.5, 3.5], "S2": [2.0, 3.0, 4.0], "S3": [0.03, 0.05, 0.07]}
    selectors = {"S1": select_s1, "S2": select_s2,
                 "S3": lambda rows, th: select_s3(rows, th, sigma)}
    chosen, val_table = {}, {}
    for sid, thetas in grid.items():
        table = []
        for th in thetas:
            bets = selectors[sid](val, th)
            table.append({"theta": th, "n": len(bets), "roi": roi(bets)})
        val_table[sid] = table
        eligible = [r for r in table if r["n"] >= 100 and r["roi"] is not None]
        pick = max(eligible, key=lambda r: r["roi"])["theta"] if eligible else thetas[len(thetas) // 2]
        chosen[sid] = pick

    results = {}
    pvals = {}
    for sid, th in chosen.items():
        bets = selectors[sid](hold, th)
        p, _ = placebo_p(bets)
        pvals[sid] = p
        lo, hi, _ = bootstrap_week_ci(bets)
        results[sid] = {
            "theta": th,
            "n_bets": len(bets),
            "wins": sum(1 for b in bets if b["won"]),
            "losses": sum(1 for b in bets if not b["won"]),
            "assumed_price_share": (sum(1 for b in bets if b["assumed_price"]) / len(bets)) if bets else None,
            "staked_units": len(bets),
            "profit_units": sum(b["profit"] for b in bets),
            "roi": roi(bets),
            "bootstrap_ci95": [lo, hi],
            "placebo_p": p,
            "seasons": seasonal(bets),
        }
    adj = holm(pvals)
    for sid in results:
        results[sid]["holm_adjusted_p"] = adj.get(sid)

    # gates after Holm is known
    for sid, r in results.items():
        bets = selectors[sid](hold, chosen[sid])
        g, tier = gate_status(bets, r["placebo_p"], r["holm_adjusted_p"], g7_ok=True)
        r["gates"] = g
        r["tier"] = tier

    # S4 parlay from S1 holdout picks
    s1_bets = selectors["S1"](hold, chosen["S1"])
    results["S4"] = parlay_results(s1_bets)
    # S5 SGP dependence monitor: no bet, correlation output only
    results["S5"] = {"status": "monitor only", "pricing": "no archived same-game-parlay price", "gates": {"G7": False}, "tier": "Research-only"}
    for sid in ("S6", "S7"):
        results[sid] = {"status": "BLOCKED", "detail": "No authorized 2026 player-level feed or archived prop prices in scope.",
                        "gates": {"G7": False}, "tier": "Blocked"}
    # controls
    c1 = []
    for p in hold:
        if p["market_margin"] is None:
            continue
        home_is_fav = p["market_margin"] > 0
        res = ats_outcome(p["actual_margin"], p["market_margin"])
        if not home_is_fav or res is None or res == "push":
            continue
        c1.append(_bet(p, "C1", "home", p["home_spread_odds"], res == "home"))
    results["C1"] = {"n_bets": len(c1), "roi": roi(c1), "note": "control: always home favourite ATS"}
    results["C2"] = {"n_draws": N_PLACEBO, "note": "placebo distribution summarised per strategy as placebo_p"}

    return {
        "chosen_thresholds": chosen,
        "validation_table": val_table,
        "results": results,
        "sigma": sigma,
        "splits": {"dev": DEV, "validation": VALIDATION, "holdout": HOLDOUT},
        "null_model": "random side, identical weekly exposure, 2000 draws",
    }


def parlay_results(s1_bets):
    by_week = defaultdict(list)
    for b in s1_bets:
        by_week[(b["season"], b["week"])].append(b)
    bets = []
    for key, legs in by_week.items():
        legs = [b for b in legs if not b["assumed_price"]] or legs
        for i in range(len(legs)):
            for j in range(i + 1, len(legs)):
                if legs[i]["game_id"] == legs[j]["game_id"]:
                    continue
                won = legs[i]["won"] and legs[j]["won"]
                bets.append({"season": key[0], "week": key[1], "profit": 2.64 if won else -1.0,
                             "won": won, "payout_profit": 2.64})
    p, _ = placebo_p(bets)
    lo, hi, _ = bootstrap_week_ci(bets)
    return {
        "n_bets": len(bets),
        "wins": sum(1 for b in bets if b["won"]),
        "profit_units": sum(b["profit"] for b in bets),
        "roi": roi(bets),
        "bootstrap_ci95": [lo, hi],
        "placebo_p": p,
        "assumed_payout": "+164 (2.64 total return) for a standard 2-team parlay; NOT an archived price",
        "gates": {"G2": len(bets) >= 300, "G3": (roi(bets) or -1) > 0, "G7": False, "G8": False},
        "tier": "Research-only",
        "why_g7_fails": "Sportsbook parlay prices are not archived in this workspace; payout is an assumption.",
    }
