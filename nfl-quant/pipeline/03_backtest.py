"""Q4: strategy backtests + validation gates + luck removal.

Protocol (pre-registered in gates.json BEFORE this script was first run):
  * thresholds tuned on VALIDATION seasons 2013-2016 only, then frozen;
  * HOLDOUT 2017-2025 evaluated exactly once at archived closing lines;
  * week-clustered bootstrap CI, matched-random permutation test, Holm
    correction across the primary family, season-stability checks,
    500-draw random placebo calibration.

Settlement conventions (verified vs official sportsbook rules):
  * FanDuel House Rules (Ontario, Part B s.19): parlay = all legs must win;
    void/push legs removed and odds recalculated; whole-number line push
    refunds the leg. Parlay payout = product of leg odds (FanDuel official
    parlay guide; DraftKings rules: payout calculated on decimal odds).
  * spread_line convention: POSITIVE = home favored (verified in 01).
"""
import json, datetime, itertools
import numpy as np
import pandas as pd
from common import DATA, load_json, save_json, write_df, am_to_dec, am_to_prob, breakeven_prob

NOW = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
rng = np.random.default_rng(20261102)
gates = json.loads((DATA.parent / "pipeline" / "gates.json").read_text())

p = pd.read_csv(DATA / "predictions.csv", parse_dates=["gameday"])
p = p[p.pred_margin.notna()].copy()
p["cover_margin"] = p.result - p.spread_line          # >0 home covers
p["total_diff"] = p.total - p.total_line              # >0 over hits
p["cluster"] = list(zip(p.season, p.week))

def odds_or(v, default=-110.0):
    return default if pd.isna(v) else float(v)

def settle_ats(row, side):
    cm = row.cover_margin
    if pd.isna(cm):
        return None
    if cm == 0:
        return ("push", 0.0, odds_or(row.home_spread_odds if side == "home" else row.away_spread_odds))
    win = (cm > 0) if side == "home" else (cm < 0)
    o = odds_or(row.home_spread_odds if side == "home" else row.away_spread_odds)
    return ("win" if win else "loss", (am_to_dec(o) - 1) if win else -1.0, o)

def settle_total(row, side):
    d = row.total_diff
    if pd.isna(d):
        return None
    if d == 0:
        return ("push", 0.0, odds_or(row.over_odds if side == "over" else row.under_odds))
    win = (d > 0) if side == "over" else (d < 0)
    o = odds_or(row.over_odds if side == "over" else row.under_odds)
    return ("win" if win else "loss", (am_to_dec(o) - 1) if win else -1.0, o)

def settle_ml(row, side):
    if pd.isna(row.result) or pd.isna(row.home_moneyline) or pd.isna(row.away_moneyline):
        return None
    if row.result == 0:
        return ("push", 0.0, float(row.home_moneyline if side == "home" else row.away_moneyline))
    win = (row.result > 0) if side == "home" else (row.result < 0)
    o = float(row.home_moneyline if side == "home" else row.away_moneyline)
    return ("win" if win else "loss", (am_to_dec(o) - 1) if win else -1.0, o)

def ats_bets(df, theta):
    rows = []
    for row in df.itertuples():
        if pd.isna(row.spread_line) or pd.isna(row.result):
            continue
        edge = row.pred_margin - row.spread_line
        if edge >= theta:
            side = "home"
        elif edge <= -theta:
            side = "away"
        else:
            continue
        s = settle_ats(row, side)
        if s:
            rows.append(dict(game_id=row.game_id, season=row.season, week=row.week, side=side,
                             outcome=s[0], profit=s[1], odds=s[2], edge=round(edge, 3), cluster=(row.season, row.week)))
    return pd.DataFrame(rows)

def total_bets(df, theta):
    rows = []
    for row in df.itertuples():
        if pd.isna(row.total_line) or pd.isna(row.total) or pd.isna(row.pred_total):
            continue
        edge = row.pred_total - row.total_line
        if edge >= theta:
            side = "over"
        elif edge <= -theta:
            side = "under"
        else:
            continue
        s = settle_total(row, side)
        if s:
            rows.append(dict(game_id=row.game_id, season=row.season, week=row.week, side=side,
                             outcome=s[0], profit=s[1], odds=s[2], edge=round(edge, 3), cluster=(row.season, row.week)))
    return pd.DataFrame(rows)

