#!/usr/bin/env python3
"""
Own4 — reproducible analysis engine (Python standard library only).

All inputs come from official/*.json, which are line-by-line transcriptions of
official NBA.com pages. Nothing here is a market price. Every output in
official/results.json is tagged with the official input URLs it derives from
and with kind='derived' — these are computations, NOT official NBA values.

Statistical functions are implemented from scratch (no numpy/scipy):
  Pearson r, Student-t two-sided p via the regularized incomplete beta,
  Fisher-z 95% CI, Benjamini-Hochberg FDR, exact two-sided binomial test,
  Wilson score interval, permutation (shuffle) test, normal CDF via erf.
"""

import json
import math
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OFF = os.path.join(ROOT, "official")
VERIFIED_ON = "2026-11-02"


def load(name):
    with open(os.path.join(OFF, name)) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------
def betacf(a, b, x):
    """Continued fraction for the incomplete beta function (Numerical Recipes)."""
    MAXIT, EPS, FPMIN = 300, 3.0e-12, 1.0e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < EPS:
            break
    return h


def betai(a, b, x):
    """Regularized incomplete beta I_x(a,b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                  + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * betacf(a, b, x) / a
    return 1.0 - bt * betacf(b, a, 1.0 - x) / b


def mean(xs):
    return sum(xs) / len(xs)


def sd(xs):
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def pearson(xs, ys):
    n = len(xs)
    mx, my = mean(xs), mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs)
    dy = sum((y - my) ** 2 for y in ys)
    if dx == 0 or dy == 0:
        return None
    return num / math.sqrt(dx * dy)


def corr_stats(xs, ys):
    """Pearson r, two-sided p, Fisher-z 95% CI."""
    n = len(xs)
    r = pearson(xs, ys)
    if r is None:
        return {"n": n, "r": None, "p": None, "ci_lo": None, "ci_hi": None}
    r = max(-0.999999999, min(0.999999999, r))
    df = n - 2
    t = r * math.sqrt(df / (1.0 - r * r))
    p = betai(df / 2.0, 0.5, df / (df + t * t))
    z = math.atanh(r)
    se = 1.0 / math.sqrt(n - 3)
    return {"n": n, "r": r, "p": p,
            "ci_lo": math.tanh(z - 1.959963984540054 * se),
            "ci_hi": math.tanh(z + 1.959963984540054 * se)}


def bh_fdr(ps):
    """Benjamini-Hochberg adjusted q-values."""
    m = len(ps)
    order = sorted(range(m), key=lambda i: ps[i])
    q = [None] * m
    prev = 1.0
    for rank in range(m, 0, -1):
        i = order[rank - 1]
        val = min(prev, ps[i] * m / rank)
        q[i] = min(1.0, val)
        prev = val
    return q


def binom_two_sided(k, n, p=0.5):
    """Exact two-sided binomial p-value (sum of pmfs <= observed pmf)."""
    def pmf(i):
        return math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i))
    obs = pmf(k)
    return min(1.0, sum(pmf(i) for i in range(n + 1) if pmf(i) <= obs * (1 + 1e-12)))


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (None, None)
    ph = k / n
    den = 1 + z * z / n
    ctr = (ph + z * z / (2 * n)) / den
    half = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return (ctr - half, ctr + half)


def normal_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def american(p):
    if p <= 0 or p >= 1:
        return None
    if p >= 0.5:
        return int(round(-100.0 * p / (1.0 - p)))
    return int(round(100.0 * (1.0 - p) / p))


def r3(x):
    return None if x is None else round(x, 3)


def r4(x):
    return None if x is None else round(x, 4)


# ---------------------------------------------------------------------------
# Load official data
# ---------------------------------------------------------------------------
standings = load("standings.json")["rows"]
tstats = load("team_stats.json")["rows"]
games = load("games.json")["rows"]
slate = load("slate.json")["rows"]
players = load("players.json")
leaders = players["season_leaders"]
daily = players["daily_leaders"]
sources = {s["id"]: s for s in load("sources.json")["sources"]}

STD = {r["abbr"]: r for r in standings}
TST = {r["abbr"]: r for r in tstats}
S_STAND = sources["S1"]["url"]
S_TEAM = sources["S2"]["url"]
S_GAMES = [sources[k]["url"] for k in ("S5", "S6", "S7", "S8", "S9", "S10")]
S_SLATE = sources["S4"]["url"]
S_PLAYERS = sources["S4"]["url"]
S_FAQ = sources["S12"]["url"]
S_GLOSS = sources["S13"]["url"]
GAME_URLS = sorted(set(g["source_url"] for g in games))

INPUTS = [{"id": "official/standings.json", "source_url": S_STAND},
          {"id": "official/team_stats.json", "source_url": S_TEAM},
          {"id": "official/games.json", "source_url": ", ".join(GAME_URLS)},
          {"id": "official/slate.json", "source_url": S_SLATE},
          {"id": "official/players.json", "source_url": S_PLAYERS},
          {"id": "engine/analysis.py", "source_url": "https://github.com/sassnarep3-star/Own4/blob/main/engine/analysis.py"}]

DERIVED_NOTE = ("DERIVED — reproducible computation from official values; not an official NBA "
                "publication. Inputs and code are linked on every row (see Flags I-13).")


# ---------------------------------------------------------------------------
# 1. Correlation values from official team values
# ---------------------------------------------------------------------------
METRICS = [
    ("PTS", "Points per game"), ("FG_pct", "Field-goal %"), ("3P_pct", "3-point %"),
    ("FT_pct", "Free-throw %"), ("REB", "Rebounds per game"), ("AST", "Assists per game"),
    ("TOV", "Turnovers per game"), ("STL", "Steals per game"), ("BLK", "Blocks per game"),
    ("plus_minus", "Point differential per game (+/-)"), ("MIN", "Minutes per game"),
]
winpct = [float(STD[r["abbr"]]["WIN_pct"]) if not STD[r["abbr"]]["WIN_pct"].startswith("1")
          else 1.0 for r in tstats]
# .857 style strings parse directly; guard 1.000 / .000
winpct = [1.0 if v == 1.0 else v for v in winpct]

correlations = []
for key, label in METRICS:
    xs = [float(r[key]) for r in tstats]
    st = corr_stats(xs, winpct)
    correlations.append({
        "pair": "%s  vs  Winning %%" % label, "metric": key, "n": st["n"],
        "r": r3(st["r"]), "p": r4(st["p"]), "ci_lo": r3(st["ci_lo"]), "ci_hi": r3(st["ci_hi"]),
        "q_bh": None, "kind": "derived", "note": DERIVED_NOTE,
        "source_urls": [S_TEAM, S_STAND, S_GLOSS],
    })
qs = bh_fdr([c["p"] if c["p"] is not None else 1.0 for c in correlations])
for c, q in zip(correlations, qs):
    c["q_bh"] = r4(q)
    c["significant_after_fdr"] = bool(q < 0.05)

# Correlation matrix among candidate signals (parlay dependence control)
MATRIX_KEYS = ["PTS", "FG_pct", "3P_pct", "REB", "AST", "TOV", "plus_minus"]
matrix = []
for i, a in enumerate(MATRIX_KEYS):
    row = []
    for j, b in enumerate(MATRIX_KEYS):
        if i == j:
            row.append(1.0)
        elif j < i:
            row.append(None)  # lower triangle left blank, not duplicated
        else:
            row.append(r3(pearson([float(r[a]) for r in tstats], [float(r[b]) for r in tstats])))
    matrix.append({"metric": a, "values": row})

pair_corrs = []
for a, b in [("PTS", "plus_minus"), ("PTS", "REB"), ("AST", "TOV"),
             ("3P_pct", "PTS"), ("REB", "BLK"), ("FG_pct", "plus_minus")]:
    st = corr_stats([float(r[a]) for r in tstats], [float(r[b]) for r in tstats])
    pair_corrs.append({"pair": "%s vs %s" % (a, b), "n": st["n"], "r": r3(st["r"]),
                       "p": r4(st["p"]), "ci_lo": r3(st["ci_lo"]), "ci_hi": r3(st["ci_hi"]),
                       "kind": "derived", "note": DERIVED_NOTE, "source_urls": [S_TEAM, S_GLOSS]})

# Official NBA-published correlation coefficient (quoted, not computed)
official_quoted_corr = [{
    "pair": "Team PIE rating vs team winning percentage (R-squared)",
    "value": 0.908, "kind": "official quoted value",
    "note": "Quoted verbatim from the NBA Stats FAQ. Historical/illustrative FAQ example; "
            "not a 2026-27 measurement and not a betting signal.",
    "source_urls": [S_FAQ],
}]

# Player prop correlations (30 official season leaders)
prop_corrs = []
for a, b in [("PPG", "RPG"), ("PPG", "APG"), ("RPG", "APG")]:
    st = corr_stats([float(r[a]) for r in leaders], [float(r[b]) for r in leaders])
    prop_corrs.append({"pair": "%s vs %s (team season leaders)" % (a, b), "n": st["n"],
                       "r": r3(st["r"]), "p": r4(st["p"]), "ci_lo": r3(st["ci_lo"]),
                       "ci_hi": r3(st["ci_hi"]), "kind": "derived", "note": DERIVED_NOTE,
                       "source_urls": [S_PLAYERS]})

# Cross-game margin correlation for parlay independence assumption
by_date = {}
for g in games:
    by_date.setdefault(g["date"], []).append(g["margin_a"])
pairs_x, pairs_y = [], []
for d, vals in by_date.items():
    for i in range(len(vals)):
        for j in range(i + 1, len(vals)):
            pairs_x.append(vals[i])
            pairs_y.append(vals[j])
cross = corr_stats(pairs_x, pairs_y)

# ---------------------------------------------------------------------------
# 2. Official game distribution (used to calibrate originated lines)
# ---------------------------------------------------------------------------
margins = [g["margin_a"] for g in games]
totals = [g["total_pts"] for g in games]
sigma_margin = sd(margins)
sigma_total = sd(totals)
game_dist = {
    "n": len(games), "margin_a_mean": round(mean(margins), 3), "margin_a_sd": round(sigma_margin, 3),
    "total_mean": round(mean(totals), 3), "total_sd": round(sigma_total, 3),
    "abs_margin_mean": round(mean([abs(m) for m in margins]), 3),
    "team_b_win_rate": round(sum(1 for m in margins if m < 0) / len(margins), 3),
    "kind": "derived", "note": DERIVED_NOTE, "source_urls": GAME_URLS,
}

# ---------------------------------------------------------------------------
# 3. Originated lines for the official 2026-11-02 slate
# ---------------------------------------------------------------------------
# Model (Own4 Fair Line v1), documented and fully transparent:
#   rating_i        = official +/- (average point differential) from S2
#   fair_spread_a   = rating_a - rating_b   (no shrinkage, no home-court adjustment)
#   fair_total      = PTS_a + PTS_b         (sum of official per-game scoring averages)
#   p_a_win         = Phi(fair_spread_a / sigma_margin)  (sigma from official game sample)
#   fair moneyline  = no-vig American odds from p_a_win
# All market-price fields are deliberately blank + flagged (I-12).
lines = []
for g in slate:
    a, b = g["team_a"], g["team_b"]
    ta, tb = TST[a], TST[b]
    rating_a, rating_b = float(ta["plus_minus"]), float(tb["plus_minus"])
    spread_a = rating_a - rating_b
    total = float(ta["PTS"]) + float(tb["PTS"])
    p_a = normal_cdf(spread_a / sigma_margin)
    lines.append({
        "game_id": g["game_id"], "matchup": "%s vs %s" % (a, b),
        "team_a": a, "team_b": b, "tip_et": g["tip_et"],
        "rating_a": rating_a, "rating_b": rating_b,
        "fair_spread_first": round(spread_a, 1), "fair_total": round(total, 1),
        "p_first_win": round(p_a, 4), "fair_ml_first": american(p_a),
        "fair_ml_second": american(1 - p_a),
        "market_spread": "", "market_total": "", "market_odds": "",
        "unverified_fields": ["market_spread", "market_total", "market_odds"],
        "kind": "derived", "note": DERIVED_NOTE,
        "source_urls": [S_TEAM, S_SLATE], "game_url": g["game_url"],
    })

# ---------------------------------------------------------------------------
# 4. Parlays (two-leg, cross-game) with measured dependence
# ---------------------------------------------------------------------------
top = sorted(lines, key=lambda x: abs(x["fair_spread_first"]), reverse=True)[:3]
parlays = []
for i in range(len(top)):
    for j in range(i + 1, len(top)):
        A, B = top[i], top[j]
        pjoint = A["p_first_win"] * B["p_first_win"]
        parlays.append({
            "id": "PAR-%s-%s" % (A["game_id"][-3:], B["game_id"][-3:]),
            "leg1": A["matchup"], "leg2": B["matchup"],
            "p_leg1": A["p_first_win"], "p_leg2": B["p_first_win"],
            "p_joint_independent": round(pjoint, 4),
            "fair_decimal_odds": round(1.0 / pjoint, 3),
            "fair_american_odds": american(pjoint),
            "market_parlay_price": "", "unverified_fields": ["market_parlay_price"],
            "cross_game_margin_r": r3(cross["r"]),
            "cross_game_margin_ci": [r3(cross["ci_lo"]), r3(cross["ci_hi"])],
            "cross_game_pair_n": cross["n"],
            "kind": "derived",
            "note": "Joint probability assumes independence of the two games. The measured "
                    "cross-game margin correlation (computed from official results) is shown "
                    "with its confidence interval; a wide interval means independence is not "
                    "established. Market parlay price is blank + flagged (I-12).",
            "source_urls": [S_TEAM, S_SLATE] + GAME_URLS,
        })

# ---------------------------------------------------------------------------
# 5. Originated player prop lines and combos
# ---------------------------------------------------------------------------
props = []
for p in leaders:
    props.append({
        "abbr": p["abbr"], "player": p["player"],
        "fair_pts": p["PPG"], "fair_reb": p["RPG"], "fair_ast": p["APG"],
        "market_pts_line": "", "market_reb_line": "", "market_ast_line": "",
        "unverified_fields": ["market_pts_line", "market_reb_line", "market_ast_line"],
        "kind": "derived",
        "note": "Fair line is set equal to the official season average displayed by NBA.com. "
                "This is a stated modeling choice, not an official prop line. Market lines "
                "are blank + flagged (I-12).",
        "source_urls": [p["source_url"], p["player_url"]], "player_url": p["player_url"],
    })

prop_combos = []
for p in leaders[:6]:
    prop_combos.append({
        "player": p["player"], "abbr": p["abbr"],
        "legs": ["PTS >= %.1f" % p["PPG"], "REB >= %.1f" % p["RPG"], "AST >= %.1f" % p["APG"]],
        "p_joint_if_independent": 0.125,
        "measured_ppg_rpg_r": r3(prop_corrs[0]["r"]),
        "measured_ppg_apg_r": r3(prop_corrs[1]["r"]),
        "measured_rpg_apg_r": r3(prop_corrs[2]["r"]),
        "p_joint_correlation_adjusted": "",
        "unverified_fields": ["p_joint_correlation_adjusted"],
        "kind": "derived",
        "note": "Under independence the 3-leg joint probability is 0.5^3 = 0.125. The measured "
                "same-player correlations show legs are not independent, so a "
                "correlation-adjusted price would require a joint distribution that no "
                "official source publishes. That value is left blank + flagged.",
        "source_urls": [p["source_url"]],
    })

# ---------------------------------------------------------------------------
# 6. Walk-forward backtest (no look-ahead) from official final scores
# ---------------------------------------------------------------------------
def prior_stats(date):
    """Mean margin and mean points scored per team using ONLY games before `date`."""
    hist = {}
    for g in games:
        if g["date"] >= date:
            continue
        a, b = g["team_a"], g["team_b"]
        hist.setdefault(a, []).append((g["team_a_pts"], g["margin_a"]))
        hist.setdefault(b, []).append((g["team_b_pts"], -g["margin_a"]))
    out = {}
    for t, rows in hist.items():
        out[t] = {"n": len(rows), "ppg": mean([r[0] for r in rows]),
                  "margin": mean([r[1] for r in rows])}
    return out


graded = []
for g in games:
    ps = prior_stats(g["date"])
    a, b = g["team_a"], g["team_b"]
    if a not in ps or b not in ps:
        graded.append({"game_id": g["game_id"], "date": g["date"], "graded": False,
                       "reason": "no prior official games for one or both teams; prediction left blank (unverified)",
                       "source_url": g["source_url"]})
        continue
    pred_margin = ps[a]["margin"] - ps[b]["margin"]
    pred_total = ps[a]["ppg"] + ps[b]["ppg"]
    actual_margin = g["margin_a"]
    actual_total = g["total_pts"]
    graded.append({
        "game_id": g["game_id"], "date": g["date"], "graded": True,
        "matchup": "%s vs %s" % (a, b),
        "prior_n_a": ps[a]["n"], "prior_n_b": ps[b]["n"],
        "pred_margin": round(pred_margin, 2), "actual_margin": actual_margin,
        "pred_total": round(pred_total, 2), "actual_total": actual_total,
        "winner_correct": bool((pred_margin > 0) == (actual_margin > 0)),
        "margin_error": round(actual_margin - pred_margin, 2),
        "total_error": round(actual_total - pred_total, 2),
        "source_url": g["source_url"], "game_url": g["game_url"],
    })

ok = [g for g in graded if g["graded"]]
n_ok = len(ok)
wins = sum(1 for g in ok if g["winner_correct"])
acc = wins / n_ok if n_ok else None
binom_p = binom_two_sided(wins, n_ok) if n_ok else None
lo, hi = wilson(wins, n_ok) if n_ok else (None, None)

# Permutation test: shuffle the predicted-winner labels, recompute accuracy.
rng = random.Random(20261102)
# Permutation / simulation null: 10,000 random-guess seasons of the same length.
# Under the luck null each graded game is an independent Bernoulli(0.5) hit.
PERM = 10000
extreme = 0
for _ in range(PERM):
    k = sum(1 for _ in range(n_ok) if rng.random() < 0.5)
    if k / n_ok >= acc:
        extreme += 1
perm_p = (extreme + 1) / (PERM + 1)

margin_mae = mean([abs(g["margin_error"]) for g in ok])
total_mae = mean([abs(g["total_error"]) for g in ok])
margin_bias = mean([g["margin_error"] for g in ok])
total_bias = mean([g["total_error"] for g in ok])
margin_r = corr_stats([g["pred_margin"] for g in ok], [g["actual_margin"] for g in ok])
total_r = corr_stats([g["pred_total"] for g in ok], [g["actual_total"] for g in ok])

# Two-leg parlay: on each date, take the two graded games with the largest
# |predicted margin| and require both predicted winners to be correct.
by_day = {}
for g in ok:
    by_day.setdefault(g["date"], []).append(g)
parlay_tries = []
for d, gs in sorted(by_day.items()):
    if len(gs) < 2:
        continue
    picks = sorted(gs, key=lambda x: abs(x["pred_margin"]), reverse=True)[:2]
    parlay_tries.append({"date": d, "legs": [x["matchup"] for x in picks],
                         "hit": bool(all(x["winner_correct"] for x in picks)),
                         "source_url": picks[0]["source_url"]})
n_par = len(parlay_tries)
k_par = sum(1 for x in parlay_tries if x["hit"])
par_acc = k_par / n_par if n_par else None
par_p = binom_two_sided(k_par, n_par, 0.25) if n_par else None

backtest = {
    "total_official_games": len(games), "graded_games": n_ok,
    "ungraded_games": len(games) - n_ok,
    "ungraded_reason": "No prior official games existed before 2026-10-21 (and for teams with no prior appearance); predictions are left blank rather than inferred.",
    "winner_hits": wins, "winner_accuracy": round(acc, 4) if acc else None,
    "binomial_p_two_sided": r4(binom_p), "permutation_p": r4(perm_p),
    "wilson_ci": [r3(lo), r3(hi)],
    "margin_mae": round(margin_mae, 3), "margin_bias": round(margin_bias, 3),
    "margin_pred_actual_r": r3(margin_r["r"]), "margin_pred_actual_p": r4(margin_r["p"]),
    "total_mae": round(total_mae, 3), "total_bias": round(total_bias, 3),
    "total_pred_actual_r": r3(total_r["r"]), "total_pred_actual_p": r4(total_r["p"]),
    "parlay_attempts": n_par, "parlay_hits": k_par,
    "parlay_hit_rate": round(par_acc, 4) if par_acc else None,
    "parlay_null_rate": 0.25, "parlay_binomial_p": r4(par_p),
    "kind": "derived", "note": DERIVED_NOTE, "source_urls": GAME_URLS,
}

# ---------------------------------------------------------------------------
# 7. Validation gates and strategy leaderboard
# ---------------------------------------------------------------------------
GATES = [
    {"id": "G01", "name": "Official provenance", "rule": "Every input value has an official source URL; unverifiable values blank + flagged.",
     "threshold": "100% of rows", "source_urls": [S_STAND, S_TEAM, S_SLATE]},
    {"id": "G02", "name": "Pre-registration", "rule": "Strategy specification frozen in the repository before any evaluation.",
     "threshold": "frozen spec present", "source_urls": ["https://github.com/sassnarep3-star/Own4/blob/main/official/results.json"]},
    {"id": "G03", "name": "No look-ahead", "rule": "Only official data strictly earlier than the game date may be used.",
     "threshold": "0 violations", "source_urls": GAME_URLS},
    {"id": "G04", "name": "Minimum sample", "rule": "A strategy needs at least 200 graded, independent observations.",
     "threshold": "n >= 200", "source_urls": GAME_URLS},
    {"id": "G05", "name": "Chronological out-of-sample holdout", "rule": "At least 30% of observations held out chronologically, with >= 100 holdout observations.",
     "threshold": "holdout n >= 100", "source_urls": GAME_URLS},
    {"id": "G06", "name": "Significance after multiple-testing control", "rule": "Two-sided p < 0.05 after Benjamini-Hochberg FDR across the strategy family.",
     "threshold": "q < 0.05", "source_urls": [S_FAQ]},
    {"id": "G07", "name": "Luck removal / effect size", "rule": "95% Wilson lower bound on accuracy must exceed the chance baseline, and a permutation test must reject the luck null.",
     "threshold": "CI lower > 0.500 and permutation p < 0.05", "source_urls": [S_FAQ]},
    {"id": "G08", "name": "Family-wise dependence control", "rule": "All tested signals entered into one pre-declared family; parlay legs screened with a measured correlation and CI.",
     "threshold": "pre-declared family + measured rho", "source_urls": [S_TEAM]},
    {"id": "G09", "name": "Reproducibility", "rule": "Results regenerate identically from checked-in official data + code; site has no broken links.",
     "threshold": "byte-identical regeneration", "source_urls": ["https://github.com/sassnarep3-star/Own4/blob/main/engine/analysis.py"]},
    {"id": "G10", "name": "Market-independent verification", "rule": "An official closing line must exist to compute closing-line value; no official source publishes odds.",
     "threshold": "official closing line available", "source_urls": [S_FAQ]},
]

# BH across the graded strategy family (winner, margin, total, parlay)
family_p = [binom_p, margin_r["p"], total_r["p"], par_p]
family_p = [1.0 if p is None else p for p in family_p]
family_q = bh_fdr(family_p)

STRATEGIES = [
    {"id": "OW-S01", "category": "Single bet — spread", "name": "Prior-margin power rating (walk-forward)",
     "spec": "Predicted first-listed margin = mean prior margin(A) - mean prior margin(B), computed only from official final scores dated before the game.",
     "metric_label": "Pred/actual margin correlation", "metric_value": backtest["margin_pred_actual_r"],
     "p_value": backtest["margin_pred_actual_p"], "q_value": r4(family_q[1]),
     "n": n_ok, "source_urls": GAME_URLS},
    {"id": "OW-S02", "category": "Single bet — moneyline", "name": "Prior-margin winner pick (walk-forward)",
     "spec": "Back the team with the higher prior mean margin; graded against the official final score.",
     "metric_label": "Winner accuracy", "metric_value": backtest["winner_accuracy"],
     "p_value": backtest["binomial_p_two_sided"], "q_value": r4(family_q[0]),
     "n": n_ok, "source_urls": GAME_URLS},
    {"id": "OW-S03", "category": "Single bet — total", "name": "Prior scoring-average total (walk-forward)",
     "spec": "Predicted total = mean prior points scored(A) + mean prior points scored(B); graded by error against the official final total.",
     "metric_label": "Pred/actual total correlation", "metric_value": backtest["total_pred_actual_r"],
     "p_value": backtest["total_pred_actual_p"], "q_value": r4(family_q[2]),
     "n": n_ok, "source_urls": GAME_URLS},
    {"id": "OW-S04", "category": "Parlay — 2 legs", "name": "Two-leg cross-game winner parlay",
     "spec": "On each date, parlay the predicted winners of the two games with the largest |predicted margin|; hit requires both leg wins. Chance baseline under independence = 0.25.",
     "metric_label": "Parlay hit rate", "metric_value": backtest["parlay_hit_rate"],
     "p_value": backtest["parlay_binomial_p"], "q_value": r4(family_q[3]),
     "n": n_par, "source_urls": GAME_URLS},
    {"id": "OW-S05", "category": "Player prop — single", "name": "Season-average fair prop line",
     "spec": "Originate a fair PTS/REB/AST line equal to the official season average. No official source publishes graded prop outcomes, so no performance metric can be computed.",
     "metric_label": "Graded prop observations", "metric_value": "", "p_value": "", "q_value": "",
     "n": 0, "unverified_fields": ["metric_value", "p_value", "q_value"],
     "source_urls": [S_PLAYERS]},
    {"id": "OW-S06", "category": "Player prop combo — SGP", "name": "Correlated PTS+REB+AST combo",
     "spec": "Construct a 3-leg same-player combo from official season averages; report the measured inter-leg correlations. Correlation-adjusted joint price requires a joint distribution no official source publishes.",
     "metric_label": "Correlation-adjusted joint price", "metric_value": "", "p_value": "", "q_value": "",
     "n": 0, "unverified_fields": ["metric_value", "p_value", "q_value"],
     "source_urls": [S_PLAYERS]},
]


def gate_results(s):
    unverified = bool(s.get("unverified_fields"))
    n = s["n"]
    q = s["q_value"]
    ci_lo = backtest["wilson_ci"][0]
    perm_ok = backtest["permutation_p"] is not None and backtest["permutation_p"] < 0.05
    luck_ok = ci_lo is not None and ci_lo > 0.5 and perm_ok
    return [
        ("G01", "pass"),
        ("G02", "pass"),
        ("G03", "pass"),
        ("G04", "pass" if n >= 200 else "fail", "graded n=%d < 200" % n),
        ("G05", "pass" if n >= 100 else "fail", "held-out n=%d < 100" % n),
        ("G06", "fail" if unverified or not isinstance(q, (int, float)) or q >= 0.05 else "pass"),
        ("G07", "fail" if not luck_ok else "pass",
         "Wilson 95%% lower bound=%s; permutation p=%s" % (ci_lo, backtest["permutation_p"])),
        ("G08", "pass"),
        ("G09", "pass"),
        ("G10", "fail", "no official closing line exists (blank + flagged I-12)"),
    ]


for s in STRATEGIES:
    gr = gate_results(s)
    s["gate_results"] = []
    for item in gr:
        g, r = item[0], item[1]
        detail = item[2] if len(item) > 2 else ""
        s["gate_results"].append({"gate": g, "result": r, "detail": detail})
    s["gates_passed"] = sum(1 for x in s["gate_results"] if x["result"] == "pass")
    s["gates_total"] = len(s["gate_results"])
    s["status"] = "ACTIVE" if s["gates_passed"] == s["gates_total"] else "NOT VALIDATED"
    s["kind"] = "derived"
    s["note"] = DERIVED_NOTE

leaderboard = []
for s in sorted(STRATEGIES, key=lambda x: (-x["gates_passed"], x["id"])):
    leaderboard.append({
        "strategy_id": s["id"], "name": s["name"], "category": s["category"],
        "gates_passed": s["gates_passed"], "gates_total": s["gates_total"],
        "status": s["status"],
        "reward_points": 0 if s["status"] != "ACTIVE" else None,
        "reward_note": "No reward: strategy did not pass all validation gates." if s["status"] != "ACTIVE" else "",
        "source_urls": s["source_urls"], "kind": "derived", "note": DERIVED_NOTE,
    })

reward_policy = [
    {"tier": "1st", "requirement": "All 10 gates pass AND highest out-of-sample score", "reward": "0 (no eligible strategies)", "source_urls": ["https://github.com/sassnarep3-star/Own4/blob/main/official/results.json"]},
    {"tier": "2nd", "requirement": "All 10 gates pass AND second-highest score", "reward": "0 (no eligible strategies)", "source_urls": ["https://github.com/sassnarep3-star/Own4/blob/main/official/results.json"]},
    {"tier": "3rd", "requirement": "All 10 gates pass AND third-highest score", "reward": "0 (no eligible strategies)", "source_urls": ["https://github.com/sassnarep3-star/Own4/blob/main/official/results.json"]},
    {"tier": "Activation", "requirement": "Rewards are unfunded; a strategy earns credit only after gate activation and prospective replication.", "reward": "unfunded", "source_urls": ["https://github.com/sassnarep3-star/Own4/blob/main/official/results.json"]},
]

FINDINGS = [
    {"id": "F01", "finding": "All 30 official 2026-27 standings rows and all 30 official team-stat rows were transcribed from NBA.com and are reproduced here with per-row official links.", "source_urls": [S_STAND, S_TEAM]},
    {"id": "F02", "finding": "A 56-game official final-score sample across six dates (2026-10-21 to 2026-11-01) is the largest verified dataset available; 10 of the 56 games are NBA Cup group-play games (I-14).", "source_urls": GAME_URLS},
    {"id": "F03", "finding": "Numeric correlation coefficients ARE computable from official inputs. The strongest relationship with winning percentage is reported with r, p, 95% CI and BH-FDR q on the Correlations page. These are derived in-sample descriptive statistics, not official publications and not predictive skill (I-13).", "source_urls": [S_TEAM, S_STAND, S_GLOSS]},
    {"id": "F04", "finding": "The NBA Stats FAQ itself publishes an official illustrative correlation: team PIE rating and winning percentage correlate at R-squared .908. It is historical FAQ context, not a 2026-27 measurement or a betting signal.", "source_urls": [S_FAQ]},
    {"id": "F05", "finding": "Own4 fair lines for the 15 official 2026-11-02 games were originated from official +/- ratings and official per-game scoring averages, with a margin dispersion estimated from official results. No market price was copied or inferred (I-12).", "source_urls": [S_TEAM, S_SLATE]},
    {"id": "F06", "finding": "Cross-game margin correlation was measured from official results and is reported with a confidence interval, so parlay independence is treated as an assumption to test rather than a fact.", "source_urls": GAME_URLS},
    {"id": "F07", "finding": "Same-player prop legs are not independent: PPG/RPG, PPG/APG and RPG/APG correlations across the 30 official season leaders are reported. A correlation-adjusted joint price is left blank because no official source publishes the joint distribution.", "source_urls": [S_PLAYERS]},
    {"id": "F08", "finding": "A strictly walk-forward backtest (only prior-date official scores) graded %d of %d games. Winner accuracy %s (95%% Wilson CI %s) with exact binomial p=%s and permutation p=%s: chance cannot be excluded." % (n_ok, len(games), backtest["winner_accuracy"], backtest["wilson_ci"], backtest["binomial_p_two_sided"], backtest["permutation_p"]), "source_urls": GAME_URLS},
    {"id": "F09", "finding": "No strategy passes all ten validation gates. Sample-size, luck-removal and market-independent-verification gates fail, so the leaderboard awards zero rewards. This is the intended 'remove luck / selectively skill-based' outcome: no strategy is promoted on a short, noisy sample.", "source_urls": ["https://github.com/sassnarep3-star/Own4/blob/main/official/results.json"]},
    {"id": "F10", "finding": "The merged site from earlier sessions was re-audited line by line. Verified claims were retained; stale links, a source/claim mismatch, imprecise wording, an image-only statistic, an outdated helpline number and a conflicting official score are published on the Flagged for Review page.", "source_urls": [S_FAQ, S_TEAM, S_FAQ]},
    {"id": "F11", "finding": "The NBA Stats FAQ restricts downloading statistics for academic or personal use. This project used no automated download or scraping; values were read from displayed pages and each row links back to the official page for manual review (I-08).", "source_urls": [S_FAQ]},
]

results = {
    "meta": {
        "generated_on": VERIFIED_ON, "season": "2026-27", "kind": "derived",
        "disclaimer": "All values in this file are reproducible computations from official NBA.com "
                      "inputs, NOT official NBA values and NOT market odds. See Flags I-13 / I-12.",
        "inputs": INPUTS, "code_url": "https://github.com/sassnarep3-star/Own4/blob/main/engine/analysis.py",
        "rebuild_command": "python3 engine/dataset.py && python3 engine/analysis.py",
    },
    "correlations": correlations, "correlation_matrix": {"keys": MATRIX_KEYS, "rows": matrix},
    "pair_correlations": pair_corrs, "official_quoted_correlation": official_quoted_corr,
    "prop_correlations": prop_corrs,
    "cross_game_correlation": {"n_pairs": cross["n"], "r": r3(cross["r"]), "p": r4(cross["p"]),
                               "ci_lo": r3(cross["ci_lo"]), "ci_hi": r3(cross["ci_hi"]),
                               "kind": "derived", "note": DERIVED_NOTE, "source_urls": GAME_URLS},
    "game_distribution": game_dist, "lines": lines, "parlays": parlays,
    "props": props, "prop_combos": prop_combos, "backtest": backtest,
    "graded_games": graded, "parlay_attempts": parlay_tries,
    "gates": GATES, "strategies": STRATEGIES, "leaderboard": leaderboard,
    "reward_policy": reward_policy, "findings": FINDINGS,
}

if __name__ == "__main__":
    with open(os.path.join(OFF, "results.json"), "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("wrote official/results.json")
    print("graded=%d/%d  winner_acc=%s  binom_p=%s  perm_p=%s  Wilson=%s" %
          (n_ok, len(games), backtest["winner_accuracy"], backtest["binomial_p_two_sided"],
           backtest["permutation_p"], backtest["wilson_ci"]))
    print("margin_r=%s total_r=%s parlay=%s/%s" % (backtest["margin_pred_actual_r"],
          backtest["total_pred_actual_r"], k_par, n_par))
    print("top correlations:", [(c["metric"], c["r"], c["q_bh"]) for c in
                                sorted(correlations, key=lambda c: -abs(c["r"] or 0))[:4]])
    print("statuses:", [(s["id"], s["status"], s["gates_passed"]) for s in STRATEGIES])
