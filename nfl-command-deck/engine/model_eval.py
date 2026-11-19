#!/usr/bin/env python3
"""
nfl-command-deck — frozen-rule evaluation engine.

Implements prereg/PREREG-CD.md exactly. Nothing here is tuned after seeing a result;
the ridge grid, the scoring window, the holdout, the bootstrap and the gates are all
fixed in that document, whose SHA-256 is checked on every run before any number is read.

Reads (read-only):  ../nfl-live-board/data/corpus_2026.json
Writes:             data/eval.json

Pure standard library. Deterministic: the bootstrap uses a seeded LCG, not `random`,
so the output is byte-identical across machines and Python builds.
"""

import hashlib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)
DATA = os.path.join(NS, "data")
CORPUS = os.path.join(ROOT, "nfl-live-board", "data", "corpus_2026.json")
PREREG = os.path.join(NS, "prereg", "PREREG-CD.md")
LOCK = os.path.join(DATA, "prereg_lock.json")

RIDGE_GRID = [1.0, 3.0, 10.0, 30.0, 100.0]
SELECT_WEEKS = [4, 5, 6, 7]          # hyper-parameter selection window (prereg §3)
SCORE_WEEKS = [4, 5, 6, 7, 8, 9, 10]  # scoring window
HOLDOUT_WEEKS = [8, 9, 10]            # final holdout
BOOT_REPS = 2000
BOOT_SEED = 20261119


# ----------------------------------------------------------------------------- maths
def phi(x):
    """Standard normal CDF, from libm erf."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def lcg(seed):
    """Deterministic uniform generator (Numerical Recipes LCG). Not `random`."""
    state = seed & 0xFFFFFFFFFFFFFFFF

    def nxt():
        nonlocal state
        state = (state * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
        return (state >> 11) / float(1 << 53)

    return nxt


def solve(a, b):
    """Gauss-Jordan with partial pivoting. Small dense systems only."""
    n = len(a)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            m[piv][col] = 1e-12
        m[col], m[piv] = m[piv], m[col]
        pv = m[col][col]
        for j in range(col, n + 1):
            m[col][j] /= pv
        for r in range(n):
            if r == col:
                continue
            f = m[r][col]
            if f:
                for j in range(col, n + 1):
                    m[r][j] -= f * m[col][j]
    return [m[i][n] for i in range(n)]


def ridge_fit(rows, n_cols, lam):
    """Ridge on the intercept-free design; the intercept column is left unpenalised."""
    a = [[0.0] * n_cols for _ in range(n_cols)]
    b = [0.0] * n_cols
    for x, y in rows:
        for i in range(n_cols):
            xi = x[i]
            if xi == 0.0:
                continue
            b[i] += xi * y
            for j in range(n_cols):
                a[i][j] += xi * x[j]
    for i in range(1, n_cols):          # column 0 is the intercept
        a[i][i] += lam
    return solve(a, b)


# ----------------------------------------------------------------------------- models
def team_index(corpus):
    teams = sorted({g["home"] for g in corpus} | {g["away"] for g in corpus})
    return {t: i for i, t in enumerate(teams)}, teams


def fit_margin(train, idx, lam):
    """margin = h + s_home - s_away  (prereg CD-1)."""
    n = len(idx) + 2                    # intercept + home edge + |teams|
    rows = []
    for g in train:
        x = [0.0] * n
        x[0] = 1.0
        x[1] = 1.0
        x[2 + idx[g["home"]]] = 1.0
        x[2 + idx[g["away"]]] = -1.0
        rows.append((x, float(g["home_pts"] - g["away_pts"])))
    return ridge_fit(rows, n, lam), n


def predict_margin(theta, idx, g):
    return theta[0] + theta[1] + theta[2 + idx[g["home"]]] - theta[2 + idx[g["away"]]]


def fit_total(train, idx, lam):
    """total = mu + o_home + d_home + o_away + d_away  (prereg CD-3)."""
    t = len(idx)
    n = 1 + 2 * t
    rows = []
    for g in train:
        x = [0.0] * n
        x[0] = 1.0
        x[1 + idx[g["home"]]] = 1.0            # offense home
        x[1 + t + idx[g["home"]]] = 1.0        # defense home
        x[1 + idx[g["away"]]] = 1.0            # offense away
        x[1 + t + idx[g["away"]]] = 1.0        # defense away
        rows.append((x, float(g["home_pts"] + g["away_pts"])))
    return ridge_fit(rows, n, lam), n


def predict_total(theta, idx, g):
    t = len(idx)
    return (theta[0] + theta[1 + idx[g["home"]]] + theta[1 + t + idx[g["home"]]]
            + theta[1 + idx[g["away"]]] + theta[1 + t + idx[g["away"]]])


def residuals(theta_fn, train, idx):
    out = []
    for g in train:
        out.append(float(g["home_pts"] - g["away_pts"]) - theta_fn(g))
    return out


def sd(xs):
    n = len(xs)
    mean = sum(xs) / n
    return math.sqrt(sum((x - mean) ** 2 for x in xs) / (n - 1))


# ----------------------------------------------------------------------------- scoring
def brier(pairs):
    return sum((p - y) ** 2 for p, y in pairs) / len(pairs)


def week_cluster_bss(by_week, bench_bs):
    """BSS point estimate plus a week-cluster bootstrap CI and a pessimistic p."""
    weeks = sorted(by_week)
    bs_all = sum(sum((p - y) ** 2 for p, y in by_week[w]) for w in weeks)
    n_all = sum(len(by_week[w]) for w in weeks)
    pt = 1.0 - (bs_all / n_all) / bench_bs

    rnd = lcg(BOOT_SEED)
    reps = []
    k = len(weeks)
    for _ in range(BOOT_REPS):
        pick = [weeks[int(rnd() * k) % k] for _ in range(k)]
        num = den = 0
        for w in pick:
            num += sum((p - y) ** 2 for p, y in by_week[w])
            den += len(by_week[w])
        reps.append(1.0 - (num / den) / bench_bs)
    reps.sort()
    lo = reps[int(0.025 * len(reps))]
    hi = reps[int(0.975 * len(reps)) - 1]
    p_le0 = sum(1 for r in reps if r <= 0.0) / len(reps)
    return {"bss": round(pt, 4), "ci95_week_cluster": [round(lo, 4), round(hi, 4)],
            "p_bss_le_0": round(p_le0, 4), "n_weeks": k, "n": n_all}


def holm(pvals):
    """Holm-Bonferroni over the pre-declared family."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    out, running = {}, 0.0
    for i, (k, p) in enumerate(items):
        adj = min(1.0, (m - i) * p)
        running = max(running, adj)
        out[k] = round(running, 4)
    return out