def ml_bets(df, theta):
    rows = []
    for row in df.itertuples():
        if pd.isna(row.home_moneyline) or pd.isna(row.away_moneyline) or pd.isna(row.result):
            continue
        ph, pa = am_to_prob(row.home_moneyline), am_to_prob(row.away_moneyline)
        fair_h = ph / (ph + pa)
        edge_h = row.p_home_win - fair_h
        if edge_h >= theta:
            side = "home"
        elif -edge_h >= theta:
            side = "away"
        else:
            continue
        s = settle_ml(row, side)
        if s:
            rows.append(dict(game_id=row.game_id, season=row.season, week=row.week, side=side,
                             outcome=s[0], profit=s[1], odds=s[2], edge=round(edge_h if side == "home" else -edge_h, 4),
                             cluster=(row.season, row.week)))
    return pd.DataFrame(rows)

val = p[p.season.between(2013, 2016)]
ho = p[p.season.between(2017, 2025)]

# ---- threshold selection on VALIDATION only (min 100 bets) ----
def pick_theta(fn, grid):
    best = None
    for th in grid:
        b = fn(val, th)
        if len(b) < 100:
            continue
        roi = b.profit.sum() / len(b)
        if best is None or roi > best[0]:
            best = (roi, th, len(b))
    return best

sel = {}
sel["S1"] = pick_theta(ats_bets, [1.5, 2.5, 3.5])
sel["S2"] = pick_theta(total_bets, [2.0, 3.0, 4.0])
sel["S3"] = pick_theta(ml_bets, [0.03, 0.05, 0.07])
print("validation-selected thresholds:", {k: (None if v is None else (round(v[0], 4), v[1], v[2])) for k, v in sel.items()})
TH = {k: (v[1] if v else 99.0) for k, v in sel.items()}  # 99 => no bets if nothing qualified

# ---- HOLDOUT evaluation (once, frozen) ----
bets = {
    "S1": ats_bets(ho, TH["S1"]),
    "S2": total_bets(ho, TH["S2"]),
    "S3": ml_bets(ho, TH["S3"]),
}
# S4: 2-leg cross-game parlays of S1 selections, same week
s1 = bets["S1"]
par_rows = []
for cl, grp in s1.groupby("cluster"):
    legs = grp.to_dict("records")
    for a, b in itertools.combinations(legs, 2):
        if a["game_id"] == b["game_id"]:
            continue
        da, db = am_to_dec(a["odds"]), am_to_dec(b["odds"])
        oa, ob = a["outcome"], b["outcome"]
        if oa == "loss" or ob == "loss":
            # a loss with a push still loses the other leg? push+loss => loss (reduced to single loss)
            profit = -1.0
            outcome = "loss"
        elif oa == "push" and ob == "push":
            profit, outcome = 0.0, "push"
        elif oa == "push":
            profit, outcome = db - 1 if ob == "win" else -1.0, ob
        elif ob == "push":
            profit, outcome = da - 1 if oa == "win" else -1.0, oa
        else:
            win = oa == "win" and ob == "win"
            profit, outcome = (da * db - 1 if win else -1.0), ("win" if win else "loss")
        par_rows.append(dict(game_id=a["game_id"] + "+" + b["game_id"], season=cl[0], week=cl[1],
                             side="parlay", outcome=outcome, profit=profit, odds=da * db, cluster=cl))
bets["S4"] = pd.DataFrame(par_rows)
# C1 control: always home favorite ATS
c1 = []
for row in ho.itertuples():
    if pd.isna(row.spread_line) or row.spread_line <= 0 or pd.isna(row.result):
        continue
    s = settle_ats(row, "home")
    if s:
        c1.append(dict(game_id=row.game_id, season=row.season, week=row.week, side="home_fav",
                       outcome=s[0], profit=s[1], odds=s[2], cluster=(row.season, row.week)))
