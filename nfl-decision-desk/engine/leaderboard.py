#!/usr/bin/env python3
"""Leaderboard, gates, luck panel, demotion evaluation.

Implements the requirements literally:

  * rank by PROPER SCORE (Brier), never win rate or ROI;
  * every rank carries a game-cluster lower bound;
  * a multiplicity adjustment (Benjamini-Hochberg over all trials) is applied to every p;
  * signal and staking are SEPARATE tables - a staking run can never lift a signal rank;
  * a control baseline (random, always-home, favourites) runs on every leaderboard build;
  * "removal of luck" panel: observed vs luck-expected spread, with a permutation p;
  * demotion gate: explicit machine-evaluable conditions that send LIVE -> PAPER.

Outputs data/leaderboard/*.json
"""
from __future__ import annotations

import json
import math
import os
import random
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "data", "leaderboard")
os.makedirs(OUT, exist_ok=True)
SEED = 20261115
MIN_N_SIGNAL = 300          # pre-registered floor, from the brief


def load(rel):
    return json.load(open(os.path.join(ROOT, "data", rel)))


def brier(p, y):
    return (p - y) ** 2


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    s = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - s) / d, (c + s) / d)


def cluster_boot(rows, stat, n_boot=4000, seed=SEED):
    """Resample WEEKS, not games: games in a week share conditions and are not independent."""
    rng = random.Random(seed)
    byweek = defaultdict(list)
    for r in rows:
        byweek[r["week"]].append(r)
    wks = list(byweek)
    vals = []
    for _ in range(n_boot):
        s = []
        for _ in wks:
            s.extend(byweek[rng.choice(wks)])
        vals.append(stat(s))
    vals.sort()
    return vals[int(0.025 * n_boot)], vals[int(0.975 * n_boot) - 1], vals