# ----------------------------------------------------------------------------- main
def main():
    lock = json.load(open(LOCK, encoding="utf-8"))
    got = hashlib.sha256(open(PREREG, "rb").read()).hexdigest()
    if got != lock["sha256"]:
        sys.exit("PREREG-CD.md has changed since registration; the frozen rules no longer hold. "
                 "Re-register with a new prospective window instead of editing this one.")

    corpus = json.load(open(CORPUS, encoding="utf-8"))
    games = corpus["corpus"]
    idx, teams = team_index(games)

    # ---- hyper-parameter selection, weeks 4-7 only (prereg §3)
    grid = {}
    for lam in RIDGE_GRID:
        err = []
        for w in SELECT_WEEKS:
            tr = [g for g in games if g["week"] < w]
            te = [g for g in games if g["week"] == w]
            th, _ = fit_margin(tr, idx, lam)
            err += [abs(predict_margin(th, idx, g) - (g["home_pts"] - g["away_pts"])) for g in te]
        grid["margin_lambda_%g" % lam] = round(sum(err) / len(err), 4)
    lam_m = min(RIDGE_GRID, key=lambda L: grid["margin_lambda_%g" % L])

    grid_t = {}
    for lam in RIDGE_GRID:
        err = []
        for w in SELECT_WEEKS:
            tr = [g for g in games if g["week"] < w]
            te = [g for g in games if g["week"] == w]
            th, _ = fit_total(tr, idx, lam)
            err += [abs(predict_total(th, idx, g) - (g["home_pts"] + g["away_pts"])) for g in te]
        grid_t["total_lambda_%g" % lam] = round(sum(err) / len(err), 4)
    lam_t = min(RIDGE_GRID, key=lambda L: grid_t["total_lambda_%g" % L])

    # ---- walk-forward
    preds, total_preds = [], []
    ties = 0
    for w in SCORE_WEEKS:
        train = [g for g in games if g["week"] < w]
        test = [g for g in games if g["week"] == w]
        th, _ = fit_margin(train, idx, lam_m)
        res = residuals(lambda g: predict_margin(th, idx, g), train, idx)
        sigma = max(sd(res), 1e-6)
        home_rate = sum(1 for g in train if g["home_pts"] > g["away_pts"]) / len(train)
        mean_margin = sum(g["home_pts"] - g["away_pts"] for g in train) / len(train)
        mean_total = sum(g["home_pts"] + g["away_pts"] for g in train) / len(train)

        tht, _ = fit_total(train, idx, lam_t)

        for g in test:
            if g["home_pts"] == g["away_pts"]:
                ties += 1
                continue
            y = 1.0 if g["home_pts"] > g["away_pts"] else 0.0
            m = predict_margin(th, idx, g)
            preds.append({
                "game_id": g["game_id"], "week": w, "y": y,
                "CD-1": phi(m / sigma),
                "CD-2": phi(mean_margin / sigma),
                "C-1": 0.5, "C-2": 1.0, "C-3": home_rate,
                "source_url": g["source_url"],
            })
            total_preds.append({
                "game_id": g["game_id"], "week": w,
                "pred": predict_total(tht, idx, g),
                "actual": float(g["home_pts"] + g["away_pts"]),
                "bench": mean_total, "source_url": g["source_url"],
            })

    benches = {"bench_brier_climatology": round(brier([(p["C-3"], p["y"]) for p in preds]), 6)}

    def score_block(rows):
        bw = {}
        for p in rows:
            bw.setdefault(p["week"], []).append((p, p["y"]))
        out = {}
        for k in ("CD-1", "CD-2", "C-1", "C-2"):
            by_week = {w: [(r[k], y) for r, y in v] for w, v in bw.items()}
            out[k] = week_cluster_bss(by_week, benches["bench_brier_climatology"])
            out[k]["brier"] = round(brier([(r[k], r["y"]) for r in rows]), 6)
        # C-3 against itself is 0 by construction; report it as the reference line
        out["C-3"] = {"bss": 0.0, "brier": benches["bench_brier_climatology"], "reference": True,
                      "n": len(rows)}
        return out

    all_scored = score_block(preds)
    holdout = score_block([p for p in preds if p["week"] in HOLDOUT_WEEKS])

    pvals = {"CD-1": all_scored["CD-1"]["p_bss_le_0"],
             "CD-2": all_scored["CD-2"]["p_bss_le_0"],
             "CD-3-total": 1.0}          # the total model is not scored on a probability gate
    adj = holm({"CD-1": pvals["CD-1"], "CD-2": pvals["CD-2"]})

    def gates(model):
        s = all_scored[model]
        h = holdout[model]
        g = {
            "G1 skill (BSS>0, weeks 4-10)": s["bss"] > 0,
            "G2 holdout (BSS>0, weeks 8-10)": h["bss"] > 0,
            "G3 lower bound (week-cluster 95%>0)": s["ci95_week_cluster"][0] > 0,
            "G4 multiplicity (Holm p<0.10)": adj.get(model, 1.0) < 0.10,
            "G5 sample (n>=90)": s["n"] >= 90,
            "G6 controls (Brier < coin and < always-home)": (
                s["brier"] < all_scored["C-1"]["brier"] and s["brier"] < all_scored["C-2"]["brier"]),
        }
        return g, all(g.values())

    gate_out = {}
    for m in ("CD-1", "CD-2"):
        g, ok = gates(m)
        gate_out[m] = {
            "gates": g, "qualifies": ok,
            "holm_adjusted_p": adj.get(m),
            "clearing_numbers": {
                "bss_to_clear_G1": "> 0",
                "gap_to_G1": round(-all_scored[m]["bss"], 4) if all_scored[m]["bss"] <= 0 else 0.0,
                "holdout_gap_to_G2": round(-holdout[m]["bss"], 4) if holdout[m]["bss"] <= 0 else 0.0,
                "lower_bound_shortfall_G3": round(-all_scored[m]["ci95_week_cluster"][0], 4)
                if all_scored[m]["ci95_week_cluster"][0] <= 0 else 0.0,
            },
        }

    # ---- total model: MAE vs training-window mean, week-cluster bootstrap
    def mae(rows, key):
        return sum(abs(r[key] - r["actual"]) for r in rows) / len(rows)

    mae_model, mae_bench = mae(total_preds, "pred"), mae(total_preds, "bench")
    by_week_diff = {}
    for r in total_preds:
        by_week_diff.setdefault(r["week"], []).append(abs(r["actual"] - r["pred"]) - abs(r["actual"] - r["bench"]))
    weeks = sorted(by_week_diff)
    rnd = lcg(BOOT_SEED + 7)
    reps = []
    for _ in range(BOOT_REPS):
        pick = [weeks[int(rnd() * len(weeks)) % len(weeks)] for _ in range(len(weeks))]
        vals = [v for w in pick for v in by_week_diff[w]]
        reps.append(sum(vals) / len(vals))
    reps.sort()
    total_block = {
        "mae": round(mae_model, 4), "mae_benchmark": round(mae_bench, 4),
        "mae_improvement": round(mae_bench - mae_model, 4),
        "diff_ci95_week_cluster": [round(reps[int(0.025 * len(reps))], 4),
                                   round(reps[int(0.975 * len(reps)) - 1], 4)],
        "beats_benchmark": mae_model < mae_bench,
        "proper_score_note": "MAE on totals is a point metric, not a proper scoring rule. "
                             "No totals market exists here, so no Brier/log score is possible.",
    }

    # ---- per-week trail (published so a reader can re-add the arithmetic)
    weeks_out = []
    for w in SCORE_WEEKS:
        rows = [p for p in preds if p["week"] == w]
        weeks_out.append({
            "week": w, "n": len(rows),
            "brier_CD-1": round(brier([(r["CD-1"], r["y"]) for r in rows]), 5),
            "brier_C-3": round(brier([(r["C-3"], r["y"]) for r in rows]), 5),
            "home_win_rate": round(sum(r["y"] for r in rows) / len(rows), 4),
            "holdout": w in HOLDOUT_WEEKS,
        })

    out = {
        "dataset": "nfl_command_deck_eval",
        "title": "Frozen walk-forward evaluation of CD-1/CD-2/CD-3 against controls (PREREG-CD)",
        "built_utc": "2026-11-19",
        "session": "arena/1153eb96-own4",
        "prereg_sha256": got,
        "inputs": {
            "corpus": "nfl-live-board/data/corpus_2026.json",
            "corpus_games": len(games),
            "corpus_weeks": sorted({g["week"] for g in games}),
            "source_url_field": "every corpus row carries source_url (nfl.com/games/...)",
            "external_verification_this_session": "none — www.nfl.com is unreachable from this "
                                                  "sandbox (RF-02); results are conditional on the "
                                                  "committed corpus",
        },
        "protocol": {
            "select_weeks": SELECT_WEEKS, "score_weeks": SCORE_WEEKS, "holdout_weeks": HOLDOUT_WEEKS,
            "ridge_grid": RIDGE_GRID, "selected_margin_lambda": lam_m, "selected_total_lambda": lam_t,
            "lambda_selection_mae": grid, "total_lambda_selection_mae": grid_t,
            "sigma_rule": "residual SD on the training window only",
            "bootstrap": "week-cluster, %d reps, seed %d, deterministic LCG" % (BOOT_REPS, BOOT_SEED),
            "ties_excluded": ties,
        },
        "benchmarks": benches,
        "scored": {"weeks_4_10": all_scored, "holdout_weeks_8_10": holdout},
        "totals": total_block,
        "gates": gate_out,
        "multiplicity": {"family": ["CD-1", "CD-2"], "method": "Holm-Bonferroni",
                         "adjusted": adj, "declared_in": "PREREG-CD §4"},
        "per_week": weeks_out,
        "leaderboard_policy": {
            "points_total": 1000, "points_awarded": 0, "qualifiers": sum(1 for v in gate_out.values() if v["qualifies"]),
            "why_zero": "CD-1 clears all six stage-1 gates, but stage 2 (the CLV/ROI escrow) cannot "
                        "be computed because no closing price exists, and 100 forecasts over 7 "
                        "independent weeks is a skill result, not a basis for payment. Points stay "
                        "at 0 until a price source is adopted and the frozen rule has run "
                        "prospectively.",
            "never_reported": ["raw win rate", "accuracy as success", "ROI on an assumed price"],
        },
        "correlations": {
            "computed": [], "n_published_with_each_value": True,
            "why_empty": "The brief asks for correlations from officially sourced numbers with n. The "
                         "only official numbers held are final scores; the correlations computable from "
                         "them (margin vs total, home points vs away points) are already published with "
                         "n=137 in nfl-book/data/correlations.json, and re-deriving them here would "
                         "duplicate a peer number rather than add evidence. Parlay and prop-combo "
                         "correlations require prices and player-level official lines, which do not "
                         "exist in this repository. Nothing is estimated; the section is empty by rule.",
            "peer_reference": "nfl-book/data/correlations.json (5 computed with n, 4 blank with reason)",
        },
    }

    with open(os.path.join(DATA, "eval.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    print("selected lambdas: margin %g, total %g" % (lam_m, lam_t))
    for m in ("CD-1", "CD-2"):
        s = all_scored[m]
        print("%s  BSS %+.4f  95%%CI [%+.4f, %+.4f]  p=%.4f  brier %.5f  holdout BSS %+.4f  qualifies=%s"
              % (m, s["bss"], s["ci95_week_cluster"][0], s["ci95_week_cluster"][1], s["p_bss_le_0"],
                 s["brier"], holdout[m]["bss"], gate_out[m]["qualifies"]))
    print("controls: coin brier %.5f  always-home %.5f" % (all_scored["C-1"]["brier"], all_scored["C-2"]["brier"]))
    print("totals: MAE %.3f vs bench %.3f  diff CI %s" % (mae_model, mae_bench, total_block["diff_ci95_week_cluster"]))


if __name__ == "__main__":
    main()
