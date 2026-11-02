#!/usr/bin/env python3
"""Empirical NFL signal + correlation research from the verified game log.

All inputs are the line-by-line verified csv files (see verify_data.py).
Statistics are computed with the standard library only:
  - Wilson score interval for proportions (95%)
  - Pearson / point-biserial / phi correlations with two-sided t-test p-values
    (regularized incomplete beta for the t distribution)
Pre-registered design: nfl-lab/params.json v1.0, strategies in strategy_registry.json v1.0.
"""
import csv, json, math, os, collections, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(ROOT, "nfl-lab", "data")
Z = 1.959963984540054  # 95%

# ---------- stats helpers ----------
def log_gamma(x):
    c = [76.18009172947146, -86.50532032941677, 24.01409824083091,
         -1.231739572450155, 0.1208650973866179e-2, -0.5395239384953e-5]
    y, tmp = x, x + 5.5
    tmp -= (x + 0.5) * math.log(tmp)
    ser = 1.000000000190015
    for j in range(6):
        ser += c[j] / (x + j + 1)
    return -tmp + math.log(2.5066282746310005 * ser / x)

def betacf(a, b, x):
    MAXIT, EPS, FPMIN = 200, 3e-12, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < FPMIN: d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN: d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN: c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN: d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN: c = FPMIN
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < EPS:
            break
    return h

def betainc(a, b, x):
    if x <= 0: return 0.0
    if x >= 1: return 1.0
    lbeta = log_gamma(a + b) - log_gamma(a) - log_gamma(b) + a * math.log(x) + b * math.log(1 - x)
    if x < (a + 1.0) / (a + b + 2.0):
        return math.exp(lbeta) * betacf(a, b, x) / a
    return 1.0 - math.exp(lbeta) * betacf(b, a, 1.0 - x) / b

def t_two_sided_p(t, df):
    if df <= 0 or not math.isfinite(t):
        return float("nan")
    return betainc(df / 2.0, 0.5, df / (df + t * t))

def wilson(k, n, z=Z):
    if n == 0:
        return (None, None, None)
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (p, max(0.0, center - half), min(1.0, center + half))

def corr(x, y):
    n = len(x)
    if n < 3:
        return dict(n=n, r=None, t=None, p=None)
    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx == 0 or syy == 0:
        return dict(n=n, r=None, t=None, p=None)
    r = sxy / math.sqrt(sxx * syy)
    r = max(-0.9999999, min(0.9999999, r))
    df = n - 2
    t = r * math.sqrt(df / (1 - r * r))
    return dict(n=n, r=round(r, 4), t=round(t, 4), p=round(t_two_sided_p(t, df), 6))

# ---------- load verified data ----------
def load(name):
    with open(os.path.join(D, name)) as f:
        return list(csv.DictReader(f))

games = load("games_2026.csv")
standings = load("standings_2026.csv")
passing = load("team_passing_2026.csv")
for g in games:
    g["week"] = int(g["week"])
    g["ap"], g["hp"] = int(g["away_pts"]), int(g["home_pts"])
    g["neutral"] = g["neutral_site"] == "1"
    g["date"] = datetime.date.fromisoformat(g["date_iso"])
    g["margin"] = g["hp"] - g["ap"]          # home perspective
    g["total"] = g["hp"] + g["ap"]
    g["home_win"] = 1 if g["margin"] > 0 else (0 if g["margin"] < 0 else 0.5)

games.sort(key=lambda g: (g["date"], g["week"], g["game_slug"]))

# rest days per team (days since previous game)
prev_date = {}
rest = {}  # (game_slug, team) -> days or None
for g in games:
    for team in (g["away"], g["home"]):
        prev = prev_date.get(team)
        rest[(g["game_slug"], team)] = (g["date"] - prev).days if prev else None
        prev_date[team] = g["date"]

