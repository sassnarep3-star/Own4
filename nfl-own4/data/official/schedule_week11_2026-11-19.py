"""Official Week-11 schedule transcription — read 2026-11-19 via page-fetch tool.

Source: https://www.nfl.com/schedules/2026/by-week/week-11
Venue column: the schedule page's own hotel-link stadium name (transcribed verbatim).
Game-centre venue: transcribed from the official game centre where read this session
(TNF IND@HOU only). The other 12 game-centre venues are blank + flagged (VF-08).

Game-centre URLs are the official game-centre links printed on the schedule page.
"""
import json
import pathlib

SOURCE_URL = "https://www.nfl.com/schedules/2026/by-week/week-11"
READ_DATE = "2026-11-19"

# (away, away_name, home, home_name, weekday, date, time, network, venue_schedule, game_centre, game_centre_venue, game_centre_location)
FIXTURES = [
    ("IND", "Indianapolis Colts", "HOU", "Houston Texans", "Thursday", "2026-11-19", "8:15 PM", "Prime Video",
     "NRG Stadium", "https://www.nfl.com/games/colts-at-texans-2026-reg-11", "Reliant Stadium", "HOUSTON, TX"),
    ("MIA", "Miami Dolphins", "BUF", "Buffalo Bills", "Sunday", "2026-11-22", "1:00 PM", "CBS",
     "Highmark Stadium", "https://www.nfl.com/games/dolphins-at-bills-2026-reg-11", None, None),
    ("BAL", "Baltimore Ravens", "CAR", "Carolina Panthers", "Sunday", "2026-11-22", "1:00 PM", "FOX",
     "Bank of America Stadium", "https://www.nfl.com/games/ravens-at-panthers-2026-reg-11", None, None),
    ("NO", "New Orleans Saints", "CHI", "Chicago Bears", "Sunday", "2026-11-22", "1:00 PM", "FOX",
     "Soldier Field", "https://www.nfl.com/games/saints-at-bears-2026-reg-11", None, None),
    ("TEN", "Tennessee Titans", "DAL", "Dallas Cowboys", "Sunday", "2026-11-22", "1:00 PM", "FOX",
     "AT&T Stadium", "https://www.nfl.com/games/titans-at-cowboys-2026-reg-11", None, None),
    ("TB", "Tampa Bay Buccaneers", "DET", "Detroit Lions", "Sunday", "2026-11-22", "1:00 PM", "FOX",
     "Ford Field", "https://www.nfl.com/games/buccaneers-at-lions-2026-reg-11", None, None),
    ("AZ", "Arizona Cardinals", "KC", "Kansas City Chiefs", "Sunday", "2026-11-22", "1:00 PM", "CBS",
     "GEHA Field at Arrowhead Stadium", "https://www.nfl.com/games/cardinals-at-chiefs-2026-reg-11", None, None),
    ("PIT", "Pittsburgh Steelers", "PHI", "Philadelphia Eagles", "Sunday", "2026-11-22", "1:00 PM", "CBS",
     "Lincoln Financial Field", "https://www.nfl.com/games/steelers-at-eagles-2026-reg-11", None, None),
    ("NYJ", "New York Jets", "LAC", "Los Angeles Chargers", "Sunday", "2026-11-22", "4:05 PM", "FOX",
     "SoFi Stadium", "https://www.nfl.com/games/jets-at-chargers-2026-reg-11", None, None),
    ("JAX", "Jacksonville Jaguars", "NYG", "New York Giants", "Sunday", "2026-11-22", "4:25 PM", "CBS",
     "MetLife Stadium", "https://www.nfl.com/games/jaguars-at-giants-2026-reg-11", None, None),
    ("LV", "Las Vegas Raiders", "DEN", "Denver Broncos", "Sunday", "2026-11-22", "4:25 PM", "CBS",
     "Empower Field at Mile High", "https://www.nfl.com/games/raiders-at-broncos-2026-reg-11", None, None),
    ("MIN", "Minnesota Vikings", "SF", "San Francisco 49ers", "Sunday", "2026-11-22", "8:20 PM", "NBC",
     "Mexico City (International Game)", "https://www.nfl.com/games/vikings-at-49ers-2026-reg-11", None, None),
    ("CIN", "Cincinnati Bengals", "WAS", "Washington Commanders", "Monday", "2026-11-23", "8:15 PM", "ESPN",
     "FedEx Field", "https://www.nfl.com/games/bengals-at-commanders-2026-reg-11", None, None),
]

BYES = [
    ("ATL", "Atlanta Falcons", "3-7"),
    ("CLE", "Cleveland Browns", "6-4"),
    ("GB", "Green Bay Packers", "6-4"),
    ("LA", "Los Angeles Rams", "6-4"),
    ("NE", "New England Patriots", "5-5"),
    ("SEA", "Seattle Seahawks", "6-4"),
]

COLUMNS = ["away", "away_name", "home", "home_name", "weekday", "date", "time", "network",
           "venue_schedule", "game_centre", "game_centre_venue", "game_centre_location"]


def main():
    out = {
        "id": "schedule-week11-2026-11-19",
        "title": "NFL Week 11 Schedule 2026 (read 2026-11-19)",
        "source_url": SOURCE_URL,
        "publisher": "NFL.com (official)",
        "read_date": READ_DATE,
        "read_route": "page-fetch tool rendered read; sandbox has no direct HTTPS egress to nfl.com",
        "columns": COLUMNS,
        "fixtures": [dict(zip(COLUMNS, f)) for f in FIXTURES],
        "byes": [{"abbr": a, "name": n, "record": r} for a, n, r in BYES],
        "venue_note": ("venue_schedule is the schedule page's hotel-link stadium name. "
                       "game_centre_venue is transcribed from the official game centre Game Info "
                       "and is populated only for TNF IND@HOU this session; the other 12 are "
                       "blank + flagged (VF-08). The IND@HOU schedule-vs-centre discrepancy "
                       "(NRG Stadium vs Reliant Stadium) is flagged VF-01; the game centre is "
                       "treated as authoritative per the brief."),
    }
    p = pathlib.Path(__file__).with_suffix(".json")
    p.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("wrote %s (%d fixtures, %d byes)" % (p, len(FIXTURES), len(BYES)))


if __name__ == "__main__":
    main()
