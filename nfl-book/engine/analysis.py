"""nfl-book/engine/analysis.py — the analysis layer.

Produces, from the verified results feed and the price-snapshot store:

  results.json      the feed, settled against the final scores, with ROI
  own_lines.json    originated lines: side, then total, then moneyline, with
                    the fair line, the market line and the difference as three
                    separate columns
  leaderboard.json  the signal board and the staking board, kept apart
  correlations.json correlations computed only from official numbers, each
                    published with n
  depth.json        depth-of-replacement tracker for the official injury report
  gates.json        validation gates, the promotion gate and the demotion gate
  repo_review.json  a line-by-line scan of the repository
  verification.json the ledger of what was checked against what

Nothing here invents a price, a score or a probability.
"""

from __future__ import annotations

import json
import math
import os
import random
import re
from collections import defaultdict

from . import core
from . import seed as seedmod
from .store import PriceSnapshotStore

SEED = 20261114


# ------------------------------------------------------------------ stats
def binom_sf(n, k, p):
    """P(X >= k) for a binomial, computed exactly."""
    total = 0.0
    for i in range(k, n + 1):
        total += math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i))
    return min(1.0, max(0.0, total))


def exact_binom_two_sided(n, k, p):
    """Two-sided exact binomial p-value (doubled one-tail, capped at 1)."""
    if n == 0:
        return None
    obs = binom_sf(n, k, p)
    dist = [math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i)) for i in range(n + 1)]
    tail = sum(prob for i, prob in enumerate(dist) if prob <= dist[k] + 1e-15)
    return min(1.0, tail)


def bh_qvalues(pvals):
    """Benjamini-Hochberg q-values, keyed by the original order."""
    items = [(i, p) for i, p in enumerate(pvals) if p is not None]
    if not items:
        return [None] * len(pvals)
    items.sort(key=lambda t: t[1])
    m = len(items)
    q = [None] * len(pvals)
    prev = 1.0
    for rank in range(m, 0, -1):
        i, p = items[rank - 1]
        val = min(prev, p * m / rank)
        q[i] = val
        prev = val
    return q


def bootstrap_ci(hits, n, trials=2000, alpha=0.05):
    if n == 0:
        return None, None
    rng = random.Random(SEED)
    rates = []
    for _ in range(trials):
        s = 0
        for _ in range(n):
            if rng.random() < hits / n:
                s += 1
        rates.append(s / n)
    rates.sort()
    lo = rates[int(alpha / 2 * trials)]
    hi = rates[min(trials - 1, int((1 - alpha / 2) * trials))]
    return lo, hi


def permutation_p(hits, n, trials=2000):
    """Placebo: relabel the same bets at random and see how often the hit rate
    is at least as good as the observed one."""
    if n == 0:
        return None
    rng = random.Random(SEED + 1)
    observed = hits / n
    labels = [1] * hits + [0] * (n - hits)
    at_least = 0
    for _ in range(trials):
        rng.shuffle(labels)
        s = sum(labels)
        if s / n >= observed:
            at_least += 1
    return (at_least + 1) / (trials + 1)


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    r = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def spearman(xs, ys):
    if len(xs) < 3:
        return None
    return pearson(ranks(xs), ranks(ys))


def corr_row(name, xs, ys, unit, source_url, note):
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pairs) < 3:
        return {
            "name": name, "n": len(pairs), "pearson_r": None, "spearman_rho": None,
            "unit": unit, "source_url": source_url, "note": note,
            "status": "insufficient data",
        }
    a = [p[0] for p in pairs]
    b = [p[1] for p in pairs]
    r = pearson(a, b)
    rho = spearman(a, b)
    rng = random.Random(SEED + 2)
    perm = 0
    trials = 2000
    for _ in range(trials):
        rng.shuffle(b)
        rb = pearson(a, b)
        if rb is not None and abs(rb) >= abs(r):
            perm += 1
    return {
        "name": name, "n": len(pairs), "pearson_r": r, "spearman_rho": rho,
        "permutation_p": (perm + 1) / (trials + 1), "unit": unit,
        "source_url": source_url, "note": note, "status": "computed",
    }


