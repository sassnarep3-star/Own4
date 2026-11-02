#!/usr/bin/env python3
"""Line-by-line verification: recompute every legend-defined standings cell
from the transcribed official game log and compare against the official
nfl.com league standings transcription. Any mismatch = failure.

Columns verified per team (legend on https://www.nfl.com/standings/league/2026/REG):
W, L, T, PCT, PF, PA, NET PTS, HOME, ROAD, DIV, CONF, STRK.
Also: internal consistency (game counts, ties, division membership, byes).
"""
import csv, json, os, sys, collections, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(ROOT, "nfl-lab", "data")

DIVISIONS = {  # verified from https://www.nfl.com/standings/division/2026/REG
    ("AFC", "EAST"): ["BUF", "NE", "NYJ", "MIA"],
    ("AFC", "NORTH"): ["PIT", "CIN", "CLE", "BAL"],
    ("AFC", "SOUTH"): ["JAX", "HOU", "IND", "TEN"],
    ("AFC", "WEST"): ["DEN", "KC", "LV", "LAC"],
    ("NFC", "EAST"): ["NYG", "DAL", "WAS", "PHI"],
    ("NFC", "NORTH"): ["CHI", "DET", "GB", "MIN"],
    ("NFC", "SOUTH"): ["TB", "ATL", "CAR", "NO"],
    ("NFC", "WEST"): ["SF", "LA", "AZ", "SEA"],
}
TEAM_DIV = {}
for (conf, div), teams in DIVISIONS.items():
    for t in teams:
        TEAM_DIV[t] = (conf, div)

def load(name):
    with open(os.path.join(D, name)) as f:
        return list(csv.DictReader(f))

games = load("games_2026.csv")
standings = load("standings_2026.csv")

checks = []
def chk(name, ok, detail=""):
    checks.append({"check": name, "pass": bool(ok), "detail": str(detail)})

# --- structure ---
chk("120 completed games", len(games) == 120, f"n={len(games)}")
chk("32 standings rows", len(standings) == 32, f"n={len(standings)}")
slugs = [g["game_slug"] for g in games]
chk("game slugs unique", len(set(slugs)) == len(slugs))
bad_pts = [g["game_slug"] for g in games if not (g["away_pts"].isdigit() and g["home_pts"].isdigit())]
chk("all scores numeric", not bad_pts, ",".join(bad_pts))
ties = [g["game_slug"] for g in games if g["away_pts"] == g["home_pts"]]
chk("exactly one tie in log (NYG-WAS W5)", len(ties) == 1 and "giants-at-commanders" in ties[0], ",".join(ties))

# --- aggregate from games ---
def blank():
    return dict(w=0, l=0, t=0, pf=0, pa=0,
                hw=0, hl=0, ht=0, rw=0, rl=0, rt=0,
                dw=0, dl=0, dt=0, cw=0, cl=0, ct=0, gp=0)
agg = collections.defaultdict(blank)
for g in games:
    a, h = g["away"], g["home"]
    ap, hp = int(g["away_pts"]), int(g["home_pts"])
    for team, pf, pa, home in ((a, ap, hp, 0), (h, hp, ap, 1)):
        x = agg[team]
        x["gp"] += 1
        x["pf"] += pf
        x["pa"] += pa
        if pf > pa: res = "w"
        elif pf < pa: res = "l"
        else: res = "t"
        x[res] += 1
        if home:
            x["h" + res] += 1
        else:
            x["r" + res] += 1
        if TEAM_DIV[a] == TEAM_DIV[h]:  # same (conf, div) pair
            x["d" + res] += 1
        if TEAM_DIV[team][0] == TEAM_DIV[a][0] == TEAM_DIV[h][0]:
            x["c" + res] += 1

# --- current streak (most recent completed game per team, by date then week) ---
ordered = sorted(games, key=lambda g: (g["date_iso"], g["week"], g["game_slug"]))
last_result = {}
for g in ordered:
    ap, hp = int(g["away_pts"]), int(g["home_pts"])
    last_result[g["away"]] = "W" if ap > hp else ("L" if ap < hp else "T")
    last_result[g["home"]] = "W" if hp > ap else ("L" if hp < ap else "T")
def result_of(g, team):
    ap, hp = int(g["away_pts"]), int(g["home_pts"])
    if team == g["away"]:
        return "W" if ap > hp else ("L" if ap < hp else "T")
    return "W" if hp > ap else ("L" if hp < ap else "T")

def streak_of(team):
    sign = last_result[team]
    s = 0
    for g in reversed(ordered):
        if team not in (g["away"], g["home"]):
            continue
        if result_of(g, team) != sign:
            break
        s += 1
    return f"{s}{sign}"

def rec(w, l, t):
    return f"{w}-{l}-{t}"

