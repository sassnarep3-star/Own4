#!/usr/bin/env python3
"""Own-line origination engine: chronological Elo (margin) + decayed scoring (totals).

Rules
-----
* STRICTLY chronological. A game's line is produced from games with an earlier
  date only (ties broken by week, then game_id). No future information.
* Knobs are calibrated on the DEV window (seasons 1999-2012) and FROZEN before the
  2013+ holdout is scored. Calibration happens inside this script on dev rows only.
* Ratings are updated from the archived result (third-party archive of official
  final scores; the 2026 subset is cross-validated against nfl.com standings in
  01_results.py, 160/160 cells).
"""
import csv, json, math, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ROOT)
SRC = os.path.join(REPO, "nfl-quant", "data", "predictions.csv")
OUT = os.path.join(ROOT, "data")

K = 20.0                 # Elo K-factor
HFA_ELO = 48.0           # home-field advantage, Elo points
MOV_CAP = 24.0           # margin-of-victory denominator cap
SEASON_REGRESS = 0.33    # shrink ratings 1/3 toward the mean between seasons
HALFLIFE = 8.0           # games; exponential half-life for scoring averages
DECAY = 0.5 ** (1.0 / HALFLIFE)

DEV_MAX_SEASON = 2012    # knob calibration window
PPE_GRID = [18, 20, 22, 24, 26, 28, 30, 32]
BLEND_GRID = [0.0, 0.2, 0.35, 0.5, 0.65, 0.8, 1.0]


def load():
    rows = [r for r in csv.DictReader(open(SRC)) if r["result"] not in ("", "NA")]
    rows.sort(key=lambda r: (int(r["season"]), int(r["week"]), r["gameday"], r["game_id"]))
    return rows


def run(rows, ppe, blend, collect=True):
    """Walk forward. Returns predictions; ratings state is rebuilt from scratch."""
    elo, w, pf, pa = {}, {}, {}, {}
    league_tot = None          # running decayed league average points-per-team
    league_w = 0.0
    league_sum = 0.0
    preds = []
    season = None
    for r in rows:
        s = int(r["season"])
        if season is not None and s != season:
            for t in elo:
                elo[t] = 1500.0 + (elo[t] - 1500.0) * (1 - SEASON_REGRESS)
                w[t] *= (1 - SEASON_REGRESS); pf[t] *= (1 - SEASON_REGRESS); pa[t] *= (1 - SEASON_REGRESS)
        season = s
        a, h = r["away_team"], r["home_team"]
        for t in (a, h):
            elo.setdefault(t, 1500.0); w.setdefault(t, 0.0)
            pf.setdefault(t, 0.0); pa.setdefault(t, 0.0)

        if collect:
            rec = {"game_id": r["game_id"], "season": s, "week": int(r["week"]),
                   "date": r["gameday"], "away": a, "home": h,
                   "result": float(r["result"]), "total": float(r["total"]),
                   "spread_line": float(r["spread_line"]) if r["spread_line"] not in ("", "NA") else None,
                   "total_line": float(r["total_line"]) if r["total_line"] not in ("", "NA") else None}
            rec["pred_margin"] = (elo[h] + HFA_ELO - elo[a]) / ppe

            nteams = len([t for t in w if w[t] > 0.05]) or 1
            lg = (league_sum / league_w) if league_w > 0 else 21.0
            def rating(t):
                if w[t] < 0.05:
                    return 0.0, 0.0
                return pf[t] / w[t] - lg, lg - pa[t] / w[t]   # offense +, defense +
            off_h, def_h = rating(h)
            off_a, def_a = rating(a)
            raw = (lg + off_h + def_a) + (lg + off_a + def_h)
            rec["pred_total"] = lg * 2 + blend * (raw - lg * 2)
            rec["league_avg_team_pts"] = round(lg, 3)
            preds.append(rec)

        # ---- update state with the actual result -------------------------
        m = r["result"] = float(r["result"])
        tot = float(r["total"])
        ew = 1.0 / (1.0 + 10 ** (-((elo[h] + HFA_ELO) - elo[a]) / 400.0))
        hw = 1.0 if m > 0 else (0.0 if m < 0 else 0.5)
        mov = math.log(abs(m) + 1.0) / math.log(MOV_CAP + 1.0)
        d = K * (hw - ew) * mov
        elo[h] += d; elo[a] -= d
        hp, ap = (tot + m) / 2.0, (tot - m) / 2.0
        for t, f, ag in ((h, hp, ap), (a, ap, hp)):
            w[t] = w[t] * DECAY + 1.0
            pf[t] = pf[t] * DECAY + f
            pa[t] = pa[t] * DECAY + ag
        league_w = league_w * DECAY + 2.0
        league_sum = league_sum * DECAY + tot
    return preds


def mae(preds, key, actual):
    v = [abs(p[key] - p[actual]) for p in preds if p[key] is not None]
    return sum(v) / len(v), len(v)


def calibrate(rows):
    dev = [r for r in rows if int(r["season"]) <= DEV_MAX_SEASON]
    best_p = None
    for ppe in PPE_GRID:
        m, n = mae(run(dev, ppe, 1.0), "pred_margin", "result")
        if best_p is None or m < best_p[1]:
            best_p = (ppe, m, n)
    best_b = None
    for b in BLEND_GRID:
        m, n = mae(run(dev, best_p[0], b), "pred_total", "total")
        if best_b is None or m < best_b[1]:
            best_b = (b, m, n)
    return best_p, best_b


def main():
    rows = load()
    print(f"archive: {len(rows)} settled games, {rows[0]['season']}-{rows[-1]['season']}")
    (ppe, m_mae, m_n), (blend, t_mae, t_n) = calibrate(rows)
    print(f"DEV calibration: points-per-Elo={ppe} (margin MAE {m_mae:.3f}, n={m_n})")
    print(f"DEV calibration: totals blend={blend} (total MAE {t_mae:.3f}, n={t_n})")

    preds = run(rows, ppe, blend)
    json.dump({"pts_per_elo": ppe, "k": K, "hfa_elo": HFA_ELO, "mov_cap": MOV_CAP,
               "season_regression": SEASON_REGRESS, "scoring_halflife_games": HALFLIFE,
               "totals_blend": blend, "dev_max_season": DEV_MAX_SEASON,
               "dev_margin_mae": round(m_mae, 3), "dev_total_mae": round(t_mae, 3),
               "n_predicted": len(preds),
               "note": "Both knobs fitted on seasons 1999-2012 only, then frozen. "
                       "Nothing from 2013+ informed these values."},
              open(os.path.join(OUT, "model_config.json"), "w"), indent=1)
    with open(os.path.join(OUT, "walkforward.csv"), "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["game_id", "season", "week", "date", "away", "home", "result", "total",
                     "spread_line", "total_line", "pred_margin", "pred_total", "league_avg_team_pts"])
        for p in preds:
            wr.writerow([p["game_id"], p["season"], p["week"], p["date"], p["away"], p["home"],
                         f"{p['result']:.1f}", f"{p['total']:.1f}",
                         "" if p["spread_line"] is None else p["spread_line"],
                         "" if p["total_line"] is None else p["total_line"],
                         round(p["pred_margin"], 3), round(p["pred_total"], 3),
                         p["league_avg_team_pts"]])
    print(f"wrote {len(preds)} walk-forward predictions -> {OUT}/walkforward.csv")


if __name__ == "__main__":
    main()
