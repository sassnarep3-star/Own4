#!/usr/bin/env python3
"""NFL Intelligence engine — computes metrics from VERIFIED transcribed official data.
stdlib only. Inputs: nfl-intel/data/standings_2026-11-12.json, week10_2026.json
Outputs: nfl-intel/data/metrics.json, correlations.json, own_lines.json
Pre-registered 2026-11-12 BEFORE Week 10 games are played (see git history)."""
import json, math, sys

SRC_STAND = "https://www.nfl.com/standings/"
SRC_SCORES = "https://www.nfl.com/scores"
PYTHAG_EXP = 2.37   # Literature constant (Pythagorean expectation, NFL) — NOT an official NFL value; flagged UNVERIFIED
MARGIN_SIGMA = 13.45  # Historical NFL margin stdev (literature) — NOT an official NFL value; flagged UNVERIFIED

def load(p):
    with open(p) as f: return json.load(f)

def beta_reg(x, a, b):
    """Regularized incomplete beta I_x(a,b) — Numerical Recipes."""
    if x <= 0: return 0.0
    if x >= 1: return 1.0
    MAXIT, EPS, FPMIN = 300, 3e-14, 1e-300
    bt = math.exp(math.lgamma(a+b)-math.lgamma(a)-math.lgamma(b)+a*math.log(x)+b*math.log(1-x))
    if x < (a+1)/(a+b+2):
        # continued fraction from the left
        ap, bq, c = a, 1.0, 1.0
        d = 1.0 - (a+b)*x/(a+1)
        if abs(d) < FPMIN: d = FPMIN
        d = 1.0/d; h = d
        for m in range(1, MAXIT+1):
            m2 = 2*m
            aa = m*(b-m)*x/((a+m2-1)*(a+m2))
            d = 1.0+aa*d
            if abs(d) < FPMIN: d = FPMIN
            c = 1.0+aa/c
            if abs(c) < FPMIN: c = FPMIN
            d = 1.0/d; h *= d*c
            aa = -(a+m)*(a+b+m)*x/((a+m2)*(a+m2+1))
            d = 1.0+aa*d
            if abs(d) < FPMIN: d = FPMIN
            c = 1.0+aa/c
            if abs(c) < FPMIN: c = FPMIN
            d = 1.0/d; de = d*c; h *= de
            if abs(de-1.0) < EPS: break
        return bt*h/a
    else:
        return 1.0 - beta_reg(1-x, b, a)

def t_sf_two(t, df):
    x = df/(df+t*t)
    return beta_reg(x, df/2, 0.5)  # two-tailed p for |t|

def pearson(xs, ys):
    n = len(xs); mx = sum(xs)/n; my = sum(ys)/n
    sxy = sum((x-mx)*(y-my) for x,y in zip(xs,ys))
    sxx = sum((x-mx)**2 for x in xs); syy = sum((y-my)**2 for y in ys)
    r = sxy/math.sqrt(sxx*syy)
    df = n-2
    t = abs(r)*math.sqrt(df/(1-r*r)) if r*r < 1 else float('inf')
    p = t_sf_two(t, df)
    return r, t, p, df

def benjamini_hochberg(pvals):
    n = len(pvals); order = sorted(range(n), key=lambda i: pvals[i])
    q = [None]*n; prev = 1.0
    for rank, i in enumerate(reversed(order), start=1):
        k = n-rank+1
        val = min(prev, pvals[i]*n/k)
        q[i] = min(val, 1.0); prev = val
    return q

