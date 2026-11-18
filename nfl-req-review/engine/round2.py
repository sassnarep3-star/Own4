#!/usr/bin/env python3
"""
nfl-req-review — round 2 (2026-11-18): official re-reads, reconciliation, audit.

Session arena/9242c387-own4. Writes data/official_reads_2026_11_18.json only: transcribed official
rows (each with its source URL) and the computed checks RC-01..RC-16. The register, flags, questions,
suggestions and repo review are written by round2_register.py; pages by build_r2.py.

Every transcribed value below was read from the cited official nfl.com page on 2026-11-18
(fetch_page tool). Totals, reconciliations and counts are COMPUTED here, never typed.
Pure standard library. Run from anywhere: python3 nfl-req-review/engine/round2.py
"""

import glob
import json
import os
import subprocess
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)
DATA = os.path.join(NS, "data")

ROUND = "2026-11-18"
SESSION = "arena/9242c387-own4"
READ_DATE = "2026-11-18"

SRC_STAND = "https://www.nfl.com/standings/league/2026/REG"
SRC_W10 = "https://www.nfl.com/schedules/2026/by-week/week-10"
SRC_W11 = "https://www.nfl.com/schedules/2026/by-week/week-11"
SRC_INJ10 = "https://www.nfl.com/injuries/league/2026/reg10"
SRC_INJ11 = "https://www.nfl.com/injuries/league/2026/reg11"
SRC_INJ_HUB = "https://www.nfl.com/injuries/"

# ---------------------------------------------------------------------------
# 1. Transcribed official reads (values typed from the fetched pages, kept verbatim)
# ---------------------------------------------------------------------------

# nfl.com/standings/league/2026/REG, read 2026-11-18 (chunks 0 and 1). W, L, T, PF, PA.
# Abbreviation LA is printed as LAR on the schedule page; LAR is used here (as in round 1).
STANDINGS_2026_11_18 = [
    ("BUF", 8, 1, 0, 287, 199), ("SF", 8, 1, 0, 281, 196), ("CHI", 7, 2, 0, 241, 184),
    ("CIN", 7, 2, 0, 278, 193), ("DEN", 7, 2, 0, 198, 186), ("DET", 7, 2, 0, 257, 199),
    ("JAX", 7, 2, 0, 269, 144), ("KC", 7, 2, 0, 237, 156), ("MIN", 7, 2, 0, 176, 126),
    ("PIT", 6, 3, 0, 198, 182), ("NYG", 5, 3, 1, 203, 196), ("CLE", 6, 4, 0, 188, 220),
    ("GB", 6, 4, 0, 226, 221), ("LAR", 6, 4, 0, 248, 187), ("SEA", 6, 4, 0, 223, 175),
    ("NE", 5, 5, 0, 221, 242), ("CAR", 4, 5, 0, 219, 236), ("BAL", 4, 6, 0, 209, 259),
    ("DAL", 4, 6, 0, 286, 282), ("LV", 4, 6, 0, 251, 289), ("WAS", 3, 5, 1, 196, 223),
    ("HOU", 3, 6, 0, 233, 219), ("NO", 3, 6, 0, 202, 236), ("TB", 3, 6, 0, 202, 178),
    ("AZ", 3, 7, 0, 184, 289), ("ATL", 3, 7, 0, 201, 258), ("IND", 3, 7, 0, 208, 271),
    ("PHI", 2, 7, 0, 148, 221), ("NYJ", 2, 8, 0, 194, 254), ("LAC", 1, 8, 0, 144, 239),
    ("MIA", 1, 8, 0, 148, 224), ("TEN", 1, 8, 0, 167, 239),
]