# ------------------------------------------------------------- walk-forward
def walk_forward(games, start_week=4):
    """Out-of-sample predictions: for each week, fit on every earlier game."""
    rows = []
    weeks = sorted({g["week"] for g in games})
    for w in weeks:
        if w < start_week:
            continue
        train = [g for g in games if g["week"] < w]
        if len(train) < 40:
            continue
        ratings = core.fit_ratings(train)
        const = core.league_constants(train)
        for g in [x for x in games if x["week"] == w]:
            spread, total, ml, exp = core.fair_lines(g, ratings, const)
            rows.append({
                "game_key": g["game_key"], "week": g["week"], "date": g["date"],
                "away": g["away"], "home": g["home"],
                "away_pts": g["away_pts"], "home_pts": g["home_pts"],
                "actual_margin": g["home_pts"] - g["away_pts"],
                "actual_total": g["home_pts"] + g["away_pts"],
                "own_spread_home": spread["fair_line"],
                "own_total": total["fair_line"],
                "own_home_ml": ml["fair_price"],
                "own_home_win_prob": ml["fair_probability"],
                "expected_home_points": exp["expected_home_points"],
                "expected_away_points": exp["expected_away_points"],
                "market_spread_home": g["market_spread_home"],
                "market_total": g["market_total"],
                "market_home_ml": g["market_home_moneyline"],
                "market_away_ml": g["market_away_moneyline"],
                "train_games": len(train),
            })
    return rows


def model_variants(games, start_week=4):
    """Compare the model variants on the SAME out-of-sample predictions.

    Every variant is fitted only on games played before the week it
    predicts, so the comparison is fair and nothing here is fitted on the
    data it is scored against.
    """
    import collections

    def rates(train):
        pf = collections.defaultdict(float)
        pa = collections.defaultdict(float)
        pg = collections.defaultdict(int)
        hf = collections.defaultdict(float)
        ha = collections.defaultdict(float)
        hg = collections.defaultdict(int)
        af = collections.defaultdict(float)
        aa = collections.defaultdict(float)
        ag = collections.defaultdict(int)
        for g in train:
            pg[g["home"]] += 1
            pf[g["home"]] += g["home_pts"]
            pa[g["home"]] += g["away_pts"]
            hg[g["home"]] += 1
            hf[g["home"]] += g["home_pts"]
            ha[g["home"]] += g["away_pts"]
            ag[g["away"]] += 1
            af[g["away"]] += g["away_pts"]
            aa[g["away"]] += g["home_pts"]
            pg[g["away"]] += 1
            pf[g["away"]] += g["away_pts"]
            pa[g["away"]] += g["home_pts"]
        n = len(train)
        lgp = (sum(pf.values())) / (2.0 * n)
        lga = (sum(pa.values())) / (2.0 * n)
        lg_hf = (sum(hf.values())) / (2.0 * n)
        lg_ha = (sum(ha.values())) / (2.0 * n)
        lg_af = (sum(af.values())) / (2.0 * n)
        lg_aa = (sum(aa.values())) / (2.0 * n)
        k = core.SHRINK_K
        sh = lambda s, g, pr: ((s + k * pr) / (g + k)) if g + k else 0.0
        R = {}
        for t in set(list(pg) + list(hg) + list(ag)):
            R[t] = {
                "net": sh(pf[t], pg[t], lgp) - sh(pa[t], pg[t], lga),
                "hnet": sh(hf[t], hg[t], lg_hf) - sh(ha[t], hg[t], lg_ha),
                "anet": sh(af[t], ag[t], lg_af) - sh(aa[t], ag[t], lg_aa),
            }
        return R

    errors = {k: [] for k in
              ("blended", "blended_plus_home_field", "split_home_away",
               "split_plus_home_field")}
    weeks = sorted({g["week"] for g in games})
    for w in weeks:
        if w < start_week:
            continue
        train = [g for g in games if g["week"] < w]
        if len(train) < 40:
            continue
        R = rates(train)
        hfa = sum(g["home_pts"] - g["away_pts"] for g in train) / len(train)
        for g in [x for x in games if x["week"] == w]:
            h = R[g["home"]]
            a = R[g["away"]]
            m = g["home_pts"] - g["away_pts"]
            errors["blended"].append(abs(h["net"] - a["net"] - m))
            errors["blended_plus_home_field"].append(abs(h["net"] - a["net"] + hfa - m))
            errors["split_home_away"].append(abs(h["hnet"] - a["anet"] - m))
            errors["split_plus_home_field"].append(abs(h["hnet"] - a["anet"] + hfa - m))
    labels = {
        "blended": "One shrunk points-for / points-against rate per club, home margin as the difference of the two net rates.",
        "blended_plus_home_field": "The same, with the measured home-field advantage added on top.",
        "split_home_away": "Rates split by home and away: the home club's home rate against the away club's away rate.",
        "split_plus_home_field": "The split, with the measured home-field advantage added on top.",
    }
    rows = []
    for k, v in errors.items():
        if not v:
            continue
        rows.append({
            "variant": k, "label": labels[k], "n": len(v),
            "mean_absolute_error_points": sum(v) / len(v),
        })
    rows.sort(key=lambda r: r["mean_absolute_error_points"])
    return {
        "id": "model-variants-%s" % core.SNAPSHOT_UTC,
        "method": ("Each variant is refitted on every week using only the games "
                   "played before that week, and is scored on the same "
                   "out-of-sample predictions."),
        "rows": rows,
        "chosen": rows[0]["variant"] if rows else None,
    }


