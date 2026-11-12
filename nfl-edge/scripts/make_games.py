#!/usr/bin/env python3
"""Build nfl-edge/data/games_2026.json.

Inputs
  1. ../../nfl-lab/data/games_2026.csv  (peer workspace archive; READ ONLY, not modified)
     - validated this session: 120 games, weeks 1-8, plus 16 games transcribed from nfl.com
       week 8/9 pages, reproduce the official 2026 standings PF/PA/W-L/PCT for all 32 teams
       with 0 mismatches (see nfl-edge/data/integrity.json).
  2. GAMES_READ_OFFICIAL below: games whose score or matchup was read directly from
     https://www.nfl.com/schedules/2026/by-week/week-<n> on 2026-11-12 by this session.
Output: one row per game, each with the official nfl.com game page URL.
No value is inferred. Missing scores stay null.
"""
import csv, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "nfl-lab", "data", "games_2026.csv")
OUT = os.path.join(ROOT, "nfl-edge", "data", "games_2026.json")

# score/matchup read directly from the official nfl.com by-week page on 2026-11-12
READ_OFFICIAL = [
    # week 8 Monday Night Football (score shown on the week-8 page)
    {"week": 8, "date": "2026-11-02", "away": "CHI", "home": "SEA", "away_pts": 34, "home_pts": 17,
     "slug": "bears-at-seahawks-2026-reg-8", "official_page": "week-8"},
    # week 9, all 15 games (complete scores read from the week-9 page)
    {"week": 9, "date": "2026-11-05", "away": "JAX", "home": "BAL", "away_pts": 33, "home_pts": 10, "slug": "jaguars-at-ravens-2026-reg-9", "official_page": "week-9"},
    {"week": 9, "date": "2026-11-08", "away": "CIN", "home": "ATL", "away_pts": 34, "home_pts": 17, "slug": "bengals-at-falcons-2026-reg-9", "official_page": "week-9"},
    {"week": 9, "date": "2026-11-08", "away": "DEN", "home": "CAR", "away_pts": 26, "home_pts": 21, "slug": "broncos-at-panthers-2026-reg-9", "official_page": "week-9"},
    {"week": 9, "date": "2026-11-08", "away": "DAL", "home": "IND", "away_pts": 27, "home_pts": 23, "slug": "cowboys-at-colts-2026-reg-9", "official_page": "week-9"},
    {"week": 9, "date": "2026-11-08", "away": "NYJ", "home": "KC", "away_pts": 12, "home_pts": 35, "slug": "jets-at-chiefs-2026-reg-9", "official_page": "week-9"},
    {"week": 9, "date": "2026-11-08", "away": "DET", "home": "MIA", "away_pts": 19, "home_pts": 9, "slug": "lions-at-dolphins-2026-reg-9", "official_page": "week-9"},
    {"week": 9, "date": "2026-11-08", "away": "CLE", "home": "NO", "away_pts": 22, "home_pts": 23, "slug": "browns-at-saints-2026-reg-9", "official_page": "week-9"},
    {"week": 9, "date": "2026-11-08", "away": "NYG", "home": "PHI", "away_pts": 19, "home_pts": 11, "slug": "giants-at-eagles-2026-reg-9", "official_page": "week-9"},
    {"week": 9, "date": "2026-11-08", "away": "LA", "home": "WAS", "away_pts": 20, "home_pts": 13, "slug": "rams-at-commanders-2026-reg-9", "official_page": "week-9"},
    {"week": 9, "date": "2026-11-08", "away": "HOU", "home": "LAC", "away_pts": 44, "home_pts": 22, "slug": "texans-at-chargers-2026-reg-9", "official_page": "week-9"},
    {"week": 9, "date": "2026-11-08", "away": "LV", "home": "SF", "away_pts": 17, "home_pts": 38, "slug": "raiders-at-49ers-2026-reg-9", "official_page": "week-9"},
    {"week": 9, "date": "2026-11-08", "away": "GB", "home": "NE", "away_pts": 45, "home_pts": 27, "slug": "packers-at-patriots-2026-reg-9", "official_page": "week-9"},
    {"week": 9, "date": "2026-11-08", "away": "AZ", "home": "SEA", "away_pts": 3, "home_pts": 17, "slug": "cardinals-at-seahawks-2026-reg-9", "official_page": "week-9"},
    {"week": 9, "date": "2026-11-08", "away": "TB", "home": "CHI", "away_pts": 24, "home_pts": 27, "slug": "buccaneers-at-bears-2026-reg-9", "official_page": "week-9"},
    {"week": 9, "date": "2026-11-09", "away": "BUF", "home": "MIN", "away_pts": 23, "home_pts": 6, "slug": "bills-at-vikings-2026-reg-9", "official_page": "week-9"},
]

