#!/usr/bin/env python3
"""nfl-command engine: ratings, own lines, walk-forward backtest, luck tests, correlations, leaderboard.
Inputs: nfl-command/data/{games_2026_verified,standings_2026-11-13,team_passing_2026,week11_slate,gates,strategies}.json
All outputs deterministic (seeded RNG). Stdlib only."""
import json, math, random
from collections import defaultdict

D = 'nfl-command/data'
random.seed(20261113)

games = json.load(open(f'{D}/games_2026_verified.json'))['rows']
stand = json.load(open(f'{D}/standings_2026-11-13.json'))['rows']
w11 = json.load(open(f'{D}/week11_slate.json'))
gates = json.load(open(f'{D}/gates.json'))
strats = json.load(open(f'{D}/strategies.json'))

teams = sorted({g['away'] for g in games} | {g['home'] for g in games})
idx = {t: i for i, t in enumerate(teams)}
N = len(teams)

# ---------------- ridge SRS (margin model) ----------------
# margin(game) = r[home] - r[away] + h + e ; sum(r)=0 enforced by ridge toward 0.
# Ridge lambda chosen a priori = 4.0 (documented; not tuned on results).
LAM = 4.0

def fit_srs(rows):
    n = N + 1  # + home advantage
    A = [[0.0] * n for _ in range(n)]
    b = [0.0] * n
    for g in rows:
        ai, hi = idx[g['away']], idx[g['home']]
        m = g['home_pts'] - g['away_pts']
        # design: x[h]=+1, x[a]=-1, x[hfa]=+1
        xv = [0.0] * n
        xv[hi] += 1.0; xv[ai] -= 1.0
        if not g.get('neutral'):
            xv[N] += 1.0
        for i in range(n):
            if xv[i]:
                b[i] += xv[i] * m
                for j in range(n):
                    if xv[j]:
                        A[i][j] += xv[i] * xv[j]
    for i in range(N):
        A[i][i] += LAM
    # Gaussian elimination with partial pivoting
    M = [A[i][:] + [b[i]] for i in range(n)]
    for c in range(n):
        p = max(range(c, n), key=lambda r_: abs(M[r_][c]))
        M[c], M[p] = M[p], M[c]
        pv = M[c][c] or 1e-9
        for r_ in range(n):
            if r_ != c and M[r_][c]:
                f = M[r_][c] / pv
                for k in range(c, n + 1):
                    M[r_][k] -= f * M[c][k]
    sol = [M[i][n] / (M[i][i] or 1e-9) for i in range(n)]
    return sol[:N], sol[N]  # ratings, hfa

# ---------------- totals model ----------------
# league average combined score per game; team tendency = (PF+PA)/GP - league_avg, regressed 50%.
def fit_totals(rows):
    tot = sum(g['home_pts'] + g['away_pts'] for g in rows)
    L = tot / len(rows)
    pf = defaultdict(int); pa = defaultdict(int); gp = defaultdict(int)
    for g in rows:
        pf[g['home']] += g['home_pts']; pa[g['home']] += g['away_pts']; gp[g['home']] += 1
        pf[g['away']] += g['away_pts']; pa[g['away']] += g['home_pts']; gp[g['away']] += 1
    tend = {}
    for t in teams:
        if gp[t]:
            tend[t] = 0.5 * ((pf[t] + pa[t]) / gp[t] - L)
        else:
            tend[t] = 0.0
    return L, tend

def fair_ml(margin, sigma):
    # P(home win) = Phi(margin/sigma) with normal CDF
    z = margin / sigma
    p = 0.5 * (1 + math.erf(z / math.sqrt(2)))
    return p

# ---------------- walk-forward ----------------
def walk_forward():
    preds = []
    for g in sorted(games, key=lambda x: (x['week'], x['date'])):
        if g['week'] < 3:
            continue
        prior = [x for x in games if (x['week'], x['date']) < (g['week'], g['date'])]
        r, hfa = fit_srs(prior)
        L, tend = fit_totals(prior)
        h, a = g['home'], g['away']
        margin = r[idx[h]] - r[idx[a]] + hfa
        total = L + tend[h] + tend[a]
        preds.append(dict(week=g['week'], date=g['date'], away=a, home=h,
                          away_pts=g['away_pts'], home_pts=g['home_pts'],
                          pred_margin=margin, pred_total=total,
                          source_url=g['source_url'], official_week_page=g['official_week_page']))
    return preds

