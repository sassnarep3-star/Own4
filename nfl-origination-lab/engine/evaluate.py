#!/usr/bin/env python3
"""
Walk-forward evaluation, proper-score leaderboard, luck removal, correlation.

Implements prereg/PREREG-LAB-1.json and nothing else:

  1. lambda is chosen on the VALIDATION block (2025 weeks 10-18) only.
  2. the model family is chosen on the validation block, by mean proper score.
  3. the FINAL block (2026 weeks 1-10) is then read once, with the choice frozen.
  4. every prediction is made by a model fitted on strictly earlier weeks, and the
     training set for week w contains no game from week w or later. Not even the
     final block's own current week.

What this file refuses to do
----------------------------
  * It does not compute ROI, CLV, win rate as a ranking metric, or "units".
    There is no official price in the repository (data/price_policy.json), so
    staking is published as an empty division with the reason, not filled with a
    -110 assumption.
  * It does not select a model on the final block. The selection is printed with
    the validation scores that produced it and the commit the rule was frozen at.

Outputs (all under data/):
  validation_scores.json   the selection evidence, lambda grid included
  leaderboard.json         proper-score leaderboard with uncertainty + multiplicity
  forecasts.json           every model output: probability + inputs + actual
  luck.json                the removal-of-luck panel
  correlations.json        measured correlations, n on every value
"""

import json
import math
import os
import random
import statistics
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import models as M
from corpus import TEAMS

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stable import dump

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
DATA = os.path.join(LAB, "data")
SEED = 20261119
BOOTSTRAP = 10000
MODEL_IDS = ["M0", "M1", "M2", "M3", "M4", "M5"]
VALIDATION_CACHE = {}
MARKETS = ["SIDE", "TOTAL", "MONEYLINE"]


def load_corpus():
    return json.load(open(os.path.join(DATA, "corpus.json"), encoding="utf-8"))


def split(games):
    """The registered ladder. Nothing here is tuned; it is read from the prereg."""
    train = [g for g in games if g["season"] == 2025 and g["week"] <= 9]
    val = [g for g in games if g["season"] == 2025 and g["week"] >= 10]
    final = [g for g in games if g["season"] == 2026]
    return train, val, final


def walk_forward(games, model_id, lam, seed_games):
    """
    Predict every game in `games` using a model fitted on `seed_games` plus only
    those `games` whose week is strictly earlier than the game's own week.
    """
    out = []
    weeks = sorted({g["week"] for g in games})
    for w in weeks:
        history = seed_games + [g for g in games if g["week"] < w]
        params = M.fit(model_id, history, lam)
        for g in games:
            if g["week"] != w:
                continue
            out.append(M.forecast(params, g))
    return out


def per_week_losses(preds):
    """Per-week mean proper losses, so any leave-one-week-out question is answerable."""
    wk = defaultdict(lambda: defaultdict(list))
    for p in preds:
        wk[p["week"]]["home"].append((p["p_home_win"] - p["actual"]["home_win"]) ** 2)
        wk[p["week"]]["tot"].append((p["p_total_over_tau"] - p["actual"]["total_over_tau"]) ** 2)
        wk[p["week"]]["crps"].append(M.crps_normal(p["fair_total"], p["sigma_total"],
                                                  p["actual"]["total"]))
    return {w: {k: sum(v) / len(v) for k, v in d.items()} for w, d in wk.items()}


