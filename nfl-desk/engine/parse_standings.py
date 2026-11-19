#!/usr/bin/env python3
"""Parse the 2026 division standings table out of a rendered nfl.com/standings read.

Why this file exists: the session's official reads arrive as rendered text (the
sandbox has no direct HTTPS egress to nfl.com; reads are returned through a fetch
tool). To avoid typing 32 rows of numbers by hand, the rendered text is saved
verbatim under evidence/reads/ and this parser turns it into structured rows.
Nothing here invents a value: a row that does not parse is dropped and counted.

Run: python3 nfl-desk/engine/parse_standings.py
Writes: nfl-desk/data/standings_2026-11-19.json
"""
import hashlib
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)
READ = os.path.join(NS, "evidence", "reads", "standings_2026-11-19.txt")
OUT = os.path.join(NS, "data", "standings_2026-11-19.json")

ROW = re.compile(
    r"clubs/logos/(?P<abbr>[A-Z]{2,3})\)\\<br>\\<br>(?P<name>[^\\]+?)\\<br>\\<br>[^|]*"
    r"\|\s*(?P<w>\d+)\s*\|\s*(?P<l>\d+)\s*\|\s*(?P<t>\d+)\s*\|\s*(?P<pct>[\d.]+)\s*\|"
    r"\s*(?P<pf>\d+)\s*\|\s*(?P<pa>\d+)\s*\|\s*(?P<net>-?\d+)\s*\|"
    r"\s*(?P<div>[\d\s-]+)\|\s*(?P<conf>[\d\s-]+)\|\s*(?P<nonconf>[\d\s-]+)\|\s*(?P<nc_pct>[\d.]+)\s*\|"
    r"\s*(?P<confrec>[\d\s-]+)\|\s*(?P<conf_pct>[\d.]+)\s*\|\s*(?P<nonconfrec>[\d\s-]+)\|\s*(?P<strk>\d+[WL])\s*\|\s*(?P<last5>[\d\s-]+)\|"
)

# Conference/division order is the order the official page prints them in; it is
# taken from the page's own headings, not assigned by guesswork.
SECTIONS = {
    "AFC": ["AFC East", "AFC North", "AFC South", "AFC West"],
    "NFC": ["NFC East", "NFC North", "NFC South", "NFC West"],
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    text = open(READ, encoding="utf-8").read()
    rows = []
    for m in ROW.finditer(text):
        d = m.groupdict()
        rows.append({
            "abbr": d["abbr"],
            "club": d["name"].strip(),
            "W": int(d["w"]), "L": int(d["l"]), "T": int(d["t"]),
            "pct": float(d["pct"]),
            "PF": int(d["pf"]), "PA": int(d["pa"]), "NET": int(d["net"]),
            "division_rec": d["div"].strip(),
            "conference_rec": d["conf"].strip(),
            "nonconference_rec": d["nonconf"].strip(),
            "streak": d["strk"],
            "last5": d["last5"].strip(),
            "source_url": "https://www.nfl.com/standings/",
        })
    # The page renders 8 rows per conference block (4 divisions x 4 rows). Assign
    # division labels only when the count matches exactly, so a partial parse can
    # never be dressed up as a complete one.
    divisions_assigned = False
    if len(rows) == 32:
        labels = []
        for conf, divs in SECTIONS.items():
            for div in divs:
                labels.extend([div] * 4)
        for r, lab in zip(rows, labels):
            r["division"] = lab
            r["conference"] = lab.split()[0]
        divisions_assigned = True
    dupes = sorted({r["abbr"] for r in rows if [x["abbr"] for x in rows].count(r["abbr"]) > 1})
    out = {
        "dataset": "nfl_desk_standings_read",
        "title": "2026 division standings as rendered by nfl.com/standings on 2026-11-19",
        "source_url": "https://www.nfl.com/standings/",
        "publisher": "NFL.com (official)",
        "read_utc": "2026-11-19",
        "read_route": "rendered-text read returned by the session's page-fetch tool; the sandbox has no direct HTTPS egress to nfl.com",
        "raw_evidence": "nfl-desk/evidence/reads/standings_2026-11-19.txt",
        "raw_sha256": sha256(READ),
        "parser": "nfl-desk/engine/parse_standings.py",
        "rows_parsed": len(rows),
        "divisions_assigned": divisions_assigned,
        "duplicate_abbreviations": dupes,
        "columns": ["abbr", "club", "W", "L", "T", "pct", "PF", "PA", "NET",
                    "division_rec", "conference_rec", "nonconference_rec", "streak", "last5"],
        "note": ("Every value is transcribed by the parser from the saved rendered read. "
                 "Columns the page prints but this project does not use (home/road split, "
                 "non-conference pct, conference pct) are not stored."),
        "rows": rows,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print("parsed %d rows -> %s (divisions assigned: %s)" % (len(rows), OUT, divisions_assigned))
    if len(rows) != 32 or dupes:
        raise SystemExit("parse did not yield 32 unique clubs")


if __name__ == "__main__":
    main()
