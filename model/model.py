"""Own-line model (pure Python, stdlib only).  See strategies/gates.json for the pre-registered definitions."""
import csv, math, os, random
D = os.path.join(os.path.dirname(__file__), "..", "data")
K_DEFAULT = 41

def rd(name):
    return list(csv.DictReader(open(os.path.join(D, name), newline="")))

def phi(x):  # standard normal cdf
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))

def pdf(x):
    return math.exp(-x * x / 2) / math.sqrt(2 * math.pi)

def orthant(a, b, rho):
    """P(Z1 > a, Z2 > b) for standard bivariate normal with correlation rho (numeric integration)."""
    if abs(rho) < 1e-9:
        return (1 - phi(a)) * (1 - phi(b))
    s = math.sqrt(1 - rho * rho)
    lo, hi, n = max(a, -8.0), 8.0, 2000
    if lo >= hi:
        return 0.0
    h = (hi - lo) / n
    tot = 0.0
    for i in range(n + 1):
        x = lo + i * h
        f = pdf(x) * (1 - phi((b - rho * x) / s))
        tot += f * (0.5 if i in (0, n) else 1)
    return tot * h

def round_half(x):
    return round(x * 2) / 2

def prior():
    """2025-26 official tables -> per-team prior ratings and league constants."""
    s = {r["abbr"]: r for r in rd("team_stats_2025-26.csv")}
    home = rd("team_stats_2025-26_home.csv")
    gp = sum(int(r["GP"]) for r in home)
    H = sum(float(r["plus_minus_per_game"]) * int(r["GP"]) for r in home) / gp
    hw = sum(int(r["W"]) for r in home)
    p = {t: dict(R=float(r["plus_minus_per_game"]), O=float(r["PTS_per_game"]),
                 Dn=float(r["PTS_per_game"]) - float(r["plus_minus_per_game"])) for t, r in s.items()}
    LG = sum(v["O"] for v in p.values()) / len(p)
    return p, H, hw / gp, LG

def ratings(prior_t, season_sums, k):
    """season_sums[t] = (n, sum_pf, sum_pa) from games strictly before the target date."""
    out = {}
    for t, pr in prior_t.items():
        n, pf, pa = season_sums.get(t, (0, 0, 0))
        w = n + k
        if w == 0:
            out[t] = dict(R=0.0, O=0.0, Dn=0.0)
            continue
        out[t] = dict(R=((pf - pa) + k * pr["R"]) / w, O=(pf + k * pr["O"]) / w, Dn=(pa + k * pr["Dn"]) / w)
    return out

def predict(rt, home, away, H, LG_override=None):
    mean_O = sum(v["O"] for v in rt.values()) / len(rt)
    margin = rt[home]["R"] - rt[away]["R"] + H
    total = rt[home]["O"] + rt[away]["Dn"] + rt[away]["O"] + rt[home]["Dn"] - 2 * mean_O
    return margin, total

def load_games():
    g = rd("games_2026-27.csv")
    for r in g:
        r["ap"], r["hp"] = int(r["away_pts"]), int(r["home_pts"])
    g.sort(key=lambda r: (r["date"], r["game_id"]))
    return g

def walk_forward(games, k_grid, prior_t, H, LG0):
    """Returns per-game dict of predictions for each k (BLEND), PRIOR (k=inf), CURRENT (k=0), plus league-average total baseline.
    Asserts that only strictly earlier dates enter each prediction."""
    sums, rows, i = {}, [], 0
    league_pts, league_n = 2 * LG0 * 1, 0   # pseudo: prior-season league avg total, replaced by in-season mean once games exist
    seen_total, seen_n = 0, 0
    dates = sorted({g["date"] for g in games})
    for d in dates:
        day = [g for g in games if g["date"] == d]
        snap = dict(sums)
        cutoff_n = sum(v[0] for v in snap.values()) // 2
        assert all(x["date"] < d for x in rows)  # no look-ahead: rows so far are strictly earlier
        rts = {k: ratings(prior_t, snap, k) for k in k_grid}
        rt_prior = ratings(prior_t, snap, 10**9)
        rt_cur = ratings(prior_t, snap, 0)
        base_total = (seen_total / seen_n) if seen_n else 2 * LG0
        for g in day:
            h, a = g["home"], g["away"]
            rec = dict(date=d, game_id=g["game_id"], home=h, away=a, hp=g["hp"], ap=g["ap"],
                       margin=g["hp"] - g["ap"], total=g["hp"] + g["ap"], n_before=cutoff_n)
            for k in k_grid:
                m, t = predict(rts[k], h, a, H)
                rec[f"m_k{k}"], rec[f"t_k{k}"] = m, t
            rec["m_prior"], rec["t_prior"] = predict(rt_prior, h, a, H)
            rec["m_cur"], rec["t_cur"] = predict(rt_cur, h, a, H)
            rec["m_hca"] = H
            rec["t_lg"] = base_total
            rows.append(rec)
        for g in day:  # update only after the whole day has been predicted
            for t, pf, pa in ((g["home"], g["hp"], g["ap"]), (g["away"], g["ap"], g["hp"])):
                n, spf, spa = sums.get(t, (0, 0, 0))
                sums[t] = (n + 1, spf + pf, spa + pa)
            seen_total += g["hp"] + g["ap"]; seen_n += 1
    return rows, sums

def mean(x):
    x = list(x)
    return sum(x) / len(x)

def corr(x, y):
    mx, my = mean(x), mean(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sx = math.sqrt(sum((a - mx) ** 2 for a in x)); sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return sxy / (sx * sy) if sx and sy else 0.0

def boot_ci(diffs, level, reps=10000, seed=20261102):
    rnd = random.Random(seed)
    n = len(diffs)
    ms = sorted(sum(diffs[rnd.randrange(n)] for _ in range(n)) / n for _ in range(reps))
    a = (1 - level) / 2
    return ms[int(a * reps)], ms[min(reps - 1, int((1 - a) * reps))]
