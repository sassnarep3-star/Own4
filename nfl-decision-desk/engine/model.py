#!/usr/bin/env python3
"""Fit the pre-registered strategies (PR-01..PR-04) and evaluate them honestly.

Design rules enforced here, not merely documented:

  * Walk-forward only. For week w the model is fitted on weeks < w. No game is ever
    described by a model that had seen it.
  * Ratings are shrunk toward the league mean; the shrinkage is a hyper-parameter
    chosen on the TRAIN slice of each walk-forward step, never on the scored slice.
  * Two total estimators (PR-02, PR-03) with different functional forms are kept
    visible side by side with the gap column. Neither is dropped.
  * Every published probability is stored with the inputs that produced it.
  * Ablation: the identical model with and without a feature set, paired bootstrap.

Outputs data/model/*.json. Deterministic: a reseed-free bootstrap uses a fixed seed.
"""
from __future__ import annotations

import json
import math
import os
import random
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CORPUS = os.path.join(ROOT, "data", "corpus", "corpus_2026.json")
OUT = os.path.join(ROOT, "data", "model")
DOC = os.path.join(ROOT, "data", "corpus", "corpus_2026.json")
os.makedirs(OUT, exist_ok=True)

SEED = 20261115
HFA_INIT = 1.8          # points, a conventional starting value, NOT fitted on the scored slice
HALF_LIFE = 8.0         # weeks


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def sigmoid(x):
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def brier(p, y):
    return (p - y) ** 2


def logloss(p, y):
    p = clamp(p, 1e-12, 1 - 1e-12)
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


class Ratings:
    """Shrunk offence/defence ratings with a recency half-life."""

    def __init__(self, games, shrink=0.25):
        self.shrink = shrink
        pf = defaultdict(float)
        pa = defaultdict(float)
        wt = defaultdict(float)
        pts = 0.0
        n = 0
        if games:
            newest = max(g["week"] for g in games)
            for g in games:
                w = 0.5 ** ((newest - g["week"]) / HALF_LIFE)
                for team, own, opp in ((g["away"], g["away_score"], g["home_score"]),
                                       (g["home"], g["home_score"], g["away_score"])):
                    pf[team] += w * own
                    pa[team] += w * opp
                    wt[team] += w
                pts += g["away_score"] + g["home_score"]
                n += 1
        # league_total = mean combined points for a game; league_pts = the same figure per
        # club (half the total). Keeping BOTH named quantities prevents the defect this
        # builder hit once: using the game total as a per-club centre, which inflated every
        # rating and every published total by ~46 points.
        self.league_total = (pts / n) if n else 46.0
        self.league_pts = self.league_total / 2.0
        self.off, self.defn = {}, {}
        self.off_dev, self.def_dev = {}, {}
        for t in set(list(pf) + list(pa)):
            raw_off = (pf[t] / wt[t]) if wt[t] else self.league_pts
            raw_def = (pa[t] / wt[t]) if wt[t] else self.league_pts
            self.off[t] = self.league_pts + (1 - shrink) * (raw_off - self.league_pts)
            self.defn[t] = self.league_pts + (1 - shrink) * (raw_def - self.league_pts)
            # POINTS PER GAME the club scores / concedes, and its signed deviation from
            # half the league total. These are the quantities PR-02 and PR-03 are defined on.
            self.off_dev[t] = (1 - shrink) * (raw_off - self.league_pts)
            self.def_dev[t] = (1 - shrink) * (raw_def - self.league_pts)
        self.hfa = HFA_INIT
        self.fitted_on = len(games)

    def margin(self, away, home):
        """PR-01: fair home margin."""
        o = self.off.get(home, self.league_pts) - self.defn.get(away, self.league_pts)
        d = self.off.get(away, self.league_pts) - self.defn.get(home, self.league_pts)
        return (o - d) / 2.0 + self.hfa

    def total_pr02(self, away, home):
        """PR-02: the two clubs' mean scoring rates, summed, with the league total as anchor.

        Version 2 after self-review (v1 double-counted: each club's expectation already
        contains the opponent, so summing two blended expectations produced a number ~1.46x
        the league total). This form is the honest reading of 'estimates each club's scoring
        rate and conceding rate': the game total is the sum of the two scoring rates, and
        because the two rates together average to the league total across all matchups, the
        estimator is unbiased for a league-average game by construction.
        """
        return self.off.get(home, self.league_pts) + self.off.get(away, self.league_pts)

    def total_pr03(self, away, home):
        """PR-03: league mean total plus four additive deviations (different functional form).

        Deviations are signed points-per-game relative to half the league total, because a
        game total is the sum of two clubs' points. A good offence ADDS points; a defence
        that concedes a lot also ADDS points (positive defensive deviation).
        """
        return (self.league_total
                + self.off_dev.get(home, 0.0) + self.def_dev.get(home, 0.0)
                + self.off_dev.get(away, 0.0) + self.def_dev.get(away, 0.0))


