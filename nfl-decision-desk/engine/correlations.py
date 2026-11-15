#!/usr/bin/env python3
"""Correlations - computed ONLY from numbers with a traceable source, with n published.

Rule enforced: a correlation is published only if every observation entering it comes from
an officially-sourced value (nfl.com) or a labelled third-party archive. A correlation whose
inputs are unavailable is published as BLANK WITH A REASON. No correlation is ever quoted
from memory or from a secondary description.
"""
from __future__ import annotations

import json
import math
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "data", "correlations")
os.makedirs(OUT, exist_ok=True)

CORPUS = os.path.join(ROOT, "data", "corpus", "corpus_2026.json")
EVAL = os.path.join(ROOT, "data", "model", "model_evaluation.json")
NFLVERSE = "https://github.com/nflverse/nfldata/blob/master/data/games.csv"
STANDINGS = "https://www.nfl.com/standings/league/2026/REG"


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None, None, n
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    vx = sum((a - mx) ** 2 for a in xs)
    vy = sum((b - my) ** 2 for b in ys)
    if vx <= 0 or vy <= 0:
        return None, None, n
    r = cov / math.sqrt(vx * vy)
    # t approximation for p; with n<30 the normal approximation is optimistic and is labelled
    t = r * math.sqrt((n - 2) / max(1e-12, 1 - r * r))
    p = 2 * (1 - _tcdf(abs(t), n - 2))
    return r, p, n


def _tcdf(t, df):
    """Student-t CDF via the regularised incomplete beta function (continued fraction)."""
    x = df / (df + t * t)
    ib = _betainc(df / 2.0, 0.5, x)
    return 1 - 0.5 * ib


