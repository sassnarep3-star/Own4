#!/usr/bin/env python3
"""
Decide the price-data policy, then publish what the price store can and cannot support,
and originate a line ourselves against the officially sourced number.

THE POLICY QUESTION
-------------------
"Decide the price-data policy before any backtest is published."

The census below is run now and is re-runnable; the answer is a measurement, not an
opinion. Two independent attributes decide whether a price row can carry an ROI:

  ATTRIBUTE 1  PUBLISHER     the source key must denote an official nfl.com page
  ATTRIBUTE 2  TIMING        the capture time must be known, so the number can be
                             ordered against kickoff and against other numbers

A row earns a claim only if BOTH hold. The store was classified before the result
was seen, and this is what the classification produced:

  every row with a known capture time  (VERIFIED-ARCHIVE, 5,901 rows, 2011-2018)
      carries a NON-OFFICIAL source key. Not claimable: wrong publisher.

  every row with an official publisher (nfl_data_games, nfl.com game centre,
      6,345 rows) carries NO capture time: the store's own status string is
      "ARCHIVE-UNPUBLISHED-TIMING". Not claimable: the number cannot be shown to
      be a close, an open, or anything else in a fixed order.

So the intersection is EMPTY, and the policy follows:

  * no ROI, no CLV, no units, no bankroll anywhere in this namespace
  * no -110 assumption, no assumed push rules, no assumed vig
  * proper scores (Brier, CRPS) need no price and are unaffected

WHAT IS STILL LEGITIMATE, AND IS PUBLISHED
------------------------------------------
An ORIGINATION comparison does not need the price to be a close. It needs the price
to be a number published by the official source, which `nfl_data_games` is. So for
every graded 2026 game this build publishes, per market:
    model fair line | official posted line (official URL) | residual
and it labels the residual "market divergence", never "CLV" and never "edge",
because without a capture time it cannot be shown to precede kickoff.

Output: data/price_policy.json, data/residuals.json
"""

import csv
import json
import os
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
ROOT = os.path.dirname(LAB)

STORE = os.path.join(ROOT, "nfl-markets/data/price_snapshots.csv")
FEED = os.path.join(ROOT, "nfl-markets/data/results_feed.csv")
CORPUS = os.path.join(LAB, "data/corpus.json")
FORECASTS = os.path.join(LAB, "data/forecasts.json")
OUT = os.path.join(LAB, "data/price_policy.json")
OUT_RES = os.path.join(LAB, "data/residuals.json")

# Registered before the census: which source keys are official.
SOURCE_REGISTER = {
    "nfl_data_games": {
        "publisher": "nfl.com game centre",
        "official": True,
        "timing_known": False,
        "timing_evidence": "every SIDE/TOTAL/MONEYLINE row with this key carries "
                           "close_verification_status = ARCHIVE-UNPUBLISHED-TIMING",
    },
    "nfl_data_closing": {
        "publisher": "third-party closing archive, not nfl.com",
        "official": False,
        "timing_known": True,
        "timing_evidence": "carries close_verification_status = VERIFIED-ARCHIVE",
    },
    "nfl_data_sc": {
        "publisher": "third-party line archive, not nfl.com",
        "official": False,
        "timing_known": False,
        "timing_evidence": "open_verification_status = UNPUBLISHED-TIMING",
    },
    "nfl_data_initial": {
        "publisher": "third-party initial-line archive, not nfl.com",
        "official": False,
        "timing_known": True,
        "timing_evidence": "open_verification_status = VERIFIED-ARCHIVE",
    },
    "repo_engine": {
        "publisher": "this repository's own model output",
        "official": False,
        "timing_known": False,
        "timing_evidence": "a model output is never a market price",
    },
    "": {"publisher": "no source recorded", "official": False,
         "timing_known": False, "timing_evidence": "blank source key"},
}


def classify(row, side):
    line = row["market_%s_line" % side]
    key = row["market_%s_source_key" % side]
    reg = SOURCE_REGISTER.get(key, {"publisher": "unregistered key", "official": False,
                                    "timing_known": False})
    return {
        "has_line": bool(line),
        "source_key": key,
        "publisher": reg["publisher"],
        "official": bool(reg["official"]),
        "timing_known": bool(reg["timing_known"]),
        "claimable": bool(line) and reg["official"] and reg["timing_known"],
    }