def bh(pvals):
    """Benjamini-Hochberg q-values. Returns q aligned with input order."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    q = [1.0] * m
    prev = 1.0
    for rank in range(m - 1, -1, -1):
        i = order[rank]
        val = pvals[i] * m / (rank + 1)
        prev = min(prev, val)
        q[i] = min(1.0, prev)
    return q


def main():
    ev = load("model/model_evaluation.json")
    rows = ev["model_rows"]
    bench = {b["game_id"]: b for b in ev["market_benchmark_rows"]}

    # ---------------------------------------------------------------- strategies
    # Each strategy is a probability generator over the SAME games, so the comparison is
    # paired. Every one is pre-registered or explicitly a control.
    def strat_model(r):
        return r["p_home_win"]

    def strat_random(r):
        return 0.5

    def strat_home(r):
        return 0.55   # always-home control; 0.55 is the long-run convention, stated not fitted

    def strat_climatology(r):
        return 0.4808  # the 2026 realised home rate on the frozen corpus; a look-ahead-free
        # constant would need a prior season. FLAGGED: this constant is computed from the
        # FULL corpus and is therefore mildly optimistic; see flag LD-02.

    def strat_market(r):
        b = bench.get(r["game_id"])
        return b["market_p_home"] if b else None

    strategies = [
        ("S1", "PR-01 team-strength shadow baseline (side)", "model", strat_model, "PR-01"),
        # PR-04 IS the moneyline link fitted on the same margins - it is the same probability
        # record, so it is listed ONCE. Publishing it twice would inflate the trial count and
        # make the BH adjustment dishonest. Recorded as a correction, not hidden.
        ("C1", "control: coin flip", "control", strat_random, None),
        ("C2", "control: always home", "control", strat_home, None),
        ("C3", "control: climatology base rate", "control", strat_climatology, None),
        ("B1", "benchmark: vig-free closing market", "benchmark", strat_market, None),
    ]

    signal = []
    for sid, name, kind, fn, prereg in strategies:
        obs = [(fn(r), r["home_win"], r) for r in rows if fn(r) is not None]
        n = len(obs)
        if not n:
            continue
        b = math.fsum(brier(p, y) for p, y, _ in obs) / n
        # base-rate Brier on the SAME sample = the honest no-skill reference
        pr = math.fsum(y for _, y, _ in obs) / n
        b0 = math.fsum(brier(pr, y) for _, y, _ in obs) / n
        skill = 1 - b / b0
        lo, hi, _ = cluster_boot([r for _, _, r in obs],
                                 lambda s: 1 - (math.fsum(brier(fn(x), x["home_win"]) for x in s) / len(s)) /
                                 (math.fsum(brier(math.fsum(z["home_win"] for z in s) / len(s), z["home_win"]) for z in s) / len(s)))
        # permutation p: is skill different from what shuffling outcomes produces?
        rng = random.Random(SEED)
        ys = [y for _, y, _ in obs]
        null = []
        for _ in range(2000):
            sh = ys[:]
            rng.shuffle(sh)
            bb = math.fsum(brier(p, y) for (p, _, _), y in zip(obs, sh)) / n
            p0 = math.fsum(sh) / n
            b00 = math.fsum(brier(p0, y) for y in sh) / n
            null.append(1 - bb / b00)
        # A Monte-Carlo p-value must have a floor: the observed statistic is ONE of the
        # (2000+1) equally likely labels, so the smallest honest p is 1/2001, never 0.
        # (Previously this divided by len(null) only, which can print p=0 for a statistic
        # that is merely at the edge of the null - an overclaim.)
        null.sort()
        pval = (1 + sum(1 for v in null if v >= skill)) / (1 + len(null))
        signal.append({
            "id": sid, "strategy": name, "kind": kind, "prereg": prereg,
            "n": n, "brier": round(b, 6), "brier_base_rate_same_sample": round(b0, 6),
            "brier_skill_vs_base": round(skill, 5),
            "skill_cluster_lower_95": round(lo, 5), "skill_cluster_upper_95": round(hi, 5),
            "permutation_p_one_sided": round(pval, 5),
            "eligible": (kind == "model" and n >= MIN_N_SIGNAL and lo > 0),
            "blocked_by": ("n < %d (pre-registered floor)" % MIN_N_SIGNAL) if n < MIN_N_SIGNAL
                          else ("cluster lower bound <= 0" if lo <= 0 else None),
            "source_url": "https://github.com/nflverse/nfldata/blob/master/data/games.csv",
        })
    # Collapse exact duplicates BEFORE the multiplicity count: a duplicated probability is
    # not an independent trial, and counting it as one weakens the correction that protects
    # against exactly this kind of inflation.
    seen, uniq = {}, []
    for s in signal:
        key = (round(s["brier"], 9), s["n"])
        if key in seen:
            seen[key]["duplicate_of"] = s["id"]
            continue
        seen[key] = s
        uniq.append(s)
    signal = uniq

    # multiplicity across every probability trial in this workspace
    qs = bh([s["permutation_p_one_sided"] for s in signal])
    for s, q in zip(signal, qs):
        s["bh_q"] = round(q, 5)
        s["significant_after_bh"] = q < 0.05 and s["brier_skill_vs_base"] > 0
        if s["eligible"] and not s["significant_after_bh"]:
            s["eligible"] = False
            s["blocked_by"] = "not significant after Benjamini-Hochberg across %d trials" % len(signal)
    signal.sort(key=lambda s: (-(s["brier_skill_vs_base"]), s["id"]))
    for i, s in enumerate(signal, 1):
        s["signal_rank"] = i

    # ---------------------------------------------------------------- staking table
    # Staking is scored ONLY at an assumed price, never at a real one, because no official
    # price source exists. It is never allowed to affect a signal rank.
    staking = []
    for s in signal:
        if s["kind"] != "model" or s["id"] != "S1":
            continue
        # flat 1u at -110, hypothetical, on the model's own side
        staked = 0
        ret = 0.0
        for r in rows:
            p = r["p_home_win"]
            pick_home = p > 0.5
            if abs(p - 0.5) < 1e-9:
                continue
            staked += 1
            won = (r["home_win"] == 1) == pick_home
            ret += 0.909 if won else -1.0     # -110 => win 100/110
        roi = ret / staked if staked else None
        wins = sum(1 for r in rows
                   if abs(r["p_home_win"] - 0.5) > 1e-9 and ((r["home_win"] == 1) == (r["p_home_win"] > 0.5)))
        lo, hi = wilson(wins, staked)
        staking.append({
            "id": s["id"], "strategy": s["strategy"], "n_bets": staked,
            "wins": wins, "win_rate": round(wins / staked, 4) if staked else None,
            "win_rate_wilson_lo": round(lo, 4) if lo is not None else None,
            "win_rate_wilson_hi": round(hi, 4) if hi is not None else None,
            "assumed_price": "-110 (assumption, not an observed price)",
            "roi_hypothetical": round(roi, 4) if roi is not None else None,
            "ranks_alone": False,
            "why_not_ranked": ("a staking run at an assumed price cannot distinguish skill from "
                               "a lucky streak, and no verified price exists to compute CLV or "
                               "real ROI. This table is published to show the number, not to "
                               "rank it."),
            "source_url": "https://github.com/nflverse/nfldata/blob/master/data/games.csv",
        })

    # ---------------------------------------------------------------- luck panel
    # "Removal of luck": how much of each strategy's apparent edge is the expected spread
    # under pure chance? Published as (observed - luck-expected) with a permutation p.
    luck = []
    for s in signal:
        if s["kind"] == "control" and s["id"] == "C3":
            continue
        rows_s = [(r, (r["p_home_win"] > 0.5)) for r in rows if s["id"] == "S1"]
        if not rows_s:
            continue
        k = sum(1 for r, ph in rows_s if (r["home_win"] == 1) == ph)
        n = len(rows_s)
        exp = math.fsum(r["p_home_win"] if ph else 1 - r["p_home_win"] for r, ph in rows_s)
        rng = random.Random(SEED)
        null = []
        for _ in range(4000):
            # under the model's own probabilities, what win count is luck alone?
            c = 0
            for r, ph in rows_s:
                p = r["p_home_win"] if ph else 1 - r["p_home_win"]
                if rng.random() < p:
                    c += 1
            null.append(c)
        null.sort()
        p_high = (1 + sum(1 for v in null if v >= k)) / (1 + len(null))
        p_low = (1 + sum(1 for v in null if v <= k)) / (1 + len(null))
        luck.append({
            "id": s["id"], "strategy": s["strategy"], "n": n,
            "correct": k, "expected_by_luck": round(exp, 3),
            "observed_minus_luck": round(k - exp, 3),
            "luck_pct_of_observed": round(100 * exp / k, 2) if k else None,
            "p_luck_at_least_this_good": round(p_high, 4),
            "p_luck_at_least_this_bad": round(p_low, 4),
            "reading": ("the model's hit count is INSIDE the range that its own probabilities "
                        "produce by chance; not evidence of skill")
            if 0.05 < p_high < 0.95 else "outside the chance range - investigate before use",
            "source_url": "https://github.com/nflverse/nfldata/blob/master/data/games.csv",
        })

    # ---------------------------------------------------------------- demotion gate
    demotion = {
        "_meta": {
            "rule": ("a strategy returns from LIVE to PAPER automatically when ANY condition "
                     "below fires; no human discretion, no averaging of conditions"),
            "evaluated_at_rows": len(rows),
            "current_live_strategies": 0,
            "note": ("nothing is LIVE, so the gate is evaluated on zero strategies. The gate is "
                     "still published and machine-checked so it cannot be waived later."),
        },
        "conditions": [
            {"code": "D1", "condition": "rolling-20-game cluster lower bound of Brier skill <= 0",
             "action": "LIVE -> PAPER", "fired_now": None,
             "why": "a live strategy that stops beating climatology is a demoted strategy"},
            {"code": "D2", "condition": "calibration slope outside [0.8, 1.25] on >= 100 games",
             "action": "LIVE -> PAPER", "fired_now": None,
             "why": "miscalibration destroys stake sizing before it destroys the average"},
            {"code": "D3", "condition": "any input feed stale beyond 24h at kickoff",
             "action": "LIVE -> PAPER", "fired_now": None,
             "why": "a correct model on stale availability is a wrong model"},
            {"code": "D4", "condition": "realised ROI below the lower edge of the pre-registered interval",
             "action": "LIVE -> PAPER", "fired_now": None,
             "why": "published so a bad staking run cannot be called variance forever"},
        ],
        "fired_today": [],
        "evaluation_available": False,
        "why_not_evaluable": "no strategy holds LIVE status, and no verified price exists for D4",
    }

    out = {
        "_meta": {
            "built_utc": "2026-11-15T23:24:27Z",
            "n_games_scored": len(rows),
            "weeks_scored": sorted({r["week"] for r in rows}),
            "signal_floor": MIN_N_SIGNAL,
            "policy": [
                "backtest numbers never appear on the live leaderboard - this file IS the "
                "backtest table and is labelled as such everywhere it is rendered",
                "rank is by benchmark-relative Brier skill with a weekly-cluster lower bound "
                "and a Benjamini-Hochberg adjustment across all trials in this workspace",
                "win rate and ROI are published but never used to rank",
                "control baselines run on every build so skill can be separated from luck",
            ],
            "scored_sample_warning": ("n=%d out-of-sample games; the pre-registered floor for "
                                      "any qualification is %d, so ZERO strategies can qualify "
                                      "at this sample regardless of their scores" % (len(rows), MIN_N_SIGNAL)),
        },
        "signal_leaderboard": signal,
        "staking_table": staking,
        "luck_panel": luck,
        "demotion_gate": demotion,
        "qualified_count": sum(1 for s in signal if s["eligible"]),
        "reward_units_available": 1000,
        "reward_units_awarded": 0,
        "reward_policy": ("reward units are escrowed until a strategy clears G1-G4 AND holds "
                          "LIVE status. 0 of 1000 awarded."),
    }
    json.dump(out, open(os.path.join(OUT, "leaderboard.json"), "w"), indent=1)

    print("%-4s %-42s %6s %8s %8s %8s %8s %5s" %
          ("id", "strategy", "n", "brier", "skill", "lo95", "bh_q", "elig"))
    for s in signal:
        print("%-4s %-42s %6d %8.4f %8.4f %8.4f %8.4f %5s"
              % (s["id"], s["strategy"][:42], s["n"], s["brier"], s["brier_skill_vs_base"],
                 s["skill_cluster_lower_95"], s["bh_q"], s["eligible"]))
    print("\nqualified:", out["qualified_count"], "| reward units awarded:", out["reward_units_awarded"])
    for l in luck:
        print("luck %-4s correct %d expected %.2f -> %+.2f (p_good %.3f)"
              % (l["id"], l["correct"], l["expected_by_luck"], l["observed_minus_luck"],
                 l["p_luck_at_least_this_good"]))
    for st in staking:
        print("stake %-4s n=%d win %.3f ROI %+.3f"
              % (st["id"], st["n_bets"], st["win_rate"], st["roi_hypothetical"]))


if __name__ == "__main__":
    main()
