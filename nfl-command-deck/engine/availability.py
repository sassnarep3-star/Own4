#!/usr/bin/env python3
"""
nfl-command-deck — availability evidence builder.

Two official captures, joined without inference:

  A. nfl-readiness-register/snapshots/2026-11-18/injury_report-2026-11-18T234917Z.html
     source https://www.nfl.com/injuries/ , captured 2026-11-18T23:49:17Z
     SHA-256 pinned in that namespace's manifest and re-checked here.
  B. nfl-depth-sweep/data/depth_register.json
     32 club depth charts captured 2026-11-17, one official club URL per club.

What the join can say:  a player the club lists at depth rank 1 who carries a game
designation in the official report, and who the club itself lists next in that slot.

What it cannot say (and therefore leaves blank):  who actually started, who was inactive,
how many snaps the replacement played. No official inactive list or snap-count source is
held for Week 11 (see flags RF-05, RF-06). Nothing here is inferred from jersey order.

Writes: data/availability.json, data/injury_rows.json
Pure standard library.
"""

import hashlib
import json
import os
import re
import unicodedata
from html import unescape

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)
DATA = os.path.join(NS, "data")

CAP = os.path.join(ROOT, "nfl-readiness-register", "snapshots", "2026-11-18",
                   "injury_report-2026-11-18T234917Z.html")
CAP_SHA = "e1bbea1bf036c949825106a9a9e51de307da86680583d201a091682d7d012e7b"
CAP_URL = "https://www.nfl.com/injuries/"
CAP_UTC = "2026-11-18T23:49:17Z"
DEPTH = os.path.join(ROOT, "nfl-depth-sweep", "data", "depth_register.json")

CLUB_BY_NAME = {
    "Cardinals": "ARI", "Falcons": "ATL", "Ravens": "BAL", "Bills": "BUF", "Panthers": "CAR",
    "Bears": "CHI", "Bengals": "CIN", "Browns": "CLE", "Cowboys": "DAL", "Broncos": "DEN",
    "Lions": "DET", "Packers": "GB", "Texans": "HOU", "Colts": "IND", "Jaguars": "JAX",
    "Chiefs": "KC", "Chargers": "LAC", "Rams": "LAR", "Raiders": "LV", "Dolphins": "MIA",
    "Vikings": "MIN", "Patriots": "NE", "Saints": "NO", "Giants": "NYG", "Jets": "NYJ",
    "Eagles": "PHI", "Steelers": "PIT", "49ers": "SF", "Seahawks": "SEA", "Buccaneers": "TB",
    "Titans": "TEN", "Commanders": "WAS",
}


def norm(s):
    s = unicodedata.normalize("NFKD", unescape(s or "")).encode("ascii", "ignore").decode()
    s = s.lower().replace(".", " ").replace("'", " ").replace("-", " ")
    s = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def strip_tags(s):
    return unescape(re.sub(r"<[^>]+>", "", s)).strip()


