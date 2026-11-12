"""Measured correlations and base rates.

Each entry reports the coefficient, its 95% confidence interval, a p-value and the
sample size, together with the exact quantities correlated. Nothing here is quoted
from memory or assumed - every figure is computed from the walk-forward table.
"""
from __future__ import annotations

from collections import Counter

from evaluate import pearson


def compute(rows):
    out = []

    def add(cid, group, label, xa, xb, ya, yb, note):
        r, extra, n = pearson(xa, xb)
        out.append({
            "id": cid, "group": group, "label": label,
            "variable_x": ya, "variable_y": yb,
            "pearson_r": r, "n": n,
            "ci95": (extra or {}).get("ci95"),
            "p_value": (extra or {}).get("p_value"),
            "note": note,
        })

    # ---- forecast skill: does the model's disagreement with the market predict anything?
    add("CR-01", "Forecast skill",
        "Own-line edge vs actual result against the market spread",
        [r["spread_edge"] for r in rows], [r["home_cover_margin"] for r in rows],
        "own spread - market spread", "actual home margin - market spread",
        "The single most important number on this site: if the model has skill, a bigger "
        "disagreement with the closing line should produce a bigger cover margin.")
    add("CR-02", "Forecast skill",
        "Own-total edge vs actual result against the market total",
        [r["total_edge"] for r in rows], [r["total"] - r["total_line"] for r in rows],
        "own total - market total", "actual total - market total",
        "Same test for the totals market.")

    # ---- forecast accuracy vs the market
    add("CR-03", "Forecast accuracy",
        "Own spread vs actual home margin",
        [r["own_spread_line"] for r in rows], [r["margin"] for r in rows],
        "own spread (home favoured +)", "actual home margin", "Accuracy of the originated line.")
    add("CR-04", "Forecast accuracy",
        "Market closing spread vs actual home margin",
        [r["spread_line"] for r in rows], [r["margin"] for r in rows],
        "market closing spread", "actual home margin",
        "Benchmark: the same correlation for the third-party closing line.")
    add("CR-05", "Forecast accuracy",
        "Own total vs actual total",
        [r["own_total_line"] for r in rows], [r["total"] for r in rows],
        "own total", "actual total", "Accuracy of the originated total.")
    add("CR-06", "Forecast accuracy",
        "Market closing total vs actual total",
        [r["total_line"] for r in rows], [r["total"] for r in rows],
        "market closing total", "actual total", "Benchmark for the total.")

    # ---- structural correlations that drive same-game parlay pricing
    hc = [r["home_cover"] for r in rows]
    ov = [r["over_result"] for r in rows]
    add("CR-07", "Parlay structure",
        "Home covers the spread AND the game goes over",
        hc, ov, "home covers (1/0)", "over (1/0)",
        "Correlation between the two legs of the most common NFL same-game parlay. "
        "A non-zero value means the independence price is wrong.")
    fav_cov, fav_ov = [], []
    for r in rows:
        if r["spread_line"] > 0:
            fav_cov.append(r["home_cover"]); fav_ov.append(r["over_result"])
        elif r["spread_line"] < 0:
            fav_cov.append(r["away_cover"]); fav_ov.append(r["over_result"])
        else:
            fav_cov.append(None); fav_ov.append(r["over_result"])
    add("CR-08", "Parlay structure",
        "Favourite covers AND the game goes over",
        fav_cov, fav_ov, "favourite covers (1/0)", "over (1/0)",
        "The exact structure priced by strategy C-SGP-FAV-OVER.")
    add("CR-09", "Parlay structure",
        "Final margin vs game total",
        [r["margin"] for r in rows], [r["total"] for r in rows],
        "home margin", "game total",
        "A positive value means blowouts are also high-scoring games.")

    # ---- team totals
    add("CR-10", "Team totals",
        "Home team points vs away team points",
        [r["home_score"] for r in rows], [r["away_score"] for r in rows],
        "home points", "away points",
        "Usually slightly negative: a bigger share for one team means less for the other.")

    # ---- rest
    add("CR-11", "Situational",
        "Rest differential vs home margin",
        [(r["home_rest"] or 7) - (r["away_rest"] or 7) for r in rows], [r["margin"] for r in rows],
        "home rest days - away rest days", "home margin",
        "Tests whether the rest differential carries information.")

    # ---- market efficiency baseline
    add("CR-12", "Market efficiency",
        "Market spread vs own spread",
        [r["spread_line"] for r in rows], [r["own_spread_line"] for r in rows],
        "market closing spread", "own spread",
        "How close the originated line is to the closing market line.")
    add("CR-13", "Market efficiency",
        "Market total vs own total",
        [r["total_line"] for r in rows], [r["own_total_line"] for r in rows],
        "market closing total", "own total", "Same for the total.")
    return out


def base_rates(rows):
    n = len(rows)
    home_win = sum(1 for r in rows if r["margin"] > 0)
    home_cover = sum(1 for r in rows if r["home_cover"] == 1)
    away_cover = sum(1 for r in rows if r["away_cover"] == 1)
    push = sum(1 for r in rows if r["home_cover"] is None)
    over = sum(1 for r in rows if r["over_result"] == 1)
    under = sum(1 for r in rows if r["under_result"] == 1)
    tot_push = sum(1 for r in rows if r["over_result"] is None)
    fav_cover = 0
    fav_n = 0
    for r in rows:
        if r["spread_line"] > 0:
            fav_n += 1; fav_cover += 1 if r["home_cover"] == 1 else 0
        elif r["spread_line"] < 0:
            fav_n += 1; fav_cover += 1 if r["away_cover"] == 1 else 0
    return {
        "games": n,
        "home_win_rate": round(home_win / n, 4),
        "home_ats_cover_rate": round(home_cover / (home_cover + away_cover), 4),
        "away_ats_cover_rate": round(away_cover / (home_cover + away_cover), 4),
        "ats_pushes": push,
        "over_rate": round(over / (over + under), 4),
        "under_rate": round(under / (over + under), 4),
        "total_pushes": tot_push,
        "favourite_ats_cover_rate": round(fav_cover / fav_n, 4) if fav_n else None,
        "favourite_ats_n": fav_n,
        "mean_abs_own_spread_error": round(sum(abs(r["margin"] - r["own_spread_line"]) for r in rows) / n, 3),
        "mean_abs_market_spread_error": round(sum(abs(r["margin"] - r["spread_line"]) for r in rows) / n, 3),
        "mean_abs_own_total_error": round(sum(abs(r["total"] - r["own_total_line"]) for r in rows) / n, 3),
        "mean_abs_market_total_error": round(sum(abs(r["total"] - r["total_line"]) for r in rows) / n, 3),
    }


def key_numbers(rows, lo=-30, hi=30):
    """Distribution of final margins - the NFL 'key numbers' that decide spread bets."""
    c = Counter(int(r["margin"]) for r in rows if r["margin"] is not None)
    total = sum(c.values())
    return [{"margin": m, "games": c.get(m, 0),
             "share": round(c.get(m, 0) / total, 4) if total else None}
            for m in range(lo, hi + 1)]
