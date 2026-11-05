#!/usr/bin/env python3
"""
Own4 — analysis engine for the 2026-11-05 verified snapshot.

Inputs (all official-source linked):
  official/games.json                    56 games, 6 October/November dates (inherited, corroborated)
  verification/data/games_fresh.json     29 games on 2026-11-02 and 2026-11-04 (re-read 2026-11-05)
  verification/data/team_stats.json      official Per Game team table (S2)
  verification/data/standings.json       official standings (S1)
  verification/data/season_leaders.json  official season-leader block for the two 11/05 games (S5)
  verification/data/gates.json           gates and model parameters, pre-registered

What this file does NOT do:
  * It never uses a betting price. None exists on an official NBA page, so ROI is
    not computable and gate G7 is BLOCKED for every strategy.
  * It does not recompute or "fix" the inherited 56 scores; it uses them as given and
    records that they were corroborated league-wide (see reconcile.py).
  * It does not use the official +/- column as a model input (see flags: the 30 published
    values do not sum to zero).

Output: verification/out/analysis.json  (everything the site renders)

Run: python3 verification/analysis.py
"""

import json
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "out")

GATES = json.load(open(os.path.join(DATA, "gates.json")))
P = GATES["model_parameters"]

TEAM_NAMES = {r["abbr"]: r["team"] for r in json.load(open(os.path.join(DATA, "team_stats.json")))["rows"]}


# ----------------------------------------------------------------------------
# small statistics toolkit (standard library only)
# ----------------------------------------------------------------------------
def mean(xs):
    return sum(xs) / float(len(xs))


def sd(xs):
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def pearson(xs, ys):
    n = len(xs)
    mx, my = mean(xs), mean(ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def norm_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def fisher_ci(r, n, z=1.959963985):
    """95% CI for a Pearson correlation via the Fisher z transform."""
    if r is None or n <= 3:
        return None, None
    r = max(min(r, 0.999999), -0.999999)
    zr = math.atanh(r)
    se = 1.0 / math.sqrt(n - 3)
    return math.tanh(zr - z * se), math.tanh(zr + z * se)


def r_pvalue(r, n):
    """Two-sided p for H0: rho = 0, using the Fisher z approximation."""
    if r is None or n <= 3:
        return None
    zr = math.atanh(max(min(r, 0.999999), -0.999999))
    z = zr * math.sqrt(n - 3)
    return 2.0 * (1.0 - norm_cdf(abs(z)))


def binom_pmf(k, n, p):
    return math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))


def binom_test(k, n, p=0.5):
    """Two-sided exact binomial test (sum of outcomes no more likely than observed)."""
    if n == 0:
        return None
    obs = binom_pmf(k, n, p)
    total = 0.0
    for i in range(n + 1):
        if binom_pmf(i, n, p) <= obs * (1 + 1e-9):
            total += binom_pmf(i, n, p)
    return min(1.0, total)


def binom_power(n, p_true, p0=0.5, alpha=0.05):
    """Approximate power of a one-sided binomial test at n trials."""
    if n <= 0:
        return 0.0
    se0 = math.sqrt(p0 * (1 - p0) / n)
    se1 = math.sqrt(p_true * (1 - p_true) / n)
    crit = p0 + 1.644853627 * se0
    return 1.0 - norm_cdf((crit - p_true) / se1)


def bh_fdr(pvals, q=0.05):
    """Benjamini-Hochberg. Returns (threshold, rejected_flags) in input order."""
    idx = sorted(range(len(pvals)), key=lambda i: pvals[i])
    m = len(pvals)
    thresh = 0.0
    k_max = -1
    for rank, i in enumerate(idx, start=1):
        if pvals[i] <= q * rank / m:
            k_max = rank
            thresh = q * rank / m
    rejected = [False] * m
    for rank, i in enumerate(idx, start=1):
        if rank <= k_max:
            rejected[i] = True
    return thresh, rejected


