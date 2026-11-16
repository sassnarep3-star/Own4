"""S2 — rating model, walk-forward forecast register, proper-score leaderboard, luck panel.

The model is the one frozen in nfl-sources/PREREGISTRATION.md section 3. Nothing in this file may be
changed without a new pre-registration: it is the object being tested.

Outputs
  data/model.json              parameters at the week-9 and week-10 cutoffs (used for Week 11 lines)
  data/forecast_register.json  one row per forecast: P, every input, the official result, the scores
  data/backtest.json           metrics, gates, bootstraps, placebo, luck panel, leaderboard, controls
"""
import math
import os
import random

from common import (DATA, REGISTERED_UTC, SEED, read_json, write_json, phi, solve, mean, rms,
                    sd, pearson, p_two_sided, fisher_ci, cluster_bootstrap_ci, percentile,
                    american_from_prob)

LAMBDA = 4.0            # frozen in the pre-registration
HFA = "fitted"          # frozen: one fitted home-field parameter, 0 at international games
PRICE_AMERICAN = -110   # ASSUMED, not a market price: the NFL publishes none (see flags)


# ------------------------------------------------------------------ model
def fit(games):
    """Weighted ridge least squares on the two-equation system of PREREGISTRATION section 3."""
    teams = sorted({g["home"] for g in games} | {g["away"] for g in games})
    idx = {t: i for i, t in enumerate(teams)}
    n_team = len(teams)
    # parameters: [mu, hfa] + o[0..n-1] + d[0..n-1]
    n_par = 2 + 2 * n_team

    def design(g):
        row = [0.0] * n_par
        row[0] = 1.0
        row[1] = 0.0 if g["international_game"] else 1.0
        row[2 + idx[g["home"]]] = 1.0
        row[2 + n_team + idx[g["away"]]] = -1.0
        return row

    A = [[0.0] * n_par for _ in range(n_par)]
    b = [0.0] * n_par
    for g in games:
        for y, home_side in ((g["home_pts"], True), (g["away_pts"], False)):
            row = design(g) if home_side else [
                (1.0 if i == 0 else 0.0) if i < 2 else
                (1.0 if i == 2 + idx[g["away"]] else (-1.0 if i == 2 + n_team + idx[g["home"]] else 0.0))
                for i in range(n_par)]
            for i in range(n_par):
                if row[i] == 0.0:
                    continue
                b[i] += row[i] * y
                for j in range(n_par):
                    if row[j]:
                        A[i][j] += row[i] * row[j]
    for i in range(2, n_par):
        A[i][i] += LAMBDA
    x = solve(A, b)
    mu, hfa = x[0], x[1]
    off = {t: x[2 + idx[t]] for t in teams}
    dfn = {t: x[2 + n_team + idx[t]] for t in teams}

    resid = []
    for g in games:
        h = mu + (0.0 if g["international_game"] else hfa) + off[g["home"]] - dfn[g["away"]]
        a = mu + off[g["away"]] - dfn[g["home"]]
        resid.append((g["home_pts"] - h))
        resid.append((g["away_pts"] - a))
    return {"mu": mu, "hfa": hfa, "off": off, "def": dfn, "sigma": rms(resid),
            "n_games": len(games), "n_params": n_par, "lambda": LAMBDA}


def fit_par(m):
    """Equal-total prior: move a constant c into every offence and out of every defence.

    o and d enter every prediction as (o - d) times +/-1, so a shift (o + c, d - c) leaves every
    MARGIN unchanged while moving the FAIR TOTAL by 2c. The split is therefore pinned by the ridge
    penalty alone: minimising lam*(sum o^2 + sum d^2) over the shift gives c = mean(d) - mean(o) over 2.
    This function returns that point explicitly and asserts the fitted parameters already sit on it,
    so the level is a documented property of the estimator and not an arbitrary choice made later.
    """
    teams = sorted(m["off"])
    c = mean([m["def"][t] - m["off"][t] for t in teams]) / 2.0
    if abs(c) > 0.05:
        raise SystemExit("ridge did not identify the level split (c=%.4f): refusing to publish" % c)
    return {"c": c, "off": {t: m["off"][t] + c for t in teams}, "def": {t: m["def"][t] - c for t in teams}}


