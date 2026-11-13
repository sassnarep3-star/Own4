"""00c - Development-window parameter sweep.

The sweep is deliberately restricted to the 1999-2022 development window. The
2023-2024 validation window and the 2025-2026 holdout are not read here, so
this script cannot tune anything on data that is later scored.

Writes: data/derived/development_sweep.json
"""
import json
import math
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import DERIVED, ROOT, dump_json, load_json
import importlib

fc_mod = importlib.import_module("01_forecast")

DEV = (1999, 2022)


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    den = math.sqrt(sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys))
    return num / den if den else None


def dev_metrics(out):
    d = [x for x in out if DEV[0] <= x["season"] <= DEV[1]]
    return {
        "n": len(d),
        "spread_mae": round(statistics.mean(abs(x["margin_error"]) for x in d), 4),
        "total_mae": round(statistics.mean(abs(x["total_error"]) for x in d), 4),
        "pred_actual_margin_correlation": round(
            pearson([x["pred_margin"] for x in d], [x["actual_margin"] for x in d]), 4),
    }


def main():
    rows = []
    for app in ("per_game", "per_season"):
        for rho in (0.03, 0.10):
            for alpha in (0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.15, 0.20):
                for hfa in (0.0, 1.0, 1.5, 2.0, 2.5, 3.0):
                    v = {"alpha": alpha, "rho": rho, "hfa": hfa, "use_rest": False,
                         "rho_application": app}
                    out = fc_mod.run(variant=v)[0]
                    m = dev_metrics(out)
                    m.update({"alpha": alpha, "rho": rho, "hfa": hfa,
                              "rho_application": app})
                    rows.append(m)
    rows.sort(key=lambda r: r["spread_mae"])
    res = {
        "id": "development-sweep",
        "window": "%d-%d (development only; the validation and holdout windows are not read)" % DEV,
        "objective": "lowest mean absolute error of the game margin",
        "note": "This sweep is the evidence behind data/parameter_amendment_1.json.",
        "rows": rows,
        "best": rows[0],
    }
    dump_json(os.path.join(DERIVED, "development_sweep.json"), res)
    print("best:", rows[0])


if __name__ == "__main__":
    main()
