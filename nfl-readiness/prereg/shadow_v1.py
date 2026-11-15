"""Singles shadow baseline v1. Frozen with SHADOW_BASELINE_v1.md. Do not edit after a forecast is recorded.

Reads only official inputs saved in nfl-readiness/data/official_inputs_2026.json and writes
nfl-readiness/data/shadow_week11.json. Stdlib only.
"""
import json, math, random, sys, pathlib

SIGMA = 13.5   # ASSUMPTION of v1 (points); flagged for review
HFA = 0.0      # no home-field term in v1
SEED = 20261115

ROOT = pathlib.Path(__file__).resolve().parents[1]
inputs = json.loads((ROOT / "data" / "official_inputs_2026.json").read_text())

def phi(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))

def rating(t):
    g = t["W"] + t["L"] + t["T"]
    return (t["PF"] - t["PA"]) / g

teams = {t["abbr"]: t for t in inputs["standings"]}
confirmed = set(inputs["week10_confirmed_final_or_bye"])
games = inputs["week11_games"]  # each: {"away": "IND", "home": "HOU", "kickoff": "..."}

rng = random.Random(SEED)
forecasts, withheld = [], []
for g in games:
    a, h = g["away"], g["home"]
    missing = [x for x in (a, h) if x not in confirmed]
    if missing:
        withheld.append({**g, "reason": "Week 10 result not confirmed final in capture: " + ", ".join(missing)})
        continue
    ra, rh = rating(teams[a]), rating(teams[h])
    m = rh - ra + HFA
    p_home = phi(m / SIGMA)
    forecasts.append({
        "away": a, "home": h, "kickoff": g["kickoff"],
        "inputs": {k: {kk: teams[k][kk] for kk in ("W", "L", "T", "PF", "PA")} for k in (a, h)},
        "rating_away": round(ra, 4), "rating_home": round(rh, 4),
        "margin_home": round(m, 4), "sigma": SIGMA, "hfa": HFA,
        "p_home": round(p_home, 4), "p_away": round(1 - p_home, 4),
        "fav_control_pick": h if m > 0 else a,
        "random_control_pick": rng.choice([a, h]),
    })

out = {
    "model": "singles_shadow_baseline_v1",
    "prereg_file": "nfl-readiness/prereg/SHADOW_BASELINE_v1.md",
    "sigma_assumption_flagged": True,
    "forecasts": forecasts,
    "withheld": withheld,
    "counts": {"week11_games": len(games), "forecast": len(forecasts), "withheld": len(withheld)},
}
json.dump(out, sys.stdout, indent=2)
sys.stdout.write("\n")
