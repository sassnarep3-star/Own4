"""nfl-markets engine — injury & REPLACEMENT-DEPTH tracker (the user requirement:
"Track the depth of the replacement, not just the fact of a replacement").

INPUTS (both read-only peer captures, provenance in data/sources.json):
- OFFICIAL    : nfl-arena/data/raw/nfl_injuries_week10_2026.md — verbatim capture of
                https://www.nfl.com/injuries/ (Week 10, 2026) made 2026-11-13 by
                session arena/d6c72eb4-own4.
- THIRD-PARTY : nfl-arena/data/raw/espn_depth_week10.json — ESPN (RotoWire) depth
                charts s1-s4 for 8 teams, captured 2026-11-13. NOT published by the
                NFL — every derived value is labelled THIRD-PARTY and flagged.
                Teams without a captured chart keep depth fields BLANK (never inferred).

OUTPUT: one row per depth-chart position slot for the covered teams:
  starter, starter availability marker (third-party), official game status
  (joined from the official report by player+team), the REPLACEMENT (first
  available s2/s3/s4), and the DEPTH OF THE REPLACEMENT (2 / 3 / 4 / NONE)
  plus a team deficiency index with a published, flagged weighting convention.
"""
import json, os, re
from . import config as C

MD = C.os.path.join(C.ROOT, "nfl-arena", "data", "raw", "nfl_injuries_week10_2026.md")
DEPTH = C.os.path.join(C.ROOT, "nfl-arena", "data", "raw", "espn_depth_week10.json")

UNAVAILABLE_MARKERS = {"O", "IR", "OUT"}          # depth-chart availability markers
DEFICIENT_STATUSES = {"Out", "Doubtful", "IR"}     # official game statuses that remove a starter
WEIGHTS = {2: 1.0, 3: 1.5, 4: 2.0, "NONE": 2.5}    # OUR convention, published + flagged

def parse_official_injuries():
    """Returns {team_abbr: [ {player, position, practice_status, game_status} ]}."""
    if not os.path.exists(MD):
        return {}, "missing"
    text = open(MD, encoding="utf-8").read()
    text = text.split("## NFL.com NEWS ITEMS")[0]
    teams = {}
    cur = None
    for line in text.splitlines():
        m = re.match(r"^### ([A-Z]{2,3}) ", line)
        if m:
            continue
        if re.match(r"^## ", line):
            continue
        m2 = re.match(r"^([A-Z]{2,3})$", line.strip())
        if m2:
            cur = m2.group(1)
            teams.setdefault(cur, [])
            continue
        if cur and line.strip().startswith("| ["):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 5 or cells[0] in ("Player", "---"):
                continue
            mname = re.match(r"\[([^\]]+)\]", cells[0])
            name = mname.group(1).strip() if mname else cells[0].strip()
            teams[cur].append({"player": name, "position": cells[1],
                               "injuries": cells[2], "practice_status": cells[3],
                               "game_status": cells[4]})
    return teams, "ok"

def compute():
    official, md_status = parse_official_injuries()
    depth = json.load(open(DEPTH))
    rows = []
    team_summary = {}
    covered = {t["team"]: t for t in depth["teams"]}
    for abbr, chart in covered.items():
        off_rows = official.get(abbr, [])
        off_by_name = {}
        for o in off_rows:
            key = o["player"].strip().lower()
            off_by_name.setdefault(key, o)
        n_out = 0; depth_count = {2: 0, 3: 0, 4: 0, "NONE": 0}; index = 0.0
        for prow in chart["rows"]:
            unit, pos = prow["unit"], prow["pos"]
            s1 = prow.get("s1") or [None, None]
            starter, marker = s1[0], s1[1]
            if starter is None:
                continue
            unavailable = (marker or "").upper() in UNAVAILABLE_MARKERS
            off_status = ""
            off_practice = ""
            hit = off_by_name.get(starter.strip().lower())
            if hit:
                off_status = hit["game_status"] or ""
                off_practice = hit.get("practice_status") or ""
            # replacement = first AVAILABLE player in s2-s4
            replacement = None; rep_depth = None
            for d in (2, 3, 4):
                slot = prow.get(f"s{d}") or [None, None]
                nm, mk = slot[0], slot[1]
                if nm and (mk or "").upper() not in UNAVAILABLE_MARKERS:
                    replacement, rep_depth = nm, d
                    break
            if unavailable:
                deficient = True
                rd = rep_depth if rep_depth is not None else "NONE"
                depth_count[rd] += 1
                pts = WEIGHTS[rd]
                index += pts
                n_out += 1
            else:
                deficient = False
            rows.append({
                "team": abbr, "unit": unit, "position": pos,
                "starter": starter,
                "starter_depth_marker": marker or "",
                "official_game_status": off_status,
                "official_practice_status": off_practice,
                "official_status_source_key": "nfl_injuries" if hit else "",
                "official_status_flag": "" if hit else
                    "player absent from the official Week-10 report capture (status blank — flagged)",
                "official_vs_depth_discrepancy": (
                    "third-party depth marker says unavailable but the official report lists NO final game-status designation"
                    + (f" (official practice status at capture: {off_practice})" if off_practice else "")
                    if (unavailable and not off_status) else ""),
                "replacement": replacement or "",
                "replacement_depth": (rep_depth if (unavailable and rep_depth is not None) else
                                      ("NONE" if unavailable else "")),
                "deficiency_points": round(WEIGHTS[rep_depth if rep_depth is not None else "NONE"], 2) if unavailable else "",
                "depth_source_key": "repo_nfl_arena_depth",
                "depth_source_label": "THIRD-PARTY (ESPN/RotoWire depth chart)",
                "injury_source_label": "OFFICIAL (nfl.com injury report)",
                "flags": ("starter-unavailable; " if unavailable else "") +
                         ("no-official-row" if (unavailable and not hit and off_status == "") else ""),
                "starter_out_row": deficient,
            })
        team_summary[abbr] = {"n_starters_out": n_out,
                              "replacement_depth_counts": {str(k): v for k, v in depth_count.items()},
                              "deficiency_index": round(index, 2),
                              "qb_out": any(r["position"] == "QB" and r["starter_out_row"] for r in rows if r["team"] == abbr),
                              "official_rows_in_report": len(off_rows)}
    # teams with an official report but NO depth chart: depth fields stay blank + flagged
    uncovered = sorted(t for t in official if t not in covered)
    for abbr in uncovered:
        team_summary[abbr] = {"n_starters_out": None,
                              "replacement_depth_counts": None,
                              "deficiency_index": None,
                              "qb_out": None,
                              "official_rows_in_report": len(official.get(abbr, [])),
                              "flag": "no third-party depth chart captured for this team — replacement depth UNVERIFIED (blank, never inferred)"}
    meta = {
        "captured_from": {"official_md": MD.split("Own4/")[-1], "depth_json": DEPTH.split("Own4/")[-1]},
        "official_md_status": md_status,
        "covered_teams": sorted(covered),
        "uncovered_teams_with_official_rows": uncovered,
        "weights_convention": {str(k): v for k, v in WEIGHTS.items()},
        "weights_flag": "weighting is THIS REPO'S convention (not an official number) — published openly, flagged for review",
        "labels": {"injury": "OFFICIAL (nfl.com)", "depth": "THIRD-PARTY (ESPN/RotoWire)"},
    }
    return rows, team_summary, meta
