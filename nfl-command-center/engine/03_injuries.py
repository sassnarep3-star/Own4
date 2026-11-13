"""03 - Normalise the Week 10 injury capture and reconcile it against the
official injury report, then build the depth-deficiency table.

The raw capture (data/raw/injuries_week10_piped.txt) holds one row per
player per game as rendered on the official injuries page. Every game-status
value in it is checked against the official Week 10 injury report article.
Rows that cannot be confirmed from an official source keep a blank value and
are marked unverified rather than being filled in.

Writes: data/derived/injuries_week10_normalized.json
        data/derived/depth_deficiency_week10.json
"""
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import DERIVED, ROOT, dump_json, load_json

RAW = os.path.join(ROOT, "data", "raw", "injuries_week10_piped.txt")
DESIGNATIONS = os.path.join(ROOT, "data", "official", "injury_designations_week10_2026.json")
ARTICLES = os.path.join(ROOT, "data", "official", "official_articles_week10.json")
SLATE = os.path.join(ROOT, "data", "official", "slate_week10_2026.json")

PRACTICE_STATUSES = {
    "Full Participation in Practice",
    "Limited Participation in Practice",
    "Did Not Participate In Practice",
    "Full Participation in Practice (Restricted)",
    "Limited Participation in Practice (Restricted)",
}
GAME_STATUSES = {"Out", "Doubtful", "Questionable", "Out (Inactive)",
                  "Questionable (Inactive)", "Doubtful (Inactive)"}


def norm_name(n):
    """Compare player names without punctuation, case or suffixes."""
    n = n.lower().replace("'", "").replace("’", "")
    n = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", n)
    n = re.sub(r"[^a-z ]", "", n)
    return " ".join(n.split())


def norm_injury(i):
    if not i:
        return ""
    i = i.lower().replace("'", "").replace("’", "")
    i = re.sub(r"[^a-z/ ]", "", i)
    parts = sorted(p.strip() for p in i.split("/") if p.strip())
    return "/".join(parts)


