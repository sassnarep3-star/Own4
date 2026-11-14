#!/usr/bin/env python3
"""Official reference data: standings and kickoff times, read 2026-11-14.

Every row is transcribed from the page named in `source_url` for that row.
The standings were read twice from two different official views
(league and conference) and the two readings were compared value by value;
any disagreement is published, not averaged.

WEEK 10 slate kickoff times come from
https://www.nfl.com/schedules/2026/by-week/week-10 . nfl.com prints them in the
viewer's local zone, so the page string is stored verbatim as text and is NOT
converted: a converted time would be a derived value, and the page does not say
which zone the viewer was in.

Run: python3 nfl-market/data/official_reference.py -> official_reference.json
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
READ = "2026-11-14T00:00:00Z"
STANDINGS_LEAGUE = "https://www.nfl.com/standings/league/2026/REG"
STANDINGS_CONF = "https://www.nfl.com/standings/conference/2026/REG"
SCHEDULES_W10 = "https://www.nfl.com/schedules/2026/by-week/week-10"

# team, W, L, T, PF, PA, streak  -- read from BOTH standings views and identical.
STANDINGS = [
    ("BUF", 7, 1, 0, 256, 187, "4W"),
    ("SF", 7, 1, 0, 235, 156, "1W"),
    ("CHI", 7, 2, 0, 241, 184, "4W"),
    ("DEN", 7, 2, 0, 198, 186, "5W"),
    ("CIN", 6, 2, 0, 240, 175, "4W"),
    ("DET", 6, 2, 0, 222, 189, "4W"),
    ("JAX", 6, 2, 0, 229, 121, "2W"),
    ("KC", 6, 2, 0, 202, 143, "1W"),
    ("MIN", 6, 2, 0, 146, 116, "2L"),
    ("PIT", 6, 2, 0, 180, 144, "4W"),
    ("GB", 6, 3, 0, 216, 191, "2W"),
    ("NYG", 5, 3, 1, 203, 196, "1L"),
    ("CLE", 5, 4, 0, 161, 196, "2L"),
    ("LA", 5, 4, 0, 214, 181, "3W"),
    ("NE", 5, 4, 0, 211, 207, "1L"),
    ("SEA", 5, 4, 0, 202, 162, "1W"),
    ("BAL", 4, 5, 0, 189, 236, "4L"),
    ("DAL", 4, 5, 0, 246, 236, "1W"),
    ("LV", 4, 5, 0, 238, 268, "1L"),
    ("WAS", 3, 5, 1, 196, 223, "1W"),
    ("CAR", 3, 5, 0, 199, 219, "3L"),
    ("HOU", 3, 5, 0, 209, 192, "1W"),
    ("NO", 3, 5, 0, 185, 216, "1W"),
    ("AZ", 3, 6, 0, 178, 255, "1L"),
    ("ATL", 3, 6, 0, 188, 223, "2L"),
    ("TB", 3, 6, 0, 202, 178, "1L"),
    ("IND", 2, 7, 0, 184, 249, "5L"),
    ("NYJ", 2, 7, 0, 182, 223, "4L"),
    ("PHI", 2, 7, 0, 148, 221, "7L"),
    ("MIA", 1, 7, 0, 126, 200, "2L"),
    ("TEN", 1, 7, 0, 144, 199, "2L"),
    ("LAC", 0, 8, 0, 121, 219, "8L"),
]

# week 10 kickoff strings exactly as printed on the official schedule page
KICKOFFS = {
    "WAS_NYG": "8:15 PM (Thursday, November 12th)",
    "NE_DET": "9:30 AM (Sunday, November 15th)",
    "KC_ATL": "1:00 PM (Sunday, November 15th)",
    "HOU_CLE": "1:00 PM (Sunday, November 15th)",
    "MIN_GB": "1:00 PM (Sunday, November 15th)",
    "MIA_IND": "1:00 PM (Sunday, November 15th)",
    "CAR_NO": "1:00 PM (Sunday, November 15th)",
    "BUF_NYJ": "1:00 PM (Sunday, November 15th)",
    "JAX_TEN": "1:00 PM (Sunday, November 15th)",
    "LA_ARI": "4:05 PM (Sunday, November 15th)",
    "SEA_LV": "4:05 PM (Sunday, November 15th)",
    "SF_DAL": "4:25 PM (Sunday, November 15th)",
    "PIT_CIN": "4:25 PM (Sunday, November 15th)",
    "LAC_BAL": "8:15 PM (Monday, November 16th)",
}


def main():
    rows = []
    for team, w, l, t, pf, pa, stk in STANDINGS:
        rows.append({
            "team": team, "w": w, "l": l, "t": t, "pf": pf, "pa": pa,
            "diff": pf - pa, "streak": stk,
            "source_league_view": STANDINGS_LEAGUE,
            "source_conference_view": STANDINGS_CONF,
        })
    checks = {
        "rows": len(rows),
        "sum_wins": sum(r["w"] for r in rows),
        "sum_losses": sum(r["l"] for r in rows),
        "sum_ties": sum(r["t"] for r in rows),
        "sum_pf": sum(r["pf"] for r in rows),
        "sum_pa": sum(r["pa"] for r in rows),
    }
    checks["wins_equal_losses"] = checks["sum_wins"] == checks["sum_losses"]
    checks["pf_equal_pa"] = checks["sum_pf"] == checks["sum_pa"]
    out = {
        "id": "official-reference-2026-11-14",
        "read_utc": READ,
        "official": True,
        "publisher": "NFL.com",
        "standings": rows,
        "standings_checks": checks,
        "kickoffs_week10": [
            {"game": k, "printed_kickoff": v, "source_url": SCHEDULES_W10}
            for k, v in KICKOFFS.items()
        ],
    }
    with open(os.path.join(HERE, "official_reference.json"), "w",
              encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=False)
        fh.write("\n")
    print("wrote official_reference.json:", checks)


if __name__ == "__main__":
    main()
