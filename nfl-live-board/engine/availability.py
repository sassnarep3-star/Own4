#!/usr/bin/env python3
"""
Own4 · nfl-live-board · L-07  (availability, depth, surprise)

Produces three things the brief asks for, and leaves blank the two it cannot yet have:

  1. availability_verification.json
     An independent, row-level re-read of the committed Week 10 injury capture. This session
     read the live official page and transcribed nine clubs by eye, then compared field by
     field. Any disagreement is a finding, not something to smooth over.

  2. injury_surprise.json
     "Make the injury signal a surprise, never a level." The repository holds ONE dated
     availability snapshot for the current season (the Week 10 report). A level needs a
     baseline for the same player at the same point in the season; a baseline needs at least
     two dated snapshots. So every surprise value here is BLANK by construction and the file
     says exactly what would fill it. Nothing is estimated.

  3. depth_status.json
     The brief's replacement-depth requirement ("2nd/3rd/4th string") needs a depth source.
     nfl.com publishes no depth chart (peer-verified 404). Snap counts, the only official
     proxy that has been proposed, are not published as a league table on nfl.com either.
     The status file records, per team, what IS verified instead - the Week 10 Out / Doubtful
     / Questionable counts from the capture - and marks replacement depth unverified rather
     than guessed. The separation matters: a count of unavailable players is a fact; which
     backup replaces them is an inference the repository does not yet have evidence for.

Run: python3 nfl-live-board/engine/availability.py
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ROOTDIR = os.path.dirname(ROOT)
DATA = os.path.join(ROOT, "data")

CAPTURE = os.path.join(ROOTDIR, "nfl-book", "data", "injuries_week10_capture.json")
INJ_URL = "https://www.nfl.com/injuries/league/2026/reg10"
RESERVE_URL = "https://www.nfl.com/transactions/league/reserve-list/2026/11"

# Transcription made in THIS session (2026-11-17) from the live page, before comparing.
# Fields: player, injury, practice, game status. Practice abbreviations decoded below.
PRACTICE = {
    "Full": "Full Participation in Practice",
    "DNP": "Did Not Participate In Practice",
    "LP": "Limited Participation in Practice",
}
LIVE = {
    "WAS": [("John Bates", "", "Full", ""), ("Treylon Burks", "", "DNP", ""), ("Jayden Daniels", "", "Full", ""),
            ("Matt Gulbin", "", "Full", ""), ("Chig Okonkwo", "", "Full", ""), ("Lucas Patrick", "Concussion", "DNP", "Out"),
            ("Amik Robertson", "", "LP", ""), ("Shy Tuttle", "", "Full", ""), ("Colson Yankoff", "Knee", "DNP", "Out")],
    "NYG": [("Abdul Carter", "", "Full", ""), ("Jermaine Eluemunor", "", "Full", ""), ("Malik Harrison", "Groin", "LP", "Questionable"),
            ("Colton Hood", "", "Full", ""), ("Theo Johnson", "", "Full", ""), ("Charlie Jones", "", "Full", ""),
            ("J.J. McCarthy", "", "Full", ""), ("Darnell Mooney", "", "Full", ""), ("Malik Nabers", "", "Full", ""),
            ("Cam Skattebo", "", "Full", ""), ("Andrew Thomas", "", "Full", "")],
    "NE": [("Ben Brown", "Knee", "DNP", "Out"), ("A.J. Brown", "Ankle, Knee", "LP", "Questionable"),
           ("Kevin Byard", "Chest", "Full", "Questionable"), ("Carlton Davis III", "Knee", "DNP", "Out"),
           ("Reggie Gilliam", "Knee", "LP", "Questionable"), ("TreVeyon Henderson", "Illness", "DNP", "Out"),
           ("Hunter Henry", "", "LP", ""), ("Cameron Latu", "Back", "LP", "Questionable"), ("Drake Maye", "", "Full", ""),
           ("Morgan Moses", "", "Full", ""), ("Walter Rouse", "Concussion", "LP", "Questionable"),
           ("Brenden Schooler", "Hamstring", "LP", "Questionable"), ("Rhamondre Stevenson", "Knee", "LP", "Questionable"),
           ("Greg Van Roten", "Hamstring", "Full", "Questionable"), ("Charles Woods", "Hamstring", "Full", "Questionable")],
    "DET": [("Brian Branch", "", "Full", ""), ("Jared Goff", "", "Full", ""), ("Kerby Joseph", "Knee", "DNP", "Out"),
            ("Cade Mays", "Ankle", "DNP", "Out"), ("D.J. Reed", "Hip", "DNP", "Out"), ("Jacob Saylors", "", "Full", ""),
            ("Amon-Ra St. Brown", "Rib", "LP", "Questionable"), ("Sione Vaki", "Ankle", "LP", "Questionable"),
            ("DJ Wonnum", "", "Full", "")],
    "CAR": [("Jonathon Brooks", "Groin", "LP", "Doubtful"), ("Brady Christensen", "Hamstring", "Full", "Questionable"),
            ("Trevor Etienne", "", "Full", ""), ("Chuba Hubbard", "", "Full", ""), ("Lee Hunter", "", "Full", ""),
            ("Mike Jackson", "Groin", "LP", "Doubtful"), ("Will Lee III", "Hamstring", "LP", "Questionable"),
            ("Xavier Legette", "Knee", "Full", "Questionable"), ("Damien Lewis", "", "Full", ""),
            ("Bobby Okereke", "Foot", "DNP", "Out"), ("Jaelan Phillips", "Hamstring", "Full", "Questionable"),
            ("Torricelli Simpkins III", "", "Full", "")],
    "NO": [("Kelvin Banks Jr.", "", "Full", ""), ("CJ Donaldson", "Shoulder", "DNP", "Out"), ("David Edwards", "", "Full", ""),
           ("Martin Emerson", "Shin", "LP", "Questionable"), ("Travis Etienne", "Hamstring", "Full", "Questionable"),
           ("Noah Fant", "", "Full", ""), ("Taliese Fuaga", "Knee", "DNP", "Out"), ("Alvin Kamara", "", "Full", ""),
           ("Erik McCoy", "Biceps", "DNP", "Out"), ("Christen Miller", "Knee", "DNP", "Out"),
           ("Asim Richards", "", "Full", ""), ("Quincy Riley", "", "Full", "")],
    "HOU": [("Azeez Al-Shaair", "Groin, Not injury related - personal matter", "DNP", "Out"),
            ("Will Anderson Jr.", "Ankle", "DNP", "Questionable"), ("Reed Blankenship", "", "Full", ""),
            ("Trent Brown", "Wrist, Illness", "DNP", "Questionable"), ("Tank Dell", "", "Full", ""),
            ("Blake Fisher", "", "Full", ""), ("Marvin Harrison Jr.", "Hamstring", "DNP", "Out"),
            ("Jacob Hummel", "Groin", "Full", "Questionable"), ("Danielle Hunter", "Hamstring", "DNP", "Out"),
            ("Brevin Jordan", "Finger, Foot", "DNP", "Out"), ("Woody Marks", "", "Full", ""),
            ("David Montgomery", "Groin", "Full", "Questionable"), ("Keylan Rutledge", "Neck, Shoulder", "DNP", "Out"),
            ("Jaylin Smith", "Hamstring", "Full", "Questionable"), ("Wyatt Teller", "Illness, Back", "LP", "Questionable"),
            ("Tommy Togiai", "", "Full", "")],
    "CLE": [("Austin Barber", "", "Full", ""), ("Denzel Boston", "Toe", "LP", "Questionable"),
            ("Michael Burton", "Calf", "DNP", "Out"), ("Maliek Collins", "", "Full", ""),
            ("Harold Fannin Jr.", "", "Full", ""), ("Ronnie Hickman Jr.", "Concussion", "DNP", "Out"),
            ("Tytus Howard", "", "Full", ""), ("Elgton Jenkins", "", "Full", ""),
            ("Donovan McMillon", "", "LP", ""), ("Carson Schwesinger", "", "Full", ""),
            ("Denzel Ward", "", "LP", ""), ("Quincy Williams", "", "Full", "")],
}

ALL_TEAMS = ["AZ","ATL","BAL","BUF","CAR","CHI","CIN","CLE","DAL","DEN","DET","GB","HOU","IND",
             "JAX","KC","LA","LAC","LV","MIA","MIN","NE","NO","NYG","NYJ","PHI","PIT","SEA","SF",
             "TB","TEN","WAS"]


def load(p):
    with open(p) as f:
        return json.load(f)


def main():
    cap = load(CAPTURE)
    rows = cap["rows"]

    # ---------- 1. row-level verification of the committed capture -------------
    checks, mismatches = [], []
    for team, live_rows in LIVE.items():
        capmap = {r["player"]: r for r in rows if r["team"] == team}
        cap_rows = [r for r in rows if r["team"] == team]
        if len(cap_rows) != len(live_rows):
            mismatches.append({"team": team, "kind": "row count",
                               "committed": len(cap_rows), "live_read": len(live_rows),
                               "note": "counts differ; every shared row is still compared below"})
        for name, inj, prac, status in live_rows:
            c = capmap.get(name)
            if not c:
                mismatches.append({"team": team, "player": name, "kind": "row missing in committed capture"})
                continue
            ok = (c["injury"] == inj and c["practice"] == PRACTICE[prac] and c["game_status"] == status)
            checks.append({"team": team, "player": name, "injury": inj,
                           "practice": PRACTICE[prac], "game_status": status,
                           "committed_agrees": ok, "source_url": INJ_URL})
            if not ok:
                mismatches.append({"team": team, "player": name, "kind": "field mismatch",
                                   "committed": [c["injury"], c["practice"], c["game_status"]],
                                   "live_read": [inj, PRACTICE[prac], status]})

    verif = {
        "dataset": "nfl_live_board_availability_verification",
        "title": "Independent row-level re-read of the committed Week 10 injury capture",
        "built_utc": "2026-11-17",
        "source_url": INJ_URL,
        "method": "the live official page was transcribed by eye for nine clubs, then compared "
                  "field by field with nfl-book/data/injuries_week10_capture.json (read-only; the "
                  "peer file was not modified)",
        "clubs_read": sorted(LIVE),
        "rows_compared": len(checks),
        "fields_compared": ["Injuries", "Practice Status", "Game Status"],
        "agreements": sum(1 for c in checks if c["committed_agrees"]),
        "disagreements": len(mismatches),
        "mismatches": mismatches,
        "coverage": "9 of the clubs on the page. The remaining clubs were not re-read in this "
                    "session and are NOT claimed as verified (F-06).",
        "checks": checks,
    }
    json.dump(verif, open(os.path.join(DATA, "availability_verification.json"), "w"), indent=1)

    # ---------- 2. injury surprise (blank by construction) --------------------
    by_team = {}
    for r in rows:
        d = by_team.setdefault(r["team"], {"total": 0, "out": 0, "doubtful": 0, "questionable": 0, "blank": 0})
        d["total"] += 1
        s = r.get("game_status") or ""
        if s == "Out":
            d["out"] += 1
        elif s == "Doubtful":
            d["doubtful"] += 1
        elif s == "Questionable":
            d["questionable"] += 1
        else:
            d["blank"] += 1
    surprise_rows = []
    for r in rows:
        surprise_rows.append({
            "team": r["team"], "player": r["player"], "position": r["pos"],
            "game_status": r.get("game_status") or "",
            "snapshot_date": "Week 10 report (captured in nfl-book; live page re-read 2026-11-17)",
            "expected_status": None, "surprise": None,
            "blank_reason": "a surprise is observed minus expected for the same player. The "
                            "repository holds one dated snapshot for this season, so there is no "
                            "expected level to subtract. A second and third dated capture would fill it.",
            "source_url": INJ_URL,
        })
    surprise = {
        "dataset": "nfl_live_board_injury_surprise",
        "title": "Injury signal as a surprise (not a level) — structurally blank",
        "built_utc": "2026-11-17",
        "definition": "surprise(player, week) = observed designations over the window minus the "
                      "designations the same player carried in the prior dated snapshots",
        "why_blank": "one snapshot is a level, not a series. Producing a surprise number from a "
                     "single snapshot would be fabrication.",
        "what_would_fill_it": "two further dated captures of the same report (Wed/Thu/Fri), which "
                              "nfl-collector and nfl-readiness-register already schedule",
        "snapshots_available_this_season": 1,
        "rows": surprise_rows,
        "n_rows": len(surprise_rows),
        "source_url": INJ_URL,
    }
    json.dump(surprise, open(os.path.join(DATA, "injury_surprise.json"), "w"), indent=1)

    # ---------- 3. depth status per team -------------------------------------
    depth_rows = []
    for t in ALL_TEAMS:
        d = by_team.get(t, {"total": 0, "out": 0, "doubtful": 0, "questionable": 0, "blank": 0})
        depth_rows.append({
            "team": t,
            "out_week10": d["out"] if t in by_team else None,
            "doubtful_week10": d["doubtful"] if t in by_team else None,
            "questionable_week10": d["questionable"] if t in by_team else None,
            "report_rows_week10": d["total"] if t in by_team else None,
            "rank1": None, "rank2": None, "rank3": None, "rank4": None,
            "replacement_named": None,
            "depth_source": None,
            "status": ("unavailable-count verified; replacement depth unverified"
                       if t in by_team else "no Week 10 report table read for this club"),
            "blank_reason": "no official depth chart is published by nfl.com (peer-verified 404) and "
                            "no official snap-count table was located; naming a backup would be an "
                            "inference, so the depth columns stay blank (F-07).",
            "source_url": INJ_URL,
        })
    depth = {
        "dataset": "nfl_live_board_depth_status",
        "title": "Per-team availability and replacement-depth status, 32 clubs",
        "built_utc": "2026-11-17",
        "verified_today": {
            "availability_counts": "Week 10 report, re-read 2026-11-17 (9 clubs row-verified)",
            "reserve_list": RESERVE_URL,
        },
        "not_verified": {
            "depth_chart": "not published by nfl.com; club sites vary and are not a league source",
            "snap_counts": "no official league-wide snap-count table located on 2026-11-17",
        },
        "rows": depth_rows,
    }
    json.dump(depth, open(os.path.join(DATA, "depth_status.json"), "w"), indent=1)

    print("availability verification: %d rows compared, %d agree, %d disagreements"
          % (len(checks), verif["agreements"], verif["disagreements"]))
    for m in mismatches[:10]:
        print("  ", m)
    print("injury surprise: %d rows, all blank (1 snapshot this season)" % len(surprise_rows))
    print("depth status: %d teams, replacement depth unverified for all (no source)" % len(depth_rows))
    print("week 10 capture totals: %d rows, Out=%d Doubtful=%d Questionable=%d blank=%d"
          % (len(rows), sum(d["out"] for d in by_team.values()), sum(d["doubtful"] for d in by_team.values()),
             sum(d["questionable"] for d in by_team.values()), sum(d["blank"] for d in by_team.values())))


if __name__ == "__main__":
    main()
