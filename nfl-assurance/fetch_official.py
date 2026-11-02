#!/usr/bin/env python3
"""Acquire public NFL pages without authentication. Never substitutes a third-party feed.

Run by .github/workflows/nfl-lab.yml when the local network cannot reach NFL.com.
Stores compressed response bytes and a SHA-256 provenance manifest. Parsing is a
separate, deterministic step; a successful HTTP response is not source verification.
"""
from __future__ import annotations
import argparse
import concurrent.futures
import gzip
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'sources'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
           'Accept': 'text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8',
           'Accept-Language': 'en-US,en;q=0.9', 'Accept-Encoding': 'gzip, deflate',
           'Connection': 'close'}
SCHEDULES = [(year, week, f'https://www.nfl.com/schedules/{year}/by-week/week-{week}')
             for year, weeks in [(2024, 18), (2025, 18), (2026, 8)]
             for week in range(1, weeks + 1)]
REFERENCES = [
    ('rules', 'https://operations.nfl.com/rules-officiating/2026-nfl-rulebook'),
    ('terms', 'https://www.nfl.com/legal/terms'),
    ('current-injuries', 'https://www.nfl.com/injuries/'),
    ('next-slate', 'https://www.nfl.com/schedules/2026/by-week/week-9'),
    ('sample-game', 'https://www.nfl.com/games/cowboys-at-eagles-2025-reg-1?tab=stats'),
    ('upcoming-game', 'https://www.nfl.com/games/bears-at-seahawks-2026-reg-8'),
    ('stats-portal', 'https://www.nfl.com/stats/'),
    ('receiving-leaders', 'https://www.nfl.com/stats/player-stats/category/receiving/2026/reg/all/receivingyards/desc'),
    ('passing-leaders', 'https://www.nfl.com/stats/player-stats/category/passing/2026/reg/all/passingyards/desc'),
    ('rushing-leaders', 'https://www.nfl.com/stats/player-stats/category/rushing/2026/reg/all/rushingyards/desc'),
    ('sample-receiver-logs', 'https://www.nfl.com/players/jaxon-smith-njigba/stats/logs/'),
    ('sample-qb-logs', 'https://www.nfl.com/players/caleb-williams/stats/logs/'),
]

def fetch_one(item):
    key, url = item
    record = {'id': key, 'source_url': url, 'publisher': 'National Football League',
              'retrieved_utc': datetime.now(timezone.utc).isoformat(),
              'http_status': None, 'final_url': None, 'sha256': None,
              'bytes': None, 'snapshot': None, 'error': None}
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=40) as response:
                data = response.read()
                record.update(http_status=response.status, final_url=response.url)
                if response.headers.get('Content-Encoding') == 'gzip' or data[:2] == b'\x1f\x8b':
                    data = gzip.decompress(data)
            record.update(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
            path = RAW / f'{key}.html.gz'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(gzip.compress(data, compresslevel=9, mtime=0))
            record['snapshot'] = str(path.relative_to(ROOT))
            text = data.decode('utf-8', errors='replace')
            record['next_data_present'] = '__NEXT_DATA__' in text
            record['script_json_ids'] = re.findall(r'<script[^>]+id=[\"\']([^\"\']+)[\"\'][^>]*>', text)[:20]
            record['game_links'] = len(set(re.findall(r'https://www\.nfl\.com/games/[a-z0-9-]+', text)))
            print(f'OK {key}: {len(data)} bytes; next_data={record["next_data_present"]}', flush=True)
            return record
        except urllib.error.HTTPError as exc:
            record['http_status'] = exc.code
            record['error'] = str(exc)
            if exc.code not in (429, 500, 502, 503, 504):
                break
        except Exception as exc:
            record['error'] = f'{type(exc).__name__}: {exc}'
        time.sleep(2 * (attempt + 1))
    print(f'FAIL {key}: {record["error"]}', flush=True)
    return record

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['discovery', 'schedules', 'references'], default='schedules')
    args = parser.parse_args()
    if args.phase == 'discovery':
        items = [('sample-schedule', SCHEDULES[0][2])] + REFERENCES[:2] + REFERENCES[4:6]
    elif args.phase == 'references':
        items = REFERENCES
    else:
        items = [(f'schedule-{year}-{week:02}', url) for year, week, url in SCHEDULES]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        records = list(executor.map(fetch_one, items))
    RAW.mkdir(parents=True, exist_ok=True)
    manifest_path = RAW / f'manifest-{args.phase}.json'
    manifest_path.write_text(json.dumps({'phase': args.phase, 'items': records}, indent=2) + '\n')
    print(f'{sum(r["http_status"] == 200 for r in records)}/{len(records)} retrieved', flush=True)
    # Acquisition failure is not silently converted to a fabricated dataset.
    if not any(r['http_status'] == 200 for r in records):
        raise SystemExit(2)

if __name__ == '__main__':
    main()
