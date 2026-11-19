#!/usr/bin/env python3
"""Seed the nfl-verify-2026-11-19 structured data files.

Every value below was transcribed line-by-line from an official NFL page read
on 2026-11-19 via the fetch tool. Each row carries its source URL. Nothing is
inferred; unconfirmable cells are left null and flagged in flags.json.

Run:  python3 engine/seed_data.py
Writes JSON into data/ (deterministic; sorted keys, stable formatting).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
os.makedirs(DATA, exist_ok=True)

READ_DATE = "2026-11-19"
SRC_STANDINGS = "https://www.nfl.com/standings/"
SRC_SCHEDULE = "https://www.nfl.com/schedules/2026/by-week/week-11"
SRC_SCORES = "https://www.nfl.com/scores/"
SRC_INJURIES = "https://www.nfl.com/injuries/"
SRC_RESERVE = "https://www.nfl.com/transactions/league/reserve-list/2026/11"
SRC_TRADES = "https://www.nfl.com/transactions/league/trades/2026/11"
SRC_GAME_CENTRE_IND_HOU = "https://www.nfl.com/games/colts-at-texans-2026-reg-11"


def w(name, obj):
    path = os.path.join(DATA, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    print("wrote", name)


# ---------------------------------------------------------------------------
# Standings — transcribed from https://www.nfl.com/standings/ (2026-11-19).
# Fields: abbr, name, conf, division, w, l, t, pct, pf, pa, net.
# ---------------------------------------------------------------------------
standings = {
    "source": SRC_STANDINGS,
    "read_date": READ_DATE,
    "season": 2026,
    "week": "through Week 10 (records as published 2026-11-19)",
    "teams": [
        # AFC East
        {"abbr": "BUF", "name": "Buffalo Bills", "conf": "AFC", "division": "East", "w": 8, "l": 1, "t": 0, "pct": 0.889, "pf": 287, "pa": 199, "net": 88},
        {"abbr": "NE", "name": "New England Patriots", "conf": "AFC", "division": "East", "w": 5, "l": 5, "t": 0, "pct": 0.500, "pf": 221, "pa": 242, "net": -21},
        {"abbr": "NYJ", "name": "New York Jets", "conf": "AFC", "division": "East", "w": 2, "l": 8, "t": 0, "pct": 0.200, "pf": 194, "pa": 254, "net": -60},
        {"abbr": "MIA", "name": "Miami Dolphins", "conf": "AFC", "division": "East", "w": 1, "l": 8, "t": 0, "pct": 0.111, "pf": 148, "pa": 224, "net": -76},
        # AFC North
        {"abbr": "CIN", "name": "Cincinnati Bengals", "conf": "AFC", "division": "North", "w": 7, "l": 2, "t": 0, "pct": 0.778, "pf": 278, "pa": 193, "net": 85},
        {"abbr": "PIT", "name": "Pittsburgh Steelers", "conf": "AFC", "division": "North", "w": 6, "l": 3, "t": 0, "pct": 0.667, "pf": 198, "pa": 182, "net": 16},
        {"abbr": "CLE", "name": "Cleveland Browns", "conf": "AFC", "division": "North", "w": 6, "l": 4, "t": 0, "pct": 0.600, "pf": 188, "pa": 220, "net": -32},
        {"abbr": "BAL", "name": "Baltimore Ravens", "conf": "AFC", "division": "North", "w": 4, "l": 6, "t": 0, "pct": 0.400, "pf": 209, "pa": 259, "net": -50},
        # AFC South
        {"abbr": "JAX", "name": "Jacksonville Jaguars", "conf": "AFC", "division": "South", "w": 7, "l": 2, "t": 0, "pct": 0.778, "pf": 269, "pa": 144, "net": 125},
        {"abbr": "HOU", "name": "Houston Texans", "conf": "AFC", "division": "South", "w": 3, "l": 6, "t": 0, "pct": 0.333, "pf": 233, "pa": 219, "net": 14},
        {"abbr": "IND", "name": "Indianapolis Colts", "conf": "AFC", "division": "South", "w": 3, "l": 7, "t": 0, "pct": 0.300, "pf": 208, "pa": 271, "net": -63},
        {"abbr": "TEN", "name": "Tennessee Titans", "conf": "AFC", "division": "South", "w": 1, "l": 8, "t": 0, "pct": 0.111, "pf": 167, "pa": 239, "net": -72},
        # AFC West
        {"abbr": "KC", "name": "Kansas City Chiefs", "conf": "AFC", "division": "West", "w": 7, "l": 2, "t": 0, "pct": 0.778, "pf": 237, "pa": 156, "net": 81},
        {"abbr": "DEN", "name": "Denver Broncos", "conf": "AFC", "division": "West", "w": 7, "l": 2, "t": 0, "pct": 0.778, "pf": 198, "pa": 186, "net": 12},
        {"abbr": "LV", "name": "Las Vegas Raiders", "conf": "AFC", "division": "West", "w": 4, "l": 6, "t": 0, "pct": 0.400, "pf": 251, "pa": 289, "net": -38},
        {"abbr": "LAC", "name": "Los Angeles Chargers", "conf": "AFC", "division": "West", "w": 1, "l": 8, "t": 0, "pct": 0.111, "pf": 144, "pa": 239, "net": -95},
        # NFC East
        {"abbr": "NYG", "name": "New York Giants", "conf": "NFC", "division": "East", "w": 5, "l": 3, "t": 1, "pct": 0.611, "pf": 203, "pa": 196, "net": 7},
        {"abbr": "DAL", "name": "Dallas Cowboys", "conf": "NFC", "division": "East", "w": 4, "l": 6, "t": 0, "pct": 0.400, "pf": 286, "pa": 282, "net": 4},
        {"abbr": "WAS", "name": "Washington Commanders", "conf": "NFC", "division": "East", "w": 3, "l": 5, "t": 1, "pct": 0.389, "pf": 196, "pa": 223, "net": -27},
        {"abbr": "PHI", "name": "Philadelphia Eagles", "conf": "NFC", "division": "East", "w": 2, "l": 7, "t": 0, "pct": 0.222, "pf": 148, "pa": 221, "net": -73},
        # NFC North
        {"abbr": "DET", "name": "Detroit Lions", "conf": "NFC", "division": "North", "w": 7, "l": 2, "t": 0, "pct": 0.778, "pf": 257, "pa": 199, "net": 58},
        {"abbr": "MIN", "name": "Minnesota Vikings", "conf": "NFC", "division": "North", "w": 7, "l": 2, "t": 0, "pct": 0.778, "pf": 176, "pa": 126, "net": 50},
        {"abbr": "CHI", "name": "Chicago Bears", "conf": "NFC", "division": "North", "w": 7, "l": 2, "t": 0, "pct": 0.778, "pf": 241, "pa": 184, "net": 57},
        {"abbr": "GB", "name": "Green Bay Packers", "conf": "NFC", "division": "North", "w": 6, "l": 4, "t": 0, "pct": 0.600, "pf": 226, "pa": 221, "net": 5},
        # NFC South
        {"abbr": "CAR", "name": "Carolina Panthers", "conf": "NFC", "division": "South", "w": 4, "l": 5, "t": 0, "pct": 0.444, "pf": 219, "pa": 236, "net": -17},
        {"abbr": "TB", "name": "Tampa Bay Buccaneers", "conf": "NFC", "division": "South", "w": 3, "l": 6, "t": 0, "pct": 0.333, "pf": 202, "pa": 178, "net": 24},
        {"abbr": "NO", "name": "New Orleans Saints", "conf": "NFC", "division": "South", "w": 3, "l": 6, "t": 0, "pct": 0.333, "pf": 202, "pa": 236, "net": -34},
        {"abbr": "ATL", "name": "Atlanta Falcons", "conf": "NFC", "division": "South", "w": 3, "l": 7, "t": 0, "pct": 0.300, "pf": 201, "pa": 258, "net": -57},
        # NFC West
        {"abbr": "SF", "name": "San Francisco 49ers", "conf": "NFC", "division": "West", "w": 8, "l": 1, "t": 0, "pct": 0.889, "pf": 281, "pa": 196, "net": 85},
        {"abbr": "SEA", "name": "Seattle Seahawks", "conf": "NFC", "division": "West", "w": 6, "l": 4, "t": 0, "pct": 0.600, "pf": 223, "pa": 175, "net": 48},
        {"abbr": "LA", "name": "Los Angeles Rams", "conf": "NFC", "division": "West", "w": 6, "l": 4, "t": 0, "pct": 0.600, "pf": 248, "pa": 187, "net": 61},
        {"abbr": "AZ", "name": "Arizona Cardinals", "conf": "NFC", "division": "West", "w": 3, "l": 7, "t": 0, "pct": 0.300, "pf": 184, "pa": 289, "net": -105},
    ],
}
w("standings_2026_11_19.json", standings)

# ---------------------------------------------------------------------------
# Week 11 schedule — transcribed from https://www.nfl.com/schedules/2026/by-week/week-11
# Venue from the schedule page's own stadium links (Marriott destination names).
# The TNF venue was additionally verified against the official game centre.
# ---------------------------------------------------------------------------
schedule = {
    "source": SRC_SCHEDULE,
    "read_date": READ_DATE,
    "season": 2026,
    "week": 11,
    "venue_note": "Venue transcribed from the schedule page's own stadium/hotel links; "
                  "TNF venue cross-checked against the official game centre Game Info.",
    "fixtures": [
        {"weekday": "Thursday", "date": "2026-11-19", "time": "8:15 PM", "network": "Prime Video", "away": "IND", "away_name": "Indianapolis Colts", "home": "HOU", "home_name": "Houston Texans", "venue": "NRG Stadium", "venue_source": SRC_SCHEDULE, "game_centre": SRC_GAME_CENTRE_IND_HOU, "game_centre_venue": "Reliant Stadium", "game_centre_location": "HOUSTON, TX"},
        {"weekday": "Sunday", "date": "2026-11-22", "time": "1:00 PM", "network": "CBS", "away": "MIA", "away_name": "Miami Dolphins", "home": "BUF", "home_name": "Buffalo Bills", "venue": "Highmark Stadium", "venue_source": SRC_SCHEDULE, "game_centre": None, "game_centre_venue": None, "game_centre_location": None},
        {"weekday": "Sunday", "date": "2026-11-22", "time": "1:00 PM", "network": "FOX", "away": "BAL", "away_name": "Baltimore Ravens", "home": "CAR", "home_name": "Carolina Panthers", "venue": "Bank of America Stadium", "venue_source": SRC_SCHEDULE, "game_centre": None, "game_centre_venue": None, "game_centre_location": None},
        {"weekday": "Sunday", "date": "2026-11-22", "time": "1:00 PM", "network": "FOX", "away": "NO", "away_name": "New Orleans Saints", "home": "CHI", "home_name": "Chicago Bears", "venue": "Soldier Field", "venue_source": SRC_SCHEDULE, "game_centre": None, "game_centre_venue": None, "game_centre_location": None},
        {"weekday": "Sunday", "date": "2026-11-22", "time": "1:00 PM", "network": "FOX", "away": "TEN", "away_name": "Tennessee Titans", "home": "DAL", "home_name": "Dallas Cowboys", "venue": "AT&T Stadium", "venue_source": SRC_SCHEDULE, "game_centre": None, "game_centre_venue": None, "game_centre_location": None},
        {"weekday": "Sunday", "date": "2026-11-22", "time": "1:00 PM", "network": "FOX", "away": "TB", "away_name": "Tampa Bay Buccaneers", "home": "DET", "home_name": "Detroit Lions", "venue": "Ford Field", "venue_source": SRC_SCHEDULE, "game_centre": None, "game_centre_venue": None, "game_centre_location": None},
        {"weekday": "Sunday", "date": "2026-11-22", "time": "1:00 PM", "network": "CBS", "away": "AZ", "away_name": "Arizona Cardinals", "home": "KC", "home_name": "Kansas City Chiefs", "venue": "GEHA Field at Arrowhead Stadium", "venue_source": SRC_SCHEDULE, "game_centre": None, "game_centre_venue": None, "game_centre_location": None},
        {"weekday": "Sunday", "date": "2026-11-22", "time": "1:00 PM", "network": "CBS", "away": "PIT", "away_name": "Pittsburgh Steelers", "home": "PHI", "home_name": "Philadelphia Eagles", "venue": "Lincoln Financial Field", "venue_source": SRC_SCHEDULE, "game_centre": None, "game_centre_venue": None, "game_centre_location": None},
        {"weekday": "Sunday", "date": "2026-11-22", "time": "4:05 PM", "network": "FOX", "away": "NYJ", "away_name": "New York Jets", "home": "LAC", "home_name": "Los Angeles Chargers", "venue": "SoFi Stadium", "venue_source": SRC_SCHEDULE, "game_centre": None, "game_centre_venue": None, "game_centre_location": None},
        {"weekday": "Sunday", "date": "2026-11-22", "time": "4:25 PM", "network": "CBS", "away": "JAX", "away_name": "Jacksonville Jaguars", "home": "NYG", "home_name": "New York Giants", "venue": "MetLife Stadium", "venue_source": SRC_SCHEDULE, "game_centre": None, "game_centre_venue": None, "game_centre_location": None},
        {"weekday": "Sunday", "date": "2026-11-22", "time": "4:25 PM", "network": "CBS", "away": "LV", "away_name": "Las Vegas Raiders", "home": "DEN", "home_name": "Denver Broncos", "venue": "Empower Field at Mile High", "venue_source": SRC_SCHEDULE, "game_centre": None, "game_centre_venue": None, "game_centre_location": None},
        {"weekday": "Sunday", "date": "2026-11-22", "time": "8:20 PM", "network": "NBC", "away": "MIN", "away_name": "Minnesota Vikings", "home": "SF", "home_name": "San Francisco 49ers", "venue": "Mexico City (International Game)", "venue_source": SRC_SCHEDULE, "game_centre": None, "game_centre_venue": None, "game_centre_location": None},
        {"weekday": "Monday", "date": "2026-11-23", "time": "8:15 PM", "network": "ESPN", "away": "CIN", "away_name": "Cincinnati Bengals", "home": "WAS", "home_name": "Washington Commanders", "venue": "FedEx Field", "venue_source": SRC_SCHEDULE, "game_centre": None, "game_centre_venue": None, "game_centre_location": None},
    ],
    "byes": [
        {"abbr": "ATL", "name": "Atlanta Falcons", "record": "3-7"},
        {"abbr": "CLE", "name": "Cleveland Browns", "record": "6-4"},
        {"abbr": "GB", "name": "Green Bay Packers", "record": "6-4"},
        {"abbr": "LA", "name": "Los Angeles Rams", "record": "6-4"},
        {"abbr": "NE", "name": "New England Patriots", "record": "5-5"},
        {"abbr": "SEA", "name": "Seattle Seahawks", "record": "6-4"},
    ],
}
w("schedule_week11_2026_11_19.json", schedule)

# ---------------------------------------------------------------------------
# Injury report — Week 11, read 2026-11-19.
# 10 clubs transcribed in full from https://www.nfl.com/injuries/ (chunks 0-1).
# Remaining clubs not re-read live this session -> flagged in flags.json.
# ---------------------------------------------------------------------------
injuries = {
    "source": SRC_INJURIES,
    "read_date": READ_DATE,
    "season": 2026,
    "week": 11,
    "report_title": "Official Latest NFL Injury Report for Players - Week 11 of the 2026 Season",
    "clubs_read": ["IND", "HOU", "PIT", "PHI", "AZ", "KC", "BAL", "CAR", "TB", "DET"],
    "clubs_not_recounted": "The full 32-club report was not recounted live this session; the 10 clubs "
                           "below were transcribed in full. Row counts for the other clubs are not "
                           "asserted and are flagged.",
    "rows": [
        # IND
        {"club": "IND", "player": "Jaylon Carlies", "position": "LB", "injury": "", "practice": "Did Not Participate In Practice", "game_status": "", "url": "https://www.nfl.com/players/jaylon-carlies/"},
        {"club": "IND", "player": "Sauce Gardner", "position": "CB", "injury": "Calf", "practice": "Did Not Participate In Practice", "game_status": "Questionable", "url": "https://www.nfl.com/players/sauce-gardner/"},
        {"club": "IND", "player": "Anthony Gould", "position": "WR", "injury": "Toe", "practice": "Full Participation in Practice", "game_status": "Questionable", "url": "https://www.nfl.com/players/anthony-gould/"},
        {"club": "IND", "player": "Charlie Heck", "position": "T", "injury": "Not injury related - personal matter", "practice": "Did Not Participate In Practice", "game_status": "Questionable", "url": "https://www.nfl.com/players/charlie-heck/"},
        {"club": "IND", "player": "Will Mallory", "position": "TE", "injury": "Hamstring", "practice": "Did Not Participate In Practice", "game_status": "Out", "url": "https://www.nfl.com/players/will-mallory/"},
        {"club": "IND", "player": "Bernhard Raimann", "position": "T", "injury": "Concussion", "practice": "Did Not Participate In Practice", "game_status": "Out", "url": "https://www.nfl.com/players/bernhard-raimann/"},
        {"club": "IND", "player": "Luke Rhodes", "position": "LS", "injury": "Hamstring", "practice": "Limited Participation in Practice", "game_status": "Questionable", "url": "https://www.nfl.com/players/luke-rhodes/"},
        {"club": "IND", "player": "Jerry Tillery", "position": "DT", "injury": "Calf", "practice": "Did Not Participate In Practice", "game_status": "Out", "url": "https://www.nfl.com/players/jerry-tillery/"},
        {"club": "IND", "player": "Jalen Travis", "position": "T", "injury": "Knee", "practice": "Did Not Participate In Practice", "game_status": "Out", "url": "https://www.nfl.com/players/jalen-travis/"},
        {"club": "IND", "player": "Dalton Tucker", "position": "G", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/dalton-tucker/"},
        {"club": "IND", "player": "Charvarius Ward", "position": "CB", "injury": "Knee", "practice": "Did Not Participate In Practice", "game_status": "Out", "url": "https://www.nfl.com/players/charvarius-ward/"},
        # HOU
        {"club": "HOU", "player": "Azeez Al-Shaair", "position": "LB", "injury": "", "practice": "Did Not Participate In Practice", "game_status": "", "url": "https://www.nfl.com/players/azeez-al-shaair/"},
        {"club": "HOU", "player": "Reed Blankenship", "position": "S", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/reed-blankenship/"},
        {"club": "HOU", "player": "Tank Dell", "position": "WR", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/tank-dell/"},
        {"club": "HOU", "player": "Blake Fisher", "position": "T", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/blake-fisher/"},
        {"club": "HOU", "player": "Marvin Harrison Jr.", "position": "WR", "injury": "Hamstring", "practice": "Did Not Participate In Practice", "game_status": "Out", "url": "https://www.nfl.com/players/marvin-harrison-jr/"},
        {"club": "HOU", "player": "Jacob Hummel", "position": "LB", "injury": "Groin", "practice": "Full Participation in Practice", "game_status": "Questionable", "url": "https://www.nfl.com/players/jake-hummel/"},
        {"club": "HOU", "player": "Danielle Hunter", "position": "DE", "injury": "Hamstring", "practice": "Did Not Participate In Practice", "game_status": "Out", "url": "https://www.nfl.com/players/danielle-hunter/"},
        {"club": "HOU", "player": "Brevin Jordan", "position": "TE", "injury": "Foot, Illness", "practice": "Did Not Participate In Practice", "game_status": "Out", "url": "https://www.nfl.com/players/brevin-jordan/"},
        {"club": "HOU", "player": "Kamari Lassiter", "position": "CB", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/kamari-lassiter/"},
        {"club": "HOU", "player": "Woody Marks", "position": "RB", "injury": "Concussion", "practice": "Did Not Participate In Practice", "game_status": "Out", "url": "https://www.nfl.com/players/woody-marks/"},
        {"club": "HOU", "player": "David Montgomery", "position": "RB", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/david-montgomery/"},
        {"club": "HOU", "player": "Febechi Nwaiwu", "position": "G", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/febechi-nwaiwu/"},
        {"club": "HOU", "player": "Keylan Rutledge", "position": "G", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/keylan-rutledge/"},
        {"club": "HOU", "player": "Jaylin Smith", "position": "CB", "injury": "Hamstring", "practice": "Full Participation in Practice", "game_status": "Questionable", "url": "https://www.nfl.com/players/jaylin-smith/"},
        {"club": "HOU", "player": "Wyatt Teller", "position": "G", "injury": "Back", "practice": "Full Participation in Practice", "game_status": "Questionable", "url": "https://www.nfl.com/players/wyatt-teller/"},
        # PIT
        {"club": "PIT", "player": "Gennings Dunker", "position": "G", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/gennings-dunker/"},
        {"club": "PIT", "player": "DeShon Elliott", "position": "S", "injury": "", "practice": "Limited Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/deshon-elliott/"},
        {"club": "PIT", "player": "Nick Herbig", "position": "LB", "injury": "", "practice": "Did Not Participate In Practice", "game_status": "", "url": "https://www.nfl.com/players/nick-herbig/"},
        {"club": "PIT", "player": "Cameron Heyward", "position": "DT", "injury": "", "practice": "Did Not Participate In Practice", "game_status": "", "url": "https://www.nfl.com/players/cameron-heyward/"},
        {"club": "PIT", "player": "Michael Pittman", "position": "WR", "injury": "", "practice": "Limited Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/michael-pittman-2/"},
        {"club": "PIT", "player": "Patrick Queen", "position": "LB", "injury": "", "practice": "Limited Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/patrick-queen/"},
        {"club": "PIT", "player": "Jalen Ramsey", "position": "CB", "injury": "", "practice": "Did Not Participate In Practice", "game_status": "", "url": "https://www.nfl.com/players/jalen-ramsey/"},
        {"club": "PIT", "player": "Darnell Washington", "position": "TE", "injury": "", "practice": "Did Not Participate In Practice", "game_status": "", "url": "https://www.nfl.com/players/darnell-washington/"},
        {"club": "PIT", "player": "T.J. Watt", "position": "LB", "injury": "", "practice": "Did Not Participate In Practice", "game_status": "", "url": "https://www.nfl.com/players/t-j-watt/"},
        {"club": "PIT", "player": "Roman Wilson", "position": "WR", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/roman-wilson/"},
        # PHI
        {"club": "PHI", "player": "Saquon Barkley", "position": "RB", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/saquon-barkley/"},
        {"club": "PHI", "player": "Zack Baun", "position": "LB", "injury": "", "practice": "Did Not Participate In Practice", "game_status": "", "url": "https://www.nfl.com/players/zack-baun/"},
        {"club": "PHI", "player": "Jihaad Campbell", "position": "LB", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/jihaad-campbell/"},
        {"club": "PHI", "player": "Michael Carter II", "position": "CB", "injury": "", "practice": "Limited Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/michael-carter-ii/"},
        {"club": "PHI", "player": "Britain Covey", "position": "WR", "injury": "", "practice": "Limited Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/britain-covey/"},
        {"club": "PHI", "player": "Jonathan Greenard", "position": "LB", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/jonathan-greenard/"},
        {"club": "PHI", "player": "Jalyx Hunt", "position": "LB", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/jalyx-hunt/"},
        {"club": "PHI", "player": "Jonathan Jones", "position": "CB", "injury": "", "practice": "Limited Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/jonathan-jones/"},
        {"club": "PHI", "player": "Tanner McKee", "position": "QB", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/tanner-mckee/"},
        {"club": "PHI", "player": "Smael Mondon Jr.", "position": "LB", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/smael-mondon-jr/"},
        {"club": "PHI", "player": "Andrew Mukuba", "position": "S", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/andrew-mukuba/"},
        {"club": "PHI", "player": "Will Shipley", "position": "RB", "injury": "", "practice": "Limited Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/will-shipley/"},
        {"club": "PHI", "player": "DeVonta Smith", "position": "WR", "injury": "", "practice": "Limited Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/devonta-smith/"},
        {"club": "PHI", "player": "Nolan Smith", "position": "LB", "injury": "", "practice": "Limited Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/nolan-smith/"},
        {"club": "PHI", "player": "Dontayvion Wicks", "position": "WR", "injury": "", "practice": "Limited Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/dontayvion-wicks/"},
        # AZ
        {"club": "AZ", "player": "Budda Baker", "position": "S", "injury": "", "practice": "Did Not Participate In Practice", "game_status": "", "url": "https://www.nfl.com/players/budda-baker/"},
        {"club": "AZ", "player": "Zachary Carter", "position": "DT", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/zachary-carter-x9168/"},
        {"club": "AZ", "player": "Hjalte Froholdt", "position": "C", "injury": "", "practice": "Limited Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/hjalte-froholdt/"},
        {"club": "AZ", "player": "Jon Gaines II", "position": "G", "injury": "", "practice": "Limited Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/jon-gaines-ii/"},
        {"club": "AZ", "player": "Roy Lopez", "position": "DT", "injury": "", "practice": "Limited Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/roy-lopez/"},
        {"club": "AZ", "player": "Max Melton", "position": "CB", "injury": "", "practice": "Limited Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/max-melton/"},
        {"club": "AZ", "player": "Walter Nolen", "position": "DT", "injury": "", "practice": "Did Not Participate In Practice", "game_status": "", "url": "https://www.nfl.com/players/walter-nolen/"},
        {"club": "AZ", "player": "Darius Robinson", "position": "DT", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/darius-robinson-2/"},
        {"club": "AZ", "player": "Isaac Seumalo", "position": "G", "injury": "", "practice": "Did Not Participate In Practice", "game_status": "", "url": "https://www.nfl.com/players/isaac-seumalo/"},
        {"club": "AZ", "player": "Josh Sweat", "position": "LB", "injury": "", "practice": "Did Not Participate In Practice", "game_status": "", "url": "https://www.nfl.com/players/josh-sweat/"},
        {"club": "AZ", "player": "Jayden Williams", "position": "T", "injury": "", "practice": "Limited Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/jayden-williams/"},
        {"club": "AZ", "player": "Mack Wilson", "position": "LB", "injury": "", "practice": "Did Not Participate In Practice", "game_status": "", "url": "https://www.nfl.com/players/mack-wilson/"},
        # KC
        {"club": "KC", "player": "Jeffrey Bassa", "position": "LB", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/jeffrey-bassa/"},
        {"club": "KC", "player": "Nick Bolton", "position": "LB", "injury": "", "practice": "Limited Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/nick-bolton/"},
        {"club": "KC", "player": "Jadon Canady", "position": "CB", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/jadon-canady/"},
        {"club": "KC", "player": "Mansoor Delane", "position": "CB", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/mansoor-delane/"},
        {"club": "KC", "player": "Justin Fields", "position": "QB", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/justin-fields/"},
        {"club": "KC", "player": "Alohi Gilman", "position": "S", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/alohi-gilman/"},
        {"club": "KC", "player": "Travis Kelce", "position": "TE", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/travis-kelce/"},
        {"club": "KC", "player": "Patrick Mahomes", "position": "QB", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/patrick-mahomes/"},
        {"club": "KC", "player": "Jaylon Moore", "position": "T", "injury": "", "practice": "Did Not Participate In Practice", "game_status": "", "url": "https://www.nfl.com/players/jaylon-moore-2/"},
        {"club": "KC", "player": "Omarr Norman-Lott", "position": "DT", "injury": "", "practice": "Limited Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/omarr-norman-lott/"},
        {"club": "KC", "player": "Jaydn Ott", "position": "RB", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/jaydn-ott/"},
        {"club": "KC", "player": "Rashee Rice", "position": "WR", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/rashee-rice/"},
        {"club": "KC", "player": "Trey Smith", "position": "G", "injury": "", "practice": "Did Not Participate In Practice", "game_status": "", "url": "https://www.nfl.com/players/trey-smith/"},
        {"club": "KC", "player": "Kenneth Walker III", "position": "RB", "injury": "", "practice": "Did Not Participate In Practice", "game_status": "", "url": "https://www.nfl.com/players/kenneth-walker-iii/"},
        {"club": "KC", "player": "Peter Woods", "position": "DT", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/peter-woods/"},
        # BAL
        {"club": "BAL", "player": "Mike Green", "position": "LB", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/mike-green-5/"},
        {"club": "BAL", "player": "Jaylinn Hawkins", "position": "S", "injury": "", "practice": "Limited Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/jaylinn-hawkins/"},
        {"club": "BAL", "player": "Matthew Hibner", "position": "TE", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/matthew-hibner/"},
        {"club": "BAL", "player": "Olaivavega Ioane", "position": "G", "injury": "", "practice": "Limited Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/olaivavega-ioane/"},
        {"club": "BAL", "player": "Nnamdi Madubuike", "position": "DT", "injury": "", "practice": "Did Not Participate In Practice", "game_status": "", "url": "https://www.nfl.com/players/nnamdi-madubuike/"},
        {"club": "BAL", "player": "Adam Randall", "position": "RB", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/adam-randall/"},
        # CAR
        {"club": "CAR", "player": "Jonathon Brooks", "position": "RB", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/jonathon-brooks/"},
        {"club": "CAR", "player": "Brady Christensen", "position": "G", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/brady-christensen/"},
        {"club": "CAR", "player": "Feleipe Franks", "position": "TE", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/feleipe-franks/"},
        {"club": "CAR", "player": "Trevis Gipson", "position": "LB", "injury": "", "practice": "Limited Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/trevis-gipson/"},
        {"club": "CAR", "player": "Chuba Hubbard", "position": "RB", "injury": "", "practice": "Did Not Participate In Practice", "game_status": "", "url": "https://www.nfl.com/players/chuba-hubbard/"},
        {"club": "CAR", "player": "Mike Jackson", "position": "CB", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/mike-jackson/"},
        {"club": "CAR", "player": "Jackson Kuwatch", "position": "LB", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/jackson-kuwatch/"},
        {"club": "CAR", "player": "Will Lee III", "position": "CB", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/will-lee-iii/"},
        {"club": "CAR", "player": "Bobby Okereke", "position": "LB", "injury": "", "practice": "Did Not Participate In Practice", "game_status": "", "url": "https://www.nfl.com/players/bobby-okereke/"},
        {"club": "CAR", "player": "Isaiah Simmons", "position": "S", "injury": "", "practice": "Did Not Participate In Practice", "game_status": "", "url": "https://www.nfl.com/players/isaiah-simmons/"},
        {"club": "CAR", "player": "Tommy Tremble", "position": "TE", "injury": "", "practice": "Did Not Participate In Practice", "game_status": "", "url": "https://www.nfl.com/players/tommy-tremble/"},
        {"club": "CAR", "player": "Darren Waller", "position": "TE", "injury": "", "practice": "Did Not Participate In Practice", "game_status": "", "url": "https://www.nfl.com/players/darren-waller/"},
        {"club": "CAR", "player": "Bryce Young", "position": "QB", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/bryce-young/"},
        # TB
        {"club": "TB", "player": "Yaya Diaby", "position": "LB", "injury": "", "practice": "Limited Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/yaya-diaby/"},
        {"club": "TB", "player": "Josh Hayes", "position": "CB", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/josh-hayes/"},
        {"club": "TB", "player": "Baker Mayfield", "position": "QB", "injury": "", "practice": "Did Not Participate In Practice", "game_status": "", "url": "https://www.nfl.com/players/baker-mayfield/"},
        {"club": "TB", "player": "Cade Otton", "position": "TE", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/cade-otton/"},
        {"club": "TB", "player": "Antoine Winfield Jr.", "position": "S", "injury": "", "practice": "Did Not Participate In Practice", "game_status": "", "url": "https://www.nfl.com/players/antoine-winfield-jr/"},
        {"club": "TB", "player": "Tristan Wirfs", "position": "T", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/tristan-wirfs/"},
        # DET
        {"club": "DET", "player": "Joe Bachie", "position": "LB", "injury": "", "practice": "Limited Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/joe-bachie/"},
        {"club": "DET", "player": "Khalil Dorsey", "position": "CB", "injury": "", "practice": "Limited Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/khalil-dorsey/"},
        {"club": "DET", "player": "Kerby Joseph", "position": "S", "injury": "", "practice": "Full Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/kerby-joseph/"},
        {"club": "DET", "player": "Tyler Lacy", "position": "DE", "injury": "", "practice": "Limited Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/tyler-lacy/"},
        {"club": "DET", "player": "Cade Mays", "position": "C", "injury": "", "practice": "Did Not Participate In Practice", "game_status": "", "url": "https://www.nfl.com/players/cade-mays/"},
        {"club": "DET", "player": "Ennis Rakestraw Jr.", "position": "CB", "injury": "", "practice": "Limited Participation In Practice", "game_status": "", "url": "https://www.nfl.com/players/ennis-rakestraw-jr/"},
        {"club": "DET", "player": "D.J. Reed", "position": "CB", "injury": "", "practice": "Limited Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/d-j-reed/"},
        {"club": "DET", "player": "Sione Vaki", "position": "RB", "injury": "", "practice": "Limited Participation in Practice", "game_status": "", "url": "https://www.nfl.com/players/sione-vaki/"},
    ],
}
w("injuries_2026_11_19.json", injuries)

# ---------------------------------------------------------------------------
# Reserve list — November 2026, complete (25 Reserve/Injured moves).
# ---------------------------------------------------------------------------
reserve = {
    "source": SRC_RESERVE,
    "read_date": READ_DATE,
    "month": "2026-11",
    "entries": [
        {"date": "11/18", "club": "PIT", "name": "Mason McCormick", "position": "", "transaction": "Reserve/Injured", "url": "https://www.nfl.com/players/mason-mccormick/"},
        {"date": "11/18", "club": "KC", "name": "Jared Wiley", "position": "", "transaction": "Reserve/Injured", "url": "https://www.nfl.com/players/jared-wiley/"},
        {"date": "11/18", "club": "DET", "name": "Aidan Hutchinson", "position": "", "transaction": "Reserve/Injured", "url": "https://www.nfl.com/players/aidan-hutchinson/"},
        {"date": "11/18", "club": "MIN", "name": "Bo Richter", "position": "", "transaction": "Reserve/Injured", "url": "https://www.nfl.com/players/bo-richter/"},
        {"date": "11/17", "club": "HOU", "name": "Azeez Al-Shaair", "position": "", "transaction": "Reserve/Injured", "url": "https://www.nfl.com/players/azeez-al-shaair/"},
        {"date": "11/17", "club": "MIA", "name": "Zeek Biggers", "position": "", "transaction": "Reserve/Injured", "url": "https://www.nfl.com/players/zeek-biggers/"},
        {"date": "11/17", "club": "MIA", "name": "Jordan Phillips", "position": "", "transaction": "Reserve/Injured", "url": "https://www.nfl.com/players/jordan-phillips-2/"},
        {"date": "11/17", "club": "AZ", "name": "Andrew Wingard", "position": "", "transaction": "Reserve/Injured", "url": "https://www.nfl.com/players/andrew-wingard/"},
        {"date": "11/17", "club": "AZ", "name": "Jordan Burch", "position": "", "transaction": "Reserve/Injured", "url": "https://www.nfl.com/players/jordan-burch/"},
        {"date": "11/17", "club": "BUF", "name": "Ar'maj Reed-Adams", "position": "", "transaction": "Reserve/Injured", "url": "https://www.nfl.com/players/ar-maj-reed-adams/"},
        {"date": "11/17", "club": "IND", "name": "Jaylon Carlies", "position": "", "transaction": "Reserve/Injured", "url": "https://www.nfl.com/players/jaylon-carlies/"},
        {"date": "11/17", "club": "TEN", "name": "Wan'Dale Robinson", "position": "", "transaction": "Reserve/Injured", "url": "https://www.nfl.com/players/wan-dale-robinson/"},
        {"date": "11/16", "club": "LA", "name": "Dylan McMahon", "position": "", "transaction": "Reserve/Injured", "url": "https://www.nfl.com/players/dylan-mcmahon/"},
        {"date": "11/16", "club": "LAC", "name": "Branson Taylor", "position": "", "transaction": "Reserve/Injured", "url": "https://www.nfl.com/players/branson-taylor/"},
        {"date": "11/14", "club": "NO", "name": "Christen Miller", "position": "", "transaction": "Reserve/Injured", "url": "https://www.nfl.com/players/christen-miller/"},
        {"date": "11/14", "club": "NE", "name": "TreVeyon Henderson", "position": "", "transaction": "Reserve/Injured", "url": "https://www.nfl.com/players/treveyon-henderson/"},
        {"date": "11/14", "club": "CLE", "name": "Michael Burton", "position": "", "transaction": "Reserve/Injured", "url": "https://www.nfl.com/players/michael-burton/"},
        {"date": "11/14", "club": "IND", "name": "Mo Alie-Cox", "position": "", "transaction": "Reserve/Injured", "url": "https://www.nfl.com/players/mo-alie-cox/"},
        {"date": "11/14", "club": "IND", "name": "Akeem Davis-Gaither", "position": "", "transaction": "Reserve/Injured", "url": "https://www.nfl.com/players/akeem-davis-gaither/"},
        {"date": "11/14", "club": "TEN", "name": "Peter Skoronski", "position": "", "transaction": "Reserve/Injured", "url": "https://www.nfl.com/players/peter-skoronski/"},
        {"date": "11/14", "club": "TEN", "name": "Tommy Townsend", "position": "", "transaction": "Reserve/Injured", "url": "https://www.nfl.com/players/tommy-townsend/"},
        {"date": "11/14", "club": "DAL", "name": "Tyler Goodson", "position": "", "transaction": "Reserve/Injured", "url": "https://www.nfl.com/players/tyler-goodson/"},
        {"date": "11/14", "club": "GB", "name": "Josh Whyle", "position": "", "transaction": "Reserve/Injured", "url": "https://www.nfl.com/players/josh-whyle/"},
        {"date": "11/12", "club": "LA", "name": "Puka Nacua", "position": "", "transaction": "Reserve/Injured", "url": "https://www.nfl.com/players/puka-nacua/"},
        {"date": "11/10", "club": "LA", "name": "Jordan Whittington", "position": "", "transaction": "Reserve/Injured", "url": "https://www.nfl.com/players/jordan-whittington/"},
    ],
}
w("reserve_list_2026_11.json", reserve)

# ---------------------------------------------------------------------------
# Trades — November 2026, complete (12 trades).
# ---------------------------------------------------------------------------
trades = {
    "source": SRC_TRADES,
    "read_date": READ_DATE,
    "month": "2026-11",
    "entries": [
        {"date": "11/10", "from_club": "ATL", "to_club": "JAX", "name": "Jessie Bates", "position": "", "transaction": "Traded", "url": "https://www.nfl.com/players/jessie-bates/"},
        {"date": "11/10", "from_club": "PHI", "to_club": "JAX", "name": "Jordan Davis", "position": "", "transaction": "Traded", "url": "https://www.nfl.com/players/jordan-davis/"},
        {"date": "11/10", "from_club": "TEN", "to_club": "BUF", "name": "Amani Hooker", "position": "", "transaction": "Traded", "url": "https://www.nfl.com/players/amani-hooker/"},
        {"date": "11/10", "from_club": "IND", "to_club": "SF", "name": "Keenan Allen", "position": "", "transaction": "Traded", "url": "https://www.nfl.com/players/keenan-allen/"},
        {"date": "11/10", "from_club": "LV", "to_club": "MIN", "name": "Kirk Cousins", "position": "", "transaction": "Traded", "url": "https://www.nfl.com/players/kirk-cousins/"},
        {"date": "11/10", "from_club": "LAC", "to_club": "DEN", "name": "Daiyan Henley", "position": "", "transaction": "Traded", "url": "https://www.nfl.com/players/daiyan-henley/"},
        {"date": "11/10", "from_club": "IND", "to_club": "KC", "name": "Josh Downs", "position": "", "transaction": "Traded", "url": "https://www.nfl.com/players/josh-downs/"},
        {"date": "11/10", "from_club": "ATL", "to_club": "BAL", "name": "Ryan Neuzil", "position": "", "transaction": "Traded", "url": "https://www.nfl.com/players/ryan-neuzil/"},
        {"date": "11/10", "from_club": "BAL", "to_club": "ATL", "name": "Andrew Vorhees", "position": "", "transaction": "Traded", "url": "https://www.nfl.com/players/andrew-vorhees/"},
        {"date": "11/09", "from_club": "NYJ", "to_club": "DET", "name": "Andre Cisco", "position": "", "transaction": "Traded", "url": "https://www.nfl.com/players/andre-cisco/"},
        {"date": "11/09", "from_club": "NO", "to_club": "JAX", "name": "Davon Godchaux", "position": "", "transaction": "Traded", "url": "https://www.nfl.com/players/davon-godchaux/"},
        {"date": "11/06", "from_club": "AZ", "to_club": "BAL", "name": "Jacoby Brissett", "position": "", "transaction": "Traded", "url": "https://www.nfl.com/players/jacoby-brissett/"},
    ],
}
w("trades_2026_11.json", trades)

print("seed complete")
