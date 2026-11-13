#!/usr/bin/env python3
"""Development-only model selection for the NFL own-lines workspace.

This script is NOT part of the published build and is NOT run by CI. It exists so the two model
parameters are reproducible and so it is on the record that they were chosen on the development
window only.

    python3 nfl-own/engine/tune.py

The selection rule is fixed in advance:

  * scoring window  = walk-forward forecasts whose season is in the DEVELOPMENT seasons only
    (2002-2010). Seasons 2017-2026 are the holdout and are never read here.
  * criterion       = mean absolute error of the own spread against the realised home margin.
  * tie-break       = larger seasons-back (less variance), then larger ridge (more shrinkage).
  * grid            = seasons_back in {3, 5, 8} x ridge in {6, 15, 40, 100}.

The chosen cell and the whole grid are written to data/derived/model_selection.json, which the site
publishes so the choice is auditable rather than asserted. `analysis.py` does not call this script:
it holds the chosen constants and re-derives the grid for the page, so a rebuild is deterministic
and offline.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OWN = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import analysis as A  # noqa: E402

# The published file is written by analysis.py, which re-derives the same grid so the build stays
# deterministic and offline. This script therefore writes an optional development copy and, by
# default, only checks that its own best cell agrees with the constants in force.
OUT = os.path.join(OWN, "data", "derived", "tuning_grid.json")
SEASONS_BACK_GRID = (3, 5, 8)
RIDGE_GRID = (6.0, 15.0, 40.0, 100.0)
DEV_START, DEV_END = A.DEV_SEASONS


def score(games, seasons_back, ridge):
    """Mean absolute spread error over the development window for one parameter cell."""
    saved = (A.SEASONS_BACK, A.RIDGE)
    A.SEASONS_BACK, A.RIDGE = seasons_back, ridge
    try:
        forecasts = A.build_forecasts(games)
    finally:
        A.SEASONS_BACK, A.RIDGE = saved
    dev = [f for f in forecasts
           if DEV_START <= f["season"] <= DEV_END and f["mkt_spread"] is not None]
    mae = sum(abs(f["home_score"] - f["away_score"] - f["own_margin"]) for f in dev) / len(dev)
    return mae, len(dev)


def main():
    games = A.load_games()
    grid = []
    for sb in SEASONS_BACK_GRID:
        for ridge in RIDGE_GRID:
            mae, n = score(games, sb, ridge)
            grid.append({"seasons_back": sb, "ridge": ridge, "dev_mae": round(mae, 4), "n": n})
            print("sb=%d ridge=%3d  dev MAE %.4f  (n=%d)" % (sb, ridge, mae, n))

    best = sorted(grid, key=lambda r: (r["dev_mae"], -r["seasons_back"], -r["ridge"]))[0]
    record = {
        "dataset": "model_selection",
        "rule": "Lowest development-window spread MAE; ties broken towards more seasons and more "
                "shrinkage. The holdout seasons are never read by this script.",
        "dev_seasons": [DEV_START, DEV_END],
        "holdout_seasons": [A.HOLDOUT_START, A.HOLDOUT_START + 10],
        "grid": grid,
        "chosen": best,
        "in_force": {"seasons_back": A.SEASONS_BACK, "ridge": A.RIDGE,
                     "hfa_prior": A.HFA_PRIOR, "hfa_prior_weight": A.HFA_PRIOR_WEIGHT},
        "source_url_archive": "https://github.com/nflverse/nfldata",
        "note": "Development-only artefact. It is not a published result and it does not grade a "
                "strategy.",
        "grid_sources": "https://github.com/nflverse/nfldata",
    }
    in_force = (A.SEASONS_BACK, A.RIDGE)
    picked = (int(best["seasons_back"]), float(best["ridge"]))
    if in_force != picked:
        print("MISMATCH: tune.py picks %s but analysis.py runs %s" % (picked, in_force))
        return 1
    print("agrees with analysis.py: sb=%d ridge=%d (dev MAE %.4f)"
          % (picked[0], picked[1], best["dev_mae"]))
    if "--write" in sys.argv:
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump(record, fh, indent=1, sort_keys=False)
            fh.write("\n")
        print("wrote development copy %s" % os.path.relpath(OUT, OWN))
    else:
        print("no file written (pass --write for a development copy)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