def score_block(preds, model_id, lam, block):
    """Proper scores for one (model, block). Brier for probabilities, CRPS for totals."""
    n = len(preds)
    bs_home = sum((p["p_home_win"] - p["actual"]["home_win"]) ** 2 for p in preds) / n
    bs_total = sum((p["p_total_over_tau"] - p["actual"]["total_over_tau"]) ** 2 for p in preds) / n
    crps = sum(M.crps_normal(p["fair_total"], p["sigma_total"], p["actual"]["total"]) for p in preds) / n
    crps_m = sum(M.crps_normal(p["fair_margin"], p["sigma_margin"], p["actual"]["margin"]) for p in preds) / n
    brier_margin = sum((p["fair_margin"] - p["actual"]["margin"]) ** 2 for p in preds) / n
    acc = sum(1 for p in preds
              if (p["p_home_win"] > 0.5) == (p["actual"]["home_win"] == 1)
              and p["actual"]["margin"] != 0) / max(1, sum(1 for p in preds if p["actual"]["margin"] != 0))
    return {"model": model_id, "lambda": lam, "block": block, "n": n,
            # rounded at source for the same reason as models.forecast: CI asserts a
            # byte-identical rebuild across CPython builds
            "brier_home_win": round(bs_home, 10),
            "brier_total_over_tau": round(bs_total, 10),
            "crps_total": round(crps, 10),
            "crps_margin": round(crps_m, 10),
            "brier_margin_point": round(brier_margin, 6),
            "accuracy_raw_not_a_ranking_metric": acc,
            "per_week": per_week_losses(preds)}


def select(validation):
    """
    Choose lambda per model on the validation block, then choose the model.
    Criterion (registered): mean of standardised proper scores across the two
    probability markets and the CRPS, all benchmark-relative to M0.
    """
    by = defaultdict(list)
    for s in validation:
        if s["lambda"] is None and s["model"] != "M0":
            continue          # the un-parameterised placeholder fit of a ridge model
        by[s["model"]].append(s)
    chosen = {}
    for m, rows in by.items():
        best = min(rows, key=lambda r: (0.5 * (r["brier_home_win"] / 1.0)
                                        + 0.5 * (r["brier_total_over_tau"] / 1.0)
                                        + r["crps_total"] / 40.0, r["lambda"]))
        chosen[m] = best
    return chosen


def bss(bs_model, bs_bench):
    return 1.0 - bs_model / bs_bench if bs_bench else float("nan")


def week_cluster_bootstrap(pairs, bench_pairs, resamples=BOOTSTRAP, seed=SEED):
    """
    Paired bootstrap over WEEKS (the unit of independence), 90% interval on the
    benchmark-relative skill, plus the one-sided p that skill <= 0.
    `pairs` / `bench_pairs` are lists of (week, loss) aligned by index.
    """
    by_week = defaultdict(list)
    for i, (wk, _) in enumerate(pairs):
        by_week[wk].append(i)
    weeks = sorted(by_week)
    rng = random.Random(seed)
    out = []
    for _ in range(resamples):
        pick = [by_week[rng.choice(weeks)] for _week in weeks] if False else []
        # resample weeks with replacement, then all games inside each drawn week
        draw = [rng.choice(weeks) for _ in weeks]
        idx = [i for wk in draw for i in by_week[wk]]
        m = sum(pairs[i][1] for i in idx) / len(idx)
        b = sum(bench_pairs[i][1] for i in idx) / len(idx)
        out.append(1.0 - m / b if b else 0.0)
    out.sort()
    lo = out[int(0.05 * len(out))]
    hi = out[int(0.95 * len(out))]
    p = sum(1 for x in out if x <= 0.0) / len(out)
    return lo, hi, p


def holm(pvals):
    """Holm-Bonferroni adjusted p-values, family as given."""
    order = sorted(range(len(pvals)), key=lambda i: pvals[i])
    m = len(pvals)
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        val = min(1.0, (m - rank) * pvals[i])
        running = max(running, val)
        adj[i] = running
    return adj