def predict(m, home, away, international):
    h = m["mu"] + (0.0 if international else m["hfa"]) + m["off"][home] - m["def"][away]
    a = m["mu"] + m["off"][away] - m["def"][home]
    margin = h - a
    p = phi(margin / m["sigma"])
    return {"pred_home_pts": h, "pred_away_pts": a, "pred_margin": margin, "fair_home_line": -margin,
            "fair_total": h + a, "p_home": p,
            "fair_home_american": american_from_prob(p),
            "fair_away_american": american_from_prob(1 - p)}


# ------------------------------------------------------------------ scoring
def brier(rows):
    vals = [(r["p_home"] - r["y_home_win"]) ** 2 for r in rows if r["y_home_win"] is not None]
    return mean(vals) if vals else None


def logloss(rows):
    out = []
    for r in rows:
        if r["y_home_win"] is None:
            continue
        p = min(max(r["p_home"], 1e-12), 1 - 1e-12)
        out.append(-math.log(p if r["y_home_win"] == 1 else 1 - p))
    return mean(out) if out else None


def accuracy(rows, key):
    hit = [1.0 if r[key] else 0.0 for r in rows if r["y_home_win"] is not None and r.get(key) is not None]
    return mean(hit) if hit else None


def payout(american, win):
    """Net units on a 1-unit stake."""
    if not win:
        return -1.0
    if american < 0:
        return 100.0 / abs(american)
    return american / 100.0