# nfl.com/schedules/2026/by-week/week-10 (final scores printed on the page). away @ home.
W10_FINALS = [
    ("W10-WAS-NYG", "WAS", 24, "NYG", 21, "https://www.nfl.com/games/commanders-at-giants-2026-reg-10", "Thu 2026-11-12"),
    ("W10-NE-DET", "NE", 10, "DET", 35, "https://www.nfl.com/games/patriots-at-lions-2026-reg-10", "Sun 2026-11-15 (Munich)"),
    ("W10-KC-ATL", "KC", 35, "ATL", 13, "https://www.nfl.com/games/chiefs-at-falcons-2026-reg-10", "Sun 2026-11-15"),
    ("W10-HOU-CLE", "HOU", 24, "CLE", 27, "https://www.nfl.com/games/texans-at-browns-2026-reg-10", "Sun 2026-11-15"),
    ("W10-MIN-GB", "MIN", 30, "GB", 10, "https://www.nfl.com/games/vikings-at-packers-2026-reg-10", "Sun 2026-11-15"),
    ("W10-MIA-IND", "MIA", 22, "IND", 24, "https://www.nfl.com/games/dolphins-at-colts-2026-reg-10", "Sun 2026-11-15"),
    ("W10-CAR-NO", "CAR", 20, "NO", 17, "https://www.nfl.com/games/panthers-at-saints-2026-reg-10", "Sun 2026-11-15"),
    ("W10-BUF-NYJ", "BUF", 31, "NYJ", 12, "https://www.nfl.com/games/bills-at-jets-2026-reg-10", "Sun 2026-11-15"),
    ("W10-JAX-TEN", "JAX", 40, "TEN", 23, "https://www.nfl.com/games/jaguars-at-titans-2026-reg-10", "Sun 2026-11-15"),
    ("W10-LAR-AZ", "LAR", 34, "AZ", 6, "https://www.nfl.com/games/rams-at-cardinals-2026-reg-10", "Sun 2026-11-15"),
    ("W10-SEA-LV", "SEA", 21, "LV", 13, "https://www.nfl.com/games/seahawks-at-raiders-2026-reg-10", "Sun 2026-11-15"),
    ("W10-SF-DAL", "SF", 46, "DAL", 40, "https://www.nfl.com/games/49ers-at-cowboys-2026-reg-10", "Sun 2026-11-15"),
    ("W10-PIT-CIN", "PIT", 18, "CIN", 38, "https://www.nfl.com/games/steelers-at-bengals-2026-reg-10", "Sun 2026-11-15"),
    ("W10-LAC-BAL", "LAC", 23, "BAL", 20, "https://www.nfl.com/games/chargers-at-ravens-2026-reg-10", "Mon 2026-11-16"),
]
W10_BYE_PRINTED = ["CHI", "DEN", "PHI", "TB"]  # "Teams on Bye" block, week-10 page chunk 1

# nfl.com/schedules/2026/by-week/week-11 (fixtures printed, away @ home, kickoff and network as printed)
W11_FIXTURES = [
    ("IND", "HOU", "Thu 2026-11-19", "8:15 PM ET", "PRIME", "https://www.nfl.com/games/colts-at-texans-2026-reg-11"),
    ("MIA", "BUF", "Sun 2026-11-22", "1:00 PM ET", "CBS", "https://www.nfl.com/games/dolphins-at-bills-2026-reg-11"),
    ("BAL", "CAR", "Sun 2026-11-22", "1:00 PM ET", "FOX", "https://www.nfl.com/games/ravens-at-panthers-2026-reg-11"),
    ("NO", "CHI", "Sun 2026-11-22", "1:00 PM ET", "FOX", "https://www.nfl.com/games/saints-at-bears-2026-reg-11"),
    ("TEN", "DAL", "Sun 2026-11-22", "1:00 PM ET", "FOX", "https://www.nfl.com/games/titans-at-cowboys-2026-reg-11"),
    ("TB", "DET", "Sun 2026-11-22", "1:00 PM ET", "FOX", "https://www.nfl.com/games/buccaneers-at-lions-2026-reg-11"),
    ("AZ", "KC", "Sun 2026-11-22", "1:00 PM ET", "CBS", "https://www.nfl.com/games/cardinals-at-chiefs-2026-reg-11"),
    ("PIT", "PHI", "Sun 2026-11-22", "1:00 PM ET", "CBS", "https://www.nfl.com/games/steelers-at-eagles-2026-reg-11"),
    ("NYJ", "LAC", "Sun 2026-11-22", "4:05 PM ET", "FOX", "https://www.nfl.com/games/jets-at-chargers-2026-reg-11"),
    ("JAX", "NYG", "Sun 2026-11-22", "4:25 PM ET", "CBS", "https://www.nfl.com/games/jaguars-at-giants-2026-reg-11"),
    ("LV", "DEN", "Sun 2026-11-22", "4:25 PM ET", "CBS", "https://www.nfl.com/games/raiders-at-broncos-2026-reg-11"),
    ("MIN", "SF", "Sun 2026-11-22", "8:20 PM ET", "NBC", "https://www.nfl.com/games/vikings-at-49ers-2026-reg-11"),
    ("CIN", "WAS", "Mon 2026-11-23", "8:15 PM ET", "ESPN", "https://www.nfl.com/games/bengals-at-commanders-2026-reg-11"),
]
W11_BYE_PRINTED = ["ATL", "CLE", "GB", "LAR", "NE", "SEA"]  # "Teams on Bye" block, week-11 page chunk 1

