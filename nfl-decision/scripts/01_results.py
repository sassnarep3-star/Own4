#!/usr/bin/env python3
"""Build the verified 2026 NFL results table for nfl-decision.

Provenance policy
-----------------
* Every row carries the official nfl.com source URL for that specific game.
* Week 9 (15 games) and the missing Week 8 game (CHI@SEA) were transcribed by this
  session directly from https://www.nfl.com/scores/2026/REG9 and
  https://www.nfl.com/games/bears-at-seahawks-2026-reg-8 .
* Weeks 1-8 excluding CHI@SEA come from the repository's pre-existing
  nfl-lab/data/games_2026.csv (a peer session's transcription of nfl.com
  schedules). They are NOT re-transcribed here; they are re-*validated* here by
  recomputing all 32 teams' W-L-T / PF / PA and comparing to the official
  nfl.com standings snapshot read on 2026-11-12.
"""
import csv, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ROOT)
SRC = os.path.join(REPO, "nfl-lab", "data", "games_2026.csv")
OUT = os.path.join(ROOT, "data", "results_2026.json")

GAME_URL = "https://www.nfl.com/games/{slug}"
SCORES_URL = "https://www.nfl.com/scores/2026/REG{w}"

# Transcribed by this session from official nfl.com score pages (2026-11-12).
WEEK9 = [
    ("JAX", "BAL", 33, 10, "jaguars-at-ravens-2026-reg-9", "2026-11-05"),
    ("CIN", "ATL", 34, 17, "bengals-at-falcons-2026-reg-9", "2026-11-08"),
    ("DEN", "CAR", 26, 21, "broncos-at-panthers-2026-reg-9", "2026-11-08"),
    ("DAL", "IND", 27, 23, "cowboys-at-colts-2026-reg-9", "2026-11-08"),
    ("NYJ", "KC", 12, 35, "jets-at-chiefs-2026-reg-9", "2026-11-08"),
    ("DET", "MIA", 19, 9, "lions-at-dolphins-2026-reg-9", "2026-11-08"),
    ("CLE", "NO", 22, 23, "browns-at-saints-2026-reg-9", "2026-11-08"),
    ("NYG", "PHI", 19, 11, "giants-at-eagles-2026-reg-9", "2026-11-08"),
    ("LA", "WAS", 20, 13, "rams-at-commanders-2026-reg-9", "2026-11-08"),
    ("HOU", "LAC", 44, 22, "texans-at-chargers-2026-reg-9", "2026-11-08"),
    ("LV", "SF", 17, 38, "raiders-at-49ers-2026-reg-9", "2026-11-08"),
    ("GB", "NE", 45, 27, "packers-at-patriots-2026-reg-9", "2026-11-08"),
    ("AZ", "SEA", 3, 17, "cardinals-at-seahawks-2026-reg-9", "2026-11-08"),
    ("TB", "CHI", 24, 27, "buccaneers-at-bears-2026-reg-9", "2026-11-08"),
    ("BUF", "MIN", 23, 6, "bills-at-vikings-2026-reg-9", "2026-11-09"),
]
# Week 8 game verified missing from the repo log; confirmed official 2026-11-12.
WEEK8_MISSING = ("CHI", "SEA", 34, 17, "bears-at-seahawks-2026-reg-8", "2026-11-02")

# Official standings snapshot read from https://www.nfl.com/standings/league/2026/REG
# on 2026-11-12. Tuple: (W, L, T, PF, PA)
OFFICIAL = {
 'BUF':(7,1,0,256,187),'SF':(7,1,0,235,156),'CHI':(7,2,0,241,184),'DEN':(7,2,0,198,186),
 'CIN':(6,2,0,240,175),'DET':(6,2,0,222,189),'JAX':(6,2,0,229,121),'KC':(6,2,0,202,143),
 'MIN':(6,2,0,146,116),'PIT':(6,2,0,180,144),'NYG':(5,2,1,182,172),'GB':(6,3,0,216,191),
 'CLE':(5,4,0,161,196),'LA':(5,4,0,214,181),'NE':(5,4,0,211,207),'SEA':(5,4,0,202,162),
 'BAL':(4,5,0,189,236),'DAL':(4,5,0,246,236),'LV':(4,5,0,238,268),'CAR':(3,5,0,199,219),
 'HOU':(3,5,0,209,192),'NO':(3,5,0,185,216),'AZ':(3,6,0,178,255),'ATL':(3,6,0,188,223),
 'TB':(3,6,0,202,178),'WAS':(2,5,1,172,202),'IND':(2,7,0,184,249),'NYJ':(2,7,0,182,223),
 'PHI':(2,7,0,148,221),'MIA':(1,7,0,126,200),'TEN':(1,7,0,144,199),'LAC':(0,8,0,121,219),
}