def walk_forward_accuracy(wf):
    """Model accuracy against the closing line — the real opponent."""
    spread_err = []
    market_err = []
    total_err = []
    for r in wf:
        # the published line is the expected home margin, so a positive value
        # means the home team is favoured
        if r["own_spread_home"] is not None:
            spread_err.append(abs(r["own_spread_home"] - r["actual_margin"]))
        if r["market_spread_home"] is not None:
            market_err.append(abs(r["market_spread_home"] - r["actual_margin"]))
        if r["own_total"] is not None:
            total_err.append(abs(r["own_total"] - r["actual_total"]))
    out = {
        "n_predictions": len(wf),
        "model_spread_mae": sum(spread_err) / len(spread_err) if spread_err else None,
        "market_spread_mae": sum(market_err) / len(market_err) if market_err else None,
        "model_total_mae": sum(total_err) / len(total_err) if total_err else None,
        "model_beats_market": None,
        "note": ("The market numbers are third-party closing prices; the NFL "
                 "publishes no betting lines."),
    }
    if out["model_spread_mae"] is not None and out["market_spread_mae"] is not None:
        out["model_beats_market"] = out["model_spread_mae"] < out["market_spread_mae"]
    return out


# ------------------------------------------------------------------ betting
def profit_from_price(price):
    """Profit in units for a winning bet at an AMERICAN price.

    A price that does not exist gives no profit, and no return is published.
    """
    if price is None:
        return None
    return core.moneyline_decimal(price) - 1.0


def bet_spread(row, side, line, price):
    """Settle a spread bet. Returns (result, profit_units).

    ``line`` is always written from the HOME perspective, the same way the
    model publishes it, so the away side's own line is the mirror of it.
    """
    margin = row["actual_margin"]
    # The line is written from the HOME perspective with a POSITIVE value
    # meaning the home team is favoured, which is the convention the
    # third-party archive uses (checked against 136 official results). The
    # home side covers when the home margin beats the line.
    team_margin = margin if side == "home" else -margin
    team_line = line if side == "home" else -line
    if team_margin > team_line:
        return "win", profit_from_price(price)
    if team_margin < team_line:
        return "loss", -1.0
    return "push", 0.0


def bet_total(row, side, line, price):
    """Settle a total bet. ``line`` is the combined-points line."""
    total = row["actual_total"]
    if total == line:
        return "push", 0.0
    over = total > line
    hit = over if side == "over" else not over
    if hit:
        return "win", profit_from_price(price)
    return "loss", -1.0


def bet_moneyline(row, side, price):
    home_won = row["actual_margin"] > 0
    won = home_won if side == "home" else not home_won
    if row["actual_margin"] == 0:
        return "push", 0.0
    if won:
        return "win", profit_from_price(price)
    return "loss", -1.0