# previous-game margin per team (momentum feature)
prev_margin = {}
momentum = {}  # (slug, team) -> prev margin (team perspective) or None
for g in games:
    for team in (g["away"], g["home"]):
        m = prev_margin.get(team)
        momentum[(g["game_slug"], team)] = m
        if team == g["away"]:
            prev_margin[team] = g["ap"] - g["hp"]
        else:
            prev_margin[team] = g["hp"] - g["ap"]

signals = []
def sig(sid, name, value, ci, n, source, note=""):
    signals.append(dict(id=sid, name=name, value=value, ci95=ci, n=n, source=source, note=note))

SCHED = "https://www.nfl.com/schedules/2026/by-week/week-8"
STAND = "https://www.nfl.com/standings/league/2026/REG"

# SIG-01 home win, non-neutral
nn = [g for g in games if not g["neutral"]]
k = sum(g["home_win"] for g in nn)
p, lo, hi = wilson(k, len(nn))
sig("SIG-01", "Designated-home win rate (excl. neutral sites)",
    round(p, 4), [round(lo, 4), round(hi, 4)], len(nn), SCHED,
    "ties count as 0.5")

# SIG-01b neutral
neu = [g for g in games if g["neutral"]]
kn = sum(g["home_win"] for g in neu)
pn, lon, hin = wilson(kn, len(neu))
sig("SIG-01b", "Designated-home win rate (international neutral-site games)",
    round(pn, 4), [round(lon, 4), round(hin, 4)], len(neu),
    "https://www.nfl.com/schedules/2026/by-week/week-1",
    "Melbourne, Rio, London x3, Saint-Denis; small n")

# SIG-02 rest buckets (team-games with a prior game)
buckets = {"short": [], "normal": [], "long": []}
for g in games:
    for team in (g["away"], g["home"]):
        r = rest[(g["game_slug"], team)]
        if r is None:
            continue
        if team == g["away"]:
            win = 1 if g["ap"] > g["hp"] else (0 if g["ap"] < g["hp"] else 0.5)
        else:
            win = g["home_win"]
        if r <= 5:
            buckets["short"].append(win)
        elif r <= 8:
            buckets["normal"].append(win)
        else:
            buckets["long"].append(win)
for i, (b, vals) in enumerate([("short", buckets["short"]), ("normal", buckets["normal"]), ("long", buckets["long"])], start=2):
    pp, lo, hi = wilson(sum(vals), len(vals))
    sig(f"SIG-0{i}", f"Win rate on {b} rest (0-5 days)" if b == "short" else
        (f"Win rate on {b} rest (6-8 days)" if b == "normal" else "Win rate on long rest (9+ days incl. bye)"),
        round(pp, 4), [round(lo, 4), round(hi, 4)], len(vals), SCHED,
        "team-games with a prior 2026 game; rest = days since previous game")

# SIG-09/10 margins and totals
absm = [abs(g["margin"]) for g in games]
one_score = sum(1 for m in absm if m <= 7)
sig("SIG-09", "Games decided by <= 7 points (one score)",
    round(one_score / len(games), 4),
    [round(wilson(one_score, len(games))[1], 4), round(wilson(one_score, len(games))[2], 4)],
    len(games), SCHED, f"mean |margin| = {round(sum(absm)/len(absm), 2)} pts")
tot = [g["total"] for g in games]
mt = sum(tot) / len(tot)
sd = math.sqrt(sum((t - mt) ** 2 for t in tot) / (len(tot) - 1))
sig("SIG-10", "Mean combined points (game total)",
    round(mt, 2), [round(mt - Z * sd / math.sqrt(len(tot)), 2), round(mt + Z * sd / math.sqrt(len(tot)), 2)],
    len(tot), SCHED, f"sd = {round(sd, 2)}")

# SIG-06/07/08 home win by day-of-week
byday = collections.defaultdict(list)
for g in nn:
    byday[g["date"].strftime("%A")].append(g["home_win"])
