"""Strategy models, cluster-robust statistics, validation gates, parlays, correlations (chronological dev/holdout split, parameters frozen)."""
import math
import numpy as np, pandas as pd
from scipy import stats
from config import *

# --------------------------------------------------------------------------- statistics helpers
def cluster_mean(v, cl):
    """Mean and date-clustered standard error of v."""
    v = np.asarray(v, float); n = len(v)
    if n < 2:
        return float(v.mean()) if n else float("nan"), float("nan")
    m = v.mean()
    s = pd.Series(v - m).groupby(np.asarray(cl)).sum()
    return float(m), float(math.sqrt((s ** 2).sum()) / n)


def one_sided_p(mean, se, null):
    if not se or math.isnan(se) or se == 0:
        return 1.0
    return float(1 - stats.norm.cdf((mean - null) / se))


def holm(pvals):
    """Holm-Bonferroni adjusted p-values (dict key -> p)."""
    items = sorted(pvals.items(), key=lambda kv: kv[1]); m = len(items); out = {}; run = 0.0
    for i, (k, p) in enumerate(items):
        run = max(run, min(1.0, (m - i) * p)); out[k] = run
    return out


def fisher_ci(r, n):
    if n < 4 or r is None or math.isnan(r):
        return (None, None)
    z = np.arctanh(r); se = 1 / math.sqrt(n - 3)
    return (float(np.tanh(z - 1.96 * se)), float(np.tanh(z + 1.96 * se)))


# --------------------------------------------------------------------------- strategy registry
TEAM_STRATS = [
    dict(id="T1", market="Game total (Over/Under)", name="Totals · pace form + league scoring drift", kind="total", feats=["f_t2", "league_drift"]),
    dict(id="T2", market="Game total (Over/Under)", name="Totals · rest (back-to-back) flags", kind="total", feats=["h_b2b", "a_b2b"]),
    dict(id="T3", market="Game total (Over/Under)", name="Totals · efficiency-form re-weighting (calibration control)", kind="total", feats=["f_t1"], control=True),
    dict(id="M1", market="Point spread (home cover)", name="Spread · margin-form re-weighting (calibration control)", kind="spread", feats=["f_m1"], control=True),
    dict(id="M2", market="Point spread (home cover)", name="Spread · rest differential + back-to-back", kind="spread", feats=["h_b2b", "a_b2b", "f_restdiff"]),
]
PLAYER_STATS = {"pts": "Points", "reb": "Rebounds", "ast": "Assists", "pra": "Points+Rebounds+Assists"}
PLAYER_FEATS = ["f_mins", "team_b2b", "home", "game_pace_exp"]
PROXY_W = 0.5   # market proxy = season-to-date mean + 0.5 * (recency EWMA - season-to-date mean)


def strategy_specs():
    specs = list(TEAM_STRATS)
    for i, (s, lab) in enumerate(PLAYER_STATS.items(), 1):
        specs.append(dict(id=f"P{i}", market=f"Player {lab} (Over/Under)", name=f"Player {lab} · minutes trend + rest + home + pace",
                          kind="player", stat=s, feats=list(PLAYER_FEATS)))
    return specs


def frame_for(spec, games, players):
    """raw = MARKET PROXY baseline (blend of season-to-date and recency); raw0 = naive season-to-date baseline."""
    if spec["kind"] == "total":
        df = games.assign(y=games["total"], raw0=games["raw_total"], form=games["f_t1"])
    elif spec["kind"] == "spread":
        df = games.assign(y=games["hmargin"], raw0=games["raw_spread"], form=games["f_m1"])
    else:
        s = spec["stat"]; df = players.assign(y=players[s], raw0=players[f"{s}_s"], form=players[f"f_{s}"])
    df = df.assign(raw=df["raw0"] + PROXY_W * df["form"], cl=df["date"])
    return df


class Model:
    """OLS without intercept on dev-centred features; line = raw baseline + dev-calibrated constant."""
    def fit(self, dev, feats):
        self.feats = feats
        self.delta = float((dev["y"] - dev["raw"]).median())          # makes 50% of dev outcomes land over the baseline line
        self.mu = dev[feats].mean()
        X = (dev[feats] - self.mu).values
        r = (dev["y"] - (dev["raw"] + self.delta)).values
        self.beta, *_ = np.linalg.lstsq(X, r, rcond=None)
        adj = X @ self.beta
        self.sd_adj = float(adj.std())
        return self

    def apply(self, df):
        out = df.copy()
        out["line"] = out["raw"] + self.delta
        out["adj"] = ((out[self.feats] - self.mu).values @ self.beta)
        out["own"] = out["line"] + out["adj"]
        out["over"] = out["adj"] > 0
        out["hit"] = ((out["y"] > out["line"]) == out["over"]).astype(float)
        out["push"] = out["y"] == out["line"]
        out["z"] = out["adj"].abs() / self.sd_adj
        return out