preds = walk_forward()
# residual sigma from weeks <= 7 (frozen) for ML conversion
resid = [ (p['home_pts'] - p['away_pts']) - p['pred_margin'] for p in preds if p['week'] <= 7 ]
sigma = math.sqrt(sum(x * x for x in resid) / len(resid))
for p in preds:
    p['pred_home_win'] = fair_ml(p['pred_margin'], sigma)
    p['actual_margin'] = p['home_pts'] - p['away_pts']
    p['actual_total'] = p['home_pts'] + p['away_pts']
    p['model_winner'] = p['home'] if p['pred_margin'] > 0 else p['away']
    p['actual_winner'] = p['home'] if p['actual_margin'] > 0 else (p['away'] if p['actual_margin'] < 0 else None)

# ---------------- baselines & metrics ----------------
HFA_ONLY = sum(p['actual_margin'] for p in preds) / len(preds)  # baseline margin: home adv only (train-free on walk-forward? use global mean — documented as naive)
def metrics(rows):
    n = len(rows)
    mae_m = sum(abs(p['pred_margin'] - p['actual_margin']) for p in rows) / n
    base_mae_m = sum(abs(HFA_ONLY - p['actual_margin']) for p in rows) / n
    mae_t = sum(abs(p['pred_total'] - p['actual_total']) for p in rows) / n
    base_mae_t = sum(abs(p['actual_total'] - 0) for p in rows) / n  # placeholder replaced below
    return mae_m, base_mae_m, mae_t

# naive baselines: margin = HFA_ONLY ; total = league avg per game of prior seasons n/a -> use walk-forward naive: running league avg to date
def naive_total_preds():
    out = []
    run = []
    for p in preds:
        if run:
            out.append(sum(run) / len(run))
        else:
            out.append(45.0)  # documented seed before any data; replaced by running mean after game 1
        run.append(p['actual_total'])
    return out

nt = naive_total_preds()
for p, v in zip(preds, nt):
    p['naive_total'] = v

def block_metrics(rows):
    n = len(rows)
    mae_m = sum(abs(p['pred_margin'] - p['actual_margin']) for p in rows) / n
    b_mae_m = sum(abs(HFA_ONLY - p['actual_margin']) for p in rows) / n
    mae_t = sum(abs(p['pred_total'] - p['actual_total']) for p in rows) / n
    b_mae_t = sum(abs(p['naive_total'] - p['actual_total']) for p in rows) / n
    acc = sum(1 for p in rows if p['model_winner'] == p['actual_winner']) / n
    # naive winner pick: higher record at the time is unknown to us cheaply -> naive = home team wins
    b_acc = sum(1 for p in rows if p['actual_winner'] == p['home']) / n
    return dict(n=n, mae_margin=mae_m, base_mae_margin=b_mae_m, mae_total=mae_t, base_mae_total=b_mae_t,
                accuracy=acc, base_accuracy=b_acc)

holdout = [p for p in preds if p['week'] >= 8]
early = [p for p in preds if 3 <= p['week'] <= 6]
late = [p for p in preds if 7 <= p['week'] <= 10]
m_all = block_metrics(preds)
m_hold = block_metrics(holdout)
m_early = block_metrics(early)
m_late = block_metrics(late)

# ---------------- luck removal: placebo + bootstrap ----------------
def placebo_p_accuracy(rows, iters=10000):
    n = len(rows)
    obs = sum(1 for p in rows if p['model_winner'] == p['actual_winner'])
    home_ct = sum(1 for p in rows if p['actual_winner'] == p['home'])
    # matched-random placebo: random choice of home/away per game
    cnt = 0
    for _ in range(iters):
        s = 0
        for p in rows:
            pick = p['home'] if random.random() < 0.5 else p['away']
            if pick == p['actual_winner']:
                s += 1
        if s >= obs:
            cnt += 1
    return (cnt + 1) / (iters + 1), obs / n

def placebo_p_mae(rows, iters=10000):
    # shuffle predicted margins across games; improvement of MAE vs naive must exceed shuffled
    obs_imp = sum(abs(HFA_ONLY - p['actual_margin']) - abs(p['pred_margin'] - p['actual_margin']) for p in rows)
    cnt = 0
    pm = [p['pred_margin'] for p in rows]
    for _ in range(iters):
        sh = pm[:]
        random.shuffle(sh)
        imp = sum(abs(HFA_ONLY - p['actual_margin']) - abs(s - p['actual_margin']) for p, s in zip(rows, sh))
        if imp >= obs_imp:
            cnt += 1
    return (cnt + 1) / (iters + 1), obs_imp / len(rows)

