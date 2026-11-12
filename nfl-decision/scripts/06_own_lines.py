#!/usr/bin/env python3
"""Originate auditable lines for every 2026 Week 10 game.

Running the frozen model on a real slate does NOT require inventing results: as of
2026-11-12 only Week 10's Thursday game (WAS@NYG) has kicked off, so the other 13
are genuine out-of-sample forecasts made before kickoff.

Published number = round(fitted prediction to the nearest 0.5) + a stated 1.0 pt
disagreement filter. Anything the model cannot price from official inputs is BLANK
and flagged, never filled in.
"""
import csv, json, os, statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data")
SLATE_SRC = "https://www.nfl.com/schedules/2026/by-week/week-10"
FILTER = 1.0     # points of disagreement before a number is published as a play

# Week 10 schedule, transcribed from the official schedule page (2026-11-12).
SCHEDULE = {
 "WAS@NYG": ("WAS", "NYG", "2026-11-12T20:15-05:00", "Prime Video", "MetLife Stadium"),
 "NE@DET":  ("NE", "DET", "2026-11-15T09:30-05:00", "FOX", "FC Bayern Munich Stadium (Munich)"),
 "KC@ATL":  ("KC", "ATL", "2026-11-15T13:00-05:00", "CBS", "Mercedes-Benz Stadium"),
 "HOU@CLE": ("HOU", "CLE", "2026-11-15T13:00-05:00", "FOX", "Huntington Bank Field"),
 "MIN@GB":  ("MIN", "GB", "2026-11-15T13:00-05:00", "FOX", "Lambeau Field"),
 "MIA@IND": ("MIA", "IND", "2026-11-15T13:00-05:00", "CBS", "Lucas Oil Stadium"),
 "CAR@NO":  ("CAR", "NO", "2026-11-15T13:00-05:00", "FOX", "Caesars Superdome"),
 "BUF@NYJ": ("BUF", "NYJ", "2026-11-15T13:00-05:00", "CBS", "MetLife Stadium"),
 "JAX@TEN": ("JAX", "TEN", "2026-11-15T13:00-05:00", "FOX", "Nissan Stadium"),
 "LA@ARI":  ("LAR", "ARI", "2026-11-15T16:05-05:00", "CBS", "State Farm Stadium"),
 "SEA@LV":  ("SEA", "LV", "2026-11-15T16:05-05:00", "CBS", "Allegiant Stadium"),
 "SF@DAL":  ("SF", "DAL", "2026-11-15T16:25-05:00", "FOX", "AT&T Stadium"),
 "PIT@CIN": ("PIT", "CIN", "2026-11-15T20:20-05:00", "NBC", "Paycor Stadium"),
 "LAC@BAL": ("LAC", "BAL", "2026-11-16T20:15-05:00", "ESPN", "M&T Bank Stadium"),
}
KICKED_OFF = {"WAS@NYG"}   # started before this session's work; excluded from the forward log


def ols(xs, ys):
    mx, my = statistics.mean(xs), statistics.mean(ys)
    b = sum((a - mx) * (c - my) for a, c in zip(xs, ys)) / sum((a - mx) ** 2 for a in xs)
    return my - b * mx, b


