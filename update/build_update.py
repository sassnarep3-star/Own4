#!/usr/bin/env python3
"""
Own4 update builder — official 2026-11-02 slate settlement + 2026-11-03..2026-11-05 refresh.

Every score, record, game id, tip time and name below was transcribed on 2026-11-05 UTC
from the official NBA.com pages listed in SOURCES. Nothing is inferred. Home/away order
follows the team listing order used by the repo (first listed = away, second = home, as
on the official game slugs, e.g. okc-vs-cle with Cleveland at home); no home/away
designation is asserted beyond the listing order, consistent with repo flag I-11.

Run: python3 update/build_update.py
Outputs: update/settlement_2026-11-02.json, update/games_2026-11-03_to_2026-11-05.json
"""
import csv
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SRC_NOV2 = "https://www.nba.com/games?date=2026-11-02"
SRC_NOV3 = "https://www.nba.com/games?date=2026-11-03"
SRC_NOV4 = "https://www.nba.com/games?date=2026-11-04"
SRC_NOV5 = "https://www.nba.com/games?date=2026-11-05"

def game_url(slug):
    return f"https://www.nba.com/game/{slug}"

# ---------------------------------------------------------------------------
# OFFICIAL 2026-11-02 final scores, transcribed line-by-line from SRC_NOV2
# (fetched 2026-11-05 UTC). "record_*" is the team record displayed next to
# the game on that page (as displayed, not recomputed). leaders_* as displayed.
# ---------------------------------------------------------------------------
NOV2_OFFICIAL = [
    dict(game_id="0022600158", slug="okc-vs-cle-0022600158", away="OKC", away_name="Thunder", away_pts=117,
         home="CLE", home_name="Cavaliers", home_pts=112, status="Final",
         record_a="5-2", record_b="4-3",
         leader_a=("Shai Gilgeous-Alexander", 43, 3, 8), leader_b=("Donovan Mitchell", 17, 5, 11)),
    dict(game_id="0022600163", slug="chi-vs-phi-0022600163", away="CHI", away_name="Bulls", away_pts=107,
         home="PHI", home_name="76ers", home_pts=126, status="Final",
         record_a="1-6", record_b="7-1",
         leader_a=("Caleb Wilson", 24, 7, 4), leader_b=("Tyrese Maxey", 26, 4, 11)),
    dict(game_id="0022600160", slug="atl-vs-ind-0022600160", away="ATL", away_name="Hawks", away_pts=108,
         home="IND", home_name="Pacers", home_pts=104, status="Final",
         record_a="4-4", record_b="2-6",
         leader_a=("Nickeil Alexander-Walker", 34, 4, 4), leader_b=("Braden Smith", 19, 4, 10)),
    dict(game_id="0022600161", slug="bkn-vs-nyk-0022600161", away="BKN", away_name="Nets", away_pts=90,
         home="NYK", home_name="Knicks", home_pts=103, status="Final",
         record_a="1-6", record_b="3-4",
         leader_a=("Julius Randle", 21, 11, 2), leader_b=("Karl-Anthony Towns", 11, 16, 5)),
    dict(game_id="0022600162", slug="was-vs-orl-0022600162", away="WAS", away_name="Wizards", away_pts=103,
         home="ORL", home_name="Magic", home_pts=94, status="Final",
         record_a="4-3", record_b="2-5",
         leader_a=("Anthony Davis", 27, 9, 1), leader_b=("Franz Wagner", 24, 3, 6)),
    dict(game_id="0022600159", slug="det-vs-cha-0022600159", away="DET", away_name="Pistons", away_pts=124,
         home="CHA", home_name="Hornets", home_pts=91, status="Final",
         record_a="6-1", record_b="3-5",
         leader_a=("Cade Cunningham", 33, 5, 7), leader_b=("Brandon Miller", 17, 1, 4)),
    dict(game_id="0022600164", slug="sac-vs-dal-0022600164", away="SAC", away_name="Kings", away_pts=115,
         home="DAL", home_name="Mavericks", home_pts=100, status="Final",
         record_a="1-6", record_b="4-3",
         leader_a=("Darius Acuff Jr.", 25, 5, 6), leader_b=("Daniel Gafford", 20, 7, 0)),
    dict(game_id="0022600166", slug="mil-vs-min-0022600166", away="MIL", away_name="Bucks", away_pts=100,
         home="MIN", home_name="Timberwolves", home_pts=112, status="Final",
         record_a="1-6", record_b="5-3",
         leader_a=("Tyler Herro", 21, 6, 3), leader_b=("LaMelo Ball", 34, 6, 3)),
    dict(game_id="0022600165", slug="nop-vs-mem-0022600165", away="NOP", away_name="Pelicans", away_pts=135,
         home="MEM", home_name="Grizzlies", home_pts=134, status="Final/OT",
         record_a="3-4", record_b="6-1",
         leader_a=("Zion Williamson", 25, 11, 4), leader_b=("Ty Jerome", 40, 5, 5)),
    dict(game_id="0022600167", slug="bos-vs-hou-0022600167", away="BOS", away_name="Celtics", away_pts=93,
         home="HOU", home_name="Rockets", home_pts=109, status="Final",
         record_a="5-2", record_b="7-1",
         leader_a=("Jayson Tatum", 19, 6, 9), leader_b=("Alperen Sengun", 26, 7, 10)),
    dict(game_id="0022600168", slug="uta-vs-sas-0022600168", away="UTA", away_name="Jazz", away_pts=97,
         home="SAS", home_name="Spurs", home_pts=119, status="Final",
         record_a="1-6", record_b="5-2",
         leader_a=("Lauri Markkanen", 22, 8, 3), leader_b=("Dylan Harper", 17, 7, 8)),
    dict(game_id="0022600169", slug="por-vs-den-0022600169", away="POR", away_name="Trail Blazers", away_pts=118,
         home="DEN", home_name="Nuggets", home_pts=110, status="Final",
         record_a="5-1", record_b="3-3",
         leader_a=("Donovan Clingan", 17, 18, 3), leader_b=("Jamal Murray", 35, 5, 6)),
    dict(game_id="0022600171", slug="tor-vs-lac-0022600171", away="TOR", away_name="Raptors", away_pts=125,
         home="LAC", home_name="Clippers", home_pts=118, status="Final",
         record_a="4-3", record_b="1-6",
         leader_a=("Scottie Barnes", 22, 15, 8), leader_b=("Kobe Sanders", 26, 4, 3)),
    dict(game_id="0022600170", slug="phx-vs-gsw-0022600170", away="PHX", away_name="Suns", away_pts=113,
         home="GSW", home_name="Warriors", home_pts=116, status="Final",
         record_a="1-4", record_b="5-3",
         leader_a=("Devin Booker", 26, 3, 5), leader_b=("Stephen Curry", 34, 6, 7)),
    dict(game_id="0022600172", slug="mia-vs-lal-0022600172", away="MIA", away_name="Heat", away_pts=117,
         home="LAL", home_name="Lakers", home_pts=138, status="Final",
         record_a="2-5", record_b="6-2",
         leader_a=("Giannis Antetokounmpo", 30, 12, 7), leader_b=("Luka Dončić", 42, 7, 13)),
]

