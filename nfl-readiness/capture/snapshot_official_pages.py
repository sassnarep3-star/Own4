#!/usr/bin/env python3
"""
nfl-readiness — immutable official availability snapshotter (REQ-28/29/53/61/62).

Fetches the official NFL injury report and the league reserve-list ledger,
stores the raw bytes immutably under snapshots/<UTC-date>/, records sha256 +
fetch timestamps in an append-only manifest, and FAILS LOUDLY (exit non-zero)
when the source schema drifts (REQ-61) instead of publishing blanks.

Also supports --selftest against a fixture file to validate the parser
without network access (used by tests and CI).

Usage:
  python3 capture/snapshot_official_pages.py                 # live capture
  python3 capture/snapshot_official_pages.py --selftest FIX  # parser self-test
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
SNAP_DIR = os.path.join(NS, "snapshots")
MANIFEST = os.path.join(SNAP_DIR, "manifest.jsonl")
SCHEMA = json.load(open(os.path.join(HERE, "expected_schema.json")))

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Own4-research-capture/1.0"}


def log(msg):
    print("[capture] %s" % msg, flush=True)


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def check_schema(kind, text):
    """Drift alarm: every required marker must be present, else fail loudly."""
    spec = SCHEMA[kind]
    missing = [m for m in spec["required_markers"] if m not in text]
    if missing:
        log("DRIFT ALARM for %s: missing markers %s" % (kind, missing))
        log("Refusing to write a parsed record. Raw bytes are still saved for replay.")
        return False
    return True


def count_team_tables(html_text):
    """Count rendered club tables heuristically: team-name headings before tables."""
    # In raw HTML the report is usually JS-rendered; if club blocks are absent
    # the count is 0 and schema check has already failed loudly.
    return len(re.findall(r"Game Status", html_text))


def append_manifest(entry):
    os.makedirs(SNAP_DIR, exist_ok=True)
    with open(MANIFEST, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")


def capture(kind):
    spec = SCHEMA[kind]
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%dT%H%M%SZ")
    day = now.strftime("%Y-%m-%d")
    url = spec["url"].format(Y=now.year, M=f"{now.month:02d}")
    log("%s: fetching %s" % (kind, url))
    raw = fetch(url)
    text = raw.decode("utf-8", "replace")
    ok = check_schema(kind, text)
    outdir = os.path.join(SNAP_DIR, day)
    os.makedirs(outdir, exist_ok=True)
    raw_path = os.path.join(outdir, "%s-%s.html" % (kind, stamp))
    with open(raw_path, "wb") as f:
        f.write(raw)
    row_markers = count_team_tables(text)
    entry = {
        "capture_id": "%s-%s" % (kind, stamp),
        "kind": kind,
        "source_url": url,
        "captured_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "raw_path": os.path.relpath(raw_path, NS),
        "sha256": sha256_bytes(raw),
        "bytes": len(raw),
        "game_status_markers_found": row_markers,
        "schema_ok": ok,
        "status": "OK" if ok else "SCHEMA-DRIFT-RAW-SAVED",
    }
    append_manifest(entry)
    log("%s -> %s (sha256 %s, schema_ok=%s)" % (kind, entry["raw_path"], entry["sha256"][:12], ok))
    return ok


def selftest(fixture_path):
    """Validate the parser/schema checker against a local fixture (no network)."""
    text = open(fixture_path, encoding="utf-8").read()
    kinds = [k for k in SCHEMA if isinstance(SCHEMA[k], dict)]
    kinds_ok = []
    for kind in kinds:
        ok = check_schema(kind, text)
        kinds_ok.append((kind, ok))
    passed = all(ok for kind, ok in kinds_ok if SCHEMA[kind]["expect_fixture_match"])
    for kind, ok in kinds_ok:
        log("selftest %-14s schema_ok=%s" % (kind, ok))
    print("SELFTEST", "PASS" if passed else "FAIL")
    return 0 if passed else 1


def main():
    if "--selftest" in sys.argv:
        fixture = sys.argv[sys.argv.index("--selftest") + 1]
        sys.exit(selftest(fixture))
    os.makedirs(SNAP_DIR, exist_ok=True)
    kinds = [k for k in SCHEMA if isinstance(SCHEMA[k], dict)]
    results = [capture(k) for k in kinds if SCHEMA[k]["enabled"]]
    # Loud failure: any schema drift exits non-zero so the scheduled run alerts.
    if not all(results):
        log("One or more sources failed schema checks — alerting (exit 2).")
        sys.exit(2)
    # freshness monitor: manifest must show recent successful captures
    if os.path.exists(MANIFEST):
        entries = [json.loads(l) for l in open(MANIFEST) if l.strip()]
        if entries and all(e["status"] != "OK" for e in entries[-len(results) * 3:]):
            log("Freshness alert: no OK captures in recent manifest tail.")
            sys.exit(3)
    log("All captures OK.")


if __name__ == "__main__":
    main()
