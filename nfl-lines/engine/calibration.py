"""Probability calibration: is the model's confidence honest?

Return on investment is dominated by luck at these sample sizes. Calibration is a
separate, luck-robust test of skill: if the model says a team wins 70% of the time,
it should win about 70% of the time. A model can be well calibrated and still lose
money (because the market already knew), and it can be badly calibrated and get
lucky. Both tests are reported because they answer different questions.
"""
from __future__ import annotations

import math

import model as M


def _brier(pairs):
    if not pairs:
        return None
    return round(sum((p - y) ** 2 for p, y in pairs) / len(pairs), 5)


def _logloss(pairs, eps=1e-6):
    if not pairs:
        return None
    tot = 0.0
    for p, y in pairs:
        p = min(max(p, eps), 1 - eps)
        tot += -(y * math.log(p) + (1 - y) * math.log(1 - p))
    return round(tot / len(pairs), 5)


def compute(rows):
    pairs_model, pairs_market = [], []
    for r in rows:
        y = r["home_win"]
        if y is None:
            continue
        mp = r.get("model_home_win_prob")
        if mp is not None:
            pairs_model.append((mp, y))
        hm, am = r.get("home_moneyline"), r.get("away_moneyline")
        if hm and am:
            ph, pa = M.implied_prob(hm), M.implied_prob(am)
            if ph and pa:
                f, _ = M.devig_two_way(ph, pa)
                pairs_market.append((f, y))

    # reliability diagram in 10 equal-width bins
    bins = []
    for i in range(10):
        lo, hi = i / 10.0, (i + 1) / 10.0
        sel = [(p, y) for p, y in pairs_model if (lo <= p < hi) or (i == 9 and p >= 0.9)]
        if not sel:
            bins.append({"bin": "%.1f-%.1f" % (lo, hi), "n": 0, "mean_predicted": None,
                         "actual_rate": None})
            continue
        bins.append({
            "bin": "%.1f-%.1f" % (lo, hi), "n": len(sel),
            "mean_predicted": round(sum(p for p, _ in sel) / len(sel), 4),
            "actual_rate": round(sum(y for _, y in sel) / len(sel), 4),
        })
    filled = [b for b in bins if b["n"] >= 25]
    reliability = None
    if filled:
        reliability = round(
            sum(b["n"] * (b["mean_predicted"] - b["actual_rate"]) ** 2 for b in filled)
            / sum(b["n"] for b in filled), 6)

    # baseline: always forecast the league home-win rate
    base_rate = (sum(y for _, y in pairs_model) / len(pairs_model)) if pairs_model else None
    brier_base = _brier([(base_rate, y) for _, y in pairs_model]) if base_rate is not None else None

    return {
        "n_games": len(pairs_model),
        "model_brier": _brier(pairs_model),
        "market_brier": _brier(pairs_market),
        "baseline_brier": brier_base,
        "baseline_home_win_rate": round(base_rate, 4) if base_rate is not None else None,
        "model_log_loss": _logloss(pairs_model),
        "market_log_loss": _logloss(pairs_market),
        "reliability_mse_weighted": reliability,
        "reliability_bins": bins,
        "reading": (
            "Lower Brier score and lower log loss are better. The market row is the "
            "benchmark built from the third-party closing moneylines with the overround "
            "removed two-way."),
    }