# ---------------------------------------------------------------------------
# OFFICIAL 2026-11-04 final scores, transcribed from SRC_NOV4 (fetched 2026-11-05 UTC)
# ---------------------------------------------------------------------------
NOV4_OFFICIAL = [
    dict(game_id="0022600174", slug="atl-vs-was-0022600174", away="ATL", away_name="Hawks", away_pts=120,
         home="WAS", home_name="Wizards", home_pts=105, status="Final",
         record_a="5-4", record_b="4-4",
         leader_a=("Onyeka Okongwu", 14, 16, 4), leader_b=("Anthony Davis", 26, 10, 3)),
    dict(game_id="0022600173", slug="phi-vs-det-0022600173", away="PHI", away_name="76ers", away_pts=112,
         home="DET", home_name="Pistons", home_pts=106, status="Final",
         record_a="8-1", record_b="6-2",
         leader_a=("Jaylen Brown", 30, 7, 1), leader_b=("Duncan Robinson", 27, 1, 2)),
    dict(game_id="0022600175", slug="mil-vs-bos-0022600175", away="MIL", away_name="Bucks", away_pts=102,
         home="BOS", home_name="Celtics", home_pts=109, status="Final",
         record_a="1-7", record_b="6-2",
         leader_a=("Tyler Herro", 25, 5, 3), leader_b=("Derrick White", 24, 4, 7)),
    dict(game_id="0022600176", slug="cha-vs-bkn-0022600176", away="CHA", away_name="Hornets", away_pts=104,
         home="BKN", home_name="Nets", home_pts=114, status="Final",
         record_a="3-6", record_b="2-6",
         leader_a=("Naz Reid", 28, 9, 2), leader_b=("Michael Porter Jr.", 26, 10, 0)),
    dict(game_id="0022600177", slug="chi-vs-nyk-0022600177", away="CHI", away_name="Bulls", away_pts=105,
         home="NYK", home_name="Knicks", home_pts=135, status="Final",
         record_a="1-7", record_b="4-4",
         leader_a=("Jaylin Sellers", 14, 3, 1), leader_b=("Jalen Brunson", 33, 2, 4)),
    dict(game_id="0022600180", slug="cle-vs-okc-0022600180", away="CLE", away_name="Cavaliers", away_pts=116,
         home="OKC", home_name="Thunder", home_pts=124, status="Final",
         record_a="4-4", record_b="6-2",
         leader_a=("Donovan Mitchell", 27, 3, 6), leader_b=("Shai Gilgeous-Alexander", 42, 4, 8)),
    dict(game_id="0022600179", slug="uta-vs-nop-0022600179", away="UTA", away_name="Jazz", away_pts=113,
         home="NOP", home_name="Pelicans", home_pts=120, status="Final/OT",
         record_a="1-7", record_b="4-4",
         leader_a=("Keyonte George", 39, 2, 9), leader_b=("Dejounte Murray", 20, 8, 4)),
    dict(game_id="0022600178", slug="ind-vs-mem-0022600178", away="IND", away_name="Pacers", away_pts=107,
         home="MEM", home_name="Grizzlies", home_pts=103, status="Final",
         record_a="3-6", record_b="6-2",
         leader_a=("Pascal Siakam", 20, 5, 2), leader_b=("Cedric Coward", 23, 9, 4)),
    dict(game_id="0022600181", slug="min-vs-hou-0022600181", away="MIN", away_name="Timberwolves", away_pts=117,
         home="HOU", home_name="Rockets", home_pts=107, status="Final",
         record_a="6-3", record_b="7-2",
         leader_a=("Jonathan Kuminga", 16, 8, 5), leader_b=("Alperen Sengun", 17, 12, 10)),
    dict(game_id="0022600182", slug="tor-vs-den-0022600182", away="TOR", away_name="Raptors", away_pts=109,
         home="DEN", home_name="Nuggets", home_pts=128, status="Final",
         record_a="4-4", record_b="4-3",
         leader_a=("RJ Barrett", 22, 5, 3), leader_b=("Nikola Jokić", 32, 10, 11)),
    dict(game_id="0022600183", slug="por-vs-phx-0022600183", away="POR", away_name="Trail Blazers", away_pts=132,
         home="PHX", home_name="Suns", home_pts=119, status="Final",
         record_a="6-1", record_b="1-5",
         leader_a=("Donovan Clingan", 24, 11, 1), leader_b=("Devin Booker", 33, 1, 2)),
    dict(game_id="0022600184", slug="dal-vs-sas-0022600184", away="DAL", away_name="Mavericks", away_pts=111,
         home="SAS", home_name="Spurs", home_pts=112, status="Final",
         record_a="4-4", record_b="6-2",
         leader_a=("Kyrie Irving", 29, 7, 5), leader_b=("Victor Wembanyama", 52, 24, 2)),
    dict(game_id="0022600185", slug="lal-vs-sac-0022600185", away="LAL", away_name="Lakers", away_pts=116,
         home="SAC", home_name="Kings", home_pts=103, status="Final",
         record_a="7-2", record_b="1-7",
         leader_a=("Luka Dončić", 40, 9, 7), leader_b=("Domantas Sabonis", 16, 17, 1)),
    dict(game_id="0022600186", slug="mia-vs-lac-0022600186", away="MIA", away_name="Heat", away_pts=117,
         home="LAC", home_name="Clippers", home_pts=116, status="Final/OT",
         record_a="3-5", record_b="1-7",
         leader_a=("Bam Adebayo", 35, 10, 4), leader_b=("Rui Hachimura", 21, 9, 7)),
]

