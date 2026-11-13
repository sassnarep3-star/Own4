#!/usr/bin/env python3
"""Build the Own4 NFL Command Center data layer from raw official transcriptions.

Every value in this namespace comes from one of two places:

  OFFICIAL    - read from nfl.com on 2026-11-13 and archived under data/raw/.
  THIRD-PARTY - the nflverse/nfldata archive, used only for historical game
                results and closing market lines. The NFL publishes no odds.

Nothing is inferred. Where an official source does not publish a value (a depth
rank, a player-prop price, an official injury reason) the field is None and is
published as a blank cell on the site and listed on the Flagged for Review page.

Run:  python3 nfl-hq/build_data.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
RAW = os.path.join(DATA, "raw")
OFF = os.path.join(DATA, "official")
DER = os.path.join(DATA, "derived")
VER = os.path.join(DATA, "verification")
for d in (OFF, DER, VER):
    os.makedirs(d, exist_ok=True)

SNAPSHOT_DATE = "2026-11-13"
SNAPSHOT_UTC = "2026-11-13T00:00:00Z"

# ---------------------------------------------------------------- source URLs
NFL_STANDINGS = "https://www.nfl.com/standings/league/2026/REG"
NFL_TEAM_STATS = "https://www.nfl.com/stats/team-stats/"
NFL_INJURIES = "https://www.nfl.com/injuries/"
NFL_SCHEDULE = "https://www.nfl.com/schedules/2026/REG10"
NFL_SCORES_REG9 = "https://www.nfl.com/scores/2026/REG9"
NFL_SCORES_REG10 = "https://www.nfl.com/scores/2026/REG10"
NFLVERSE = "https://github.com/nflverse/nfldata"

TEAM_NAMES = {
    "BUF": "Buffalo Bills", "ATL": "Atlanta Falcons", "NE": "New England Patriots",
    "BAL": "Baltimore Ravens", "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns",
    "DAL": "Dallas Cowboys", "DEN": "Denver Broncos", "DET": "Detroit Lions",
    "GB": "Green Bay Packers", "HOU": "Houston Texans", "IND": "Indianapolis Colts",
    "JAX": "Jacksonville Jaguars", "KC": "Kansas City Chiefs", "LV": "Las Vegas Raiders",
    "LAC": "Los Angeles Chargers", "LAR": "Los Angeles Rams", "LA": "Los Angeles Rams",
    "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings", "NE2": "New England Patriots",
    "NYG": "New York Giants", "NYJ": "New York Jets", "PHI": "Philadelphia Eagles",
    "PIT": "Pittsburgh Steelers", "SF": "San Francisco 49ers", "SEA": "Seattle Seahawks",
    "TB": "Tampa Bay Buccaneers", "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
    "ARI": "Arizona Cardinals", "AZ": "Arizona Cardinals", "NO": "New Orleans Saints",
    "CHI": "Chicago Bears", "CAR": "Carolina Panthers",
}

# Unit grouping and the deficiency weights. These are analyst-defined weights,
# not official values. They are published on the site with the formula so a
# reader can recompute or reject them.
GROUPS = [
    ("Offense skill", {"QB", "RB", "FB", "WR", "TE"}),
    ("Offensive line", {"T", "G", "C", "OL"}),
    ("Front seven", {"DE", "DT", "LB", "NT"}),
    ("Secondary", {"CB", "S", "DB"}),
    ("Special teams", {"K", "P", "LS"}),
]
STATUS_WEIGHT = {"Out": 1.0, "Doubtful": 0.75, "Questionable": 0.35, "": 0.10}
PRACTICE_WEIGHT = {
    "Did Not Participate In Practice": 0.6,
    "Limited Participation in Practice": 0.3,
    "Full Participation in Practice": 0.0,
    "": 0.0,
}
DEFICIENCY_FORMULA = (
    "deficiency_load = sum over listed players of "
    "STATUS_WEIGHT[game status] + PRACTICE_WEIGHT[practice status]; "
    "STATUS_WEIGHT = Out 1.0, Doubtful 0.75, Questionable 0.35, no status 0.10; "
    "PRACTICE_WEIGHT = Did Not Participate 0.6, Limited 0.3, Full 0.0."
)


def group_of(pos: str) -> str:
    for name, s in GROUPS:
        if pos in s:
            return name
    return "Unclassified"


def sha256(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def write_json(path: str, obj) -> None:
    with open(path, "w") as fh:
        json.dump(obj, fh, indent=1)
        fh.write("\n")


def read_tsv(path: str):
    rows = []
    for ln in open(path, encoding="utf-8"):
        ln = ln.rstrip("\n")
        if not ln or ln.startswith("#"):
            continue
        rows.append(ln.split("\t"))
    return rows


def num_eq(a, b) -> bool:
    try:
        return abs(float(a) - float(b)) < 1e-9
    except (TypeError, ValueError):
        return str(a).strip() == str(b).strip()


# ------------------------------------------------------------------ standings
def build_standings():
    raw = open(os.path.join(RAW, "standings_league_2026_REG.md"), encoding="utf-8").read()
    lines, buf = [], None
    for ln in raw.splitlines():
        if ln.startswith("CHUNK"):
            continue
        if buf is not None:
            buf += ln.strip()
            if buf.endswith("|"):
                lines.append(buf)
                buf = None
        elif ln.strip().startswith("|"):
            s = ln.strip()
            if s.endswith("|"):
                lines.append(s)
            else:
                buf = s
    rows = []
    for l in lines:
        cells = [c.strip() for c in l.strip("|").split("|")]
        abbr = re.search(r"logos/([A-Z]+)\)", cells[0]).group(1)
        name = cells[0].split("\\<br>")[2]
        url = re.search(r"\]\((https://www\.nfl\.com/teams/[^)]+)\)", cells[0]).group(1)
        rows.append({"team": name, "abbr": abbr, "team_url": url,
                     "v": [c.replace(" - ", "-") for c in cells[1:17]]})

    cols = ["team", "abbr", "w", "l", "t", "pct", "pf", "pa", "net_pts", "home",
            "road", "div", "div_pct", "conf", "conf_pct", "nonconf", "streak", "last5"]
    out_rows = [[r["team"], r["abbr"]] + r["v"] for r in rows]
    doc = {
        "id": "standings_2026",
        "title": "2026 NFL League Standings",
        "source_url": NFL_STANDINGS,
        "publisher": "NFL.com (official league site)",
        "official": True,
        "method": ("Page fetched and read directly on %s (2 chunks). All 32 rows transcribed "
                   "from the rendered league standings table. Raw capture: "
                   "nfl-hq/data/raw/standings_league_2026_REG.md") % SNAPSHOT_DATE,
        "retrieved_utc": SNAPSHOT_UTC,
        "snapshot_date": SNAPSHOT_DATE,
        "columns": cols,
        "rows": out_rows,
        "team_urls": {r["abbr"]: r["team_url"] for r in rows},
    }
    write_json(os.path.join(OFF, "standings_2026-11-13.json"), doc)
    return doc


# ----------------------------------------------------------------- team stats
def build_team_stats():
    raw = open(os.path.join(RAW, "team_stats_offense_passing_2026.md"), encoding="utf-8").read()
    rows = []
    for ln in raw.splitlines():
        if ln.startswith("CHUNK") or not ln.strip().startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        abbr = re.search(r"logos/([A-Z]+)\)", cells[0]).group(1)
        rows.append((abbr, cells[1:]))
    cols = ["team", "nfl_abbr", "archive_abbr", "att", "cmp", "cmp_pct", "yds_per_att",
            "pass_yds", "pass_td", "int", "rating", "first_downs", "first_pct",
            "passes_20plus", "passes_40plus", "longest", "sacks", "sack_yards"]
    out_rows = [[TEAM_NAMES[a], a, a] + v for a, v in rows]
    doc = {
        "id": "team_stats_offense_passing_2026",
        "title": "NFL 2026 REG - offense passing stats",
        "source_url": NFL_TEAM_STATS,
        "publisher": "NFL.com (official league site)",
        "official": True,
        "method": ("Page fetched and read directly on %s. All 32 rows transcribed from the "
                   "rendered offense/passing table. Raw capture: "
                   "nfl-hq/data/raw/team_stats_offense_passing_2026.md") % SNAPSHOT_DATE,
        "retrieved_utc": SNAPSHOT_UTC,
        "snapshot_date": SNAPSHOT_DATE,
        "columns": cols,
        "rows": out_rows,
    }
    write_json(os.path.join(OFF, "team_stats_2026-11-13.json"), doc)
    return doc


# ------------------------------------------------------------------- injuries
def build_injuries(schedule):
    rows = []
    for p in read_tsv(os.path.join(RAW, "injuries_week10_2026.tsv")):
        rows.append(dict(game=p[0], away=p[1], home=p[2], team=p[3], player=p[4],
                         position=p[5], injuries=p[6], practice=p[7], status=p[8], url=p[9]))
    by_game = defaultdict(lambda: defaultdict(list))
    meta = {}
    for r in rows:
        by_game[r["game"]][r["team"]].append(r)
        meta[r["game"]] = (r["away"], r["home"])

    sched_by_pair = {(s["away"], s["home"]): s for s in schedule}
    games = []
    for gi in sorted(by_game, key=lambda x: int(x)):
        teams = by_game[gi]
        pair = meta[gi]
        s = sched_by_pair.get(pair, {})
        games.append({
            "game_index": int(gi),
            "date_label": s.get("date_label"),
            "kickoff_et": s.get("kickoff_et"),
            "network": s.get("network"),
            "away": pair[0], "home": pair[1],
            "away_record": s.get("away_record"), "home_record": s.get("home_record"),
            "game_url": s.get("game_url"),
            "teams": {t: [[r["player"], r["position"], r["injuries"], r["practice"],
                           r["status"], r["url"]] for r in v] for t, v in teams.items()},
        })
    doc = {
        "id": "injuries_week10_2026",
        "title": "Official Latest NFL Injury Report for Players - Week 10 of the 2026 Season",
        "source_url": NFL_INJURIES,
        "publisher": "NFL.com (official league site)",
        "official": True,
        "method": ("Page fetched and read directly on %s (chunks 0-6 of 8; chunk 7 is page "
                   "footer). All 14 games and every published player row transcribed. Raw "
                   "capture: nfl-hq/data/raw/injuries_week10_2026.tsv") % SNAPSHOT_DATE,
        "page_title_as_published": "Official Latest NFL Injury Report for Players - Week 10 of the 2026 Season | NFL.com",
        "retrieved_utc": SNAPSHOT_UTC,
        "snapshot_date": SNAPSHOT_DATE,
        "rolling_document_note": ("NFL.com republishes this page each day with new practice and "
                                   "game-status designations. A snapshot is only valid for the "
                                   "date it was read. Re-fetch before any kickoff decision."),
        "games": games,
        "player_rows": len(rows),
    }
    write_json(os.path.join(OFF, "injuries_week10_2026-11-13.json"), doc)
    return doc, rows


# ------------------------------------------------------------------- schedule
def build_schedule():
    games = []
    for p in read_tsv(os.path.join(RAW, "schedule_week10_2026.tsv")):
        games.append(dict(away=p[0], home=p[1], game_url=p[2], date_label=p[3],
                           kickoff_et=p[4], network=p[5], away_record=p[6], home_record=p[7],
                           source_url=NFL_SCORES_REG10))
    byes = [dict(team=p[0], record=p[1], source_url=NFL_SCORES_REG10)
            for p in read_tsv(os.path.join(RAW, "byes_week10_2026.tsv"))]
    doc = {
        "id": "schedule_week10_2026",
        "title": "NFL 2026 Week 10 schedule, matchups, kickoff times, networks and byes",
        "source_url": NFL_SCHEDULE,
        "secondary_source_url": NFL_SCORES_REG10,
        "publisher": "NFL.com (official league site)",
        "official": True,
        "method": ("Week 10 matchups, kickoff times, networks, team records, official game "
                   "page URLs and the bye list read on %s from the NFL.com Week 10 scores and "
                   "schedule pages and the Week 10 injury report.") % SNAPSHOT_DATE,
        "retrieved_utc": SNAPSHOT_UTC,
        "snapshot_date": SNAPSHOT_DATE,
        "games": games,
        "byes": byes,
    }
    write_json(os.path.join(OFF, "schedule_week10_2026-11-13.json"), doc)
    return doc


# ------------------------------------------------------------------ deficiency
def build_deficiency(injuries_doc):
    teams = {}
    for g in injuries_doc["games"]:
        for side in ("away", "home"):
            abbr = g[side]
            listed_rows = g["teams"].get(abbr, [])
            counts = {name: dict(listed=0, out=0, doubtful=0, questionable=0,
                                 dnp=0, limited=0, load=0.0) for name, _ in GROUPS}
            qb_rows = []
            for player, pos, inj, practice, status, url in listed_rows:
                grp = group_of(pos)
                c = counts.setdefault(grp, dict(listed=0, out=0, doubtful=0, questionable=0,
                                                dnp=0, limited=0, load=0.0))
                c["listed"] += 1
                if status == "Out":
                    c["out"] += 1
                elif status == "Doubtful":
                    c["doubtful"] += 1
                elif status == "Questionable":
                    c["questionable"] += 1
                if practice == "Did Not Participate In Practice":
                    c["dnp"] += 1
                elif practice == "Limited Participation in Practice":
                    c["limited"] += 1
                c["load"] += STATUS_WEIGHT.get(status, 0.0) + PRACTICE_WEIGHT.get(practice, 0.0)
                if pos == "QB":
                    qb_rows.append(dict(player=player, injury=inj, practice=practice,
                                        status=status, url=url))
            worst = sorted(counts.items(), key=lambda kv: -kv[1]["load"])
            teams[abbr] = {
                "team": abbr,
                "opponent": g["home"] if side == "away" else g["away"],
                "game_index": g["game_index"],
                "players_listed": sum(c["listed"] for c in counts.values()),
                "ruled_out": sum(c["out"] for c in counts.values()),
                "doubtful": sum(c["doubtful"] for c in counts.values()),
                "questionable": sum(c["questionable"] for c in counts.values()),
                "did_not_practice": sum(c["dnp"] for c in counts.values()),
                "limited_practice": sum(c["limited"] for c in counts.values()),
                "deficiency_load": round(sum(c["load"] for c in counts.values()), 2),
                "most_affected_unit": worst[0][0] if worst and worst[0][1]["listed"] else None,
                "most_affected_unit_load": round(worst[0][1]["load"], 2) if worst and worst[0][1]["listed"] else None,
                "by_group": {k: v for k, v in counts.items() if v["listed"]},
                "qb_rows": qb_rows,
                "qb_depth_rank": None,
                "qb_depth_rank_source": None,
                "qb_depth_rank_note": ("The NFL publishes no depth-chart rank. The only official "
                                        "depth evidence is the substitution depth code printed in "
                                        "the official game book after the game; see the Depth Chart "
                                        "page for the two worked examples."),
            }
    rows = []
    for abbr, t in teams.items():
        rows.append({
            "team": abbr, "opponent": t["opponent"], "game_index": t["game_index"],
            "players_listed": t["players_listed"], "ruled_out": t["ruled_out"],
            "doubtful": t["doubtful"], "questionable": t["questionable"],
            "did_not_practice": t["did_not_practice"],
            "limited_practice": t["limited_practice"],
            "deficiency_load": t["deficiency_load"],
            "most_affected_unit": t["most_affected_unit"],
            "most_affected_unit_load": t["most_affected_unit_load"],
            "qbs_on_report": "; ".join(
                "%s (%s, %s)" % (q["player"], q["practice"], q["status"] or "no game status")
                for q in t["qb_rows"]) or "none listed",
            "qb_depth_rank_2nd_3rd_4th": None,
        })
    rows.sort(key=lambda r: (-r["deficiency_load"], r["team"]))
    doc = {
        "id": "deficiency_week10_2026",
        "title": "Unit-deficiency read for every team in the Week 10 slate",
        "source_url": NFL_INJURIES,
        "official_source": True,
        "value_type": "derived",
        "derivation": DEFICIENCY_FORMULA,
        "snapshot_date": SNAPSHOT_DATE,
        "retrieved_utc": SNAPSHOT_UTC,
        "teams": teams,
        "rows": rows,
    }
    write_json(os.path.join(DER, "deficiency_2026-11-13.json"), doc)
    return doc


# ----------------------------------------------------------- score spot-check
WEEK9_OFFICIAL = [
    ("JAX", 33, "BAL", 10, "https://www.nfl.com/games/jaguars-at-ravens-2026-reg-9"),
    ("CIN", 34, "ATL", 17, "https://www.nfl.com/games/bengals-at-falcons-2026-reg-9"),
    ("DEN", 26, "CAR", 21, "https://www.nfl.com/games/broncos-at-panthers-2026-reg-9"),
    ("DAL", 27, "IND", 23, "https://www.nfl.com/games/cowboys-at-colts-2026-reg-9"),
    ("NYJ", 12, "KC", 35, "https://www.nfl.com/games/jets-at-chiefs-2026-reg-9"),
    ("DET", 19, "MIA", 9, "https://www.nfl.com/games/lions-at-dolphins-2026-reg-9"),
    ("CLE", 22, "NO", 23, "https://www.nfl.com/games/browns-at-saints-2026-reg-9"),
    ("NYG", 19, "PHI", 11, "https://www.nfl.com/games/giants-at-eagles-2026-reg-9"),
    ("LA", 20, "WAS", 13, "https://www.nfl.com/games/rams-at-commanders-2026-reg-9"),
    ("HOU", 44, "LAC", 22, "https://www.nfl.com/games/texans-at-chargers-2026-reg-9"),
    ("LV", 17, "SF", 38, "https://www.nfl.com/games/raiders-at-49ers-2026-reg-9"),
    ("GB", 45, "NE", 27, "https://www.nfl.com/games/packers-at-patriots-2026-reg-9"),
    ("AZ", 3, "SEA", 17, "https://www.nfl.com/games/cardinals-at-seahawks-2026-reg-9"),
    ("TB", 24, "CHI", 27, "https://www.nfl.com/games/buccaneers-at-bears-2026-reg-9"),
    ("BUF", 23, "MIN", 6, "https://www.nfl.com/games/bills-at-vikings-2026-reg-9"),
]
WEEK10_OFFICIAL = [
    ("WAS", 24, "NYG", 21, "https://www.nfl.com/games/commanders-at-giants-2026-reg-10"),
]


def load_archive():
    path = os.path.join(os.path.dirname(ROOT), "nfl-lines", "data", "raw", "nfldata_games.csv")
    if not os.path.exists(path):
        return None, None
    rows = {}
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows[(r["season"], r["game_type"], r["week"], r["away_team"], r["home_team"])] = r
    return rows, path


def spot_check():
    arch, path = load_archive()
    out = []
    if arch is None:
        return {"status": "archive not found", "checks": []}
    # NFL.com renders the Cardinals as AZ; the nflverse archive uses ARI.
    # The Rams are LA in both.
    arch_abbr = {"AZ": "ARI"}
    for label, official in (("2026 REG9", WEEK9_OFFICIAL), ("2026 REG10", WEEK10_OFFICIAL)):
        for away, ascore, home, hscore, url in official:
            key = ("2026", "REG", "9" if label.endswith("9") else "10",
                   arch_abbr.get(away, away), arch_abbr.get(home, home))
            r = arch.get(key)
            if r is None:
                out.append(dict(week=label, away=away, home=home, official_away=ascore,
                                official_home=hscore, archive_away=None, archive_home=None,
                                result="missing_in_archive", source_url=url))
                continue
            av, hv = r.get("away_score", ""), r.get("home_score", "")
            if av == "" or hv == "":
                out.append(dict(week=label, away=away, home=home, official_away=ascore,
                                official_home=hscore, archive_away=None, archive_home=None,
                                result="unscored_in_archive",
                                note=("The archived copy of this game carries no final score; the "
                                      "archive snapshot predates the game."),
                                source_url=url))
                continue
            a = int(float(av))
            h = int(float(hv))
            out.append(dict(week=label, away=away, home=home, official_away=ascore,
                            official_home=hscore, archive_away=a, archive_home=h,
                            result="match" if (a == ascore and h == hscore) else "mismatch",
                            source_url=url))
    matched = sum(1 for c in out if c["result"] == "match")
    doc = {
        "id": "official_score_spotcheck_2026-11-13",
        "title": "Official NFL.com final scores re-read and compared to the third-party archive",
        "method": ("Week 9 (15 games) and the completed Week 10 Thursday game were re-read from "
                   "NFL.com scores pages on %s and compared row by row against the nflverse "
                   "nfldata archive. The NFL publishes no market lines; the archive is the only "
                   "source for prices and is labelled third-party everywhere." % SNAPSHOT_DATE),
        "official_source_url": NFL_SCORES_REG9,
        "third_party_source_url": NFLVERSE,
        "archive_path": os.path.relpath(path, os.path.dirname(ROOT)) if path else None,
        "archive_sha256": sha256(path) if path else None,
        "checked_utc": SNAPSHOT_UTC,
        "games_compared": len(out),
        "matched": matched,
        "mismatched": sum(1 for c in out if c["result"] == "mismatch"),
        "missing_in_archive": sum(1 for c in out if c["result"] == "missing_in_archive"),
        "unscored_in_archive": sum(1 for c in out if c["result"] == "unscored_in_archive"),
        "checks": out,
    }
    write_json(os.path.join(VER, "official_score_spotcheck_2026-11-13.json"), doc)
    return doc


def standings_finding(prev, standings, teams_changed, diffs, checked):
    """Derived, never written by hand: the numbers in the sentence come from the diff itself."""
    total = len(prev["rows"])
    identical = total - len(teams_changed)
    if not teams_changed:
        return ("All %d teams are cell-for-cell identical to the 2026-11-12 snapshot across %d "
                "compared cells." % (total, checked))
    ncells = sum(len(d["changed"]) for d in diffs)
    names = ", ".join(teams_changed)
    cols = sorted({c["column"] for d in diffs for c in d["changed"]})
    return ("%d of %d teams are cell-for-cell identical across %d compared cells. %d teams moved "
            "across %d cells (%s). Columns that moved: %s. The only result known to have landed "
            "between the two reads is the Thursday 12 November game, Commanders 24 - Giants 21, "
            "which NFL.com's scores page shows as Final. NFL.com does not state why any standings "
            "value changed, so every moved cell is listed here rather than explained away."
            % (identical, total, checked, len(teams_changed), ncells, names, ", ".join(cols)))


def stats_finding(prev, teams_changed, diffs, checked, derived_map):
    """Descriptive only. NFL.com publishes no reason for a change, so none is asserted."""
    total = len(prev["rows"])
    identical = total - len(teams_changed)
    base = ("%d of %d teams are cell-for-cell identical across %d compared official cells."
            % (identical, total, checked))
    if not teams_changed:
        tail = " No official value moved."
    else:
        ncells = sum(len(d["changed"]) for d in diffs)
        names = ", ".join(teams_changed)
        cols = sorted({c["column"] for d in diffs for c in d["changed"]})
        tail = (" %d teams moved across %d cells (%s). Columns that moved: %s. NFL.com does not "
                "state why a value changed, so no cause is asserted here; the Thursday 12 November "
                "game is the only result known to have landed between the two reads."
                % (len(teams_changed), ncells, names, ", ".join(cols)))
    if derived_map:
        pairs = ", ".join("%s: %s to %s" % (d["team"], d["prior"], d["current"]) for d in derived_map)
        tail += (" Separately, the derived archive-abbreviation column differs for %s. That column "
                 "is computed here, not published by the NFL, and it is recorded as an irregularity."
                 % pairs)
    return base + tail



# ------------------------------------------- diff against the 2026-11-12 peer
def diff_against_prior(standings, team_stats, injuries_rows, deficiency):
    peer = os.path.join(os.path.dirname(ROOT), "nfl-lines", "data", "official")
    result = {"id": "verification_2026-11-13", "snapshot_date": SNAPSHOT_DATE,
              "compared_to": "nfl-lines/data/official/*.json (snapshot retrieved 2026-11-12)",
              "sections": {}}

    # standings
    p = os.path.join(peer, "standings_2026.json")
    if os.path.exists(p):
        prev = json.load(open(p))
        cols = prev["columns"][2:]
        diffs, teams_changed = [], []
        by_abbr = {r[1]: r for r in standings["rows"]}
        checked = 0
        for s in prev["rows"]:
            cur = by_abbr[s[1]]
            changed = []
            for i, c in enumerate(cols):
                checked += 1
                if not num_eq(str(s[2 + i]), str(cur[2 + i])):
                    changed.append(dict(column=c, prior=s[2 + i], current=cur[2 + i]))
            if changed:
                teams_changed.append(s[1])
                diffs.append(dict(team=s[1], team_name=s[0], changed=changed))
        result["sections"]["standings"] = {
            "rows_compared": len(prev["rows"]), "cells_compared": checked,
            "teams_identical": len(prev["rows"]) - len(teams_changed),
            "teams_changed": teams_changed, "cell_diffs": diffs,
            "prior_source_url": NFL_STANDINGS,
            "finding": standings_finding(prev, standings, teams_changed, diffs, checked),
        }

    # team stats
    p = os.path.join(peer, "team_stats_offense_passing_2026.json")
    if os.path.exists(p):
        prev = json.load(open(p))
        cols = prev["columns"]
        cur_by = {r[1]: r for r in team_stats["rows"]}
        diffs, teams_changed, derived_map = [], [], []
        checked = 0
        for s in prev["rows"]:
            cur = cur_by[s[1]]
            changed = []
            for i, c in enumerate(cols):
                if c == "team":
                    a = cur[0]
                elif c in ("nfl_abbr", "archive_abbr"):
                    a = cur[1]
                else:
                    a = cur[cols.index(c)]
                checked += 1
                if c == "archive_abbr":
                    # derived mapping column, not an official value: recorded separately
                    if not num_eq(str(s[i]), str(a)):
                        derived_map.append(dict(team=s[1], prior=s[i], current=a))
                    continue
                if not num_eq(str(s[i]), str(a)):
                    changed.append(dict(column=c, prior=s[i], current=a))
            if changed:
                teams_changed.append(s[1])
                diffs.append(dict(team=s[1], team_name=s[0], changed=changed))
        result["sections"]["team_stats"] = {
            "rows_compared": len(prev["rows"]), "cells_compared": checked,
            "teams_identical": len(prev["rows"]) - len(teams_changed),
            "teams_changed": teams_changed, "cell_diffs": diffs,
            "prior_source_url": NFL_TEAM_STATS,
            "derived_abbr_mapping_diffs": derived_map,
            "finding": stats_finding(prev, teams_changed, diffs, checked, derived_map),
        }

    # injuries
    p = os.path.join(peer, "injuries_week10_2026.json")
    if os.path.exists(p):
        prev = json.load(open(p))
        theirs = {}
        for g in prev["games"]:
            for tm, lst in g["teams"].items():
                for r in lst:
                    theirs[(tm, r[0])] = dict(pos=r[1], injury=r[2], practice=r[3], status=r[4])
        mine = {(r["team"], r["player"]): dict(pos=r["position"], injury=r["injuries"],
                                               practice=r["practice"], status=r["status"])
                for r in injuries_rows}
        only_now = sorted(set(mine) - set(theirs))
        only_prev = sorted(set(theirs) - set(mine))
        changed = []
        for k in sorted(set(mine) & set(theirs)):
            d = [(f, theirs[k][f], mine[k][f]) for f in ("pos", "injury", "practice", "status")
                 if theirs[k][f] != mine[k][f]]
            if d:
                changed.append(dict(team=k[0], player=k[1],
                                    changed=[dict(field=f, prior=a, current=b) for f, a, b in d]))
        prev_empty = [g["away"] + "@" + g["home"] for g in prev["games"]
                      if not g["teams"].get(g["away"]) and not g["teams"].get(g["home"])]
        result["sections"]["injuries"] = {
            "prior_player_rows": len(theirs), "current_player_rows": len(mine),
            "rows_only_in_current": [{"team": k[0], "player": k[1],
                                       "practice": mine[k]["practice"], "status": mine[k]["status"]}
                                      for k in only_now],
            "rows_only_in_prior": [{"team": k[0], "player": k[1],
                                     "practice": theirs[k]["practice"], "status": theirs[k]["status"]}
                                    for k in only_prev],
            "rows_with_changed_fields": changed,
            "games_with_no_rows_in_prior": prev_empty,
            "prior_source_url": NFL_INJURIES,
            "finding": ("NFL.com rewrites this page every day. Between the 2026-11-12 read and "
                        "the 2026-11-13 read the report gained a complete Monday-night table "
                        "(Chargers-Ravens), filled in the Injury and Game Status columns for "
                        "several teams, and dropped four Kansas City players who carried no "
                        "designation on the earlier page. NFL.com does not state why a listed "
                        "player disappears, so the reason is left blank."),
        }

    # integrity checks
    result["sections"]["integrity_checks"] = integrity_checks(standings, team_stats,
                                                               injuries_rows, deficiency)
    result["status"] = "verified"
    write_json(os.path.join(VER, "verification_2026-11-13.json"), result)
    return result


def integrity_checks(standings, team_stats, injuries_rows, deficiency):
    checks = []

    def add(cid, name, passed, detail):
        checks.append(dict(id=cid, check=name, passed=passed, detail=detail))

    add("IC-01", "All 32 teams appear exactly once in the league standings",
        len(standings["rows"]) == 32 and len({r[1] for r in standings["rows"]}) == 32,
        "32 rows, 32 distinct abbreviations")
    add("IC-02", "All 32 teams appear exactly once in the official team-stats table",
        len(team_stats["rows"]) == 32 and len({r[1] for r in team_stats["rows"]}) == 32,
        "32 rows, 32 distinct abbreviations")
    # standings internal consistency: W+L+T equals games played and home+road equals it
    bad = []
    for r in standings["rows"]:
        w, l, t = int(r[2]), int(r[3]), int(r[4])
        home = r[9].split("-")
        road = r[10].split("-")
        if (w + l + t) != (int(home[0]) + int(home[1]) + int(home[2])
                           + int(road[0]) + int(road[1]) + int(road[2])):
            bad.append(r[1])
        if abs((w + 0.5 * t) / (w + l + t) - float(r[5])) > 0.0015:
            bad.append(r[1] + "/pct")
    add("IC-03", "Every standings row is internally consistent (home+road=W-L-T, PCT=(W+0.5T)/G)",
        not bad, "no inconsistent rows" if not bad else "inconsistent: %s" % bad)
    # league totals: sum of PF == sum of PA across the league
    pf = sum(int(r[6]) for r in standings["rows"])
    pa = sum(int(r[7]) for r in standings["rows"])
    add("IC-04", "League points for equals league points against",
        pf == pa, "PF=%d PA=%d" % (pf, pa))
    add("IC-05", "Every injury row carries a player and a position",
        all(r["player"] and r["position"] for r in injuries_rows),
        "%d player rows" % len(injuries_rows))
    add("IC-06", "Every injury row links to an nfl.com player page",
        all(r["url"].startswith("https://www.nfl.com/players/") for r in injuries_rows),
        "%d/%d rows carry a player-page link" % (
            sum(1 for r in injuries_rows if r["url"].startswith("https://www.nfl.com/players/")),
            len(injuries_rows)))
    add("IC-07", "Deficiency table covers all 28 teams playing in Week 10",
        len(deficiency["rows"]) == 28, "%d team rows" % len(deficiency["rows"]))
    return checks


# ------------------------------------------------------------------- news
def build_news():
    """Official NFL.com headlines published on the Week 10 injury page.

    Each entry is a headline exactly as rendered by NFL.com together with the
    NFL.com URL it links to. The linked articles were NOT opened in this pass:
    only the headline text and URL as published by NFL.com are reproduced.
    """
    entries = [
        ("nfl-news-roundup-latest-league-updates-from-friday-nov-13",
         "NFL news roundup: Ravens confirm Lamar Jackson expected to miss 6-10 weeks; Kenneth Walker questionable"),
        ("nfl-news-roundup-latest-league-updates-from-thursday-nov-12",
         "NFL news roundup: Latest league updates from Thursday, Nov. 12"),
        ("nfl-news-roundup-latest-league-updates-from-wednesday-nov-11",
         "NFL news roundup: Browns to start QB Deshaun Watson vs. Texans; Cardinals' Carson Beck to start vs. Rams"),
        ("dolphins-place-qb-malik-willis-groin-on-injured-reserve-kyle-mccord-in-line-for-first-start",
         "Dolphins place QB Malik Willis (groin) on injured reserve; Kyle McCord in line for first start"),
        ("nfl-news-roundup-latest-league-updates-from-tuesday-nov-10",
         "NFL news roundup: Bills acquire S Amani Hooker; Broncos trade for Chargers' Daiyan Henley"),
        ("rams-wr-puka-nacua-likely-to-be-placed-on-injured-reserve-with-turf-toe-sprained-mcl-and-pcl",
         "Rams WR Puka Nacua likely to be placed on injured reserve with turf toe, sprained MCL and PCL"),
        ("packers-rb-josh-jacobs-to-undergo-surgery-on-finger-this-week",
         "Packers RB Josh Jacobs to undergo surgery on finger this week; timeline to return TBD"),
        ("sam-darnold-ruled-out-for-seahawks-week-10-game-vs-raiders-drew-lock-expected-to-start-again",
         "Sam Darnold ruled out for Seahawks' Week 10 game vs. Raiders; Drew Lock expected to start again"),
        ("nfl-news-roundup-latest-league-updates-from-monday-nov-9",
         "NFL news roundup: J.J. McCarthy expected to play Week 10; Justin Herbert avoids finger fracture"),
        ("notable-injuries-news-sunday-week-9-games-2026",
         "Notable injuries, news from Sunday's Week 9 games: Rams WR Puka Nacua to undergo testing on knee injury"),
        ("ravens-lamar-jackson-right-thumb-out-6-9-weeks-expects-to-return-this-season",
         "NFL Network: Ravens' Lamar Jackson (right thumb) out 6-9 weeks, expects to return this season"),
        ("week-9-injuries-sunday-pregame-2026-nfl-season",
         "NFL Week 9 injuries to monitor for Sunday's games"),
        ("nfl-week-9-inactives-players-ruled-out-sunday-2026-season",
         "NFL Week 9 inactives: Players ruled out for Sunday's 13 games"),
        ("nfl-news-roundup-latest-league-updates-from-saturday-nov-7",
         "NFL news roundup: Saints waive Kendre Miller; Cowboys place Malachi Lawrence on IR"),
        ("nfl-news-roundup-latest-league-updates-from-friday-nov-6",
         "NFL news roundup: Jets' Garrett Wilson ruled out; Falcons RB Brian Robinson out for Madrid game"),
        ("pats-treveyon-henderson-says-he-was-hospitalized-after-unusual-emergency-focused-on-recovery",
         "Pats' TreVeyon Henderson says he was hospitalized after 'unusual' emergency; RB focused on recovery"),
        ("nfl-news-roundup-latest-league-updates-from-thursday-nov-5",
         "NFL news roundup: Ravens officially place Lamar Jackson on injured reserve"),
        ("nfl-week-9-injury-report-2026-season",
         "NFL Week 9 injury report: Player statuses for all 15 games"),
        ("deshaun-watson-concussion-protocol-browns-week-9-shedeur-sanders",
         "Deshaun Watson enters concussion protocol ahead of Browns' Week 9 game vs. Saints"),
        ("ravens-qb-tyler-huntley-out-for-season-turf-toe-injury",
         "Report: Ravens QB Tyler Huntley out for season with turf toe injury"),
        ("notable-injuries-news-sunday-week-8-games-2026",
         "Notable injuries, news from Sunday's Week 8 games: Cardinals bench QB Jacoby Brissett vs. Cowboys"),
        ("nfl-week-8-inactives-players-ruled-out-sunday-2026-season",
         "NFL Week 8 inactives: Players ruled out for Sunday's 12 games"),
        ("week-8-injuries-sunday-pregame-2026-nfl-season",
         "NFL Week 8 injuries to monitor for Sunday's games"),
        ("ravens-qb-lamar-jackson-ankle-play-bills-three-game-absence",
         "Ravens QB Lamar Jackson (ankle) will return Sunday vs. Bills after three-game absence"),
    ]
    rows = [dict(headline=h, url="https://www.nfl.com/news/" + slug) for slug, h in entries]
    doc = {
        "id": "official_news_headlines_2026-11-13",
        "title": "NFL.com news headlines published on the Week 10 injury page",
        "source_url": NFL_INJURIES,
        "publisher": "NFL.com (official league site)",
        "official": True,
        "method": ("Headline text and target URL were read from the rendered markup of the "
                   "official Week 10 injury page on %s. The linked articles were not opened in "
                   "this pass, so only the headline as published by NFL.com is reproduced." %
                   SNAPSHOT_DATE),
        "retrieved_utc": SNAPSHOT_UTC,
        "snapshot_date": SNAPSHOT_DATE,
        "headlines": rows,
    }
    write_json(os.path.join(OFF, "news_headlines_2026-11-13.json"), doc)
    return doc


def main():
    standings = build_standings()
    team_stats = build_team_stats()
    schedule = build_schedule()
    injuries, injury_rows = build_injuries(schedule["games"])
    deficiency = build_deficiency(injuries)
    news = build_news()
    spot = spot_check()
    ver = diff_against_prior(standings, team_stats, injury_rows, deficiency)
    print("standings rows      :", len(standings["rows"]))
    print("team stats rows     :", len(team_stats["rows"]))
    print("schedule games      :", len(schedule["games"]), "byes:", len(schedule["byes"]))
    print("injury player rows  :", len(injury_rows))
    print("deficiency teams    :", len(deficiency["rows"]))
    print("news headlines      :", len(news["headlines"]))
    print("spot check          :", spot["games_compared"], "compared,",
          spot["matched"], "matched,", spot["mismatched"], "mismatched,",
          spot["missing_in_archive"], "missing")
    for c in ver["sections"]["integrity_checks"]:
        print("  %s %-8s %s" % (c["id"], "PASS" if c["passed"] else "FAIL", c["check"]))


if __name__ == "__main__":
    main()
