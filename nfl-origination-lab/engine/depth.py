#!/usr/bin/env python3
"""
Availability and depth: what the stored official depth charts actually support,
measured rather than asserted, plus what they do not support at all.

INPUTS (stored, not fetched)
  nfl-depth-sweep/data/depth_register.json   32 clubs, 705 slots, 1,503 player entries,
                                             transcribed club by club from official
                                             club depth-chart pages on 2026-11-17
  nfl-depth-sweep/data/roster_ir_sweep.json  32-club sweep of the November 2026
                                             Reserve/Injured list against those charts
  data/availability_parse.json               this lab's own parse of the two stored
                                             Week 11 injury-report captures

FOUR MEASUREMENTS
  1. Slot shape. A depth slot is not always one player. The register stores a slot as
     {name} or {name, alt} or {name, jersey}. This build counts each shape instead of
     treating column 1 as "the starter" — the failure mode the brief names.
  2. Replacement depth. Where a reserve-listed player still sits on a chart, is there a
     documented replacement, and at what rank? "Depth of the replacement" is a rank
     difference, not a yes/no.
  3. Jersey-prefixed names. The Packers prepend jersey numbers. Count how many entries
     arrive with a jersey field, so the parser fix can be checked rather than assumed.
  4. Evidence gaps. Image-only charts, unstamped charts, and the absence of snap
     counts or inactive lists in the repository are counted and published, not filled.

WHAT THIS FILE REFUSES TO DO
  * infer a starter from jersey order, salary, experience or draft position
  * treat a rank-1 slot with two names as a named starter
  * call a chart "current" when it carries no capture timestamp
  * compute a "backup deficiency" feature: the brief's own gate requires one verified
    depth-order source for all 32 clubs first, and one club (Houston) publishes its
    chart only as an image, so the gate is unmet. The code that would build the
    feature is deliberately absent, and the unmet gate is printed instead.

Output: data/depth.json
"""

import json
import os
from collections import Counter, defaultdict

import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stable import dump

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
ROOT = os.path.dirname(LAB)

REGISTER = os.path.join(ROOT, "nfl-depth-sweep/data/depth_register.json")
SWEEP = os.path.join(ROOT, "nfl-depth-sweep/data/roster_ir_sweep.json")
INJ = os.path.join(LAB, "data/availability_parse.json")
OUT = os.path.join(LAB, "data/depth.json")


def slot_shape(slot):
    if slot is None:
        return "empty"
    if isinstance(slot, list):
        return "list"
    if not isinstance(slot, dict) or not slot.get("name"):
        return "empty"
    if slot.get("alt"):
        return "shared"
    if slot.get("jersey"):
        return "jersey_prefixed"
    return "single"


