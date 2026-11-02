#!/usr/bin/env python3
"""Walk-forward Elo line-origination engine (pre-registered params v1.0).

- Chronological Elo over all 120 completed 2026 games (pre-game probabilities only).
- Margin scale + baselines fitted on weeks 1-4 ONLY; holdout weeks 5-8 evaluated once.
- Validation gates G1-G8 from nfl-lab/params.json applied per strategy.
- Emits fair moneylines, spreads and totals for the upcoming slate (Week 8 MNF + Week 9).
No market/line source exists officially -> market columns stay blank (G7 blocked).
"""
import csv, json, math, os, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(ROOT, "nfl-lab", "data")
PARAMS = json.load(open(os.path.join(ROOT, "nfl-lab", "params.json")))
P = PARAMS["elo"]
K = P["k"]
HFA = P["home_advantage_elo"]
INIT = P["initial_rating"]

def load(name):
    with open(os.path.join(D, name)) as f:
        return list(csv.DictReader(f))

games = load("games_2026.csv")
for g in games:
    g["week"] = int(g["week"])
    g["ap"], g["hp"] = int(g["away_pts"]), int(g["home_pts"])
    g["neutral"] = g["neutral_site"] == "1"
    g["date"] = datetime.date.fromisoformat(g["date_iso"])
    g["margin"] = g["hp"] - g["ap"]
    g["total"] = g["hp"] + g["ap"]
games.sort(key=lambda g: (g["date"], g["week"], g["game_slug"]))

TRAIN = set(PARAMS["data"]["train_weeks"])
HOLD = set(PARAMS["data"]["holdout_weeks"])

def mov_mult(margin, elo_diff_winner):
    return math.log(1 + abs(margin)) * 2.2 / (2.2 + 0.001 * elo_diff_winner)

def expected(r_home, r_away, hfa):
    d = r_home + hfa - r_away
    return 1.0 / (1.0 + 10 ** (-d / 400.0))

# ---------- walk-forward Elo ----------
ratings = {t: float(INIT) for t in
           ["BUF","MIN","SF","DEN","PIT","CHI","CIN","DET","JAX","KC","NYG","CLE","GB","NE",
            "SEA","BAL","LV","LA","CAR","AZ","ATL","DAL","TB","WAS","HOU","NO","IND","NYJ",
            "PHI","MIA","TEN","LAC"]}
preds = []
for g in games:
    hfa = 0 if g["neutral"] else HFA
    ph = expected(ratings[g["home"]], ratings[g["away"]], hfa)
    preds.append(dict(slug=g["game_slug"], week=g["week"], date=g["date_iso"],
                      home=g["home"], away=g["away"], p_home=round(ph, 5),
                      neutral=g["neutral"], actual=g["home_win"] if "home_win" in g else
                      (1 if g["margin"] > 0 else (0 if g["margin"] < 0 else 0.5))))
    # outcome for Elo (home score)
    hs = 1.0 if g["margin"] > 0 else (0.0 if g["margin"] < 0 else 0.5)
    rh, ra = ratings[g["home"]], ratings[g["away"]]
    exp_h = expected(rh, ra, hfa)
    if g["margin"] == 0:
        ediff = 0.0
    else:
        winner_is_home = g["margin"] > 0
        ediff = (rh - ra + hfa) if winner_is_home else (ra - rh - hfa)
    m = mov_mult(g["margin"], ediff) if g["margin"] != 0 else 1.0
    delta = K * m * (hs - exp_h)
    ratings[g["home"]] += delta
    ratings[g["away"]] -= delta

# attach actual outcomes
for pr, g in zip(preds, games):
    pr["actual"] = 1 if g["margin"] > 0 else (0 if g["margin"] < 0 else 0.5)

# ---------- margin scale fit on weeks 1-4 ----------
best_s, best_sse = None, None
fit = [p for p in preds if p["week"] in TRAIN]
for i in range(1, 61):  # 1.0 .. 30.0 step 0.5
    s = i * 0.5
    sse = 0.0
    for p in fit:
        ph = min(0.999, max(0.001, p["p_home"]))
        pred_m = s * math.log(ph / (1 - ph))
        g = next(x for x in games if x["game_slug"] == p["slug"])
        sse += (pred_m - g["margin"]) ** 2
    if best_sse is None or sse < best_sse:
        best_s, best_sse = s, sse
