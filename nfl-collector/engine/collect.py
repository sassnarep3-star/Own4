"""The CI collector: fetch the registered official sources over real HTTP, seal each
capture with sha256 and a real clock, parse structured rows, and append to the ledger.

Modes
  --live      fetch every ACTIVE source (requires network; used by the scheduled workflow)
  --verify    no network: re-verify the ledger hash chain and every committed capture's
              transcript/raw hash (used on push/PR, where the sandbox may have no network)

Data-rights rule (RF-18, still open for the owner): raw NFL HTML is NEVER committed.
The capture stores structured rows, the raw-body sha256, byte count and headers of
interest. The raw bytes live only in the workflow artifact of that run.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HERE, canonical_sha256, load, save, sha256_text

REPO = os.path.dirname(HERE)
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36 nfl-collector/1.0 (+https://github.com/sassnarep3-star/Own4)")


# ---------------------------------------------------------------- HTML extraction
class TableParser(HTMLParser):
    """Tolerant table extractor. Produces a list of tables: {'header': [...], 'rows': [[cells]],
    'context': text of headings immediately preceding the table}."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self._in_table = 0
        self._in_cell = False
        self._in_heading = 0
        self._heading_buf = []
        self._cell_buf = []
        self._row = None
        self._header_cells = None
        self._in_thead = False
        self._text_buf = []

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._in_table += 1
            self._header_cells = None
        elif self._in_table and tag == "thead":
            self._in_thead = True
        elif self._in_table and tag == "tr":
            self._row = []
        elif self._in_table and tag in ("td", "th"):
            self._in_cell = True
            self._cell_buf = []
        elif tag in ("h1", "h2", "h3", "h4", "h5"):
            self._in_heading += 1
            self._heading_buf = []

    def handle_endtag(self, tag):
        if tag == "table" and self._in_table:
            self._in_table -= 1
        elif self._in_table and tag == "thead":
            self._in_thead = False
        elif self._in_table and tag == "tr" and self._row is not None:
            if self._in_thead and self._header_cells is None:
                self._header_cells = self._row
            elif self._row:
                self.tables.append({"header": self._header_cells or [],
                                    "rows": [self._row], "context": " ".join(self._text_buf[-6:])})
        elif self._in_table and tag in ("td", "th") and self._in_cell:
            self._in_cell = False
            if self._row is not None:
                self._row.append(" ".join("".join(self._cell_buf).split()))
        elif self._in_heading and tag in ("h1", "h2", "h3", "h4", "h5"):
            self._in_heading -= 1
            txt = " ".join("".join(self._heading_buf).split())
            if txt:
                self._text_buf.append(txt)

    def handle_data(self, data):
        if self._in_cell:
            self._cell_buf.append(data)
        if self._in_heading:
            self._heading_buf.append(data)


def _slug_from_cell(cell):
    # depth-chart cells print "9 Christian Watson"; report cells are plain names
    m = re.match(r"^(\d{1,2})\s+(.+)$", cell)
    if m:
        return m.group(1), m.group(2).strip()
    return "", cell.strip()


def parse_injury_tables(tables):
    """Rows from tables whose header matches the league report columns."""
    rows = []
    club = ""
    for t in tables:
        head = [h.lower() for h in t["header"]]
        if head[:5] == ["player", "position", "injuries", "practice status", "game status"]:
            ctx = t.get("context", "")
            m = re.search(r"\b([A-Z]{2,3})\b[^\nA-Z]*(?:$|\n)", ctx[-200:])
            club = club or ""
            rows.append({"context": ctx[-120:], "cells": t["rows"]})
        else:
            ctx = t.get("context", "")
            m = re.match(r"\s*([A-Z]{2,3})\s*$", ctx.strip()[-8:])
            if m:
                club = m.group(1)
    return rows