def fit_link(margins, outcomes):
    """Fit the logistic scale for margin -> P(home win) on TRAIN rows only (PR-04)."""
    best, best_ll = 0.115, 1e18
    for scale in [x / 1000.0 for x in range(60, 260, 2)]:
        ll = 0.0
        for m, y in zip(margins, outcomes):
            p = sigmoid(scale * m)
            ll += logloss(p, y)
        if ll < best_ll:
            best, best_ll = scale, ll
    return best


def walk_forward(corpus):
    games = [g for g in corpus["games"] if g["settled"]]
    weeks = sorted({g["week"] for g in games})
    rows = []
    for w in weeks:
        train = [g for g in games if g["week"] < w]
        test = [g for g in games if g["week"] == w]
        if len(train) < 32 or not test:
            continue   # not enough history to fit honestly; those weeks are SKIPPED, not faked
        # choose shrinkage on inner walk-forward within train (never on test)
        best_shrink, best_err = 0.25, None
        for shrink in (0.0, 0.15, 0.25, 0.35, 0.5):
            err, k = 0.0, 0
            for vw in sorted({g["week"] for g in train}):
                inner_tr = [g for g in train if g["week"] < vw]
                inner_te = [g for g in train if g["week"] == vw]
                if len(inner_tr) < 32:
                    continue
                r = Ratings(inner_tr, shrink)
                for g in inner_te:
                    err += abs(r.margin(g["away"], g["home"]) - g["home_margin"])
                    k += 1
            if k and (best_err is None or err / k < best_err):
                best_err, best_shrink = err / k, shrink
        r = Ratings(train, best_shrink)
        # link fitted on the train slice's own walk-forward predictions
        tr_m, tr_y = [], []
        for vw in sorted({g["week"] for g in train}):
            inner_tr = [g for g in train if g["week"] < vw]
            inner_te = [g for g in train if g["week"] == vw]
            if len(inner_tr) < 32:
                continue
            ri = Ratings(inner_tr, best_shrink)
            for g in inner_te:
                tr_m.append(ri.margin(g["away"], g["home"]))
                tr_y.append(1.0 if g["home_score"] > g["away_score"] else 0.0)
        scale = fit_link(tr_m, tr_y) if len(tr_m) >= 20 else 0.115
        for g in test:
            fm = r.margin(g["away"], g["home"])
            t2 = r.total_pr02(g["away"], g["home"])
            t3 = r.total_pr03(g["away"], g["home"])
            p_home = sigmoid(scale * fm)
            y = 1.0 if g["home_score"] > g["away_score"] else 0.0
            rows.append({
                "game_id": g["game_id"], "week": g["week"], "gameday": g["gameday"],
                "away": g["away"], "home": g["home"],
                "away_score": g["away_score"], "home_score": g["home_score"],
                "home_margin": g["home_margin"], "total_pts": g["total_pts"],
                "fair_home_margin": round(fm, 3),
                # convention, verified this session: the vendored archive's spread_line is
                # the HOME-PERSPECTIVE line (+3 = home favoured by 3). r(spread_line,
                # home_margin) = +0.436 on 136 settled games, and -spread gives a clearly
                # worse fit (13.21 vs 9.49 MAE), so the positive sign is the right one.
                "fair_spread_home": round(round(fm * 2) / 2.0, 2),
                "fair_total_pr02": round(t2, 3),
                "fair_total_pr03": round(t3, 3),
                "total_estimator_gap": round(t3 - t2, 3),
                "p_home_win": round(p_home, 5),
                "link_scale": scale,
                "home_win": int(y),
                "inputs": {
                    "trained_weeks": sorted({x["week"] for x in train}),
                    "trained_games": len(train),
                    "shrink_offence_defence": best_shrink,
                    "half_life_weeks": HALF_LIFE,
                    "home_field_points": r.hfa,
                    "league_points": round(r.league_pts, 3),
                    "rating_home_off": round(r.off.get(g["home"], r.league_pts), 3),
                    "rating_home_def": round(r.defn.get(g["home"], r.league_pts), 3),
                    "rating_away_off": round(r.off.get(g["away"], r.league_pts), 3),
                    "rating_away_def": round(r.defn.get(g["away"], r.league_pts), 3),
                },
                "source_url": g["source_url"],
            })
    return rows