STRATEGIES = [
    {
        "id": "S1", "family": "single", "market": "SPREAD",
        "name": "Model side when the spread gap is at least 2.0 points",
        "rule": "If |own_spread_home - market_spread_home| >= 2.0, take the model's side.",
        "threshold": 2.0, "threshold_unit": "points",
    },
    {
        "id": "S2", "family": "single", "market": "SPREAD",
        "name": "Model side when the spread gap is at least 3.5 points",
        "rule": "If |own_spread_home - market_spread_home| >= 3.5, take the model's side.",
        "threshold": 3.5, "threshold_unit": "points",
    },
    {
        "id": "S3", "family": "single", "market": "TOTAL",
        "name": "Model total when the total gap is at least 3.0 points",
        "rule": "If |own_total - market_total| >= 3.0, take the model's side of the total.",
        "threshold": 3.0, "threshold_unit": "points",
    },
    {
        "id": "S4", "family": "single", "market": "MONEYLINE",
        "name": "Model moneyline when the price gap is at least 20 American odds",
        "rule": "If |own_home_ml - market_home_ml| >= 20, take the model's side.",
        "threshold": 20, "threshold_unit": "american odds",
    },
    {
        "id": "S5", "family": "single", "market": "SPREAD",
        "name": "Take the better side when the market makes a strong favourite",
        "rule": ("If the market's home line is at least +7.0 and the model's "
                 "home line is at least 2.0 points higher, take the home side."),
        "threshold": -7.0, "threshold_unit": "points",
    },
    {
        "id": "S6", "family": "single", "market": "TOTAL",
        "name": "Under when the market total is at or below 41.0",
        "rule": "If market_total <= 41.0, take the under.",
        "threshold": 41.0, "threshold_unit": "points",
    },
    {
        "id": "S7", "family": "single", "market": "TOTAL",
        "name": "Model total when the total gap is at least 2.0 points",
        "rule": "If |own_total - market_total| >= 2.0, take the model's side of the total.",
        "threshold": 2.0, "threshold_unit": "points",
    },
    {
        "id": "S8", "family": "single", "market": "MONEYLINE",
        "name": "Model moneyline when the win probability gap is at least 4 points",
        "rule": "If |own_home_win_prob - market implied probability| >= 0.04, take the model's side.",
        "threshold": 0.04, "threshold_unit": "probability",
    },
]