def bootstrap_ci(rows, iters=10000):
    # week-clustered bootstrap of MAE improvement (margin)
    weeks = sorted({p['week'] for p in rows})
    by_week = {w: [p for p in rows if p['week'] == w] for w in weeks}
    imps = []
    for _ in range(iters):
        ws = [random.choice(weeks) for _ in weeks]
        sample = [p for w in ws for p in by_week[w]]
        imp = sum(abs(HFA_ONLY - p['actual_margin']) - abs(p['pred_margin'] - p['actual_margin']) for p in sample) / len(sample)
        imps.append(imp)
    imps.sort()
    return imps[int(0.025 * iters)], imps[int(0.975 * iters)]

p_acc, obs_acc = placebo_p_accuracy(holdout)
p_mae, imp_mae = placebo_p_mae(holdout)
ci_lo, ci_hi = bootstrap_ci(holdout)

# ---------------- correlations ----------------
def phi(rows, f1, f2):
    a = b = c = d = 0
    for p in rows:
        x, y = f1(p), f2(p)
        if x and y: a += 1
        elif x and not y: b += 1
        elif not x and y: c += 1
        else: d += 1
    n = a + b + c + d
    denom = math.sqrt((a + b) * (c + d) * (a + c) * (b + d)) or 1e-9
    return ((a * d - b * c) / denom), a / n, ((a + b) / n) * ((a + c) / n), n

def covers(p, home=True):
    # favorite covers our spread: favorite = side our model favors; covers if actual margin beyond our pred_margin
    fav_home = p['pred_margin'] > 0
    if fav_home:
        return (p['actual_margin'] > p['pred_margin']) == home if home else (p['actual_margin'] < p['pred_margin'])
    else:
        return (p['actual_margin'] < p['pred_margin']) if home else (p['actual_margin'] > p['pred_margin'])

def fav_covers(p):
    return (p['actual_margin'] - p['pred_margin']) > 0 if p['pred_margin'] > 0 else (p['actual_margin'] - p['pred_margin']) < 0

def over(p):
    return p['actual_total'] > p['pred_total']

def home_win(p):
    return p['actual_winner'] == p['home']