for i, day in enumerate(["Thursday", "Sunday", "Monday"], start=6):
    vals = byday.get(day, [])
    if vals:
        pp, lo, hi = wilson(sum(vals), len(vals))
        sig(f"SIG-0{i}", f"Designated-home win rate on {day} games",
            round(pp, 4), [round(lo, 4), round(hi, 4)], len(vals), SCHED, "")

# SIG-07 rest-diff game level (both teams have prior games)
rd_rows = []
for g in games:
    rh, ra = rest[(g["game_slug"], g["home"])], rest[(g["game_slug"], g["away"])]
    if rh is None or ra is None:
        continue
    rd_rows.append((rh - ra, g["home_win"], g))
sig_home3 = [y for d, y, _ in rd_rows if d >= 3]
sig_away3 = [1 - y if y in (0, 1) else y for d, y, _ in rd_rows if d <= -3]
p1, l1, h1 = wilson(sum(sig_home3), len(sig_home3))
p2, l2, h2 = wilson(sum(sig_away3), len(sig_away3))
sig("SIG-11a", "Home win rate when home side has 3+ days more rest",
    round(p1, 4), [round(l1, 4), round(h1, 4)], len(sig_home3), SCHED, "")
sig("SIG-11b", "Away win rate when away side has 3+ days more rest",
    round(p2, 4), [round(l2, 4), round(h2, 4)], len(sig_away3), SCHED, "")
# combined: rest-advantaged side wins when |diff| >= 3
adv = []
for d, y, g in rd_rows:
    if d >= 3:
        adv.append(y)
    elif d <= -3:
        adv.append(1 - y if y in (0, 1) else y)
pa, la, ha = wilson(sum(adv), len(adv))
sig("SIG-11", "Rest-advantaged side win rate (3+ days edge, either side)",
    round(pa, 4), [round(la, 4), round(ha, 4)], len(adv), SCHED,
    "games where both sides have a prior 2026 game; ties count 0.5")

# ---------- correlations ----------
corrs = []
def cor(cid, name, x, y, source, note, kind="pearson"):
    c = corr(x, y)
    corrs.append(dict(id=cid, name=name, kind=kind, n=c["n"], r=c["r"], p=c["p"],
                      ci_note="two-sided t-test", source=source, note=note))

# C1 home vs win (phi) at team-game level: each decisive non-neutral game contributes
# (x=home, y=win) for the home side and (x=away, y=win) for the away side
c1x, c1y = [], []
for g in nn:
    if g["margin"] == 0:
        continue
    hw = 1 if g["margin"] > 0 else 0
    c1x += [1, 0]
    c1y += [hw, 1 - hw]
cor("C1", "Designated home field vs win (phi)",
    c1x, c1y, SCHED,
    "decisive non-neutral games, team-game level (2 obs per game; p-values approximate under within-game clustering)",
    "phi")

# C2 rest differential vs home win
c2 = [(d, y) for d, y, g in rd_rows if y in (0, 1)]
cor("C2", "Rest-day differential (home minus away) vs home win",
    [d for d, y in c2], [y for d, y in c2], SCHED,
    "games where both sides have a prior game; decisive only; point-biserial", "point-biserial")

# C3 short rest by home side vs home win
c3 = [(1 if rest[(g["game_slug"], g["home"])] is not None and rest[(g["game_slug"], g["home"])] <= 5 else 0, g["home_win"])
      for g in games if rest[(g["game_slug"], g["home"])] is not None and g["margin"] != 0]
cor("C3", "Home side on short rest (<=5 days) vs home win (phi)",
    [a for a, b in c3], [b for a, b in c3], SCHED, "decisive games; week 1 excluded (no prior)", "phi")

# C4 momentum: previous-game margin vs current win (team-games)
mx, my = [], []
for g in games:
    for team in (g["away"], g["home"]):
        m = momentum[(g["game_slug"], team)]
        if m is None:
            continue
        if team == g["away"]:
            win = 1 if g["ap"] > g["hp"] else (0 if g["ap"] < g["hp"] else 0.5)
        else:
            win = g["home_win"]
        mx.append(m)
        my.append(win)
