"""Official-source register — every URL opened this session (2026-11-19).

Each entry states what the page showed and what it was used for. URLs that were
checked and found empty/404 are recorded as such (depth-charts 404).
"""
import json
import pathlib

READ_DATE = "2026-11-19"

SOURCES = [
    ("SRC-01", "https://www.nfl.com/standings/", "2026 NFL Division Standings",
     "32-team standings (W/L/T, PCT, PF, PA, NET, division/conference records, streak, last-5). "
     "Transcribed in full; arithmetic reconciles (149 W = 149 L, 150 games)."),
    ("SRC-02", "https://www.nfl.com/schedules/2026/by-week/week-11", "NFL Week 11 Schedule 2026",
     "13 fixtures (dates, times, networks, game-centre links, hotel-link venues) + 6 byes "
     "(ATL, CLE, GB, LAR, NE, SEA). Hotel-link venue for IND@HOU reads 'NRG Stadium'."),
    ("SRC-03", "https://www.nfl.com/games/colts-at-texans-2026-reg-11", "Indianapolis Colts at Houston Texans 2026 REG 11 - Game Center",
     "TNF Game Info: Location HOUSTON, TX, Stadium RELIANT STADIUM. Authoritative venue for "
     "IND@HOU per the brief; disagrees with the schedule hotel link (VF-01)."),
    ("SRC-04", "https://www.nfl.com/injuries/", "Official Latest NFL Injury Report - Week 11 of the 2026 Season",
     "Full 26-club Week-11 report: 253 rows, 16 with game status (TNF only), 237 blank "
     "game-status, 2 no-injury sections (CIN, WAS)."),
    ("SRC-05", "https://www.nfl.com/scores/", "NFL Scores and Highlights",
     "Week-11 slate state: TNF upcoming Nov 19, no Week-11 finals yet. Consistent with "
     "standings through Week 10 (150 games)."),
    ("SRC-06", "https://www.nfl.com/transactions/league/reserve-list/2026/11", "2026 NFL reserve-list by month (November)",
     "25 November Reserve/Injured moves with dates. Position column blank on the official page."),
    ("SRC-07", "https://www.nfl.com/transactions/league/trades/2026/11", "2026 NFL trades by month (November)",
     "12 November trades with from/to clubs and dates."),
    ("SRC-08", "https://www.nfl.com/depth-charts/", "404 - Flag on the Play",
     "Checked 2026-11-19: returns a 404 page. The NFL publishes no league depth chart; "
     "club depth charts are the only route (peer register, HOU image-only)."),
]

COLUMNS = ["id", "url", "title", "used_for"]


def main():
    out = {
        "id": "sources-2026-11-19",
        "note": "Official-source register for the 2026-11-19 verification round. Every value on the site traces to one of these URLs.",
        "read_date": READ_DATE,
        "columns": COLUMNS,
        "sources": [dict(zip(COLUMNS, s)) for s in SOURCES],
    }
    p = pathlib.Path(__file__).with_suffix(".json")
    p.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("wrote %s (%d sources)" % (p, len(SOURCES)))


if __name__ == "__main__":
    main()