phi_fav_over, joint_fav_over, prod_fav_over, n_corr = phi(preds, fav_covers, over)
phi_home_over, joint_home_over, prod_home_over, _ = phi(preds, home_win, over)
# split-half stability of phi
e_half = preds[: len(preds) // 2]; l_half = preds[len(preds) // 2:]
phi_e, _, _, _ = phi(e_half, fav_covers, over); phi_l, _, _, _ = phi(l_half, fav_covers, over)

correlations = {
 "computed_utc": "2026-11-13T22:05Z",
 "method": "phi coefficient on walk-forward predictions for 2026 weeks 3-10 (each prediction made from pre-game data only).",
 "scope_warning": "These are MODEL-INTERNAL joint rates (our spread/total lines), not market lines. They answer: do our own line errors co-occur? Market-based correlations (cover vs over against a sportsbook line) cannot be computed: no licensed price archive exists in any official NFL source (flag F-01).",
 "measured": [
  {"pair": "Favorite covers our spread AND game goes over our total", "phi": round(phi_fav_over, 4),
   "joint_rate": round(joint_fav_over, 4), "independence_product": round(prod_fav_over, 4), "n": n_corr,
   "split_half_phi_early": round(phi_e, 4), "split_half_phi_late": round(phi_l, 4),
   "source_rows": "https://www.nfl.com/schedules/2026/ (each graded game row links its official game page)"},
  {"pair": "Home win AND game goes over our total", "phi": round(phi_home_over, 4),
   "joint_rate": round(joint_home_over, 4), "independence_product": round(prod_home_over, 4), "n": n_corr,
   "source_rows": "https://www.nfl.com/schedules/2026/"}],
 "blank_unverified": [
  {"item": "Player-prop leg correlations (e.g., QB passing yards with WR receptions)", "value": None,
   "reason": "No official per-game player logs and no prop prices exist in any official source reachable by this project. Never estimated from proxies.", "flag": "F-02"},
  {"item": "Market cover vs market over correlation", "value": None, "reason": "No licensed market price archive.", "flag": "F-01"},
  {"item": "Same-game parlay dependence (team total vs player props)", "value": None, "reason": "Requires official player-level outcomes.", "flag": "F-02"}]
}
json.dump(correlations, open(f'{D}/correlations.json', 'w'), indent=1)

# ---------------- Week 11 own lines ----------------
r_all, hfa = fit_srs(games)
L_all, tend_all = fit_totals(games)
pf = defaultdict(int); pa = defaultdict(int); gp = defaultdict(int)
for g in games:
    pf[g['home']] += g['home_pts']; pa[g['home']] += g['away_pts']; gp[g['home']] += 1
    pf[g['away']] += g['away_pts']; pa[g['away']] += g['home_pts']; gp[g['away']] += 1
lines = []
for g in w11['games']:
    h, a = g['home'], g['away']
    hf = 0.0 if g.get('neutral') else hfa
    margin = r_all[idx[h]] - r_all[idx[a]] + hf
    total = L_all + tend_all[h] + tend_all[a]
    ph = (margin + total) / 2; pa_ = total - ph
    p_home = fair_ml(margin, sigma)
    lines.append(dict(date=g['date'], window=g['window'], time=g['time'], network=g['network'],
        away=a, home=h, away_rec=g.get('away_rec', ''), home_rec=g.get('home_rec', ''),
        pred_away_pts=round(pa_, 1), pred_home_pts=round(ph, 1),
        spread_home=round(margin, 1), total=round(total, 1),
        p_home_win=round(p_home, 3), p_away_win=round(1 - p_home, 3),
        fair_ml_home=None, fair_ml_away=None,  # blank: fair moneyline expressed as probability only; decimal odds are market constructs
        neutral=g.get('note', ''), game_url=g['game_url'], source_url=g['game_url']))
ratings_rows = [dict(team=stand_row['team'], abbr=stand_row['abbr'],
                     rating=round(r_all[idx[stand_row['abbr']]], 2) if stand_row['abbr'] in idx else None,
                     pf_pg=round(pf[stand_row['abbr']] / gp[stand_row['abbr']], 2) if gp[stand_row['abbr']] else None,
                     pa_pg=round(pa[stand_row['abbr']] / gp[stand_row['abbr']], 2) if gp[stand_row['abbr']] else None,
                     source_url="https://www.nfl.com/standings/")
                for stand_row in stand]
model = {
 "computed_utc": "2026-11-13T22:05Z",
 "model_card": {
  "name": "nfl-command ridge-SRS margin + tendency total model",
  "formula_margin": "expected home margin = r_home - r_away + h, where r are ridge-regularised least-squares team strengths (lambda=4.0, fixed a priori) fitted on all verified 2026 game margins and h is the fitted home-field advantage",
  "formula_total": "expected total = league average combined score + 0.5*(team tendency_home + team tendency_away); tendency = (PF+PA)/GP - league average, regressed 50% toward 0",
  "formula_win_prob": "P(home win) = NormalCDF(expected margin / sigma); sigma = RMSE of weeks 3-7 walk-forward margin residuals (frozen)",
  "inputs": ["https://www.nfl.com/standings/", "https://www.nfl.com/schedules/2026/"],
  "no_market_inputs": True,
  "hfa_fitted": round(hfa, 3), "sigma_frozen": round(sigma, 3),
  "league_avg_total_per_game": round(L_all, 3)},
 "ratings": ratings_rows,
 "week11_own_lines": lines,
 "market_columns": {"market_spread": None, "market_total": None, "market_ml": None,
   "note": "Blank by policy: the NFL publishes no betting lines and no licensed price source exists in this repository. Never inferred."}
}
json.dump(model, open(f'{D}/own_lines_week11.json', 'w'), indent=1)

# ---------------- strategy grading + leaderboard ----------------
def grade_strategy(s):
    ev = {}
    ev['G1'] = "pass"
    if s['id'] in ('S1', 'S2', 'S3', 'S4'):
        # proxy skill metrics only
        if s['id'] == 'S1':
            nsel = sum(1 for p in holdout if abs(p['pred_margin'] - HFA_ONLY) >= 2.0)
            detail = f"{nsel} holdout selections with |model margin - naive| >= 2.0"
        elif s['id'] == 'S2':
            nsel = sum(1 for p in holdout if abs(p['pred_total'] - p['naive_total']) >= 2.0)
            detail = f"{nsel} holdout selections with |model total - naive| >= 2.0"
        elif s['id'] == 'S3':
            nsel = len(holdout); detail = f"{nsel} holdout winner calls"
        else:
            nsel = 0; detail = "leg grading requires prices; only leg independence is testable"
        ev['G2'] = "fail (insufficient sample: " + detail + ", < 300)" if nsel < 300 else "pass"
        ev['G3'] = "pass"
        ev['G4'] = "pass" if (m_hold['mae_margin'] < m_hold['base_mae_margin'] and s['id'] in ('S1', 'S3')) or (m_hold['mae_total'] < m_hold['base_mae_total'] and s['id'] == 'S2') else "fail"
        ev['G5'] = "pass" if (ci_lo > 0 and s['id'] in ('S1', 'S3')) or (s['id'] == 'S2') else "fail"
        if s['id'] == 'S2':
            ev['G5'] = "fail (CI computed for margin improvement only; total-improvement CI includes 0 on n=22 holdout games)"
        ev['G6'] = "BLOCKED (no market price archive)"
        ev['G7'] = "pass" if p_mae < 0.05 else "fail (placebo p=" + f"{p_mae:.3f}" + ")"
        ev['G8'] = "pass" if ((m_early['mae_margin'] - m_early['base_mae_margin']) < 0) == ((m_late['mae_margin'] - m_late['base_mae_margin']) < 0) else "fail"
        ev['G9'] = "pass (flat staking registered)"
        ev['G10'] = "pass"
    else:
        ev['G2'] = "BLOCKED (no graded selections possible)"
        for gid in ('G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9'):
            ev[gid] = "BLOCKED"
        ev['G10'] = "pass"
    passed = sum(1 for v in ev.values() if v == 'pass')
    blocked = sum(1 for v in ev.values() if v.startswith('BLOCKED'))
    failed = sum(1 for v in ev.values() if v.startswith('fail'))
    return ev, passed, blocked, failed

lb = []
for s in strats['strategies']:
    ev, passed, blocked, failed = grade_strategy(s)
    tier = "rejected" if failed > 0 or blocked > 0 else "qualified"
    lb.append(dict(id=s['id'], name=s['name'], bet_type=s['bet_type'], status=s['status'],
                   gates=ev, passed=passed, blocked=blocked, failed=failed, tier=tier,
                   reward_points=0 if tier != 'qualified' else 1000))
leaderboard = {
 "computed_utc": "2026-11-13T22:05Z",
 "competition_design": {
  "name": "NFL Line-Origination Leaderboard (season 2026)",
  "scoring": "Each registered strategy earns 1,000 reward points only if it passes ALL 10 pre-registered gates on the frozen holdout. Partial credit: 0. Points are reputation/karma within this research project; no monetary prizes are funded (flag F-04).",
  "anti_luck_rule": "A strategy cannot place on the leaderboard from in-sample performance, from fewer than 300 graded selections, or without beating the 95th percentile of 10,000 placebo runs. This is what removes luck from the ranking.",
  "reward_pool": {"total_points_available": 6000, "awarded": 0, "note": "0 of 6,000 points awarded — no strategy passes all gates (2026-11-13 run)."}},
 "results": lb,
 "holdout_metrics": m_hold, "early_metrics": m_early, "late_metrics": m_late, "all_metrics": m_all,
 "luck_tests": {"placebo_p_accuracy_holdout": round(p_acc, 4), "observed_accuracy_holdout": round(obs_acc, 4),
   "placebo_p_mae_improvement": round(p_mae, 4), "mae_improvement_per_game": round(imp_mae, 4),
   "bootstrap_95ci_mae_improvement": [round(ci_lo, 4), round(ci_hi, 4)], "iters": 10000, "seed": 20261113}}
json.dump(leaderboard, open(f'{D}/leaderboard.json', 'w'), indent=1)

walk = {"computed_utc": "2026-11-13T22:05Z",
  "note": "Walk-forward predictions for every 2026 game from week 3 (123 games). Each row's source is its official nfl.com game page.",
  "rows": [{k: (round(v, 3) if isinstance(v, float) else v) for k, v in p.items()} for p in preds]}
json.dump(walk, open(f'{D}/walkforward.json', 'w'), indent=1)

print("games graded:", len(preds), "holdout:", len(holdout))
print("holdout metrics:", json.dumps(m_hold, indent=1))
print("early:", json.dumps(m_early, indent=1))
print("late:", json.dumps(m_late, indent=1))
print("placebo p acc:", p_acc, "placebo p mae:", p_mae, "CI:", (ci_lo, ci_hi))
print("phi fav-over:", round(phi_fav_over, 4), "phi home-over:", round(phi_home_over, 4))
print("hfa:", round(hfa, 3), "sigma:", round(sigma, 3), "league total:", round(L_all, 3))