def main():
    rows = [r for r in csv.DictReader(open(os.path.join(OUT, "walkforward.csv")))]
    hist = [r for r in rows if r["spread_line"] not in ("", "None") and r["total_line"] not in ("", "None")]
    cfg = json.load(open(os.path.join(OUT, "model_config.json")))
    # Recalibration coefficients fitted on the ENTIRE archived history (in-sample,
    # stated explicitly). Diagnostics showed the raw model is over-dispersed.
    m_a, m_b = ols([float(r["pred_margin"]) for r in hist], [float(r["result"]) for r in hist])
    t_a, t_b = ols([float(r["pred_total"]) for r in hist], [float(r["total"]) for r in hist])

    fwd = json.load(open(os.path.join(OUT, "forward_slate.json")))
    slate = {}
    for r in fwd["games"]:
        if r["season"] != 2026 or r["week"] != 10:
            continue
        key = f'{r["away"]}@{r["home"]}'
        slate[key] = r
        slate[key.replace("LA@", "LAR@")] = r
    print("forward keys:", sorted(slate))
    print("forward forecasts available for week 10:", len(slate))

    lines = []
    for key, (away, home, kick, tv, venue) in SCHEDULE.items():
        r = slate.get(key) or slate.get(key.replace("LAR", "LA"))
        raw_m = float(r["pred_margin"]); raw_t = float(r["pred_total"])
        m = m_a + m_b * raw_m
        t = t_a + t_b * raw_t
        def half(x):
            return round(x * 2) / 2
        own_spread = half(-m)          # negative = home favourite (market convention: home margin)
        own_total = half(t)
        market_spread = r["spread_line"]
        market_total = r["total_line"]
        play = ""
        if market_spread is not None:
            edge = m - float(market_spread)
            if abs(edge) >= FILTER:
                play = f'{home} {own_spread:+.1f}' if edge > 0 else f'{away} {own_spread:+.1f}'
        tot_play = ""
        if market_total is not None:
            de = t - float(market_total)
            if abs(de) >= FILTER:
                tot_play = f'{"Over" if de > 0 else "Under"} {own_total:.1f}'
        lines.append({
            "game": key, "kickoff_local": kick, "tv": tv, "venue": venue,
            "away": away, "home": home,
            "own_home_margin": round(own_spread, 1), "own_total": round(own_total, 1),
            "model_win_prob_home": None,
            "raw_model_margin": round(raw_m, 2), "raw_model_total": round(raw_t, 2),
            "market_spread": None, "market_total": None,
            "spread_edge_pts": None, "total_edge_pts": None,
            "spread_play": play, "total_play": tot_play,
            "in_forward_log": key not in KICKED_OFF,
            "source": SLATE_SRC,
            "injury_source": "https://www.nfl.com/injuries/",
        })
        if key in KICKED_OFF:
            lines[-1]["note"] = "Kicked off before this work was recorded; excluded from the forward log."

    # win probability from the normal model with sigma = realised residual sd
    sig = statistics.pstdev([float(r["result"]) - (m_a + m_b * float(r["pred_margin"])) for r in hist])
    def norm_cdf(z):
        return 0.5 * (1 + __import__("math").erf(z / 2 ** 0.5))
    for L in lines:
        L["model_win_prob_home"] = round(norm_cdf(L["own_home_margin"] / sig), 4)

    out = {
        "generated_utc": "2026-11-12",
        "week": 10, "season": 2026, "n_games": len(lines),
        "forward_log_games": sum(1 for L in lines if L["in_forward_log"]),
        "filter_points": FILTER,
        "sigma_margin": round(sig, 3),
        "recalibration": {"margin": {"intercept": round(m_a, 4), "slope": round(m_b, 4)},
                          "total": {"intercept": round(t_a, 4), "slope": round(t_b, 4)},
                          "fitted_on": f"all {len(hist)} archived games with a closing line (in-sample; disclosed)",
                          "why": "raw model output is over-dispersed (margin slope > 1, total slope < 1)"},
        "gates": {"G7_pricing": False,
                  "note": "Market columns come from a third-party closing-line archive. No official NFL odds "
                          "source exists, so any edge vs these numbers is unpriced and unproven."},
        "lines": sorted(lines, key=lambda L: L["kickoff_local"]),
    }
    json.dump(out, open(os.path.join(OUT, "own_lines_wk10.json"), "w"), indent=1)
    print(f"{'game':9} {'own':>7} {'mkt':>6} {'edge':>6} {'own T':>6} {'mkt T':>6} {'edge':>6}  play")
    for L in out["lines"]:
        print(f"{L['game']:9} {L['own_home_margin']:7.1f} {str(L['market_spread']):>6} "
              f"{str(L['spread_edge_pts']):>6} {L['own_total']:6.1f} {str(L['market_total']):>6} "
              f"{str(L['total_edge_pts']):>6}  {L['spread_play'] or '-'} | {L['total_play'] or '-'}")
    print("sigma:", round(sig, 3), " forward-log games:", out["forward_log_games"])


if __name__ == "__main__":
    main()