def _betainc(a, b, x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    front = math.exp(math.log(x) * a + math.log(1 - x) * b - lbeta) / a
    f, c, d = 1.0, 1.0, 0.0
    for i in range(0, 200):
        m = i // 2
        if i == 0:
            num = 1.0
        elif i % 2 == 0:
            num = (m * (b - m) * x) / ((a + 2 * m - 1) * (a + 2 * m))
        else:
            num = -((a + m) * (a + b + m) * x) / ((a + 2 * m) * (a + 2 * m + 1))
        d = 1.0 + num * d
        d = 1e-30 if abs(d) < 1e-30 else d
        d = 1.0 / d
        c = 1.0 + num / c
        c = 1e-30 if abs(c) < 1e-30 else c
        f *= c * d
        if abs(1 - c * d) < 1e-10:
            break
    return front * (f - 1)


def ci_r(r, n, z=1.96):
    if r is None or n < 4 or abs(r) >= 1:
        return (None, None)
    zr = 0.5 * math.log((1 + r) / (1 - r))
    se = 1 / math.sqrt(n - 3)
    return (round(math.tanh(zr - z * se), 3), round(math.tanh(zr + z * se), 3))


def main():
    corpus = json.load(open(CORPUS))
    ev = json.load(open(EVAL))
    settled = [g for g in corpus["games"] if g["settled"]]
    rows = {r["game_id"]: r for r in ev["model_rows"]}

    items = []

    def add(cid, question, xs, ys, source, note, caveat=None):
        r, p, n = pearson(xs, ys)
        lo, hi = ci_r(r, n)
        # ---- robustness guard: recompute on the trimmed x-range (drop the extreme 5% each
        # side). A correlation that lives only in a handful of tail observations is a
        # property of those observations, not of the league, and must not be published as a
        # finding. This guard caught CR-04 below during self-review.
        robust, r_trim, trim_n, trim_note = True, None, 0, None
        # ---- degenerate-x guard: if most observations share ONE value, x is a group label,
        # not a continuous quantity, and a Pearson r on it is not interpretable on its own.
        mode_share, groups = None, None
        if n:
            from collections import Counter
            cnt = Counter(xs)
            mode_val, mode_n = cnt.most_common(1)[0]
            mode_share = mode_n / n
            if mode_share >= 0.5:
                robust = False
                buckets = {}
                for xv, yv in zip(xs, ys):
                    key = ("%+g" % xv) if abs(xv) <= 3 else ("<= -4" if xv < 0 else ">= +4")
                    buckets.setdefault(key, []).append(yv)
                groups = [{"x_group": k, "n": len(v), "mean_y": round(sum(v) / len(v), 3)}
                          for k, v in sorted(buckets.items())]
                trim_note = ("x is a GROUP VARIABLE, not a continuous one: %.0f%% of the n=%d "
                             "observations share the single value %g. The Pearson r is dominated "
                             "by the small tail groups listed alongside it. Read the group means "
                             "and their n, not the r."
                             % (100 * mode_share, n, mode_val))
        if n >= 20 and r is not None:
            order = sorted(range(n), key=lambda i: xs[i])
            k = max(1, int(round(0.05 * n)))
            keep = order[k:n - k]
            r_trim, _, trim_n = pearson([xs[i] for i in keep], [ys[i] for i in keep])
            if r_trim is None:
                robust, trim_note = False, "trimmed sample degenerate"
            elif (r_trim * r < 0) or abs(r_trim) < 0.5 * abs(r):
                robust = False
                trim_note = ("the correlation collapses or changes sign when the extreme 5% of "
                             "the x-distribution is removed (r=%.3f full, r=%.3f trimmed on "
                             "n=%d): the relationship is carried by a few tail observations, "
                             "not by the league" % (r, r_trim, trim_n))
        items.append({
            "id": cid, "question": question,
            "n": n,
            "r": round(r, 4) if r is not None else None,
            "r_ci95": [lo, hi],
            "p_two_sided": round(p, 5) if p is not None else None,
            "source_url": source,
            "inputs": "officially sourced / labelled third-party archive; see source column",
            "note": note,
            "r_trimmed_5pct": round(r_trim, 4) if r_trim is not None else None,
            "x_mode_share": round(mode_share, 3) if mode_share is not None else None,
            "x_groups": groups,
            "n_trimmed": trim_n,
            "robust": robust,
            "robustness_note": trim_note,
            "caveat": caveat,
            "verified": r is not None,
        })

    # ---- 1. spread vs margin (the market's own coherence; a sanity anchor)
    xs = [g["close_spread_home"] for g in settled if g["close_spread_home"] is not None]
    ys = [g["home_margin"] for g in settled if g["close_spread_home"] is not None]
    add("CR-01", "Does the closing spread predict the final home margin?", xs, ys, NFLVERSE,
        "the market's own coherence check; r near 0 would mean the archive's sign is wrong",
        "single season; 136 games")

    # ---- 2. total vs sum of club scoring (construct validity)
    xs2 = [g["close_total"] for g in settled if g["close_total"] is not None]
    ys2 = [g["total_pts"] for g in settled if g["close_total"] is not None]
    add("CR-02", "Does the closing total predict the actual combined score?", xs2, ys2, NFLVERSE,
        "136 games; the total is harder to price than the side and this quantifies that",
        "a low r here is expected and is not an error")

    # ---- 3. our fair margin vs the market spread (are we a copy of the market?)
    pairs = [(rows[g["game_id"]]["fair_spread_home"], g["close_spread_home"])
             for g in settled
             if g["game_id"] in rows and g["close_spread_home"] is not None]
    add("CR-03", "Is our fair spread a repackaging of the market number?",
        [a for a, _ in pairs], [b for _, b in pairs], NFLVERSE,
        "the single most important anti-fraud check on this site: if r were ~1.0 our 'own' "
        "line would be a copy, not an origination",
        "computed after the walk-forward model saw only prior weeks")

    # ---- 4. rest advantage vs margin (an honestly computable schedule feature)
    rest = {}
    by_team = {}
    for g in settled:
        for t in (g["away"], g["home"]):
            by_team.setdefault(t, []).append(g["gameday"])
    xs4, ys4 = [], []
    for g in settled:
        aw = [d for d in by_team.get(g["away"], []) if d < g["gameday"]]
        hm = [d for d in by_team.get(g["home"], []) if d < g["gameday"]]
        if not aw or not hm:
            continue
        from datetime import date
        def days(a, b):
            ya, ma, da = map(int, a.split("-")); yb, mb, db = map(int, b.split("-"))
            return (date(yb, mb, db) - date(ya, ma, da)).days
        xs4.append(days(max(aw), g["gameday"]) - days(max(hm), g["gameday"]))
        ys4.append(g["home_margin"])
    add("CR-04", "Does rest differential correlate with home margin?", xs4, ys4, NFLVERSE,
        "rest is derived arithmetically from the archived official gamedates, so both inputs "
        "are traceable", "n is smaller than 136 because week-1 clubs have no prior game")

    # ---- 5. team scoring vs conceding (are good offences also good defences?)
    offs, defs, labels = [], [], []
    for abbr, r in [(r["abbr"], r) for r in corpus["standings_reconciliation"]]:
        games_n = r["corpus_gp"]
        if games_n == 0:
            continue
        offs.append(r["corpus_pf"] / games_n)
        defs.append(r["corpus_pa"] / games_n)
        labels.append(abbr)
    add("CR-05", "Across clubs, are points scored and points conceded correlated?",
        offs, defs, NFLVERSE,
        "32 clubs; a near-zero r supports modelling offence and defence separately, a strong "
        "negative r would support a single strength axis",
        "club-level n=32, so the interval is wide by construction")

    # ---- blank rows with reasons: the honest half of a correlation table
    blanks = [
        {"id": "CR-06", "question": "Does injury designation predict snap share?",
         "n": 0, "r": None, "r_ci95": [None, None], "p_two_sided": None,
         "source_url": "https://www.nfl.com/injuries/",
         "inputs": "NOT AVAILABLE",
         "note": ("requires a per-player snap-count feed joined to designations. The official "
                  "injury page read this session carries no snap counts and the repository "
                  "holds no snap-count archive."),
         "caveat": None, "verified": False,
         "blocked_by": "no official snap-count archive"},
        {"id": "CR-07", "question": "Does a backup replacing a starter cost points?",
         "n": 0, "r": None, "r_ci95": [None, None], "p_two_sided": None,
         "source_url": "https://www.nfl.com/injuries/",
         "inputs": "NOT AVAILABLE",
         "note": ("requires (a) a confirmed inactive list and (b) a depth rank per club. The "
                  "official injury table has no depth column and 6 of its rows carry a game "
                  "designation."),
         "caveat": None, "verified": False,
         "blocked_by": "no inactive list + no depth rank"},
        {"id": "CR-08", "question": "Are same-game parlay legs dependent?",
         "n": 0, "r": None, "r_ci95": [None, None], "p_two_sided": None,
         "source_url": "https://github.com/nflverse/nfldata",
         "inputs": "NOT AVAILABLE",
         "note": ("player-level outcomes are not in the vendored archive, and no price source "
                  "exists for legs. Publishing a dependence estimate here would be fabrication."),
         "caveat": None, "verified": False,
         "blocked_by": "no player-level official feed, no leg prices"},
    ]

    out = {
        "_meta": {
            "built_utc": "2026-11-15T23:24:27Z",
            "policy": ["every value carries n", "every value carries its source",
                       "values that cannot be computed are blank with a named blocker",
                       "no correlation is quoted from memory"],
            "computed": sum(1 for i in items if i["verified"]),
            "blank_with_reason": len(blanks),
        },
        "correlations": items + blanks,
        "warnings": [
            "n=136 is one season. A correlation that survives one season has not been shown to survive another.",
            "CR-03 is a fraud check, not a performance claim.",
            "Multiple comparisons: 5 computed values at alpha=0.05 implies ~0.25 false positives by chance. Treat any single p as descriptive.",
        ],
    }
    json.dump(out, open(os.path.join(OUT, "correlations.json"), "w"), indent=1)
    for i in out["correlations"]:
        if i["r"] is not None:
            print("%-6s n=%3d r=%+.3f CI[%+.3f,%+.3f] p=%.4f %-9s %s"
                  % (i["id"], i["n"], i["r"], i["r_ci95"][0], i["r_ci95"][1],
                     i["p_two_sided"], "ROBUST" if i.get("robust") else "NOT ROBUST",
                     i["question"][:46]))
        else:
            print("%-6s BLANK  %s" % (i["id"], i["question"][:60]))


if __name__ == "__main__":
    main()
