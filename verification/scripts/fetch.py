#!/usr/bin/env python3
"""fetch.py — provenance-preserving fetcher for official NBA sources.

Every request is recorded in verification/raw/manifest.json with the exact URL,
UTC timestamp, HTTP status, byte count and SHA-256 of the stored body.
Failures are recorded as failures; nothing is ever invented or filled in later.

Raw bodies land in verification/raw/<kind>/<key>.<ext> verbatim.
"""
import gzip, hashlib, json, os, re, ssl, sys, time, urllib.error, urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                      # verification/
RAW = os.path.join(ROOT, "raw")
MANIFEST = os.path.join(RAW, "manifest.json")

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "close",
}
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def _manifest():
    if os.path.exists(MANIFEST):
        return json.load(open(MANIFEST))
    return {"created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "items": []}


def get(url, kind, key, ext="html", retries=3, timeout=45):
    """Fetch url, store body at raw/<kind>/<key>.<ext>, append provenance, return (path, status)."""
    outdir = os.path.join(RAW, kind)
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f"{key}.{ext}")
    last = None
    for attempt in range(retries):
        started = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=CTX, timeout=timeout) as r:
                body = r.read()
                status = r.status
                if r.headers.get("Content-Encoding") == "gzip" or body[:2] == b"\x1f\x8b":
                    body = gzip.decompress(body)
            with open(path, "wb") as f:
                f.write(body)
            rec = {"url": url, "kind": kind, "key": key, "requested_utc": started,
                   "http_status": status, "bytes": len(body),
                   "sha256": hashlib.sha256(body).hexdigest(), "file": os.path.relpath(path, ROOT)}
            m = _manifest()
            m["items"] = [i for i in m["items"] if not (i["url"] == url and i["kind"] == kind and i["key"] == key)]
            m["items"].append(rec)
            m["updated_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            json.dump(m, open(MANIFEST, "w"), indent=1)
            return path, status
        except Exception as e:                      # noqa: BLE001 - recorded, never hidden
            last = f"{type(e).__name__}: {e}"
            time.sleep(1.5 * (attempt + 1))
    rec = {"url": url, "kind": kind, "key": key, "requested_utc": started,
           "http_status": None, "error": last, "file": None}
    m = _manifest()
    m["items"] = [i for i in m["items"] if not (i["url"] == url and i["kind"] == kind and i["key"] == key)]
    m["items"].append(rec)
    json.dump(m, open(MANIFEST, "w"), indent=1)
    return None, None


if __name__ == "__main__":
    tests = [("https://www.nba.com/games?date=2026-11-04", "smoke", "games_2026-11-04", "html"),
             ("https://cdn.nba.com/static/json/liveData/scoreboard/scoreboard_2026-11-04.json",
              "smoke", "cdn_scoreboard_2026-11-04", "json"),
             ("https://statsdmz.nba.com/pdfs/20261021/20261021_ATLORL.pdf", "smoke", "pdf_20261021_ATLORL", "pdf")]
    for u, k, key, ext in tests:
        p, s = get(u, k, key, ext)
        print(f"{s} {u} -> {p}")