def main():
    stand = load('nfl-intel/data/standings_2026-11-12.json')['teams']
    week10 = load('nfl-intel/data/week10_2026.json')

    # ---- G1-style internal consistency gate (transcribed data self-consistency)
    errs = []
    W = sum(t['w'] for t in stand); L = sum(t['l'] for t in stand)
    PF = sum(t['pf'] for t in stand); PA = sum(t['pa'] for t in stand)
    if W != L: errs.append(f"wins {W} != losses {L}")
    if PF != PA: errs.append(f"PF {PF} != PA {PA}")
    for t in stand:
        if t['net'] != t['pf']-t['pa']: errs.append(f"{t['team']} net mismatch")
        gp = t['w']+t['l']+t['t']
        exp_pct = (t['w']+0.5*t['t'])/gp
        if abs(t['pct']-exp_pct) > 0.001: errs.append(f"{t['team']} pct mismatch")
    if errs:
        print("CONSISTENCY GATE FAILED:", errs); sys.exit(1)
    print(f"consistency gate PASS (W=L={W}, PF=PA={PF})")

    # ---- metrics
    lg_ppg = PF/sum(t['w']+t['l']+t['t'] for t in stand)  # per team-game
    metrics = []
    for t in stand:
        gp = t['w']+t['l']+t['t']
        off, deff = t['pf']/gp, t['pa']/gp
        pyth = (t['pf']**PYTHAG_EXP)/((t['pf']**PYTHAG_EXP)+(t['pa']**PYTHAG_EXP))
        metrics.append({**t, 'gp':gp, 'off_ppg':round(off,2), 'def_ppg':round(deff,2),
                        'net_ppg':round(off-deff,2), 'pythag':round(pyth,3),
                        'pythag_wins':round(pyth*gp,2), 'luck_delta':round((t['w']+0.5*t['t'])-pyth*gp,2),
                        'source_url':SRC_STAND})
    with open('nfl-intel/data/metrics.json','w') as f:
        json.dump({'meta':{'title':'Per-team metrics derived from verified official standings (2026-11-12)',
                            'source_url':SRC_STAND,'pythag_exp':PYTHAG_EXP,
                            'pythag_exp_note':'Literature constant, UNVERIFIED (not an official NFL value)',
                            'league_ppg_per_team':round(lg_ppg,2)}, 'teams':metrics}, f, indent=2)

    # ---- correlations (n=32, descriptive only)
    by = {t['team']: t for t in metrics}
    gp_of = lambda t: t['gp']
    arr = lambda key: [m[key] for m in metrics]
    pairs = [
        ('net_ppg','pct','Point differential per game vs win percentage'),
        ('off_ppg','pct','Points for per game vs win percentage'),
        ('def_ppg','pct','Points against per game vs win percentage'),
        ('off_ppg','def_ppg','Points for per game vs points against per game'),
        ('off_ppg','net_ppg','Points for per game vs point differential per game'),
        ('def_ppg','net_ppg','Points against per game vs point differential per game'),
    ]
    pvals=[]; results=[]
    for a,b,label in pairs:
        r,tstat,p,df = pearson(arr(a),arr(b))
        pvals.append(p)
        results.append({'x':a,'y':b,'label':label,'n':32,'r':round(r,4),'t':round(tstat,4),'df':df,'p':round(p,6),'source_url':SRC_STAND})
    q = benjamini_hochberg(pvals)
    for i,res in enumerate(results):
        res['bh_q'] = round(q[i],6)
        res['fdr_survives_0.05'] = bool(q[i] < 0.05)
    with open('nfl-intel/data/correlations.json','w') as f:
        json.dump({'meta':{'title':'Descriptive correlations (n=32, 2026 season to date)',
                            'note':'Descriptive, in-sample, season-to-date. NOT predictive validation. Multiple testing: Benjamini–Hochberg across 6 tests. p from Student-t (df=30).',
                            'source_url':SRC_STAND}, 'correlations':results}, f, indent=2)

    # ---- originated Week 10 lines (model v1, pre-registered)
    tmap = {m['team']: m for m in metrics}
    lines=[]
    for g in week10['games']:
        h,a = tmap[g['home']], tmap[g['away']]
        exp_home = (h['off_ppg'] + a['def_ppg'])/2
        exp_away = (a['off_ppg'] + h['def_ppg'])/2
        margin = exp_home - exp_away
        total = exp_home + exp_away
        p_home = 0.5*(1+math.erf(margin/(MARGIN_SIGMA*math.sqrt(2))))
        p_home = min(max(p_home,0.001),0.999)
        def ml(p):
            return round(-100*p/(1-p)) if p>=0.5 else round(100*(1-p)/p)
        lines.append({**g, 'exp_home_pts':round(exp_home,2), 'exp_away_pts':round(exp_away,2),
                      'fair_margin_home':round(margin,2), 'fair_total':round(total,2),
                      'p_home_win':round(p_home,4), 'fair_ml_home':ml(p_home), 'fair_ml_away':ml(1-p_home),
                      'pythag_home':round((h['pf']**PYTHAG_EXP)/((h['pf']**PYTHAG_EXP)+(h['pa']**PYTHAG_EXP)),3),
                      'pythag_away':round((a['pf']**PYTHAG_EXP)/((a['pf']**PYTHAG_EXP)+(a['pa']**PYTHAG_EXP)),3),
                      'source_url':SRC_SCORES, 'model':'v1-pythag-netPPG-2026-11-12',
                      'status':'ORIGINATED — no market comparison available (G7 blocked); informational only'})
    with open('nfl-intel/data/own_lines.json','w') as f:
        json.dump({'meta':{'title':'Originated Week 10 2026 fair lines (model v1)',
                            'model':'exp_home=(home_off+away_def_allowed)/2; exp_away=(away_off+home_def_allowed)/2; fair_margin=exp_home-exp_away; fair_total=exp_home+exp_away; P(home)=Normal(margin, 13.45); no explicit HFA term (embedded in season PF/PA); neutral site (W10-02) unchanged by construction.',
                            'assumptions':['Pythagorean exponent 2.37 — UNVERIFIED literature constant','Margin sigma 13.45 — UNVERIFIED literature constant','No injury adjustment applied (backup identity unverified — see injuries page)','No market/odds comparison: no official operator line source exists; every row UNVERIFIED vs market'],
                            'pre_registered':'Committed 2026-11-12 before Week 10 games conclude; see git history.',
                            'source_url':SRC_SCORES}, 'games':lines}, f, indent=2)

    print("league PPG/team:", round(lg_ppg,2))
    for c in results: print(f"r({c['x']},{c['y']})={c['r']:+.3f} p={c['p']:.4g} q={c['bh_q']:.4g} FDR<.05={c['fdr_survives_0.05']}")
    print("lines originated for", len(lines), "games")

if __name__=='__main__': main()
