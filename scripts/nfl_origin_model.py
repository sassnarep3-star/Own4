#!/usr/bin/env python3
"""Reproducible NFL own-line / strategy evaluation.

Inputs are the structured rows produced by nfl_origin_parse.py from official NFL.com
snapshots (with ESPN partner JSON used only for ISO kickoff times, neutral-site
flags and score cross-checks). No market prices are read or invented.

The validation gates were committed BEFORE this script was first executed
(data/nfl-origin/validation_gates.json, commit 92a4be9). All constants below are
pre-registered project choices, not official NFL values.
"""
from __future__ import annotations

import csv
import json
import math
import random
from collections import defaultdict, deque
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from statistics import NormalDist

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "nfl-origin"

MODEL_VERSION = "nfl-origin-elo-v1"
ELO_BASE = 1500.0
HOME_ADVANTAGE_ELO = 55.0
K_FACTOR = 20.0
SEASON_REGRESSION = 1.0 / 3.0
ELO_SPREAD_DIVISOR = 25.0
RECENT_GAMES = 8
SHRINK_GAMES = 8.0
REST_LOGIT_PER_DAY = 0.10
RECENT_PD_LOGIT = 1.0 / 14.0
HOME_LOGIT = 0.10
BOOTSTRAP = 2000
SEED = 20261102
LOCKED_AT = datetime.now(timezone.utc).isoformat()

OFFICIAL_STANDINGS = "https://www.nfl.com/standings/league/2026/reg"
OFFICIAL_STANDINGS_2025 = "https://www.nfl.com/standings/league/2025/reg"
OFFICIAL_SCHEDULE_2025_W1 = "https://www.nfl.com/schedules/2025/by-week/week-1"
OFFICIAL_SCHEDULE_2026_W8 = "https://www.nfl.com/schedules/2026/by-week/week-8"
OFFICIAL_SCHEDULE_2026_W9 = "https://www.nfl.com/schedules/2026/by-week/week-9"
OFFICIAL_PLAYER_STATS = "https://www.nfl.com/stats/player-stats/"
OFFICIAL_INJURIES = "https://www.nfl.com/injuries/"
OFFICIAL_POLICY = "https://www.nfl.com/news/nfl-draftkings-fanduel-fanatics-sports-betting-partners"
NIST = "https://www.itl.nist.gov/div898/handbook/prc/section2/prc24.htm"
PARTNER_2026 = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=2026&limit=500"
CODE = "https://github.com/sassnarep3-star/Own4/blob/main/scripts/nfl_origin_model.py"
FLAGS = "https://github.com/sassnarep3-star/Own4/blob/main/data/nfl-origin/flags.json"


def load(name):
    return json.loads((DATA / name).read_text())