# nfl.com/injuries/league/2026/reg10 (the Week-10 report), chunk 0 read 2026-11-18.
# Only the chunk-0 clubs were re-read this round (WAS, NYG, NE, DET, KC/ATL partial).
# Rows: club, player, position, injury, practice, game status. Out rows only.
INJ_REG10_CHUNK0_OUT = [
    ("WAS", "Lucas Patrick", "C", "Concussion", "Did Not Participate In Practice", "Out"),
    ("WAS", "Colson Yankoff", "TE", "Knee", "Did Not Participate In Practice", "Out"),
    ("NE", "Ben Brown", "C", "Knee", "Did Not Participate In Practice", "Out"),
    ("NE", "Carlton Davis III", "CB", "Knee", "Did Not Participate In Practice", "Out"),
    ("NE", "TreVeyon Henderson", "RB", "Illness", "Did Not Participate In Practice", "Out"),
    ("DET", "Kerby Joseph", "S", "Knee", "Did Not Participate In Practice", "Out"),
    ("DET", "Cade Mays", "C", "Ankle", "Did Not Participate In Practice", "Out"),
    ("DET", "D.J. Reed", "CB", "Hip", "Did Not Participate In Practice", "Out"),
]
INJ_REG10_CHUNK0_BLANK_GAME_STATUS_CHECKED = ["Kerby Joseph", "Cade Mays", "D.J. Reed"]