# Final/OT markers: NOP-MEM (2026-11-02), UTA-NOP and MIA-LAC (2026-11-04).
# ADR: the official page displays "Final/OT" for these; no overtime points are broken out here.

# ---------------------------------------------------------------------------
# 2026-11-05 — scheduled only, nothing played at fetch time (fetched 2026-11-05 UTC)
# "season_leader_*" are the PPG/RPG/APG values displayed on the schedule preview,
# NOT game results.
# ---------------------------------------------------------------------------
NOV5_SCHEDULED = [
    dict(game_id="0022600187", slug="orl-vs-phx-0022600187", away="ORL", away_name="Magic", away_record="2-5",
         home="PHX", home_name="Suns", home_record="1-5", tip_et="9:00 PM ET", status="scheduled",
         season_leaders={"ORL": ("Franz Wagner", 20.3, 6.1, 7.6), "PHX": ("Devin Booker", 24.7, 3.2, 4.7)}),
    dict(game_id="0022600188", slug="mia-vs-gsw-0022600188", away="MIA", away_name="Heat", away_record="3-5",
         home="GSW", home_name="Warriors", home_record="5-3", tip_et="10:00 PM ET", status="scheduled",
         season_leaders={"MIA": ("Giannis Antetokounmpo", 28.3, 12.5, 5.8), "GSW": ("Stephen Curry", 30.0, 4.2, 4.5)}),
]