def parse_capture():
    raw = open(CAP, "rb").read()
    digest = hashlib.sha256(raw).hexdigest()
    s = raw.decode("utf-8", errors="replace")
    week_label = (re.findall(r"Injuries - (WEEK \d+)", s) or [None])[0]

    sections = re.split(r'<div class="nfl-t-stats__title">', s)[1:]
    rows, section_report = [], []
    for sec in sections:
        m = re.search(r'd3-o-section-sub-title"><span>([^<]*)</span>', sec)
        team_full = strip_tags(m.group(1)) if m else ""
        club = CLUB_BY_NAME.get(team_full, "")
        t = sec.find("<table")
        chunk = sec[t:sec.find("</table>", t)] if t >= 0 else ""
        n = 0
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", chunk, re.S):
            cells = [strip_tags(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            if not cells:
                continue
            # the table is 5 columns: Player | Position | Injuries | Practice | Game status
            cells += [""] * (5 - len(cells))
            player, pos, injury, practice, game = cells[:5]
            if not player:
                continue
            rows.append({
                "club": club, "club_name": team_full, "player": player, "position": pos,
                "injury": injury, "practice_status": practice,
                "game_status": game if game in ("Out", "Doubtful", "Questionable") else "",
                "game_status_raw": game,
            })
            n += 1
        section_report.append({"club": club, "club_name": team_full, "rows": n,
                               "source_url": "https://www.nfl.com/injuries/"})
    return {"sha256": digest, "week_label": week_label, "rows": rows,
            "sections": section_report}


def depth_slots():
    d = json.load(open(DEPTH, encoding="utf-8"))
    out = {}
    for c in d["clubs"]:
        for p in c.get("positions", []):
            r1, r2, r3 = p.get("rank1") or {}, p.get("rank2") or {}, p.get("rank3") or {}
            names1 = [n for n in (r1.get("name"), r1.get("alt")) if n]
            out.setdefault(c["club"], []).append({
                "position": p["position"], "rank1": names1,
                "rank2": r2.get("name") or "", "rank3": r3.get("name") or "",
                "source_url": c["source_url"], "snapshot_date": c["snapshot_date"],
            })
    return out


def main():
    cap = parse_capture()
    if cap["sha256"] != CAP_SHA:
        raise SystemExit("capture hash mismatch: the committed file changed under the parse")
    slots = depth_slots()

    rows = cap["rows"]
    statuses = {}
    for r in rows:
        statuses.setdefault(r["club"], {"rows": 0, "Out": 0, "Questionable": 0, "Doubtful": 0,
                                        "no_game_status": 0, "no_practice_status": 0})
        st = statuses[r["club"]]
        st["rows"] += 1
        if r["game_status"]:
            st[r["game_status"]] += 1
        else:
            st["no_game_status"] += 1
        if not r["practice_status"]:
            st["no_practice_status"] += 1

    # join on (club, normalized player name) against rank 1 of each club's own chart
    by_club1 = {}
    for club, sl in slots.items():
        for s in sl:
            for nm in s["rank1"]:
                by_club1[(club, norm(nm))] = s
    depth_hits = []
    for r in rows:
        s = by_club1.get((r["club"], norm(r["player"])))
        if not s:
            continue
        depth_hits.append({
            "club": r["club"], "player": r["player"], "position_on_report": r["position"],
            "depth_position": s["position"], "game_status": r["game_status"] or "(blank)",
            "practice_status": r["practice_status"],
            "club_lists_next": s["rank2"], "club_lists_third": s["rank3"],
            "replacement_named_by_club": bool(s["rank2"]),
            "report_url": CAP_URL, "depth_source_url": s["source_url"],
            "snapshot_date": s["snapshot_date"],
        })

    starters_out = [h for h in depth_hits if h["game_status"] == "Out"]
    starters_q = [h for h in depth_hits if h["game_status"] == "Questionable"]

    per_team = []
    for club in sorted(statuses):
        sl = slots.get(club, [])
        one_deep = [s for s in sl if not s["rank2"]]
        per_team.append({
            "club": club,
            **statuses[club],
            "depth_slots": len(sl),
            "depth_slots_with_no_second_name": len(one_deep),
            "rank1_players_on_report": sum(1 for h in depth_hits if h["club"] == club),
            "rank1_players_out": sum(1 for h in starters_out if h["club"] == club),
            "rank1_players_questionable": sum(1 for h in starters_q if h["club"] == club),
            "named_next_on_chart_for_out_players": sum(
                1 for h in starters_out if h["club"] == club and h["replacement_named_by_club"]),
            "source_url": CAP_URL,
            "depth_source_url": sl[0]["source_url"] if sl else "",
            "actual_starter": "",
            "actual_starter_blank_reason": "no official inactive list or snap count is held for "
                                           "Week 11; a starter cannot be confirmed, only suspected",
        })

    out = {
        "dataset": "nfl_command_deck_availability",
        "title": "Week 11 official designations joined to each club's own depth chart",
        "built_utc": "2026-11-19",
        "session": "arena/1153eb96-own4",
        "capture": {"url": CAP_URL, "captured_utc": CAP_UTC, "sha256": cap["sha256"],
                    "week_label": cap["week_label"],
                    "path": "nfl-readiness-register/snapshots/2026-11-18/"
                            "injury_report-2026-11-18T234917Z.html"},
        "depth_register": {"path": "nfl-depth-sweep/data/depth_register.json",
                           "snapshot_date": "2026-11-17",
                           "clubs": len(slots), "verified_text_clubs": 31,
                           "flagged_clubs": ["HOU"]},
        "counts": {
            "clubs_in_report": len(cap["sections"]),
            "player_rows": len(rows),
            "rows_with_game_status": sum(1 for r in rows if r["game_status"]),
            "rows_without_game_status": sum(1 for r in rows if not r["game_status"]),
            "rows_without_practice_status": sum(1 for r in rows if not r["practice_status"]),
            "Out": sum(1 for r in rows if r["game_status"] == "Out"),
            "Questionable": sum(1 for r in rows if r["game_status"] == "Questionable"),
            "Doubtful": sum(1 for r in rows if r["game_status"] == "Doubtful"),
            "rank1_players_on_report": len(depth_hits),
            "rank1_players_out": len(starters_out),
            "rank1_players_questionable": len(starters_q),
            "out_players_with_a_named_next_man": sum(
                1 for h in starters_out if h["replacement_named_by_club"]),
        },
        "per_team": per_team,
        "starters_out_detail": starters_out,
        "starters_questionable_detail": starters_q,
        "limits": [
            "One capture (2026-11-18T23:49:17Z). The Week 11 report is a series that runs "
            "Wednesday to kickoff; a single read cannot show a designation moving.",
            "The report's game status may be blank mid-week even for a player later ruled out; a "
            "blank is published as blank, not as 'available'.",
            "No inactive list and no snap count are held, so 'the backup replaced the starter' "
            "cannot be confirmed from these sources. The chart's next name is what the club "
            "publishes, not evidence of who played.",
            "The depth snapshot (2026-11-17) and the report capture (2026-11-18) are one day "
            "apart; a roster move in that window would not appear in both.",
        ],
    }
    json.dump(out, open(os.path.join(DATA, "availability.json"), "w", encoding="utf-8"),
              indent=1, sort_keys=True)
    json.dump({"capture": out["capture"], "rows": rows},
              open(os.path.join(DATA, "injury_rows.json"), "w", encoding="utf-8"),
              indent=1, sort_keys=True)

    c = out["counts"]
    print("clubs %d  rows %d  Out %d  Questionable %d  Doubtful %d  no-status %d"
          % (c["clubs_in_report"], c["player_rows"], c["Out"], c["Questionable"],
             c["Doubtful"], c["rows_without_game_status"]))
    print("rank-1 chart players appearing on the report: %d  (Out %d, Questionable %d, "
          "with a named next man %d)"
          % (c["rank1_players_on_report"], c["rank1_players_out"], c["rank1_players_questionable"],
             c["out_players_with_a_named_next_man"]))


if __name__ == "__main__":
    main()
