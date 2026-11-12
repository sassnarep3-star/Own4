"""Correlation register.

Computes only quantities the data can actually support. Player-level prop
correlations are NOT computed: no authorized player feed is in scope, so the
rows stay blank and flagged rather than being estimated from a proxy.
"""
from __future__ import annotations

import math
from collections import defaultdict


def pearson(xs, ys):
    n = min(len(xs), len(ys))
    if n < 3:
        return None, n
    mx = sum(xs[:n]) / n
    my = sum(ys[:n]) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs[:n])
    syy = sum((y - my) ** 2 for y in ys[:n])
    if sxx == 0 or syy == 0:
        return None, n
    return sxy / math.sqrt(sxx * syy), n


def fisher_ci(r, n, z=1.96):
    if r is None or n is None or n < 4 or abs(r) >= 1:
        return None, None
    zr = 0.5 * math.log((1 + r) / (1 - r))
    se = 1 / math.sqrt(n - 3)
    lo, hi = zr - z * se, zr + z * se
    return math.tanh(lo), math.tanh(hi)


def phi(a, b):
    """Phi coefficient for two binary vectors."""
    n = len(a)
    if n == 0:
        return None
    n11 = sum(1 for x, y in zip(a, b) if x and y)
    n10 = sum(1 for x, y in zip(a, b) if x and not y)
    n01 = sum(1 for x, y in zip(a, b) if not x and y)
    n00 = n - n11 - n10 - n01
    den = math.sqrt((n11 + n10) * (n01 + n00) * (n11 + n01) * (n10 + n00))
    return None if den == 0 else (n11 * n00 - n10 * n01) / den


def _row(rid, question, x, y, method="Pearson r", note=""):
    r, n = pearson(x, y) if method == "Pearson r" else (phi(x, y), len(x))
    lo, hi = fisher_ci(r, n)
    return {
        "id": rid,
        "question": question,
        "r": None if r is None else round(r, 4),
        "ci95": [None if lo is None else round(lo, 4), None if hi is None else round(hi, 4)],
        "n": n,
        "method": method,
        "status": "DERIVED" if r is not None else "BLOCKED",
        "note": note,
        "source": "computed from data/source/games.csv (nflverse archive) — reproducible via pipeline/correlations.py",
    }


def build(preds):
    hold = [p for p in preds if 2013 <= p["season"] <= 2025 and p["market_margin"] is not None]
    rows = []

    # 1. Do spread and total move together?
    rows.append(_row(
        "C-01", "Are the closing spread and closing total of the same game correlated?",
        [p["market_margin"] for p in hold], [p["market_total"] for p in hold],
        note="Tests whether a game's expected margin carries information about its expected pace."))

    # 2. Are actual margin and actual total correlated?
    rows.append(_row(
        "C-02", "Are the final margin and final total of the same game correlated?",
        [p["actual_margin"] for p in hold], [p["actual_total"] for p in hold],
        note="Game-script dependence: blowouts can suppress or inflate totals."))

    # 3. SGP dependence: favourite covers AND under hits
    cov, und = [], []
    for p in hold:
        if p["actual_margin"] == p["market_margin"] or p["actual_total"] == p["market_total"]:
            continue
        fav_home = p["market_margin"] > 0
        covered = (p["actual_margin"] > p["market_margin"]) if fav_home else (p["actual_margin"] < p["market_margin"])
        cov.append(1 if covered else 0)
        und.append(1 if p["actual_total"] < p["market_total"] else 0)
    rows.append(_row(
        "C-03", "Within one game, does the favourite covering correlate with the under hitting?",
        cov, und, method="Phi", note="This is the dependence a same-game parlay must price. A negative phi means the book's independent multiplication overprices the combo."))

    # 4. Model edge vs market residual (skill of the signal)
    edge = [p["model_margin"] - p["market_margin"] for p in hold]
    resid = [p["actual_margin"] - p["market_margin"] for p in hold]
    rows.append(_row(
        "C-04", "Does the model's disagreement with the closing line predict the actual result?",
        edge, resid, note="If this is ~0 the model has no exploitable information at closing prices."))

    # 5. Cross-game parlay leg independence
    by_week = defaultdict(list)
    for p in hold:
        if p["actual_margin"] != p["market_margin"]:
            by_week[(p["season"], p["week"])].append(p)
    xs, ys = [], []
    for games in by_week.values():
        for i in range(len(games)):
            for j in range(i + 1, len(games)):
                xs.append(1 if games[i]["actual_margin"] > games[i]["market_margin"] else 0)
                ys.append(1 if games[j]["actual_margin"] > games[j]["market_margin"] else 0)
    rows.append(_row(
        "C-05", "Do two legs of a cross-game parlay on the same week move together?",
        xs, ys, method="Phi", note="Near zero is expected: independent games. It is the assumption behind multiplying parlay legs."))

    # 6. Total vs pace proxy unavailable
    rows.append({
        "id": "C-06",
        "question": "Do a quarterback's passing yards and his team's total points correlate in the same game?",
        "r": None, "ci95": [None, None], "n": 0, "method": "Pearson r",
        "status": "BLOCKED",
        "note": "No authorized 2026 player-level feed and no player game logs are bundled in this workspace. No value is estimated.",
        "source": "Open Question Q-07",
    })
    rows.append({
        "id": "C-07",
        "question": "Do two same-game player prop legs (e.g. QB passing yards + WR1 receiving yards) correlate?",
        "r": None, "ci95": [None, None], "n": 0, "method": "Pearson r",
        "status": "BLOCKED",
        "note": "Requires player-level data and archived same-game parlay prices. Neither is in scope. No proxy is substituted.",
        "source": "Open Question Q-08",
    })

    return {
        "generated_utc": "2026-11-12T17:00:00Z",
        "sample": "Regular-season games 2013-2025 with archived closing lines",
        "rows": rows,
        "interpretation_guard": [
            "Correlation is not causation and not an edge.",
            "All values are DERIVED from a third-party archive, not official NFL statistics.",
            "Confidence intervals are Fisher-z approximations and ignore week clustering; treat them as indicative.",
        ],
    }