def main():
    reg = json.load(open(REGISTER, encoding="utf-8"))
    sweep = json.load(open(SWEEP, encoding="utf-8"))
    inj = json.load(open(INJ, encoding="utf-8"))

    shapes = Counter()
    shapes_by_club = defaultdict(Counter)
    slots = 0
    entries = 0
    shared_examples = []
    empty_examples = []
    jersey_clubs = Counter()
    unverified = []
    for c in reg["clubs"]:
        if c.get("status") != "verified_text":
            unverified.append({
                "club": c["club"], "status": c.get("status"),
                "source_url": c["source_url"],
                "why_blank": "the club publishes its chart in a format that was not "
                             "transcribable as text; no values are inferred from an image",
            })
            continue
        for p in c["positions"]:
            slots += 1
            for rank in ("rank1", "rank2", "rank3"):
                s = p.get(rank)
                sh = slot_shape(s)
                if sh in ("empty",):
                    if rank == "rank1":
                        empty_examples.append({"club": c["club"],
                                               "position": p["position"]})
                    continue
                shapes[sh] += 1
                shapes_by_club[c["club"]][sh] += 1
                entries += 1
                if sh == "shared":
                    shared_examples.append({"club": c["club"], "position": p["position"],
                                            "rank": rank, "names": [s["name"], s["alt"]],
                                            "source_url": c["source_url"]})
                if sh == "jersey_prefixed":
                    jersey_clubs[c["club"]] += 1

    # ---------- replacement depth from the reserve-list sweep ----------
    repl = []
    for club in sweep["clubs"]:
        for r in club.get("replacement_depth", []):
            chart = [x for x in club.get("chart_listings", [])
                     if x["player"] == r["for_player"]]
            listed_rank = chart[0]["rank"] if chart else None
            repl.append({
                "club": club["club"],
                "out": r["for_player"],
                "position": r["position"],
                "out_was_listed_at_rank": listed_rank,
                "replacement": r["replacement"],
                "replacement_at_rank": r["replacement_rank"],
                "depth_of_replacement": (None if listed_rank is None or
                                         r["replacement_rank"] is None
                                         else r["replacement_rank"] - listed_rank),
                "source_url": "https://www.nfl.com/transactions/league/reserve-list/2026/11",
                "reading": "depth_of_replacement counts how many ranks the club moved down "
                           "the same position to fill the slot; blank where the chart did "
                           "not list the player",
            })

    stale = [{"club": c["club"], "flags": c["stale_depth_flags"]}
             for c in sweep["clubs"] if c.get("stale_depth_flags")]

    # ---------- injury-report availability, quantified ----------
    b = inj["rows"]
    n_b = len(b)
    n_desig = sum(1 for r in b if r["game_status"])
    by_club = Counter(r["club"] for r in b)
    practice = Counter(r["practice"] for r in b)
    no_injury_clubs = sorted(set(by_club) ^ set(r["club"] for r in inj["rows_earlier_read"])) 
    tc = inj["transcription_control"]

    # the designation wording calendar: an Out on an early-week report on a
    # non-participant is the pattern the brief calls "surprise", not a level.
    surprise_pairs = []
    for r in inj["rows_earlier_read"]:
        for r2 in b:
            if r["club"] == r2["club"] and r["player"] == r2["player"]:
                if r["game_status"] != r2["game_status"] or r["practice"] != r2["practice"]:
                    surprise_pairs.append({
                        "club": r["club"], "player": r["player"],
                        "field": "game_status" if r["game_status"] != r2["game_status"] else "practice",
                        "earlier_2026-11-18": r["game_status"] or "(blank)",
                        "later_2026-11-19": r2["game_status"] or "(blank)",
                        "delta_note": "the earlier read is 7.3 hours earlier on the same "
                                      "report week; blank is not 'available'",
                    })
            if r["club"] == r2["club"] and r["player"] == r2["player"] and r["practice"] != r2["practice"]:
                pass
    d = ()
    payload = {
        "dataset": "nfl_origination_lab_depth",
        "title": "Depth and availability: what the stored official pages support, measured",
        "built": "2026-11-19",
        "sources": [
            {"path": os.path.relpath(REGISTER, ROOT),
             "title": "official club depth-chart register, 32 clubs, captured 2026-11-17"},
            {"path": os.path.relpath(SWEEP, ROOT),
             "title": "32-club Reserve/Injured sweep against those charts"},
            {"url": "https://www.nfl.com/transactions/league/reserve-list/2026/11",
             "title": "official November 2026 reserve list"},
            {"url": "https://www.nfl.com/injuries/",
             "title": "official Week 11 injury report (two dated captures)"},
        ],
        "slot_shape": {
            "definition": "how a single club/position/rank cell is populated on the stored "
                          "chart. 'shared' means the club named more than one player at that "
                          "rank, and no starter is chosen here.",
            "clubs_transcribed": len([c for c in reg["clubs"] if c.get("status") == "verified_text"]),
            "clubs_not_transcribed": len(unverified),
            "slots": slots,
            "player_entries": entries,
            "shape_counts": dict(shapes),
            "shared_slots": len(shared_examples),
            "empty_rank1_slots": len(empty_examples),
            "jersey_prefixed_entries": dict(jersey_clubs),
            "shared_examples": shared_examples[:40],
            "empty_examples": empty_examples,
            "not_transcribed": unverified,
            "finding": "a depth cell is a group, not a starter. Any feature that reads "
                       "column 1 as 'the starter' fabricates a starter on %d slots here."
                       % len(shared_examples),
        },
        "replacement_depth": {
            "n_replacements_documented": len(repl),
            "rows": repl,
            "finding": "the sweep documents %d replacements and %d of them have a rank for "
                       "the replacement. Depth of replacement is computed where both ranks "
                       "exist and left blank otherwise."
                       % (len(repl), sum(1 for r in repl if r["depth_of_replacement"] is not None)),
        },
        "stale_chart_flags": {
            "n_clubs_flagged": len(stale),
            "rows": stale,
        },
        "injury_report": {
            "rows_later_read": n_b,
            "rows_earlier_read": len(inj["rows_earlier_read"]),
            "rows_with_a_game_designation": n_desig,
            "pct_with_a_game_designation": round(100.0 * n_desig / n_b, 2),
            "clubs_with_rows": len(by_club),
            "practice_vocabulary": dict(practice),
            "transcription_control": {
                "joined": tc["joined_rows"],
                "fields_equal": tc["fields_equal"],
                "differences": len(tc["differences"]),
                "detail": tc["differences"],
            },
            "between_read_deltas": surprise_pairs,
            "no_designation_note": "on this report week only the Thursday fixture carries game "
                                   "designations; a Sunday club's blank cell is blank, not "
                                   "'available'. A feature built on designations has one "
                                   "game of coverage this week.",
        },
        "gaps": [
            {"id": "G1", "missing": "snap counts",
             "why_it_matters": "the brief asks for depth modelled from playing time, not "
                               "jersey order. No snap-count series exists in this repository "
                               "and this session could not read an official one.",
             "what_would_fill_it": "an official NFL snap-count publication, captured per week "
                                   "with a timestamp",
             "then_what": "re-fit the depth feature on snaps and report the difference "
                          "against the chart-based version, with uncertainty"},
            {"id": "G2", "missing": "inactive lists",
             "why_it_matters": "a backup replacing a starter cannot be confirmed from a "
                              "chart; the inactive list is the evidence",
             "what_would_fill_it": "the official inactive list per game, captured at kickoff",
             "then_what": "join it to the chart to convert 'suspected replacement' into "
                          "'confirmed replacement'"},
            {"id": "G3", "missing": "a depth-order source verified for all 32 clubs",
             "why_it_matters": "the brief's own precondition for building the "
                               "backup-deficiency feature",
             "what_would_fill_it": "a structured Houston chart (currently image-only), or an "
                                   "official snap-count source covering all clubs",
             "then_what": "the feature may be built; until then it must not be"},
            {"id": "G4", "missing": "a dated depth-chart series",
             "why_it_matters": "one capture per club cannot show turnover, and the brief calls "
                               "roster turnover a first-class event",
             "what_would_fill_it": "daily captures of the 32 club charts with retained hashes",
             "then_what": "diff consecutive captures and version each row against the last "
                          "official roster event"},
        ],
        "gate": {
            "name": "backup-deficiency feature",
            "status": "CLOSED",
            "why": "G3 is unmet: one club's chart is image-only, so no depth-order source is "
                   "verified for all 32 clubs. No deficiency feature is built, and no fixed "
                   "points penalty is substituted for one.",
        },
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        dump(payload, fh, indent=1)
        fh.write("\n")
    print("depth: %d clubs transcribed, %d slots, %d entries, shapes %s"
          % (payload["slot_shape"]["clubs_transcribed"], slots, entries, dict(shapes)))
    print("  shared slots %d, empty rank-1 %d, jersey-prefixed entries %s"
          % (len(shared_examples), len(empty_examples), dict(jersey_clubs)))
    print("  replacements documented %d, with a rank diff %d"
          % (len(repl), sum(1 for r in repl if r["depth_of_replacement"] is not None)))
    print("  injury rows %d, %d with a designation (%.2f%%), deltas between reads %d"
          % (n_b, n_desig, 100.0 * n_desig / n_b, len(surprise_pairs)))


if __name__ == "__main__":
    main()
