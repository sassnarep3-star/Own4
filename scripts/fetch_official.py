#!/usr/bin/env python3
"""
fetch_official.py — Pull NBA game data with full provenance (run in Actions).

Sources (see data/pipeline_sources.json):
  1. NBA domains (canonical): cdn.nba.com JSON, www.nba.com HTML — attempted first.
  2. ESPN site.api (official NBA broadcast partner) — bulk fallback when NBA
     endpoints block datacenter clients (403/timeouts are recorded, not hidden).

Every request is logged in data/manifest.json with source_url, status, time.
No value is ever invented: failures are recorded as failures.

Outputs:
  data/raw/nba/games_<date>.html      (if reachable)
  data/raw/espn/scoreboard_<date>.json
  data/raw/espn/summary_<eventId>.json
  data/raw/... (cdn/stats attempts recorded in manifest)
"""

import gzip
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(REPO_ROOT, "data", "raw")
MANIFEST_PATH = os.path.join(REPO_ROOT, "data", "manifest.json")
SEASON = "2026-27"

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*; q=0.01, text/html;q=0.9, */*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-site",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "Connection": "close",
}

DATES = [
    "2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23", "2026-10-24",
    "2026-10-25", "2026-10-26", "2026-10-27", "2026-10-28", "2026-10-29",
    "2026-10-30", "2026-10-31", "2026-11-01", "2026-11-02",
]

NBA_DAILY = "https://www.nba.com/games?date={date}"
CDN_CANDIDATES = [
    "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json",
    "https://cdn.nba.com/static/json/liveData/scoreboard/scoreboard_{date}.json",
]
STATS_STANDINGS = (
    "https://stats.nba.com/stats/leaguestandingsv3?LeagueID=00"
    f"&Season={SEASON}&SeasonType=Regular%20Season"
)
ESPN_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={ymd}"
ESPN_SUMMARY = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={eid}"

manifest = {"updated_utc": None, "season": SEASON, "items": []}


def load_manifest():
    global manifest
    if os.path.exists(MANIFEST_PATH):
        try:
            with open(MANIFEST_PATH) as f:
                manifest = json.load(f)
        except Exception:
            pass


def save_manifest():
    manifest["updated_utc"] = datetime.now(timezone.utc).isoformat()
    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=1)


def record(source_url, status, out_rel, note=""):
    manifest["items"].append({
        "source_url": source_url,
        "http_status": status,
        "output": out_rel,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "note": note,
    })


def fetch(url, timeout=25, tries=2, sleep=1.5):
    """Return (bytes|None, status). Never raises."""
    last = "error"
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=BROWSER_HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip" or data[:2] == b"\x1f\x8b":
                    try:
                        data = gzip.decompress(data)
                    except Exception:
                        pass
                return data, resp.status
        except urllib.error.HTTPError as e:
            last = e.code
            if e.code in (429, 500, 503) and attempt < tries - 1:
                time.sleep(sleep * (attempt + 1))
                continue
            break
        except Exception as e:
            last = f"error:{type(e).__name__}"
            if attempt < tries - 1:
                time.sleep(sleep)
                continue
            break
    return None, last


def save(rel, data):
    path = os.path.join(REPO_ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mode = "wb" if isinstance(data, bytes) else "w"
    with open(path, mode) as f:
        f.write(data)
    return rel


def try_store(url, rel, note=""):
    data, status = fetch(url)
    if data is None:
        record(url, status, None, f"fetch failed {note}")
        print(f"FAIL {status} {url}")
        return None
    save(rel, data)
    record(url, status, rel, f"ok {note}")
    print(f"OK   {status} {url} -> {rel}")
    return data


def main():
    load_manifest()
    os.makedirs(RAW, exist_ok=True)

    # --- Attempt 1: canonical NBA endpoints (recorded regardless) ---
    try_store(CDN_CANDIDATES[0], "data/raw/nba/todaysScoreboard.json", "cdn")
    try_store(STATS_STANDINGS, "data/raw/nba/standings_stats.json", "stats-api")

    for d in DATES:
        try_store(NBA_DAILY.format(date=d), f"data/raw/nba/games_{d}.html", "nba-html")
        try_store(CDN_CANDIDATES[1].format(date=d), f"data/raw/nba/scoreboard_{d}.json", "cdn")
        time.sleep(0.3)

    # --- Attempt 2: ESPN (official NBA broadcast partner) bulk ---
    event_ids = []
    for d in DATES:
        ymd = d.replace("-", "")
        rel = f"data/raw/espn/scoreboard_{d}.json"
        data = try_store(ESPN_SCOREBOARD.format(ymd=ymd), rel, "espn-partner")
        if data:
            try:
                payload = json.loads(data)
                for ev in payload.get("events", []):
                    if ev.get("id"):
                        event_ids.append(ev["id"])
            except Exception:
                pass
        time.sleep(0.35)

    # De-duplicate, keep order; cap defensively
    seen, ids = set(), []
    for e in event_ids:
        if e not in seen:
            seen.add(e)
            ids.append(e)
    print(f"espn events: {len(ids)}")

    ok = 0
    for eid in ids:
        rel = f"data/raw/espn/summary_{eid}.json"
        full = os.path.join(REPO_ROOT, rel)
        if os.path.exists(full) and os.path.getsize(full) > 2000:
            continue
        data = try_store(ESPN_SUMMARY.format(event_id=eid), rel, "espn-partner")
        if data:
            ok += 1
        time.sleep(0.35)
    print(f"espn summaries fetched: {ok}")

    save_manifest()
    okn = sum(1 for i in manifest["items"] if i["http_status"] == 200)
    print(f"manifest: {len(manifest['items'])} items, {okn} ok")


if __name__ == "__main__":
    sys.exit(main())
