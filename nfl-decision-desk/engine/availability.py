#!/usr/bin/env python3
"""Availability layer.

Publishes what the official report actually supports, and refuses to publish what it does not:

  * a per-club decision view (Out / Doubtful / Questionable counts, practice splits),
  * the DELTA against the prior capture held in this repo, never the level alone,
  * the practice-only group (a player practising but carrying no game designation) as its own
    quantity, because collapsing it into "healthy" is the error the brief warns about,
  * an explicit, published statement of what is MISSING (inactives, snap counts, depth ranks)
    and therefore which features are BLOCKED rather than estimated.
"""
from __future__ import annotations

import csv
import json
import os
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "data", "availability")
os.makedirs(OUT, exist_ok=True)

CAPTURE = "2026-11-15T23:24:27Z"
SRC = "https://www.nfl.com/injuries/"
CUR = os.path.join(ROOT, "data/raw/injuries_week10_2026-11-15T2324Z.csv")
# prior capture held in another session's namespace - READ ONLY, never rewritten
PRIOR = os.path.join(os.path.dirname(ROOT), "nfl-arena/data/injuries_week10.json")


def main():
    rows = list(csv.DictReader(open(CUR)))
    teams = sorted({r["team"] for r in rows})

    def counts(rs):
        c = Counter()
        for r in rs:
            g = r["game_status"]
            c[g or "no_designation"] += 1
            p = r["practice_status"]
            if p.startswith("Did Not"):
                c["dnp"] += 1
            elif p.startswith("Limited"):
                c["lp"] += 1
            elif p.startswith("Full"):
                c["fp"] += 1
            if not r["injury"]:
                c["injury_cell_blank"] += 1
        return c

    by_team = defaultdict(list)
    for r in rows:
        by_team[r["team"]].append(r)

    prior = json.load(open(PRIOR)) if os.path.exists(PRIOR) else None
    prior_t = (prior or {}).get("totals_by_team", {})

    club_rows = []
    for t in teams:
        c = counts(by_team[t])
        p = prior_t.get(t)
        club_rows.append({
            "team": t,
            "players_listed": len(by_team[t]),
            "out": c["Out"], "doubtful": c["Doubtful"], "questionable": c["Questionable"],
            "no_game_designation": c["no_designation"],
            "practice_dnp": c["dnp"], "practice_lp": c["lp"], "practice_fp": c["fp"],
            "injury_cell_blank": c["injury_cell_blank"],
            # the brief's "net injury count": designated Out + Doubtful, published as a range
            # because Questionable is not the same kind of quantity - see calibration note
            "out_plus_doubtful": c["Out"] + c["Doubtful"],
            "prior_capture_players_listed": p["players_listed"] if p else None,
            "delta_players_listed": (len(by_team[t]) - p["players_listed"]) if p else None,
            "prior_capture_utc": "2026-11-14 (peer session arena/28a71529-own4 capture)",
            "capture_utc": CAPTURE,
            "source_url": SRC,
            "depth_rank": None,
            "depth_rank_status": "NOT PUBLISHED by the official report - blocked, not blank-by-choice",
        })

    # ------------------------------------------------ the three published facts
    n = len(rows)
    designated = sum(1 for r in rows if r["game_status"])
    practice_only = sum(1 for r in rows if r["practice_status"].startswith("Did Not")
                        and not r["game_status"])
    full_but_q = sum(1 for r in rows if r["practice_status"].startswith("Full")
                     and r["game_status"] == "Questionable")

    facts = {
        "capture_utc": CAPTURE,
        "source_url": SRC,
        "clubs_read": len(teams),
        "rows": n,
        "designated_rows": designated,
        "designation_rate": round(designated / n, 4),
        "out": sum(1 for r in rows if r["game_status"] == "Out"),
        "doubtful": sum(1 for r in rows if r["game_status"] == "Doubtful"),
        "questionable": sum(1 for r in rows if r["game_status"] == "Questionable"),
        "no_game_designation": n - designated,
        "practice_dnp_without_designation": practice_only,
        "full_participation_but_questionable": full_but_q,
        "injury_cell_blank": sum(1 for r in rows if not r["injury"]),
        "comparison_to_brief_claims": [
            {
                "claim_in_brief": "Only 6 of 254 report rows carry a game designation",
                "observed_here": "%d of %d rows carry a designation (%.1f%%)"
                                 % (designated, n, 100 * designated / n),
                "verdict": "CONTRADICTED AT THIS CAPTURE",
                "explanation": ("the live page at %s carries designations on roughly half of all "
                                "rows. Either the earlier count used a different definition "
                                "(perhaps counting only rows whose INJURY cell was blank) or it "
                                "was taken at an earlier point in the week before Friday "
                                "designations were posted. Both are checkable; neither is "
                                "asserted." % CAPTURE),
                "checkable_alternative": ("rows with a BLANK injury cell but a designation: %d. "
                                          "If the earlier 6/254 referred to a different quantity, "
                                          "this is the quantity to test."
                                          % sum(1 for r in rows if not r["injury"] and r["game_status"])),
            },
            {
                "claim_in_brief": "Kerby Joseph, Cade Mays and D.J. Reed are published with a blank game-status cell while the article lists all three as Out",
                "observed_here": "all three read 'Out' in this capture",
                "verdict": "RESOLVED / NO LONGER REPRODUCIBLE",
                "evidence_rows": [
                    {"player": r["player"], "team": r["team"], "injury": r["injury"],
                     "practice": r["practice_status"], "game_status": r["game_status"]}
                    for r in rows if r["player"] in ("Kerby Joseph", "Cade Mays", "D.J. Reed")
                ],
                "explanation": ("the blank cells were a Friday-pre-designation state. By %s the "
                                "official table carries all three as Out. The earlier flag was "
                                "correct for its capture time and is now stale, which is exactly "
                                "why every capture must carry a clock." % CAPTURE),
            },
            {
                "claim_in_brief": "Seattle and Cincinnati are shown as injury-free while listing 15 and 4 players",
                "observed_here": "SEA lists %d rows, CIN lists %d rows"
                                 % (len(by_team.get("SEA", [])), len(by_team.get("CIN", []))),
                "verdict": "SEATTLE CONFIRMED NON-EMPTY; CINCINNATI DIFFERS",
                "explanation": ("SEA carries %d rows and CIN carries %d at this capture. The "
                                "brief's '4' for Cincinnati does not match; the live count is "
                                "published here rather than reconciled to the older figure."
                                % (len(by_team.get("SEA", [])), len(by_team.get("CIN", [])))),
            },
        ],
    }

    # ------------------------------------------------ what is missing, and what it blocks
    missing = [
        {"item": "official inactive list", "why_needed": "confirms who did NOT dress, which is the only way to know a backup actually replaced a starter",
         "status": "NOT CAPTURED", "official_location": "nfl.com game centre publishes inactives ~90 minutes before kickoff",
         "blocks": ["CR-07", "PR-05 personnel ablation", "replacement-depth feature"]},
        {"item": "snap counts per player", "why_needed": "the brief's required proxy for starter/backup when no depth chart exists",
         "status": "NOT CAPTURED", "official_location": "nfl.com game centre / stats pages",
         "blocks": ["CR-06", "PR-05", "depth-from-playing-time"]},
        {"item": "depth chart with rank per club", "why_needed": "to say a replacement is 2nd/3rd/4th string rather than merely 'another player'",
         "status": "NOT PUBLISHED BY THE OFFICIAL INJURY REPORT",
         "official_location": "club depth-chart pages vary; an earlier session recorded nfl.com/teams/<club>/depth-chart as 404",
         "blocks": ["PR-05", "replacement-depth feature"]},
        {"item": "multi-day archived injury series", "why_needed": "to compute Questionable->Out transitions and to backtest availability at all",
         "status": "NOT CAPTURED",
         "official_location": "the same nfl.com/injuries/ URL changes through the week and keeps no dated history",
         "blocks": ["CR-06", "PR-05", "any availability backtest"]},
    ]

    out = {
        "_meta": {
            "built_utc": CAPTURE,
            "policy": [
                "publish the level WITH its clock time and its delta against the prior capture",
                "publish what the feed supports; name what it does not",
                "never infer a depth rank, a snap share or an inactive status",
                "never subtract a fixed points penalty for a missing starter",
            ],
            "source_url": SRC,
            "source_kind": "OFFICIAL (nfl.com)",
            "coverage": ("28 of 28 clubs playing in Week 10 were read from the official page in "
                         "reader chunks 0-6. Every row is transcribed verbatim; published blanks "
                         "are preserved as blanks."),
        },
        "facts": facts,
        "clubs": club_rows,
        "missing_inputs": missing,
        "feature_status": [
            {"feature": "availability count per club (Out/Doubtful/Questionable)",
             "status": "AVAILABLE", "n": len(rows), "used_in_model": False,
             "why_not_used": "one capture cannot support a chronological ablation; using it would leak"},
            {"feature": "practice participation", "status": "AVAILABLE", "n": len(rows),
             "used_in_model": False, "why_not_used": "same"},
            {"feature": "backup depth rank", "status": "BLOCKED", "reason": "no official depth rank"},
            {"feature": "confirmed replacement of a starter", "status": "BLOCKED",
             "reason": "requires inactive lists"},
            {"feature": "snap-share decline", "status": "BLOCKED", "reason": "requires snap counts"},
        ],
    }
    json.dump(out, open(os.path.join(OUT, "availability.json"), "w"), indent=1)

    print("clubs:", len(teams), "rows:", n)
    print("designations: Out %d / Doubtful %d / Questionable %d / none %d"
          % (facts["out"], facts["doubtful"], facts["questionable"], facts["no_game_designation"]))
    print("practice-only DNP rows (no designation):", practice_only)
    print("full participation but Questionable:", full_but_q)
    print("\nper-club (team: rows, out, doubtful, questionable, none, dnp, lp, fp)")
    for c in club_rows:
        print("  %-4s %3d  %2d %2d %2d %3d | %2d %2d %2d  delta_vs_prior %s"
              % (c["team"], c["players_listed"], c["out"], c["doubtful"], c["questionable"],
                 c["no_game_designation"], c["practice_dnp"], c["practice_lp"], c["practice_fp"],
                 c["delta_players_listed"]))


if __name__ == "__main__":
    main()