bets["C1"] = pd.DataFrame(c1)

# ---- statistics & gates ----
def cluster_bootstrap_roi(b, n_draws=2000):
    clusters = b.cluster.unique()
    sums = b.groupby("cluster").agg(profit=("profit", "sum"), n=("profit", "size"))
    idx = {c: i for i, c in enumerate(clusters)}
    prof = sums.profit.to_numpy(); ns = sums.n.to_numpy()
    draws = rng.integers(0, len(clusters), size=(n_draws, len(clusters)))
    rois = prof[draws].sum(axis=1) / ns[draws].sum(axis=1)
    return float(np.percentile(rois, 2.5)), float(np.percentile(rois, 97.5)), float(np.percentile(rois, 5))

def permutation_p(b, n_draws=2000):
    obs = b.profit.sum() / len(b)
    settled = b[b.outcome != "push"]
    if len(settled) == 0:
        return 1.0
    pbe = np.array([breakeven_prob(o) for o in settled.odds])
    wins = rng.random((n_draws, len(settled))) < pbe
    profits = np.where(wins, np.array([am_to_dec(o) - 1 for o in settled.odds]), -1.0)
    null_rois = profits.sum(axis=1) / len(b)  # pushes contribute 0, stake counted
    return float((null_rois >= obs).mean())

def season_stats(b):
    by = b.groupby("season").agg(profit=("profit", "sum"), n=("profit", "size"))
    by["roi"] = by.profit / by.n
    return by

results = {}
primary = ["S1", "S2", "S3", "S4", "C1"]
for sid, b in bets.items():
    if len(b) == 0:
        results[sid] = {"n_bets": 0, "tier": "Blocked", "note": "no qualifying bets"}
        continue
    n = len(b); profit = float(b.profit.sum()); roi = profit / n
    lo, hi, p5 = cluster_bootstrap_roi(b)
    pperm = permutation_p(b)
    by = season_stats(b)
    pos_seasons = int((by.roi > 0).sum()); n_seasons = len(by)
    max_share = float(by.profit.max() / profit) if profit > 0 else None
    results[sid] = {
        "n_bets": n, "wins": int((b.outcome == "win").sum()), "losses": int((b.outcome == "loss").sum()),
        "pushes": int((b.outcome == "push").sum()), "staked": n, "profit_units": round(profit, 3),
        "roi": round(roi, 5), "bootstrap_ci95": [round(lo, 5), round(hi, 5)], "bootstrap_p5": round(p5, 5),
        "permutation_p": round(pperm, 5),
        "seasons": {int(s): {"n": int(r.n), "roi": round(float(r.roi), 5)} for s, r in by.iterrows()},
        "positive_season_frac": round(pos_seasons / n_seasons, 3),
        "max_single_season_profit_share": None if max_share is None else round(max_share, 3),
    }

# Holm correction across primary family
pvals = {s: results[s]["permutation_p"] for s in primary if results[s].get("n_bets", 0) > 0}
order = sorted(pvals, key=pvals.get)
m = len(order)
adj = {}; running = 0.0
for k, s in enumerate(order):
    running = max(running, (m - k) * pvals[s])
    adj[s] = min(1.0, running)
for s in primary:
    if s in results and "permutation_p" in results[s]:
        results[s]["holm_adjusted_p"] = round(adj[s], 5)

# gate evaluation + tiers
for s in primary:
    r = results[s]
    if r.get("n_bets", 0) == 0:
        continue
    g2 = r["n_bets"] >= 300 and len(r["seasons"]) >= 3
    g3 = r["roi"] > 0
    g4 = (r["bootstrap_ci95"][0] > 0) and (r["permutation_p"] < 0.05) and (r["holm_adjusted_p"] < 0.05)
    g4_raw = (r["bootstrap_ci95"][0] > 0) and (r["permutation_p"] < 0.05)
    g5 = (r["positive_season_frac"] >= 0.6) and (r["max_single_season_profit_share"] is None or r["max_single_season_profit_share"] <= 0.5)
    r["gates"] = {"G1": True, "G2": g2, "G3": g3, "G4": g4, "G5": g5, "G6": True, "G7": True, "G8": False}
    if not g3:
        tier = "Rejected"
    elif g2 and g4 and g5:
        tier = "Gold (provisional)"
    elif g4_raw:
        tier = "Silver"
    else:
        tier = "Bronze"
    r["tier"] = tier