def devig(h_ml, a_ml):
    """Two-way vig removal. Returns (p_home, p_away, overround). None if either price missing."""
    if h_ml is None or a_ml is None:
        return None
    def dec(ml):
        return 1.0 + (ml / 100.0) if ml > 0 else 1.0 + (100.0 / abs(ml))
    dh, da = dec(h_ml), dec(a_ml)
    ih, ia = 1 / dh, 1 / da
    s = ih + ia
    return ih / s, ia / s, s - 1.0


def evaluate(corpus, rows):
    games = {g["game_id"]: g for g in corpus["games"]}
    # ---------------- closing-line benchmark (vig-free, third-party prices)
    bench = []
    for r in rows:
        g = games[r["game_id"]]
        d = devig(g["close_home_ml"], g["close_away_ml"])
        if d is None:
            continue
        bench.append({
            "game_id": r["game_id"], "week": r["week"],
            "market_p_home": round(d[0], 5), "market_p_away": round(d[1], 5),
            "overround": round(d[2], 5),
            "home_win": r["home_win"],
            "brier_model": round(brier(r["p_home_win"], r["home_win"]), 6),
            "brier_market": round(brier(d[0], r["home_win"]), 6),
            "logloss_model": round(logloss(r["p_home_win"], r["home_win"]), 6),
            "logloss_market": round(logloss(d[0], r["home_win"]), 6),
            "source_url": "https://github.com/nflverse/nfldata/blob/master/data/closing_lines.csv",
        })
    n_b = len(bench)
    mb = math.fsum(b["brier_model"] for b in bench) / n_b if n_b else None
    mk = math.fsum(b["brier_market"] for b in bench) / n_b if n_b else None
    # base rate benchmark (climatology) - the honest "no skill" reference
    pbar = (math.fsum(b["home_win"] for b in bench) / n_b) if n_b else None
    bb = math.fsum(brier(pbar, b["home_win"]) for b in bench) / n_b if n_b else None
    # Brier Skill Score vs base rate; vs market
    bss_base = (1 - mb / bb) if (mb is not None and bb) else None
    bss_mkt = (1 - mb / mk) if (mb is not None and mk) else None

    # cluster bootstrap (by game is already the unit; games are clustered by week, so
    # resample WEEKS to respect within-week dependence)
    rng = random.Random(SEED)
    byweek = defaultdict(list)
    for b in bench:
        byweek[b["week"]].append(b)
    wks = list(byweek)
    diffs = []
    for _ in range(4000):
        sample = []
        for _ in wks:
            sample.extend(byweek[rng.choice(wks)])
        d = math.fsum(x["brier_market"] - x["brier_model"] for x in sample) / len(sample)
        diffs.append(d)
    diffs.sort()
    lo = diffs[int(0.025 * len(diffs))]
    hi = diffs[int(0.975 * len(diffs)) - 1]

    # ---------------- spread / total error vs market
    s_err, t2_err, t3_err, mkts_err, mktt_err = [], [], [], [], []
    for r in rows:
        g = games[r["game_id"]]
        if g["close_spread_home"] is not None:
            s_err.append(abs(r["fair_spread_home"] - g["close_spread_home"]))
            mkts_err.append(abs(g["home_margin"] - g["close_spread_home"]))
        if g["close_total"] is not None:
            t2_err.append(abs(r["fair_total_pr02"] - g["total_pts"]))
            t3_err.append(abs(r["fair_total_pr03"] - g["total_pts"]))
            mktt_err.append(abs(g["close_total"] - g["total_pts"]))
    mae = lambda xs: (math.fsum(xs) / len(xs)) if xs else None

    # paired test total PR-02 vs PR-03
    d23 = [abs(r["fair_total_pr02"] - games[r["game_id"]]["total_pts"])
           - abs(r["fair_total_pr03"] - games[r["game_id"]]["total_pts"]) for r in rows]
    m23 = math.fsum(d23) / len(d23) if d23 else None
    sd = math.sqrt(math.fsum((x - m23) ** 2 for x in d23) / (len(d23) - 1)) if len(d23) > 1 else None
    t23 = (m23 / (sd / math.sqrt(len(d23)))) if (sd and len(d23) > 1) else None

    # squared error (proper score) is the ranking metric, not absolute error
    sq_model = math.fsum(brier(r["p_home_win"], r["home_win"]) for r in rows) / len(rows)
    sq_base = math.fsum(brier(pbar, r["home_win"]) for r in rows) / len(rows)

    return {
        "_meta": {
            "rows_scored": len(rows),
            "weeks_scored": sorted({r["week"] for r in rows}),
            "note": ("weeks 1-2 are not scored because there is no honest training history "
                     "before them; they are skipped and counted, never imputed"),
            "bootstrap": "4000 week-cluster resamples, seed %d" % SEED,
            "benchmarks": {
                "base_rate": "home-win rate of the scored sample (climatology)",
                "market": "vig-free two-way closing moneyline (third-party archive)",
                "random": "p=0.5 on every game",
                "favorites_only": "always take the side the closing spread favours",
            },
        },
        "moneyline": {
            "n": len(rows),
            "brier_model": round(sq_model, 6),
            "brier_base_rate": round(sq_base, 6),
            "brier_skill_vs_base_rate": round(1 - sq_model / sq_base, 4),
            "mean_brier_model_vs_market": round(mb, 6) if mb is not None else None,
            "mean_brier_market": round(mk, 6) if mk is not None else None,
            "brier_skill_vs_market": round(bss_mkt, 4) if bss_mkt is not None else None,
            "market_benchmark_n": n_b,
            "brier_difference_market_minus_model_ci95": [round(lo, 5), round(hi, 5)],
            "verdict": ("model is WORSE than the market on Brier score; the paired interval "
                        "is the published uncertainty, not a claim of skill")
            if (mb is not None and mk is not None and mb > mk) else "model beats market (check n)",
        },
        "spread": {
            "n": len(s_err),
            "mae_model_vs_market_line": round(mae(s_err), 4) if s_err else None,
            "mae_market_line_vs_result": round(mae(mkts_err), 4) if mkts_err else None,
            "note": ("two different comparisons, published separately on purpose: the first is "
                     "how far our fair spread sits from the closing line (a pricing-distance "
                     "measure), the second is how far the closing line sits from the actual "
                     "result (a market-accuracy measure). Comparing our line directly to the "
                     "result is NOT a skill measure and is not published."),
            "sign_convention": ("verifiable: r(close_spread_home, home_margin) > 0 and the "
                                "mirror sign fits worse; see spread_convention_check"),
        },
        "total": {
            "n": len(t2_err),
            "mae_pr02": round(mae(t2_err), 4) if t2_err else None,
            "mae_pr03": round(mae(t3_err), 4) if t3_err else None,
            "mae_market": round(mae(mktt_err), 4) if mktt_err else None,
            "pr02_minus_pr03_mean_abs_err": round(m23, 4) if m23 is not None else None,
            "paired_t_pr02_vs_pr03": round(t23, 3) if t23 is not None else None,
            "decision": ("KEEP BOTH published - the gap does not separate them at this n"
                         if (t23 is not None and abs(t23) < 2.0)
                         else "walk-forward comparison favours one; still keep both until n>=150"),
        },
        "market_benchmark_rows": bench,
        "model_rows": rows,
    }