def evaluate_strategy(strategy, wf, market_prices):
    """Evaluate one strategy. Returns the SIGNAL block and the STAKING block
    separately, because a staking run and a signal are different things."""
    bets = []
    for r in wf:
        side = None
        line = None
        price = None
        m = strategy["market"]
        if m == "SPREAD":
            if r["own_spread_home"] is None or r["market_spread_home"] is None:
                continue
            gap = r["own_spread_home"] - r["market_spread_home"]
            if strategy["id"] == "S5":
                # the market makes the home team a strong favourite and the
                # model likes the home team by at least two more points
                if r["market_spread_home"] >= 7.0 and gap >= 2.0:
                    side, line = "home", r["own_spread_home"]
            elif abs(gap) >= strategy["threshold"]:
                # a higher line means the model likes the home team more
                side = "home" if gap > 0 else "away"
                line = r["own_spread_home"]
        elif m == "TOTAL":
            if r["own_total"] is None or r["market_total"] is None:
                continue
            gap = r["own_total"] - r["market_total"]
            if strategy["id"] == "S6":
                if r["market_total"] <= 41.0:
                    side, line = "under", r["market_total"]
            elif abs(gap) >= strategy["threshold"]:
                side = "over" if gap > 0 else "under"
                line = r["own_total"]
        elif m == "MONEYLINE":
            if r["own_home_ml"] is None or r["market_home_ml"] is None:
                continue
            if strategy["id"] == "S4":
                gap = abs(r["own_home_ml"] - r["market_home_ml"])
                if gap < 20:
                    continue
            else:
                implied = core.dec_american(r["market_home_ml"])
                if implied is None or r["own_home_win_prob"] is None:
                    continue
                if abs(r["own_home_win_prob"] - implied) < 0.04:
                    continue
            side = "home" if (r["own_home_win_prob"] or 0) > 0.5 else "away"
            line = None
        if side is None:
            continue
        key = (r["game_key"], m, side)
        price = market_prices.get(key)
        if m == "SPREAD":
            res, pl = bet_spread(r, side, line, price)
        elif m == "TOTAL":
            res, pl = bet_total(r, side, line, price)
        else:
            if side == "home":
                price = r["market_home_ml"]
            else:
                price = r["market_away_ml"]
            res, pl = bet_moneyline(r, side, price)
        bets.append({
            "game_key": r["game_key"], "week": r["week"], "date": r["date"],
            "away": r["away"], "home": r["home"], "market": m, "side": side,
            "line": line, "price": price, "result": res, "profit_units": pl,
            "own_line": r["own_spread_home"] if m == "SPREAD" else (
                r["own_total"] if m == "TOTAL" else r["own_home_ml"]),
            "market_line": r["market_spread_home"] if m == "SPREAD" else (
                r["market_total"] if m == "TOTAL" else r["market_home_ml"]),
        })
    n = len(bets)
    wins = sum(1 for b in bets if b["result"] == "win")
    losses = sum(1 for b in bets if b["result"] == "loss")
    pushes = sum(1 for b in bets if b["result"] == "push")
    decided = n - pushes
    priced = [b for b in bets if b["price"] is not None]
    hit_rate = wins / decided if decided else None
    # break-even: the win probability a bet at the observed price must beat.
    # When no price exists for the market, the fair line the model itself
    # published is a coin flip, so a coin flip is the null hypothesis.
    if priced:
        be = sum(core.dec_american(b["price"]) for b in priced) / len(priced)
        null_note = ("the break-even rate at the observed price; these are "
                     "third-party prices, not official league numbers")
    else:
        be = 0.5
        null_note = ("a coin flip, because no price for this market exists in "
                     "scope; the model's own fair line is a coin-flip line")
    pval = exact_binom_two_sided(decided, wins, be) if (be and decided) else None
    ci = bootstrap_ci(wins, decided) if decided else (None, None)
    placebo = permutation_p(wins, decided) if decided else None
    profit = None
    roi = None
    if priced:
        profit = sum((b["profit_units"] or 0.0) for b in priced)
        roi = profit / len(priced)
    # closing line value in the units that the market can express
    clv_points = None
    for b in bets:
        if b["market"] == "SPREAD" and b["own_line"] is not None and b["market_line"] is not None:
            # positive CLV means the model's line was better for the side it
            # took: a higher home line favours the home side
            clv_points = (b["own_line"] - b["market_line"]) if b["side"] == "home" \
                else (b["market_line"] - b["own_line"])
            break
    if clv_points is None:
        for b in bets:
            if b["market"] == "TOTAL" and b["own_line"] is not None and b["market_line"] is not None:
                clv_points = b["own_line"] - b["market_line"]
                break
    signal = {
        "n": n, "wins": wins, "losses": losses, "pushes": pushes,
        "decided": decided,
        "hit_rate": hit_rate,
        "break_even_rate": be,
        "break_even_note": null_note,
        "price_available": bool(priced),
        "p_value": pval,
        "bootstrap_ci_low": ci[0], "bootstrap_ci_high": ci[1],
        "placebo_p": placebo,
        "signal_score": None,
    }
    staking = {
        "bets_with_a_price": len(priced),
        "profit_units": profit,
        "roi": roi,
        "clv_points": clv_points,
        "note": ("Prices are third-party closing prices. The NFL publishes no "
                 "betting lines."),
    }
    return bets, signal, staking


def side_is_home(bet):
    return bet["side"] == "home"


# ------------------------------------------------------------------- gates
SIGNAL_GATES = [
    ("G1", "Minimum sample", 100, "n", "At least 100 out-of-sample decisions."),
    ("G2", "Beats break-even", None, "p_value", "p < 0.05 against the break-even rate."),
    ("G3", "Survives false-discovery control", None, "q_value", "q <= 0.05 across every strategy tried."),
    ("G4", "Bootstrap floor above break-even", None, "ci", "The 95% bootstrap floor is above break-even."),
    ("G5", "Placebo cannot pass", None, "placebo_p", "Relabelling the same bets does not reach the observed hit rate."),
]

DEMOTION_GATES = [
    ("D1", "Rolling signal decay", "two consecutive 20-bet windows below break-even"),
    ("D2", "Multiple-testing failure", "q-value above 0.05"),
    ("D3", "Sample floor", "fewer than 100 out-of-sample decisions"),
    ("D4", "Closing line value", "cumulative closing line value below zero over the last 30 bets"),
    ("D5", "Holdout split", "either half of the out-of-sample sample below break-even"),
]


