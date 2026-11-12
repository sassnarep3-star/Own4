"""Turn the official NFL injury report into a defensible unit-deficiency read.

The NFL publishes, for every game, a table of Player / Position / Injury /
Practice Status / Game Status. That is the only official input used here. It does
NOT publish a depth-chart rank, so '2nd / 3rd / 4th string' cannot be filled in from
an official source and is left blank and flagged.
"""
from __future__ import annotations

import dataset as D

OFFENSE_SKILL = {"QB", "RB", "FB", "WR", "TE"}
OFFENSIVE_LINE = {"T", "G", "C", "OL"}
FRONT_SEVEN = {"DE", "DT", "LB", "NT"}
SECONDARY = {"CB", "S", "DB"}
SPECIAL = {"K", "P", "LS"}

GROUPS = [
    ("Offense skill", OFFENSE_SKILL),
    ("Offensive line", OFFENSIVE_LINE),
    ("Front seven", FRONT_SEVEN),
    ("Secondary", SECONDARY),
    ("Special teams", SPECIAL),
]

STATUS_WEIGHT = {"Out": 1.0, "Doubtful": 0.75, "Questionable": 0.35, "": 0.10}
PRACTICE_WEIGHT = {
    "Did Not Participate In Practice": 0.6,
    "Limited Participation in Practice": 0.3,
    "Full Participation in Practice": 0.0,
    "": 0.0,
}


def group_of(pos):
    for name, s in GROUPS:
        if pos in s:
            return name
    return "Unclassified"


def build():
    src = D.load_json(D.OFFICIAL + "/injuries_week10_2026.json")
    teams = {}
    for g in src["games"]:
        for side in ("away", "home"):
            abbr = g[side]
            rows = g["teams"].get(abbr, [])
            counts = {name: {"listed": 0, "out": 0, "doubtful": 0, "questionable": 0,
                             "dnp": 0, "limited": 0, "load": 0.0}
                      for name, _ in GROUPS}
            qb_rows = []
            for player, pos, injury, practice, game_status in rows:
                grp = group_of(pos)
                c = counts.setdefault(grp, {"listed": 0, "out": 0, "doubtful": 0,
                                            "questionable": 0, "dnp": 0, "limited": 0, "load": 0.0})
                c["listed"] += 1
                if game_status == "Out":
                    c["out"] += 1
                elif game_status == "Doubtful":
                    c["doubtful"] += 1
                elif game_status == "Questionable":
                    c["questionable"] += 1
                if practice == "Did Not Participate In Practice":
                    c["dnp"] += 1
                elif practice == "Limited Participation in Practice":
                    c["limited"] += 1
                c["load"] += STATUS_WEIGHT.get(game_status, 0.0) + PRACTICE_WEIGHT.get(practice, 0.0)
                if pos == "QB":
                    qb_rows.append({"player": player, "injury": injury,
                                    "practice": practice, "game_status": game_status})
            listed = sum(c["listed"] for c in counts.values())
            out_n = sum(c["out"] for c in counts.values())
            load = sum(c["load"] for c in counts.values())
            teams[abbr] = {
                "team": abbr,
                "opponent": g["home"] if side == "away" else g["away"],
                "players_listed": listed,
                "ruled_out": out_n,
                "doubtful": sum(c["doubtful"] for c in counts.values()),
                "questionable": sum(c["questionable"] for c in counts.values()),
                "did_not_practice": sum(c["dnp"] for c in counts.values()),
                "limited_practice": sum(c["limited"] for c in counts.values()),
                "deficiency_load": round(load, 2),
                "by_group": {k: v for k, v in counts.items() if v["listed"]},
                "qb_rows": qb_rows,
                "qb_depth_rank": None,
                "qb_depth_rank_source": None,
            }
    return {"source": src, "teams": teams}


def deficiency_table(inj):
    """One row per team-game with the officially derivable deficiency read."""
    rows = []
    for abbr, t in sorted(inj["teams"].items()):
        worst = sorted(t["by_group"].items(), key=lambda kv: -kv[1]["load"])
        rows.append({
            "team": abbr,
            "opponent": t["opponent"],
            "players_listed": t["players_listed"],
            "ruled_out": t["ruled_out"],
            "doubtful": t["doubtful"],
            "questionable": t["questionable"],
            "did_not_practice": t["did_not_practice"],
            "limited_practice": t["limited_practice"],
            "deficiency_load": t["deficiency_load"],
            "most_affected_unit": worst[0][0] if worst else None,
            "most_affected_unit_load": round(worst[0][1]["load"], 2) if worst else None,
            "qbs_on_report": "; ".join(
                "%s (%s, %s)" % (q["player"], q["practice"], q["game_status"] or "no game status")
                for q in t["qb_rows"]) or "none listed",
            "backup_depth_rank_2nd_3rd_4th": None,
        })
    rows.sort(key=lambda r: -r["deficiency_load"])
    return rows