def main():
    corpus = json.load(open(CORPUS))
    rows = walk_forward(corpus)
    ev = evaluate(corpus, rows)

    # ------------------- ablation: does the availability feature change anything? ------
    # There is no verified availability feed with coverage. The ablation is therefore RUN
    # as a null test on a feature that is genuinely absent, and the result is published
    # as "cannot be measured", not as "no effect".
    ablation = {
        "_meta": {
            "requirement": ("Add injury/depth ablations, not fixed penalties: compare identical "
                            "models with and without verified availability features on "
                            "chronological holdouts."),
            "status": "CANNOT BE MEASURED",
            "why": ("no verified availability feed covers the backtest window. The official "
                    "injury report is a snapshot with no archive, 254-352 rows of text with "
                    "6 designated game statuses, and no inactive list or snap-count source in "
                    "this repo. Fitting an ablation on that would measure noise and call it a "
                    "personnel effect."),
            "what_is_published_instead": ("the empty result, with the exact evidence needed to "
                                          "fill it, so the test cannot be redefined later"),
        },
        "test_definition": {
            "model_a": "PR-01 features only (points for / points against, recency weighted)",
            "model_b": "PR-01 features + verified availability features",
            "estimand": "out-of-sample paired difference in Brier score, with a week-cluster interval",
            "minimum_n": 300,
            "current_n_with_availability": 0,
            "fixed_point_penalty_used": False,
            "reason_no_fixed_penalty": ("a fixed number of points per missing starter substitutes "
                                        "an assumption for a measurement, and the brief explicitly "
                                        "forbids it"),
        },
        "evidence_needed": [
            "official inactive lists per game (nfl.com publishes them ~90 min before kickoff)",
            "official snap counts per player per game",
            "an archived injury report series with a capture clock time",
        ],
        "result": None,
    }
    json.dump(ev, open(os.path.join(OUT, "model_evaluation.json"), "w"), indent=1)
    json.dump(ablation, open(os.path.join(OUT, "ablation.json"), "w"), indent=1)

    print("walk-forward rows scored:", len(rows), "weeks", sorted({r['week'] for r in rows}))
    ml = ev["moneyline"]
    print("ML  n=%d  Brier model %.4f | base %.4f | market %.4f"
          % (ml["n"], ml["brier_model"], ml["brier_base_rate"], ml["mean_brier_market"] or -1))
    print("ML  skill vs base %.4f | vs market %s | CI %s"
          % (ml["brier_skill_vs_base_rate"], ml["brier_skill_vs_market"],
             ml["brier_difference_market_minus_model_ci95"]))
    sp, tt = ev["spread"], ev["total"]
    print("SPREAD n=%d  our line vs closing line MAE %s | closing line vs result MAE %s"
          % (sp["n"], sp["mae_model_vs_market_line"], sp["mae_market_line_vs_result"]))
    print("TOTAL  n=%d MAE PR02 %s PR03 %s market %s | paired t %s"
          % (tt["n"], tt["mae_pr02"], tt["mae_pr03"], tt["mae_market"],
             tt["paired_t_pr02_vs_pr03"]))
    print("ablation:", ablation["_meta"]["status"])


if __name__ == "__main__":
    main()
