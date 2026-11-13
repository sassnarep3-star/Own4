#!/usr/bin/env python3
"""Line-by-line team-stats verification — session arena/8e2de421-own4 (2026-11-13).

Re-fetches (transcribed below) the official NFL.com team-stat pages on 2026-11-13 and
compares them, value by value, with the repository's stored copies:

  A. Passing page   https://www.nfl.com/stats/team-stats/offense/passing/2026/reg/all
     fields: att, cmp, cmp_pct, yds_per_att, pass_yds, pass_td, int, rating
     vs nfl-lines/data/official/team_stats_offense_passing_2026.json (through Week 9)
  B. Scoring page   https://www.nfl.com/stats/team-stats/offense/scoring/2026/reg/all
     fields: rush_td (col 1), pass_td (col 2)
     vs nfl-edge/data/team_stats_2026.json (captured 2026-11-12, pre-Thursday)
  C. Official cross-check: scoring-page pass_td == passing-page pass_td (all 32)
  D. nfl-edge pts vs official standings PF (transcribed in compare_standings.py)

Expected drift: only WAS and NYG played between the repository captures and this
fetch (WAS 24 - NYG 21, Thursday 2026-11-12, https://www.nfl.com/scores/2026/REG10),
so exactly those two clubs may differ; every other club must match exactly.

Run:  python3 nfl-integration/scripts/compare_team_stats.py
Writes: nfl-integration/data/team_stats_comparison.json
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from compare_standings import LIVE as LIVE_STANDINGS  # noqa: E402  (official 2026-11-13)

ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "nfl-integration", "data", "team_stats_comparison.json")

PASSING_URL = "https://www.nfl.com/stats/team-stats/offense/passing/2026/reg/all"
SCORING_URL = "https://www.nfl.com/stats/team-stats/offense/scoring/2026/reg/all"
SCORES_URL = "https://www.nfl.com/scores/2026/REG10"
FETCHED = "2026-11-13"
DRIFT = {"WAS", "NYG"}  # Thursday game

# --- official transcription: passing page (chunk 0, all 32 rows, 2026-11-13) --------
# abbr: (att, cmp, cmp_pct, yds_per_att, pass_yds, pass_td, int, rating)
LIVE_PASS = {
    "AZ": (359, 232, 64.6, 5.8, 2080, 13, 7, 84),
    "LA": (349, 232, 66.5, 6.8, 2387, 16, 9, 90.5),
    "GB": (341, 215, 63, 7.7, 2618, 19, 6, 97.9),
    "DAL": (336, 218, 64.9, 7.1, 2381, 16, 5, 95.4),
    "LV": (324, 209, 64.5, 7.4, 2401, 20, 8, 97),
    "CAR": (313, 189, 60.4, 7.2, 2244, 16, 6, 91.3),
    "CHI": (312, 211, 67.6, 7.4, 2310, 10, 9, 88),
    "NO": (308, 204, 66.2, 6.4, 1986, 14, 6, 91.2),
    "IND": (304, 184, 60.5, 5.7, 1730, 6, 10, 69.1),
    "NYG": (304, 188, 61.8, 7.2, 2193, 13, 7, 88.3),
    "PHI": (303, 179, 59.1, 5.7, 1740, 10, 6, 78),
    "WAS": (299, 187, 62.5, 6.8, 2025, 15, 3, 95),
    "CIN": (296, 219, 74, 8.1, 2386, 23, 6, 114.8),
    "PIT": (290, 175, 60.3, 6.4, 1871, 13, 6, 85.6),
    "SEA": (288, 182, 63.2, 7.2, 2089, 15, 9, 89.3),
    "DEN": (287, 174, 60.6, 6, 1730, 11, 4, 84.7),
    "HOU": (285, 182, 63.9, 7.9, 2258, 16, 2, 104.1),
    "CLE": (283, 185, 65.4, 7.4, 2105, 9, 3, 93.7),
    "NE": (281, 183, 65.1, 8.4, 2349, 18, 11, 96.2),
    "DET": (274, 186, 67.9, 7.8, 2145, 15, 2, 106.5),
    "NYJ": (271, 183, 67.5, 7.7, 2078, 12, 3, 100.4),
    "KC": (263, 177, 67.3, 7.8, 2037, 14, 4, 101.8),
    "ATL": (256, 156, 60.9, 6.9, 1766, 11, 12, 76.4),
    "TEN": (248, 155, 62.5, 6, 1483, 6, 5, 78.8),
    "BAL": (247, 165, 66.8, 7.5, 1842, 10, 5, 93.9),
    "LAC": (243, 146, 60.1, 6.6, 1615, 7, 11, 70.6),
    "TB": (240, 146, 60.8, 5.9, 1423, 6, 9, 70.2),
    "BUF": (236, 156, 66.1, 8.6, 2027, 12, 6, 99.3),
    "SF": (236, 163, 69.1, 8.4, 1980, 17, 5, 109.8),
    "JAX": (227, 147, 64.8, 8.6, 1940, 18, 4, 110.8),
    "MIN": (225, 137, 60.9, 6.4, 1437, 8, 5, 82),
    "MIA": (209, 122, 58.4, 6.9, 1442, 6, 6, 77.1),
}
PASS_FIELDS = ["att", "cmp", "cmp_pct", "yds_per_att", "pass_yds",
               "pass_td", "int", "rating"]

# --- official transcription: scoring page (col1 = rush_td, col2 = pass_td) ---------
LIVE_RUSH_TD = {
    "SF": 12, "CHI": 17, "CIN": 5, "BUF": 17, "DEN": 9, "CLE": 6, "TB": 11,
    "AZ": 4, "LAC": 4, "KC": 10, "IND": 11, "WAS": 5, "DAL": 11, "MIA": 7,
    "PHI": 8, "ATL": 9, "NYG": 8, "JAX": 8, "NYJ": 5, "DET": 10, "GB": 6,
    "CAR": 7, "NE": 7, "LV": 5, "LA": 11, "BAL": 11, "NO": 7, "SEA": 7,
    "PIT": 4, "HOU": 6, "TEN": 8, "MIN": 3,
}
LIVE_PASS_TD_SCORING = {
    "SF": 17, "CHI": 10, "CIN": 23, "BUF": 12, "DEN": 11, "CLE": 9, "TB": 6,
    "AZ": 13, "LAC": 7, "KC": 14, "IND": 6, "WAS": 15, "DAL": 16, "MIA": 6,
    "PHI": 10, "ATL": 11, "NYG": 13, "JAX": 18, "NYJ": 12, "DET": 15, "GB": 19,
    "CAR": 16, "NE": 18, "LV": 20, "LA": 16, "BAL": 10, "NO": 14, "SEA": 15,
    "PIT": 13, "HOU": 16, "TEN": 6, "MIN": 8,
}


def load_nfl_lines_passing():
    p = os.path.join(ROOT, "nfl-lines/data/official/team_stats_offense_passing_2026.json")
    doc = json.load(open(p, encoding="utf-8"))
    cols = doc["columns"]
    out = {}
    for row in doc["rows"]:
        r = dict(zip(cols, row))
        out[r["nfl_abbr"]] = r
    return out


def load_nfl_edge_stats():
    p = os.path.join(ROOT, "nfl-edge/data/team_stats_2026.json")
    doc = json.load(open(p, encoding="utf-8"))
    return {r["team"]: r for r in doc["rows"]}


def cmp_field(results, label, got, want, abbr, field):
    if got == want:
        results["match"] += 1
    else:
        item = {"abbr": abbr, "field": field, "file": got, "official": want}
        if abbr in DRIFT:
            results["expected_drift"].append(item)
        else:
            results["mismatch"].append(item)


def main():
    report = {"fetched_utc": FETCHED,
              "sources": {"passing": PASSING_URL, "scoring": SCORING_URL,
                          "scores": SCORES_URL},
              "expected_drift_clubs": sorted(DRIFT)}

    # A. passing page vs nfl-lines
    lines = load_nfl_lines_passing()
    res = {"match": 0, "mismatch": [], "expected_drift": []}
    for abbr, vals in LIVE_PASS.items():
        row = lines.get(abbr)
        if row is None:
            res["mismatch"].append({"abbr": abbr, "field": "*",
                                    "file": None, "official": "present"})
            continue
        for i, f in enumerate(PASS_FIELDS):
            cmp_field(res, "passing", row[f], vals[i], abbr, f)
    report["nfl_lines_passing"] = {
        "file": "nfl-lines/data/official/team_stats_offense_passing_2026.json",
        "fields_compared": PASS_FIELDS,
        "values_compared": res["match"] + len(res["mismatch"])
                           + len(res["expected_drift"]),
        "exact_matches": res["match"],
        "mismatches": res["mismatch"],
        "expected_drift": res["expected_drift"],
        "verdict": "PASS" if not res["mismatch"] else "FAIL",
    }

    # B. scoring page vs nfl-edge (rush_td, pass_td) + C. internal official cross-check
    edge = load_nfl_edge_stats()
    res = {"match": 0, "mismatch": [], "expected_drift": []}
    for abbr in sorted(LIVE_PASS):
        row = edge.get(abbr)
        if row is None:
            res["mismatch"].append({"abbr": abbr, "field": "*",
                                    "file": None, "official": "present"})
            continue
        cmp_field(res, "rush_td", row["rush_td"], LIVE_RUSH_TD[abbr], abbr, "rush_td")
        cmp_field(res, "pass_td", row["pass_td"], LIVE_PASS_TD_SCORING[abbr],
                  abbr, "pass_td")
        # D. pts vs official standings PF
        cmp_field(res, "pts", row["pts"], LIVE_STANDINGS[abbr][3], abbr, "pts")
    report["nfl_edge_scoring_and_pts"] = {
        "file": "nfl-edge/data/team_stats_2026.json",
        "fields_compared": ["rush_td", "pass_td", "pts"],
        "values_compared": res["match"] + len(res["mismatch"])
                           + len(res["expected_drift"]),
        "exact_matches": res["match"],
        "mismatches": res["mismatch"],
        "expected_drift": res["expected_drift"],
        "verdict": "PASS" if not res["mismatch"] else "FAIL",
    }

    # C. official page vs official page
    x = [(a, LIVE_PASS[a][5], LIVE_PASS_TD_SCORING[a])
         for a in LIVE_PASS if LIVE_PASS[a][5] != LIVE_PASS_TD_SCORING[a]]
    report["official_cross_check_scoring_vs_passing_td"] = {
        "compared": 32, "mismatches": x,
        "verdict": "PASS" if not x else "FAIL",
    }

    # summary
    fails = [k for k, v in report.items()
             if isinstance(v, dict) and v.get("verdict") == "FAIL"]
    report["summary"] = {
        "checks_failed": len(fails),
        "failed_sections": fails,
        "verdict": "PASS" if not fails else "FAIL",
        "note": ("WAS/NYG differences are the documented Thursday-game drift "
                 "(repo captured pre-game 2026-11-12)."),
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1, sort_keys=True)
        f.write("\n")

    for key in ("nfl_lines_passing", "nfl_edge_scoring_and_pts",
                "official_cross_check_scoring_vs_passing_td"):
        s = report[key]
        print("%-46s %-4s exact=%s drift=%d mismatch=%d"
              % (key, s["verdict"], s.get("exact_matches", s.get("compared")),
                 len(s.get("expected_drift", [])), len(s["mismatches"])))
        for m in s["mismatches"][:10]:
            print("    MISMATCH", m)
        for d in s.get("expected_drift", [])[:6]:
            print("    drift   ", d)
    print("summary:", report["summary"]["verdict"])
    print("wrote", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
