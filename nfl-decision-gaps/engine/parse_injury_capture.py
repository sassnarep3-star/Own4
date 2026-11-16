#!/usr/bin/env python3
"""Parse the committed verbatim Week-10 injury capture into structured rows.

Input : nfl-arena/data/raw/nfl_injuries_week10_2026.md  (committed in this repo,
        captured 2026-11-13 from https://www.nfl.com/injuries/)
Output: nfl-decision-gaps/data/injury_week10_parsed.json

Pure stdlib, deterministic. Nothing is inferred: a cell the page left blank is
recorded as "" and counted as blank.
"""
import hashlib
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)
SRC = os.path.join(ROOT, "nfl-arena", "data", "raw", "nfl_injuries_week10_2026.md")
OUT = os.path.join(NS, "data", "injury_week10_parsed.json")

text = open(SRC, encoding="utf-8").read()
raw_bytes = open(SRC, "rb").read()

game_re = re.compile(r"^## (.+?) — (.+?) — (.+)$")
match_re = re.compile(r"^### (\S+) (.+?) \((\S+?)\) at (\S+) (.+?) \((\S+?)\)$")
row_re = re.compile(r"^\| \[(.+?)\]\((.+?)\) \| (\S*) \| (.*?) \| (.*?) \| (.*?) \|$")

games = []
cur_game = None
cur_match = None
cur_team = None
team_re = re.compile(r"^(WAS|NYG|NE|DET|KC|ATL|MIN|GB|JAX|TEN|BUF|NYJ|MIA|IND|CAR|NO|HOU|CLE|LAR|AZ|SEA|LV|SF|DAL|PIT|CIN|LAC|BAL)$")

rows = []
for line in text.splitlines():
    line = line.rstrip()
    m = game_re.match(line)
    if m:
        cur_game = {"day": m.group(1), "time": m.group(2), "network": m.group(3),
                    "matches": [], "news": []}
        games.append(cur_game)
        continue
    m = match_re.match(line)
    if m:
        cur_match = {"away": {"abbr": m.group(1), "name": m.group(2), "record": m.group(3)},
                     "home": {"abbr": m.group(4), "name": m.group(5), "record": m.group(6)},
                     "teams": []}
        cur_game["matches"].append(cur_match)
        continue
    if team_re.match(line.strip()) and cur_match is not None:
        cur_team = line.strip()
        cur_match["teams"].append(cur_team)
        continue
    m = row_re.match(line)
    if m and cur_team is not None:
        player, url, pos, injury, practice, status = m.groups()
        rows.append({
            "team": cur_team,
            "player": player.strip(),
            "player_url": url.strip(),
            "position": pos.strip(),
            "injury": injury.strip(),
            "practice_status": practice.strip(),
            "game_status": status.strip(),
        })
        continue
    if line.startswith("- https://www.nfl.com/news/") and cur_game is not None:
        url = line[2:].split(" ", 1)[0]
        rest = line[2:][len(url):].strip()
        label = rest[3:-1] if rest.startswith('— "') and rest.endswith('"') else rest.lstrip("— ").strip()
        cur_game["news"].append({"url": url, "label": label})

n_rows = len(rows)
teams = sorted({r["team"] for r in rows})
prac = {}
stat = {}
for r in rows:
    prac[r["practice_status"] or "(blank)"] = prac.get(r["practice_status"] or "(blank)", 0) + 1
    stat[r["game_status"] or "(blank)"] = stat.get(r["game_status"] or "(blank)", 0) + 1

per_team = {}
for r in rows:
    t = per_team.setdefault(r["team"], {"rows": 0, "out": 0, "questionable": 0,
                                        "doubtful": 0, "blank_status": 0,
                                        "dnp": 0, "limited": 0, "full": 0})
    t["rows"] += 1
    gs = r["game_status"]
    if gs == "Out":
        t["out"] += 1
    elif gs == "Questionable":
        t["questionable"] += 1
    elif gs == "Doubtful":
        t["doubtful"] += 1
    elif gs == "":
        t["blank_status"] += 1
    ps = r["practice_status"]
    if ps.startswith("Did Not"):
        t["dnp"] += 1
    elif ps.startswith("Limited"):
        t["limited"] += 1
    elif ps.startswith("Full"):
        t["full"] += 1

out = {
    "source_file": os.path.relpath(SRC, ROOT),
    "source_url": "https://www.nfl.com/injuries/",
    "page_title": "Official Latest NFL Injury Report for Players - Week 10 of the 2026 Season | NFL.com",
    "captured": "2026-11-13",
    "sha256": hashlib.sha256(raw_bytes).hexdigest(),
    "bytes": len(raw_bytes),
    "columns_published": ["Player", "Position", "Injuries", "Practice Status", "Game Status"],
    "n_games": len(games),
    "n_matchups": sum(len(g["matches"]) for g in games),
    "n_teams_listed": len(teams),
    "n_rows": n_rows,
    "practice_status_counts": dict(sorted(prac.items(), key=lambda kv: -kv[1])),
    "game_status_counts": dict(sorted(stat.items(), key=lambda kv: -kv[1])),
    "per_team": per_team,
    "games": games,
    "rows": rows,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as f:
    json.dump(out, f, indent=1, sort_keys=False)

print("rows:", n_rows, "teams:", len(teams), "games:", len(games),
      "matchups:", out["n_matchups"])
print("practice:", out["practice_status_counts"])
print("status:", out["game_status_counts"])