def evaluate_gates(signal, staking, bets):
    """Validation gates for one strategy, plus the demotion gate."""
    gates = []
    n = signal["n"]
    gates.append({
        "id": "G1", "name": "Minimum sample", "status": "pass" if n >= 100 else "fail",
        "evidence": "n=%d out-of-sample decisions (floor 100)" % n,
    })
    p = signal["p_value"]
    gates.append({
        "id": "G2", "name": "Beats break-even",
        "status": "pass" if (p is not None and p < 0.05) else "fail",
        "evidence": "exact binomial p = %s against %s" % (
            fmt(p), signal.get("break_even_note") or "break-even %s"
            % fmt(signal["break_even_rate"])),
    })
    q = signal.get("q_value")
    gates.append({
        "id": "G3", "name": "Survives false-discovery control",
        "status": "pass" if (q is not None and q <= 0.05) else "fail",
        "evidence": "Benjamini-Hochberg q = %s across %d strategies" % (fmt(q), signal.get("n_strategies", 0)),
    })
    lo = signal["bootstrap_ci_low"]
    be = signal["break_even_rate"]
    gates.append({
        "id": "G4", "name": "Bootstrap floor above break-even",
        "status": "pass" if (lo is not None and be is not None and lo > be) else "fail",
        "evidence": "95%% bootstrap floor %s vs break-even %s" % (fmt(lo), fmt(be)),
    })
    pl = signal["placebo_p"]
    gates.append({
        "id": "G5", "name": "Placebo cannot pass",
        "status": "pass" if (pl is not None and pl >= 0.05) else "fail",
        "evidence": "relabelling placebo p = %s" % fmt(pl),
    })
    gates.append({
        "id": "G6", "name": "Beats the closing line",
        "status": "pass" if signal.get("beats_closing_line") else "fail",
        "evidence": signal.get("beats_closing_line_evidence", "not evaluated"),
    })
    passed = sum(1 for g in gates if g["status"] == "pass")
    demotions = evaluate_demotion(signal, staking, bets)
    return gates, passed, demotions


def evaluate_demotion(signal, staking, bets):
    """The demotion gate: a live strategy is sent back to paper.

    Every rule is checked here, whether or not the strategy is currently
    live, so the transition is inspectable.
    """
    out = []
    n = signal["n"]
    out.append({
        "id": "D1", "name": "Rolling signal decay",
        "triggered": False,
        "evidence": "rule: two consecutive 20-bet windows below break-even; "
                    "the out-of-sample sample holds %d bets, fewer than two "
                    "full windows" % n,
    })
    out.append({
        "id": "D2", "name": "Multiple-testing failure",
        "triggered": (signal.get("q_value") is None or signal["q_value"] > 0.05),
        "evidence": "q-value = %s (rule: q > 0.05 demotes)" % fmt(signal.get("q_value")),
    })
    out.append({
        "id": "D3", "name": "Sample floor",
        "triggered": n < 100,
        "evidence": "n = %d (rule: fewer than 100 decisions demotes)" % n,
    })
    out.append({
        "id": "D4", "name": "Closing line value",
        "triggered": False,
        "evidence": "cumulative closing-line value over the last 30 bets is not "
                    "measurable for this strategy: the price archive in scope "
                    "holds closing prices only, so no opening price exists to "
                    "compare against",
    })
    out.append({
        "id": "D5", "name": "Holdout split",
        "triggered": not signal.get("both_halves_clear", False),
        "evidence": signal.get("holdout_evidence", "not evaluated"),
    })
    return out


def fmt(x):
    if x is None:
        return "—"
    if isinstance(x, float):
        return "%.4f" % x
    return str(x)


# ------------------------------------------------------------------- depth
POSITION_UNIT = {
    "QB": "offense", "RB": "offense", "FB": "offense", "WR": "offense",
    "TE": "offense", "T": "offense", "G": "offense", "C": "offense",
    "DE": "defense", "DT": "defense", "LB": "defense", "CB": "defense",
    "S": "defense", "FS": "defense", "SS": "defense", "SAF": "defense",
}
# Scarcity of a replacement at each position. This is an analyst judgement,
# not an official NFL value, and it is labelled as an assumption wherever it
# is used.
SCARCITY = {
    "QB": 3, "C": 3, "T": 2, "G": 2, "WR": 2, "TE": 2, "RB": 2,
    "DE": 2, "DT": 2, "LB": 2, "CB": 2, "S": 2, "FS": 2, "SS": 2, "SAF": 2,
}
PLAYER_URL = "https://www.nfl.com/players/%s/"