SCALE = best_s

# ---------- baselines ----------
def pre_wpct(team, upto_slug):
    w = l = t = 0
    for g in games:
        if g["game_slug"] == upto_slug:
            break
        if team in (g["away"], g["home"]):
            if team == g["away"]:
                r = 1 if g["ap"] > g["hp"] else (0 if g["ap"] < g["hp"] else 0.5)
            else:
                r = 1 if g["hp"] > g["ap"] else (0 if g["hp"] < g["ap"] else 0.5)
            if r == 1: w += 1
            elif r == 0: l += 1
            else: t += 1
    n = w + l + t
    return (w + 0.5 * t) / n if n else 0.5

train_home = []
for p in preds:
    if p["week"] in TRAIN:
        train_home.append(p["actual"])
B0 = sum(train_home) / len(train_home)

def b1_p(g):
    return 1.0 / (1.0 + math.exp(-5.0 * (pre_wpct(g["home"], g["game_slug"]) -
                                         pre_wpct(g["away"], g["game_slug"]))))

# ---------- holdout metrics ----------
def metrics(rows):
    # rows: list of (p, y)
    n = len(rows)
    brier = sum((p - y) ** 2 for p, y in rows) / n
    eps = 1e-6
    ll = -sum(y * math.log(max(eps, p)) + (1 - y) * math.log(max(eps, 1 - p)) for p, y in rows) / n
    # ECE 5 equal-count bins
    srt = sorted(rows, key=lambda r: r[0])
    bins = [srt[i * n // 5:(i + 1) * n // 5] for i in range(5)]
    ece = 0.0
    cal = []
    for b in bins:
        if not b:
            continue
        mp = sum(p for p, y in b) / len(b)
        my = sum(y for p, y in b) / len(b)
        ece += len(b) / n * abs(mp - my)
        cal.append(dict(n=len(b), mean_p=round(mp, 4), mean_y=round(my, 4)))
    return dict(n=n, brier=round(brier, 5), log_loss=round(ll, 5),
                ece=round(ece, 4), calibration_bins=cal)

hold_preds = [p for p in preds if p["week"] in HOLD]
m_elo = metrics([(p["p_home"], p["actual"]) for p in hold_preds])
m_b0 = metrics([(B0, p["actual"]) for p in hold_preds])
m_b1 = metrics([(b1_p(next(x for x in games if x["game_slug"] == p["slug"])), p["actual"])
                for p in hold_preds])
train_metrics = metrics([(p["p_home"], p["actual"]) for p in preds if p["week"] in TRAIN])

# S8: Elo + rest filter (rest-advantaged side aligns with Elo side) on holdout
def rest_days_map():
    prev, rd = {}, {}
    for g in games:
        for t in (g["away"], g["home"]):
            rd[(g["game_slug"], t)] = (g["date"] - prev[t]).days if t in prev else None
            prev[t] = g["date"]
    return rd
RD = rest_days_map()
s8_rows = []
for p in hold_preds:
    g = next(x for x in games if x["game_slug"] == p["slug"])
    rh, ra = RD[(g["game_slug"], g["home"])], RD[(g["game_slug"], g["away"])]
    if rh is None or ra is None:
        continue
    diff = rh - ra
    if abs(diff) < 3:
        continue
    # only games where rest side and Elo side agree
    elo_side_home = p["p_home"] >= 0.5
    rest_side_home = diff > 0
    if elo_side_home != rest_side_home:
        continue
    # evaluate Elo probability of the AGREED side
    p_side = p["p_home"] if elo_side_home else 1 - p["p_home"]
    y_side = p["actual"] if elo_side_home else (1 - p["actual"] if p["actual"] in (0, 1) else 0.5)
    s8_rows.append((p_side, y_side))
m_s8 = metrics(s8_rows) if len(s8_rows) >= 5 else dict(n=len(s8_rows), brier=None, log_loss=None,
                                                       ece=None, calibration_bins=[],
                                                       note="too few rows for metrics")

# S4 totals: expected total model on holdout vs baseline (train mean total)
train_totals = [g["total"] for g in games if g["week"] in TRAIN]
BASE_TOT = sum(train_totals) / len(train_totals)
def exp_total(g):
    # priors: season-to-date scoring before this game
    off, gp = {}, {}
    for x in games:
        if x["game_slug"] == g["game_slug"]:
            break
        for t in (x["away"], x["home"]):
            off.setdefault(t, 0)
            gp.setdefault(t, 0)
            pts = x["ap"] if t == x["away"] else x["hp"]
            off[t] += pts
            gp[t] += 1
    def prior(t):
        if gp.get(t, 0) == 0:
            return BASE_TOT / 2
        s = gp[t] / (gp[t] + 4)
        return BASE_TOT / 2 + s * (off[t] / gp[t] - BASE_TOT / 2)
    return BASE_TOT + (prior(g["home"]) - BASE_TOT / 2) + (prior(g["away"]) - BASE_TOT / 2)

s4_rows = []
for g in games:
    if g["week"] in HOLD:
        e = exp_total(g)
        s4_rows.append((e, g["total"]))
mae_model = sum(abs(e - a) for e, a in s4_rows) / len(s4_rows)
mae_base = sum(abs(BASE_TOT - a) for _, a in s4_rows) / len(s4_rows)
bias_model = sum(e - a for e, a in s4_rows) / len(s4_rows)

# ---------- gates ----------
n_hold = m_elo["n"]
gates = {
    "G1_provenance": dict(result="PASS", detail="all inputs carry official nfl.com source URLs; verification_report.json 14/14"),
    "G2_leakage": dict(result="PASS", detail="chronological walk-forward; scale/baselines fitted on weeks 1-4; holdout weeks 5-8 evaluated once after params commit"),
    "G3_sample_size": dict(result="PASS" if n_hold >= 300 else "FAIL",
                           detail=f"holdout n={n_hold}, required >= 300"),
    "G4_baseline": dict(result="PASS" if (m_elo["brier"] < m_b0["brier"] and m_elo["brier"] < m_b1["brier"]) else "FAIL",
                        detail=f"Elo {m_elo['brier']} vs B0 {m_b0['brier']} vs B1 {m_b1['brier']} (holdout Brier)"),
    "G5_calibration": dict(result="PASS" if m_elo["ece"] <= 0.10 else "FAIL",
                           detail=f"holdout ECE(5-bin)={m_elo['ece']} (threshold 0.10)"),
    "G6_registry": dict(result="PASS", detail="strategy_registry.json v1.0 registered before evaluation"),
    "G7_market": dict(result="BLOCKED", detail="no official operator price archive exists; market comparison impossible"),
    "G8_costs": dict(result="BLOCKED", detail="no official operator settlement/limits terms published"),
}
eligible = all(gates[k]["result"] == "PASS" for k in gates)

# ---------- own lines for upcoming slate ----------
up = load("upcoming_2026.csv")
own_lines = []
for u in up:
    home, away = u["home"], u["away"]
    neutral = u["neutral_site"] == "1"
    hfa = 0 if neutral else HFA
    ph = expected(ratings[home], ratings[away], hfa)
    ph = min(0.999, max(0.001, ph))
    pred_m = SCALE * math.log(ph / (1 - ph))  # home margin expectation
    # totals model (priors = all completed games)
    class G:
        pass
    gg = G()
    gg.game_slug = u["game_slug"]
    # build priors directly
    off, gp = {}, {}
    for x in games:
        for t in (x["away"], x["home"]):
            off.setdefault(t, 0); gp.setdefault(t, 0)
            off[t] += x["ap"] if t == x["away"] else x["hp"]
            gp[t] += 1
    def prior(t):
        if gp.get(t, 0) == 0:
            return BASE_TOT / 2
        s = gp[t] / (gp[t] + 4)
        return BASE_TOT / 2 + s * (off[t] / gp[t] - BASE_TOT / 2)
    et = BASE_TOT + (prior(home) - BASE_TOT / 2) + (prior(away) - BASE_TOT / 2)
    # fair (no-vig) decimal moneylines
    ml_home = round(1 / ph, 3)
    ml_away = round(1 / (1 - ph), 3)
    # spread: favorite gives points; express as home line
    if pred_m >= 0:
        spread = f"HOME -{round(pred_m * 2) / 2}"
    else:
        spread = f"HOME +{round(abs(pred_m) * 2) / 2}"
    own_lines.append(dict(
        week=u["week"], date=u["date_iso"], kickoff_et=u["kickoff_et"], network=u["network"],
        away=away, home=home, neutral=neutral, game_slug=u["game_slug"],
        p_home=round(ph, 4), fair_ml_home=ml_home, fair_ml_away=ml_away,
        model_spread=spread, model_home_margin=round(pred_m, 2),
        model_total=round(et * 2) / 2,
        market_spread="", market_total="", market_ml="",  # permanently blank: G7 blocked
        source_url=u["source_url"]))

# ---------- outputs ----------
out_ratings = dict(
    generated_from="nfl-lab/data/games_2026.csv (120 verified games, walk-forward chronological)",
    params="nfl-lab/params.json v1.0",
    ratings={t: round(r, 2) for t, r in sorted(ratings.items(), key=lambda kv: -kv[1])},
)
json.dump(out_ratings, open(os.path.join(D, "model_ratings.json"), "w"), indent=1)
json.dump(dict(params="nfl-lab/params.json v1.0",
               predictions=[{k: p[k] for k in ("slug", "week", "date", "home", "away", "p_home", "neutral", "actual")}
                            for p in preds]),
          open(os.path.join(D, "walkforward_predictions.json"), "w"), indent=1)
json.dump(dict(
    margin_scale_fitted=SCALE, margin_scale_fit_sse=round(best_sse, 2),
    train_weeks=sorted(TRAIN), holdout_weeks=sorted(HOLD),
    B0_constant_p=round(B0, 5),
    holdout=dict(elo=m_elo, B0_constant=m_b0, B1_record_diff=m_b1),
    train_view_elo=train_metrics,
    s8_elo_plus_rest_filter=m_s8,
    totals_holdout=dict(model_mae=round(mae_model, 2), baseline_mae=round(mae_base, 2),
                        model_bias=round(bias_model, 2), baseline_total=round(BASE_TOT, 2),
                        n=len(s4_rows)),
    gates_S1=gates, S1_reward_eligible=eligible,
), open(os.path.join(D, "holdout_metrics.json"), "w"), indent=1)

cols = ["week", "date", "kickoff_et", "network", "away", "home", "neutral", "p_home",
        "fair_ml_away", "fair_ml_home", "model_spread", "model_home_margin", "model_total",
        "market_ml", "market_spread", "market_total", "game_slug", "source_url"]
with open(os.path.join(D, "own_lines_2026.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for row in own_lines:
        w.writerow({c: row[c] for c in cols})

print(f"margin scale (W1-4 fit) = {SCALE}")
print(f"holdout n={n_hold}  Elo Brier={m_elo['brier']}  B0={m_b0['brier']}  B1={m_b1['brier']}  ECE={m_elo['ece']}")
print(f"train-view Elo Brier={train_metrics['brier']} (optimistic; params fitted on train)")
print(f"S8 (Elo+rest align) n={m_s8.get('n')} Brier={m_s8.get('brier')}")
print(f"totals holdout: model MAE={mae_model:.2f} vs baseline MAE={mae_base:.2f} (bias {bias_model:+.2f})")
print("gates:", {k: v["result"] for k, v in gates.items()}, "eligible:", eligible)
print(f"own lines written: {len(own_lines)} upcoming games")
for o in own_lines[:4]:
    print(" ", o["away"], "@", o["home"], "p_home=", o["p_home"], o["model_spread"], "total", o["model_total"])