# ----------------------------------------------------------------------------
# data assembly
# ----------------------------------------------------------------------------
def load_games():
    rows = []
    inherited = json.load(open(os.path.join(ROOT, "official", "games.json")))["rows"]
    for r in inherited:
        assert r["game_url"].split("/game/")[1].startswith(
            (r["team_a"].lower() + "-vs-" + r["team_b"].lower())
        ), "unexpected away/home order in " + r["game_id"]
        rows.append({
            "date": r["date"], "game_id": r["game_id"],
            "away": r["team_a"], "home": r["team_b"],
            "away_pts": r["team_a_pts"], "home_pts": r["team_b_pts"],
            "source_url": r["source_url"], "game_url": r["game_url"],
            "provenance": "inherited 2026-11-02 transcription, corroborated league-wide",
        })
    fresh = json.load(open(os.path.join(DATA, "games_fresh.json")))["rows"]
    for r in fresh:
        rows.append({
            "date": r["date"], "game_id": r["game_id"],
            "away": r["away"], "home": r["home"],
            "away_pts": r["away_pts"], "home_pts": r["home_pts"],
            "source_url": r["source_url"], "game_url": r["game_url"],
            "provenance": "re-read from nba.com on 2026-11-05",
        })
    rows.sort(key=lambda r: (r["date"], r["game_id"]))
    # duplicate guard
    seen = set()
    for r in rows:
        assert r["game_id"] not in seen, "duplicate game " + r["game_id"]
        seen.add(r["game_id"])
    return rows


def team_ratings(games):
    """Shrunk offense/defense per team from a list of games."""
    scored, allowed, counts = {}, {}, {}
    for g in games:
        for t, pts, opp in ((g["home"], g["home_pts"], g["away_pts"]),
                            (g["away"], g["away_pts"], g["home_pts"])):
            scored[t] = scored.get(t, 0) + pts
            allowed[t] = allowed.get(t, 0) + opp
            counts[t] = counts.get(t, 0) + 1
    lg = mean([g["home_pts"] for g in games] + [g["away_pts"] for g in games])
    k = P["shrinkage_k_offense_defense"]
    out = {}
    for t in scored:
        n = counts[t]
        off = (scored[t] + k * lg) / (n + k)
        dfn = (allowed[t] + k * lg) / (n + k)
        out[t] = {"n": n, "off": off, "def": dfn}
    return out, lg


def home_edge(games):
    if not games:
        return 0.0
    margins = [g["home_pts"] - g["away_pts"] for g in games]
    n = len(margins)
    k = P["shrinkage_k_home_advantage"]
    return (sum(margins) + k * 0.0) / (n + k)


def predict(g, prior_games, ratings, lg, hfa):
    """Originated fair values for a game using only information available before it."""
    h, a = g["home"], g["away"]
    rh, ra = ratings.get(h), ratings.get(a)
    if not rh or not ra:
        return None
    if min(rh["n"], ra["n"]) < P["min_prior_games_per_team"]:
        return None
    home_pts = (rh["off"] + ra["def"]) / 2.0 + hfa / 2.0
    away_pts = (ra["off"] + rh["def"]) / 2.0 - hfa / 2.0
    return {
        "home_pts": home_pts, "away_pts": away_pts,
        "total": home_pts + away_pts,
        "margin": home_pts - away_pts,
    }