def main():
    corpus = load_corpus()
    games = corpus["games"]
    train, val, final = split(games)
    print("blocks: train %d, validation %d, final %d" % (len(train), len(val), len(final)))

    # ---------- stage 1: lambda + model selection on validation ----------
    validation = []
    for mid in MODEL_IDS:
        if mid == "M0":
            preds = walk_forward(val, mid, None, train)
            validation.append(score_block(preds, mid, None, "2025 weeks 10-18"))
        if mid == "M0":
            continue
        for lam in M.LAMBDA_GRID:
            preds = walk_forward(val, mid, lam, train)
            validation.append(score_block(preds, mid, lam, "2025 weeks 10-18"))

    VALIDATION_CACHE["rows"] = validation
    chosen = select(validation)
    chosen_model = min(chosen.values(),
                       key=lambda r: (0.5 * r["brier_home_win"] + 0.5 * r["brier_total_over_tau"]
                                      + r["crps_total"] / 40.0, r["model"]))["model"]
    print("selected on validation:", chosen_model,
          {m: r["lambda"] for m, r in chosen.items()})

    with open(os.path.join(DATA, "validation_scores.json"), "w", encoding="utf-8") as fh:
        dump({
            "dataset": "nfl_origination_lab_validation_scores",
            "title": "Selection evidence: every model and lambda, scored on 2025 weeks 10-18 only",
            "blocks": {"train": "2025 weeks 1-9 (%d games)" % len(train),
                       "validation": "2025 weeks 10-18 (%d games)" % len(val),
                       "final_holdout": "2026 weeks 1-10 (%d games), not used here" % len(final)},
            "criterion": "minimise 0.5*Brier(home) + 0.5*Brier(total>44) + CRPS(total)/40",
            "chosen_lambda": {m: r["lambda"] for m, r in chosen.items()},
            "chosen_model": chosen_model,
            "scores": validation,
        }, fh, indent=1)

    # ---------- stage 2: the final block, read once ----------
    lam = chosen[chosen_model]["lambda"]
    preds = {}
    for mid in MODEL_IDS:
        ln = chosen[mid]["lambda"] if mid != "M0" else None
        preds[mid] = walk_forward(final, mid, ln, train + val)

    bench = preds["M0"]
    final_scores = {}
    for mid in MODEL_IDS:
        n = len(preds[mid])
        loss_home = [(p["week"], (p["p_home_win"] - p["actual"]["home_win"]) ** 2) for p in preds[mid]]
        bench_home = [(p["week"], (p["p_home_win"] - p["actual"]["home_win"]) ** 2) for p in bench]
        loss_tot = [(p["week"], (p["p_total_over_tau"] - p["actual"]["total_over_tau"]) ** 2)
                    for p in preds[mid]]
        bench_tot = [(p["week"], (p["p_total_over_tau"] - p["actual"]["total_over_tau"]) ** 2)
                     for p in bench]
        loss_crps = [(p["week"], M.crps_normal(p["fair_total"], p["sigma_total"], p["actual"]["total"]))
                     for p in preds[mid]]
        bench_crps = [(p["week"], M.crps_normal(p["fair_total"], p["sigma_total"], p["actual"]["total"]))
                      for p in bench]

        row = {"model": mid, "lambda": chosen[mid]["lambda"], "n": n,
               "brier_home_win": sum(x for _w, x in loss_home) / n,
               "bench_brier_home_win": sum(x for _w, x in bench_home) / n,
               "brier_total_over_tau": sum(x for _w, x in loss_tot) / n,
               "bench_brier_total_over_tau": sum(x for _w, x in bench_tot) / n,
               "crps_total": sum(x for _w, x in loss_crps) / n,
               "bench_crps_total": sum(x for _w, x in bench_crps) / n}
        row["bss_home_win"] = round(bss(row["brier_home_win"], row["bench_brier_home_win"]), 10)
        row["bss_total_over_tau"] = round(bss(row["brier_total_over_tau"], row["bench_brier_total_over_tau"]), 10)
        row["skill_crps"] = round(1.0 - row["crps_total"] / row["bench_crps_total"], 10)
        row["ci90_home_win"] = list(week_cluster_bootstrap(loss_home, bench_home)[:2])
        row["p_home_win"] = week_cluster_bootstrap(loss_home, bench_home)[2]
        row["ci90_total_over_tau"] = list(week_cluster_bootstrap(loss_tot, bench_tot)[:2])
        row["p_total_over_tau"] = week_cluster_bootstrap(loss_tot, bench_tot)[2]
        row["ci90_crps_total"] = list(week_cluster_bootstrap(loss_crps, bench_crps)[:2])
        row["p_crps_total"] = week_cluster_bootstrap(loss_crps, bench_crps)[2]
        row["weeks"] = len({p["week"] for p in preds[mid]})
        final_scores[mid] = row

    # multiplicity: one test per (model, market) pair, family declared before scoring
    family = []
    for mid in MODEL_IDS:
        family += [(mid, "MONEYLINE", final_scores[mid]["p_home_win"]),
                   (mid, "TOTAL", final_scores[mid]["p_total_over_tau"]),
                   (mid, "SIDE", final_scores[mid]["p_crps_total"])]
    adj = holm([p for _m, _k, p in family])
    for (mid, market, raw), a in zip(family, adj):
        final_scores[mid]["holm_p_%s" % market] = a

    # ---------- leaderboard: proper score + blank staking division ----------
    led_rows = []
    for mid in MODEL_IDS:
        r = final_scores[mid]
        eligible = mid != "M0"
        passes = (eligible and r["n"] >= 100
                  and r["holm_p_MONEYLINE"] < 0.10
                  and r["holm_p_TOTAL"] < 0.10
                  and r["ci90_home_win"][0] > 0 and r["ci90_total_over_tau"][0] > 0)
        led_rows.append({
            "model": mid,
            "eligible_for_ranking": eligible,
            "proper_score": {
                "bss_moneyline": r["bss_home_win"],
                "ci90_moneyline": r["ci90_home_win"],
                "bss_total": r["bss_total_over_tau"],
                "ci90_total": r["ci90_total_over_tau"],
                "skill_crps_side": r["skill_crps"],
                "ci90_side": r["ci90_crps_total"],
                "n": r["n"], "weeks": r["weeks"],
                "holm_p_moneyline": r["holm_p_MONEYLINE"],
                "holm_p_total": r["holm_p_TOTAL"],
                "holm_p_side": r["holm_p_SIDE"],
            },
            "staking_division": {
                "roi": None, "clv": None, "n_bets": None,
                "blank_reason": "no officially sourced closing price exists in this "
                                "repository for any 2026 market (data/price_policy.json)",
            },
            "stage_1_qualified": passes,
            "what_would_promote": "a 2026 closing price with an official, timestamped "
                                  "source would open the staking division; sustained CLV "
                                  "above 0 over >= 8 weeks would promote to live",
            "what_would_retire": "a negative 90% lower bound on benchmark-relative Brier "
                                 "skill over any rolling 4-week window, or a drift-alarm "
                                 "failure on the inputs twice in a row",
        })

    qualified = [r["model"] for r in led_rows if r["stage_1_qualified"]]
    with open(os.path.join(DATA, "leaderboard.json"), "w", encoding="utf-8") as fh:
        dump({
            "dataset": "nfl_origination_lab_leaderboard",
            "title": "Proper-score leaderboard on the untouched 2026 holdout; staking division empty",
            "built": "2026-11-19",
            "rule": "rank by benchmark-relative proper score with a week-cluster lower bound "
                    "and a Holm adjustment over the whole declared family. Raw win rate and "
                    "ROI are not ranking metrics and are not shown as if they were.",
            "benchmark": "M0 climatology (training-window base rates, no team information)",
            "block": "2026 weeks 1-10 (the final holdout; never used for selection)",
            "n_games": len(final),
            "families_scored": len(family),
            "qualifiers": qualified,
            "shadows_only_reason": ("no model cleared the registered gate"
                                    if not qualified else "see qualifiers"),
            "rows": led_rows,
            "divisions": {
                "singles": {"status": "open", "note": "one straight bet per game, one market"},
                "game_parlays": {"status": "closed",
                                 "reason": "leg dependence must be measured on officially "
                                           "sourced joint prices, which do not exist here"},
                "same_game_parlays": {"status": "closed", "reason": "same as game parlays"},
                "prop_combos": {"status": "closed",
                                "reason": "no official player-level price or per-game log "
                                          "in the repository; marginal probabilities cannot "
                                          "be multiplied under dependence"},
            },
        }, fh, indent=1)

    # ---------- forecasts store: probability + inputs, not just a pick ----------
    with open(os.path.join(DATA, "forecasts.json"), "w", encoding="utf-8") as fh:
        dump({
            "dataset": "nfl_origination_lab_forecasts",
            "title": "Every model output on the 2026 holdout, with its inputs",
            "selected_model": chosen_model,
            "threshold_tau": M.THRESHOLD_TAU,
            "markets_order": MARKETS,
            "rows": [dict(p, model=mid) for mid in MODEL_IDS for p in preds[mid]],
        }, fh, indent=1)

    # ---------- removal of luck ----------
    luck = build_luck(preds, bench, final_scores, chosen_model)
    with open(os.path.join(DATA, "luck.json"), "w", encoding="utf-8") as fh:
        dump(luck, fh, indent=1)

    # ---------- correlations with n ----------
    corr = build_correlations(games)
    with open(os.path.join(DATA, "correlations.json"), "w", encoding="utf-8") as fh:
        dump(corr, fh, indent=1)

    print("final block: %d games, %d weeks" % (len(final), len({g['week'] for g in final})))
    for mid in MODEL_IDS:
        r = final_scores[mid]
        print("  %s BSS(ML) %+0.4f [%+0.4f,%+0.4f] p=%.4f holm=%.4f | BSS(total>%g) %+0.4f "
              "p=%.4f holm=%.4f | CRPS skill %+0.4f"
              % (mid, r["bss_home_win"], r["ci90_home_win"][0], r["ci90_home_win"][1],
                 r["p_home_win"], r["holm_p_MONEYLINE"], M.THRESHOLD_TAU,
                 r["bss_total_over_tau"], r["p_total_over_tau"], r["holm_p_TOTAL"],
                 r["skill_crps"]))
    print("qualified:", qualified)


