#!/usr/bin/env python3
"""fetch_round2.py — second network stage: per-player game logs + season tables.

Run where nba.com is reachable (GitHub Actions). Fetch-only, verbatim, with SHA-256.
Player ids come from verification/data/player_ids.json (discovered from official pages
and from official box scores already committed by earlier sessions).
"""
import hashlib, json, os, time, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_official_data import fetch, records, RAW, MANIFEST   # reuse the audited fetcher

HERE = os.path.dirname(os.path.abspath(__file__))
V = os.path.dirname(HERE)
SEASON = "2026-27"


def main():
    ids = json.load(open(os.path.join(V, "data", "player_ids.json")))
    print(f"player ids: {len(ids)}")
    for pid in ids:
        fetch(f"https://www.nba.com/stats/player/{pid}/boxscores-traditional?Season={SEASON}",
              "nba_playerlogs", f"player_{pid}")
        time.sleep(0.35)
    for sort in ("PTS", "REB", "AST"):
        fetch(f"https://www.nba.com/stats/players/traditional?Season={SEASON}&PerMode=PerGame"
              f"&PerPage=100&dir=-1&sort={sort}", "nba_tables", f"players_{sort.lower()}")
        time.sleep(0.4)
    fetch("https://www.nba.com/stats/teams/advanced", "nba_tables", "teams_advanced")
    fetch("https://www.nba.com/standings?GroupBy=division", "nba_tables", "standings_division")
    m = {"updated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "season": SEASON,
         "note": "round 2: per-player official game logs + season tables (verbatim)",
         "ok": sum(1 for r in records if r["http_status"]),
         "failed": sum(1 for r in records if not r["http_status"]), "items": records}
    json.dump(m, open(MANIFEST, "w"), indent=1)
    print(f"round2 manifest: ok={m['ok']} failed={m['failed']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
