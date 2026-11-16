#!/usr/bin/env python3
"""Machine-validation of the transcribed Week 10 availability capture.

This does NOT fetch anything: the fetch path available to this session returns a rendered reading
of a page, not its bytes, so a re-fetch here would silently disagree with the transcription
(wording, ordering, and live record fields all move). What this file does instead is verify the
structural claims the site makes about the capture:

  * every row carries all required fields;
  * a club's rows form a contiguous block, and every block has an opponent recorded;
  * the club blocks pair off into the fixtures listed in data/fixtures_week10.csv (away and home
    each publish a section) - which is what catches a club section dropped mid-transcription;
  * blanks are preserved as blanks (never 'None', 'Healthy', a carried-forward value);
  * the game-status and practice-status vocabularies contain nothing the official table can print;
  * a non-injury reason is counted as a non-injury, not as an injury.

Exit code 1 means the capture is not fit to publish.
"""
from __future__ import annotations

import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)

SNAP = os.path.join(NS, "data", "availability_snapshot_2026-11-15.csv")
FIX = os.path.join(NS, "data", "fixtures_week10.csv")

REQUIRED = ["team", "opp", "player", "pos", "injury", "practice_status", "game_status", "player_slug"]
GAME_STATUS_OK = {"", "Out", "Doubtful", "Questionable", "Probable"}
PRACTICE_OK = {"Full Participation in Practice", "Limited Participation in Practice",
               "Did Not Participate In Practice"}
BAD_BLANKS = {"none", "null", "n/a", "healthy", "no", "-"}


def main() -> int:
    problems: list[str] = []
    with open(SNAP, newline="", encoding="utf-8") as fh:
        rdr = csv.DictReader(fh)
        header = rdr.fieldnames or []
        rows = list(rdr)
        extra = rdr.restkey  # populated by csv.DictReader when a line has too many fields
        ragged = [i for i, r in enumerate(rows, 2) if r.get(extra)]

    for f in REQUIRED:
        if f not in header:
            problems.append(f"missing required column: {f}")
    if ragged:
        problems.append(f"rows with the wrong field count (line numbers): {ragged[:10]}")

    if not rows:
        problems.append("empty capture")
        print("\n".join(problems))
        return 1

    # required non-empty values
    for i, r in enumerate(rows, 2):
        for f in ("team", "opp", "player", "pos", "practice_status", "player_slug"):
            if not (r[f] or "").strip():
                problems.append(f"line {i}: required field '{f}' is blank for {r.get('team')} {r.get('player')}")
        gs = (r.get("game_status") or "").strip()
        if gs not in GAME_STATUS_OK:
            problems.append(f"line {i}: game_status outside the official vocabulary: {gs!r}")
        if r["practice_status"].strip() not in PRACTICE_OK:
            problems.append(f"line {i}: practice_status outside the official vocabulary: {r['practice_status']!r}")
        for f in ("injury", "game_status"):
            v = (r.get(f) or "").strip().lower()
            if v in BAD_BLANKS:
                problems.append(f"line {i}: '{r.get(f)}' is an inferred blank in column '{f}' - a blank must be published as blank")
        if len(r["player_slug"]) > 60 or " " in r["player_slug"]:
            problems.append(f"line {i}: player_slug looks malformed: {r['player_slug']!r}")

    # contiguous club blocks + fixture pairing
    order, seen = [], set()
    for r in rows:
        if r["team"] not in seen:
            seen.add(r["team"])
            order.append(r["team"])
        elif r["team"] != order[-1]:
            problems.append(f"club block not contiguous: {r['team']} appears after {order[-1]}")
    block_teams = order

    with open(FIX, newline="", encoding="utf-8") as fh:
        fixtures = list(csv.DictReader(fh))
    expected = set()
    for f in fixtures:
        expected.add(f["away"])
        expected.add(f["home"])
    missing_sections = sorted(expected - set(block_teams))
    extra_sections = sorted(set(block_teams) - expected)
    if missing_sections:
        problems.append(f"fixture clubs with no section in the capture: {missing_sections}")
    if extra_sections:
        problems.append(f"capture sections that match no fixture: {extra_sections}")
    if len(block_teams) % 2:
        problems.append(f"club sections ({len(block_teams)}) do not pair into fixtures")

    # per-fixture opponent agreement
    opp_of = {}
    for r in rows:
        opp_of.setdefault(r["team"], set()).add(r["opp"])
    for t, s in opp_of.items():
        if len(s) > 1:
            problems.append(f"{t} lists more than one opponent in the capture: {sorted(s)}")
    for f in fixtures:
        if opp_of.get(f["away"]) and opp_of[f["away"]] != {f["home"]}:
            problems.append(f"{f['away']} opponent in capture ({opp_of[f['away']]}) != fixture card ({f['home']})")
        if opp_of.get(f["home"]) and opp_of[f["home"]] != {f["away"]}:
            problems.append(f"{f['home']} opponent in capture ({opp_of[f['home']]}) != fixture card ({f['away']})")

    # duplicates: the official table lists a player once per club section
    counts = {}
    for r in rows:
        counts[(r["team"], r["player"])] = counts.get((r["team"], r["player"]), 0) + 1
    for k, v in counts.items():
        if v > 1:
            problems.append(f"duplicate row for {k[0]} {k[1]} x{v}")

    n = len(rows)
    designated = sum(1 for r in rows if (r["game_status"] or "").strip())
    non_injury = sum(1 for r in rows if "Not injury related" in (r["injury"] or ""))
    label: dict[str, int] = {}
    for r in rows:
        inj = (r["injury"] or "").strip()
        if inj:
            label[inj] = label.get(inj, 0) + 1

    summary = {
        "rows": n,
        "club_sections": len(block_teams),
        "fixtures": len(fixtures),
        "designation_rows": designated,
        "designation_coverage_pct": round(100 * designated / n, 1),
        "rows_with_injury_text": sum(1 for r in rows if (r["injury"] or "").strip()),
        "rows_with_non_injury_reason": non_injury,
        "distinct_injury_strings": len(label),
        "problems": problems,
        "verdict": "PASS" if not problems else "FAIL",
    }
    out = os.path.join(NS, "data", "derived", "capture_validation.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1)
        fh.write("\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "problems"}, indent=1))
    for p in problems[:30]:
        print("PROBLEM:", p)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
