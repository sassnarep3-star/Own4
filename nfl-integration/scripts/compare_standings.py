#!/usr/bin/env python3
"""Line-by-line standings verification — session arena/8e2de421-own4 (2026-11-13).

Compares every standings table stored in the repository's NFL namespaces against the
official NFL.com division standings page, re-fetched and transcribed line by line on
2026-11-13 (all 32 clubs, W/L/T/PF/PA).

Official source: https://www.nfl.com/standings/  (fetched 2026-11-13, 2 chunks)

Between the repository snapshots (2026-11-12, "before Week 10") and this fetch, exactly
one game was played: WAS 24 - NYG 21 (Thursday 2026-11-12), confirmed on
https://www.nfl.com/scores/2026/REG10 . The script therefore compares each file against
two reference states:
  * LIVE        — standings as displayed on 2026-11-13;
  * PRE-WEEK10  — live standings with WAS/NYG rolled back to their pre-Thursday values
                  (WAS 2-5-1, PF 172, PA 202; NYG 5-2-1, PF 182, PA 172).

A file that documents a capture "before Week 10" / "through Week 9" must match
PRE-WEEK10 exactly. A file documenting an older capture is reported with its drift and
is not judged against either reference (its own snapshot date governs).

Internal consistency is checked for every file regardless:
  * 32 clubs present, no duplicates;
  * sum of wins == sum of losses across the league (ties contribute to both);
  * sum of PF == sum of PA across the league.

Run:  python3 nfl-integration/scripts/compare_standings.py
Writes: nfl-integration/data/standings_comparison.json
"""

import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))          # repo root
OUT = os.path.join(ROOT, "nfl-integration", "data", "standings_comparison.json")

SOURCE = "https://www.nfl.com/standings/"
SCORES_SOURCE = "https://www.nfl.com/scores/2026/REG10"
FETCHED = "2026-11-13"

# --- official transcription (nfl.com/standings, fetched 2026-11-13, both chunks) ----
# abbr: (W, L, T, PF, PA)
LIVE = {
    "BUF": (7, 1, 0, 256, 187), "NE": (5, 4, 0, 211, 207), "NYJ": (2, 7, 0, 182, 223),
    "MIA": (1, 7, 0, 126, 200), "PIT": (6, 2, 0, 180, 144), "CIN": (6, 2, 0, 240, 175),
    "CLE": (5, 4, 0, 161, 196), "BAL": (4, 5, 0, 189, 236), "JAX": (6, 2, 0, 229, 121),
    "HOU": (3, 5, 0, 209, 192), "IND": (2, 7, 0, 184, 249), "TEN": (1, 7, 0, 144, 199),
    "DEN": (7, 2, 0, 198, 186), "KC": (6, 2, 0, 202, 143), "LV": (4, 5, 0, 238, 268),
    "LAC": (0, 8, 0, 121, 219), "NYG": (5, 3, 1, 203, 196), "DAL": (4, 5, 0, 246, 236),
    "WAS": (3, 5, 1, 196, 223), "PHI": (2, 7, 0, 148, 221), "CHI": (7, 2, 0, 241, 184),
    "DET": (6, 2, 0, 222, 189), "MIN": (6, 2, 0, 146, 116), "GB": (6, 3, 0, 216, 191),
    "CAR": (3, 5, 0, 199, 219), "NO": (3, 5, 0, 185, 216), "TB": (3, 6, 0, 202, 178),
    "ATL": (3, 6, 0, 188, 223), "SF": (7, 1, 0, 235, 156), "SEA": (5, 4, 0, 202, 162),
    "LA": (5, 4, 0, 214, 181), "AZ": (3, 6, 0, 178, 255),
}
# Thursday game rollback (WAS 24, NYG 21 — https://www.nfl.com/scores/2026/REG10)
PRE = dict(LIVE)
PRE["WAS"] = (2, 5, 1, 172, 202)
PRE["NYG"] = (5, 2, 1, 182, 172)

# --- files under verification -------------------------------------------------------
# (path, abbr-key source, expected reference, capture label from the file itself)
FILES = [
    ("nfl-audit/data/standings_2026-11-12.csv", "csv", "PRE",
     "captured 2026-11-12 (file name)"),
    ("nfl-edge/data/official_standings.json", "nfl-edge", "PRE",
     "captured_utc 2026-11-12 (file meta)"),
    ("nfl-hub/data/official/standings_2026.json", "nfl-hub", "PRE",
     "as_of 2026-11-12 (before Week 10) (file meta)"),
    ("nfl-intel/data/standings_2026-11-12.json", "nfl-intel", "PRE",
     "transcribed 2026-11-12 (file meta)"),
    ("nfl-lines/data/official/standings_2026.json", "nfl-lines", "PRE",
     "through Week 9 (file title)"),
    ("nfl-lab/data/standings_2026.csv", "csv", "OLDER",
     "older snapshot (file shows BUF 6-1-0; no capture date in file)"),
]