def leader_dict(t):
    return {"player": t[0], "pts": t[1], "reb": t[2], "ast": t[3]}


def final_row(g, date, src):
    total = g["away_pts"] + g["home_pts"]
    margin_home = g["home_pts"] - g["away_pts"]
    return {
        "date": date,
        "game_id": g["game_id"],
        "away": g["away"], "away_name": g["away_name"], "away_pts": g["away_pts"],
        "home": g["home"], "home_name": g["home_name"], "home_pts": g["home_pts"],
        "status": g["status"],
        "total_pts": total,
        "margin_home": margin_home,
        "away_record_shown": g["record_a"],
        "home_record_shown": g["record_b"],
        "away_leader": leader_dict(g["leader_a"]),
        "home_leader": leader_dict(g["leader_b"]),
        "source_url": src,
        "game_url": game_url(g["slug"]),
        "verification": "transcribed line-by-line from the official NBA.com games page on 2026-11-05 UTC",
        "unverified": False,
    }


def build_settlement():
    slate_path = os.path.join(ROOT, "data", "own_lines_2026-11-02.csv")
    with open(slate_path, newline="", encoding="utf-8") as f:
        slate = {r["game_id"]: r for r in csv.DictReader(f)}

    official = {g["game_id"]: g for g in NOV2_OFFICIAL}
    missing = sorted(set(slate) - set(official))
    extra = sorted(set(official) - set(slate))
    rows = []
    for gid, line in slate.items():
        g = official.get(gid)
        if g is None:
            continue
        if g["away"] != line["away"] or g["home"] != line["home"]:
            raise SystemExit(f"TEAM MISMATCH for {gid}: slate {line['away']}@{line['home']} vs official {g['away']}@{g['home']}")
        total_pts = g["away_pts"] + g["home_pts"]
        margin_home = g["home_pts"] - g["away_pts"]
        spread_home = float(line["own_spread_home"])
        own_total = float(line["own_total"])
        p_home = float(line["p_home_win"])
        p_over = float(line["p_over_own_total"])
        model_margin = float(line["model_margin_home"])
        model_total = float(line["model_total"])
        home_win = 1 if margin_home > 0 else 0
        home_cover = (margin_home + spread_home) > 0
        push_spread = (margin_home + spread_home) == 0
        over = total_pts > own_total
        push_total = total_pts == own_total
        su_pick_home = p_home >= 0.5
        su_hit = (margin_home > 0) == su_pick_home
        total_pick_over = p_over >= 0.5
        total_hit = (total_pts > own_total) == total_pick_over
        rows.append({
            "date": "2026-11-02",
            "game_id": gid,
            "away": g["away"], "home": g["home"],
            "away_pts": g["away_pts"], "home_pts": g["home_pts"],
            "status": g["status"],
            "total_pts": total_pts,
            "margin_home": margin_home,
            "own_spread_home": spread_home,
            "home_cover": home_cover,
            "home_spread_push": push_spread,
            "own_total": own_total,
            "over_own_total": over,
            "total_push": push_total,
            "p_home_win": p_home,
            "su_pick": "home" if su_pick_home else "away",
            "su_hit": su_hit,
            "p_over_own_total": p_over,
            "total_pick": "over" if total_pick_over else "under",
            "total_hit": total_hit,
            "brier": round((p_home - home_win) ** 2, 6),
            "model_margin_home": model_margin,
            "margin_abs_error": round(abs(model_margin - margin_home), 6),
            "model_total": model_total,
            "total_abs_error": round(abs(model_total - total_pts), 6),
            "source_url": SRC_NOV2,
            "game_url": game_url(g["slug"]),
            "slate_source": "data/own_lines_2026-11-02.csv (repo, pre-tip 2026-11-02T18:02Z)",
            "unverified": False,
        })

    n = len(rows)
    over_n = sum(1 for r in rows if r["over_own_total"])
    home_cover_n = sum(1 for r in rows if r["home_cover"])
    su_hits = sum(1 for r in rows if r["su_hit"])
    tot_hits = sum(1 for r in rows if r["total_hit"])
    out = {
        "season": "2026-27",
        "built_utc": "2026-11-05",
        "slate": "2026-11-02 (15 games; pre-tip lines committed in repo before first tip)",
        "sources": [SRC_NOV2],
        "games_in_slate": len(slate),
        "games_settled": n,
        "games_missing_official_result": missing,
        "official_games_not_in_slate": extra,
        "aggregates": {
            "n": n,
            "su_hits": su_hits,
            "su_accuracy": round(su_hits / n, 6) if n else None,
            "home_spread_covers": home_cover_n,
            "overs_own_total": over_n,
            "over_rate": round(over_n / n, 6) if n else None,
            "totals_pick_hits": tot_hits,
            "totals_pick_accuracy": round(tot_hits / n, 6) if n else None,
            "mean_brier": round(sum(r["brier"] for r in rows) / n, 6) if n else None,
            "margin_mae": round(sum(r["margin_abs_error"] for r in rows) / n, 6) if n else None,
            "total_mae": round(sum(r["total_abs_error"] for r in rows) / n, 6) if n else None,
            "ot_games": sum(1 for r in rows if r["status"] == "Final/OT"),
        },
        "interpretation": (
            "n=15. This is ONE pre-registered slate settled prospectively (G12-style). "
            "It does NOT validate any strategy: the repo's G1 gate requires n>=300. "
            "Records shown are the team records displayed on the official games page as fetched 2026-11-05 UTC."
        ),
        "rows": rows,
    }
    return out


