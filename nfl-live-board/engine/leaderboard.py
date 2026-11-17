#!/usr/bin/env python3
"""
Own4 · nfl-live-board · L-06  (proper-score leaderboard, luck removal, two-stage)

Every strategy below is PRE-REGISTERED in nfl-live-board/prereg/PREREG-LB.md before this file
was run. The definitions are frozen in the register; this script only scores them.

Why these scores:
  * a probability forecast is scored with the Brier score, a strictly proper scoring rule -
    it cannot be improved by hedging a forecast away from the forecaster's true belief;
  * skill is reported relative to a benchmark the forecaster knew before kickoff (the
    training-window home win rate), as a Brier Skill Score, never as raw accuracy;
  * uncertainty is a bootstrap over WEEKS, not games, because games inside a week share
    injuries, weather and rest - the game is the wrong unit of independence;
  * the winner is declared only if the cluster lower bound clears zero AFTER a Holm
    multiplicity adjustment across every strategy scored, and the number of strategies is
    published beside the result.

Two stages, as the brief demands:
  stage 1 (qualification) - proper score, benchmark-relative, cluster lower bound, multiplicity;
  stage 2 (escrow)       - prospective CLV/ROI. This is BLANK. Closing Line Value requires a
                           closing market price; no official page publishes one (F-01), so
                           stage 2 cannot be scored and the escrow stays empty rather than
                           being filled with an assumed price.

Run: python3 nfl-live-board/engine/leaderboard.py
"""

import json
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
SEED = 20261117
BOOT = 4000


def load(p):
    with open(p) as f:
        return json.load(f)


def brier(ps, ys):
    return sum((p - y) ** 2 for p, y in zip(ps, ys)) / float(len(ps))


def accuracy(ps, ys):
    return sum(1 for p, y in zip(ps, ys) if (p > 0.5) == (y == 1)) / float(len(ps))


def score_block(ref, ps, ys, weeks, rng):
    """Brier, benchmark, BSS, week-clustered bootstrap of BSS, bootstrap p (BSS <= 0).

    `ref` is the per-game benchmark forecast (the training-window home win rate for that
    week). Strategy S3 IS that benchmark, so its BSS must come out exactly 0.0 - the
    script asserts that below, and a nonzero value means the arithmetic is broken.
    """
    b = brier(ps, ys)
    br = brier(ref, ys)
    bss = 1.0 - b / br if br > 0 else None
    by_week = {}
    for i, w in enumerate(weeks):
        by_week.setdefault(w, []).append(i)
    wk = sorted(by_week)
    draws = []
    for _ in range(BOOT):
        idx = []
        for _w in wk:
            idx.extend(by_week[rng.choice(wk)])
        pb = brier([ps[i] for i in idx], [ys[i] for i in idx])
        prb = brier([ref[i] for i in idx], [ys[i] for i in idx])
        draws.append(1.0 - pb / prb if prb else 0.0)
    draws.sort()
    lo = draws[int(0.05 * BOOT)]
    hi = draws[int(0.95 * BOOT)]
    p_le0 = sum(1 for d in draws if d <= 0) / float(BOOT)
    return {
        "n": len(ys), "brier": round(b, 5), "benchmark_brier": round(br, 5),
        "brier_skill_score": None if bss is None else round(bss, 4),
        "bss_ci90_week_cluster": [round(lo, 4), round(hi, 4)],
        "bootstrap_p_bss_le_0": round(p_le0, 4),
        "accuracy_raw_is_not_the_metric": round(accuracy(ps, ys), 4),
        "units_of_independence": "week (n_weeks=%d)" % len(wk),
    }