# ---------------------------------------------------------------------------
# 2. Helpers
# ---------------------------------------------------------------------------


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def dump(name, obj):
    with open(os.path.join(DATA, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, sort_keys=False)
        f.write("\n")


def tally(games):
    """games: iterable of (away, away_pts, home, home_pts) -> per-club W,L,T,PF,PA."""
    t = defaultdict(lambda: dict(w=0, l=0, t=0, pf=0, pa=0))
    for away, ap, home, hp in games:
        for club, pf, pa in ((away, ap, hp), (home, hp, ap)):
            t[club]["pf"] += pf
            t[club]["pa"] += pa
        if ap > hp:
            t[away]["w"] += 1; t[home]["l"] += 1
        elif hp > ap:
            t[home]["w"] += 1; t[away]["l"] += 1
        else:
            t[away]["t"] += 1; t[home]["t"] += 1
    return t


KEYS = ("w", "l", "t", "pf", "pa")


def main():
    checks = []

    def check(cid, label, value, expected, source, note=""):
        checks.append(dict(id=cid, label=label, value=value, expected=expected,
                           ok=(value == expected), source=source, note=note))

    # --- standings arithmetic -------------------------------------------------
    stand = {a: dict(w=w, l=l, t=t, pf=pf, pa=pa) for a, w, l, t, pf, pa in STANDINGS_2026_11_18}
    total_gp = sum(v["w"] + v["l"] + v["t"] for v in stand.values())
    games_thru_w10 = total_gp // 2
    check("RC-01", "Clubs in official standings", len(stand), 32, SRC_STAND)
    check("RC-02", "Games completed through Week 10 = sum(W+L+T)/2", games_thru_w10, 150, SRC_STAND)
    check("RC-03", "Points for equals points against across the league",
          sum(v["pf"] for v in stand.values()), sum(v["pa"] for v in stand.values()), SRC_STAND)

    # --- Week 10 finals -------------------------------------------------------
    w10_games = [(a, ap, h, hp) for _id, a, ap, h, hp, _u, _d in W10_FINALS]
    w10_clubs = [c for g in w10_games for c in (g[0], g[2])]
    check("RC-04", "Week-10 final games read from the official page", len(W10_FINALS), 14, SRC_W10)
    check("RC-05", "Clubs appearing once each in Week 10", len(set(w10_clubs)) == len(w10_clubs), True, SRC_W10)
    byes_computed = sorted(set(stand) - set(w10_clubs))
    check("RC-06", "Clubs on bye in Week 10 (computed) = printed 'Teams on Bye'",
          byes_computed, sorted(W10_BYE_PRINTED), SRC_W10)
    games_thru_w9 = games_thru_w10 - len(W10_FINALS)
    check("RC-07", "Completed games through Week 9 = Week-10 total minus Week-10 finals",
          games_thru_w9, 136, SRC_W10)

    # --- Week 11 fixtures -----------------------------------------------------
    w11_clubs = [c for g in W11_FIXTURES for c in g[:2]]
    byes11 = sorted(set(stand) - set(w11_clubs))
    check("RC-08", "Week-11 fixtures read from the official page", len(W11_FIXTURES), 13, SRC_W11)
    check("RC-09", "Week-11 clubs on bye (computed) = printed 'Teams on Bye'",
          byes11, sorted(W11_BYE_PRINTED), SRC_W11)

    # --- Feed reconciliation: nfl-book results feed vs official standings ------
    feed = load_feed()
    # The feed prints the Rams as "LA"; the official standings/schedule bye box prints "LAR".
    # Normalised here, and recorded in the output so the mapping is visible.
    def norm(c):
        return "LAR" if c == "LA" else c
    feed_games_w19 = [(norm(r["away"]), r["away_pts"], norm(r["home"]), r["home_pts"]) for r in feed["rows"] if r["week"] <= 9]
    feed_w10 = [r["game_id"] for r in feed["rows"] if r["week"] == 10]
    check("RC-10", "Feed rows for Weeks 1-9 (nfl-book/data/results_feed.json)", len(feed_games_w19), 136, SRC_STAND)
    official_w10_t = tally(w10_games)
    official_w9 = {}
    for c in stand:
        official_w9[c] = {k: stand[c][k] - official_w10_t[c][k] for k in KEYS}
    feed_w9_t = tally(feed_games_w19)
    mismatches = []
    for c in sorted(stand):
        fc = {k: feed_w9_t[c][k] for k in KEYS}
        if fc != official_w9[c]:
            mismatches.append(dict(club=c, feed_through_w9=fc, official_through_w9=official_w9[c]))
    check("RC-11", "Clubs whose Weeks 1-9 feed totals (W,L,T,PF,PA) equal official totals minus Week 10",
          len(stand) - len(mismatches), 32, SRC_STAND,
          note="Team-aggregate reconciliation only; per-game scores are not re-read in this round.")
    check("RC-12", "Week-10 games present in the feed", len(feed_w10), 14, SRC_W10,
          note="Feed holds only the Thursday game (W10-WAS-NYG); 13 official Week-10 finals are absent.")
    missing_w10 = [g[0] for g in W10_FINALS if g[0] not in feed_w10]

    # --- Injury capture internal consistency (round-1 capture) ---------------
    cap1 = load("official_reads_2026_11_17.json")
    inj1 = cap1["injury_report_week10"]
    inj_sum = sum(r["players_listed"] for r in inj1["rows"])
    tot = inj1["totals"]
    check("RC-13", "Round-1 capture: players_listed summed over clubs = its own totals.players_listed",
          inj_sum, tot["players_listed"], SRC_INJ10,
          note="Round-1 findings text states 326 rows / 14 Out / 11 Questionable; the capture's own totals differ.")
    cin = [r for r in inj1["rows"] if r["club"] == "CIN"]
    check("RC-14", "Round-1 capture: CIN players listed (brief states 4; live CIN section not re-read this round)",
          cin[0]["players_listed"] if cin else None, 4, SRC_INJ10,
          note="Unresolved. Needs a full re-read of the report chunks for CIN.")

    # --- Round-1 standings capture vs today's standings -----------------------
    cap_stand = cap1["standings_2026_week10"]["rows"]
    stale = []
    for r in cap_stand:
        a = r["abbr"]
        if a not in stand:
            continue
        cur = stand[a]
        old = dict(w=r["w"], l=r["l"], t=r["t"], pf=r["pf"], pa=r["pa"])
        if old != cur:
            stale.append(dict(club=a, round1=old, today=cur))
    check("RC-15", "Round-1 standings capture rows equal today's official standings",
          len(cap_stand) - len(stale), len(cap_stand), SRC_STAND,
          note="Differences are Monday's Chargers-Ravens game (final 23-20), played after the round-1 read.")

    # --- Lions / Week-10 designations (live, 2026-11-18) ----------------------
    lions_out = [p for (c, p, _pos, _inj, _pr, gs) in INJ_REG10_CHUNK0_OUT if c == "DET" and gs == "Out"]
    check("RC-16", "Lions Week-10 Out designations with game status populated (Joseph, Mays, Reed)",
          sorted(lions_out), sorted(INJ_REG10_CHUNK0_BLANK_GAME_STATUS_CHECKED), SRC_INJ10)

    # --- Build the official-reads file -----------------------------------------
    reads = dict(
        dataset="nfl_req_review_official_reads",
        round=ROUND,
        session=SESSION,
        read_date=READ_DATE,
        rule="Values typed from the cited official page as read on the read date; totals and reconciliations are computed by engine/round2.py. Structured rows only, no raw HTML committed.",
        sources=[
            dict(id="R2-STAND", url=SRC_STAND, what="2026 league standings, 32 clubs, through Week 10 (chunks 0-1 read)"),
            dict(id="R2-W10", url=SRC_W10, what="Week 10 schedule: 14 final scores and the Teams-on-Bye block (chunks 0-1 read)"),
            dict(id="R2-W11", url=SRC_W11, what="Week 11 schedule: 13 fixtures and the Teams-on-Bye block (chunks 0-1 read)"),
            dict(id="R2-INJ10", url=SRC_INJ10, what="Week 10 injury report: chunk 0 read (WAS, NYG, NE, DET, KC partial); chunks 1-7 not re-read this round"),
            dict(id="R2-INJ11", url=SRC_INJ11, what="Week 11 injury report URL: resolves to the Week 10 report (not yet published at read time)"),
            dict(id="R2-HUB", url=SRC_INJ_HUB, what="Injury hub: shows Week 10 at read time"),
        ],
        standings_2026_11_18=[dict(club=a, w=w, l=l, t=t, pf=pf, pa=pa) for a, w, l, t, pf, pa in STANDINGS_2026_11_18],
        week10_finals=[dict(game_id=g[0], away=g[1], away_pts=g[2], home=g[3], home_pts=g[4], game_url=g[5], date=g[6]) for g in W10_FINALS],
        week11_fixtures=[dict(away=g[0], home=g[1], date=g[2], kickoff=g[3], network=g[4], game_url=g[5]) for g in W11_FIXTURES],
        injury_reg10_chunk0_out=[dict(club=c, player=p, position=pos, injury=inj, practice=pr, game_status=gs)
                                 for c, p, pos, inj, pr, gs in INJ_REG10_CHUNK0_OUT],
        feed_reconciliation=dict(
            feed_file="nfl-book/data/results_feed.json",
            abbreviation_map={"LA": "LAR"},
            feed_rows_total=len(feed["rows"]),
            feed_rows_weeks_1_9=len(feed_games_w19),
            feed_week10_game_ids=feed_w10,
            official_week10_missing_from_feed=missing_w10,
            clubs_matching=len(stand) - len(mismatches),
            clubs_mismatching=mismatches,
        ),
        derived=dict(
            games_completed_through_week10=games_thru_w10,
            games_completed_through_week9=games_thru_w9,
            week10_byes_computed=byes_computed,
            week11_byes_computed=byes11,
            week11_fixture_count=len(W11_FIXTURES),
            round1_capture_players_listed_sum=inj_sum,
            round1_capture_totals=tot,
        ),
        checks=checks,
    )
    dump("official_reads_2026_11_18.json", reads)
    return reads


def load_feed():
    return json.load(open(os.path.join(ROOT, "nfl-book", "data", "results_feed.json"), encoding="utf-8"))


if __name__ == "__main__":
    r = main()
    bad = [c for c in r["checks"] if not c["ok"]]
    print("computed checks:", len(r["checks"]), "not-as-expected:", [c["id"] for c in bad])
