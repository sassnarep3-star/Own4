#!/usr/bin/env python3
"""
nfl-req-review — round-verdict generator (2026-11-17).

Loads the consolidated 73-row requirement register (nfl-consolidated/data/
requirements.json, built 2026-11-15) and writes this session's re-verified
register: nfl-req-review/data/requirements_2026_11_17.json.

Round verdicts are applied only where this session read the supporting official
source live (2026-11-17). Every row keeps its prior status, gate and clearing
number; the round adds the evidence read and, where the evidence changes the
status, the new status. Nothing is marked verified without an official read.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(os.path.dirname(HERE), "data")

SRC_STAND = "https://www.nfl.com/standings/league/2026/REG"
SRC_SCHED = "https://www.nfl.com/schedules/2026/by-week/week-11"
SRC_INJ = "https://www.nfl.com/injuries/league/2026/reg10"
SRC_INACT = "https://www.nfl.com/news/nfl-week-10-inactives-players-ruled-out-sunday-2026-season"
SRC_TRADES = "https://www.nfl.com/transactions/"
SRC_RESERVE = "https://www.nfl.com/transactions/league/reserve-list/2026/11"
SRC_GAME = "https://www.nfl.com/games/vikings-at-49ers-2026-reg-11"
SRC_DEPTH = "https://www.nfl.com/teams/baltimore-ravens/depth-chart"
SRC_ARCH = "https://www.nfl.com/injuries/league/2025/reg1"

# Per-ID round updates. status: unchanged | advanced | confirmed | done
UP = {
    "A03": dict(
        status="partial",
        evidence="Week-11 slate re-read line by line: all 14 fixtures carry a venue "
                 "transcribed from official pages (13 from the schedule page's own "
                 "stadium links; MIN@SF from the game centre Game Info: Estadio Banorte, "
                 "Mexico City). Roof/surface: no official field on the pages read — left "
                 "blank and flagged.",
        source=SRC_SCHED,
    ),
    "A04": dict(
        status="partial",
        evidence="Week-11 schedule announcement read live (14 fixtures, 6 byes, network "
                 "and kickoff times). The dated multi-week archive gap stands: this is a "
                 "point-in-time read, not a retained dated archive.",
        source=SRC_SCHED,
    ),
    "A05": dict(
        status="partial",
        evidence="Game-centre route re-verified live (Game Info section with Location/"
                 "Stadium; injury-report tabs not yet available for Week 11). The official "
                 "Game Book PDF route was verified 2026-11-16 by session arena/013190b4-own4. "
                 "Capture remains sample-based (1/14 Week-10 fixtures).",
        source=SRC_GAME,
    ),
    "E05": dict(
        status="partial",
        evidence="November 2026 transactions re-captured from the official hub: 12 trades "
                 "and 25 Reserve/Injured moves (16 clubs). The 32-club sweep with IR/reserve "
                 "reconciliation remains sample-based.",
        source=SRC_TRADES,
    ),
    "E06": dict(
        status="partial", change="blocked → partial",
        evidence="Official inactive lists now captured for Week 10: 147 entries across the "
                 "24 clubs of Sunday's 12 games (nfl.com news article, read live). Snap "
                 "counts exist only inside the official Game Book PDF (route verified); no "
                 "standalone official snap-count page exists on nfl.com. Snap-count capture "
                 "remains fixture-by-fixture.",
        source=SRC_INACT,
    ),
    "E11": dict(
        status="partial",
        evidence="This round adds a second dated read of the same Week-10 report "
                 "(2026-11-17), on top of the committed 2026-11-13 capture: a two-point "
                 "timestamped series with a measurable delta. A scheduled Wed/Thu/Fri "
                 "multi-day history is still not retained in-repo.",
        source=SRC_INJ,
    ),
    "E12": dict(
        status="partial",
        evidence="Delta computed and published: committed 2026-11-13 capture (326 rows; 14 "
                 "Out; 11 Questionable; 0 Doubtful) vs live 2026-11-17 read (346 rows; 70 "
                 "Out; 90 Questionable; 11 Doubtful). Both reads carry their clock dates.",
        source=SRC_INJ,
    ),
    "E13": dict(
        status="blocked",
        evidence="Re-confirmed 2026-11-17: nfl.com club depth-chart pages return 404 "
                 "(Baltimore checked live). Route (b) snap counts are available only via "
                 "the official Game Book PDF and give snaps/starters, not a depth rank. No "
                 "verified depth-order route for all 32 clubs.",
        source=SRC_DEPTH,
    ),
    "E14": dict(
        status="partial", change="not_started → partial",
        evidence="Designation reliability scored empirically for the final Week-10 report "
                 "joined to the official inactive list (24 Sunday clubs): Out did-not-play "
                 "58/64 = 90.6% (Wilson 95% CI 81.0–95.6); Doubtful 4/10 = 40.0% "
                 "(CI 16.8–68.7); Questionable 14/82 = 17.1% (CI 10.5–26.6). Six Out "
                 "designations are uncorroborated by either list and are flagged. Single-"
                 "week sample; the multi-season gate stands.",
        source=SRC_INACT,
    ),
    "E15": dict(
        status="partial",
        evidence="Two dated reads of the Week-10 report now exist (2026-11-13 committed, "
                 "2026-11-17 live) with a published delta. A daily Wed→kickoff series with "
                 "fetch timestamps is still not retained.",
        source=SRC_INJ,
    ),
    "E16": dict(
        status="partial", change="not_started → partial",
        evidence="Past-season weekly injury archive re-confirmed available on the official "
                 "site (2025 Season, Week 1 read live; week tabs 1–18 plus playoffs). The "
                 "multi-season archive is not yet built in-repo.",
        source=SRC_ARCH,
    ),
    "E17": dict(
        status="partial",
        evidence="November 2026 reserve list re-captured from the official page: 25 dated "
                 "Reserve/Injured moves, including Malik Willis (MIA, 11/10) — the case the "
                 "brief names. Systematic 32-club, multi-season capture remains partial.",
        source=SRC_RESERVE,
    ),
    "E21": dict(
        status="partial", change="not_started → partial",
        evidence="'Questionable' calibrated empirically instead of from old percentages: "
                 "of 82 Questionable designations in Sunday's 24 clubs, 14 did not play "
                 "(17.1%; Wilson 95% CI 10.5–26.6) and 68 played (82.9%). Official text "
                 "publishes no percentages; this is the project's measured single-week "
                 "rate. Multi-season calibration remains the gate.",
        source=SRC_INACT,
    ),
    "E23": dict(
        status="partial",
        evidence="Official transactions log re-captured (12 November trades, 25 reserve "
                 "moves) and available for the staleness join; depth rows themselves "
                 "remain third-party-sourced (E13 blocks the official join).",
        source=SRC_TRADES,
    ),
    "E25": dict(
        status="met", change="re-confirmed live 2026-11-17",
        evidence="Re-confirmed on the final report read live: Kerby Joseph (S, knee, DNP, "
                 "Out), Cade Mays (C, ankle, DNP, Out), D.J. Reed (CB, hip, DNP, Out).",
        source=SRC_INJ,
    ),
    "E26": dict(
        status="met", change="re-confirmed live 2026-11-17",
        evidence="Week-10 injury tables re-captured live 2026-11-17 at their final "
                 "designations (346 rows, 28 clubs, 14 fixtures). The earlier 2026-11-13 "
                 "capture was a Friday point-in-time snapshot; the delta is published.",
        source=SRC_INJ,
    ),
    "F04": dict(
        status="not_started",
        evidence="No official per-game onside-kick publication found on nfl.com pages read "
                 "this session; the official Game Book PDF is the only per-game kickoff "
                 "log identified. The regime-prior filter remains unbuilt.",
        source=SRC_GAME,
    ),
    "G12": dict(
        status="in_progress",
        evidence="This session's task R-08: PR from arena/ca159db5-own4 to main, merged "
                 "without waiting, GitHub Pages deploy confirmed, PR link and merge result "
                 "recorded in COORDINATION.md.",
        source="https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md",
    ),
}

prior = json.load(open(os.path.join(ROOT, "nfl-consolidated", "data", "requirements.json")))
rows = []
for r in prior["rows"]:
    rid = r["id"]
    u = UP.get(rid)
    rows.append({
        "id": rid,
        "group": r["group"],
        "requirement": r["requirement"],
        "status_2026_11_15": r["status"],
        "status": u["status"] if u else r["status"],
        "status_change": (u["status"] if u else r["status"]) != r["status"],
        "gate": r.get("gate", "—"),
        "clears": r.get("clears", "—"),
        "source": u["source"] if u else r.get("source", ""),
        "note": r.get("note", ""),
        "round_evidence": u["evidence"] if u else "",
        "implemented_by": r.get("implemented_by", ""),
    })

out = {
    "dataset": "nfl_req_review_requirements",
    "title": "Requirement register — re-verified 2026-11-17 (session arena/ca159db5-own4)",
    "built_utc": "2026-11-17",
    "base_register": "nfl-consolidated/data/requirements.json (built 2026-11-15, session arena/507da9a4-own4)",
    "statuses": {
        "met": "implemented and verified against an official source",
        "partial": "implemented, limited by a documented evidence gap (blank + flagged)",
        "blocked": "cannot be completed from official sources; published blank + flagged",
        "not_started": "no implementation exists",
        "in_progress": "under way this session",
    },
    "counts_2026_11_15": prior["counts"],
    "rows": rows,
}
from collections import Counter
out["counts_2026_11_17"] = dict(Counter(r["status"].split(": ")[0] for r in rows))
out["advanced_this_round"] = [r["id"] for r in rows if r["status_change"]]

with open(os.path.join(DATA, "requirements_2026_11_17.json"), "w") as f:
    json.dump(out, f, indent=1, ensure_ascii=False)

print("requirements_2026_11_17.json written —", len(rows), "rows")
print("counts:", out["counts_2026_11_17"])
print("advanced:", out["advanced_this_round"])