cor("C4", "Previous-game margin vs current-game win (point-biserial)",
    mx, my, SCHED,
    "team-games with a prior game; observations clustered within games (p-values approximate); ties=0.5",
    "point-biserial")

# C5a parlay slots: Thursday home win x Sunday SNF home win (official SNF slugs from weekly pages)
SNF_SLUGS = {
    "cowboys-at-giants-2026-reg-1", "colts-at-chiefs-2026-reg-2", "rams-at-broncos-2026-reg-3",
    "lions-at-panthers-2026-reg-4", "ravens-at-falcons-2026-reg-5", "cowboys-at-packers-2026-reg-6",
    "chiefs-at-seahawks-2026-reg-7", "eagles-at-commanders-2026-reg-8",
}
thu, snf = {}, {}
for g in games:
    if g["date"].strftime("%A") == "Thursday":
        thu[g["week"]] = g["home_win"]
    if g["game_slug"] in SNF_SLUGS:
        snf[g["week"]] = g["home_win"]
weeks = sorted(set(thu) & set(snf))
x5 = [thu[w] for w in weeks]
y5 = [snf[w] for w in weeks]
c5 = corr(x5, y5)
corrs.append(dict(id="C5a", name="Thursday-game home win x Sunday-night home win (phi)",
                  kind="phi", n=c5["n"], r=c5["r"], p=c5["p"],
                  ci_note="two-sided t-test", source=SCHED,
                  note="parlay leg independence test; official SNF slots identified from weekly page headers; "
                       "n < pre-registered minimum 30 -> underpowered, reported as inconclusive"))
# C5b early/late Sunday: BLOCKED (kickoff times not present in extracted official schedule rows)
corrs.append(dict(id="C5b", name="Early x late Sunday window home win (phi)",
                  kind="phi", n=0, r=None, p=None,
                  ci_note="", source="https://www.nfl.com/schedules/2026/by-week/week-8",
                  note="BLOCKED: official schedule extraction exposes dates but not kickoff windows; "
                       "no value computed, flagged"))

# C6 team passing yards per game vs wins (official team stats x standings)
st = {r["team"]: r for r in standings}
tx, ty = [], []
for row in passing:
    t = row["team"]
    if t not in st:
        continue
    s = st[t]
    gp = int(s["w"]) + int(s["l"]) + int(s["t"])
    tx.append(int(row["yds"]) / gp)
    ty.append(int(s["w"]) + 0.5 * int(s["t"]))
c6 = corr(tx, ty)
corrs.append(dict(id="C6", name="Team passing yards per game vs team wins (point-biserial)",
                  kind="point-biserial", n=c6["n"], r=c6["r"], p=c6["p"],
                  ci_note="two-sided t-test",
                  source="https://www.nfl.com/stats/team-stats/offense/passing/2026/reg/all",
                  note="cross-section n=32, season-to-date; column semantics confirmed by cross-matching "
                       "player tables (e.g., Purdy 211/146/69.2/8.3/1748 equals SF team row)"))

out = dict(
    design="pre-registered nfl-lab/params.json v1.0; inputs verified by scripts/verify_data.py",
    inputs=["nfl-lab/data/games_2026.csv", "nfl-lab/data/standings_2026.csv",
            "nfl-lab/data/team_passing_2026.csv"],
    signals=signals,
    correlations=corrs,
)
with open(os.path.join(D, "signals.json"), "w") as f:
    json.dump(out, f, indent=1)
print(f"{len(signals)} signals, {len(corrs)} correlations written to nfl-lab/data/signals.json")
for s in signals:
    print(" ", s["id"], s["value"], s["ci95"], "n=", s["n"])
for c in corrs:
    print(" ", c["id"], "r=", c["r"], "p=", c["p"], "n=", c["n"])