# research-only strategies registered but not priced by real markets
results["S5"] = {"tier": "Research-only", "note": "Same-game combo fair-price monitor; no archived official SGP prices exist. See correlations + props outputs. G7 fails by construction.", "gates": {"G7": False, "G8": False}}
results["S6"] = {"tier": "Research-only", "note": "Prop singles vs rolling-mean PROXY line (2021-2022). Not a sportsbook market. G7 fails by construction. See props output.", "gates": {"G7": False, "G8": False}}
results["S7"] = {"tier": "Research-only", "note": "QB+WR1 same-game prop combo joint probabilities (2021-2022). No archived prop prices. G7 fails by construction.", "gates": {"G7": False, "G8": False}}

# ---- C2 placebo calibration: 500 random-side ATS strategies on holdout ----
ho_played = ho[ho.result.notna() & ho.spread_line.notna()]
placebo_rois = []
for _ in range(500):
    sides = rng.random(len(ho_played)) < 0.5
    prof = 0.0
    for row, is_home in zip(ho_played.itertuples(), sides):
        s = settle_ats(row, "home" if is_home else "away")
        if s:
            prof += s[1]
    placebo_rois.append(prof / len(ho_played))
placebo_rois = np.array(placebo_rois)
luck = {
    "n_placebo_strategies": 500,
    "placebo_roi_mean": round(float(placebo_rois.mean()), 5),
    "placebo_roi_p95": round(float(np.percentile(placebo_rois, 95)), 5),
    "placebo_frac_roi_positive": round(float((placebo_rois > 0).mean()), 4),
    "interpretation": "Random betting loses the vig on average; ~half of random strategies still show positive ROI over short samples. This is why gates G2-G5 exist.",
}
save_json("luck_calibration.json", luck)

# leaderboard (betting) — score = max(0, bootstrap p5 ROI) * sqrt(n)
lb = []
for s in primary:
    r = results[s]
    if r.get("n_bets", 0) == 0:
        continue
    score = max(0.0, r["bootstrap_p5"]) * np.sqrt(r["n_bets"])
    lb.append({"strategy": s, "tier": r["tier"], "n_bets": r["n_bets"], "roi": r["roi"],
               "bootstrap_p5_roi": r["bootstrap_p5"], "score": round(float(score), 4)})
lb.sort(key=lambda x: -x["score"])
gold = [x for x in lb if x["tier"] == "Gold (provisional)"]
pool = gates["rewards"]["pool"]
for x in lb:
    x["reward_points"] = round(pool / len(gold), 2) if gold and x in gold else 0
leaderboard = {"generated_utc": NOW, "entries": lb, "reward_pool": pool,
               "awarded": bool(gold), "note": gates["rewards"]["allocation"]}
save_json("leaderboard.json", leaderboard)
save_json("strategy_results.json", {"generated_utc": NOW, "thresholds_frozen": {k: TH[k] for k in ("S1", "S2", "S3")},
                                     "validation_selection": {k: (None if v is None else {"val_roi": round(v[0], 5), "theta": v[1], "n": v[2]}) for k, v in sel.items()},
                                     "results": results, "primary_family_for_holm": primary})
for sid, b in bets.items():
    if len(b):
        bb = b.copy(); bb["cluster"] = bb.cluster.astype(str)
        write_df(bb, f"bets_{sid}.csv")
print(json.dumps({s: {k: results[s].get(k) for k in ("n_bets", "roi", "tier", "holm_adjusted_p")} for s in results}, indent=1))
print("luck:", json.dumps(luck))
print("03_backtest done.")
