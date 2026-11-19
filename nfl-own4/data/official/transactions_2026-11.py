"""Official November-2026 transactions transcription — read 2026-11-19 via page-fetch tool.

Sources:
  Reserve list: https://www.nfl.com/transactions/league/reserve-list/2026/11 (25 rows)
  Trades:       https://www.nfl.com/transactions/league/trades/2026/11 (12 rows)
Position column is blank on the official page for every row and is published as blank.
"""
import json
import pathlib

RESERVE_URL = "https://www.nfl.com/transactions/league/reserve-list/2026/11"
TRADES_URL = "https://www.nfl.com/transactions/league/trades/2026/11"
READ_DATE = "2026-11-19"

# (club, date, name, transaction)
RESERVE = [
    ("PIT", "11/18", "Mason McCormick", "Reserve/Injured"),
    ("KC", "11/18", "Jared Wiley", "Reserve/Injured"),
    ("DET", "11/18", "Aidan Hutchinson", "Reserve/Injured"),
    ("MIN", "11/18", "Bo Richter", "Reserve/Injured"),
    ("HOU", "11/17", "Azeez Al-Shaair", "Reserve/Injured"),
    ("MIA", "11/17", "Zeek Biggers", "Reserve/Injured"),
    ("MIA", "11/17", "Jordan Phillips", "Reserve/Injured"),
    ("AZ", "11/17", "Andrew Wingard", "Reserve/Injured"),
    ("AZ", "11/17", "Jordan Burch", "Reserve/Injured"),
    ("BUF", "11/17", "Ar'maj Reed-Adams", "Reserve/Injured"),
    ("IND", "11/17", "Jaylon Carlies", "Reserve/Injured"),
    ("TEN", "11/17", "Wan'Dale Robinson", "Reserve/Injured"),
    ("LA", "11/16", "Dylan McMahon", "Reserve/Injured"),
    ("LAC", "11/16", "Branson Taylor", "Reserve/Injured"),
    ("NO", "11/14", "Christen Miller", "Reserve/Injured"),
    ("NE", "11/14", "TreVeyon Henderson", "Reserve/Injured"),
    ("CLE", "11/14", "Michael Burton", "Reserve/Injured"),
    ("IND", "11/14", "Mo Alie-Cox", "Reserve/Injured"),
    ("IND", "11/14", "Akeem Davis-Gaither", "Reserve/Injured"),
    ("TEN", "11/14", "Peter Skoronski", "Reserve/Injured"),
    ("TEN", "11/14", "Tommy Townsend", "Reserve/Injured"),
    ("DAL", "11/14", "Tyler Goodson", "Reserve/Injured"),
    ("GB", "11/14", "Josh Whyle", "Reserve/Injured"),
    ("LA", "11/12", "Puka Nacua", "Reserve/Injured"),
    ("LA", "11/10", "Jordan Whittington", "Reserve/Injured"),
]

# (from_club, to_club, date, name, transaction)
TRADES = [
    ("ATL", "JAX", "11/10", "Jessie Bates", "Traded"),
    ("PHI", "JAX", "11/10", "Jordan Davis", "Traded"),
    ("TEN", "BUF", "11/10", "Amani Hooker", "Traded"),
    ("IND", "SF", "11/10", "Keenan Allen", "Traded"),
    ("LV", "MIN", "11/10", "Kirk Cousins", "Traded"),
    ("LAC", "DEN", "11/10", "Daiyan Henley", "Traded"),
    ("IND", "KC", "11/10", "Josh Downs", "Traded"),
    ("ATL", "BAL", "11/10", "Ryan Neuzil", "Traded"),
    ("BAL", "ATL", "11/10", "Andrew Vorhees", "Traded"),
    ("NYJ", "DET", "11/09", "Andre Cisco", "Traded"),
    ("NO", "JAX", "11/09", "Davon Godchaux", "Traded"),
    ("AZ", "BAL", "11/06", "Jacoby Brissett", "Traded"),
]


def main():
    out = {
        "id": "transactions-2026-11",
        "title": "2026 NFL Transactions — November (read 2026-11-19)",
        "read_date": READ_DATE,
        "read_route": "page-fetch tool rendered read; sandbox has no direct HTTPS egress to nfl.com",
        "reserve": {
            "source_url": RESERVE_URL,
            "columns": ["club", "date", "name", "position", "transaction"],
            "rows": [{"club": c, "date": d, "name": n, "position": "", "transaction": t}
                     for c, d, n, t in RESERVE],
        },
        "trades": {
            "source_url": TRADES_URL,
            "columns": ["from_club", "to_club", "date", "name", "position", "transaction"],
            "rows": [{"from_club": f, "to_club": t, "date": d, "name": n, "position": "", "transaction": x}
                     for f, t, d, n, x in TRADES],
        },
        "position_note": "The official page prints a blank Position cell for every row; published as blank.",
    }
    p = pathlib.Path(__file__).with_suffix(".json")
    p.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("wrote %s (%d reserve, %d trades)" % (p, len(RESERVE), len(TRADES)))


if __name__ == "__main__":
    main()
