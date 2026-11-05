#!/usr/bin/env python3
"""verify_inherited.py — line-by-line cross-check of previously published values
against official NBA data fetched for this verification round.

Compared artefacts (all earlier sessions' published outputs, read-only):
  official/standings.json    -> verification/data/standings_2026-11-05.csv  (live nba.com/standings)
  official/games.json        -> verification/data/games.csv                 (live nba.com/games?date=...)
  official/results.json lines-> verification/data/verify_2026-11-02.csv     (live finals, graded)
  data/games_official.json   -> verification/data/games.csv                 (92-game pipeline sample)
  data/player_gamelogs.json  -> provenance audit (partner-sourced, not official)

Output: verification/data/inherited_verification.json  + .csv (one row per value compared)
No value is ever "corrected" here: mismatches are reported, not silently rewritten.
"""
import csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
V = os.path.dirname(HERE)
REPO = os.path.dirname(V)
DATA = os.path.join(V, "data")


def load_csv(name):
    with open(os.path.join(DATA, name), newline="") as f:
        return list(csv.DictReader(f))


def main():
    live_std = {r["abbr"]: r for r in load_csv("standings_2026-11-05.csv")}
    live_games = {r["game_id"]: r for r in load_csv("games.csv")}
    checks, rows = [], []

    # 1. official/standings.json (snapshot verified_on 2026-11-02) vs live standings
    old = json.load(open(os.path.join(REPO, "official", "standings.json")))
    for r in old["rows"]:
        ab = r["abbr"]
        cur = live_std.get(ab)
        if not cur:
            rows.append({"artifact": "official/standings.json", "key": ab, "field": "team",
                         "published": r["team"], "live_official": "", "match": "NO LIVE ROW",
                         "source_url": "https://www.nba.com/standings", "verified_on": "2026-11-05"})
            continue
        for f in ("W", "L", "WIN_pct", "GB", "CONF", "DIV", "HOME", "ROAD", "OT", "LAST10", "STREAK"):
            a, b = str(r.get(f, "")).strip(), str(cur.get(f, "")).strip()
            rows.append({"artifact": "official/standings.json", "key": ab, "field": f,
                         "published": a, "live_official": b,
                         "match": "identical" if a == b else "changed since 2026-11-02",
                         "source_url": "https://www.nba.com/standings", "verified_on": "2026-11-05"})

    # 2. official/games.json (56 finals) vs live games
    old = json.load(open(os.path.join(REPO, "official", "games.json")))
    for r in old["rows"]:
        gid = r.get("game_id", "")
        cur = live_games.get(gid)
        if not cur:
            rows.append({"artifact": "official/games.json", "key": gid, "field": "game_id",
                         "published": f'{r["team_a"]} {r["team_a_pts"]}-{r["team_b_pts"]} {r["team_b"]}',
                         "live_official": "", "match": "NOT FOUND IN LIVE SAMPLE",
                         "source_url": r.get("source_url", ""), "verified_on": "2026-11-05"})
            continue
        pairs = [("team_a", r["team_a"], cur["away"]), ("team_b", r["team_b"], cur["home"]),
                 ("team_a_pts", str(r["team_a_pts"]), str(cur["away_pts"])),
                 ("team_b_pts", str(r["team_b_pts"]), str(cur["home_pts"])),
                 ("total_pts", str(r["total_pts"]), str(cur["total_pts"]))]
        for f, a, b in pairs:
            rows.append({"artifact": "official/games.json", "key": gid, "field": f,
                         "published": a, "live_official": b,
                         "match": "identical" if str(a) == str(b) else "MISMATCH",
                         "source_url": cur["source_url"], "verified_on": "2026-11-05"})

    # 3. data/games_official.json (92-game pipeline sample sourced from official pages)
    old = json.load(open(os.path.join(REPO, "data", "games_official.json")))
    for g in old["games"]:
        cur = live_games.get(g["game_id"])
        if not cur:
            rows.append({"artifact": "data/games_official.json", "key": g["game_id"], "field": "game_id",
                         "published": f'{g["away"]["tricode"]} {g["away"]["score"]}-{g["home"]["score"]} {g["home"]["tricode"]}',
                         "live_official": "", "match": "NOT FOUND IN LIVE SAMPLE",
                         "source_url": "", "verified_on": "2026-11-05"})
            continue
        for f, a, b in (("away_pts", str(g["away"]["score"]), str(cur["away_pts"])),
                        ("home_pts", str(g["home"]["score"]), str(cur["home_pts"]))):
            rows.append({"artifact": "data/games_official.json", "key": g["game_id"], "field": f,
                         "published": a, "live_official": b,
                         "match": "identical" if a == b else "MISMATCH",
                         "source_url": cur["source_url"], "verified_on": "2026-11-05"})

    # 4. player game logs provenance
    pl = json.load(open(os.path.join(REPO, "data", "player_gamelogs.json")))
    rows.append({"artifact": "data/player_gamelogs.json", "key": f'{len(pl["rows"])} rows',
                 "field": "source_class", "published": pl["source_class"],
                 "live_official": "official league box scores not re-fetched row by row",
                 "match": "partner-sourced, NOT promoted to official",
                 "source_url": "https://www.nba.com/stats/help/faq", "verified_on": "2026-11-05"})

    # 5. own lines for 2026-11-02 graded against live finals
    try:
        v = json.load(open(os.path.join(DATA, "verify_2026-11-02.json")))
        rows.append({"artifact": "official/results.json (lines)", "key": "2026-11-02 slate",
                     "field": "winner accuracy (out-of-sample)",
                     "published": "n/a - no post-hoc grading existed",
                     "live_official": f'{v["winner_hits"]}/{v["graded"]} = {v["winner_accuracy"]}',
                     "match": "graded by this round", "source_url": v["sources"][0],
                     "verified_on": "2026-11-05"})
    except FileNotFoundError:
        pass

    with open(os.path.join(DATA, "inherited_verification.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["artifact", "key", "field", "published",
                                          "live_official", "match", "source_url", "verified_on"])
        w.writeheader(); w.writerows(rows)

    from collections import Counter
    agg = {}
    for r in rows:
        a = agg.setdefault(r["artifact"], Counter())
        a[r["match"]] += 1
    out = {"verified_on": "2026-11-05", "rows_compared": len(rows),
           "artifacts": {k: dict(v) for k, v in agg.items()},
           "mismatches": [r for r in rows if r["match"] == "MISMATCH"],
           "not_found": [r for r in rows if r["match"] in ("NOT FOUND IN LIVE SAMPLE", "NO LIVE ROW")],
           "interpretation": ("'changed since 2026-11-02' is expected: standings are a live snapshot. "
                              "A MISMATCH on a final score would be an irregularity.")}
    json.dump(out, open(os.path.join(DATA, "inherited_verification.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "not_found"}, indent=1)[:3000])
    print("mismatches:", len(out["mismatches"]), "not_found:", len(out["not_found"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
