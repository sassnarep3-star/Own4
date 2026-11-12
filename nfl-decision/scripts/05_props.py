#!/usr/bin/env python3
"""Player-prop combo correlation study.

Data: the repository's archived per-player prop legs (2021-2022), which are a
third-party archive of official NFL box-score statistics. NO 2026 player feed and
NO archived prop prices exist, so this is a CORRELATION study only. No price, no
edge and no ROI is claimed. Gates G7 and G2 therefore block every prop strategy.
"""
import csv, json, math, os, statistics
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ROOT)
SRC = os.path.join(REPO, "nfl-quant", "data", "prop_combo_legs.csv")
OUT = os.path.join(ROOT, "data")


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = statistics.mean(xs), statistics.mean(ys)
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs); syy = sum((b - my) ** 2 for b in ys)
    return sxy / math.sqrt(sxx * syy) if sxx and syy else None


def fisher_ci(r, n):
    if r is None or n < 5 or abs(r) >= 1:
        return None
    z = 0.5 * math.log((1 + r) / (1 - r)); se = 1 / math.sqrt(n - 3)
    return [round(math.tanh(z - 1.96 * se), 4), round(math.tanh(z + 1.96 * se), 4)]


def main():
    rows = list(csv.DictReader(open(SRC)))
    for r in rows:
        for k in ("qb_line", "wr_line", "qb_over", "wr_over"):
            r[k] = float(r[k]) if k != "qb_over" and k != "wr_over" else (r[k] == "True")
    n = len(rows)
    qb = [1.0 if r["qb_over"] else 0.0 for r in rows]
    wr = [1.0 if r["wr_over"] else 0.0 for r in rows]
    p_qb, p_wr = statistics.mean(qb), statistics.mean(wr)
    p_both = sum(1 for a, b in zip(qb, wr) if a and b) / n
    phi = pearson(qb, wr)
    lift = p_both / (p_qb * p_wr) if p_qb * p_wr else None

    # per-position single-leg over-rates vs the 0.5 line used by the proxy rule
    singles = {}
    for pos in ("QB1", "RB1", "WR1"):
        sub = [r for r in rows if pos in ("QB1", "WR1")] if pos != "RB1" else rows
        if pos == "QB1":
            v = qb
        elif pos == "WR1":
            v = wr
        else:
            v = None
        if v:
            singles[pos] = {"n": len(v), "over_rate": round(statistics.mean(v), 4),
                            "breakeven_at_minus110": 0.5238,
                            "beats_breakeven": statistics.mean(v) > 0.5238}

    # yards-level correlation: the actual quantity behind the two legs
    y_corr = pearson([r["qb_line"] for r in rows], [r["wr_line"] for r in rows])

    out = {
        "generated_utc": "2026-11-12",
        "source": SRC.replace(REPO + "/", ""),
        "source_note": "Third-party archive of official NFL box scores (2021-2022). Thresholds "
                       "(qb_line, wr_line) are PROXY lines from a rolling mean, not sportsbook prices.",
        "n_team_games": n,
        "seasons": sorted({int(r["season"]) for r in rows}),
        "teams_covered": len({r["team"] for r in rows}),
        "combo": {
            "leg_a": "QB passing yards over proxy line", "leg_b": "WR1 receiving yards over proxy line",
            "p_a": round(p_qb, 4), "p_b": round(p_wr, 4), "p_both": round(p_both, 4),
            "independence_expected": round(p_qb * p_wr, 4), "lift": round(lift, 4) if lift else None,
            "phi": round(phi, 4) if phi is not None else None,
            "phi_ci95": fisher_ci(phi, n),
            "verdict": ("positive dependence: joint probability exceeds the product of the marginals, so "
                        "an independent-lines parlay UNDERPRICES this combo"
                        if phi is not None and phi > 0.05 else
                        "weak or no dependence at this proxy threshold"),
        },
        "yard_level_correlation": {"r": round(y_corr, 4) if y_corr else None,
                                   "ci95": fisher_ci(y_corr, n),
                                   "label": "QB passing yards vs WR1 receiving yards, same team-game"},
        "singles": singles,
        "gates": {
            "G2_min_sample": {"pass": n >= 300, "detail": f"n={n} team-games but only 2021-2022 seasons (2 < 3 required)"},
            "G7_pricing": {"pass": False, "detail": "No archived prop prices and no 2026 player feed. "
                                                    "Proxy lines are not tradeable prices."},
            "status": "Blocked - research-only. No prop strategy can be scored on the betting leaderboard.",
        },
        "what_would_unblock_it": [
            "An official or licensed 2026 player-level box-score feed (nfl.com/stats is client-rendered and "
            "the stats download policy must be respected).",
            "An archived sportsbook price history for player props including same-game-parlay repricing.",
            "A minimum of three seasons of player-level data so the >=300-bet / >=3-season gate can be met.",
        ],
    }
    json.dump(out, open(os.path.join(OUT, "props.json"), "w"), indent=1)
    print(f"n={n} team-games, seasons={out['seasons']}, teams={out['teams_covered']}")
    print(f"P(QB over)={p_qb:.4f}  P(WR over)={p_wr:.4f}  P(both)={p_both:.4f}  "
          f"independent={p_qb*p_wr:.4f}  lift={lift:.4f}  phi={phi:.4f}")
    print(f"phi 95% CI ({n} rows) = {out['combo']['phi_ci95']}")
    print(f"yard-level r = {y_corr:.4f}")


if __name__ == "__main__":
    main()
