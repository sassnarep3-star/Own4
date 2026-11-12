#!/usr/bin/env python3
"""Recompute every numeric identity that the official NFL.com pages must satisfy.

If any check fails, this script exits non-zero: the site build refuses to publish.
It performs no estimation; each check is an internal-consistency test of the
transcribed official values, and it is the only thing that makes the rows
'verified' in the mechanical sense used on this site.
"""
import json, os, sys

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
L = lambda n: json.load(open(os.path.join(D, n)))

st = L("official_standings.json")["rows"]
off = L("team_stats_2026.json")["rows"]
dfn = L("team_stats_defense_2026.json")["rows"]
games = L("games_2026.json")["rows"]
inj = L("injuries_week10.json")
slate = L("slate_week10.json")

checks = []
def check(cid, desc, ok, detail, source):
    checks.append({"id": cid, "check": desc, "pass": bool(ok), "detail": detail, "source_url": source})

# 1. standings internal arithmetic
bad = [r["team"] for r in st if r["pf"] - r["pa"] != r["net_pts"]]
check("C1", "PF - PA equals published NET PTS for every team", not bad,
      "%d/32 rows agree; mismatches: %s" % (32 - len(bad), bad or "none"), "https://www.nfl.com/standings/")
check("C2", "Sum of PF equals sum of PA across the league", sum(r["pf"] for r in st) == sum(r["pa"] for r in st),
      "PF=%d PA=%d" % (sum(r["pf"] for r in st), sum(r["pa"] for r in st)), "https://www.nfl.com/standings/")
check("C3", "Sum of wins equals sum of losses", sum(r["w"] for r in st) == sum(r["l"] for r in st),
      "W=%d L=%d T=%d" % (sum(r["w"] for r in st), sum(r["l"] for r in st), sum(r["t"] for r in st)),
      "https://www.nfl.com/standings/")

# 2. standings vs team stats
check("C4", "League total points on the offence page equals league PF on the standings page",
      sum(r["pts"] for r in off) == sum(r["pf"] for r in st),
      "offence page=%d standings=%d" % (sum(r["pts"] for r in off), sum(r["pf"] for r in st)),
      "https://www.nfl.com/stats/team-stats/offense/scoring/2026/reg/all")
check("C5", "League total points allowed on the defence page equals league PA on the standings page",
      sum(r["pts"] for r in dfn) == sum(r["pa"] for r in st),
      "defence page=%d standings=%d" % (sum(r["pts"] for r in dfn), sum(r["pa"] for r in st)),
      "https://www.nfl.com/stats/team-stats/defense/scoring/2026/reg/all")
for cid, key in (("C6", "pass_yds"), ("C7", "pass_td"), ("C8", "rush_yds"), ("C9", "rush_td")):
    o = sum(r[key] for r in off); d = sum(r[key] for r in dfn)
    check(cid, "League offence %s equals league defence %s allowed" % (key, key), o == d,
          "offence=%d defence=%d" % (o, d), "https://www.nfl.com/stats/team-stats/")

# 3. game archive reconciles to official standings
from collections import defaultdict
agg = defaultdict(lambda: [0, 0, 0, 0, 0])
for g in games:
    if g["away_pts"] is None or g["home_pts"] is None:
        continue
    for t, pf, pa in ((g["away"], g["away_pts"], g["home_pts"]), (g["home"], g["home_pts"], g["away_pts"])):
        a = agg[t]; a[3] += pf; a[4] += pa
        if pf > pa: a[0] += 1
        elif pf < pa: a[1] += 1
        else: a[2] += 1
bad = []
for r in st:
    a = agg.get(r["team"], [0, 0, 0, 0, 0])
    if [a[0], a[1], a[2], a[3], a[4]] != [r["w"], r["l"], r["t"], r["pf"], r["pa"]]:
        bad.append(r["team"])
check("C10", "W-L-T / PF / PA recomputed from the game archive match the official standings",
      not bad and len(games) == 136,
      "games=%d teams_checked=32 mismatches=%s" % (len(games), bad or "none"),
      "https://www.nfl.com/standings/")

# 4. schedule / slate consistency
wk = defaultdict(int)
for g in games:
    wk[g["week"]] += 1
check("C11", "Games per week look like complete NFL weeks (13-16 per week, no gaps)",
      all(13 <= wk[w] <= 16 for w in range(1, 10)) and sorted(wk) == list(range(1, 10)),
      "per-week counts: %s" % dict(sorted(wk.items())), "https://www.nfl.com/schedules/2026/")
teams_in_slate = set()
for g in slate["rows"]:
    teams_in_slate.add(g["away"]); teams_in_slate.add(g["home"])
check("C12", "Week 10 slate has 14 games and 28 distinct clubs (4 clubs on the official bye list)",
      len(slate["rows"]) == 14 and len(teams_in_slate) == 28,
      "games=%d distinct_teams=%d" % (len(slate["rows"]), len(teams_in_slate)),
      slate["source_url"])
check("C13", "Every Week 10 game has an official nfl.com game page URL",
      all(g["source_url"].startswith("https://www.nfl.com/games/") for g in slate["rows"]),
      "%d/%d" % (sum(1 for g in slate["rows"] if g["source_url"].startswith("https://www.nfl.com/games/")),
                 len(slate["rows"])), slate["source_url"])

# 5. injury report structure
check("C14", "Injury report has one section for each of the 28 clubs playing in Week 10",
      len(inj["teams"]) == 28 and {t["team"] for t in inj["teams"]} == teams_in_slate,
      "club sections=%d, all 28 Week 10 clubs present" % len(inj["teams"]),
      "https://www.nfl.com/injuries/")
check("C15", "Every injury row carries the official injuries-page URL it was read from",
      all(row["source_url"] == "https://www.nfl.com/injuries/" for t in inj["teams"] for row in t["players"]),
      "rows=%d, 100%% sourced" % sum(len(t["players"]) for t in inj["teams"]), "https://www.nfl.com/injuries/")

fails = [c for c in checks if not c["pass"]]
out = {
    "dataset": "integrity_checks",
    "generated_utc": "2026-11-12",
    "description": "Mechanical consistency checks over the transcribed official values. A pass means the two "
                   "official figures agree with each other; it does not mean a third party audited the transcription.",
    "n_checks": len(checks), "n_pass": len(checks) - len(fails), "n_fail": len(fails),
    "checks": checks,
}
json.dump(out, open(os.path.join(D, "integrity.json"), "w"), indent=1)
for c in checks:
    print(("PASS " if c["pass"] else "FAIL ") + c["id"] + " " + c["check"] + " | " + c["detail"])
if fails:
    sys.exit("integrity checks failed: %s" % [c["id"] for c in fails])