def summarize_hits(b):
    b = b[~b["push"]]
    n = len(b)
    if n == 0:
        return dict(n=0, hit=None, se=None, z=None, p_raw=None)
    m, se = cluster_mean(b["hit"], b["cl"])
    return dict(n=n, hit=m, se=se, z=(m - BREAKEVEN) / se if se else None, p_raw=one_sided_p(m, se, BREAKEVEN))


def run_singles(games, players, rng):
    """Fit on dev, freeze, evaluate on holdout. Returns (rows, legs_for_parlays, extras)."""
    rows, legs, extras = [], [], {}
    for spec in strategy_specs():
        df = frame_for(spec, games, players)
        dev = df[df["season"].isin(DEV_SEASONS)]; hold = df[df["season"].isin(HOLDOUT_SEASONS)]
        m = Model().fit(dev, spec["feats"])
        d, h = m.apply(dev), m.apply(hold)
        thr = {q: float(d["adj"].abs().quantile(q)) for q in QUANTILES}
        # MAE skill vs baseline on ALL holdout rows
        diff = (h["y"] - h["line"]).abs() - (h["y"] - h["own"]).abs()
        dm, dse = cluster_mean(diff, h["cl"])
        ic = float(np.corrcoef(h["adj"], h["y"] - h["line"])[0, 1]); ic_ci = fisher_ci(ic, len(h))
        # selected threshold: best dev lower bound
        sel, best = None, -9
        dev_by_q = {}
        for q in QUANTILES:
            s = summarize_hits(d[d["adj"].abs() >= thr[q]]); dev_by_q[q] = s
            lb = (s["hit"] - 1.645 * s["se"]) if s["n"] else -9
            if lb > best: best, sel = lb, q
        for q in QUANTILES:
            b = h[h["adj"].abs() >= thr[q]]
            s = summarize_hits(b)
            bb = b[~b["push"]]
            by_season = {sea: float(g["hit"].mean()) for sea, g in bb.groupby("season")}
            by_season_n = {sea: int(len(g)) for sea, g in bb.groupby("season")}
            parity = (bb["date"].dt.dayofyear // 7) % 2
            halves = [float(bb[parity == k]["hit"].mean()) if (parity == k).any() else None for k in (0, 1)]
            # directional-null: expected hit if the side were independent of the outcome, given each season's over-rate
            rs = h.groupby("season").apply(lambda g: float((g["y"] > g["line"]).mean()))
            nullhit = np.where(bb["over"], bb["season"].map(rs), 1 - bb["season"].map(rs))
            ex_m, ex_se = cluster_mean(bb["hit"].values - nullhit, bb["cl"])
            rows.append(dict(strategy=spec["id"], control=bool(spec.get("control")), name=spec["name"], market=spec["market"], q=q, selected_on_dev=(q == sel),
                             thr_adj=thr[q], n_dev=dev_by_q[q]["n"], hit_dev=dev_by_q[q]["hit"],
                             n=s["n"], hit=s["hit"], se=s["se"], z=s["z"], p_raw=s["p_raw"], roi=(s["hit"] * LEG_DECIMAL - 1) if s["n"] else None,
                             by_season=by_season, by_season_n=by_season_n, halves=halves,
                             over_share=float(bb["over"].mean()) if len(bb) else None,
                             excess=ex_m, excess_se=ex_se, excess_p=one_sided_p(ex_m, ex_se, 0.0), null_hit=float(nullhit.mean()) if len(bb) else None,
                             mae_gain=dm, mae_gain_se=dse, mae_p=one_sided_p(dm, dse, 0.0),
                             mae_base=float((h["y"] - h["line"]).abs().mean()), mae_own=float((h["y"] - h["own"]).abs().mean()),
                             ic=ic, ic_lo=ic_ci[0], ic_hi=ic_ci[1], n_rows=len(h),
                             beta=dict(zip(spec["feats"], map(float, m.beta))), delta=m.delta))
        # legs for parlay construction at selected q (holdout)
        b = h[(h["adj"].abs() >= thr[sel]) & (~h["push"])]
        keep = ["season", "date", "game_id", "hit", "z", "over"]
        for c in ("team_id", "pid", "name"):
            if c in b.columns: keep.append(c)
        L = b[keep].copy(); L["strat"] = spec["id"]; L["kind"] = spec["kind"]; L["stat"] = spec.get("stat")
        L["cl"] = L["date"]
        legs.append(L)
        # residual frames for correlation analysis
        extras[spec["id"]] = dict(dev=d, hold=h)
    return rows, pd.concat(legs, ignore_index=True), extras


# --------------------------------------------------------------------------- gates for singles
def gate_singles(rows, leak_ok):
    holm_p = holm({(r["strategy"], r["q"]): r["p_raw"] for r in rows if r["p_raw"] is not None})
    for r in rows:
        r["p_holm"] = holm_p.get((r["strategy"], r["q"]), 1.0)
    by = {}
    for r in rows: by.setdefault(r["strategy"], {})[r["q"]] = r
    for r in rows:
        sel_row = next(x for x in by[r["strategy"]].values() if x["selected_on_dev"])
        g = {}
        g["G1"] = bool(leak_ok)
        g["G2"] = r["n"] >= MIN_BETS_SINGLE
        g["G3"] = bool(r["mae_gain"] > 0 and r["mae_p"] < ALPHA)
        g["G4"] = bool(r["hit"] is not None and r["hit"] > BREAKEVEN and r["p_holm"] < ALPHA)
        seas_ok = sum(1 for v in r["by_season"].values() if v > 0.5) >= 3
        g["G5"] = bool(seas_ok and (r["hit_dev"] or 0) > 0.5 and all((h or 0) > 0.5 for h in r["halves"]))
        g["G6"] = all((by[r["strategy"]][q]["hit"] or 0) > 0.5 for q in QUANTILES)
        g["G7"] = bool(r["over_share"] is not None and SIDE_BALANCE[0] <= r["over_share"] <= SIDE_BALANCE[1]
                       and r["excess"] > 0 and r["excess_p"] < ALPHA)
        r["gates"] = {k: bool(v) for k, v in g.items()}
        r["passed_all"] = all(g.values())
        r["gate_fails"] = [k for k, v in g.items() if not v]
    return rows


def placebo_calibration(rows, games, players, rng, runs=PLACEBO_RUNS):
    """Apply the significance gate (raw Bonferroni across the same number of trials) to RANDOM-side strategies
    placed on identical bet sets. Expected false-positive rate = alpha / m (<< 5%)."""
    m = len(rows); alpha_b = ALPHA / m
    fp = tot = 0; hit_means = []
    for spec in strategy_specs():
        df = frame_for(spec, games, players)
        dev = df[df["season"].isin(DEV_SEASONS)]; hold = df[df["season"].isin(HOLDOUT_SEASONS)]
        mod = Model().fit(dev, spec["feats"]); h = mod.apply(hold)
        for q in QUANTILES:
            thr = float(mod.apply(dev)["adj"].abs().quantile(q))
            b = h[(h["adj"].abs() >= thr) & (~h["push"])]
            up = (b["y"] > b["line"]).values
            for _ in range(runs // len(QUANTILES)):
                side = rng.random(len(b)) < 0.5
                hit = (side == up).astype(float)
                mean, se = cluster_mean(hit, b["cl"])
                tot += 1; hit_means.append(mean)
                if mean > BREAKEVEN and one_sided_p(mean, se, BREAKEVEN) < alpha_b: fp += 1
    return dict(placebo_strategies=tot, false_positives=fp, false_positive_rate=fp / tot, bonferroni_alpha=alpha_b,
                placebo_hit_mean=float(np.mean(hit_means)), placebo_hit_sd=float(np.std(hit_means)), passes=bool(fp / tot <= ALPHA))


# --------------------------------------------------------------------------- parlays
def _phi(cols):
    if len(cols) == 2:
        a, b = cols
        return float(np.corrcoef(a, b)[0, 1]) if a.std() > 0 and b.std() > 0 else float("nan")
    ps = []
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            ps.append(np.corrcoef(cols[i], cols[j])[0, 1])
    return float(np.nanmean(ps))


def build_parlays(legs):
    """Returns dict name -> (DataFrame with one row per parlay: date, season, leg hit columns h1..hn, legs=n)."""
    out = {}
    L = legs.copy()
    best_per_game = L.sort_values("z", ascending=False).groupby(["date", "game_id"], as_index=False).head(1)

    def xg(n):
        rows = []
        for date, d in best_per_game.groupby("date"):
            if len(d) >= n:
                t = d.sort_values("z", ascending=False).head(n)
                rows.append(dict(date=date, season=t["season"].iloc[0], **{f"h{i+1}": v for i, v in enumerate(t["hit"].values)}))
        return pd.DataFrame(rows)
    out["XG2 · Cross-game 2-leg (top-2 edges per day, different games)"] = xg(2)
    out["XG3 · Cross-game 3-leg (top-3 edges per day, different games)"] = xg(3)

    def pair(a_mask, b_mask, same_player=False, key=("game_id",)):
        A = L[a_mask].sort_values("z", ascending=False).groupby(list(key), as_index=False).head(1)
        B = L[b_mask].sort_values("z", ascending=False).groupby(list(key), as_index=False).head(1)
        m = A.merge(B, on=list(key), suffixes=("_a", "_b"))
        if same_player: m = m[m["pid_a"] == m["pid_b"]] if "pid_a" in m else m
        return pd.DataFrame(dict(date=m["date_a"], season=m["season_a"], h1=m["hit_a"], h2=m["hit_b"]))
    tot = L["strat"].isin(["T1", "T2"]); spr = L["strat"].isin(["M1", "M2"]); pts = L["strat"] == "P1"
    out["SGP1 · Same game: game total + player points"] = pair(tot, pts)
    out["SGP2 · Same game: spread + player points"] = pair(spr, pts)
    out["SGP3 · Same game: game total + spread"] = pair(tot, spr)
    # same-player combos
    P = L[L["kind"] == "player"]
    if P.empty: return out
    wide = P.pivot_table(index=["game_id", "pid"], columns="stat", values="hit", aggfunc="first")
    meta = P.groupby(["game_id", "pid"]).agg(date=("date", "first"), season=("season", "first"))
    wide = wide.join(meta)
    for a, b in [("pts", "reb"), ("pts", "ast"), ("reb", "ast")]:
        w = wide.dropna(subset=[a, b])
        out[f"CMB · {a.upper()}+{b.upper()} same player (2 legs)"] = pd.DataFrame(dict(date=w["date"], season=w["season"], h1=w[a], h2=w[b]))
    w = wide.dropna(subset=["pts", "reb", "ast"])
    out["CMB · PTS+REB+AST same player (3 legs)"] = pd.DataFrame(dict(date=w["date"], season=w["season"], h1=w["pts"], h2=w["reb"], h3=w["ast"]))
    # teammate / opponent point props
    PP = L[L["strat"] == "P1"].sort_values("z", ascending=False)
    rows = []
    for (gid, tid), d in PP.groupby(["game_id", "team_id"]):
        if len(d) >= 2:
            t = d.head(2); rows.append(dict(date=t["date"].iloc[0], season=t["season"].iloc[0], h1=t["hit"].iloc[0], h2=t["hit"].iloc[1]))
    out["CMB · Teammates: two player-points legs, same team"] = pd.DataFrame(rows)
    rows = []
    for gid, d in PP.groupby("game_id"):
        top = d.groupby("team_id").head(1)
        if len(top) == 2:
            rows.append(dict(date=top["date"].iloc[0], season=top["season"].iloc[0], h1=top["hit"].iloc[0], h2=top["hit"].iloc[1]))
    out["CMB · Opponents: one player-points leg per team"] = pd.DataFrame(rows)
    return out


def evaluate_parlays(parlays):
    res = []
    for name, df in parlays.items():
        hcols = [c for c in df.columns if c.startswith("h") and c[1:].isdigit()]
        nlegs = len(hcols)
        if len(df) == 0:
            res.append(dict(name=name, legs=max(nlegs, 2), n=0, note="Not buildable: no eligible legs of the required market")); continue
        won = df[hcols].prod(axis=1).values
        ret = won * (LEG_DECIMAL ** nlegs) - 1
        mean, se = cluster_mean(ret, df["date"])
        leg_means = [float(df[c].mean()) for c in hcols]
        indep = float(np.prod(leg_means)); joint = float(won.mean())
        rho = _phi([df[c].values for c in hcols]) if len(df) > 5 else float("nan")
        seas = {s: float((g[hcols].prod(axis=1) * (LEG_DECIMAL ** nlegs) - 1).mean()) for s, g in df.groupby("season")}
        seas_n = {s: int(len(g)) for s, g in df.groupby("season")}
        par = (df["date"].dt.dayofyear // 7) % 2
        halves = [float((df[par == k][hcols].prod(axis=1) * (LEG_DECIMAL ** nlegs) - 1).mean()) if (par == k).any() else None for k in (0, 1)]
        res.append(dict(name=name, legs=nlegs, n=int(len(df)), joint_hit=joint, indep_hit=indep, lift=joint / indep if indep else None,
                        leg_hits=leg_means, rho=rho, breakeven_joint=1 / (LEG_DECIMAL ** nlegs), roi=float(mean), roi_se=se,
                        p_raw=one_sided_p(mean, se, 0.0), by_season=seas, by_season_n=seas_n, halves=halves))
    ok = {r["name"]: r["p_raw"] for r in res if r.get("n")}
    hp = holm(ok)
    for r in res:
        if not r.get("n"):
            r.update(p_holm=1.0, gates={k: False for k in ("G2", "G4", "G5", "G8", "G9")}, passed_all=False, gate_fails=["G2"]); continue
        r["p_holm"] = hp[r["name"]]
        g = {}
        g["G2"] = r["n"] >= MIN_BETS_PARLAY
        g["G4"] = bool(r["roi"] > 0 and r["p_holm"] < ALPHA)
        g["G5"] = bool(sum(1 for v in r["by_season"].values() if v > 0) >= 3 and all((h or -1) > 0 for h in r["halves"]))
        g["G8"] = bool(r["rho"] == r["rho"] and abs(r["rho"]) <= PARLAY_MAX_ABS_RHO)
        g["G9"] = r["legs"] <= PARLAY_MAX_LEGS
        r["gates"] = g; r["passed_all"] = all(g.values()); r["gate_fails"] = [k for k, v in g.items() if not v]
    return res


# --------------------------------------------------------------------------- correlations
def corr_row(label, a, b, n_note="", cluster=None):
    a = np.asarray(a, float); b = np.asarray(b, float)
    ok = ~(np.isnan(a) | np.isnan(b)); a, b = a[ok], b[ok]; n = len(a)
    if n < 30 or a.std() == 0 or b.std() == 0:
        return dict(pair=label, n=n, r=None, lo=None, hi=None)
    r = float(np.corrcoef(a, b)[0, 1]); lo, hi = fisher_ci(r, n)
    sp = float(stats.spearmanr(a, b)[0])
    return dict(pair=label, n=n, r=r, lo=lo, hi=hi, spearman=sp)


def compute_correlations(extras, games):
    out = {"stat_residuals": [], "teammate_opponent": [], "context": [], "signal_vs_outcome": []}
    P = {s: extras[f"P{i}"] for i, s in enumerate(PLAYER_STATS, 1)}
    for part, key in (("holdout", "hold"), ("dev", "dev")):
        base = P["pts"][key][["game_id", "pid", "team_id", "y", "line", "pts_s", "mins", "season", "adj"]].rename(columns={"y": "pts", "line": "pts_line"})
        base["pts_res"] = base["pts"] - base["pts_line"]
        for s in ("reb", "ast"):
            q = P[s][key][["game_id", "pid", "y", "line"]].rename(columns={"y": s, "line": f"{s}_line"})
            base = base.merge(q, on=["game_id", "pid"]); base[f"{s}_res"] = base[s] - base[f"{s}_line"]
        for a, b, lab in [("pts_res", "reb_res", "Points ↔ Rebounds"), ("pts_res", "ast_res", "Points ↔ Assists"), ("reb_res", "ast_res", "Rebounds ↔ Assists")]:
            r = corr_row(lab, base[a], base[b]); r["sample"] = part; out["stat_residuals"].append(r)
        r = corr_row("Points ↔ Minutes played (same game)", base["pts_res"], base["mins"] - base["mins"].groupby(base["pid"]).transform("mean")); r["sample"] = part; out["stat_residuals"].append(r)
        # teammates / opponents (top-scorers by season-to-date ppg)
        t = base.sort_values("pts_s", ascending=False).groupby(["game_id", "team_id"]).head(2)
        rk = t.groupby(["game_id", "team_id"]).cumcount()
        a_ = t[rk == 0].set_index(["game_id", "team_id"])["pts_res"]; b_ = t[rk == 1].set_index(["game_id", "team_id"])["pts_res"]
        j = pd.concat([a_, b_], axis=1, keys=["a", "b"]).dropna()
        r = corr_row("Teammates: top-2 scorers' points residuals", j["a"], j["b"]); r["sample"] = part; out["teammate_opponent"].append(r)
        top = t[rk == 0]
        g2 = top.groupby("game_id").filter(lambda x: len(x) == 2)
        gg = g2.groupby("game_id")["pts_res"].apply(list)
        r = corr_row("Opponents: each team's top scorer points residuals", [x[0] for x in gg], [x[1] for x in gg]); r["sample"] = part; out["teammate_opponent"].append(r)
        tot = games.set_index("game_id")
        tp = top.merge(tot[["total", "raw_total"]], left_on="game_id", right_index=True)
        r = corr_row("Top scorer points residual ↔ game total residual", tp["pts_res"], tp["total"] - tp["raw_total"]); r["sample"] = part; out["teammate_opponent"].append(r)
        g = games[games["season"].isin(HOLDOUT_SEASONS if part == "holdout" else DEV_SEASONS)]
        out["context"] += [
            dict(corr_row("Pre-game combined pace ↔ game total", g["game_pace_exp"], g["total"]), sample=part),
            dict(corr_row("Pre-game margin differential (PPG-diff proxy) ↔ home margin", g["raw_spread"], g["hmargin"]), sample=part),
            dict(corr_row("Home back-to-back flag ↔ home margin residual", g["h_b2b"], g["hmargin"] - g["raw_spread"]), sample=part),
            dict(corr_row("Away back-to-back flag ↔ home margin residual", g["a_b2b"], g["hmargin"] - g["raw_spread"]), sample=part),
            dict(corr_row("Home back-to-back flag ↔ game total residual", g["h_b2b"], g["total"] - g["raw_total"]), sample=part),
            dict(corr_row("Away back-to-back flag ↔ game total residual", g["a_b2b"], g["total"] - g["raw_total"]), sample=part),
        ]
    return out


def proxy_vs_naive(games, players):
    """CONTROL: how much of a 'win' is just beating the naive season-to-date line? Bet the direction of recency form
    against the NAIVE line (no fitting). Shows why strategies are settled against the market proxy instead."""
    out = []
    for spec in [TEAM_STRATS[0], TEAM_STRATS[3]] + [dict(id="P1", kind="player", stat="pts", market="Player Points (Over/Under)")]:
        if spec["kind"] == "total": sp = dict(kind="total")
        elif spec["kind"] == "spread": sp = dict(kind="spread")
        else: sp = spec
        df = frame_for(sp, games, players)
        dev = df[df["season"].isin(DEV_SEASONS)]; hold = df[df["season"].isin(HOLDOUT_SEASONS)]
        delta = float((dev["y"] - dev["raw0"]).median())
        h = hold.assign(line=hold["raw0"] + delta)
        h = h[h["form"].abs() >= h["form"].abs().quantile(0.5)]
        over = h["form"] > 0
        hit = ((h["y"] > h["line"]) == over).astype(float)
        m, se = cluster_mean(hit, h["cl"])
        out.append(dict(market={"total": "Game total", "spread": "Point spread", "player": "Player points"}[spec["kind"]],
                        rule="Over if recency form > season mean, else Under; top-50% |form|; settled vs NAIVE season-to-date line",
                        n=int(len(h)), hit=m, se=se))
    return out


def assign_tiers(rows):
    """Recognition tiers (no cash reward). Controls are never ranked."""
    for r in rows:
        f = set(r["gate_fails"])
        if r.get("control"):
            r["tier"] = "Control · not eligible"
        elif r["passed_all"]:
            r["tier"] = "Provisional Gold"
        elif r.get("p_holm", 1) < ALPHA and not (f - {"G2", "G7"}) and r.get("hit", 0) and r["hit"] > BREAKEVEN:
            r["tier"] = "Silver"
        elif r.get("p_raw") is not None and r["p_raw"] < ALPHA and r.get("hit") and r["hit"] > BREAKEVEN:
            r["tier"] = "Bronze"
        else:
            r["tier"] = "No award"
        # score: lower 95% bound of edge over breakeven (singles) / lower bound of ROI (parlays), in percentage points
        if "hit" in r and r["hit"] is not None and r.get("se"):
            r["score_pp"] = 100 * (r["hit"] - 1.645 * r["se"] - BREAKEVEN)
        elif "roi" in r and r.get("roi_se"):
            r["score_pp"] = 100 * (r["roi"] - 1.645 * r["roi_se"])
        else:
            r["score_pp"] = None
    return rows