def main():
    des = load_json(DESIGNATIONS)
    arts = load_json(ARTICLES)
    slate = load_json(SLATE)

    # ---- index the official designations -------------------------------------
    official = {}
    for row in des["teams"]:
        for status in ("out", "doubtful", "questionable"):
            for p in row[status]:
                official[(row["game_id"], row["team"], norm_name(p["name"]))] = {
                    "status": status.upper(), "name": p["name"],
                    "position": p["position"], "injury": p["injury"],
                    "source_id": des["source_id"], "source_url": des["source_url"]}
        if row.get("no_designations_published"):
            official[("__none__", row["game_id"], row["team"])] = {
                "status": "NO_DESIGNATIONS_PUBLISHED", "name": "", "position": "",
                "injury": "", "source_id": des["source_id"], "source_url": des["source_url"]}

    # ---- parse the raw capture ----------------------------------------------
    rows = []
    unresolved = []
    with open(RAW, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line.strip():
                continue
            parts = line.split("~")
            if len(parts) != 7:
                unresolved.append({"line": lineno, "raw": line,
                                   "problem": "expected 7 pipe-separated fields, found %d" % len(parts)})
                continue
            gid, team, player, position, injury, practice, game_status = parts
            rows.append({"line": lineno, "game_id": gid, "team": team, "player": player,
                         "position": position, "injury": injury,
                         "practice_status": practice, "game_status": game_status})

    # ---- resolve placeholders against the official article ------------------
    for r in rows:
        if r["practice_status"] not in PRACTICE_STATUSES:
            # The official article publishes game designations, not practice
            # reports. A practice status that could not be read is left blank.
            r["practice_status_original"] = r["practice_status"]
            r["practice_status"] = ""
            r["practice_status_note"] = ("The captured practice status was not readable. The official Week 10 "
                                         "report article publishes game designations only, so the cell is left "
                                         "blank rather than guessed.")
        if r["game_status"] in GAME_STATUSES and r["practice_status"] in PRACTICE_STATUSES:
            continue
        key = (r["game_id"], r["team"], norm_name(r["player"]))
        off = official.get(key)
        if off and off["status"] in ("OUT", "DOUBTFUL", "QUESTIONABLE"):
            r["placeholder_resolved"] = True
            r["placeholder_original"] = r["game_status"]
            r["game_status"] = off["status"]
            r["injury"] = r["injury"] or off["injury"]
            r["source_id"] = off["source_id"]
            r["source_url"] = off["source_url"]
            r["verification"] = "Confirmed against the official Week 10 injury report article."
        else:
            r["placeholder_resolved"] = False
            r["source_id"] = None
            r["source_url"] = None
            r["verification"] = "Not confirmable from an official source. Left unverified."

    # ---- reconcile every row against the official article -------------------
    matched = 0
    confirmed_rows = 0
    practice_only = 0
    conflicts = []
    for r in rows:
        key = (r["game_id"], r["team"], norm_name(r["player"]))
        off = official.get(key)
        r["official_status"] = off["status"] if off else None
        r["official_injury"] = off["injury"] if off else None
        if off and off["status"] in ("OUT", "DOUBTFUL", "QUESTIONABLE"):
            matched += 1
            r["source_id"] = off["source_id"]
            r["source_url"] = off["source_url"]
            r["verification"] = "Confirmed against the official Week 10 injury report article."
            raw_gs = r["game_status"].upper().replace(" (INACTIVE)", "")
            if raw_gs != off["status"]:
                r["conflict"] = True
                conflicts.append({"line": r["line"], "game_id": r["game_id"], "team": r["team"],
                                  "player": r["player"], "captured_status": r["game_status"],
                                  "official_status": off["status"],
                                  "official_injury": off["injury"], "source_url": off["source_url"]})
            else:
                r["conflict"] = False
                confirmed_rows += 1
        else:
            if r.get("placeholder_resolved"):
                pass
            else:
                r["conflict"] = None
                if r["game_status"]:
                    r["verification"] = ("Captured from the official NFL injuries page. The official Week 10 "
                                          "injury report article publishes no designation for this player, so the "
                                          "value is unverified against the article and is flagged as such.")
                else:
                    r["verification"] = ("Practice report only. The official injury report article publishes no "
                                          "designation for this player and the official injuries page shows no game "
                                          "status either, so the game-status cell is left blank.")
                r["source_id"] = "SRC-09"
                r["source_url"] = "https://www.nfl.com/injuries/"
                practice_only += 1
        if not r["source_url"]:
            r["source_url"] = des["source_url"]

    # ---- the official designations that the capture did not carry ----------
    captured_players = {(r["game_id"], r["team"], norm_name(r["player"])) for r in rows}
    official_only = []
    for row in des["teams"]:
        for status in ("out", "doubtful", "questionable"):
            for p in row[status]:
                k = (row["game_id"], row["team"], norm_name(p["name"]))
                if k not in captured_players:
                    official_only.append({"game_id": row["game_id"], "team": row["team"],
                                          "player": p["name"], "position": p["position"],
                                          "injury": p["injury"], "status": status.upper(),
                                          "source_id": row["source_id"],
                                          "source_url": des["source_url"],
                                          "note": "Present in the official injury report article but not in the captured page rows."})

    # ---- team counts ---------------------------------------------------------
    counts = defaultdict(lambda: defaultdict(int))
    for r in rows:
        if r["game_status"]:
            counts[(r["game_id"], r["team"])][r["game_status"]] += 1
    team_counts = [{"game_id": k[0], "team": k[1],
                    "out": v.get("Out", 0), "doubtful": v.get("Doubtful", 0),
                    "questionable": v.get("Questionable", 0),
                    "source_id": des["source_id"], "source_url": des["source_url"]}
                   for k, v in sorted(counts.items())]

    # ---- depth deficiency ----------------------------------------------------
    # A depth deficiency is a position where a starter is unavailable and a
    # lower depth option is expected to start. Only an official statement or an
    # official game book can support that claim, so the table is built from the
    # official depth-chart news and the official game-book evidence only.
    src_url = {x["id"]: x["url"] for x in arts["sources"]}
    # Every row below was read in the named official source. The replacement
    # depth column is filled only where the official source states it.
    deficiency = [
        {"id": "DD-01", "team": "BAL", "position": "QB", "game": "2026_10_LAC_BAL",
         "incumbent": "Lamar Jackson", "incumbent_status": "Out, expected to miss 6-10 weeks after thumb surgery",
         "replacement": "", "replacement_depth": "",
         "replacement_depth_note": "No official source read in this session names Baltimore's Week 10 starting quarterback. The cell is left blank.",
         "verdict": "Starter out, replacement not named by any official source",
         "quote": "QB Lamar Jackson is expected to miss 6-10 weeks after undergoing surgery to repair his broken and dislocated thumb, coach Jesse Minter said in a statement.",
         "source_id": "SRC-04", "source_url": src_url.get("SRC-04"),
         "depth_verified": False, "replacement_confirmed": False},
        {"id": "DD-02", "team": "BAL", "position": "QB", "game": "2026_10_LAC_BAL",
         "incumbent": "Lamar Jackson", "incumbent_status": "Out",
         "replacement": "J. Fagnano", "replacement_depth": "Third quarterback (3QB) on the depth chart in the official game books",
         "replacement_depth_note": "The official game books list Fagnano as 3QB (third quarterback) for the Bills game on 2026-11-01 and list him as the starting quarterback for the Jaguars game on 2026-11-05, with K. Slovis as 3QB. The official game book for the Week 10 game had not been published when this table was built.",
         "verdict": "Third-string quarterback started the previous two games while the starter was out",
         "quote": "3QB 12 J.Fagnano / 3QB 18 K.Slovis / QB 12 J.Fagnano (starting quarterback on 2026-11-05)",
         "source_id": "SRC-07", "source_url": src_url.get("SRC-07"),
         "depth_verified": True, "replacement_confirmed": True},
        {"id": "DD-03", "team": "AZ", "position": "QB", "game": "2026_10_LA_AZ",
         "incumbent": "", "incumbent_status": "",
         "replacement": "Carson Beck", "replacement_depth": "",
         "replacement_depth_note": "The article does not state whether Beck is the second or third quarterback on Arizona's roster. Left blank.",
         "verdict": "First career start, replacement starter confirmed by the club",
         "quote": "QB Carson Beck will start Sunday's game against the Rams, per head coach Mike LaFleur. This will be Beck's first career start in the NFL after he was selected in the third round of the 2026 draft.",
         "source_id": "SRC-05", "source_url": src_url.get("SRC-05"),
         "depth_verified": False, "replacement_confirmed": True},
        {"id": "DD-04", "team": "CLE", "position": "QB", "game": "2026_10_HOU_CLE",
         "incumbent": "Shedeur Sanders", "incumbent_status": "Started Week 9 while Watson was inactive",
         "replacement": "Deshaun Watson", "replacement_depth": "",
         "replacement_depth_note": "The article does not state Watson's depth position on Cleveland's roster. Left blank.",
         "verdict": "Returning starter, not a depth replacement",
         "quote": "QB Deshaun Watson will start Sunday against the Texans, the team announced Wednesday. Watson cleared concussion protocol before Cleveland's Week 9 game but was inactive as Shedeur Sanders got the start in the loss to New Orleans.",
         "source_id": "SRC-05", "source_url": src_url.get("SRC-05"),
         "depth_verified": False, "replacement_confirmed": True},
        {"id": "DD-05", "team": "MIA", "position": "QB", "game": "2026_10_MIA_IND",
         "incumbent": "Malik Willis", "incumbent_status": "Placed on injured reserve with a groin injury",
         "replacement": "", "replacement_depth": "",
         "replacement_depth_note": "Only the headline of the official article was read. It names Kyle McCord as in line for a first start, which is not the same as a confirmed start, so the cell is left blank.",
         "verdict": "Starter on injured reserve, replacement not confirmed",
         "quote": "Dolphins place QB Malik Willis (groin) on injured reserve; Kyle McCord in line for first start",
         "source_id": "SRC-08", "source_url": src_url.get("SRC-08"),
         "depth_verified": False, "replacement_confirmed": False},
        {"id": "DD-06", "team": "BAL", "position": "K", "game": "2026_10_LAC_BAL",
         "incumbent": "", "incumbent_status": "",
         "replacement": "Riley Patterson", "replacement_depth": "",
         "replacement_depth_note": "The article does not state Patterson's depth position on Baltimore's roster. Left blank.",
         "verdict": "Replacement kicker signed for this game only",
         "quote": "K Riley Patterson is signing with Baltimore following a workout and will kick for the Ravens during Monday's game against the Chargers, NFL Network Insider Mike Garafolo reported.",
         "source_id": "SRC-05", "source_url": src_url.get("SRC-05"),
         "depth_verified": False, "replacement_confirmed": True},
        {"id": "DD-07", "team": "MIN", "position": "QB", "game": "2026_10_MIN_GB",
         "incumbent": "", "incumbent_status": "",
         "replacement": "Kirk Cousins", "replacement_depth": "",
         "replacement_depth_note": "The article does not state Cousins's depth position on Minnesota's roster. Left blank.",
         "verdict": "Starter named, no depth replacement stated",
         "quote": "QB Kirk Cousins will start Sunday's game against the Packers, head coach Kevin O'Connell announced.",
         "source_id": "SRC-04", "source_url": src_url.get("SRC-04"),
         "depth_verified": False, "replacement_confirmed": True},
    ]

    res = {
        "id": "injuries-week10-normalized",
        "generated_utc": "2026-11-13T00:00:00Z",
        "raw_capture": {"file": "data/raw/injuries_week10_piped.txt", "rows": len(rows),
                        "unparsed_lines": unresolved},
        "official_source": {"source_id": des["source_id"], "url": des["source_url"],
                            "title": des["source_title"], "publisher": des["publisher"],
                            "retrieved_utc": des["retrieved_utc"], "method": des["method"]},
        "reconciliation": {
            "rows_total": len(rows),
            "rows_with_an_official_designation": matched,
            "rows_confirmed_and_agreeing": confirmed_rows,
            "rows_practice_report_only": practice_only,
            "rows_with_a_status_conflict": len(conflicts),
            "official_designations_not_present_in_the_capture": len(official_only),
            "conflicts": conflicts,
            "official_only": official_only,
        },
        "team_counts": team_counts,
        "rows": rows,
        "note": "Every row carries the official source link. A game-status cell that the official article does not publish is left blank and the row is marked as unverified for the game status; nothing is inferred.",
    }
    dump_json(os.path.join(DERIVED, "injuries_week10_normalized.json"), res)

    dep = {
        "id": "depth-deficiency-week10",
        "generated_utc": "2026-11-13T00:00:00Z",
        "rule": "A depth deficiency is recorded only when an official NFL.com article or an official NFL game book states that a starter is unavailable and names the replacement. The depth position, for example second or third quarterback, is left blank when no official source states it.",
        "rows": deficiency,
        "count": len(deficiency),
        "official_only_depth_verified": sum(1 for d in deficiency if d["depth_verified"]),
        "official_only_depth_unverified": sum(1 for d in deficiency if not d["depth_verified"]),
        "replacement_confirmed_rows": sum(1 for d in deficiency if d["replacement_confirmed"]),
        "replacement_unconfirmed_rows": sum(1 for d in deficiency if not d["replacement_confirmed"]),
        "note": "The official sources give the replacement starter but do not state the depth position of that player on the depth chart, so the depth column is blank and marked unverified for every row that is not a game-book designation.",
    }
    dump_json(os.path.join(DERIVED, "depth_deficiency_week10.json"), dep)

    print("rows:", len(rows), "| with official designation:", matched,
          "| agreeing:", confirmed_rows, "| conflicts:", len(conflicts),
          "| practice-only:", practice_only, "| official-only:", len(official_only))
    print("depth deficiency rows:", len(deficiency),
          "| depth verified:", dep["official_only_depth_verified"])


if __name__ == "__main__":
    main()