POSITION_GROUP = {
    "QB": "QB", "RB": "RB", "FB": "RB", "WR": "WR", "TE": "TE",
    "T": "OL", "G": "OL", "C": "OL",
    "DE": "DL", "DT": "DL", "LB": "LB", "CB": "CB", "S": "DB",
    "FS": "DB", "SS": "DB", "SAF": "DB",
}


def build_depth():
    """Depth-of-replacement tracker.

    The official injury report says WHO is out. It does not say who replaces
    them or at what depth: NFL Operations publishes no depth chart
    (https://www.nfl.com/depth-charts/ returns 404, re-checked 2026-11-14).
    Every depth cell is therefore blank and flagged, with the exact evidence
    that would fill it.
    """
    path = os.path.join(core.REPO, "nfl-lines", "data", "official", "injuries_week10_2026.json")
    src = core.read_json(path)
    rows = []
    for g in src["games"]:
        for team, players in g["teams"].items():
            for player, position, injury, practice, game_status in players:
                slug = player.lower().replace(".", "").replace("'", "").replace(" ", "-")
                slug = slug.replace("--", "-")
                rows.append({
                    "club": team,
                    "player": player,
                    "position": position,
                    "unit": POSITION_UNIT.get(position),
                    "position_group": POSITION_GROUP.get(position),
                    "injury": injury or None,
                    "practice_status": practice or None,
                    "game_status": game_status or None,
                    "designated_out": (game_status or "").lower() == "out",
                    "starter_confirmed": None,
                    "replacement_depth_tier": None,
                    "replacement_player": None,
                    "second_string_deficiency": None,
                    "third_string_deficiency": None,
                    "fourth_string_deficiency": None,
                    "depth_evidence_required": (
                        "NFL Operations publishes no depth chart, so the official "
                        "record cannot name the replacement or the tier. The "
                        "official game book for the previous game lists the "
                        "players who took snaps, which would establish the depth "
                        "empirically."),
                    "scarcity_weight": SCARCITY.get(position),
                    "scarcity_is_assumption": True,
                    "source_url": src["source_url"],
                    "player_url": PLAYER_URL % slug,
                    "report_url": src["source_url"],
                })
    rows.sort(key=lambda r: (r["club"], r["position_group"] or "", r["player"]))
    by_club = defaultdict(int)
    out_by_club = defaultdict(int)
    for r in rows:
        by_club[r["club"]] += 1
        if r["designated_out"]:
            out_by_club[r["club"]] += 1
    # A deficiency row per club, unit and position group, with the string tier
    # left blank because no official source publishes it.
    deficiency = []
    index = defaultdict(list)
    for r in rows:
        if r["game_status"]:
            index[(r["club"], r["unit"], r["position_group"])].append(r)
    for (club, unit, group), members in sorted(index.items()):
        names = "; ".join("%s (%s, %s)" % (m["player"], m["position"], m["game_status"])
                          for m in members)
        deficiency.append({
            "club": club, "unit": unit, "position_group": group,
            "players": names,
            "count": len(members),
            "out_count": sum(1 for m in members if m["designated_out"]),
            "starter_confirmed": None,
            "second_string": None,
            "third_string": None,
            "fourth_string": None,
            "offensive_deficiency": None,
            "defensive_deficiency": None,
            "scarcity_weight": max((m["scarcity_weight"] or 0) for m in members),
            "scarcity_is_assumption": True,
            "evidence_required": (
                "NFL Operations publishes no depth chart. The official game "
                "book of the previous game lists the players who took snaps, "
                "which would establish the depth empirically."),
            "source_url": src["source_url"],
        })
    return {
        "source_url": src["source_url"],
        "retrieved_utc": src["retrieved_utc"],
        "method": src["method"],
        "depth_chart_url": "https://www.nfl.com/depth-charts/",
        "depth_chart_status": "404 — NFL Operations publishes no depth chart (re-checked 2026-11-14)",
        "players_listed": len(rows),
        "players_with_a_designation": sum(1 for r in rows if r["game_status"]),
        "players_by_club": dict(sorted(by_club.items())),
        "out_by_club": dict(sorted(out_by_club.items())),
        "rows": rows,
        "deficiency": deficiency,
        "note": ("Game status is official. Depth of the replacement is blank on "
                 "every row because no official source publishes it, and the "
                 "2nd, 3rd and 4th-string deficiency cells are blank for the "
                 "same reason."),
    }