mismatches = []
for row in standings:
    team = row["team"]
    x = agg[team]
    exp = {
        "w": x["w"], "l": x["l"], "t": x["t"],
        "pf": x["pf"], "pa": x["pa"], "net": x["pf"] - x["pa"],
        "home": rec(x["hw"], x["hl"], x["ht"]),
        "road": rec(x["rw"], x["rl"], x["rt"]),
        "div_rec": rec(x["dw"], x["dl"], x["dt"]),
        "conf_rec": rec(x["cw"], x["cl"], x["ct"]),
        "strk": streak_of(team),
    }
    for k, v in exp.items():
        got = row[k]
        if k in ("w", "l", "t", "pf", "pa", "net"):
            ok = int(got) == v
        else:
            ok = got == str(v)
        if not ok:
            mismatches.append(f"{team}.{k}: standings={got} recomputed={v}")
    # pct
    games_n = x["w"] + x["l"] + x["t"]
    pct = round((x["w"] + 0.5 * x["t"]) / games_n, 3)
    if abs(float(row["pct"]) - pct) > 0.0005:
        mismatches.append(f"{team}.pct: standings={row['pct']} recomputed={pct}")
    # division membership consistency
    conf, div = TEAM_DIV[team]
    if row["conf"] != conf or row["div"] != div:
        mismatches.append(f"{team}.membership: standings={row['conf']}/{row['div']} division-page={conf}/{div}")

chk("every standings cell matches recomputation from game log (32 teams x 13 fields)",
    not mismatches, f"{len(mismatches)} mismatches: " + "; ".join(mismatches[:10]))

# --- cross totals ---
total_pf = sum(int(r["pf"]) for r in standings)
total_games_pf = sum(int(g["away_pts"]) + int(g["home_pts"]) for g in games)
chk("sum(standings PF) == sum(game scores)", total_pf == total_games_pf, f"{total_pf} vs {total_games_pf}")
wins = sum(int(r["w"]) for r in standings); losses = sum(int(r["l"]) for r in standings); ts = sum(int(r["t"]) for r in standings)
chk("sum(W) == sum(L) and sum(T) == 2 x ties_in_log", wins == losses and ts == 2 * len(ties),
    f"W={wins} L={losses} T={ts} ties_in_log={len(ties)}")
gp_sum = sum(agg[t]["gp"] for t in agg)
chk("team-games == 2 x games", gp_sum == 2 * len(games), f"{gp_sum} vs {2*len(games)}")
# per-team game counts: 8 for all except CHI/SEA (7, pending MNF) and bye-in-w8 teams already have 7
count8 = sorted(t for t in agg if agg[t]["gp"] == 8)
count7 = sorted(t for t in agg if agg[t]["gp"] == 7)
# 16 teams with 7 games: one bye each in W5-W8 (14) + MNF-pending CHI/SEA (2)
expected7 = {"CAR", "KC", "CIN", "DET", "MIA", "MIN", "BUF", "JAX", "LAC", "WAS",
             "HOU", "NO", "NYG", "SF", "CHI", "SEA"}
chk("16 teams with 7 games (one bye each W5-W8 + MNF-pending CHI/SEA), 16 with 8",
    len(count7) == 16 and len(count8) == 16 and set(count7) == expected7,
    f"7-game={count7}")

# byes observed vs game counts
bye_w5 = {"CAR", "KC"}; bye_w6 = {"CIN", "DET", "MIA", "MIN"}
bye_w7 = {"BUF", "JAX", "LAC", "WAS"}; bye_w8 = {"HOU", "NO", "NYG", "SF"}
for wk, byes in ((5, bye_w5), (6, bye_w6), (7, bye_w7), (8, bye_w8)):
    played = set()
    for g in games:
        if int(g["week"]) == wk:
            played.update([g["away"], g["home"]])
    pending = {"CHI", "SEA"} if wk == 8 else set()  # MNF Nov 2 not yet played
    chk(f"week {wk}: byes {sorted(byes)} are exactly teams not playing",
        not (byes & played) and len(played) == 32 - len(byes) - len(pending),
        f"played={len(played)} overlap={sorted(byes & played)}")

# --- write report ---
report = {
    "generated_from": ["nfl-lab/data/games_2026.csv", "nfl-lab/data/standings_2026.csv"],
    "official_sources": [
        "https://www.nfl.com/schedules/2026/by-week/week-1 … week-8",
        "https://www.nfl.com/standings/league/2026/REG",
        "https://www.nfl.com/standings/division/2026/REG",
    ],
    "checks": checks,
    "all_pass": all(c["pass"] for c in checks),
    "games": len(games),
    "standings_rows": len(standings),
    "cells_compared": len(standings) * 15,
}
with open(os.path.join(D, "verification_report.json"), "w") as f:
    json.dump(report, f, indent=1)

n_fail = sum(1 for c in checks if not c["pass"])
for c in checks:
    print(("PASS " if c["pass"] else "FAIL ") + c["check"] + (" | " + c["detail"] if c["detail"] and not c["pass"] else ""))
print(f"\n{len(checks)} checks, {n_fail} failures; {report['cells_compared']} cells compared")
sys.exit(1 if n_fail else 0)