def build_refresh():
    nov4 = [final_row(g, "2026-11-04", SRC_NOV4) for g in NOV4_OFFICIAL]
    nov5 = []
    for g in NOV5_SCHEDULED:
        nov5.append({
            "date": "2026-11-05",
            "game_id": g["game_id"],
            "away": g["away"], "away_name": g["away_name"], "away_record": g["away_record"],
            "home": g["home"], "home_name": g["home_name"], "home_record": g["home_record"],
            "tip_et": g["tip_et"],
            "status": g["status"],
            "away_pts": None, "home_pts": None,
            "season_leaders_shown": {
                team: {"player": v[0], "ppg": v[1], "rpg": v[2], "apg": v[3]}
                for team, v in g["season_leaders"].items()
            },
            "source_url": SRC_NOV5,
            "game_url": game_url(g["slug"]),
            "verification": "schedule preview as displayed on the official NBA.com games page on 2026-11-05 UTC; NOT a result",
            "unverified": False,
        })
    out = {
        "season": "2026-27",
        "built_utc": "2026-11-05",
        "window": "2026-11-03 through 2026-11-05",
        "completed_games_2026-11-03": 0,
        "completed_games_2026-11-04": len(nov4),
        "scheduled_games_2026-11-05": len(nov5),
        "no_games_2026-11-03": {
            "status": "no games scheduled (official page displays 'No Games Scheduled')",
            "source_url": SRC_NOV3,
        },
        "completed_games_total_through_2026-11-04": 92 + 15 + 0 + len(nov4),
        "completed_games_note": (
            "92 = lab dataset (data/games_2026-27.csv, through 2026-11-01) + 15 (2026-11-02, official, this session) "
            "+ 0 (2026-11-03) + 14 (2026-11-04, official, this session) = 121 completed games through 2026-11-04. "
            "The repo's own date-scoped snapshots (official/ 56 rows; lab 92; own4-dashboard 62) are retained unchanged; "
            "this file is additive and does not rewrite them."
        ),
        "sources": [SRC_NOV3, SRC_NOV4, SRC_NOV5],
        "games_2026-11-04": nov4,
        "games_2026-11-05": nov5,
    }
    return out


def main():
    settlement = build_settlement()
    refresh = build_refresh()
    with open(os.path.join(HERE, "settlement_2026-11-02.json"), "w", encoding="utf-8") as f:
        json.dump(settlement, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with open(os.path.join(HERE, "games_2026-11-03_to_2026-11-05.json"), "w", encoding="utf-8") as f:
        json.dump(refresh, f, indent=2, ensure_ascii=False)
        f.write("\n")
    agg = settlement["aggregates"]
    print(f"settled {settlement['games_settled']}/{settlement['games_in_slate']} games")
    print(json.dumps(agg, indent=2))
    print(f"refresh: nov3={refresh['completed_games_2026-11-03']} nov4={refresh['completed_games_2026-11-04']} nov5_sched={refresh['scheduled_games_2026-11-05']} total_through_nov4={refresh['completed_games_total_through_2026-11-04']}")


if __name__ == "__main__":
    main()