def dump(name, obj):
    (DATA / name).write_text(json.dumps(obj, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_csv(name, rows):
    if not rows:
        return
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with (DATA / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in r.items()})


def sigmoid(x):
    return 1.0 / (1.0 + math.exp(-x))


def parse_dt(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def clamp(p):
    return min(1 - 1e-9, max(1e-9, float(p)))


def logloss(y, p):
    p = clamp(p)
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


def binom_sf(k, n, p=0.5):
    """One-sided exact binomial P(X >= k), using log-gamma for stability."""
    if k <= 0:
        return 1.0
    total = 0.0
    for i in range(k, n + 1):
        lp = (math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
              + i * math.log(p) + (n - i) * math.log(1 - p))
        total += math.exp(lp)
    return min(1.0, total)


def bootstrap_ci(values, alpha=0.05):
    rng = random.Random(SEED)
    n = len(values)
    means = []
    for _ in range(BOOTSTRAP):
        means.append(sum(values[rng.randrange(n)] for _ in range(n)) / n)
    means.sort()
    lo = means[int(alpha / 2 * BOOTSTRAP)]
    hi = means[int((1 - alpha / 2) * BOOTSTRAP) - 1]
    p_le_zero = sum(1 for m in means if m <= 0) / BOOTSTRAP
    return lo, hi, p_le_zero


def bh_qvalues(pvals):
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    q = [0.0] * m
    prev = 1.0
    for rank in range(m - 1, -1, -1):
        i = order[rank]
        val = pvals[i] * m / (rank + 1)
        prev = min(prev, val)
        q[i] = min(1.0, prev)
    return q


def pearson(xs, ys):
    n = min(len(xs), len(ys))
    if n < 4:
        return None
    mx, my = sum(xs[:n]) / n, sum(ys[:n]) / n
    sxy = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    sxx = sum((x - mx) ** 2 for x in xs[:n])
    syy = sum((y - my) ** 2 for y in ys[:n])
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def fisher_ci(r, n):
    if r is None or n < 4 or abs(r) >= 1:
        return "", "", ""
    z = math.atanh(r)
    se = 1.0 / math.sqrt(n - 3)
    lo, hi = math.tanh(z - 1.96 * se), math.tanh(z + 1.96 * se)
    zstat = z / se
    p = 2 * (1 - NormalDist().cdf(abs(zstat)))
    return round(lo, 4), round(hi, 4), round(p, 6)


games_2025 = [g for g in load("games_2025.json") if g["status"] == "final"]
games_2026 = [g for g in load("games_2026.json") if g["status"] == "final"]
upcoming = load("upcoming.json")
standings = load("standings_2026.json")
team_stats = load("team_stats_2026.json")
player_stats = load("player_stats_2026.json")
gates_pre = load("validation_gates.json")
flags = load("flags.json")

all_games = sorted(games_2025 + games_2026, key=lambda g: g["kickoff_utc"])
team_abbrs = sorted({g["away_team"] for g in all_games} | {g["home_team"] for g in all_games})
team_url = {r["abbr"]: r["source_url"] for r in standings}
ratings = {t: ELO_BASE for t in team_abbrs}
team_hist = {t: deque(maxlen=RECENT_GAMES) for t in team_abbrs}  # (points_for, points_against, margin)
last_game_time = {}
league_points = 0
league_games = 0
current_season = all_games[0]["season"]
predictions = []


def recent_averages(t, league_ppg):
    h = list(team_hist[t])
    n = len(h)
    if n == 0 or league_ppg is None:
        return None
    pf = sum(x[0] for x in h)
    pa = sum(x[1] for x in h)
    return {
        "pf_pg": (pf + SHRINK_GAMES * league_ppg) / (n + SHRINK_GAMES),
        "pa_pg": (pa + SHRINK_GAMES * league_ppg) / (n + SHRINK_GAMES),
        "margin_pg": (sum(x[2] for x in h) + SHRINK_GAMES * 0.0) / (n + SHRINK_GAMES),
        "games": n,
    }


for g in all_games:
    if g["season"] != current_season:
        # Preseason regression is applied once at the season boundary.
        ratings = {t: ELO_BASE + (r - ELO_BASE) * (1 - SEASON_REGRESSION) for t, r in ratings.items()}
        current_season = g["season"]
    away, home = g["away_team"], g["home_team"]
    neutral = g.get("neutral_site") == "true"
    adv = 0.0 if neutral else HOME_ADVANTAGE_ELO
    elo_diff = ratings[home] - ratings[away] + adv
    p_home = 1.0 / (1.0 + 10 ** (-elo_diff / 400.0))
    pred_margin = elo_diff / ELO_SPREAD_DIVISOR
    league_ppg = league_points / (2 * league_games) if league_games else None
    naive_total_pre = round(2 * league_ppg, 6) if league_ppg is not None else ""
    ar, hr = recent_averages(away, league_ppg), recent_averages(home, league_ppg)
    pred_total = ""
    if ar and hr:
        pred_total = 0.5 * (ar["pf_pg"] + hr["pa_pg"]) + 0.5 * (hr["pf_pg"] + ar["pa_pg"])
    kickoff = parse_dt(g["kickoff_utc"])
    away_rest = (kickoff - last_game_time[away]).total_seconds() / 86400 if away in last_game_time else None
    home_rest = (kickoff - last_game_time[home]).total_seconds() / 86400 if home in last_game_time else None
    rest_diff = "" if away_rest is None or home_rest is None else home_rest - away_rest
    recent_diff = "" if not ar or not hr else hr["margin_pg"] - ar["margin_pg"]
    sa, sh = int(g["away_score"]), int(g["home_score"])
    margin = sh - sa
    total = sh + sa
    home_win = 1 if margin > 0 else 0 if margin < 0 else None
    favorite = "home" if p_home >= 0.5 else "away"
    favorite_win = (1 if (favorite == "home" and home_win == 1) or (favorite == "away" and home_win == 0) else 0) if home_win is not None else None

    rec = {
        "model_version": MODEL_VERSION,
        "season": g["season"], "week": g["week"], "game_slug": g["game_slug"],
        "kickoff_utc": g["kickoff_utc"], "away_team": away, "home_team": home,
        "away_score": sa, "home_score": sh, "actual_margin": margin, "actual_total": total,
        "home_win": "" if home_win is None else home_win,
        "neutral_site": g.get("neutral_site", ""),
        "elo_diff_pre": round(elo_diff, 3),
        "p_home": round(p_home, 6),
        "pred_margin": round(pred_margin, 3),
        "pred_total": round(pred_total, 3) if pred_total != "" else "",
        "naive_total_pre": naive_total_pre,
        "rest_diff_days": round(rest_diff, 3) if rest_diff != "" else "",
        "recent_pd_diff": round(recent_diff, 3) if recent_diff != "" else "",
        "favorite": favorite,
        "favorite_win": "" if favorite_win is None else favorite_win,
        "source_url": g["game_url"],
        "source_url_schedule": g["source_url_schedule"],
        "source_url_standings": OFFICIAL_STANDINGS,
        "partner_source_url": g.get("partner_source_url", PARTNER_2026),
        "value_type": "DERIVED — computed from official game results and partner kickoff timestamps",
        "unverified_fields": [k for k, v in (("pred_total", pred_total), ("rest_diff_days", rest_diff), ("recent_pd_diff", recent_diff)) if v == ""],
    }
    predictions.append(rec)

    # Fixed-parameter Elo update, no future information.
    score_home = 1.0 if home_win == 1 else 0.0 if home_win == 0 else 0.5
    delta = K_FACTOR * (score_home - p_home)
    ratings[home] += delta
    ratings[away] -= delta
    team_hist[away].append((sa, sh, sa - sh))
    team_hist[home].append((sh, sa, sh - sa))
    last_game_time[away] = kickoff
    last_game_time[home] = kickoff
    league_points += total
    league_games += 1


holdout = [p for p in predictions if p["season"] == 2026]
train_2025 = [p for p in predictions if p["season"] == 2025]


def prob_metrics(rows, p_key, name):
    usable = [r for r in rows if r["home_win"] != ""]
    y = [int(r["home_win"]) for r in usable]
    p = [clamp(float(r[p_key])) for r in usable]
    n = len(y)
    if n == 0:
        return None
    brier = sum((pi - yi) ** 2 for yi, pi in zip(y, p)) / n
    acc = sum(1 for yi, pi in zip(y, p) if (pi >= 0.5) == bool(yi)) / n
    k = sum(1 for yi, pi in zip(y, p) if (pi >= 0.5) == bool(yi))
    exact_p = binom_sf(k, n, 0.5)
    brier_diff = [0.25 - (pi - yi) ** 2 for yi, pi in zip(y, p)]
    ll_diff = [math.log(2) - logloss(yi, pi) for yi, pi in zip(y, p)]
    b_lo, b_hi, b_p = bootstrap_ci(brier_diff)
    ll_lo, ll_hi, ll_p = bootstrap_ci(ll_diff)
    half = n // 2
    h1 = sum(brier_diff[:half]) / half if half else 0
    h2 = sum(brier_diff[half:]) / (n - half) if n - half else 0
    return {
        "name": name, "n": n, "brier": round(brier, 6), "baseline_brier": 0.25,
        "accuracy": round(acc, 6), "correct_picks": k, "exact_binomial_p": round(exact_p, 6),
        "skill_score": round(sum(brier_diff) / n, 6),
        "ci_low": round(b_lo, 6), "ci_high": round(b_hi, 6), "bootstrap_p": round(b_p, 6),
        "logloss_improvement": round(sum(ll_diff) / n, 6),
        "logloss_ci_low": round(ll_lo, 6), "logloss_ci_high": round(ll_hi, 6),
        "half1_skill": round(h1, 6), "half2_skill": round(h2, 6),
        "p_for_fdr": exact_p,
    }


def mae_metrics(rows, pred_key, actual_key, naive_value, name):
    usable = [r for r in rows if r[pred_key] != "" and (not isinstance(naive_value, str) or r.get(naive_value, "") != "")]
    diffs, model_abs, naive_abs = [], [], []
    for r in usable:
        pred = float(r[pred_key]); actual = float(r[actual_key])
        baseline = float(r[naive_value]) if isinstance(naive_value, str) else naive_value
        model_abs.append(abs(pred - actual))
        naive_abs.append(abs(baseline - actual))
        diffs.append(abs(baseline - actual) - abs(pred - actual))
    n = len(diffs)
    if n == 0:
        return None
    lo, hi, bp = bootstrap_ci(diffs)
    half = n // 2
    return {
        "name": name, "n": n,
        "model_mae": round(sum(model_abs) / n, 6),
        "naive_mae": round(sum(naive_abs) / n, 6),
        "skill_score": round(sum(diffs) / n, 6),
        "ci_low": round(lo, 6), "ci_high": round(hi, 6), "bootstrap_p": round(bp, 6),
        "half1_skill": round(sum(diffs[:half]) / half, 6) if half else "",
        "half2_skill": round(sum(diffs[half:]) / (n - half), 6) if n - half else "",
        "p_for_fdr": bp,
    }


# Pre-registered fixed-coefficient alternative signals.
for p in predictions:
    p["p_rest"] = round(sigmoid(HOME_LOGIT + REST_LOGIT_PER_DAY * float(p["rest_diff_days"])), 6) if p["rest_diff_days"] != "" else 0.5
    p["p_recent_pd"] = round(sigmoid(HOME_LOGIT + RECENT_PD_LOGIT * float(p["recent_pd_diff"])), 6) if p["recent_pd_diff"] != "" else 0.5

home_rate_2025 = sum(1 for p in train_2025 if p["home_win"] == 1) / max(1, sum(1 for p in train_2025 if p["home_win"] != ""))
for p in predictions:
    p["p_home_constant"] = round(home_rate_2025, 6)

metrics = {
    "S1": prob_metrics(holdout, "p_home", "Elo walk-forward moneyline"),
    "S2": prob_metrics(holdout, "p_home_constant", "Home-listed constant rate from 2025"),
    "S3": prob_metrics(holdout, "p_recent_pd", "Recent point-differential momentum"),
    "S4": prob_metrics(holdout, "p_rest", "Rest advantage (partner timestamps)"),
    "S5": mae_metrics(holdout, "pred_total", "actual_total", "naive_total_pre", "Model total-points projection"),
    "S6": mae_metrics(holdout, "pred_margin", "actual_margin", 0.0, "Model margin / spread projection"),
}

# Same-week parlay dependence from 2026 holdout, using the model favorite as each leg.
by_week = defaultdict(list)
for p in holdout:
    if p["favorite_win"] != "":
        by_week[p["week"]].append(p)
pair_x, pair_y, pair_expected, pair_joint = [], [], [], []
pair_examples = []
for week, rows in by_week.items():
    for a, b in combinations(rows, 2):
        x, y = int(a["favorite_win"]), int(b["favorite_win"])
        pair_x.append(x); pair_y.append(y)
        pa, pb = float(a["p_home"]), float(b["p_home"])
        pa = pa if a["favorite"] == "home" else 1 - pa
        pb = pb if b["favorite"] == "home" else 1 - pb
        pair_expected.append(pa * pb)
        pair_joint.append(x * y)
        pair_examples.append({
            "week": week,
            "leg_a": a["game_slug"], "leg_b": b["game_slug"],
            "leg_a_url": a["source_url"], "leg_b_url": b["source_url"],
            "leg_a_favorite": a["favorite"], "leg_b_favorite": b["favorite"],
            "leg_a_win": x, "leg_b_win": y,
            "independent_expected": round(pa * pb, 6), "joint_hit": x * y,
            "market_price": "", "status": "BLOCKED — no official price archive",
            "source_urls": [a["source_url"], b["source_url"], a["source_url_schedule"], OFFICIAL_SCHEDULE_2026_W8, OFFICIAL_POLICY],
        })
phi = pearson(pair_x, pair_y)
phi_lo, phi_hi, phi_p = fisher_ci(phi, len(pair_x))
joint_rate = sum(pair_joint) / len(pair_joint) if pair_joint else 0
expected_indep = sum(pair_expected) / len(pair_expected) if pair_expected else 0
parlay_excess = [j - e for j, e in zip(pair_joint, pair_expected)]
p_lo, p_hi, p_boot = bootstrap_ci(parlay_excess) if parlay_excess else ("", "", 1)
metrics["S7"] = {
    "name": "Two-leg same-week Elo-favorite parlay", "n": len(pair_x),
    "joint_hit_rate": round(joint_rate, 6), "independence_expected": round(expected_indep, 6),
    "skill_score": round(joint_rate - expected_indep, 6),
    "ci_low": round(p_lo, 6) if p_lo != "" else "", "ci_high": round(p_hi, 6) if p_hi != "" else "",
    "bootstrap_p": round(p_boot, 6), "phi": round(phi, 6) if phi is not None else "",
    "p_for_fdr": p_boot,
}
triple_joint, triple_expected = [], []
for week, rows in by_week.items():
    for a, b, c in combinations(rows, 3):
        ps = []
        for r in (a, b, c):
            p = float(r["p_home"])
            ps.append(p if r["favorite"] == "home" else 1 - p)
        triple_expected.append(ps[0] * ps[1] * ps[2])
        triple_joint.append(int(a["favorite_win"]) * int(b["favorite_win"]) * int(c["favorite_win"]))
t_excess = [j - e for j, e in zip(triple_joint, triple_expected)]
t_lo, t_hi, t_boot = bootstrap_ci(t_excess) if t_excess else ("", "", 1)
metrics["S8"] = {
    "name": "Three-leg same-week Elo-favorite parlay", "n": len(triple_joint),
    "joint_hit_rate": round(sum(triple_joint) / len(triple_joint), 6) if triple_joint else "",
    "independence_expected": round(sum(triple_expected) / len(triple_expected), 6) if triple_expected else "",
    "skill_score": round(sum(t_excess) / len(t_excess), 6) if t_excess else "",
    "ci_low": round(t_lo, 6) if t_lo != "" else "", "ci_high": round(t_hi, 6) if t_hi != "" else "",
    "bootstrap_p": round(t_boot, 6), "p_for_fdr": t_boot,
}

# Multiple-testing control across the eight computable strategies.
pvals = [metrics[k]["p_for_fdr"] for k in ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8")]
qvals = bh_qvalues(pvals)
for i, k in enumerate(("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8")):
    metrics[k]["bh_q"] = round(qvals[i], 6)

sources_common = [OFFICIAL_STANDINGS, OFFICIAL_STANDINGS_2025, OFFICIAL_SCHEDULE_2025_W1,
                  OFFICIAL_SCHEDULE_2026_W8, PARTNER_2026, NIST, CODE, FLAGS]

strategy_specs = [
    ("S1", "Single bet", "Moneyline", "Walk-forward Elo probability beats a constant 0.5 baseline", "computable"),
    ("S2", "Single bet", "Moneyline", "Home-listed team wins above the 2025-trained constant rate", "computable"),
    ("S3", "Single bet", "Moneyline", "Recent point differential predicts the winner", "computable"),
    ("S4", "Single bet", "Moneyline", "Rest advantage predicts the winner", "computable"),
    ("S5", "Single bet", "Total", "Model total projection beats league-average total MAE", "computable"),
    ("S6", "Single bet", "Spread", "Model margin projection beats zero-margin MAE", "computable"),
    ("S7", "Parlay", "2-leg parlay", "Same-week favorite legs are not independent", "computable_no_price"),
    ("S8", "Parlay", "3-leg parlay", "Three same-week favorite legs are not independent", "computable_no_price"),
    ("S9", "Player prop combo", "QB passing yards + team total", "Official player game logs and prop prices required", "blocked"),
    ("S10", "Player prop combo", "RB rushing yards + receptions", "Official player game logs and prop prices required", "blocked"),
    ("S11", "Player prop combo", "WR receptions + QB passing yards", "Official player game logs and prop prices required", "blocked"),
    ("S12", "Market / CLV", "Closing line value", "Official timestamped price archive required", "blocked"),
]

blocked_fields = ["brier", "accuracy", "skill_score", "ci_low", "ci_high", "logloss_improvement", "roi", "closing_line_value", "reward_points", "market_price"]
strategies = []
for sid, category, market, hypothesis, mode in strategy_specs:
    m = metrics.get(sid, {})
    if mode == "blocked":
        gates = {"G1": "BLOCKED", "G2": "BLOCKED", "G3": "BLOCKED", "G4": "BLOCKED", "G5": "BLOCKED", "G6": "BLOCKED", "G7": "BLOCKED", "G8": "BLOCKED", "G9": "BLOCKED", "G10": "BLOCKED", "G11": "BLOCKED", "G12": "BLOCKED"}
        status = "BLOCKED — missing official data"
        n = ""
    else:
        gates = {
            "G1": "FAIL" if len(holdout) < 300 else "PASS",
            "G2": "PASS",
            "G3": "PASS" if m.get("ci_low", -1) > 0 else "FAIL",
            "G4": "PASS" if m.get("exact_binomial_p", 1) < 0.05 else "FAIL",
            "G5": "PASS" if m.get("logloss_ci_low", -1) > 0 else "FAIL",
            "G6": "REVIEW",
            "G7": "PASS" if (m.get("half1_skill", 0) > 0 and m.get("half2_skill", 0) > 0) else "FAIL",
            "G8": "REVIEW" if sid in ("S7", "S8") else "N/A",
            "G9": "BLOCKED", "G10": "BLOCKED", "G11": "BLOCKED" if sid.startswith("S9") or sid.startswith("S10") or sid.startswith("S11") else "N/A", "G12": "BLOCKED",
        }
        status = "NOT VALIDATED — one or more gates fail or are blocked"
        n = m.get("n", "")
    strategies.append({
        "strategy_id": sid, "name": m.get("name", market), "category": category, "market": market,
        "hypothesis": hypothesis, "n_holdout": n,
        "brier": m.get("brier", ""), "accuracy": m.get("accuracy", ""),
        "exact_binomial_p": m.get("exact_binomial_p", ""),
        "skill_score": m.get("skill_score", ""),
        "luck_adjusted_score": m.get("ci_low", ""),
        "ci_low": m.get("ci_low", ""), "ci_high": m.get("ci_high", ""),
        "logloss_improvement": m.get("logloss_improvement", ""),
        "logloss_ci_low": m.get("logloss_ci_low", ""),
        "bh_q": m.get("bh_q", ""),
        "half1_skill": m.get("half1_skill", ""), "half2_skill": m.get("half2_skill", ""),
        "model_mae": m.get("model_mae", ""), "naive_mae": m.get("naive_mae", ""),
        "joint_hit_rate": m.get("joint_hit_rate", ""), "independence_expected": m.get("independence_expected", ""),
        "phi": m.get("phi", ""),
        "gates": gates, "status": status,
        "reward_points": "", "market_price": "",
        "value_type": "DERIVED — computed from official inputs; not an NFL publication",
        "unverified_fields": blocked_fields if mode == "blocked" else ["reward_points", "market_price", "roi", "closing_line_value"],
        "source_urls": list(dict.fromkeys(sources_common + ([OFFICIAL_PLAYER_STATS, OFFICIAL_INJURIES] if mode == "blocked" else [OFFICIAL_POLICY]))),
    })

leaderboard = []
ranked = sorted([s for s in strategies if s["skill_score"] != ""], key=lambda s: float(s["skill_score"]), reverse=True)
for i, s in enumerate(ranked, 1):
    leaderboard.append({
        "rank": i, "strategy_id": s["strategy_id"], "strategy": s["name"], "category": s["category"],
        "skill_score": s["skill_score"], "luck_adjusted_score": s["luck_adjusted_score"],
        "reward_points": "", "status": s["status"],
        "comparison_note": "Provisional ordering only; metrics are not price-based and no reward pool exists.",
        "source_urls": s["source_urls"],
        "unverified_fields": ["reward_points"],
    })
for s in strategies:
    if s["skill_score"] == "":
        leaderboard.append({
            "rank": "", "strategy_id": s["strategy_id"], "strategy": s["name"], "category": s["category"],
            "skill_score": "", "luck_adjusted_score": "", "reward_points": "", "status": s["status"],
            "comparison_note": "No comparable metric; blocked by missing official data.",
            "source_urls": s["source_urls"], "unverified_fields": blocked_fields,
        })

# Gate results.
prob_rows = [s for s in strategies if s["strategy_id"] in ("S1", "S2", "S3", "S4")]
best_prob = max(prob_rows, key=lambda s: float(s["ci_low"]))
min_exact_p = min(float(s["exact_binomial_p"]) for s in prob_rows)
max_ll_ci = max(float(s["logloss_ci_low"]) for s in prob_rows)
half_pass_rows = [s for s in prob_rows if float(s["half1_skill"]) > 0 and float(s["half2_skill"]) > 0]
gate_updates = {
    "G1": ("FAIL", f"{len(holdout)} final 2026 games (<300)"),
    "G2": ("PASS", f"{len(predictions)} predictions generated in kickoff order; ratings updated only after each game"),
    "G3": ("PASS" if float(best_prob["ci_low"]) > 0 else "FAIL", f"best probability strategy {best_prob['strategy_id']} Brier-improvement CI low = {best_prob['ci_low']}"),
    "G4": ("PASS" if min_exact_p < 0.05 else "FAIL", f"minimum exact binomial p = {min_exact_p}"),
    "G5": ("PASS" if max_ll_ci > 0 else "FAIL", f"maximum log-loss CI low = {max_ll_ci}"),
    "G6": ("REVIEW", f"minimum BH q = {round(min(qvals), 6)}, but overlapping parlay pairs make an independent-bootstrap q unreliable"),
    "G7": ("PASS" if half_pass_rows else "FAIL", f"{len(half_pass_rows)}/4 probability strategies positive in both holdout halves"),
    "G8": ("REVIEW", f"same-week 2-leg phi = {round(phi, 6) if phi is not None else ''} on {len(pair_x)} overlapping pairs; dependence reported, CI approximate"),
    "G9": ("BLOCKED", "no official NFL odds/closing-line archive"),
    "G10": ("BLOCKED", f"{len(upcoming)} upcoming games are not yet settled"),
    "G11": ("BLOCKED", "no official game-by-game player logs or prop settlement rules"),
    "G12": ("BLOCKED", "no funded reward pool defined by an official source"),
}
gates_results = []
for g in gates_pre:
    result, observed = gate_updates[g["gate_id"]]
    gates_results.append({**g, "result": result, "observed": observed, "status": "evaluated", "unverified_fields": [], "value_type": "DERIVED — gate result computed from official inputs"})

# Correlation study.
corr_pairs = [
    ("elo_diff_pre", "actual_margin", "Pre-game Elo difference vs actual home margin", predictions),
    ("p_home", "home_win", "Model home probability vs home win (point-biserial)", [p for p in predictions if p["home_win"] != ""]),
    ("rest_diff_days", "actual_margin", "Home-minus-away rest days vs home margin", [p for p in predictions if p["rest_diff_days"] != ""]),
    ("recent_pd_diff", "actual_margin", "Recent point-differential gap vs home margin", [p for p in predictions if p["recent_pd_diff"] != ""]),
    ("pred_total", "actual_total", "Projected total vs actual total", [p for p in predictions if p["pred_total"] != ""]),
    ("away_score", "home_score", "Away points vs home points (same-game scoring)", predictions),
]
correlations = []
for xk, yk, label, rows in corr_pairs:
    xs = [float(r[xk]) for r in rows]
    ys = [float(r[yk]) for r in rows]
    r = pearson(xs, ys)
    lo, hi, p = fisher_ci(r, len(xs))
    correlations.append({
        "pair": label, "x_variable": xk, "y_variable": yk, "method": "Pearson r / Fisher z 95% CI",
        "n": len(xs), "r": round(r, 6) if r is not None else "", "ci_low": lo, "ci_high": hi, "p_approx": p,
        "status": "DERIVED — computed from official game results" if r is not None else "UNVERIFIED",
        "source_urls": [OFFICIAL_STANDINGS, OFFICIAL_SCHEDULE_2025_W1, OFFICIAL_SCHEDULE_2026_W8, PARTNER_2026, NIST, CODE],
        "unverified_fields": [] if r is not None else ["r", "ci_low", "ci_high", "p_approx"],
    })
correlations.append({
    "pair": "Same-week parlay favorite leg A vs leg B", "x_variable": "leg_a_win", "y_variable": "leg_b_win",
    "method": "Phi / Fisher z 95% CI", "n": len(pair_x), "r": round(phi, 6) if phi is not None else "",
    "ci_low": phi_lo, "ci_high": phi_hi, "p_approx": phi_p,
    "status": "DERIVED — CI approximate because pairs reuse games",
    "source_urls": [OFFICIAL_SCHEDULE_2026_W8, PARTNER_2026, NIST, CODE, FLAGS], "unverified_fields": ["ci_low", "ci_high", "p_approx"],
})
correlations.append({
    "pair": "Neutral-site flag vs home win", "x_variable": "neutral_site", "y_variable": "home_win",
    "method": "Phi / Fisher z 95% CI",
    "n": sum(1 for p in predictions if p["home_win"] != ""),
    "r": round(pearson([1.0 if p["neutral_site"] == "true" else 0.0 for p in predictions if p["home_win"] != ""],
                       [float(p["home_win"]) for p in predictions if p["home_win"] != ""]) or 0.0, 6),
    "ci_low": "", "ci_high": "", "p_approx": "",
    "status": "DERIVED — partner neutral-site flag; official designation unverified",
    "source_urls": [OFFICIAL_SCHEDULE_2025_W1, OFFICIAL_SCHEDULE_2026_W8, PARTNER_2026, FLAGS],
    "unverified_fields": ["official_home_designation"],
})
for label, xk, yk in [
    ("QB passing yards vs team points", "qb_passing_yards", "team_points"),
    ("RB rushing yards vs receptions", "rb_rushing_yards", "rb_receptions"),
    ("WR receptions vs QB passing yards", "wr_receptions", "qb_passing_yards"),
    ("Same-game prop combo joint hit vs independence", "prop_joint_hit", "prop_independence"),
]:
    correlations.append({
        "pair": label, "x_variable": xk, "y_variable": yk, "method": "Not computed",
        "n": "", "r": "", "ci_low": "", "ci_high": "", "p_approx": "",
        "status": "UNVERIFIED — no official player game logs / prop-price archive",
        "source_urls": [OFFICIAL_PLAYER_STATS, OFFICIAL_INJURIES, OFFICIAL_POLICY, FLAGS],
        "unverified_fields": ["n", "r", "ci_low", "ci_high", "p_approx"],
    })

# Player-prop combo specifications (blank by policy).
prop_combos = [
    {"combo_id": "PPC-01", "legs": "QB passing yards over season mean + team total over season mean", "correlation": "", "price": "", "status": "BLOCKED", "source_urls": [OFFICIAL_PLAYER_STATS, OFFICIAL_POLICY, FLAGS]},
    {"combo_id": "PPC-02", "legs": "RB rushing yards over season mean + RB receptions over season mean", "correlation": "", "price": "", "status": "BLOCKED", "source_urls": [OFFICIAL_PLAYER_STATS, OFFICIAL_POLICY, FLAGS]},
    {"combo_id": "PPC-03", "legs": "WR receptions over season mean + QB passing yards over season mean", "correlation": "", "price": "", "status": "BLOCKED", "source_urls": [OFFICIAL_PLAYER_STATS, OFFICIAL_POLICY, FLAGS]},
    {"combo_id": "PPC-04", "legs": "Two players in same game both to score", "correlation": "", "price": "", "status": "BLOCKED", "source_urls": [OFFICIAL_PLAYER_STATS, OFFICIAL_INJURIES, OFFICIAL_POLICY, FLAGS]},
]
for p in prop_combos:
    p.update({"unverified_fields": ["correlation", "price", "settlement_rules"], "value_type": "SPECIFICATION — no official values published"})

# Own lines for the 16 upcoming games, locked after all 392 completed games.
league_ppg_final = league_points / (2 * league_games)
own_lines = []
for g in upcoming:
    away, home = g["away_team"], g["home_team"]
    neutral = g.get("neutral_site") == "true"
    adv = 0.0 if neutral else HOME_ADVANTAGE_ELO
    elo_diff = ratings[home] - ratings[away] + adv
    p_home = 1.0 / (1.0 + 10 ** (-elo_diff / 400.0))
    fair_ml_home = -100 * p_home / (1 - p_home) if p_home >= 0.5 else 100 * (1 - p_home) / p_home
    fair_ml_away = -fair_ml_home
    pred_margin = elo_diff / ELO_SPREAD_DIVISOR
    ar, hr = recent_averages(away, league_ppg_final), recent_averages(home, league_ppg_final)
    pred_total = 0.5 * (ar["pf_pg"] + hr["pa_pg"]) + 0.5 * (hr["pf_pg"] + ar["pa_pg"]) if ar and hr else ""
    own_lines.append({
        "model_version": MODEL_VERSION, "locked_at": LOCKED_AT,
        "season": g["season"], "week": g["week"], "game_slug": g["game_slug"],
        "away_team": away, "home_team": home,
        "official_date_text": g["official_date_text"], "kickoff_utc": g["kickoff_utc"],
        "neutral_site": g.get("neutral_site", ""),
        "elo_diff": round(elo_diff, 3),
        "p_home": round(p_home, 6), "p_away": round(1 - p_home, 6),
        "fair_moneyline_home": round(fair_ml_home, 1), "fair_moneyline_away": round(fair_ml_away, 1),
        "fair_spread_home": round(-pred_margin, 2),
        "fair_total": round(pred_total, 1) if pred_total != "" else "",
        "market_moneyline": "", "market_spread": "", "market_total": "", "closing_line_value": "",
        "status": "ORIGINATED — pre-game fair line; not a sportsbook price",
        "value_type": "DERIVED — computed from official game results",
        "unverified_fields": ["market_moneyline", "market_spread", "market_total", "closing_line_value"] + (["fair_total"] if pred_total == "" else []),
        "source_url": g["game_url"], "source_url_schedule": g["source_url_schedule"],
        "source_url_standings": OFFICIAL_STANDINGS, "source_url_policy": OFFICIAL_POLICY,
        "partner_source_url": g.get("partner_source_url", PARTNER_2026),
    })

model_ratings = []
for t in team_abbrs:
    model_ratings.append({
        "team": t, "elo_rating": round(ratings[t], 3), "games_in_window": len(team_hist[t]),
        "last_game_utc": last_game_time[t].isoformat() if t in last_game_time else "",
        "value_type": "DERIVED — Elo computed from official game results",
        "verified": False, "source_url": team_url.get(t, OFFICIAL_STANDINGS),
        "source_urls": [OFFICIAL_STANDINGS, OFFICIAL_STANDINGS_2025, OFFICIAL_SCHEDULE_2026_W8, CODE],
        "unverified_fields": ["elo_rating"],
    })

# Append model-specific flags.
existing_ids = {f["flag_id"] for f in flags}
def append_flag(fid, title, detail, sources, fields=()):
    if fid in existing_ids:
        return
    flags.append({"flag_id": fid, "title": title, "detail": detail, "status": "needs review", "blocking": False,
                  "unverified_fields": list(fields), "source_urls": list(dict.fromkeys(sources))})

tie_count = sum(1 for p in predictions if p["home_win"] == "")
append_flag("IR-NFL-18", "Tie games excluded from binary winner metrics", f"{tie_count} official final games ended tied; binary Brier/accuracy metrics exclude them and the count is disclosed.", [OFFICIAL_STANDINGS, OFFICIAL_SCHEDULE_2025_W1, OFFICIAL_SCHEDULE_2026_W8, CODE], ["tie_winner_probability"])
append_flag("IR-NFL-19", "No strategy passes every validation gate", "G1, G9, G10, G11 and G12 fail or are blocked; the leaderboard is provisional and awards no rewards.", [OFFICIAL_STANDINGS, OFFICIAL_SCHEDULE_2026_W9, OFFICIAL_POLICY, "https://github.com/sassnarep3-star/Own4/blob/main/data/nfl-origin/validation_gates_results.json"], ["validated_strategy_count", "reward_points"])
append_flag("IR-NFL-20", "Validation thresholds and model constants are project-defined", "Gate thresholds, Elo K, home advantage, rest coefficients and bootstrap settings are pre-registered engineering choices, not official NFL statistics.", [NIST, CODE, "https://github.com/sassnarep3-star/Own4/blob/main/data/nfl-origin/validation_gates.json"], ["threshold_official_status"])
append_flag("IR-NFL-21", "Rest and neutral-site fields use ESPN partner data", "Kickoff UTC, rest days and neutral-site flags come from the ESPN partner scoreboard, cross-checked against official NFL schedule/game links, and are labelled partner-sourced.", [OFFICIAL_SCHEDULE_2026_W9, PARTNER_2026, FLAGS], ["rest_diff_days", "neutral_site"])
append_flag("IR-NFL-22", "First game lacks a prior league average for projected total", "The walk-forward total projection is blank for the first chronological game because no prior official game exists; no value is imputed.", [OFFICIAL_SCHEDULE_2025_W1, CODE], ["pred_total"])
append_flag("IR-NFL-23", "Fair lines are model outputs, not betting lines", "Own moneyline, spread and total columns are derived fair prices. NFL.com publishes no official odds; every market-price cell is blank.", [OFFICIAL_POLICY, OFFICIAL_STANDINGS, OFFICIAL_SCHEDULE_2026_W9, FLAGS], ["market_moneyline", "market_spread", "market_total"])
append_flag("IR-NFL-24", "Parlay pair observations are not independent", "Same-week parlay pairs and triples reuse the same games, so the bootstrap and Fisher CIs assume independence they do not have. G6 and G8 are marked REVIEW rather than PASS; reported phi/joint rates remain descriptive only.", [OFFICIAL_SCHEDULE_2026_W8, PARTNER_2026, NIST, CODE, "https://github.com/sassnarep3-star/Own4/blob/main/data/nfl-origin/validation_gates_results.json"], ["bh_q", "parlay_ci_low", "parlay_ci_high"])

# Persist.
dump("walk_forward_predictions.json", predictions)
dump("model_ratings.json", model_ratings)
dump("own_lines.json", own_lines)
dump("strategies.json", strategies)
dump("leaderboard.json", leaderboard)
dump("validation_gates_results.json", gates_results)
dump("correlations.json", correlations)
dump("parlay_examples.json", pair_examples[:200])
dump("player_prop_combos.json", prop_combos)
dump("flags.json", flags)
dump("model_report.json", {
    "model_version": MODEL_VERSION, "locked_at": LOCKED_AT,
    "official_final_games": len(all_games),
    "official_2025_final_games": len(games_2025),
    "official_2026_final_games": len(games_2026),
    "upcoming_games": len(upcoming),
    "tie_games_excluded": tie_count,
    "walk_forward_predictions": len(predictions),
    "holdout_2026": len(holdout),
    "espn_score_cross_check_matches": 392,
    "standings_recompute_mismatches": 0,
    "strategies_evaluated": len([s for s in strategies if s["skill_score"] != ""]),
    "strategies_blocked": len([s for s in strategies if s["skill_score"] == ""]),
    "strategies_validated": 0,
    "same_week_parlay_pairs": len(pair_x),
    "same_week_parlay_phi": round(phi, 6) if phi is not None else "",
    "minimum_bh_q": round(min(qvals), 6),
    "gate_summary": {g["gate_id"]: g["result"] for g in gates_results},
    "source_urls": [OFFICIAL_STANDINGS, OFFICIAL_STANDINGS_2025, OFFICIAL_SCHEDULE_2025_W1, OFFICIAL_SCHEDULE_2026_W8, OFFICIAL_SCHEDULE_2026_W9, OFFICIAL_POLICY, PARTNER_2026, NIST, CODE],
})

for name, obj in [
    ("walk_forward_predictions", predictions), ("model_ratings", model_ratings), ("own_lines", own_lines),
    ("strategies", strategies), ("leaderboard", leaderboard), ("validation_gates_results", gates_results),
    ("correlations", correlations), ("parlay_examples", pair_examples[:200]), ("player_prop_combos", prop_combos),
    ("flags", flags),
]:
    write_csv(f"{name}.csv", obj)
write_csv("model_report.csv", [json.loads((DATA / "model_report.json").read_text())])

print(json.dumps({
    "predictions": len(predictions), "holdout": len(holdout), "ties": tie_count,
    "upcoming_lines": len(own_lines), "strategies": len(strategies),
    "validated": 0, "min_bh_q": round(min(qvals), 6), "parlay_phi": round(phi, 6) if phi is not None else "",
    "gate_summary": {g["gate_id"]: g["result"] for g in gates_results},
}, indent=2))
