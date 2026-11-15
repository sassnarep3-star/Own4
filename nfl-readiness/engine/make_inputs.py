"""Writes data/official_inputs_2026.json from values transcribed from official nfl.com pages.
Every number below is copied from the cited URL (see SOURCES) and re-checked by verify.py.
"""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
# abbr: (W, L, T, PF, PA)  source: https://www.nfl.com/standings/league/2026/REG (chunks 0 and 1)
STANDINGS = {
 "BUF": (8,1,0,287,199), "SF": (7,1,0,235,156), "CHI": (7,2,0,241,184), "DEN": (7,2,0,198,186),
 "DET": (7,2,0,257,199), "JAX": (7,2,0,269,144), "KC": (7,2,0,237,156), "MIN": (7,2,0,176,126),
 "CIN": (6,2,0,240,175), "PIT": (6,2,0,180,144), "NYG": (5,3,1,203,196), "CLE": (6,4,0,188,220),
 "GB": (6,4,0,226,221), "LAR": (5,4,0,214,181), "SEA": (5,4,0,202,162), "NE": (5,5,0,221,242),
 "BAL": (4,5,0,189,236), "CAR": (4,5,0,219,236), "DAL": (4,5,0,246,236), "LV": (4,5,0,238,268),
 "WAS": (3,5,1,196,223), "ARI": (3,6,0,178,255), "HOU": (3,6,0,233,219), "NO": (3,6,0,202,236),
 "TB": (3,6,0,202,178), "ATL": (3,7,0,201,258), "IND": (3,7,0,208,271), "PHI": (2,7,0,148,221),
 "NYJ": (2,8,0,194,254), "MIA": (1,8,0,148,224), "TEN": (1,8,0,167,239), "LAC": (0,8,0,121,219),
}
# Week 10 games confirmed Final on https://www.nfl.com/schedules/2026/by-week/week-10 (chunk 0): 18 clubs.
W10_FINAL = ["WAS","NYG","NE","DET","KC","ATL","HOU","CLE","MIN","GB","MIA","IND","CAR","NO","BUF","NYJ","JAX","TEN"]
# Clubs absent from the 14 Week 10 matchups in the official injury report -> Week 10 bye (deduced).
W10_BYE = ["CHI","TB","DEN","PHI"]
# Week 11 matchups, "away at home", from https://www.nfl.com/schedules/2026/by-week/week-11 (chunks 0-2)
W11 = [
 ("IND","HOU","Thu 2026-11-19 8:15 PM ET"), ("MIA","BUF","Sun 2026-11-22 1:00 PM ET"),
 ("BAL","CAR","Sun 2026-11-22 1:00 PM ET"), ("NO","CHI","Sun 2026-11-22 1:00 PM ET"),
 ("TEN","DAL","Sun 2026-11-22 1:00 PM ET"), ("TB","DET","Sun 2026-11-22 1:00 PM ET"),
 ("ARI","KC","Sun 2026-11-22 1:00 PM ET"), ("PIT","PHI","Sun 2026-11-22 1:00 PM ET"),
 ("NYJ","LAC","Sun 2026-11-22 4:05 PM ET"), ("JAX","NYG","Sun 2026-11-22 4:25 PM ET"),
 ("LV","DEN","Sun 2026-11-22 4:25 PM ET"), ("MIN","SF","Sun 2026-11-22 8:20 PM ET"),
 ("CIN","WAS","Mon 2026-11-23 8:15 PM ET"),
]
assert len(STANDINGS) == 32 and len(W10_FINAL) + len(W10_BYE) == 22
out = {
 "captured": "bounded: between 2026-11-15T23:24:51Z and 2026-11-15T23:28:20Z (bash clock bracketing the fetch_page calls)",
 "standings_source": "https://www.nfl.com/standings/league/2026/REG",
 "week10_source": "https://www.nfl.com/schedules/2026/by-week/week-10",
 "week11_source": "https://www.nfl.com/schedules/2026/by-week/week-11",
 "abbr_note": "ARI = Arizona Cardinals (nfl.com logo code AZ)",
 "standings": [{"abbr": k, "W": v[0], "L": v[1], "T": v[2], "PF": v[3], "PA": v[4]} for k, v in STANDINGS.items()],
 "week10_confirmed_final_or_bye": W10_FINAL + W10_BYE,
 "week10_pending_at_capture": sorted(set(STANDINGS) - set(W10_FINAL + W10_BYE)),
 "week11_games": [{"away": a, "home": h, "kickoff": k} for a, h, k in W11],
}
(ROOT / "data" / "official_inputs_2026.json").write_text(json.dumps(out, indent=2) + "\n")
print("standings", len(STANDINGS), "pending", out["week10_pending_at_capture"])
