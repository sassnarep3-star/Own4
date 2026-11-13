"""Week 10 slate and the results already on record, transcribed from nfl.com on 2026-11-13.

Two sources, kept deliberately separate:

  * SCHEDULE  -- https://www.nfl.com/schedules/2026/by-week/week-10 (read directly, 3 chunks).
                 Kick-off times, networks, venues and byes exactly as the page lists them.
  * RESULTS   -- one file per completed game. The Thursday game was read from its own official
                 game centre page; Weeks 1-9 come from the third-party archive after being
                 spot-checked against official score pages (see verify.py).

Anything the official page did not state is left as None and flagged downstream, never filled in.
"""
import json
import pathlib

SCHEDULE_URL = "https://www.nfl.com/schedules/2026/by-week/week-10"
RETRIEVED = "2026-11-13"

# away, home, date, time ET, network(s), venue, official game-centre path
SCHEDULE = [
    ("WAS", "NYG", "2026-11-12", "8:15 PM", "Prime Video", "MetLife Stadium (East Rutherford, N.J.)",
     "commanders-at-giants-2026-reg-10"),
    ("NE", "DET", "2026-11-15", "9:30 AM", "FOX", "FC Bayern Munich Stadium (Munich, Germany)",
     "patriots-at-lions-2026-reg-10"),
    ("KC", "ATL", "2026-11-15", "1:00 PM", "CBS", "Mercedes-Benz Stadium (Atlanta)",
     "chiefs-at-falcons-2026-reg-10"),
    ("HOU", "CLE", "2026-11-15", "1:00 PM", "FOX", "Huntington Bank Field (Cleveland)",
     "texans-at-browns-2026-reg-10"),
    ("MIN", "GB", "2026-11-15", "1:00 PM", "FOX", "Lambeau Field (Green Bay, Wis.)",
     "vikings-at-packers-2026-reg-10"),
    ("MIA", "IND", "2026-11-15", "1:00 PM", "CBS", "Lucas Oil Stadium (Indianapolis)",
     "dolphins-at-colts-2026-reg-10"),
    ("CAR", "NO", "2026-11-15", "1:00 PM", "FOX", "Caesars Superdome (New Orleans)",
     "panthers-at-saints-2026-reg-10"),
    ("BUF", "NYJ", "2026-11-15", "1:00 PM", "CBS", "MetLife Stadium (East Rutherford, N.J.)",
     "bills-at-jets-2026-reg-10"),
    ("JAX", "TEN", "2026-11-15", "1:00 PM", "FOX", "Nissan Stadium (Nashville, Tenn.)",
     "jaguars-at-titans-2026-reg-10"),
    ("LA", "AZ", "2026-11-15", "4:05 PM", "CBS", "State Farm Stadium (Glendale, Ariz.)",
     "rams-at-cardinals-2026-reg-10"),
    ("SEA", "LV", "2026-11-15", "4:05 PM", "CBS", "Allegiant Stadium (Las Vegas)",
     "seahawks-at-raiders-2026-reg-10"),
    ("SF", "DAL", "2026-11-15", "4:25 PM", "FOX", "AT&T Stadium (Arlington, Texas)",
     "49ers-at-cowboys-2026-reg-10"),
    ("PIT", "CIN", "2026-11-15", "8:20 PM", "NBC", "Paycor Stadium (Cincinnati)",
     "steelers-at-bengals-2026-reg-10"),
    ("LAC", "BAL", "2026-11-16", "8:15 PM", "ESPN/ABC", "M&T Bank Stadium (Baltimore)",
     "chargers-at-ravens-2026-reg-10"),
]

BYES = ["CHI", "DEN", "PHI", "TB"]

# Completed Week 10 games. Read from the official game centre page / score page.
COMPLETED = [
    {"away": "WAS", "home": "NYG", "away_score": 24, "home_score": 21,
     "quarters_away": [0, 10, 7, 7], "quarters_home": [0, 7, 7, 7],
     "source": "https://www.nfl.com/games/commanders-at-giants-2026-reg-10",
     "venue_read": "EAST RUTHERFORD, NJ / METLIFE STADIUM",
     "how_verified": "Game centre page read directly 2026-11-13: final 24-21, quarter box score "
                     "0-0 / 10-7 / 7-7 / 7-7, and the Week 10 schedule page lists the same final."},
]

DOC = {
    "id": "week10-slate-2026-11-13",
    "title": "2026 Week 10 slate and completed results",
    "schedule_source": SCHEDULE_URL,
    "retrieved": RETRIEVED,
    "columns": ["away", "home", "date", "time_et", "network", "venue", "game_url"],
    "schedule": [
        {"away": a, "home": h, "date": d, "time_et": t, "network": n, "venue": v,
         "game_url": "https://www.nfl.com/games/%s" % g}
        for (a, h, d, t, n, v, g) in SCHEDULE
    ],
    "byes": BYES,
    "completed": COMPLETED,
    "notes": [
        "Only the Thursday 2026-11-12 game had been played when this page was read.",
        "The scoring-drive list on the game centre page does not state a 4th-quarter scoring "
        "sequence that reconciles to the published 24-21 quarter box score; the quarter totals "
        "are transcribed and the drive list is not used. Flagged as F-03.",
        "Network column is the primary network; the schedule page also shows streaming "
        "alternates for several games.",
    ],
}


def main():
    out = pathlib.Path(__file__).with_suffix(".json")
    out.write_text(json.dumps(DOC, indent=1) + "\n")
    print("wrote", out.name, len(SCHEDULE), "games,", len(COMPLETED), "completed,", len(BYES), "byes")


if __name__ == "__main__":
    main()