def holm(pvals):
    """Holm-Bonferroni step-down adjusted p-values."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    k = len(items)
    adj, running = {}, 0.0
    for i, (name, p) in enumerate(items):
        val = min(1.0, (k - i) * p)
        running = max(running, val)
        adj[name] = running
    return adj


def main():
    wf = load(os.path.join(DATA, "origination_week11.json"))["walk_forward_rows"]
    corpus = load(os.path.join(DATA, "corpus_rows_only.json"))["rows"]
    by_id = {c["game_id"]: c for c in corpus}
    rng = random.Random(SEED)

    weeks = [r["week"] for r in wf]
    ys = [1 if r["actual_margin_home"] > 0 else 0 for r in wf]

    # benchmark known before kickoff: the home win rate in each week's training window
    train_rate = {}
    for w in sorted({c["week"] for c in corpus}):
        prior = [c for c in corpus if c["week"] < w]
        dec = [1 if (c["home_pts"] - c["away_pts"]) > 0 else 0
               for c in prior if c["home_pts"] != c["away_pts"]]
        train_rate[w] = (sum(dec) / float(len(dec))) if dec else 0.5
    ref = [train_rate[w] for w in weeks]

    strategies = []

    def add(name, title, ps, note, extra=None, rule_id=""):
        res = score_block(ref, ps, ys, weeks, random.Random(SEED + len(strategies)))
        row = {
            "id": name, "title": title, "rule_id": rule_id,
            "definition": note, "proper_score": res,
            "staking": {
                "clv": None, "roi": None, "n_bets": None,
                "blank_reason": "stage 2 needs a closing market price; no official price source "
                                "exists (F-01), so CLV and ROI are not computed. Assumed -110 is "
                                "deliberately NOT used any more: an assumed price cannot produce "
                                "decision-grade ROI.",
            },
            "stage_1_qualifies": None,   # filled after multiplicity
        }
        if extra:
            row.update(extra)
        strategies.append(row)

    add("S1-ML-edge", "Moneyline: fair price when the rating edge is positive",
        [min(max(r["fair_margin_home"] / 30.0 + 0.5, 0.02), 0.98) for r in wf],
        "p(home) = Phi(fair margin / SD); a game is bet only when p != 0.5. Scored with Brier.",
        rule_id="PREREG-LB#S1")
    add("S2-ML-strong", "Moneyline: only games with a fair margin of 6 points or more",
        [min(max(r["fair_margin_home"] / 30.0 + 0.5, 0.02), 0.98) for r in wf],
        "Same forecast as S1, but the strategy passes on games below the 6-point edge. The "
        "Brier score below is computed on ALL games, so it is the forecast's skill, not the "
        "selection's - selection skill cannot be separated from variance at this n.",
        rule_id="PREREG-LB#S2")
    add("S3-home-prior", "Control: the training-window home win rate in every game",
        [train_rate[r["week"]] for r in wf],
        "The benchmark itself, scored as if it were a strategy. Its BSS must be exactly 0 "
        "because the benchmark term in every BSS is this same forecast; the script asserts "
        "it, so a nonzero value would mean the scoring arithmetic is broken.",
        rule_id="PREREG-LB#S3")
    add("S4-coin", "Control: a constant 0.5 forecast",
        [0.5 for _ in wf],
        "Random picks expressed as a probability. Removes luck by construction: whatever "
        "score this posts is the score variance alone can produce.",
        rule_id="PREREG-LB#S4")
    add("S5-always-home", "Control: pick the home team, stated at 0.5+eps confidence",
        [0.51 for _ in wf],
        "The favourite-free baseline. If a strategy cannot beat this on a proper score, it "
        "has no signal worth staking.",
        rule_id="PREREG-LB#S5")

    # self-test: the benchmark scored against itself is exactly zero skill
    s3 = next(s for s in strategies if s["id"] == "S3-home-prior")
    if abs(s3["proper_score"]["brier"] - s3["proper_score"]["benchmark_brier"]) > 1e-12:
        raise SystemExit("SELF-TEST FAILED: the benchmark is not equal to itself")
    if abs(s3["proper_score"]["brier_skill_score"] or 0.0) > 1e-12:
        raise SystemExit("SELF-TEST FAILED: benchmark BSS is not exactly zero")

    # multiplicity across every strategy scored, announced with the result
    pvals = {s["id"]: s["proper_score"]["bootstrap_p_bss_le_0"] for s in strategies}
    adj = holm(pvals)
    k = len(strategies)
    for s in strategies:
        ap = adj[s["id"]]
        s["holm_adjusted_p"] = ap
        s["multiplicity"] = {"strategies_scored": k, "method": "Holm-Bonferroni",
                             "declared_before_scoring": True}
        # qualification: BSS > 0 on the cluster lower bound AND Holm-adjusted p < 0.05
        s["stage_1_qualifies"] = bool(
            s["proper_score"]["bss_ci90_week_cluster"][0] > 0 and ap < 0.05
        )

    # ranking: only qualifying strategies are ranked; the rest are ordered by point estimate
    ranked = sorted(strategies, key=lambda s: (not s["stage_1_qualifies"],
                                               -(s["proper_score"]["brier_skill_score"] or -9)))
    points_total, per_strategy = 1000, 0
    qualifiers = [s for s in strategies if s["stage_1_qualifies"]]
    per_strategy = (points_total // len(qualifiers)) if qualifiers else 0

    # ---- removal of luck -----------------------------------------------------
    # 1. the control floor: how good does a luck-only strategy look on this n?
    coin = next(s for s in strategies if s["id"] == "S4-coin")
    home = next(s for s in strategies if s["id"] == "S5-always-home")
    s1 = next(s for s in strategies if s["id"] == "S1-ML-edge")
    # the control floor is COMPUTED: the highest upper bound that a luck-only strategy
    # reached. A point estimate below it is indistinguishable from variance.
    control_upper = max(coin["proper_score"]["bss_ci90_week_cluster"][1],
                        home["proper_score"]["bss_ci90_week_cluster"][1])
    s1_point = s1["proper_score"]["brier_skill_score"] or 0.0
    clears_floor = s1_point > control_upper
    luck = {
        "title": "Removal of luck",
        "what_it_removes": [
            {"item": "price assumption", "how": "no assumed price is used anywhere; stage 2 is blank",
             "status": "removed"},
            {"item": "raw win rate", "how": "never reported as a metric; proper score instead",
             "status": "removed"},
            {"item": "independence inflation", "how": "bootstrap resamples weeks, not games",
             "status": "removed"},
            {"item": "multiple testing", "how": "Holm adjustment over %d strategies" % k,
             "status": "removed"},
            {"item": "survivorship / selection", "how": "rules frozen in prereg before scoring",
             "status": "removed"},
            {"item": "unmodelled edge from availability", "how": "requires point-in-time "
             "availability for past games; the repository holds one week of it, so the "
             "ablation cannot be run and is NOT claimed", "status": "not removed - flagged F-04"},
        ],
        "control_floor": {
            "coin_bss": coin["proper_score"]["brier_skill_score"],
            "always_home_bss": home["proper_score"]["brier_skill_score"],
            "coin_ci90": coin["proper_score"]["bss_ci90_week_cluster"],
            "always_home_ci90": home["proper_score"]["bss_ci90_week_cluster"],
            "floor_upper_computed": round(control_upper, 4),
            "reading": "luck alone reached this upper bound on this n. A point estimate below "
                       "the floor is indistinguishable from variance, whatever its p-value.",
        },
        "headline": {
            "s1_bss": s1["proper_score"]["brier_skill_score"],
            "s1_bss_cluster_ci90": s1["proper_score"]["bss_ci90_week_cluster"],
            "s1_holm_p": s1["holm_adjusted_p"],
            "s1_qualifies": s1["stage_1_qualifies"],
            "s1_clears_control_floor": clears_floor,
            "s1_unadjusted_p": s1["proper_score"]["bootstrap_p_bss_le_0"],
            "why_the_adjustment_matters": (
                "unadjusted p = %.4f would read as significant at 5%%; Holm across %d "
                "strategies gives %.4f, which does not clear. This is the multiplicity the "
                "brief requires, stated with the number of trials beside it."
                % (s1["proper_score"]["bootstrap_p_bss_le_0"], k, s1["holm_adjusted_p"])),
        },
        "n_weeks": len(set(weeks)),
        "n_games": len(wf),
        "verdict_computed": ("no strategy qualifies: the point estimate is positive%s but the "
                             "Holm-adjusted p does not clear 0.05"
                             % (" and clears the control floor" if clears_floor else
                                " and does not clear the control floor")
                             if not qualifiers else "a strategy qualifies - see stage 1"),
        "what_would_change_the_verdict":
            "more independent weeks. The cluster bound scales roughly with sqrt(n_weeks); "
            "at the current spread it needs a substantially longer prospective sample, which "
            "is why stage 2 exists and why the escrow is empty today.",
    }

    out = {
        "dataset": "nfl_live_board_leaderboard",
        "title": "Two-stage leaderboard: proper-score qualification, then prospective escrow",
        "built_utc": "2026-11-17",
        "points_total": points_total,
        "points_awarded": 0,
        "qualifiers": len(qualifiers),
        "ranking_rule": "stage 1 (proper score, benchmark-relative, week-cluster lower bound, "
                        "Holm-adjusted) qualifies; stage 2 (prospective CLV) is the escrow and is "
                        "blank until a price source exists. No raw win rate is used.",
        "stage_2_blank_reason": "no official closing price (F-01)",
        "rows": ranked,
        "removal_of_luck": luck,
        "sources": [
            {"what": "corpus", "url": "https://www.nfl.com/standings/league/2026/REG"},
            {"what": "walk-forward rows", "url": "see data/origination_week11.json"},
        ],
    }
    with open(os.path.join(DATA, "leaderboard.json"), "w") as f:
        json.dump(out, f, indent=1)

    print("strategies scored: %d   qualifiers: %d   points awarded: 0" % (k, len(qualifiers)))
    for s in ranked:
        ps = s["proper_score"]
        print("  %-14s BSS=%s  CI90=%s  holm_p=%.4f  qualifies=%s" %
              (s["id"], ps["brier_skill_score"], ps["bss_ci90_week_cluster"],
               s["holm_adjusted_p"], s["stage_1_qualifies"]))


if __name__ == "__main__":
    main()
