#!/usr/bin/env python3
"""fetch_official_data.py — network stage of the Own4 verification pipeline.

Runs where official NBA endpoints are reachable (GitHub Actions). It only *fetches*:
no parsing, no inference, no filling-in. Every response is stored verbatim under
verification/raw/ with a SHA-256 and an HTTP status in verification/raw/manifest.json.
Parsing and statistics happen in verification/scripts/*.py, locally and in CI.

Sources (all first-party NBA):
  https://www.nba.com/games?date=YYYY-MM-DD                      daily scoreboard
  https://www.nba.com/standings                                 standings
  https://www.nba.com/stats/teams/traditional                   team per-game stats
  https://www.nba.com/stats/players/traditional?Season=...      player per-game stats
  https://www.nba.com/stats/player/<id>/boxscores-traditional   per-player game log
"""
import gzip, hashlib, json, os, re, ssl, sys, time, urllib.error, urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # verification/
RAW = os.path.join(ROOT, "raw")
MANIFEST = os.path.join(RAW, "manifest.json")
SEASON = "2026-27"
DATES = ["2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23", "2026-10-24",
         "2026-10-25", "2026-10-26", "2026-10-27", "2026-10-28", "2026-10-29",
         "2026-10-30", "2026-10-31", "2026-11-01", "2026-11-02", "2026-11-03",
         "2026-11-04", "2026-11-05"]
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/125.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://www.nba.com/",
}
CTX = ssl.create_default_context()

records = []


def fetch(url, kind, key, ext="html", tries=3, timeout=45):
    outdir = os.path.join(RAW, kind)
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f"{key}.{ext}")
    err = None
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=CTX, timeout=timeout) as r:
                body = r.read()
                status = r.status
                enc = (r.headers.get("Content-Encoding") or "").lower()
                if "gzip" in enc or body[:2] == b"\x1f\x8b":
                    try:
                        body = gzip.decompress(body)
                    except Exception:
                        pass
            open(path, "wb").write(body)
            rec = {"url": url, "kind": kind, "key": key, "http_status": status,
                   "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                   "file": os.path.relpath(path, ROOT),
                   "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            records.append(rec)
            print(f"OK {status} {url} -> {rec['file']} ({len(body)} bytes)")
            return body, status
        except urllib.error.HTTPError as e:
            err = f"HTTP {e.code}"
            if e.code in (429, 500, 502, 503) and attempt < tries - 1:
                time.sleep(2 * (attempt + 1)); continue
            break
        except Exception as e:                                   # noqa: BLE001
            err = f"{type(e).__name__}: {e}"
            time.sleep(2 * (attempt + 1))
    records.append({"url": url, "kind": kind, "key": key, "http_status": None, "error": err,
                    "bytes": 0, "sha256": None, "file": None,
                    "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    print(f"FAIL {err} {url}")
    return None, None


def main():
    os.makedirs(RAW, exist_ok=True)
    # 1. daily scoreboards (one page per date, all games of that date)
    for d in DATES:
        fetch(f"https://www.nba.com/games?date={d}", "nba_games", f"games_{d}")
        time.sleep(0.5)
    # 2. season tables
    fetch("https://www.nba.com/standings", "nba_tables", "standings")
    fetch("https://www.nba.com/stats/teams/traditional", "nba_tables", "teams_traditional")
    blob, _ = fetch(f"https://www.nba.com/stats/players/traditional?Season={SEASON}"
                    "&PerMode=PerGame&PerPage=100&dir=-1&sort=PTS", "nba_tables", "players_traditional")
    # 3. per-player game logs for the players listed on the official season table
    ids = []
    if blob:
        txt = blob.decode("utf-8", "ignore").replace('\\"', '"')
        seen = set()
        for pid in re.findall(r'/stats/player/(\d{6,8})', txt):
            if pid not in seen:
                seen.add(pid); ids.append(pid)
    print(f"player ids discovered on official table: {len(ids)}")
    ids = ids[:120]
    for pid in ids:
        fetch(f"https://www.nba.com/stats/player/{pid}/boxscores-traditional?Season={SEASON}",
              "nba_playerlogs", f"player_{pid}")
        time.sleep(0.4)
    m = {"updated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
         "season": SEASON,
         "note": ("Network stage only. Bodies are verbatim official NBA responses; "
                  "no parsing or inference happens here."),
         "ok": sum(1 for r in records if r["http_status"]),
         "failed": sum(1 for r in records if not r["http_status"]),
         "items": records}
    json.dump(m, open(MANIFEST, "w"), indent=1)
    print(f"manifest: {m['ok']} ok / {m['failed']} failed")
    return 0 if m["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
