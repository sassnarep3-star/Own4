#!/usr/bin/env python3
"""Verifier for the Week 11 injury-report delta re-read. Standard library only.

  1. private transcription parses: 253 rows, per-club counts and allowed values;
  2. the public JSON's SHA-256 of the private transcription matches the file (tamper check);
  3. the stored 2026-11-18 raw capture matches its manifest SHA-256 (manifests in snapshots/manifest.jsonl);
  4. the delta is re-derived from the two inputs and must equal the published JSON;
  5. public pages: every data row carries an https link; internal links resolve; no localhost; no per-player table;
  6. every flag has an https source.
Exit 0 only if all checks pass. The private transcription is required; if it is absent, the run fails loudly.
"""
import hashlib
import html.parser
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent
PSV = REPO / "private-store" / "nfl-week11" / "week11_injury_report_rows.psv"
RAW = REPO / "nfl-readiness-register" / "snapshots" / "2026-11-18" / "injury_report-2026-11-18T234917Z.html"
MANIFEST = REPO / "nfl-readiness-register" / "snapshots" / "manifest.jsonl"
JSON_F = ROOT / "data" / "delta_week11.json"
PAGES = [ROOT / "index.html", ROOT / "pages" / "delta.html", ROOT / "pages" / "flagged.html"]

EXPECTED_ROWS = 253
EXPECTED_PER_CLUB = {
    "IND": 11, "HOU": 15, "PIT": 10, "PHI": 15, "AZ": 12, "KC": 15, "BAL": 6, "CAR": 13,
    "TB": 6, "DET": 8, "MIA": 11, "BUF": 15, "TEN": 9, "DAL": 14, "NO": 10, "CHI": 5,
    "NYJ": 8, "LAC": 11, "JAX": 13, "NYG": 6, "LV": 6, "DEN": 9, "MIN": 10, "SF": 15,
}
PRACTICE_OK = {"Full Participation in Practice", "Limited Participation in Practice", "Did Not Participate In Practice"}
GAME_OK = {"", "Questionable", "Doubtful", "Out", "Probable"}
failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print("FAIL:", msg)


if not PSV.exists():
    print("FAIL: private transcription missing:", PSV)
    sys.exit(1)

# 1 transcription
rows = []
for raw in PSV.read_text(encoding="utf-8").splitlines():
    if not raw or raw.startswith("#") or raw.startswith(("GAME|", "NOINJ|")):
        continue
    parts = raw.split("|")
    check(len(parts) == 6, f"bad column count: {raw}")
    if len(parts) == 6:
        rows.append(parts)
check(len(rows) == EXPECTED_ROWS, f"row count {len(rows)} != {EXPECTED_ROWS}")
per = {}
for r in rows:
    per[r[0]] = per.get(r[0], 0) + 1
check(per == EXPECTED_PER_CLUB, "per-club counts differ from transcription record")
for r in rows:
    check(r[4] in PRACTICE_OK, f"unexpected practice status: {r[1]}")
    check(r[5] in GAME_OK, f"unexpected game status: {r[1]}")
    check(bool(r[1].strip()), "empty player name")

# 2 + 3 hashes
digest_psv = hashlib.sha256(PSV.read_bytes()).hexdigest()
digest_raw = hashlib.sha256(RAW.read_bytes()).hexdigest()
manifest_hashes = set()
for line in MANIFEST.read_text(encoding="utf-8").splitlines():
    try:
        manifest_hashes.add(json.loads(line).get("sha256"))
    except json.JSONDecodeError:
        pass
check(digest_raw in manifest_hashes, "stored 2026-11-18 raw capture hash not in snapshot manifest")
data = json.loads(JSON_F.read_text(encoding="utf-8"))
check(data["capture_now"]["private_transcription_sha256"] == digest_psv,
      "public JSON transcription hash does not match the private file")
check(data["capture_then"]["raw_file_sha256"] == digest_raw, "public JSON raw hash does not match the stored file")

# 4 re-derive delta
spec = importlib.util.spec_from_file_location("b", ROOT / "build.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
rows2, _, _ = b.parse_private()
raw_then = b.parse_raw_1118()
per_club = b.delta(rows2, raw_then)
check(per_club == data["per_club_delta"], "re-derived delta differs from published JSON")
check(data["clubs_total"] == 32 and data["clubs_compared"] == 26, "club totals unexpected")
check(data["clubs_changed"] == 1 and data["clubs_absent_both_reads"] == 6, "delta totals unexpected")
check(data["rows_unchanged_count"] == 242, "unchanged-row count unexpected")
for f in data["flags"]:
    check(f["source"].startswith("https://"), f"flag {f['id']} has no https source")


# 5 pages
class Collector(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs, self.rows, self.in_tr = [], [], False
        self.cur_links, self.tr_has_td = [], False
        self.headers = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and "href" in a:
            self.hrefs.append(a["href"])
            if self.in_tr:
                self.cur_links.append(a["href"])
        if tag == "tr":
            self.in_tr, self.cur_links, self.tr_has_td = True, [], False
        if tag == "td" and self.in_tr:
            self.tr_has_td = True
        if tag == "th":
            self._th = True

    def handle_data(self, d):
        if getattr(self, "_th", False) and d.strip():
            self.headers.append(d.strip())

    def handle_endtag(self, tag):
        if tag == "th":
            self._th = False
        if tag == "tr" and self.in_tr:
            if self.tr_has_td:
                self.rows.append(list(self.cur_links))
            self.in_tr = False


for page in PAGES:
    text = page.read_text(encoding="utf-8")
    check("localhost" not in text and "127.0.0.1" not in text, f"localhost reference in {page.name}")
    c = Collector()
    c.feed(text)
    for row_links in c.rows:
        check(any(h.startswith("https://") for h in row_links), f"data row without https source in {page.name}")
    for href in c.hrefs:
        if href.startswith(("http", "#")):
            continue
        check((page.parent / href).resolve().exists(), f"broken internal link {href} in {page.name}")
    check("Practice status" not in c.headers and "Injuries" not in c.headers,
          f"per-player table found in public page {page.name}")

print(json.dumps({
    "private_rows": len(rows), "clubs_total": data["clubs_total"], "clubs_compared": data["clubs_compared"],
    "unchanged": data["clubs_no_change"], "changed": data["clubs_changed"],
    "absent_both_reads": data["clubs_absent_both_reads"], "flags": len(data["flags"]),
    "sha256_private": digest_psv, "sha256_raw_1118": digest_raw, "failures": len(failures)}, indent=2))
sys.exit(1 if failures else 0)
