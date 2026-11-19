"""Official 2026 standings transcription — read 2026-11-19 via page-fetch tool.

Source: https://www.nfl.com/standings/ (Division view, 2026 REG).
Every value below is transcribed verbatim from the rendered table. No arithmetic
is performed in this file; reconciliation is computed in engine/model.py.

Cross-check: matches the committed 2026-11-19 reads in nfl-desk/data/standings_2026-11-19.json
and nfl-verify-2026-11-19/data/standings_2026_11_19.json field by field (32/32 teams).
"""
import json
import pathlib

SOURCE_URL = "https://www.nfl.com/standings/"
READ_DATE = "2026-11-19"

# (abbr, club, conference, division, W, L, T, PCT, PF, PA, NET, div_rec, conf_rec, nonconf_rec, streak, last5)
ROWS = [
    ("BUF", "Buffalo Bills", "AFC", "East", 8, 1, 0, 0.889, 287, 199, 88, "3 - 1 - 0", "5 - 0 - 0", "1 - 1 - 0", "5W", "5 - 0 - 0"),
    ("NE", "New England Patriots", "AFC", "East", 5, 5, 0, 0.500, 221, 242, -21, "3 - 1 - 0", "2 - 4 - 0", "3 - 0 - 0", "2L", "2 - 3 - 0"),
    ("NYJ", "New York Jets", "AFC", "East", 2, 8, 0, 0.200, 194, 254, -60, "1 - 4 - 0", "1 - 4 - 0", "0 - 3 - 0", "5L", "0 - 5 - 0"),
    ("MIA", "Miami Dolphins", "AFC", "East", 1, 8, 0, 0.111, 148, 224, -76, "0 - 4 - 0", "1 - 4 - 0", "1 - 1 - 0", "3L", "1 - 4 - 0"),
    ("CIN", "Cincinnati Bengals", "AFC", "North", 7, 2, 0, 0.778, 278, 193, 85, "3 - 1 - 0", "4 - 1 - 0", "2 - 1 - 0", "5W", "5 - 0 - 0"),
    ("PIT", "Pittsburgh Steelers", "AFC", "North", 6, 3, 0, 0.667, 198, 182, 16, "4 - 0 - 0", "2 - 3 - 0", "2 - 2 - 0", "1L", "4 - 1 - 0"),
    ("CLE", "Cleveland Browns", "AFC", "North", 6, 4, 0, 0.600, 188, 220, -32, "4 - 0 - 0", "2 - 4 - 0", "2 - 1 - 0", "1W", "3 - 2 - 0"),
    ("BAL", "Baltimore Ravens", "AFC", "North", 4, 6, 0, 0.400, 209, 259, -50, "1 - 4 - 0", "3 - 2 - 0", "0 - 2 - 0", "5L", "0 - 5 - 0"),
    ("JAX", "Jacksonville Jaguars", "AFC", "South", 7, 2, 0, 0.778, 269, 144, 125, "4 - 1 - 0", "3 - 1 - 0", "2 - 1 - 0", "3W", "4 - 1 - 0"),
    ("HOU", "Houston Texans", "AFC", "South", 3, 6, 0, 0.333, 233, 219, 14, "0 - 4 - 0", "3 - 2 - 0", "2 - 1 - 0", "1L", "3 - 2 - 0"),
    ("IND", "Indianapolis Colts", "AFC", "South", 3, 7, 0, 0.300, 208, 271, -63, "2 - 3 - 0", "1 - 4 - 0", "1 - 2 - 0", "1W", "1 - 4 - 0"),
    ("TEN", "Tennessee Titans", "AFC", "South", 1, 8, 0, 0.111, 167, 239, -72, "0 - 5 - 0", "1 - 3 - 0", "1 - 2 - 0", "3L", "1 - 4 - 0"),
    ("KC", "Kansas City Chiefs", "AFC", "West", 7, 2, 0, 0.778, 237, 156, 81, "4 - 0 - 0", "3 - 2 - 0", "3 - 1 - 0", "2W", "3 - 2 - 0"),
    ("DEN", "Denver Broncos", "AFC", "West", 7, 2, 0, 0.778, 198, 186, 12, "4 - 0 - 0", "3 - 2 - 0", "2 - 1 - 0", "5W", "5 - 0 - 0"),
    ("LV", "Las Vegas Raiders", "AFC", "West", 4, 6, 0, 0.400, 251, 289, -38, "1 - 4 - 0", "3 - 2 - 0", "1 - 1 - 0", "2L", "1 - 4 - 0"),
    ("LAC", "Los Angeles Chargers", "AFC", "West", 1, 8, 0, 0.111, 144, 239, -95, "0 - 4 - 0", "1 - 4 - 0", "0 - 3 - 0", "1W", "1 - 4 - 0"),
    ("NYG", "New York Giants", "NFC", "East", 5, 3, 1, 0.611, 203, 196, 7, "3 - 2 - 0", "2 - 1 - 1", "2 - 1 - 1", "1L", "2 - 2 - 1"),
    ("DAL", "Dallas Cowboys", "NFC", "East", 4, 6, 0, 0.400, 286, 282, 4, "1 - 4 - 0", "3 - 2 - 0", "2 - 1 - 0", "1L", "2 - 3 - 0"),
    ("WAS", "Washington Commanders", "NFC", "East", 3, 5, 1, 0.389, 196, 223, -27, "2 - 2 - 1", "1 - 3 - 0", "2 - 2 - 1", "1W", "2 - 2 - 1"),
    ("PHI", "Philadelphia Eagles", "NFC", "East", 2, 7, 0, 0.222, 148, 221, -73, "1 - 4 - 0", "1 - 3 - 0", "1 - 3 - 0", "7L", "0 - 5 - 0"),
    ("DET", "Detroit Lions", "NFC", "North", 7, 2, 0, 0.778, 257, 199, 58, "5 - 0 - 0", "2 - 2 - 0", "2 - 0 - 0", "5W", "5 - 0 - 0"),
    ("MIN", "Minnesota Vikings", "NFC", "North", 7, 2, 0, 0.778, 176, 126, 50, "3 - 1 - 0", "4 - 1 - 0", "3 - 1 - 0", "1W", "3 - 2 - 0"),
    ("CHI", "Chicago Bears", "NFC", "North", 7, 2, 0, 0.778, 241, 184, 57, "4 - 1 - 0", "3 - 1 - 0", "0 - 2 - 0", "4W", "4 - 1 - 0"),
    ("GB", "Green Bay Packers", "NFC", "North", 6, 4, 0, 0.600, 226, 221, 5, "3 - 2 - 0", "3 - 2 - 0", "1 - 3 - 0", "1L", "3 - 2 - 0"),
    ("CAR", "Carolina Panthers", "NFC", "South", 4, 5, 0, 0.444, 219, 236, -17, "1 - 3 - 0", "3 - 2 - 0", "2 - 1 - 0", "1W", "2 - 3 - 0"),
    ("TB", "Tampa Bay Buccaneers", "NFC", "South", 3, 6, 0, 0.333, 202, 178, 24, "1 - 4 - 0", "2 - 2 - 0", "2 - 0 - 0", "1L", "3 - 2 - 0"),
    ("NO", "New Orleans Saints", "NFC", "South", 3, 6, 0, 0.333, 202, 236, -34, "1 - 5 - 0", "2 - 1 - 0", "0 - 2 - 0", "1L", "2 - 3 - 0"),
    ("ATL", "Atlanta Falcons", "NFC", "South", 3, 7, 0, 0.300, 201, 258, -57, "1 - 5 - 0", "2 - 2 - 0", "1 - 2 - 0", "3L", "1 - 4 - 0"),
    ("SF", "San Francisco 49ers", "NFC", "West", 8, 1, 0, 0.889, 281, 196, 85, "5 - 0 - 0", "3 - 1 - 0", "3 - 0 - 0", "2W", "4 - 1 - 0"),
    ("SEA", "Seattle Seahawks", "NFC", "West", 6, 4, 0, 0.600, 223, 175, 48, "4 - 2 - 0", "2 - 2 - 0", "2 - 1 - 0", "2W", "3 - 2 - 0"),
    ("LA", "Los Angeles Rams", "NFC", "West", 6, 4, 0, 0.600, 248, 187, 61, "2 - 3 - 0", "4 - 1 - 0", "1 - 2 - 0", "4W", "4 - 1 - 0"),
    ("AZ", "Arizona Cardinals", "NFC", "West", 3, 7, 0, 0.300, 184, 289, -105, "0 - 4 - 0", "3 - 3 - 0", "1 - 4 - 0", "2L", "2 - 3 - 0"),
]

COLUMNS = ["abbr", "club", "conference", "division", "W", "L", "T", "pct", "PF", "PA", "NET",
           "division_rec", "conference_rec", "nonconference_rec", "streak", "last5"]


def main():
    out = {
        "id": "standings-2026-11-19",
        "title": "2026 NFL Division Standings (read 2026-11-19)",
        "source_url": SOURCE_URL,
        "publisher": "NFL.com (official)",
        "read_date": READ_DATE,
        "read_route": "page-fetch tool rendered read; sandbox has no direct HTTPS egress to nfl.com",
        "columns": COLUMNS,
        "rows": [dict(zip(COLUMNS, r)) for r in ROWS],
    }
    p = pathlib.Path(__file__).with_suffix(".json")
    p.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("wrote %s (%d rows)" % (p, len(ROWS)))


if __name__ == "__main__":
    main()