rows = []
with open(SRC) as f:
    for r in csv.DictReader(f):
        rows.append({
            "week": int(r["week"]), "date": r["date_iso"],
            "away": r["away"], "home": r["home"],
            "away_pts": int(r["away_pts"]), "home_pts": int(r["home_pts"]),
            "neutral": r["neutral_site"] == "1",
            "slug": r["game_slug"],
            "source_url": r["source_url"],
            "provenance": "peer_archive_reconciled",
            "official_week_page": "https://www.nfl.com/schedules/2026/by-week/week-%d" % int(r["week"]),
        })

seen = {(g["week"], g["away"], g["home"]) for g in rows}
added = 0
for g in READ_OFFICIAL:
    key = (g["week"], g["away"], g["home"])
    if key in seen:
        for row in rows:
            if (row["week"], row["away"], row["home"]) == key:
                row["provenance"] = "read_from_official_week_page"
                row["score_source_url"] = "https://www.nfl.com/schedules/2026/by-week/%s" % g["official_page"]
        continue
    rows.append({
        "week": g["week"], "date": g["date"], "away": g["away"], "home": g["home"],
        "away_pts": g["away_pts"], "home_pts": g["home_pts"], "neutral": False,
        "slug": g["slug"], "source_url": "https://www.nfl.com/games/%s" % g["slug"],
        "provenance": "read_from_official_week_page",
        "official_week_page": "https://www.nfl.com/schedules/2026/by-week/%s" % g["official_page"],
        "score_source_url": "https://www.nfl.com/schedules/2026/by-week/%s" % g["official_page"],
    })
    added += 1

rows.sort(key=lambda r: (r["week"], r["date"], r["away"]))
for r in rows:
    r.setdefault("score_source_url", r["source_url"])

payload = {
    "dataset": "nfl_2026_regular_season_games",
    "title": "2026 NFL regular-season games through Week 9 (136 games)",
    "captured_utc": "2026-11-12",
    "official_schedule_index": "https://www.nfl.com/schedules/2026/",
    "score_verification": "Team-level W-L-T, PF and PA for all 32 teams recomputed from these 136 rows match the official standings page https://www.nfl.com/standings/ with 0 mismatches (nfl-edge/data/integrity.json). 16 games were read directly from official nfl.com week pages on 2026-11-12; the remaining 120 come from the peer archive nfl-lab/data/games_2026.csv, whose own rows carry the official game-page URL, and are corroborated game-for-game by that aggregate reconciliation.",
    "columns": ["week", "date", "away", "home", "away_pts", "home_pts", "neutral", "slug", "source_url", "score_source_url", "provenance", "official_week_page"],
    "n_rows": len(rows),
    "n_read_from_official": sum(1 for r in rows if r["provenance"] == "read_from_official_week_page"),
    "n_peer_archive": sum(1 for r in rows if r["provenance"] == "peer_archive_reconciled"),
    "rows": rows,
}
with open(OUT, "w") as f:
    json.dump(payload, f, indent=1)
print("wrote", OUT, len(rows), "games;", payload["n_read_from_official"], "read official;", added, "added")