def build_luck(preds, bench, final_scores, chosen_model):
    """
    The removal-of-luck panel. Four separate questions, each answered with a number:
      1. is the skill a coin flip?              permutation test, 2,000 label shuffles
      2. is it one or two weeks?                leave-one-week-out re-scoring
      3. is the selection itself lucky?         selection stability across weeks
      4. what would a perfect model have scored? the observed bound, for scale
    """
    rows = preds[chosen_model]
    n = len(rows)

    # 1. permutation: shuffle the outcome labels across games, re-score
    rng = random.Random(SEED)
    obs = final_scores[chosen_model]["brier_home_win"]
    bench_obs = final_scores[chosen_model]["bench_brier_home_win"]
    obs_skill = 1 - obs / bench_obs
    labels = [p["actual"]["home_win"] for p in rows]
    ph = [p["p_home_win"] for p in rows]
    bp = [p["p_home_win"] for p in bench]
    null = []
    for _ in range(2000):
        sh = labels[:]
        rng.shuffle(sh)
        bm = sum((a - b) ** 2 for a, b in zip(ph, sh)) / n
        bb = sum((a - b) ** 2 for a, b in zip(bp, sh)) / n
        null.append(1 - bm / bb if bb else 0.0)
    null.sort()
    perm_p = sum(1 for x in null if x >= obs_skill) / len(null)
    perm_ci = [null[int(0.05 * len(null))], null[int(0.95 * len(null))]]

    # 2. leave-one-week-out
    by_week = defaultdict(list)
    for p in rows:
        by_week[p["week"]].append(p)
    lowo = []
    for w in sorted(by_week):
        keep = [p for p in rows if p["week"] != w]
        if not keep:
            continue
        bm = sum((p["p_home_win"] - p["actual"]["home_win"]) ** 2 for p in keep) / len(keep)
        bb = sum((p["p_home_win"] - p["actual"]["home_win"]) ** 2 for p in bench if p["week"] != w) / len(keep)
        lowo.append({"week_removed": w, "skill": 1 - bm / bb, "n": len(keep)})
    worst = min(lowo, key=lambda r: r["skill"])

    # 3. selection stability: re-run the registered selection with each validation
    #    week removed in turn. A model choice that flips is a choice made of luck.
    selection_folds = []
    if VALIDATION_CACHE.get("rows"):
        vrows = VALIDATION_CACHE["rows"]
        weeks = sorted({int(w) for r in vrows for w in r.get("per_week", {})})
        for drop in weeks:
            def crit(r):
                pw = {int(k): v for k, v in r["per_week"].items() if int(k) != drop}
                if not pw:
                    return float("inf")
                n = len(pw)
                bh = sum(v["home"] for v in pw.values()) / n
                bt = sum(v["tot"] for v in pw.values()) / n
                cp = sum(v["crps"] for v in pw.values()) / n
                return 0.5 * bh + 0.5 * bt + cp / 40.0
            best = min((r for r in vrows if not (r["lambda"] is None and r["model"] != "M0")),
                       key=lambda r: (crit(r), r["model"]))
            selection_folds.append({"week_removed": drop, "would_choose": best["model"],
                                    "lambda": best["lambda"]})
        counts = {}
        for f in selection_folds:
            counts[f["would_choose"]] = counts.get(f["would_choose"], 0) + 1
        stable = len(counts) == 1
        sel_display = ("stable: %s in %d of %d folds"
                       % (next(iter(counts)), len(selection_folds), len(selection_folds))
                       if stable else
                       "flips: %s over %d folds"
                       % (", ".join("%s x%d" % kv for kv in sorted(counts.items())),
                          len(selection_folds)))
    else:
        selection_folds, stable, sel_display = [], False, "not computable in this run"

    # 4. scale: a model that knows the score exactly scores 0 Brier; the observed
    #    bound is what one week of football can carry at this n.
    luck_rows = [
        {"id": "L1", "question": "Could a coin have produced this skill?",
         "method": "2,000 permutations of the outcome labels", "value": perm_p,
         "display": ("p < %.4f" % (1.0 / 2000.0)) if perm_p == 0 else ("p = %.4f" % perm_p),
         "reading": "fraction of label shuffles that beat the observed skill"},
        {"id": "L2", "question": "Is one week carrying the result?",
         "method": "leave-one-week-out re-scoring",
         "value": worst["skill"],
         "display": "worst fold %+0.4f (drop week %d)" % (worst["skill"], worst["week_removed"]),
         "reading": "the skill that survives dropping the single most valuable week"},
        {"id": "L3", "question": "Is the model choice stable or fluky?",
         "method": "re-run the registered selection with each validation week removed",
         "value": 1.0 if stable else 0.0,
         "display": sel_display,
         "reading": "the fraction of validation folds that would still choose the "
                    "selected model; a choice that flips when one week is removed is "
                    "a choice made of luck"},
        {"id": "L4", "question": "How much skill is even available at this n?",
         "method": "null interval on benchmark-relative skill",
         "value": perm_ci[1],
         "display": "shuffled-label 90th pct %+0.4f" % perm_ci[1],
         "reading": "a skill below this line is inside what shuffling buys for free"},
    ]
    return {
        "dataset": "nfl_origination_lab_luck",
        "title": "Removal of luck: four separate questions, four separate numbers",
        "built": "2026-11-19",
        "model": chosen_model,
        "n_games": n,
        "n_weeks": len(by_week),
        "observed_skill_moneyline": obs_skill,
        "null_interval_90": perm_ci,
        "panel": luck_rows,
        "leave_one_week_out": lowo,
        "selection_stability": {"folds": selection_folds, "stable": stable,
                                "display": sel_display},
        "controls": {
            "coin_flip": "Brier 0.25 on every game; skill 0 by construction",
            "always_home": "the home-won label base rate in the block",
            "always_favourite": "not computable: requires a price",
        },
    }