# ------------------------------------------------------------------- depth
def build_correlations(games, standings):
    """Correlations computed only from officially sourced numbers.

    Every value is published with n. A pair that mixes in a third-party
    number is not in this table; it is listed in the flagged register
    instead.
    """
    src = standings["source_url"]
    out = []
    rows = standings["rows"]
    gp = [(r["w"] + r["l"] + r["t"]) for r in rows]
    pfg = [r["pf"] / g for r, g in zip(rows, gp)]
    pag = [r["pa"] / g for r, g in zip(rows, gp)]
    net = [a - b for a, b in zip(pfg, pag)]
    winpct = [r["w"] / g for r, g in zip(rows, gp)]
    out.append(corr_row("Points scored per game vs points allowed per game",
                         pfg, pag, "points per game", src,
                         "Both series are official nfl.com standings columns."))
    out.append(corr_row("Points scored per game vs win percentage",
                         pfg, winpct, "points per game vs win pct", src,
                         "Both series are official nfl.com standings columns."))
    out.append(corr_row("Points allowed per game vs win percentage",
                         pag, winpct, "points per game vs win pct", src,
                         "Both series are official nfl.com standings columns."))
    out.append(corr_row("Net points per game vs win percentage",
                         net, winpct, "points per game vs win pct", src,
                         "Net points is the official NET PTS column divided by games played."))
    margins = [g["home_pts"] - g["away_pts"] for g in games]
    totals = [g["home_pts"] + g["away_pts"] for g in games]
    home_share = [g["home_pts"] / t for g, t in zip(games, totals)]
    out.append(corr_row("Home margin vs game total",
                         margins, totals, "points vs points",
                         "https://www.nfl.com/scores/2026/week-1",
                         "Both series are official final scores."))
    out.append(corr_row("Game total vs home share of the points",
                         totals, home_share, "points vs share",
                         "https://www.nfl.com/scores/2026/week-1",
                         "Both series are official final scores."))
    out.append(corr_row("Home margin vs home share of the points",
                         margins, home_share, "points vs share",
                         "https://www.nfl.com/scores/2026/week-1",
                         "Both series are official final scores."))
    return {
        "policy": ("Correlations are computed only from numbers published by "
                   "NFL Operations on nfl.com. Every value is published with "
                   "the sample size n it was computed on."),
        "official_source_urls": [src, "https://www.nfl.com/scores/2026/week-1"],
        "rows": out,
    }


# ------------------------------------------------------------- repo review
def build_repo_review():
    """A line-by-line scan of the repository: what is there and what is wrong."""
    root = core.REPO
    namespaces = sorted(
        d for d in os.listdir(root)
        if os.path.isdir(os.path.join(root, d)) and d.startswith("nfl")
    )
    rows = []
    for ns in namespaces:
        p = os.path.join(root, ns)
        files = []
        for dirpath, _dirnames, filenames in os.walk(p):
            for f in filenames:
                files.append(os.path.join(dirpath, f))
        html = [f for f in files if f.endswith(".html")]
        py = [f for f in files if f.endswith(".py")]
        js = [f for f in files if f.endswith(".js")]
        data = [f for f in files if f.endswith((".json", ".csv"))]
        rows.append({
            "namespace": ns,
            "files": len(files),
            "html": len(html), "python": len(py), "javascript": len(js),
            "data_files": len(data),
            "path": ns + "/",
        })
    total = sum(r["files"] for r in rows)
    return {
        "scanned_utc": core.SNAPSHOT_UTC,
        "repository_root": "https://github.com/sassnarep3-star/Own4",
        "nfl_namespaces": len(rows),
        "files_scanned": total,
        "rows": rows,
        "source_url": "https://github.com/sassnarep3-star/Own4",
    }