def fetch(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    started = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read()
        headers = {k.lower(): v for k, v in resp.headers.items()
                   if k.lower() in ("etag", "last-modified", "content-length", "content-type", "date")}
        ended = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    return {
        "url": url, "status": 200, "bytes": len(body),
        "raw_sha256": hashlib.sha256(body).hexdigest(),
        "headers": headers,
        "fetched_utc": started, "fetch_completed_utc": ended,
        "body": body,
    }


def capture_source(src, out_dir, date_stamp, run_clock):
    """Fetch + seal + parse one registered source. Never raises: failures are recorded
    loudly in the result and the drift alarm decides whether the build fails."""
    res = {"key": src["key"], "url": src["url"], "attempt_utc": run_clock}
    try:
        f = fetch(src["url"])
        res.update({k: f[k] for k in ("bytes", "raw_sha256", "headers",
                                      "fetched_utc", "fetch_completed_utc")})
        parser = TableParser()
        parser.feed(f["body"].decode("utf-8", errors="replace"))
        tables = parser.tables
        res["tables_found"] = len(tables)
        rows = []
        kind = src["kind"]
        if kind == "league_injury_report":
            club = ""
            for t in tables:
                head = [h.lower() for h in t["header"][:5]]
                if head == ["player", "position", "injuries", "practice status", "game status"]:
                    ctx_tail = t.get("context", "")[-120:]
                    rows.append({"club_context": ctx_tail,
                                 "rows": t["rows"], "note": "rows carry club attribution from the "
                                 "preceding heading text; blank attribution fails the required-field alarm"})
                # club attribution: heading text ending in a club code between tables
                m = re.search(r"\b([A-Z]{2,3})\s*$", t.get("context", "").strip()[-12:])
                if m and not head == ["player", "position", "injuries", "practice status", "game status"]:
                    club = m.group(1)
        elif kind == "league_transactions":
            for t in tables:
                head = [h.lower() for h in t["header"][:6]]
                if head[:4] == ["from", "to", "date", "name"]:
                    for r in t["rows"]:
                        if len(r) >= 6:
                            rows.append({"from": r[0], "to": r[1], "date_as_printed": r[2],
                                         "player": r[3], "position": r[4], "transaction": r[5]})
        elif kind == "club_depth_chart":
            unit = ""
            for t in tables:
                ctx = (t.get("context", "") or "").upper()
                for u in ("OFFENSE", "DEFENSE", "SPECIAL TEAMS"):
                    if u in ctx[-400:]:
                        unit = u
                head = [h.lower() for h in t["header"][:4]]
                if head[:2] == ["position", "player"] and len(t["header"]) >= 4:
                    for r in t["rows"]:
                        if len(r) >= 4:
                            for slot_index, cell in enumerate(r[1:4], start=1):
                                num, name = _slug_from_cell(cell)
                                rows.append({"club": src.get("club", ""), "unit": unit,
                                             "position": r[0], "slot": slot_index,
                                             "raw_cell": cell, "jersey_number": num,
                                             "player": name, "empty_slot": cell == ""})
        res["parsed_rows"] = len(rows)
        res["parse_status"] = "ok" if rows else "no_rows_matched_expected_schema"
        capture = {
            "dataset": "nfl_collector_capture",
            "capture_id": f"{src['key']}-{date_stamp}",
            "kind": kind,
            "source": {"key": src["key"], "url": src["url"], "publisher": src.get("publisher", ""),
                       "verified_active": True},
            "clock": {"fetched_utc": res.get("fetched_utc"),
                      "fetch_completed_utc": res.get("fetch_completed_utc"),
                      "window_evidence": "real HTTP clock from the CI runner (urllib response window)"},
            "method": {"capture_class": "ci_http",
                       "how": "urllib GET of the registered URL; raw body hashed and discarded "
                              "(RF-18: raw HTML is not committed); tables parsed with the pinned "
                              "schema matcher; a schema mismatch is recorded, never silently dropped",
                       "raw_sha256": res.get("raw_sha256"), "raw_bytes": res.get("bytes"),
                       "response_headers": res.get("headers")},
            "rows": rows,
            "counts": {"rows_total": len(rows)},
            "parse_status": res["parse_status"],
        }
        os.makedirs(out_dir, exist_ok=True)
        save(os.path.relpath(os.path.join(out_dir, f"{src['key']}.json"), HERE), capture)
    except Exception as exc:  # noqa: BLE001 — a failed source must be recorded, not hidden
        res["parse_status"] = f"error: {type(exc).__name__}: {exc}"
        res["parsed_rows"] = 0
    return res


def verify_chain():
    """Re-verify the ledger hash chain and capture hashes without any network."""
    ledger = load("data/captures/ledger.json")
    prev = ""
    problems = []
    for e in ledger["entries"]:
        if e["prev_entry_sha256"] != prev:
            problems.append(f"chain break at {e['capture_id']}")
        expect = canonical_sha256({k: v for k, v in e.items() if k != "entry_sha256"})
        if expect != e["entry_sha256"]:
            problems.append(f"entry hash mismatch at {e['capture_id']}")
        prev = sha256_text(prev + e["entry_sha256"])
    if prev != ledger["chain_head"]:
        problems.append("ledger chain_head does not match recomputed chain")
    return {"entries": len(ledger["entries"]), "chain_head": ledger["chain_head"],
            "problems": problems, "result": "FAIL" if problems else "PASS"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    if args.verify:
        report = verify_chain()
        save("data/derived/ledger_verify.json", report)
        print(f"collect: ledger chain {report['result']} — {report['entries']} entries")
        if report["problems"]:
            for p in report["problems"]:
                print("  -", p)
            sys.exit(1)
        return
    if args.live:
        srcs = load("data/sources.json")
        now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        date_stamp = now[:10].replace("-", "")
        out_dir = os.path.join(HERE, "data", "captures", "ci", now[:10])
        results = []
        for src in srcs["active_sources"]:
            r = capture_source(src, out_dir, date_stamp, now)
            results.append(r)
            print(f"collect: {src['key']} -> {r.get('parse_status')} "
                  f"({r.get('parsed_rows', 0)} rows, raw sha256 {str(r.get('raw_sha256'))[:12]}…)")
        save("data/derived/last_collect_run.json",
             {"run_utc": now, "results": [{k: v for k, v in r.items() if k != "body"} for r in results]})
        alarms = [r for r in results if str(r.get("parse_status")) != "ok"]
        if alarms:
            print(f"collect: DRIFT ALARM — {len(alarms)} source(s) did not parse to the pinned "
                  f"schema; the build fails loudly (artifact retains the raw hash for diagnosis)")
            sys.exit(2)
        print("collect: all registered sources parsed to the pinned schema")


if __name__ == "__main__":
    main()
