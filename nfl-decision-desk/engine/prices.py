#!/usr/bin/env python3
"""Origination and price snapshots.

Enforces two requirements mechanically:
  1. ORIGINATION ORDER: side first, then total, then moneyline. The moneyline is derived
     from the side probability, so a moneyline cannot exist without its side first.
  2. FAIR / MARKET / DIFFERENCE as three separate columns, never one blended number.

Price policy (decided before any backtest is published, and published as DEC-1):
  * the NFL publishes no prices; no price in this project is official;
  * closing prices exist 2011-2025 in the vendored archive, opening prices ONLY for 2021;
  * therefore 2026 origination rows carry a fair line and an EMPTY market column with a
    named reason. They are not backfilled from any odds site, because none can be cited.
"""
from __future__ import annotations

import json
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "data", "prices")
os.makedirs(OUT, exist_ok=True)

EVAL = os.path.join(ROOT, "data", "model", "model_evaluation.json")
CORPUS = os.path.join(ROOT, "data", "corpus", "corpus_2026.json")
CAPTURE = "2026-11-15T23:24:27Z"


def main():
    ev = json.load(open(EVAL))
    corpus = json.load(open(CORPUS))
    games = {g["game_id"]: g for g in corpus["games"]}
    rows = ev["model_rows"]

    orig = []
    for r in rows:
        g = games[r["game_id"]]
        fair_m = r["fair_home_margin"]
        fair_spread = r["fair_spread_home"]
        # market column: the closing line the archive carries, or blank with a reason
        mk_spread = g["close_spread_home"]
        mk_total = g["close_total"]
        mk_home_ml = g["close_home_ml"]
        orig.append({
            "game_id": r["game_id"], "week": r["week"], "gameday": r["gameday"],
            "away": r["away"], "home": r["home"],
            # --- 1. SIDE (originated first)
            "fair_side_spread_home": fair_spread,
            "fair_side_label": ("%s %+.1f" % (r["home"] if fair_spread > 0 else r["away"],
                                              -abs(fair_spread))),
            "market_side_spread_home": mk_spread,
            "side_difference": round(fair_spread - mk_spread, 2) if mk_spread is not None else None,
            # --- 2. TOTAL (originated second, two estimators, never collapsed)
            "fair_total_pr02": r["fair_total_pr02"],
            "fair_total_pr03": r["fair_total_pr03"],
            "total_estimator_gap": r["total_estimator_gap"],
            "market_total": mk_total,
            "total_difference_pr02": round(r["fair_total_pr02"] - mk_total, 2) if mk_total is not None else None,
            "total_difference_pr03": round(r["fair_total_pr03"] - mk_total, 2) if mk_total is not None else None,
            # --- 3. MONEYLINE (originated last, from the side probability)
            "fair_home_win_prob": r["p_home_win"],
            "fair_away_win_prob": round(1 - r["p_home_win"], 5),
            "fair_home_ml_american": (round(-100 * r["p_home_win"] / (1 - r["p_home_win"]))
                                      if r["p_home_win"] > 0.5 else
                                      round(100 * (1 - r["p_home_win"]) / r["p_home_win"])),
            "market_home_ml": mk_home_ml,
            "market_away_ml": g["close_away_ml"],
            "ml_difference_cents": None,   # cannot be computed honestly without an opening quote
            "origination_order": "side -> total -> moneyline",
            "captured_utc": CAPTURE,
            "verification_status": "fair line SELF-COMPUTED; market line THIRD-PARTY",
            "primary_source_url": r["source_url"],
            "market_source_url": "https://github.com/nflverse/nfldata/blob/master/data/closing_lines.csv",
            "flags": ["PR-01: no official NFL price source exists; market column is third-party"],
        })

    # ------------------------------------------------ price snapshot store
    # One row per market per game, opening + closing, with the capture clock.
    # Opening numbers do not exist for 2026 (verified: the vendored opening archive is 2021
    # only), so the open columns are BLANK WITH A REASON, never copied from the close.
    snaps = []
    for r in orig:
        g = games[r["game_id"]]
        for market in ("side", "total", "moneyline"):
            open_val, close_val, open_note = None, None, None
            if market == "side":
                close_val = g["close_spread_home"]
            elif market == "total":
                close_val = g["close_total"]
            else:
                close_val = g["close_home_ml"]
            open_note = ("no 2026 opening number is archived anywhere this session could cite; "
                         "the opening column stays blank rather than being filled with the close")
            fair_val = (r["fair_side_spread_home"] if market == "side" else
                        r["fair_total_pr02"] if market == "total" else
                        r["fair_home_win_prob"])
            snaps.append({
                "snapshot_id": "%s-%s" % (r["game_id"], market),
                "game_id": r["game_id"], "week": r["week"], "market": market,
                "open_value": open_val, "close_value": close_val,
                "open_captured_utc": None, "close_captured_utc": CAPTURE,
                "open_unavailable_reason": open_note if open_val is None else None,
                "model_fair_value": fair_val,
                "residual_fair_minus_close": (round(fair_val - close_val, 3)
                                              if close_val is not None else None),
                "source_url": "https://github.com/nflverse/nfldata/blob/master/data/closing_lines.csv",
                "immutable": True,
                "schema_version": "1.0",
            })

    res = [s for s in snaps if s["residual_fair_minus_close"] is not None]
    by_market = {}
    for m in ("side", "total", "moneyline"):
        xs = [s["residual_fair_minus_close"] for s in res if s["market"] == m]
        if not xs:
            continue
        by_market[m] = {
            "n": len(xs),
            "mean_residual": round(statistics.mean(xs), 4),
            "mean_abs_residual": round(statistics.mean(abs(x) for x in xs), 4),
            "sd": round(statistics.pstdev(xs), 4) if len(xs) > 1 else None,
            "interpretation": ("positive mean = our fair value sits above the close on home "
                               "perspective; a persistent non-zero mean is a bias, a near-zero "
                               "mean with large spread is noise"),
        }

    out = {
        "_meta": {
            "built_utc": CAPTURE,
            "origination_order_enforced": ["side", "total", "moneyline"],
            "order_enforcement": ("the moneyline probability is derived from the side margin, "
                                  "so the order is a data dependency, not a convention"),
            "price_data_policy": "DEC-1 - see pages/prices.html; decided before any backtest",
            "snapshots": len(snaps), "originations": len(orig),
            "official_price_source": None,
            "official_price_source_note": "the NFL publishes no betting prices",
        },
        "originations": orig,
        "snapshots": snaps,
        "residual_summary_by_market": by_market,
    }
    json.dump(out, open(os.path.join(OUT, "origination.json"), "w"), indent=1)
    print("originations:", len(orig), "| snapshots:", len(snaps))
    for m, v in by_market.items():
        print("residual %-10s n=%d mean %+.3f |mean| %.3f" % (m, v["n"], v["mean_residual"],
                                                              v["mean_abs_residual"]))


if __name__ == "__main__":
    main()