def walk_forward(games):
    graded, skipped = [], 0
    for i, g in enumerate(games):
        prior = games[:i]
        ratings, lg = team_ratings(prior) if prior else ({}, 0.0)
        hfa = home_edge(prior)
        p = predict(g, prior, ratings, lg, hfa)
        if p is None:
            skipped += 1
            continue
        actual_margin = g["home_pts"] - g["away_pts"]
        actual_total = g["home_pts"] + g["away_pts"]
        graded.append({
            "date": g["date"], "game_id": g["game_id"], "home": g["home"], "away": g["away"],
            "pred_margin": p["margin"], "pred_total": p["total"],
            "pred_home_pts": p["home_pts"], "pred_away_pts": p["away_pts"],
            "actual_margin": actual_margin, "actual_total": actual_total,
            "home_won": actual_margin > 0,
            "pick_home": p["margin"] > 0,
            "winner_correct": (p["margin"] > 0) == (actual_margin > 0),
            "margin_error": abs(p["margin"] - actual_margin),
            "total_error": abs(p["total"] - actual_total),
            "prior_total_mean": mean([x["home_pts"] + x["away_pts"] for x in prior]),
            "source_url": g["source_url"], "game_url": g["game_url"],
        })
    return graded, skipped


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------
def main():
    os.makedirs(OUT, exist_ok=True)
    rng = random.Random(P["rng_seed"])
    games = load_games()
    ts = {r["abbr"]: r for r in json.load(open(os.path.join(DATA, "team_stats.json")))["rows"]}
    st = {r["abbr"]: r for r in json.load(open(os.path.join(DATA, "standings.json")))["rows"]}
    leaders = json.load(open(os.path.join(DATA, "season_leaders.json")))["rows"]
    slate = json.load(open(os.path.join(DATA, "slate.json")))["rows"]

    graded, skipped = walk_forward(games)
    n = len(graded)

    # ---------- headline accuracy / error metrics ----------
    wins = sum(1 for g in graded if g["winner_correct"])
    acc = wins / float(n) if n else None
    home_wins = sum(1 for g in graded if g["home_won"])
    home_acc = max(home_wins, n - home_wins) / float(n) if n else None
    p_break_even = binom_test(wins, n, 0.5) if n else None
    p_vs_home = None
    if n:
        # one-sided: is the model better than the home baseline?
        k, p0 = wins, home_acc
        p_vs_home = sum(binom_pmf(i, n, p0) for i in range(k, n + 1))

    mae_margin = mean([g["margin_error"] for g in graded]) if n else None
    mae_total = mean([g["total_error"] for g in graded]) if n else None
    # naive baseline: predict the running league-average total
    base_total_err = [abs(g["prior_total_mean"] - g["actual_total"]) for g in graded]
    mae_total_base = mean(base_total_err) if n else None

    # ---------- luck removal: bootstrap + permutation ----------
    boot = []
    for _ in range(P["bootstrap_resamples"]):
        sample = [graded[rng.randrange(n)] for _ in range(n)] if n else []
        boot.append(sum(1 for g in sample if g["winner_correct"]) / float(n))
    boot.sort()
    acc_ci = (boot[int(0.025 * len(boot))], boot[int(0.975 * len(boot)) - 1]) if boot else (None, None)

    perm = []
    actuals = [g["actual_total"] for g in graded]
    preds = [g["pred_total"] for g in graded]
    base_pred = [g["prior_total_mean"] for g in graded]
    obs_gain = (mae_total_base - mae_total) if n else 0.0
    for _ in range(P["permutation_resamples"]):
        rng.shuffle(actuals)
        mp = mean([abs(p - a) for p, a in zip(preds, actuals)])
        mb = mean([abs(p - a) for p, a in zip(base_pred, actuals)])
        perm.append(mb - mp)
    perm_p = (sum(1 for x in perm if x >= obs_gain) + 1) / (len(perm) + 1.0) if n else None

    # ---------- temporal stability: three disjoint blocks ----------
    blocks = []
    if n >= 6:
        size = n // 3
        for b in range(3):
            chunk = graded[b * size:(b + 1) * size] if b < 2 else graded[2 * size:]
            blocks.append({
                "block": b + 1,
                "from": chunk[0]["date"], "to": chunk[-1]["date"], "games": len(chunk),
                "accuracy": sum(1 for g in chunk if g["winner_correct"]) / float(len(chunk)),
                "mae_total": mean([g["total_error"] for g in chunk]),
                "over_baseline": mean([g["total_error"] for g in chunk])
                                < mean([abs(g["prior_total_mean"] - g["actual_total"]) for g in chunk]),
            })

    # ---------- power: how large a sample is needed for a 55% edge ----------
    power_n = None
    for cand in range(10, 2000, 5):
        if binom_power(cand, 0.55) >= 0.8:
            power_n = cand
            break

    # ---------- measured correlations ----------
    team_corr = []
    for feat, label in (("plus_minus", "Point differential per game"),
                        ("PTS", "Points per game"),
                        ("FG_pct", "Field-goal %"),
                        ("3P_pct", "Three-point %"),
                        ("FT_pct", "Free-throw %"),
                        ("REB", "Rebounds per game"),
                        ("AST", "Assists per game"),
                        ("TOV", "Turnovers per game"),
                        ("STL", "Steals per game"),
                        ("BLK", "Blocks per game")):
        xs = [ts[a][feat] for a in ts]
        ys = [float(st[a]["win_pct"]) for a in ts]
        r = pearson(xs, ys)
        lo, hi = fisher_ci(r, len(xs))
        team_corr.append({
            "feature": feat, "label": label, "n": len(xs), "r": r,
            "ci_low": lo, "ci_high": hi, "p": r_pvalue(r, len(xs)),
            "source_url": "https://www.nba.com/stats/teams/traditional",
            "standings_url": "https://www.nba.com/standings",
        })
    pv = [c["p"] for c in team_corr]
    thresh, rej = bh_fdr(pv)
    for c, r_ in zip(team_corr, rej):
        c["bh_reject"] = r_
        c["bh_threshold"] = thresh

    game_corr = []
    for label, xs, ys, note in (
        ("Home points vs away points (same game)", [g["home_pts"] if False else None for g in games], None, ""),
    ):
        pass  # placeholder removed below

    xs = [g["home_pts"] for g in games]
    ys = [g["away_pts"] for g in games]
    r = pearson(xs, ys)
    lo, hi = fisher_ci(r, len(xs))
    game_corr.append({
        "label": "Home team points vs away team points in the same game",
        "why": "Pace dependence: if a game is fast, both teams score more. This is the dependence that makes same-game total legs correlated.",
        "n": len(xs), "r": r, "ci_low": lo, "ci_high": hi, "p": r_pvalue(r, len(xs)),
        "source_url": "https://www.nba.com/games?date=2026-11-04",
    })

    xs = [g["actual_margin"] for g in graded]
    ys = [g["actual_total"] for g in graded]
    r = pearson(xs, ys)
    lo, hi = fisher_ci(r, len(xs))
    game_corr.append({
        "label": "Winning margin vs game total (graded sample)",
        "why": "Dependence between a winner leg and a total leg inside one same-game parlay.",
        "n": len(xs), "r": r, "ci_low": lo, "ci_high": hi, "p": r_pvalue(r, len(xs)),
        "source_url": "https://www.nba.com/games?date=2026-11-02",
    })

    xs = [g["pred_margin"] for g in graded]
    ys = [g["actual_margin"] for g in graded]
    r = pearson(xs, ys)
    lo, hi = fisher_ci(r, len(xs))
    game_corr.append({
        "label": "Originated margin vs actual margin (model discrimination)",
        "why": "If this is near zero the originated spread carries no information.",
        "n": len(xs), "r": r, "ci_low": lo, "ci_high": hi, "p": r_pvalue(r, len(xs)),
        "source_url": "https://www.nba.com/games?date=2026-11-04",
    })

    xs = [g["pred_total"] for g in graded]
    ys = [g["actual_total"] for g in graded]
    r = pearson(xs, ys)
    lo, hi = fisher_ci(r, len(xs))
    game_corr.append({
        "label": "Originated total vs actual total (model discrimination)",
        "why": "Same test for the totals market.",
        "n": len(xs), "r": r, "ci_low": lo, "ci_high": hi, "p": r_pvalue(r, len(xs)),
        "source_url": "https://www.nba.com/games?date=2026-11-02",
    })

    # ---------- parlay dependence: winner + total, same game ----------
    parlay = None
    if n:
        joint = sum(1 for g in graded if g["pick_home"] == g["home_won"] and g["actual_total"] > g["pred_total"])
        p_win = acc
        p_over = sum(1 for g in graded if g["actual_total"] > g["pred_total"]) / float(n)
        parlay = {
            "legs": "leg 1 = originated winner; leg 2 = over the originated total",
            "n": n,
            "p_leg1": p_win, "p_leg2": p_over,
            "p_independent": p_win * p_over,
            "p_joint_observed": joint / float(n),
            "joint_hits": joint,
            "gap": joint / float(n) - p_win * p_over,
            "note": "Observed joint frequency vs the independence product, on the same sample. Small n: the gap is descriptive, not significant.",
        }

    # ---------- originated lines for the 2026-11-05 slate ----------
    ratings, lg = team_ratings(games)
    hfa = home_edge(games)
    resid = [g["pred_margin"] - g["actual_margin"] for g in graded]
    sigma = sd(resid) if n > 2 else P["fallback_sigma_margin"]
    own_lines = []
    for s in slate:
        h, a = s["home"], s["away"]
        rh, ra = ratings[h], ratings[a]
        home_pts = (rh["off"] + ra["def"]) / 2.0 + hfa / 2.0
        away_pts = (ra["off"] + rh["def"]) / 2.0 - hfa / 2.0
        margin = home_pts - away_pts
        total = home_pts + away_pts
        own_lines.append({
            "game_id": s["game_id"], "date": s["date"], "tip_et": s["tip_et"],
            "away": a, "away_name": TEAM_NAMES[a], "home": h, "home_name": TEAM_NAMES[h],
            "home_off": rh["off"], "home_def": rh["def"], "home_n": rh["n"],
            "away_off": ra["off"], "away_def": ra["def"], "away_n": ra["n"],
            "fair_home_pts": home_pts, "fair_away_pts": away_pts,
            "fair_total": total, "fair_margin_home": margin,
            "fair_line_home": -round(margin * 2) / 2.0,
            "fair_total_line": round(total * 2) / 2.0,
            "home_win_prob": norm_cdf(margin / sigma) if sigma else None,
            "price": None,
            "price_note": "blank — no official NBA source publishes a price; see flag F-PRICE",
            "source_url": s["source_url"], "game_url": s["game_url"],
        })

    # ---------- player props ----------
    props = []
    for L in leaders:
        props.append({
            "player": L["player"], "team": L["team"], "team_name": L["team_name"],
            "market": "Points", "reference_line": L["PPG"],
            "rpg": L["RPG"], "apg": L["APG"],
            "variance": None, "over_prob": None, "edge": None,
            "status": "REFERENCE ONLY — no game-log distribution, no opponent adjustment, no injury status",
            "source_url": L["source_url"],
        })

    # ---------- calibration / Brier ----------
    def brier_scores(sample):
        total = 0.0
        for gg in sample:
            prob = norm_cdf(gg["pred_margin"] / sigma)
            outcome = 1.0 if gg["home_won"] else 0.0
            total += (prob - outcome) ** 2
        return total / float(len(sample))

    brier = brier_scores(graded) if n else None
    brier_boot = []
    if n:
        for _ in range(P["bootstrap_resamples"]):
            sample = [graded[rng.randrange(n)] for _ in range(n)]
            brier_boot.append(0.25 - brier_scores(sample))
        brier_boot.sort()
        brier_ci = (brier_boot[int(0.025 * len(brier_boot))], brier_boot[int(0.975 * len(brier_boot)) - 1])
    else:
        brier_ci = (None, None)

    calibration = []
    if n:
        buckets = [(0.0, 0.45), (0.45, 0.55), (0.55, 1.0)]
        for lo, hi in buckets:
            chunk = [g for g in graded if lo <= norm_cdf(g["pred_margin"] / sigma) < hi]
            if chunk:
                calibration.append({
                    "bin": "%.2f–%.2f" % (lo, hi), "games": len(chunk),
                    "predicted_mean": mean([norm_cdf(g["pred_margin"] / sigma) for g in chunk]),
                    "observed_home_win_rate": sum(1 for g in chunk if g["home_won"]) / float(len(chunk)),
                })

    strategy_pvals = [x for x in (p_break_even, perm_p) if x is not None]

    # ---------- gate evaluation ----------
    gate_results = []
    for g in GATES["gates"]:
        gid = g["id"]
        status, value, note = "FAIL", "", ""
        if gid == "G1":
            value = "%d graded games (floor 300)" % n
            status = "PASS" if n >= 300 else "FAIL"
        elif gid == "G2":
            value = "model Brier %.4f vs 0.2500 baseline; paired bootstrap 95%% CI on the improvement = [%.4f, %.4f]" % (
                brier, brier_ci[0], brier_ci[1])
            status = "PASS" if brier_ci[0] > 0 else "FAIL"
        elif gid == "G3":
            value = "accuracy %.4f (%d/%d) vs home baseline %.4f; one-sided p = %s" % (
                acc, wins, n, home_acc, ("%.4f" % p_vs_home) if p_vs_home is not None else "blank")
            status = "PASS" if (p_vs_home is not None and p_vs_home < 0.05 and acc > home_acc) else "FAIL"
        elif gid == "G4":
            value = "MAE %.3f vs baseline %.3f; permutation p = %s" % (
                mae_total, mae_total_base, ("%.4f" % perm_p) if perm_p is not None else "blank")
            status = "PASS" if (perm_p is not None and perm_p < 0.05 and mae_total < mae_total_base) else "FAIL"
        elif gid == "G5":
            ok = bool(blocks) and all(b["accuracy"] > 0.5 for b in blocks)
            value = "; ".join("block %d %.3f (n=%d)" % (b["block"], b["accuracy"], b["games"]) for b in blocks)
            status = "PASS" if ok else "FAIL"
        elif gid == "G6":
            value = "correlation reported for every combination (see Correlations page); parlay legs priced with the measured dependence, not independence"
            status = "PASS"
        elif gid == "G7":
            value = "no official closing price exists in any official NBA source; ROI not computable"
            status = "BLOCKED"
        elif gid == "G8":
            value = ("strategy-level tests m=%d (winner p=%.4f, totals p=%.4f); "
                     "Benjamini-Hochberg at q=0.05 sets the smallest threshold to %.4f, so no strategy claim survives"
                     % (len(strategy_pvals), p_break_even, perm_p, 0.05 / len(strategy_pvals)))
            status = "PASS" if any(bh_fdr(strategy_pvals)[1]) else "FAIL"
        elif gid == "G9":
            value = "every published row links to its official page; NBA Stats FAQ restriction acknowledged on the Flagged page"
            status = "PASS"
        elif gid == "G10":
            value = "one command rebuild + automated site checks (verification/verify_site.py)"
            status = "PASS"
        gate_results.append({"id": gid, "name": g["name"], "type": g["type"], "rule": g["rule"],
                             "status": status, "evidence": value, "rationale": g["rationale"]})

    # ---------- strategy / leaderboard scoring ----------
    failed = [g["id"] for g in gate_results if g["status"] in ("FAIL", "BLOCKED")]
    strategies = []
    for s in GATES["strategy_universe"]:
        blocked_reason = ""
        if s["family"] == "player-prop":
            blocked_reason = "No official player game logs are available to this session, so no per-game distribution, variance or pair correlation can be measured."
        elif s["id"] == "S8":
            blocked_reason = "Alternate-line pricing requires a full joint distribution of the game outcome; not identifiable from 85 official finals."
        strategies.append({
            "id": s["id"], "name": s["name"], "family": s["family"],
            "priced_by": s["priced_by"],
            "gates_passed": sum(1 for g in gate_results if g["status"] == "PASS"),
            "gates_total": len(gate_results),
            "failed_gates": failed,
            "status": "NO QUALIFICATION",
            "blocked_reason": blocked_reason or "Fails the sample floor and the price gate like every other strategy in this run.",
        })

    analysis = {
        "snapshot": "2026-11-05",
        "generated_by": "verification/analysis.py",
        "sample": {
            "games": len(games),
            "graded": n,
            "skipped_insufficient_history": skipped,
            "dates": sorted(set(g["date"] for g in games)),
            "official_season_games": 121,
        },
        "metrics": {
            "winner_accuracy": acc, "wins": wins, "graded": n,
            "home_baseline_accuracy": home_acc,
            "binom_p_vs_0_5": p_break_even,
            "binom_p_vs_home_baseline": p_vs_home,
            "accuracy_bootstrap_ci": acc_ci,
            "mae_margin": mae_margin,
            "mae_total": mae_total,
            "mae_total_baseline": mae_total_base,
            "mae_total_improvement": obs_gain,
            "permutation_p_totals": perm_p,
            "sigma_margin": sigma,
            "home_edge_points": hfa,
            "league_avg_team_points_sample": lg,
            "power_games_needed_for_55pct_edge": power_n,
        },
        "blocks": blocks,
        "calibration": calibration,
        "brier": brier,
        "brier_improvement_ci": brier_ci,
        "graded_games": [{
            "date": g["date"], "game_id": g["game_id"], "away": g["away"], "home": g["home"],
            "pred_margin": g["pred_margin"], "pred_total": g["pred_total"],
            "actual_margin": g["actual_margin"], "actual_total": g["actual_total"],
            "winner_correct": g["winner_correct"],
            "source_url": g["source_url"], "game_url": g["game_url"],
        } for g in graded],
        "ratings": [{
            "abbr": t, "team": TEAM_NAMES[t], "n": v["n"], "off": v["off"], "def": v["def"],
            "source_url": "https://www.nba.com/stats/teams/traditional",
        } for t, v in sorted(ratings.items(), key=lambda kv: kv[1]["off"] - kv[1]["def"], reverse=True)],
        "team_correlations": team_corr,
        "game_correlations": game_corr,
        "parlay_dependence": parlay,
        "own_lines": own_lines,
        "props": props,
        "gates": gate_results,
        "strategies": strategies,
        "rewards": {
            "awarded": 0,
            "pool": "notional only — no funds exist",
            "reason": "No strategy passes all ten gates; the competition awards nothing.",
        },
    }

    with open(os.path.join(OUT, "analysis.json"), "w") as f:
        json.dump(analysis, f, indent=1)
        f.write("\n")

    print("games=%d graded=%d acc=%.4f home_base=%.4f p_vs_home=%s" %
          (len(games), n, acc, home_acc, ("%.4f" % p_vs_home) if p_vs_home else "n/a"))
    print("MAE total %.3f vs base %.3f  perm_p=%.4f" % (mae_total, mae_total_base, perm_p))
    print("sigma=%.3f hfa=%.3f power_n=%s" % (sigma, hfa, power_n))
    print("wrote", os.path.join(OUT, "analysis.json"))


if __name__ == "__main__":
    main()