def load_rows(path, kind):
    """Return {abbr: (w,l,t,pf,pa)} for a supported file format."""
    full = os.path.join(ROOT, path)
    if kind == "csv":
        out = {}
        with open(full, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                ab = (r.get("abbr") or r.get("team") or "").strip()
                out[ab] = (int(r["w"]), int(r["l"]), int(r["t"]),
                           int(r["pf"]), int(r["pa"]))
        return out
    with open(full, encoding="utf-8") as f:
        doc = json.load(f)

    # Schema 1: columns + rows-as-ARRAYS (nfl-lines). nfl-edge also has
    # columns+rows but its rows are dicts — that falls through to Schema 2.
    if (isinstance(doc, dict) and "columns" in doc and "rows" in doc
            and doc["rows"] and isinstance(doc["rows"][0], list)):
        cols = doc["columns"]
        out = {}
        for row in doc["rows"]:
            r = dict(zip(cols, row))
            out[str(r["abbr"])] = (int(r["w"]), int(r["l"]), int(r["t"]),
                                   int(r["pf"]), int(r["pa"]))
        return out

    # Schema 2: list of team dicts under any container key (nfl-edge rows[],
    # nfl-hub teams[], nfl-intel teams[])
    out = {}

    def walk(node):
        if isinstance(node, dict):
            ab = node.get("abbr") or node.get("team_abbr") or node.get("key")
            if not ab and isinstance(node.get("team"), str):
                ab = node["team"]          # "BUF" style abbreviation
            w = node.get("w", node.get("wins"))
            l = node.get("l", node.get("losses"))
            t = node.get("t", node.get("ties"))
            pf = node.get("pf", node.get("points_for"))
            pa = node.get("pa", node.get("points_against"))
            if (isinstance(ab, str) and len(ab) <= 4
                    and None not in (w, l, t, pf, pa)):
                out[ab] = (int(w), int(l), int(t), int(pf), int(pa))
                return
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(doc)
    return out


def normalize_abbrs(rows):
    """Arizona's club appears as ARI (official team code) in some files and AZ
    (logo slug) in others; only the key differs, never the values. Canonicalise
    to AZ so the comparison judges numbers, not naming conventions."""
    if "ARI" in rows and "AZ" not in rows:
        rows = dict(rows)
        rows["AZ"] = rows.pop("ARI")
    return rows


def check_internal(rows):
    problems = []
    if len(rows) != 32:
        problems.append("club count %d != 32" % len(rows))
    w = sum(v[0] for v in rows.values())
    l = sum(v[1] for v in rows.values())
    t = sum(v[2] for v in rows.values())
    pf = sum(v[3] for v in rows.values())
    pa = sum(v[4] for v in rows.values())
    if w != l:
        problems.append("sum W %d != sum L %d" % (w, l))
    if pf != pa:
        problems.append("sum PF %d != sum PA %d" % (pf, pa))
    return {"clubs": len(rows), "sum_w": w, "sum_l": l, "sum_t": t,
            "sum_pf": pf, "sum_pa": pa, "problems": problems}


def compare(rows, ref):
    mismatches = []
    for ab in sorted(set(rows) | set(ref)):
        got, want = rows.get(ab), ref.get(ab)
        if got != want:
            mismatches.append({"abbr": ab, "file": list(got) if got else None,
                               "official": list(want) if want else None})
    return {"matches": 32 - len(mismatches), "mismatches": mismatches}


def main():
    results = []
    for path, kind, ref_name, capture in FILES:
        try:
            rows = normalize_abbrs(load_rows(path, kind))
        except Exception as exc:  # unreadable file is a finding, not a crash
            results.append({"path": path, "error": str(exc)})
            continue
        internal = check_internal(rows)
        ref = LIVE if ref_name == "LIVE" else PRE
        vs_ref = compare(rows, ref)
        vs_live = compare(rows, LIVE)
        entry = {
            "path": path,
            "capture_label": capture,
            "expected_reference": ref_name,
            "internal_consistency": internal,
            "vs_expected_reference": vs_ref,
            "vs_live_2026-11-13": vs_live,
            "verdict": None,
        }
        if internal["problems"]:
            entry["verdict"] = "INTERNAL-CONSISTENCY FAIL"
        elif ref_name == "PRE" and not vs_ref["mismatches"]:
            entry["verdict"] = "PASS (matches pre-Week-10 official exactly)"
        elif ref_name == "OLDER":
            entry["verdict"] = "OLDER SNAPSHOT (drift reported; not judged)"
        else:
            entry["verdict"] = "MISMATCH vs expected reference"
        results.append(entry)

    doc = {
        "generated_by": "nfl-integration/scripts/compare_standings.py",
        "fetched_utc": FETCHED,
        "official_source": SOURCE,
        "scores_source": SCORES_SOURCE,
        "note": ("Only WAS 24-NYG 21 (Thu 2026-11-12) was played between the "
                 "repository snapshots and this fetch; all other differences are "
                 "snapshot-date drift or defects."),
        "results": results,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, sort_keys=True)
        f.write("\n")

    # console summary
    print("standings comparison vs official (%s):" % SOURCE)
    for r in results:
        if "error" in r:
            print("  ERROR %s: %s" % (r["path"], r["error"]))
            continue
        v = r["vs_expected_reference"]
        print("  %-52s %-48s expected-match %2d/32  live-match %2d/32"
              % (r["path"], r["verdict"], v["matches"],
                 r["vs_live_2026-11-13"]["matches"]))
        for m in v["mismatches"]:
            print("      %s: file=%s official=%s"
                  % (m["abbr"], m["file"], m["official"]))
        for p in r["internal_consistency"]["problems"]:
            print("      internal: %s" % p)
    print("wrote %s" % os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
