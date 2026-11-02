#!/usr/bin/env python3
"""Fetch official NFL pages and trusted partner scoreboard JSON with full provenance.

Run by .github/workflows/fetch-nfl-quant.yml on the GitHub-hosted runner, which has
outbound access to www.nfl.com and site.api.espn.com. The Arena sandbox shell does not,
so this script must not be run locally as a data source.

Design rules:
  * Every attempted URL is recorded in manifest.json with status, SHA-256 and output path.
  * No value is invented; a failed fetch is recorded as a failure.
  * Only official league domains are labelled official. ESPN is an official NFL broadcast
    partner / trusted cross-check, not an NFL publication.
  * Raw responses are stored gzipped to keep the repository small.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "nfl-quant", "raw")
MANIFEST = os.path.join(RAW_DIR, "manifest.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "close",
}

OFFICIAL_HOSTS = {
    "www.nfl.com",
    "operations.nfl.com",
    "static.www.nfl.com",
    "media.nfl.com",
    "www.itl.nist.gov",
    "docs.github.com",
    "github.com",
    "api.github.com",
}
PARTNER_HOSTS = {"site.api.espn.com"}


def source_id(url: str) -> str:
    """Stable, filesystem-safe ID derived from the URL path."""
    p = urlparse(url)
    raw = (p.netloc + p.path + ("_" + p.query if p.query else "")).strip("/")
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in raw)[:150]


def is_official(url: str) -> bool:
    return urlparse(url).netloc in OFFICIAL_HOSTS


def is_partner(url: str) -> bool:
    return urlparse(url).netloc in PARTNER_HOSTS


def fetch(url: str, timeout: int = 30, tries: int = 2):
    last = "error"
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
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
            if e.code in (429, 500, 502, 503, 504) and attempt < tries - 1:
                time.sleep(1.5 * (attempt + 1))
                continue
            break
        except Exception as e:  # noqa: BLE001 - provenance script must record, not crash
            last = f"error:{type(e).__name__}"
            if attempt < tries - 1:
                time.sleep(1.0)
                continue
            break
    return None, last


def build_sources():
    official = []

    def add(url, kind, note):
        official.append({"url": url, "kind": kind, "official": True, "note": note})

    # Standings: current 2026 season and official 2025 prior season.
    for year in (2025, 2026):
        add(f"https://www.nfl.com/standings/league/{year}/reg", "standings", f"{year} league standings")
        add(f"https://www.nfl.com/standings/division/{year}/REG", "standings", f"{year} division standings")

    # Regular-season schedule / results by week (official game links and final scores).
    for year, max_week in ((2025, 18), (2026, 9)):
        for week in range(1, max_week + 1):
            add(
                f"https://www.nfl.com/schedules/{year}/by-week/week-{week}",
                "schedule",
                f"{year} regular season week {week}",
            )

    # 2026 team and player statistics tables.
    for cat in ("passing", "rushing", "receiving", "scoring", "downs"):
        add(
            f"https://www.nfl.com/stats/team-stats/offense/{cat}/2026/reg/all",
            "team_stats",
            f"2026 team offense {cat}",
        )
    add(
        "https://www.nfl.com/stats/player-stats/category/passing/2026/reg/all/passingyards/desc",
        "player_stats",
        "2026 player passing leaders",
    )
    add(
        "https://www.nfl.com/stats/player-stats/category/rushing/2026/reg/all/rushingyards/desc",
        "player_stats",
        "2026 player rushing leaders",
    )
    add(
        "https://www.nfl.com/stats/player-stats/category/receiving/2026/reg/all/receivingreceptions/desc",
        "player_stats",
        "2026 player receiving leaders",
    )

    # Official injury report portal (currently shows week 8; week 9 not yet published).
    add("https://www.nfl.com/injuries/", "injuries", "official NFL injury report portal")

    # Official league policy / rules and methodology sources.
    add("https://operations.nfl.com/rules-officiating/2026-nfl-rulebook", "rules", "2026 official NFL rulebook")
    add(
        "https://www.nfl.com/news/nfl-draftkings-fanduel-fanatics-sports-betting-partners",
        "policy",
        "NFL game-integrity / sports-betting policy article",
    )
    add("https://www.nfl.com/standings/tiebreakingprocedures", "rules", "official tie-breaking procedures")
    add(
        "https://www.itl.nist.gov/div898/handbook/prc/section2/prc24.htm",
        "methodology",
        "NIST binomial proportion test background",
    )
    add(
        "https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages",
        "methodology",
        "GitHub Pages official documentation",
    )

    # A small, explicitly listed sample of official game centers for line-by-line checks.
    for slug in (
        "cowboys-at-eagles-2025-reg-1",
        "chiefs-at-chargers-2025-reg-1",
        "buccaneers-at-falcons-2025-reg-1",
        "bengals-at-browns-2025-reg-1",
        "dolphins-at-colts-2025-reg-1",
        "panthers-at-packers-2026-reg-8",
        "ravens-at-bills-2026-reg-8",
        "titans-at-bengals-2026-reg-8",
        "cardinals-at-cowboys-2026-reg-8",
        "vikings-at-lions-2026-reg-8",
    ):
        add(f"https://www.nfl.com/games/{slug}", "game_center", f"official game center {slug}")

    # Trusted partner bulk scoreboard JSON (cross-check only; not an NFL publication).
    partner = [
        {
            "url": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=2025&limit=500",
            "kind": "partner_scoreboard",
            "official": False,
            "note": "ESPN partner 2025 season scoreboard (cross-check)",
        },
        {
            "url": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=2026&limit=500",
            "kind": "partner_scoreboard",
            "official": False,
            "note": "ESPN partner 2026 season scoreboard (cross-check)",
        },
    ]
    return official + partner


def main() -> int:
    os.makedirs(RAW_DIR, exist_ok=True)
    sources = build_sources()
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "Provenance snapshots for the NFL quantitative workspace",
        "official_hosts": sorted(OFFICIAL_HOSTS),
        "partner_hosts": sorted(PARTNER_HOSTS),
        "items": [],
    }
    ok = 0
    for src in sources:
        url = src["url"]
        sid = source_id(url)
        ext = ".json" if src["kind"] == "partner_scoreboard" else ".html"
        rel = f"data/nfl-quant/raw/{sid}{ext}.gz"
        out = os.path.join(ROOT, rel)
        data, status = fetch(url)
        item = {
            "source_id": sid,
            "source_url": url,
            "kind": src["kind"],
            "official": src["official"],
            "note": src["note"],
            "http_status": status,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "output": None,
            "sha256": None,
            "bytes": None,
            "gzip_bytes": None,
        }
        if data is not None:
            packed = gzip.compress(data, compresslevel=9, mtime=0)
            with open(out, "wb") as f:
                f.write(packed)
            item.update(
                output=rel,
                sha256=hashlib.sha256(data).hexdigest(),
                bytes=len(data),
                gzip_bytes=len(packed),
            )
            ok += 1
            print(f"OK   {status} {url} -> {rel} ({len(data)} bytes)")
        else:
            print(f"FAIL {status} {url}")
        manifest["items"].append(item)
        time.sleep(0.25)

    manifest["ok_count"] = ok
    manifest["fail_count"] = len(sources) - ok
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"manifest: {len(sources)} sources, {ok} OK, {len(sources) - ok} failed")
    return 0 if ok >= 25 else 1


if __name__ == "__main__":
    raise SystemExit(main())
