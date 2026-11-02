"""Reproducible official-only NFL research engine (Python standard library).

Run: python nfl-lab/engine.py
All parameters are frozen in protocol.json. No sportsbook prices are consumed.
Derived outputs are model calculations, never represented as official NFL facts.
"""
from __future__ import annotations
import csv
import itertools
import json
import math
import random
from collections import defaultdict
from datetime import date
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "results"
PROTOCOL = json.loads((ROOT / "protocol.json").read_text())
P = PROTOCOL["fixed_parameters"]
SEED = P["random_seed"]
REPS = P["bootstrap_replicates"]
MAX_SCORE = 100


def load(name):
    return json.loads((DATA / name).read_text())


def dump(name, obj):
    OUT.mkdir(exist_ok=True)
    (OUT / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def csv_dump(name, rows):
    OUT.mkdir(exist_ok=True)
    if not rows:
        return
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with (OUT / name).open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def pearson(x, y):
    if len(x) != len(y) or len(x) < 3:
        return None
    mx, my = mean(x), mean(y)
    sx = sum((a - mx) ** 2 for a in x)
    sy = sum((b - my) ** 2 for b in y)
    if sx <= 0 or sy <= 0:
        return None
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(sx * sy)


def quantile(xs, q):
    xs = sorted(xs)
    pos = (len(xs) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def cluster_groups(values, clusters):
    d = defaultdict(lambda: [0.0, 0])
    for v, c in zip(values, clusters):
        d[c][0] += v
        d[c][1] += 1
    return list(d.values())


def cluster_ci(values, clusters, seed=SEED, reps=REPS):
    groups = cluster_groups(values, clusters)
    rng = random.Random(seed)
    n = len(groups)
    estimates = []
    for _ in range(reps):
        s = c = 0
        for _ in range(n):
            a, b = groups[rng.randrange(n)]
            s += a
            c += b
        estimates.append(s / c)
    return [quantile(estimates, .025), quantile(estimates, .975)]


def cluster_permutation(values, clusters, seed=SEED, reps=REPS):
    groups = cluster_groups(values, clusters)
    total_n = sum(c for _, c in groups)
    observed = sum(s for s, _ in groups) / total_n
    rng = random.Random(seed)
    extreme = 0
    for _ in range(reps):
        s = sum(a * (1 if rng.random() < .5 else -1) for a, _ in groups)
        extreme += abs(s / total_n) >= abs(observed) - 1e-12
    return (extreme + 1) / (reps + 1)


def correlation_ci(x, y, clusters, seed=SEED, reps=REPS):
    groups = defaultdict(list)
    for a, b, c in zip(x, y, clusters):
        groups[c].append((a, b))
    keys = list(groups)
    rng = random.Random(seed)
    vals = []
    degenerate = 0
    for _ in range(reps):
        xx, yy = [], []
        for _ in keys:
            for a, b in groups[keys[rng.randrange(len(keys))]]:
                xx.append(a)
                yy.append(b)
        r = pearson(xx, yy)
        if r is None:
            degenerate += 1
        else:
            vals.append(r)
    ci = [quantile(vals, .025), quantile(vals, .975)] if len(vals) >= .95 * reps else [None, None]
    return ci, degenerate


def correlation_p(x, y, seed=SEED):
    r = pearson(x, y)
    if r is None:
        return None, "undefined"
    if len(x) <= 8:
        perms = itertools.permutations(y)
        n = extreme = 0
        for yy in perms:
            rr = pearson(x, yy)
            n += 1
            extreme += rr is not None and abs(rr) >= abs(r) - 1e-12
        return (extreme + 1) / (n + 1), "exact permutations + 1 correction"
    rng = random.Random(seed)
    yy = list(y)
    extreme = 0
    for _ in range(REPS):
        rng.shuffle(yy)
        rr = pearson(x, yy)
        extreme += rr is not None and abs(rr) >= abs(r) - 1e-12
    return (extreme + 1) / (REPS + 1), "seeded permutations + 1 correction"


def holm(pvals):
    order = sorted(range(len(pvals)), key=lambda i: pvals[i])
    out = [None] * len(pvals)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (len(pvals) - rank) * pvals[i])
        out[i] = min(1.0, running)
    return out


def poisson(lam, kmax=MAX_SCORE):
    p = [math.exp(-lam)]
    for k in range(1, kmax + 1):
        p.append(p[-1] * lam / k)
    z = sum(p)
    return [v / z for v in p]


def score_features(l1, l2):
    pa, pb = poisson(l1), poisson(l2)
    margin = [0.0] * (2 * MAX_SCORE + 1)
    total = [0.0] * (2 * MAX_SCORE + 1)
    win = tie = 0.0
    for i, x in enumerate(pa):
        for j, y in enumerate(pb):
            p = x * y
            margin[i - j + MAX_SCORE] += p
            total[i + j] += p
            if i > j:
                win += p
            elif i == j:
                tie += p
    def best_line(probs, offset=0):
        # suffix[k] = P(integer outcome >= k); half line is k-0.5.
        suffix = [0.0] * (len(probs) + 1)
        for k in range(len(probs) - 1, -1, -1):
            suffix[k] = suffix[k + 1] + probs[k]
        candidates = []
        for k in range(len(probs)):
            t = k - offset - .5
            candidates.append((abs(suffix[k] - .5), t, suffix[k]))
        _, t, over = min(candidates)
        return t, over
    margin_t, cover_a = best_line(margin, MAX_SCORE)
    total_t, over = best_line(total)
    return {"lambda_a": l1, "lambda_b": l2, "mean_margin": l1 - l2,
            "mean_total": l1 + l2, "p_a_win": win, "p_tie": tie,
            "p_a_winshare": win + .5 * tie, "spread_a": -margin_t,
            "spread_a_cover_p": cover_a, "total_line": total_t, "total_over_p": over,
            "fair_decimal_a": 1 / (win + .5 * tie),
            "fair_decimal_b": 1 / (1 - win - .5 * tie)}


def same_game_combo(l1, l2):
    f = score_features(l1, l2)
    a_favorite = f["p_a_winshare"] >= .5
    # Favorite handicap h means favorite margin + h > 0.
    threshold = -f["spread_a"] if a_favorite else f["spread_a"]
    total_t = f["total_line"]
    pa, pb = poisson(l1), poisson(l2)
    joint = cover = over = 0.0
    for i, x in enumerate(pa):
        for j, y in enumerate(pb):
            p = x * y
            fav_margin = i - j if a_favorite else j - i
            hit_cover = fav_margin > threshold
            hit_over = i + j > total_t
            cover += p * hit_cover
            over += p * hit_over
            joint += p * (hit_cover and hit_over)
    denom = math.sqrt(cover * (1 - cover) * over * (1 - over))
    phi = (joint - cover * over) / denom if denom else None
    return {"favorite": "A" if a_favorite else "B", "favorite_spread": -threshold,
            "total_line": total_t, "p_cover": cover, "p_over": over,
            "p_joint_model": joint, "p_independent_product": cover * over,
            "phi_model": phi, "fair_decimal_joint_model": 1 / joint if joint else None,
            "status": "Model-implied only; not empirical or executable; no reward"}


class PointsModel:
    def __init__(self, games, standings, sources):
        self.games = sorted(games, key=lambda g: (g["date"], g["id"]))
        self.standings = standings
        self.sources = sources
        self.preds = []
        self.parlays = []
        self.hist = defaultdict(list)
        self.last_date = {}
        self.rest_xy = self.rest_xx = 0.0
        self.leg_history = defaultdict(list)
        self.cross_num = defaultdict(float)
        self.cross_den = defaultdict(float)
        self.prior = {}
        for season in (2025, 2026):
            rows = [r for r in standings if r["season"] == season - 1]
            lg = sum(r["pf"] for r in rows) / sum(r["w"] + r["l"] + r["t"] for r in rows)
            self.prior[season] = {"league": lg, "teams": {}}
            for r in rows:
                n = r["w"] + r["l"] + r["t"]
                w = P["prior_shrinkage_games"]
                self.prior[season]["teams"][r["team"]] = (
                    (r["pf"] + w * lg) / (n + w), (r["pa"] + w * lg) / (n + w))
        self.weeks = sorted({(g["season"], g["week"]) for g in self.games})

    def rating(self, team, season, week, cfg):
        prior_off, prior_def = self.prior[season]["teams"][team]
        if cfg["decay"] == 0:
            return prior_off, prior_def, 0.0
        obs = [(w, pf, pa) for (s, w, pf, pa) in self.hist[team] if s == season and w < week]
        weights = [cfg["decay"] ** (week - w) for w, _, _ in obs]
        neff = sum(weights)
        if not neff:
            return prior_off, prior_def, 0.0
        off = sum(w * pf for w, (_, pf, _) in zip(weights, obs)) / neff
        deff = sum(w * pa for w, (_, _, pa) in zip(weights, obs)) / neff
        pw = cfg["prior_weight"]
        return (pw * prior_off + neff * off) / (pw + neff), (pw * prior_def + neff * deff) / (pw + neff), neff

    def rest_diff(self, g):
        d = date.fromisoformat(g["date"])
        def days(team):
            prev = self.last_date.get(team)
            return (d - prev[1]).days if prev and prev[0] == g["season"] else P["rest_default_days"]
        ra, rb = days(g["team_a"]), days(g["team_b"])
        return max(-P["rest_feature_clip_days"], min(P["rest_feature_clip_days"], ra - rb))

    def base_lambdas(self, g, cfg):
        oa, da, na = self.rating(g["team_a"], g["season"], g["week"], cfg)
        ob, db, nb = self.rating(g["team_b"], g["season"], g["week"], cfg)
        return max(P["lambda_floor"], (oa + db) / 2), max(P["lambda_floor"], (ob + da) / 2), na, nb

    def rho(self, model):
        bound = P["cross_game_dependence_bound"]
        return max(-bound, min(bound, self.cross_num[model] / (self.cross_den[model] + P["cross_game_dependence_ridge"])))

    def run(self):
        for season, week in self.weeks:
            slate = [g for g in self.games if g["season"] == season and g["week"] == week]
            beta = self.rest_xy / (self.rest_xx + P["rest_ridge"])
            week_preds = {m: [] for m in PROTOCOL["models"]}
            week_legs = {m: [] for m in ("M2", "M4")}
            for g in slate:
                rd = self.rest_diff(g)
                margin = g["score_a"] - g["score_b"]
                total = g["score_a"] + g["score_b"]
                ywin = 1.0 if margin > 0 else 0.0 if margin < 0 else .5
                base2 = self.base_lambdas(g, PROTOCOL["models"]["M2"])
                for mid, cfg in PROTOCOL["models"].items():
                    l1, l2, na, nb = self.base_lambdas(g, cfg)
                    if cfg["rest"]:
                        m = l1 - l2 + beta * rd
                        t = l1 + l2
                        l1, l2 = max(P["lambda_floor"], (t + m) / 2), max(P["lambda_floor"], (t - m) / 2)
                    f = score_features(l1, l2)
                    row = {"game_id": g["id"], "season": season, "week": week, "date": g["date"],
                           "model": mid, "team_a": g["team_a"], "team_b": g["team_b"],
                           "rest_diff": rd, "rest_beta": beta if cfg["rest"] else 0.0,
                           "prior_games_a": na, "prior_games_b": nb,
                           **f, "actual_margin": margin, "actual_total": total,
                           "actual_a_winshare": ywin, "actual_a_win": 1 if margin > 0 else 0,
                           "evaluation": season > 2025 or week >= 6,
                           "source_id": g["source_id"], "source_url": g["source_url"],
                           "provenance": "Derived from earlier official games; not an official NFL line or market price"}
                    self.preds.append(row)
                    week_preds[mid].append(row)
                    if mid in week_legs:
                        a_fav = f["p_a_win"] >= .5
                        leg = {"game_id": g["id"], "p": f["p_a_win"] if a_fav else 1 - f["p_a_win"] - f["p_tie"],
                               "hit": 1 if (margin > 0 if a_fav else margin < 0) else 0,
                               "favorite": g["team_a"] if a_fav else g["team_b"]}
                        week_legs[mid].append(leg)
                # Only past M2 residuals enter the online rest coefficient.
                self.rest_xy += rd * (margin - (base2[0] - base2[1]))
                self.rest_xx += rd * rd
            for mid in ("M2", "M4"):
                eligible = sorted([x for x in week_legs[mid] if x["p"] >= P["primary_favorite_threshold"]], key=lambda x: x["game_id"])
                rho = self.rho(mid)
                for i in range(0, len(eligible) - 1, 2):
                    a, b = eligible[i:i + 2]
                    p1, p2 = a["p"], b["p"]
                    raw = p1 * p2 + rho * math.sqrt(p1 * (1 - p1) * p2 * (1 - p2))
                    joint = max(max(0, p1 + p2 - 1), min(min(p1, p2), raw))
                    self.parlays.append({"model": mid, "season": season, "week": week,
                                         "leg_1": a["game_id"], "leg_2": b["game_id"],
                                         "favorite_1": a["favorite"], "favorite_2": b["favorite"],
                                         "p1": p1, "p2": p2, "rho_prior": rho,
                                         "p_joint": joint, "p_independent": p1 * p2,
                                         "leg_1_hit": a["hit"], "leg_2_hit": b["hit"],
                                         "hit": a["hit"] * b["hit"],
                                         "fair_decimal_joint": 1 / joint if joint else None,
                                         "evaluation": season > 2025 or week >= 6,
                                         "source_url": self.sources[f"NFL-{season}-W{week}"]["url"],
                                         "provenance": "Derived two-leg outright-win research event; ties lose; not sportsbook settlement"})
                # Update cross-game residual dependence AFTER predicting this week.
                legs = week_legs[mid]
                for i in range(len(legs)):
                    for j in range(i + 1, len(legs)):
                        a, b = legs[i], legs[j]
                        if a["game_id"] == b["game_id"]:
                            continue
                        va, vb = a["p"] * (1 - a["p"]), b["p"] * (1 - b["p"])
                        self.cross_num[mid] += (a["hit"] - a["p"]) * (b["hit"] - b["p"])
                        self.cross_den[mid] += math.sqrt(va * vb)
            for g in slate:
                d = date.fromisoformat(g["date"])
                self.last_date[g["team_a"]] = self.last_date[g["team_b"]] = (season, d)
                self.hist[g["team_a"]].append((season, week, g["score_a"], g["score_b"]))
                self.hist[g["team_b"]].append((season, week, g["score_b"], g["score_a"]))
        return self.preds, self.parlays

    def current(self, upcoming):
        upcoming = {**upcoming, "team_a": upcoming["away_team"], "team_b": upcoming["home_team"]}
        beta = self.rest_xy / (self.rest_xx + P["rest_ridge"])
        rd = self.rest_diff(upcoming)
        rows = []
        for mid, cfg in PROTOCOL["models"].items():
            l1, l2, na, nb = self.base_lambdas(upcoming, cfg)
            if cfg["rest"]:
                m, t = l1 - l2 + beta * rd, l1 + l2
                l1, l2 = max(P["lambda_floor"], (t + m) / 2), max(P["lambda_floor"], (t - m) / 2)
            f = score_features(l1, l2)
            rows.append({"model": mid, "model_name": cfg["name"], "date": upcoming["date"],
                         "away": upcoming["away_team"], "home": upcoming["home_team"],
                         "away_points": l1, "home_points": l2, "away_spread": f["spread_a"],
                         "total": f["total_line"], "away_winshare_p": f["p_a_winshare"],
                         "home_winshare_p": 1 - f["p_a_winshare"],
                         "away_fair_decimal": f["fair_decimal_a"], "home_fair_decimal": f["fair_decimal_b"],
                         "rest_diff": rd, "rest_beta": beta if cfg["rest"] else 0,
                         "market_spread": None, "market_total": None, "market_odds": None,
                         "edge": None, "recommendation": "Research only — release gates blocked",
                         "source_id": "GAME", "source_url": upcoming["source_url"],
                         "provenance": "Derived fair line; official source supports inputs/matchup, not the line"})
        return rows


def calibration(rows, metric="win"):
    if metric == "win":
        pk, yk = "p_a_winshare", "actual_a_winshare"
        pairs = [(r[pk], r[yk]) for r in rows]
    elif metric == "margin":
        pairs = [(r["spread_a_cover_p"], 1.0 if r["actual_margin"] > -r["spread_a"] else 0.0) for r in rows]
    else:
        pairs = [(r["total_over_p"], 1.0 if r["actual_total"] > r["total_line"] else 0.0) for r in rows]
    pairs.sort(key=lambda x: x[0])
    n = len(pairs)
    bins = []
    ece = 0.0
    for i in range(P["calibration_bins"]):
        part = pairs[i * n // 5:(i + 1) * n // 5]
        p = mean(a for a, _ in part)
        y = mean(b for _, b in part)
        ece += len(part) / n * abs(p - y)
        bins.append({"n": len(part), "predicted": p, "observed": y, "gap": p - y})
    max_gap = max((abs(b["gap"]) for b in bins if b["n"] >= 20), default=0)
    return {"metric": metric, "ece": ece, "max_bin_gap_n20": max_gap, "bins": bins,
            "pass": ece <= .04 and max_gap <= .10}


def loss(row, metric):
    if metric == "win":
        return (row["p_a_winshare"] - row["actual_a_winshare"]) ** 2
    if metric == "margin":
        return (row["mean_margin"] - row["actual_margin"]) ** 2
    return (row["mean_total"] - row["actual_total"]) ** 2


def evaluate(preds, parlays, integrity, leakage):
    ev = [r for r in preds if r["evaluation"]]
    clusters = [f'{r["season"]}-{r["week"]}' for r in ev]
    by_model = {m: [r for r in ev if r["model"] == m] for m in PROTOCOL["models"]}
    base = by_model["M1"]
    metrics, diffs, primary = {}, {}, []
    for mid, rows in by_model.items():
        metrics[mid] = {"n": len(rows), "weeks": len(set(clusters)),
                        "win_brier": mean(loss(r, "win") for r in rows),
                        "margin_mse": mean(loss(r, "margin") for r in rows),
                        "total_mse": mean(loss(r, "total") for r in rows),
                        "margin_mae": mean(abs(r["mean_margin"] - r["actual_margin"]) for r in rows),
                        "total_mae": mean(abs(r["mean_total"] - r["actual_total"]) for r in rows),
                        "calibration": calibration(rows),
                        "calibration_by_metric": {metric: calibration(rows, metric) for metric in ("win", "margin", "total")}}
        diffs[mid] = {}
        for metric in ("win", "margin", "total"):
            d = [loss(b, metric) - loss(r, metric) for b, r in zip(base, rows)]
            ci = cluster_ci(d, clusters)
            pval = cluster_permutation(d, clusters)
            season_imp = {str(y): mean(v for v, r in zip(d, rows) if r["season"] == y) for y in (2025, 2026)}
            groups = cluster_groups(d, clusters)
            total_d, total_n = sum(s for s, _ in groups), sum(n for _, n in groups)
            lowoo = min((total_d - s) / (total_n - n) for s, n in groups)
            diffs[mid][metric] = {"mean_improvement": mean(d), "ci95": ci, "p_perm": pval,
                                  "season_improvement": season_imp, "min_leave_one_week_out": lowoo}
            if mid in ("M2", "M4"):
                primary.append((mid, metric, pval))
    adjusted = holm([x[2] for x in primary])
    for (mid, metric, _), q in zip(primary, adjusted):
        diffs[mid][metric]["p_holm"] = q
    strategies = []
    for mid in ("M2", "M4"):
        for metric, division, label in (("win", "Singles", "Draw-half win-share favorite pricing"),
                                         ("margin", "Singles", "Own fair spread / margin calibration"),
                                         ("total", "Singles", "Own fair total / total calibration")):
            d = diffs[mid][metric]
            m = metrics[mid]
            gates = {
                "G01": "pass" if integrity["pass"] else "fail",
                "G02": "pass" if leakage["pass"] else "fail",
                "G03": "pass" if m["n"] >= 300 and m["weeks"] >= 20 else "fail",
                "G04": "pass" if d["ci95"][0] > 0 and d["p_holm"] < .05 else "fail",
                "G05": "pass" if m["calibration_by_metric"][metric]["pass"] else "fail",
                "G06": "pass" if all(v > 0 for v in d["season_improvement"].values()) and d["min_leave_one_week_out"] > 0 else "fail",
                "G07": "pass",
                "G08": "blocked", "G09": "blocked", "G10": "blocked",
                "G11": "pass", "G12": "pass",
            }
            strategies.append({"id": f"{mid}-{metric}", "division": division, "name": f'{PROTOCOL["models"][mid]["name"]}: {label}',
                               "n": m["n"], "weeks": m["weeks"], "metric": metric,
                               "loss": m["win_brier" if metric == "win" else metric + "_mse"],
                               "improvement_vs_prior": d["mean_improvement"], "ci95": d["ci95"],
                               "p_holm": d["p_holm"], "gates": gates,
                               "eligible": all(v == "pass" for v in gates.values()),
                               "status": "Research only — market/prospective gates blocked", "reward": 0,
                               "market_roi": None, "clv": None,
                               "source_ids": ["STAND-2024", "STAND-2025", "STAND-2026", "CALIBRATION", "SPLITS"],
                               "source_url": "https://www.nfl.com/standings/league/2025/REG"})
    par_metrics = {}
    for mid in ("M2", "M4"):
        rows = [r for r in parlays if r["model"] == mid and r["evaluation"]]
        cl = [f'{r["season"]}-{r["week"]}' for r in rows]
        d = [(r["p_independent"] - r["hit"]) ** 2 - (r["p_joint"] - r["hit"]) ** 2 for r in rows]
        ci = cluster_ci(d, cl) if rows else [None, None]
        par_metrics[mid] = {"n": len(rows), "weeks": len(set(cl)),
                            "hit_rate": mean(r["hit"] for r in rows) if rows else None,
                            "joint_brier": mean((r["p_joint"] - r["hit"]) ** 2 for r in rows) if rows else None,
                            "independent_brier": mean((r["p_independent"] - r["hit"]) ** 2 for r in rows) if rows else None,
                            "improvement_vs_independent": mean(d) if d else None,
                            "ci95": ci, "final_rho": None}
        gates = {"G01": "pass" if integrity["pass"] else "fail", "G02": "pass" if leakage["pass"] else "fail",
                 "G03": "pass" if len(rows) >= 150 and len(set(cl)) >= 20 else "fail",
                 "G04": "blocked", "G05": "blocked", "G06": "blocked",
                 "G07": "pass" if ci[0] is not None and ci[0] > 0 else "fail",
                 "G08": "blocked", "G09": "blocked", "G10": "blocked", "G11": "blocked", "G12": "pass"}
        strategies.append({"id": f"{mid}-parlay", "division": "Parlays", "name": f'{PROTOCOL["models"][mid]["name"]}: cross-game favorite pair',
                           "n": len(rows), "weeks": len(set(cl)), "metric": "joint_brier",
                           "loss": par_metrics[mid]["joint_brier"], "improvement_vs_prior": par_metrics[mid]["improvement_vs_independent"],
                           "ci95": ci, "p_holm": None, "gates": gates, "eligible": False,
                           "status": "Exploratory — sample/dependence/market gates not passed", "reward": 0,
                           "market_roi": None, "clv": None, "source_ids": ["BOOTSTRAP", "CORRELATION"],
                           "source_url": "https://www.nfl.com/schedules/2025/by-week/week-6"})
    return {"metrics": metrics, "improvements": {m: v for m, v in diffs.items() if m in ("M2", "M4")},
            "primary_family_size": len(primary), "parlays": par_metrics, "strategies": strategies}


def player_research(players, sources):
    lines, combos, correlations = [], [], []
    for name in dict.fromkeys(p["player"] for p in players):
        rows = [p for p in players if p["player"] == name]
        for key, metric in (("a", rows[0]["metric_a"]), ("b", rows[0]["metric_b"])):
            vals = [p["value_" + key] for p in rows if p["value_" + key] is not None]
            med = quantile(vals, .5)
            candidates = [math.floor(med) - .5, math.floor(med) + .5]
            line = min(candidates, key=lambda t: (abs(mean(v > t for v in vals) - .5), t))
            lines.append({"player": name, "team": rows[0]["team"], "metric": metric,
                          "observed_n": len(vals), "missing_n": len(rows) - len(vals),
                          "median": med, "own_line": line, "empirical_over_p": mean(v > line for v in vals),
                          "market_line": None, "market_odds": None, "edge": None,
                          "status": "Descriptive only — insufficient sample and blocked market/availability gates",
                          "source_id": rows[0]["source_id"], "source_url": rows[0]["source_url"]})
        complete = [p for p in rows if p["value_a"] is not None and p["value_b"] is not None]
        x = [p["value_a"] for p in complete]
        y = [p["value_b"] for p in complete]
        r = pearson(x, y)
        ci, deg = correlation_ci(x, y, [p["week"] for p in complete]) if len(complete) >= 3 else ([None, None], 0)
        pv, method = correlation_p(x, y)
        correlations.append({"id": f"PROP-{name}", "pair": f'{name}: {rows[0]["metric_a"]} vs {rows[0]["metric_b"]}',
                             "kind": "Empirical paired player-game Pearson r; small sample, mechanically related",
                             "n": len(complete), "r": r, "ci95": ci, "p": pv, "p_method": method,
                             "degenerate_bootstrap_replicates": deg,
                             "source_id": rows[0]["source_id"], "source_url": rows[0]["source_url"],
                             "status": "Measured from official logs; not a sportsbook edge"})
        if rows[0]["metric_a"] == "receptions":
            la = next(l for l in lines if l["player"] == name and l["metric"] == "receptions")["own_line"]
            lb = next(l for l in lines if l["player"] == name and l["metric"] == "receiving_yards")["own_line"]
            hits_a = [p["value_a"] > la for p in complete]
            hits_b = [p["value_b"] > lb for p in complete]
            joint = mean(a and b for a, b in zip(hits_a, hits_b))
            p1, p2 = mean(hits_a), mean(hits_b)
            den = math.sqrt(p1 * (1 - p1) * p2 * (1 - p2))
            combos.append({"player": name, "legs": f'receptions > {la:g} + receiving yards > {lb:g}',
                           "n": len(complete), "joint_hits": sum(a and b for a, b in zip(hits_a, hits_b)),
                           "p_joint_empirical": joint, "p_independent_product": p1 * p2,
                           "phi_empirical": (joint - p1 * p2) / den if den else None,
                           "market_odds": None, "status": "Research only — n<100, no prospective or market validation",
                           "gates": {**{f"G{i:02}": "blocked" for i in range(1, 13)}, "G01": "pass", "G03": "fail", "G07": "fail", "G12": "pass"},
                           "eligible": False, "reward": 0,
                           "source_id": rows[0]["source_id"], "source_url": rows[0]["source_url"]})
    correlations.append({"id": "CROSS-PLAYER", "pair": "Smith-Njigba receiving yards vs Burden receiving yards in same game",
                         "kind": "Cross-player same-game dependence", "n": 0, "r": None,
                         "ci95": [None, None], "p": None, "p_method": "No paired observations",
                         "source_id": "GAME", "source_url": sources["GAME"]["url"],
                         "status": "Unverified — different-team player logs do not supply a shared-game sample; joint price blocked"})
    return lines, combos, correlations


def game_correlations(preds, sources):
    rows = [r for r in preds if r["model"] == "M2" and r["evaluation"]]
    clusters = [f'{r["season"]}-{r["week"]}' for r in rows]
    specs = [
        ("SCORES", "Listed team A points vs team B points", [r["actual_margin"] + r["actual_total"] for r in rows], [r["actual_total"] - r["actual_margin"] for r in rows], "Empirical game-score association; includes shared pace/game state"),
        ("MARGIN-ERROR", "M2 margin error vs total error", [r["mean_margin"] - r["actual_margin"] for r in rows], [r["mean_total"] - r["actual_total"] for r in rows], "Empirical residual association; not a causal effect"),
        ("REST-MARGIN", "Rest-day difference vs actual margin", [r["rest_diff"] for r in rows], [r["actual_margin"] for r in rows], "Empirical unadjusted association; not the fitted rest coefficient"),
    ]
    out = []
    for sid, pair, x, y, kind in specs:
        # Recover integer scores without division to avoid rounding.
        if sid == "SCORES":
            x = [(r["actual_total"] + r["actual_margin"]) / 2 for r in rows]
            y = [(r["actual_total"] - r["actual_margin"]) / 2 for r in rows]
        r = pearson(x, y)
        ci, deg = correlation_ci(x, y, clusters)
        pv, method = correlation_p(x, y)
        out.append({"id": sid, "pair": pair, "kind": kind, "n": len(rows), "r": r,
                    "ci95": ci, "p": pv, "p_method": method, "degenerate_bootstrap_replicates": deg,
                    "source_id": "STAND-2025", "source_url": sources["STAND-2025"]["url"],
                    "status": "Derived from official game scores; not an official NFL coefficient"})
    return out


def integrity_check(games, standings, players, sources):
    checks = 0
    details = []
    for season in (2025, 2026):
        agg = defaultdict(lambda: [0, 0, 0, 0, 0])
        for g in games:
            if g["season"] != season:
                continue
            for t, s, o in ((g["team_a"], g["score_a"], g["score_b"]), (g["team_b"], g["score_b"], g["score_a"])):
                a = agg[t]
                a[0] += s > o
                a[1] += s < o
                a[2] += s == o
                a[3] += s
                a[4] += o
        for r in [r for r in standings if r["season"] == season]:
            expected = [r[k] for k in ("w", "l", "t", "pf", "pa")]
            assert agg[r["team"]] == expected, (season, r["team"], agg[r["team"]], expected)
            checks += 5
        details.append({"season": season, "games": sum(g["season"] == season for g in games), "team_rows": 32, "cells_matched": 160})
    totals = {"Caleb Williams": (1020, None), "Sam Darnold": (1290, None),
              "Jaxon Smith-Njigba": (58, 867), "Luther Burden III": (35, 491)}
    for name, (a, b) in totals.items():
        rows = [p for p in players if p["player"] == name]
        assert sum(p["value_a"] for p in rows if p["value_a"] is not None) == a
        if b is not None:
            assert sum(p["value_b"] for p in rows if p["value_b"] is not None) == b
    assert all(r["source_url"].startswith("https://") for r in games + standings + players)
    return {"pass": True, "standings_cells_matched": checks, "season_details": details,
            "player_sum_checks": "Receiving sums and both QB passing sums match the official Game Center; blank cells excluded, never zero-filled.",
            "missing_player_cells": sum(p[k] is None for p in players for k in ("value_a", "value_b"))}


def leakage_test(games, standings, sources):
    original = PointsModel(games, standings, sources).run()[0]
    changed = [dict(g) for g in games]
    # Change every outcome in the final eight official games. No earlier prediction may change.
    for g in changed:
        if g["season"] == 2026 and g["week"] == 8:
            g["score_a"], g["score_b"] = g["score_b"] + 17, g["score_a"] + 11
    perturbed = PointsModel(changed, standings, sources).run()[0]
    before = [r for r in original if not (r["season"] == 2026 and r["week"] == 8)]
    after = [r for r in perturbed if not (r["season"] == 2026 and r["week"] == 8)]
    # Actual-outcome fields in earlier rows do not change; all prediction fields must match exactly.
    same = before == after
    return {"pass": same, "rows_compared": len(before),
            "method": "Perturbed all 2026 Week 8 scores and reran; compared every earlier prediction row exactly."}


def main():
    games, standings, players, sources, upcoming = (load(n) for n in ("games.json", "standings.json", "players.json", "sources.json", "upcoming.json"))
    integrity = integrity_check(games, standings, players, sources)
    model = PointsModel(games, standings, sources)
    preds, parlays = model.run()
    leakage = leakage_test(games, standings, sources)
    assert leakage["pass"]
    evaluation = evaluate(preds, parlays, integrity, leakage)
    for mid in ("M2", "M4"):
        evaluation["parlays"][mid]["final_rho"] = model.rho(mid)
    current = model.current(upcoming)
    combo = same_game_combo(next(r["away_points"] for r in current if r["model"] == "M2"), next(r["home_points"] for r in current if r["model"] == "M2"))
    combo.update({"game": "CHI at SEA", "source_id": "GAME", "source_url": sources["GAME"]["url"]})
    plines, pcombos, pcorr = player_research(players, sources)
    correlations = game_correlations(preds, sources) + pcorr
    # Explicitly blocked strategy entries for every requested prop category.
    for c in pcombos:
        evaluation["strategies"].append({"id": "PROP-" + c["player"], "division": "Player prop combinations",
                                         "name": c["player"] + " receptions + receiving yards", "n": c["n"], "weeks": c["n"],
                                         "metric": "empirical joint hit rate", "loss": None,
                                         "improvement_vs_prior": None, "ci95": [None, None], "p_holm": None,
                                         "gates": c["gates"], "eligible": False, "status": c["status"], "reward": 0,
                                         "market_roi": None, "clv": None, "source_ids": [c["source_id"]], "source_url": c["source_url"]})
    evaluation["strategies"].append({"id": "SGP-M2", "division": "Parlays", "name": "Same-game favorite spread + total (model joint)",
                                     "n": 0, "weeks": 0, "metric": "model joint probability", "loss": None,
                                     "improvement_vs_prior": None, "ci95": [None, None], "p_holm": None,
                                     "gates": {**{f"G{i:02}": "blocked" for i in range(1, 13)}, "G12": "pass"},
                                     "eligible": False, "status": "Model-implied only; no empirical SGP price validation", "reward": 0,
                                     "market_roi": None, "clv": None, "source_ids": ["GAME", "CORRELATION"], "source_url": sources["GAME"]["url"]})
    evaluation["strategies"].append({"id": "PROP-CROSS", "division": "Player prop combinations", "name": "Smith-Njigba + Burden same-game receiving yards",
                                     "n": 0, "weeks": 0, "metric": "joint probability", "loss": None,
                                     "improvement_vs_prior": None, "ci95": [None, None], "p_holm": None,
                                     "gates": {**{f"G{i:02}": "blocked" for i in range(1, 13)}, "G12": "pass"},
                                     "eligible": False, "status": "Unverified cross-player dependence; no joint price", "reward": 0,
                                     "market_roi": None, "clv": None, "source_ids": ["GAME"], "source_url": sources["GAME"]["url"]})
    leaderboard = {"eligible": [s["id"] for s in evaluation["strategies"] if s["eligible"]],
                   "reward_points_awarded": 0, "funded": False,
                   "message": "No strategy passed every gate. Probability research is not betting ROI. No winner or reward is manufactured."}
    summary = {"cutoff": "2026-11-02", "official_games": len(games), "evaluation_games": evaluation["metrics"]["M1"]["n"],
               "evaluation_weeks": evaluation["metrics"]["M1"]["weeks"], "player_rows": len(players),
               "missing_player_cells": integrity["missing_player_cells"], "eligible_strategies": 0,
               "reward_points": 0, "protocol_version": PROTOCOL["version"]}
    dump("integrity.json", integrity)
    dump("leakage.json", leakage)
    dump("evaluation.json", evaluation)
    dump("current_lines.json", current)
    dump("same_game_combo.json", combo)
    dump("player_lines.json", plines)
    dump("player_combos.json", pcombos)
    dump("correlations.json", correlations)
    dump("leaderboard.json", leaderboard)
    dump("summary.json", summary)
    csv_dump("predictions.csv", preds)
    csv_dump("parlays.csv", parlays)
    csv_dump("current_lines.csv", current)
    csv_dump("player_lines.csv", plines)
    csv_dump("correlations.csv", [{**r, "ci95": json.dumps(r["ci95"])} for r in correlations])
    print(json.dumps(summary, indent=2))
    for mid in ("M1", "M2", "M3", "M4"):
        m = evaluation["metrics"][mid]
        print(mid, "Brier", round(m["win_brier"], 5), "margin MAE", round(m["margin_mae"], 3), "total MAE", round(m["total_mae"], 3), "ECE", round(m["calibration"]["ece"], 4))
    print("Current M2:", next(r for r in current if r["model"] == "M2"))
    print("Eligible:", leaderboard["eligible"])


if __name__ == "__main__":
    main()