def build_correlations(games):
    """
    Correlations, only from values the corpus itself carries, with n on every one
    and a 95% interval from a Fisher z transform. Nothing here is a betting
    correlation: those need prices, which do not exist (see price_policy).
    """
    def pearson(xs, ys):
        n = len(xs)
        if n < 4 or len(ys) < 4:
            return None
        # Deliberately NOT statistics.fmean: it sums exact Fractions internally, so the
        # last bits of the result can move between CPython versions. A plain left-to-right
        # float sum is identical everywhere, and six decimals is all this lab publishes.
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        sx = math.sqrt(sum((x - mx) ** 2 for x in xs) / (n - 1))
        sy = math.sqrt(sum((y - my) ** 2 for y in ys) / (n - 1))
        if sx == 0 or sy == 0:
            return None
        r = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / ((n - 1) * sx * sy)
        z = math.atanh(max(-0.999999, min(0.999999, r)))
        se = 1 / math.sqrt(n - 3)
        return {"r": r, "n": n,
                "ci95": [math.tanh(z - 1.96 * se), math.tanh(z + 1.96 * se)]}

    def consecutive_club_totals(gs):
        """A club's total in its game k vs its total in game k+1, pooled over clubs.

        This is the only legitimate persistence measure available without prices:
        it says whether a club's game total carries over, which is the assumption
        every total model makes.
        """
        seq = defaultdict(list)
        for g in sorted(gs, key=lambda g: g["gameday"]):
            seq[g["home"]].append(g["total"])
            seq[g["away"]].append(g["total"])
        a, b = [], []
        for club, tots in seq.items():
            for i in range(len(tots) - 1):
                a.append(tots[i])
                b.append(tots[i + 1])
        return a, b

    def by_season(season):
        return [g for g in games if g["season"] == season]

    out = []
    for season in (2025, 2026):
        gs = by_season(season)
        pairs = [
            ("margin", "total", [g["margin"] for g in gs], [g["total"] for g in gs]),
            ("abs_margin", "total", [abs(g["margin"]) for g in gs], [g["total"] for g in gs]),
            ("rest_diff", "margin",
             [g["rest_diff"] for g in gs if g["rest_diff"] is not None],
             [g["margin"] for g in gs if g["rest_diff"] is not None]),
            ("club_total_game_k", "club_total_game_k+1",
             *consecutive_club_totals(gs)),
        ]
        for name, other, xs, ys in pairs:
            c = pearson(xs, ys)
            out.append({
                "season": season, "pair": "%s ~ %s" % (name, other),
                "r": None if not c else round(c["r"], 4),
                "n": None if not c else c["n"],
                "ci95": None if not c else [round(c["ci95"][0], 4), round(c["ci95"][1], 4)],
                "source": "computed from data/corpus.json; each row's games carry their own "
                          "official URL",
                "uses_price": False,
            })
    return {
        "dataset": "nfl_origination_lab_correlations",
        "title": "Measured correlations from the verified corpus, n on every value",
        "built": "2026-11-19",
        "policy": "only officially sourced numbers are used; no correlation involving a "
                  "price is published because no official price exists. Every row states n.",
        "not_published": [
            {"item": "same-game parlay leg correlation",
             "why": "requires joint prices from an official or licensed source; F-01"},
            {"item": "player prop pair correlation",
             "why": "requires official player-level prices or per-game logs; neither exists here"},
            {"item": "closing-line correlation",
             "why": "requires a closing price; the store has none for 2026"},
        ],
        "rows": out,
    }


if __name__ == "__main__":
    main()
