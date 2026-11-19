#!/usr/bin/env python3
"""Parse the stored 2026-11-18 official injury-report capture into per-team rows.

Why this file exists: the brief asserts "only 6 of 254 report rows carry a game
designation". That is a countable claim, but the copy it refers to is not in the repo.
The earliest faithful machine copy is the 2026-11-18T23:49:17Z capture taken by the
nfl-readiness-register workflow (raw HTML + sha256 in its manifest). This parser
re-counts from that copy so the number published by this workspace is measured from a
stored, hashed artifact — not retyped from a brief.

It counts, per club table: player rows, rows with a blank Game Status, rows with a
blank Injury description, and the designation split. A blank cell is counted as blank,
never filled.

Run: python3 nfl-desk/engine/parse_injuries.py
"""
import hashlib
import html
import json
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)
CAPTURE = os.path.join(ROOT, "nfl-readiness-register", "snapshots", "2026-11-18",
                       "injury_report-2026-11-18T234917Z.html")
OUT = os.path.join(NS, "data", "injuries_2026-11-18_parsed.json")
SOURCE_URL = "https://www.nfl.com/injuries/"

TABLE = re.compile(r'<tbody>(.*?)</tbody>', re.S)
SECTION = re.compile(r'<div class="d3-o-section-sub-title"><span>([^<]+)</span></div>')
ROW = re.compile(r"<tr>(.*?)</tr>", re.S)
CELL = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
TAG = re.compile(r"<[^>]+>")


def text(cell):
    return html.unescape(TAG.sub("", cell)).strip()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    raw = open(CAPTURE, encoding="utf-8", errors="replace").read()
    title = re.search(r"<title>([^<]+)</title>", raw)
    # Walk the document once, in order, so each club table is attached to the club
    # heading that precedes it.
    events = []
    for m in SECTION.finditer(raw):
        events.append((m.start(), "club", m.group(1).strip()))
    for m in TABLE.finditer(raw):
        events.append((m.start(), "table", m.group(1)))
    events.sort()

    clubs, pending = [], None
    for _, kind, payload in events:
        if kind == "club":
            pending = payload
            continue
        if pending is None:
            continue
        rows = []
        for r in ROW.finditer(payload):
            cells = [text(c) for c in CELL.findall(r.group(1))]
            if len(cells) < 5:
                continue
            rows.append({"player": cells[0], "position": cells[1], "injury": cells[2],
                         "practice": cells[3], "game_status": cells[4]})
        clubs.append({"club": pending, "rows": rows})
        pending = None

    total = sum(len(c["rows"]) for c in clubs)
    designated = sum(1 for c in clubs for r in c["rows"] if r["game_status"])
    no_injury_text = sum(1 for c in clubs for r in c["rows"] if not r["injury"])
    split = Counter(r["game_status"] for c in clubs for r in c["rows"] if r["game_status"])
    practice = Counter(r["practice"] for c in clubs for r in c["rows"] if r["practice"])

    out = {
        "dataset": "nfl_desk_injury_capture_parse",
        "title": "Week 11 official injury report, re-counted from the stored 2026-11-18 capture",
        "source_url": SOURCE_URL,
        "publisher": "NFL.com (official)",
        "captured_utc": "2026-11-18T23:49:17Z",
        "captured_by": "nfl-readiness-register scheduled capture (not this session)",
        "raw_path": "nfl-readiness-register/snapshots/2026-11-18/injury_report-2026-11-18T234917Z.html",
        "raw_sha256": sha256(CAPTURE),
        "manifest_sha256": "e1bbea1bf036c949825106a9a9e51de307da86680583d201a091682d7d012e7b",
        "page_title": title.group(1).strip() if title else "",
        "parser": "nfl-desk/engine/parse_injuries.py",
        "counts": {
            "club_tables": len(clubs),
            "player_rows": total,
            "rows_with_game_status": designated,
            "rows_blank_game_status": total - designated,
            "rows_blank_injury_text": no_injury_text,
        },
        "game_status_split": dict(sorted(split.items())),
        "practice_split": dict(sorted(practice.items())),
        "clubs": clubs,
        "note": ("Counts are taken from the stored HTML, cell by cell. A blank Game Status or "
                 "Injury cell is reported as blank; nothing is inferred from practice status. "
                 "The capture is one snapshot of one week, so it cannot by itself reconcile the "
                 "brief's 6-of-254 figure, which refers to a copy and date that are not in the repo."),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    if out["raw_sha256"] != out["manifest_sha256"]:
        raise SystemExit("capture hash does not match the manifest — refusing to publish counts")
    print(json.dumps(out["counts"], indent=1))
    print("game status:", out["game_status_split"])
    print("-> %s" % OUT)


if __name__ == "__main__":
    main()