def main():
    res = read_json(os.path.join(DATA, "results.json"))
    games = sorted(res["rows"], key=lambda g: (g["week"], g["date_iso"], g["game_id"]))

    # ------------------------------------------------ walk-forward forecasts
    register = []
    param_history = []
    for w in range(3, 11):
        train = [g for g in games if g["week"] < w]
        if not train:
            continue
        m = fit(train)
        param_history.append({"cutoff_week": w - 1, "n_train_games": len(train),
                              "mu": m["mu"], "hfa": m["hfa"], "sigma": m["sigma"],
                              "ratings": {t: {"off": m["off"][t], "def": m["def"][t]}
                                          for t in sorted(m["off"])}})
        for g in [x for x in games if x["week"] == w]:
            pred = predict(m, g["home"], g["away"], g["international_game"])
            y = None if g["away_pts"] == g["home_pts"] else (1 if g["home_pts"] > g["away_pts"] else 0)
            row = {
                "game_id": g["game_id"], "week": w, "date": g["date_iso"],
                "away": g["away"], "home": g["home"],
                "international_game": g["international_game"],
                "source_url": g["game_url"], "week_page_url": g["week_page_url"],
                "train_cutoff_week": w - 1, "n_train_games": len(train),
                "inputs": {
                    "mu": round(m["mu"], 6), "hfa": round(m["hfa"], 6),
                    "sigma": round(m["sigma"], 6),
                    "off_home": round(m["off"][g["home"]], 6),
                    "def_away": round(m["def"][g["away"]], 6),
                    "off_away": round(m["off"][g["away"]], 6),
                    "def_home": round(m["def"][g["home"]], 6),
                    "formula": ("pred_home = mu + (hfa if not international) + off_home - def_away ; "
                                "pred_away = mu + off_away - def_home ; p_home = Phi(margin / sigma)"),
                },
                "p_home": round(pred["p_home"], 6),
                "fair_american": (pred["fair_home_american"] if pred["p_home"] >= 0.5
                                  else pred["fair_away_american"]),
                "fair_home_line": round(pred["fair_home_line"], 2),
                "fair_total": round(pred["fair_total"], 2),
                "y_home_win": y,
                "result": {"away_pts": g["away_pts"], "home_pts": g["home_pts"],
                           "tie": y is None, "verified": "page-verified against " + g["week_page_url"]},
                "scores": {
                    "brier": None if y is None else round((pred["p_home"] - y) ** 2, 6),
                    "log_loss": None if y is None else round(
                        -math.log(max(min(pred["p_home"] if y == 1 else 1 - pred["p_home"], 1 - 1e-12), 1e-12)), 6),
                    "abs_margin_error": round(abs(pred["pred_margin"] - (g["home_pts"] - g["away_pts"])), 3),
                    "abs_total_error": round(abs(pred["fair_total"] - (g["home_pts"] + g["away_pts"])), 3),
                },
            }
            # registered strategies, all price-free decisions
            pick_home = pred["p_home"] >= 0.5
            row["strategies"] = {
                "S1_model_favourite": {"pick": g["home"] if pick_home else g["away"],
                                       "correct": None if y is None else (pick_home == (y == 1))},
            }
            conf = max(pred["p_home"], 1 - pred["p_home"])
            if conf >= 0.65:
                row["strategies"]["S2_high_confidence"] = {
                    "pick": g["home"] if pick_home else g["away"],
                    "correct": None if y is None else (pick_home == (y == 1))}
            # S3 control: better point-in-time record, computed from earlier weeks only
            rec = {}
            for t in {g["home"], g["away"]}:
                w_ = sum(1 for p in train if t in (p["home"], p["away"]) and
                         ((p["home"] == t and p["home_pts"] > p["away_pts"]) or
                          (p["away"] == t and p["away_pts"] > p["home_pts"])))
                l_ = sum(1 for p in train if t in (p["home"], p["away"]) and
                         ((p["home"] == t and p["home_pts"] < p["away_pts"]) or
                          (p["away"] == t and p["away_pts"] < p["home_pts"])))
                rec[t] = (w_ - l_, w_)
            pick_home_s3 = (rec[g["home"]][0], rec[g["home"]][1]) >= (rec[g["away"]][0], rec[g["away"]][1])
            row["strategies"]["S3_record_baseline"] = {
                "pick": g["home"] if pick_home_s3 else g["away"],
                "correct": None if y is None else (pick_home_s3 == (y == 1)),
                "inputs": {"home_W_L": rec[g["home"]][0], "away_W_L": rec[g["away"]][0]},
                "note": "control, not a candidate: uses only wins-minus-losses from weeks < w"}
            register.append(row)

    # ------------------------------------------------ metrics per strategy
    n_games = len(register)
    weeks = sorted({r["week"] for r in register})
    base_rate = mean([r["y_home_win"] for r in register if r["y_home_win"] is not None])
    bs = brier(register)
    ll = logloss(register)
    # baseline: always 0.5
    bs_base = mean([(r["y_home_win"] - 0.5) ** 2 for r in register if r["y_home_win"] is not None])
    # baseline: point-in-time home base rate (fitted on weeks < w only)
    bs_home_base = []
    for w in weeks:
        prior = [r["y_home_win"] for r in register if r["week"] < w and r["y_home_win"] is not None]
        p = mean(prior) if prior else 0.5
        for r in register:
            if r["week"] == w and r["y_home_win"] is not None:
                bs_home_base.append((p - r["y_home_win"]) ** 2)
    bs_home_base = mean(bs_home_base)

    def strat_rows(name):
        out = []
        for r in register:
            s = r["strategies"].get(name)
            if s and s["correct"] is not None:
                out.append({"week": r["week"], "game_id": r["game_id"], "correct": s["correct"],
                            "p_home": r["p_home"], "y": r["y_home_win"], "pick": s["pick"],
                            "fair_american": r["fair_american"]})
        return out

    rng = random.Random(SEED)
    strategies = {}
    for name in ("S1_model_favourite", "S2_high_confidence", "S3_record_baseline"):
        rows = strat_rows(name)
        if not rows:
            continue
        acc = mean([1.0 if r["correct"] else 0.0 for r in rows])
        acc_ci = cluster_bootstrap_ci(
            [{"week": r["week"], "v": 1.0 if r["correct"] else 0.0} for r in rows],
            lambda s: mean([x["v"] for x in s]))
        net = math.fsum(payout(PRICE_AMERICAN, r["correct"]) for r in rows)
        roi = net / len(rows)
        roi_ci = cluster_bootstrap_ci(
            [{"week": r["week"], "v": payout(PRICE_AMERICAN, r["correct"])} for r in rows],
            lambda s: mean([x["v"] for x in s]))
        # placebo: shuffle this strategy's probabilities across games within each week
        obs_bs = mean([(r["p_home"] - r["y"]) ** 2 for r in rows])
        null = []
        by_week = {}
        for r in rows:
            by_week.setdefault(r["week"], []).append(r)
        for _ in range(2000):
            vals = []
            for w in weeks:
                grp = by_week.get(w, [])
                if not grp:
                    continue
                ps = [g["p_home"] for g in grp]
                rng.shuffle(ps)
                for g, p in zip(grp, ps):
                    if g["y"] is not None:
                        vals.append((p - g["y"]) ** 2)
            null.append(mean(vals))
        hits = sum(1 for v in null if v <= obs_bs)
        p_placebo = (1.0 + hits) / (1.0 + len(null))
        # coin-flip counterfactual at the same n
        coin = []
        for _ in range(2000):
            wins = sum(1 for _ in range(len(rows)) if rng.random() < 0.5)
            coin.append(math.fsum(payout(PRICE_AMERICAN, True) for _ in range(wins))
                        + math.fsum(-1.0 for _ in range(len(rows) - wins)))
        coin = [c / len(rows) for c in coin]
        # halves: does skill persist?
        h1 = [r for r in rows if r["week"] <= 6]
        h2 = [r for r in rows if r["week"] >= 7]
        per_week = {}
        for r in rows:
            per_week.setdefault(r["week"], []).append(1.0 if r["correct"] else 0.0)
        wk_keys = sorted(per_week)
        acc_by_week = [mean(per_week[w]) for w in wk_keys]
        strategies[name] = {
            "n": len(rows),
            "accuracy": acc,
            "accuracy_ci95_week_cluster": acc_ci,
            "beats_coin": (acc_ci[0] > 0.5) if acc_ci else None,
            "brier": obs_bs,
            "brier_skill_vs_coinflip": 1 - obs_bs / 0.25,
            "accuracy_h1_weeks3_6": mean([1.0 if r["correct"] else 0.0 for r in h1]) if h1 else None,
            "accuracy_h2_weeks7_10": mean([1.0 if r["correct"] else 0.0 for r in h2]) if h2 else None,
            "n_h1": len(h1), "n_h2": len(h2),
            "accuracy_by_week": dict(zip(wk_keys, [round(a, 4) for a in acc_by_week])),
            "hypothetical_staking": {
                "price": "ASSUMED -110 (the NFL publishes no prices; this is NOT a market price)",
                "net_units": net, "staked_units": float(len(rows)), "roi": roi,
                "roi_ci95_week_cluster": roi_ci,
                "coin_flip_null_p95": percentile(sorted(coin), 0.95),
                "coin_flip_p_value": (1.0 + sum(1 for c in coin if c >= roi)) / (1.0 + len(coin)),
                "ranked": False,
                "why_not_ranked": "no citable price source exists, so this number cannot be a market return",
            },
            "placebo_label_shuffle_p": p_placebo,
            "n_placebos": 2000,
            "mean_fair_american_of_picks": mean([r["fair_american"] for r in rows
                                                 if r.get("fair_american") is not None]) if rows else None,
        }

    # paired comparison: does the model beat the trivial record baseline on the SAME games?
    s1 = {r["game_id"]: r for r in strat_rows("S1_model_favourite")}
    s3 = {r["game_id"]: r for r in strat_rows("S3_record_baseline")}
    common = sorted(set(s1) & set(s3))
    diffs = [{"week": s1[g]["week"],
              "v": (1.0 if s1[g]["correct"] else 0.0) - (1.0 if s3[g]["correct"] else 0.0)} for g in common]
    paired = {
        "comparison": "S1_model_favourite minus S3_record_baseline, same games",
        "n": len(common),
        "accuracy_diff": mean([d["v"] for d in diffs]) if diffs else None,
        "accuracy_diff_ci95_week_cluster": cluster_bootstrap_ci(diffs, lambda s_: mean([x["v"] for x in s_])),
        "n_disagree": sum(1 for d in diffs if d["v"] != 0.0),
        "note": ("If this interval contains 0, the model has not been shown to beat a trivial "
                 "picking-the-better-record rule on this sample, whatever its absolute accuracy."),
    }

    # what price would each strategy need? (a winner-picking strategy is settled at a moneyline,
    # not at a spread price, so the ASSUMED -110 ROI above is a sensitivity, not a return)
    breakeven = {}
    for k, v in strategies.items():
        a = v["accuracy"]
        if a and 0 < a < 1:
            breakeven[k] = {
                "accuracy": a,
                "breakeven_american_if_all_bets_same_price": int(round(100.0 * (1 - a) / a)),
                "mean_fair_american_of_own_picks": v.get("mean_fair_american_of_picks"),
                "note": ("A winner-picking bet is settled at a MONEYLINE price. At the mean fair price of "
                         "its own picks a strategy breaks even by construction, so the number that matters is "
                         "whether a real market price is worse than ours — and no citable price source exists."),
            }

    # fade controls
    fade = {}
    for name in ("S1_model_favourite", "S2_high_confidence"):
        rows = strat_rows(name)
        if not rows:
            continue
        acc = mean([0.0 if r["correct"] else 1.0 for r in rows])
        fade[name + "_faded"] = {"n": len(rows), "accuracy": acc,
                                 "note": "if this also looks skilful, the original score is noise"}

    skill_ci = cluster_bootstrap_ci(register, lambda s_: 1 - brier(s_) / 0.25)
    skill_lower = skill_ci[0] if skill_ci else None
    gates = {
        "G1_coverage": {"required": 300, "have": n_games, "pass": n_games >= 300},
        "G2_signal": {
            "rule": ("BOTH: (a) each strategy's accuracy interval must exclude 0.500, AND (b) the model's "
                     "Brier skill vs the coin-flip baseline must have a week-cluster lower bound above 0."),
            "brier_skill_lower_bound": skill_lower,
            "brier_skill_ci95": skill_ci,
            "condition_a_accuracy": {k: {"accuracy_ci95": v.get("accuracy_ci95_week_cluster"),
                                         "pass": bool(v.get("beats_coin"))}
                                     for k, v in strategies.items()},
            "condition_b": {"lower_bound": skill_lower,
                            "pass": bool(skill_lower is not None and skill_lower > 0)},
            "pass": bool(skill_lower is not None and skill_lower > 0
                         and all(v.get("beats_coin") for v in strategies.values())),
            "reading": ("Condition (a) is nearly free on this sample: the historical home-favourite base rate "
                        "is high, so picking favourites beats 0.500 without any skill. Condition (b) is the "
                        "real test and it does NOT clear."),
        },
        "G2b_naive_accuracy_trap": {
            "home_base_rate_in_walk_forward_sample": base_rate,
            "record_baseline_accuracy": strategies.get("S3_record_baseline", {}).get("accuracy"),
            "model_accuracy": strategies.get("S1_model_favourite", {}).get("accuracy"),
            "paired_accuracy_difference": None,  # filled below
            "why_this_matters": ("A model-free rule (pick the club with the better win-loss record) scores "
                                 "within a few points of the model. Accuracy against 0.500 cannot separate "
                                 "them; only the paired difference can, and its interval is published."),
        },
        "G3_leakage": None,  # filled by verify.py (mutates results, re-runs the register)
        "G4_placebo": {k: {"p": v["placebo_label_shuffle_p"], "pass": v["placebo_label_shuffle_p"] < 0.05}
                       for k, v in strategies.items()},
        "G5_staking": {"pass": False, "why": "no citable price source: every ROI is at an assumed price"},
        "G6_joint_evidence": {"pass": False, "why": "no validated joint probability and no operator void/push rules"},
        "G7_demotion": {"live_strategies": 0, "fired": 0,
                        "why": "nothing is live: G1 and G5 both block promotion"},
    }

    gates["G2b_naive_accuracy_trap"]["paired_accuracy_difference"] = paired["accuracy_diff"]
    gates["G2b_naive_accuracy_trap"]["paired_ci95"] = paired["accuracy_diff_ci95_week_cluster"]

    out = {
        "dataset": "nfl_sources_backtest",
        "title": "Walk-forward backtest of the pre-registered rating model on page-verified official results",
        "built_utc": REGISTERED_UTC,
        "preregistration": "nfl-sources/PREREGISTRATION.md (registration commit a4f26f5)",
        "protocol": ("For each week w in 3..10 the model is refitted on games from weeks < w only, then the "
                     "forecasts for week w are scored against the official result. Weeks 1-2 are the "
                     "minimum burn-in and are never scored; they are not a validation set and were not "
                     "used to choose anything."),
        "n_forecasts": n_games, "n_weeks": len(weeks),
        "model": {"lambda": LAMBDA, "sigma_definition": "RMS of fit-set per-team scoring residuals",
                  "hfa_rule": "0 at international games (official week page prints an International Game section)"},
        "proper_scores": {
            "brier": bs, "log_loss": ll,
            "baseline_coinflip_brier": 0.25,
            "baseline_home_rate_brier": bs_home_base,
            "brier_skill_vs_coinflip": 1 - bs / 0.25,
            "brier_skill_vs_home_rate": 1 - bs / bs_home_base,
            "brier_ci95_week_cluster": cluster_bootstrap_ci(register, brier),
            "brier_skill_ci95_week_cluster": cluster_bootstrap_ci(
                register, lambda s: 1 - brier(s) / 0.25),
            "home_base_rate_in_sample": base_rate,
        },
        "calibration": calibration(register),
        "margin_and_total_error": {
            "mae_margin": mean([r["scores"]["abs_margin_error"] for r in register]),
            "rmse_margin": math.sqrt(mean([r["scores"]["abs_margin_error"] ** 2 for r in register])),
            "mae_total": mean([r["scores"]["abs_total_error"] for r in register]),
            "n": n_games,
        },
        "strategies": strategies,
        "paired_vs_control": paired,
        "breakeven_prices": breakeven,
        "fade_controls": fade,
        "gates": gates,
        "parameter_history": param_history,
    }
    write_json(os.path.join(DATA, "backtest.json"), out)
    write_json(os.path.join(DATA, "forecast_register.json"), {
        "dataset": "nfl_sources_forecast_register",
        "title": "Every forecast with its probability, every input, the official result and the scores",
        "built_utc": REGISTERED_UTC,
        "n_rows": len(register),
        "rule": ("A row without an official result is stored with y_home_win null and contributes to no "
                 "metric. No forecast uses data from its own week or later."),
        "rows": register,
    })

    # ------------------------------------------------ Week 11 model state
    m9 = fit([g for g in games if g["week"] < 10])
    m10 = fit(games)
    par9, par10 = fit_par(m9), fit_par(m10)
    write_json(os.path.join(DATA, "model.json"), {
        "dataset": "nfl_sources_model",
        "title": "Fitted club ratings at two cutoffs (page-verified official results, weeks 1-9 and 1-10)",
        "built_utc": REGISTERED_UTC,
        "spec": "see nfl-sources/PREREGISTRATION.md section 3 (frozen)",
        "cutoffs": [
            {"label": "open", "trained_through_week": 9, "n_train_games": m9["n_games"],
             "mu": round(m9["mu"], 6), "hfa": round(m9["hfa"], 6), "sigma": round(m9["sigma"], 6),
             "ridge_level_shift_c": round(par9["c"], 6),
             "ratings": {t: {"off": round(par9["off"][t], 4), "def": round(par9["def"][t], 4),
                             "expected_pts_scored_vs_avg": round(22.5 + par9["off"][t] + par9["def"][t] / 2, 3),
                             "net_vs_average_opponent": round(par9["off"][t] + par9["def"][t], 4)}
                         for t in sorted(par9["off"])}},
            {"label": "update", "trained_through_week": 10, "n_train_games": m10["n_games"],
             "mu": round(m10["mu"], 6), "hfa": round(m10["hfa"], 6), "sigma": round(m10["sigma"], 6),
             "ridge_level_shift_c": round(par10["c"], 6),
             "ratings": {t: {"off": round(par10["off"][t], 4), "def": round(par10["def"][t], 4),
                             "expected_pts_scored_vs_avg": round(22.5 + par10["off"][t] + par10["def"][t] / 2, 3),
                             "net_vs_average_opponent": round(par10["off"][t] + par10["def"][t], 4)}
                         for t in sorted(par10["off"])}},
        ],
    })
    write_json(os.path.join(DATA, "_model_state.json"),
               {"open": {"mu": m9["mu"], "hfa": m9["hfa"], "sigma": m9["sigma"],
                         "off_raw": m9["off"], "def_raw": m9["def"],
                         "off": par9["off"], "def": par9["def"], "shift_c": par9["c"], "n": m9["n_games"]},
                "update": {"mu": m10["mu"], "hfa": m10["hfa"], "sigma": m10["sigma"],
                           "off_raw": m10["off"], "def_raw": m10["def"],
                           "off": par10["off"], "def": par10["def"], "shift_c": par10["c"],
                           "n": m10["n_games"]}})

    print("forecasts scored:", n_games, "weeks", weeks[0], "-", weeks[-1])
    print("brier %.5f  logloss %.5f  skill vs coinflip %.4f  skill vs home-rate %.4f"
          % (bs, ll, 1 - bs / 0.25, 1 - bs / bs_home_base))
    for k, v in strategies.items():
        print(" %-22s n=%3d acc=%.4f ci=%s roi=%.4f placebo_p=%.4f"
              % (k, v["n"], v["accuracy"], v["accuracy_ci95_week_cluster"],
                 v["hypothetical_staking"]["roi"], v["placebo_label_shuffle_p"]))
    print(" fade:", {k: round(v["accuracy"], 4) for k, v in fade.items()})
    print(" paired S1-S3: %.4f  ci=%s  n_disagree=%d"
          % (paired["accuracy_diff"], paired["accuracy_diff_ci95_week_cluster"], paired["n_disagree"]))


def calibration(rows):
    bins = [(0.0, 0.4), (0.4, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 1.01)]
    out = []
    for lo, hi in bins:
        grp = [r for r in rows if lo <= r["p_home"] < hi and r["y_home_win"] is not None]
        if not grp:
            out.append({"bin": "%.2f-%.2f" % (lo, hi), "n": 0, "mean_p": None, "observed": None})
            continue
        out.append({"bin": "%.2f-%.2f" % (lo, hi), "n": len(grp),
                    "mean_p": mean([r["p_home"] for r in grp]),
                    "observed": mean([r["y_home_win"] for r in grp])})
    return {"bins": out,
            "note": ("Reliability bins on the walk-forward forecasts. With n = %d the per-bin counts are "
                     "small and the intervals are wide; the table is a diagnostic, not a verdict."
                     % len(rows))}


if __name__ == "__main__":
    main()
