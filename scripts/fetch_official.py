#!/usr/bin/env python3
"""
fetch_official.py — Pull NBA data from official NBA sources only.

Official sources used (see data/sources.json for the registry):
  - cdn.nba.com static/live JSON (NBA's official CDN, same origin as nba.com assets)
  - stats.nba.com official stats API (NBA)
  - www.nba.com HTML pages (NBA)

Every fetched artifact is recorded in data/manifest.json with:
  source_url, http_status, fetched_at (UTC), bytes, and output path.

This script is designed to run in GitHub Actions (unrestricted egress).
Stdlib only. Retries with backoff; never fabricates data: on failure it
records the failure in the manifest and leaves outputs untouched.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(REPO_ROOT, "data", "raw")
MANIFEST_PATH = os.path.join(REPO_ROOT, "data", "manifest.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com",
    "Connection": "close",
}

SEASON = "2026-27"
SEASON_TYPE = "Regular Season"

# Candidate official endpoints, tried in order (paths have changed over seasons).
SCHEDULE_CANDIDATES = [
    "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json",
    "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json",
    "https://cdn.nba.com/static/json/liveData/schedule/scheduleLeagueV2_1.json",
    "https://cdn.nba.com/static/json/liveData/schedule/scheduleV2.json",
]

SCOREBOARD_TODAY = "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json"
SCOREBOARD_BY_DATE = "https://cdn.nba.com/static/json/liveData/scoreboard/scoreboard_{date}.json"
BOXSCORE = "https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json"

STANDINGS = (
    "https://stats.nba.com/stats/leaguestandingsv3?LeagueID=00"
    f"&Season={SEASON}&SeasonType={SEASON.replace(' ', '%20')}"
)
TEAM_GAMES = (
    "https://stats.nba.com/stats/leaguegamefinder?LeagueID=00"
    f"&Season={SEASON}&SeasonType=Regular%20Season&PlayerOrTeam=T"
)

manifest = {"updated_utc": None, "season": SEASON, "items": []}


def load_manifest():
    global manifest
    if os.path.exists(MANIFEST_PATH):
        try:
            with open(MANIFEST_PATH) as f:
                manifest = json.load(f)
        except Exception:
            manifest = {"updated_utc": None, "season": SEASON, "items": []}


def save_manifest():
    manifest["updated_utc"] = datetime.now(timezone.utc).isoformat()
    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=1)


def record(source_url, status, out_path, note=""):
    manifest["items"].append(
        {
            "source_url": source_url,
            "http_status": status,
            "output": os.path.relpath(out_path, REPO_ROOT) if out_path else None,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "note": note,
        }
    )


def fetch(url, timeout=30, tries=3, sleep=2.0):
    """Return (bytes, status) or (None, status). Never raises."""
    last_status = "error"
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
                return data, resp.status
        except urllib.error.HTTPError as e:
            last_status = e.code
            if e.code in (403, 404, 429, 500, 503) and attempt < tries - 1:
                time.sleep(sleep * (attempt + 1))
                continue
            break
        except Exception as e:
            last_status = f"error:{type(e).__name__}"
            if attempt < tries - 1:
                time.sleep(sleep * (attempt + 1))
                continue
            break
    return None, last_status


def write_raw(rel_path, data):
    path = os.path.join(REPO_ROOT, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mode = "wb" if isinstance(data, bytes) else "w"
    with open(path, mode) as f:
        f.write(data)
    return path


def try_json(url, rel_out):
    data, status = fetch(url)
    if data is None:
        record(url, status, None, "fetch failed")
        print(f"FAIL {status} {url}")
        return None
    try:
        payload = json.loads(data)
    except Exception:
        record(url, status, None, "response was not valid JSON")
        print(f"FAIL json {url}")
        return None
    path = write_raw(rel_out, json.dumps(payload, indent=1))
    record(url, status, path, "ok")
    print(f"OK   {status} {url} -> {rel_out}")
    return payload


def main():
    load_manifest()
    os.makedirs(RAW_DIR, exist_ok=True)

    # 1) Full-season schedule (contains game ids, dates, scores once played)
    schedule = None
    for url in SCHEDULE_CANDIDATES:
        schedule = try_json(url, "data/raw/schedule.json")
        if schedule:
            break

    # 2) Today's scoreboard (fallback source of game ids / results)
    try_json(SCOREBOARD_TODAY, "data/raw/scoreboard_today.json")

    # 3) Standings (official stats API)
    try_json(STANDINGS, "data/raw/standings.json")

    # 4) Team game finder (all team games this season — compact results)
    try_json(TEAM_GAMES, "data/raw/team_gamefinder.json")

    # 5) Daily scoreboards Oct 20 -> Nov 2 (official results per day)
    dates = [
        "2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23", "2026-10-24",
        "2026-10-25", "2026-10-26", "2026-10-27", "2026-10-28", "2026-10-29",
        "2026-10-30", "2026-10-31", "2026-11-01", "2026-11-02",
    ]
    game_ids = set()

    # Harvest game ids from anything already fetched this run or on disk
    for rel in ("data/raw/schedule.json", "data/raw/scoreboard_today.json",
                "data/raw/team_gamefinder.json"):
        path = os.path.join(REPO_ROOT, rel)
        if os.path.exists(path):
            try:
                with open(path) as f:
                    blob = f.read()
                import re
                game_ids.update(re.findall(r"\b(00226\d{5})\b", blob))
            except Exception:
                pass

    for d in dates:
        url = SCOREBOARD_BY_DATE.format(date=d)
        payload = try_json(url, f"data/raw/scoreboard_{d}.json")
        if payload:
            import re
            with open(os.path.join(REPO_ROOT, f"data/raw/scoreboard_{d}.json")) as f:
                game_ids.update(re.findall(r"\b(00226\d{5})\b", f.read()))
        time.sleep(0.5)

    # 6) Box scores for every discovered regular-season game id (2026-27 = 00226*)
    #    Cap at 140 ids defensively (92 games expected through Nov 2).
    ids = sorted(game_ids)[:140]
    print(f"boxscore ids discovered: {len(ids)}")
    ok = 0
    for gid in ids:
        rel = f"data/raw/boxscores/boxscore_{gid}.json"
        full = os.path.join(REPO_ROOT, rel)
        if os.path.exists(full) and os.path.getsize(full) > 1000:
            continue
        url = BOXSCORE.format(game_id=gid)
        payload = try_json(url, rel)
        if payload:
            ok += 1
        time.sleep(0.4)
    print(f"boxscores fetched this run: {ok}")

    save_manifest()
    print(f"manifest items: {len(manifest['items'])}")


if __name__ == "__main__":
    sys.exit(main())