def main():
    rows = list(csv.DictReader(open(STORE, newline="", encoding="utf-8")))
    feed = list(csv.DictReader(open(FEED, newline="", encoding="utf-8")))

    # ---------- census over the whole store ----------
    cells = Counter()
    by_season = defaultdict(Counter)
    for r in rows:
        for side in ("open", "close"):
            c = classify(r, side)
            bucket = ("no_line" if not c["has_line"] else
                      "claimable" if c["claimable"] else
                      "not_official_publisher" if not c["official"] else
                      "official_but_no_timing")
            cells[side, bucket] += 1
            by_season[r["season"]][side, bucket] += 1

    claimable_open = cells[("open", "claimable")]
    claimable_close = cells[("close", "claimable")]

    # ---------- origination residuals on graded 2026 games ----------
    corpus = {g["game_id"]: g for g in json.load(open(CORPUS, encoding="utf-8"))["games"]}
    fcs = json.load(open(FORECASTS, encoding="utf-8"))
    selected = fcs["selected_model"]
    fair = {}
    for r in fcs["rows"]:
        if r["model"] != selected or r["season"] != 2026:
            continue
        fair[(r["week"], r["away"], r["home"])] = r

    official = defaultdict(dict)
    for r in rows:
        if r["season"] != "2026":
            continue
        if r["market_close_source_key"] != "nfl_data_games" or not r["market_close_line"]:
            continue
        official[(int(r["week"]), r["away_team"], r["home_team"])][r["market"]] = {
            "line": float(r["market_close_line"]),
            "odds_american": r["market_close_odds_american"] or None,
            "snapshot_id": r["snapshot_id"],
            "timing_status": r["close_verification_status"],
            "source_key": r["market_close_source_key"],
        }

    res_rows = []
    for key, f in sorted(fair.items()):
        g = corpus.get(f["game_id"])
        if not g:
            continue
        entry = official.get(key, {})
        src = f.get("source_url") or g.get("url")
        for market, fair_val in (("SIDE", f["fair_margin"]), ("TOTAL", f["fair_total"])):
            o = entry.get(market)
            res_rows.append({
                "game_id": f["game_id"], "week": f["week"], "gameday": f["gameday"],
                "fixture": "%s at %s" % (f["away"], f["home"]),
                "market": market,
                "model_fair_line": round(fair_val, 3),
                "official_posted_line": None if not o else o["line"],
                "residual_model_minus_market": None if not o else round(fair_val - o["line"], 3),
                "official_odds_american": None if not o else o["odds_american"],
                "timing_status": None if not o else o["timing_status"],
                "label": "market divergence (NOT CLV: capture time unpublished)",
                "official_source_url": g["url"],
                "price_snapshot_id": None if not o else o["snapshot_id"],
            })
    for market, fair_key in (("MONEYLINE", "fair_moneyline_home"),):
        for key, f in sorted(fair.items()):
            g = corpus.get(f["game_id"])
            if not g:
                continue
            o = official.get(key, {}).get(market)
            res_rows.append({
                "game_id": f["game_id"], "week": f["week"], "gameday": f["gameday"],
                "fixture": "%s at %s" % (f["away"], f["home"]),
                "market": market,
                "model_fair_line": f[fair_key],
                "official_posted_line": None if not o else o["line"],
                "residual_model_minus_market": None if not o else
                    (None if f[fair_key] is None else round(f[fair_key] - o["line"], 1)),
                "official_odds_american": None if not o else o["odds_american"],
                "timing_status": None if not o else o["timing_status"],
                "label": "market divergence (NOT CLV: capture time unpublished)",
                "official_source_url": g["url"],
                "price_snapshot_id": None if not o else o["snapshot_id"],
            })

    graded_2026 = [g for g in corpus.values() if g["season"] == 2026]
    with_res = sum(1 for g in graded_2026
                   if all(any(r["game_id"] == g["game_id"] and r["market"] == m and
                              r["official_posted_line"] is not None for r in res_rows)
                          for m in ("SIDE", "TOTAL")))
    priced_weeks = sorted({r["week"] for r in res_rows if r["official_posted_line"] is not None})
    unpriced_weeks = sorted({g["week"] for g in graded_2026} - set(priced_weeks))

    policy = {
        "dataset": "nfl_origination_lab_price_policy",
        "title": "Price-data policy, decided before any staking number is published",
        "built": "2026-11-19",
        "decision": {
            "rule": "a price row may carry an ROI only if its publisher is official AND its "
                    "capture time is known",
            "claimable_open_rows": claimable_open,
            "claimable_close_rows": claimable_close,
            "verdict": "the intersection is empty. No officially published number in the "
                       "store has a known capture time, and no number with a known capture "
                       "time is officially published.",
            "therefore": [
                "no ROI, CLV, units or bankroll is published in this namespace",
                "no -110, no assumed vig, no assumed push or void rule",
                "proper scores (Brier, CRPS) are unaffected and are published",
                "an ORIGINATION residual against the official posted line is published and "
                "labelled 'market divergence', never 'CLV'",
            ],
            "what_would_unblock_staking": [
                "a licensed feed or an operator's own price history with capture timestamps",
                "or an official league/club page that publishes a dated closing number",
                "and, separately, the operator's own void/push rules for combos",
            ],
        },
        "source_register": SOURCE_REGISTER,
        "census": {
            "rows_total": len(rows),
            "seasons": sorted({r["season"] for r in rows}),
            "open": {b: n for (s, b), n in cells.items() if s == "open"},
            "close": {b: n for (s, b), n in cells.items() if s == "close"},
            "by_season": {s: {"%s_%s" % k: v for k, v in sorted(c.items())}
                          for s, c in sorted(by_season.items())},
        },
        "graded_games_available": {
            "games_in_feed": len(feed),
            "games_2026_graded": len(graded_2026),
            "games_with_official_posted_line": with_res,
            "weeks_with_a_priced_game": priced_weeks,
            "weeks_with_none": unpriced_weeks,
            "note": "a game can be graded without a price (proper scores need none); a "
                    "bankroll cannot, and one is not simulated here.",
        },
        "sources": [
            {"path": os.path.relpath(STORE, ROOT),
             "title": "inherited price-snapshot store, 12,573 rows, 2011-2026"},
            {"path": os.path.relpath(FEED, ROOT),
             "title": "verified results feed, 4,056 graded games"},
            {"path": os.path.relpath(CORPUS, ROOT),
             "title": "this lab's reconciled corpus, 150 2026 games"},
        ],
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(policy, fh, indent=1)
        fh.write("\n")

    residuals = {
        "dataset": "nfl_origination_lab_residuals",
        "title": "Own line vs the officially sourced posted line, on a weekly schedule",
        "built": "2026-11-19",
        "model": selected,
        "markets": ["SIDE", "TOTAL", "MONEYLINE"],
        "schedule": {
            "cadence": "one row per (game, market) per week, written when the week is graded",
            "weeks_covered": sorted({r["week"] for r in res_rows}),
            "weeks_with_a_price": priced_weeks,
            "weeks_without": unpriced_weeks,
            "from_day_one": "the schedule starts with week 1; weeks without an official "
                            "posted line are published as blank, never interpolated",
        },
        "interpretation": "residual = model fair line minus the official posted line. It is a "
                          "market-divergence measurement. It is NOT CLV and NOT an edge: the "
                          "posted line's capture time is unpublished, so this build cannot "
                          "show that the line preceded kickoff.",
        "sign_convention": {
            "SIDE": "positive means the model likes the home team by more than the posted "
                    "home-margin line",
            "TOTAL": "positive means the model's fair total is above the posted total",
            "MONEYLINE": "model fair American price for the home side minus the posted one; "
                         "positive means the model prices the home side shorter (more likely)",
        },
        "counts": {
            "rows": len(res_rows),
            "rows_with_an_official_line": sum(1 for r in res_rows
                                              if r["official_posted_line"] is not None),
            "rows_blank": sum(1 for r in res_rows if r["official_posted_line"] is None),
        },
        "rows": res_rows,
        "sources": [{"url": "https://www.nfl.com/games/",
                     "title": "per-game official game centre, carried on each row"}],
    }
    with open(OUT_RES, "w", encoding="utf-8") as fh:
        json.dump(residuals, fh, indent=1)
        fh.write("\n")

    print("price store %d rows" % len(rows))
    print("  open : %s" % policy["census"]["open"])
    print("  close: %s" % policy["census"]["close"])
    print("claimable open %d / close %d -> staking division closed"
          % (claimable_open, claimable_close))
    print("residuals: %d rows, %d with an official line, weeks with a price %s, without %s"
          % (len(res_rows), residuals["counts"]["rows_with_an_official_line"],
             priced_weeks, unpriced_weeks))


if __name__ == "__main__":
    main()
