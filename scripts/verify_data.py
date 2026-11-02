#!/usr/bin/env python3
"""Independent consistency checks on the transcribed official data.
Exit code 1 if any check fails.  Writes data/verification_report.json.
These checks do NOT replace line-by-line comparison with nba.com; they prove the
transcription is internally consistent across *different* nba.com pages
(standings page vs stats page vs per-game scoreboard pages)."""
import csv, json, os, sys, collections
D=os.path.join(os.path.dirname(__file__),"..","data")
rd=lambda n:list(csv.DictReader(open(os.path.join(D,n))))
checks=[]
def chk(name,ok,detail=""):
    checks.append({"check":name,"pass":bool(ok),"detail":detail})
teams=[t['abbr'] for t in rd('teams.csv')]
chk("30 distinct teams",len(set(teams))==30)
games=rd('games_2026-27.csv')
chk("games: unique game_id",len({g['game_id'] for g in games})==len(games),f"{len(games)} games")
# --- 1. games -> team stats 2026-27
agg=collections.defaultdict(lambda:dict(gp=0,w=0,pf=0,pa=0,hw=0,hl=0,rw=0,rl=0))
for g in games:
    a,h=g['away'],g['home'];ap,hp=int(g['away_pts']),int(g['home_pts'])
    for t,pf,pa,home in((a,ap,hp,0),(h,hp,ap,1)):
        x=agg[t];x['gp']+=1;x['pf']+=pf;x['pa']+=pa
        win=pf>pa;x['w']+=win
        k=('h' if home else 'r')+('w' if win else 'l');x[k]+=1
bad=[];ptsdiff={}
for r in rd('team_stats_2026-27.csv'):
    t=r['abbr'];x=agg[t]
    ok=(x['gp']==int(r['GP']) and x['w']==int(r['W']) and x['gp']-x['w']==int(r['L'])
        and abs((x['pf']-x['pa'])/x['gp']-float(r['plus_minus_per_game']))<0.051)
    if not ok:bad.append((t,x,r))
    d=x['pf']/x['gp']-float(r['PTS_per_game'])
    if abs(d)>=0.051:ptsdiff[t]=round(d,2)
chk("game-level data reproduces official 2026-27 team table (GP, W, L, +/- per game) for all 30 teams",not bad,str(bad)[:300])
# PTS/g: known, FLAGGED discrepancies (see data/flags.csv F-03). Any *new* mismatch fails.
chk("game-level PTS/g equals official stats page for 28/30 teams; DAL and ATL differ slightly (flagged, unresolved)",set(ptsdiff)<={'DAL','ATL'} and len(ptsdiff)==2,f"games minus stats page, pts/g: {ptsdiff}")
# --- 2. standings 26-27
bad=[]
ts={r['abbr']:r for r in rd('team_stats_2026-27.csv')}
for r in rd('standings_2026-27.csv'):
    t=r['abbr'];x=agg[t]
    hw,hl=map(int,r['home_W-L'].split('-'));rw,rl=map(int,r['road_W-L'].split('-'))
    if not(int(r['W'])==int(ts[t]['W']) and int(r['L'])==int(ts[t]['L']) and (hw,hl,rw,rl)==(x['hw'],x['hl'],x['rw'],x['rl'])):
        bad.append((t,r['home_W-L'],r['road_W-L'],x))
chk("2026-27 standings W-L and home/road splits equal split recomputed from game-level data (30 teams)",not bad,str(bad)[:300])
# --- 3. standings 25-26
bad=[];tsp={r['abbr']:r for r in rd('team_stats_2025-26.csv')};hm={r['abbr']:r for r in rd('team_stats_2025-26_home.csv')}
sh=0;shg=0;hw_tot=0
for r in rd('standings_2025-26.csv'):
    t=r['abbr'];W,L=int(r['W']),int(r['L'])
    hw,hl=map(int,r['home_W-L'].split('-'));rw,rl=map(int,r['road_W-L'].split('-'));nw,nl=map(int,r['neutral_W-L'].split('-'))
    if not(W+L==82 and hw+rw+nw==W and hl+rl+nl==L and W==int(tsp[t]['W']) and L==int(tsp[t]['L'])
           and hw==int(hm[t]['W']) and hl==int(hm[t]['L']) and int(hm[t]['GP'])==hw+hl):
        bad.append(t)
chk("2025-26: W+L=82; home+road+neutral = overall; standings = stats-page W-L; home split on stats page = standings home record (30 teams)",not bad,str(bad))
# --- 4. zero-sum checks (league points for = points against)
for nm,fn,tol in(("2025-26 all-games +/- sums to ~0 (tol = 3 sd of rounding noise)","team_stats_2025-26.csv",3*0.0289*82*30**.5),
                 ("2026-27 +/- GP-weighted sums to ~0","team_stats_2026-27.csv",3*0.0289*6.5*30**.5)):
    rows=rd(fn);s=sum(float(r['plus_minus_per_game'])*int(r['GP']) for r in rows)
    chk(nm,abs(s)<=tol,f"sum(GP*+/-)={s:.1f}, tol={tol:.1f}")
rows=rd('team_stats_2025-26_home.csv');s=sum(float(r['plus_minus_per_game'])*int(r['GP']) for r in rows)
chk("2025-26 home +/-: GP-weighted league mean is the home-court margin (informational)",True,f"{s/sum(int(r['GP']) for r in rows):.3f} pts/game over {sum(int(r['GP']) for r in rows)} home games")
# --- 5. slate
sl=rd('slate_2026-11-02.csv');tm=[x for g in sl for x in(g['away'],g['home'])]
chk("slate: 15 games, each of the 30 teams exactly once",len(sl)==15 and sorted(tm)==sorted(teams))
ids=sorted(int(g['game_id']) for g in sl)
chk("slate: game ids contiguous 0022600158..172",ids==list(range(22600158,22600173)))
rep={"passed":sum(c['pass'] for c in checks),"total":len(checks),"checks":checks}
json.dump(rep,open(os.path.join(D,'verification_report.json'),'w'),indent=1)
for c in checks:print(("PASS" if c['pass'] else "FAIL"),c['check'],c['detail'][:150])
sys.exit(0 if all(c['pass'] for c in checks) else 1)