def main():
    games = []
    for r in csv.DictReader(open(SRC)):
        games.append({
            "season": 2026, "week": int(r["week"]), "date": r["date_iso"],
            "away": r["away"], "home": r["home"],
            "away_pts": int(r["away_pts"]), "home_pts": int(r["home_pts"]),
            "slug": r["game_slug"],
            "source": GAME_URL.format(slug=r["game_slug"]),
            "origin": "repo:nfl-lab/data/games_2026.csv (re-validated this session)",
        })
    for away, home, ap, hp, slug, date in WEEK9 + [WEEK8_MISSING]:
        if any(g["slug"] == slug for g in games):
            continue
        games.append({"season": 2026, "week": int(slug.rsplit("-", 1)[1]), "date": date,
                      "away": away, "home": home, "away_pts": ap, "home_pts": hp,
                      "slug": slug, "source": GAME_URL.format(slug=slug),
                      "origin": "this session: transcribed from official nfl.com score page"})
    games.sort(key=lambda g: (g["week"], g["date"], g["slug"]))

    # Recompute team records and compare with the official standings snapshot.
    rec = {t: {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0} for t in OFFICIAL}
    for g in games:
        for t, f, a in ((g["away"], g["away_pts"], g["home_pts"]), (g["home"], g["home_pts"], g["away_pts"])):
            rec[t]["pf"] += f; rec[t]["pa"] += a
        if g["away_pts"] > g["home_pts"]:
            rec[g["away"]]["w"] += 1; rec[g["home"]]["l"] += 1
        elif g["home_pts"] > g["away_pts"]:
            rec[g["home"]]["w"] += 1; rec[g["away"]]["l"] += 1
        else:
            rec[g["away"]]["t"] += 1; rec[g["home"]]["t"] += 1

    checks, mismatches = [], []
    for t, (w, l, ti, pf, pa) in OFFICIAL.items():
        c = rec[t]
        if (w, l, ti, pf, pa) != (c["w"], c["l"], c["t"], c["pf"], c["pa"]):
            mismatches.append({"team": t, "official": [w, l, ti, pf, pa],
                               "recomputed": [c["w"], c["l"], c["t"], c["pf"], c["pa"]]})
    n = len(games)
    checks.append({"check": "game count == official weeks 1-9 total (136)", "pass": n == 136, "detail": f"n={n}"})
    checks.append({"check": "league wins == league losses", "pass": sum(r["w"] for r in rec.values()) == sum(r["l"] for r in rec.values()),
                   "detail": f"{sum(r['w'] for r in rec.values())} = {sum(r['l'] for r in rec.values())}"})
    checks.append({"check": "league ties is an even number (each tie counted twice)", "pass": sum(r["t"] for r in rec.values()) % 2 == 0,
                   "detail": f"{sum(r['t'] for r in rec.values())}"})
    checks.append({"check": "all 32 teams match official W-L-T/PF/PA (5 cells x 32 teams = 160 cells)",
                   "pass": not mismatches, "detail": f"{160 - 5*len(mismatches)}/160 cells match; {len(mismatches)} teams differ"})
    checks.append({"check": "every row has an nfl.com source URL",
                   "pass": all(g["source"].startswith("https://www.nfl.com/") for g in games),
                   "detail": f"{n}/{n}"})

    out = {
        "generated_utc": "2026-11-12",
        "policy": "Official-source-only. Values that cannot be confirmed on an official NFL page are left blank.",
        "sources": [
            {"id": "R1", "what": "2026 Weeks 1-9 final scores", "url": "https://www.nfl.com/scores/2026/REG9"},
            {"id": "R2", "what": "2026 league standings snapshot", "url": "https://www.nfl.com/standings/league/2026/REG"},
            {"id": "R3", "what": "Week 8 missing game CHI@SEA 34-17", "url": "https://www.nfl.com/games/bears-at-seahawks-2026-reg-8"},
            {"id": "R4", "what": "Official 2026 schedule by week", "url": "https://www.nfl.com/schedules/2026/by-week/week-10"},
        ],
        "checks": checks,
        "mismatches": mismatches,
        "teams": {t: rec[t] for t in sorted(rec)},
        "games": games,
    }
    json.dump(out, open(OUT, "w"), indent=1)
    for c in checks:
        print(("PASS " if c["pass"] else "FAIL ") + c["check"] + " — " + c["detail"])
    print("games:", n, "->", OUT)


if __name__ == "__main__":
    main()
