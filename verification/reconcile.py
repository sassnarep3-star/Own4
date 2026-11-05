#!/usr/bin/env python3
"""
Own4 — line-by-line reconciliation of what the repository already contained
against the official pages re-read on 2026-11-05, plus internal consistency
checks on the fresh snapshot.

Every check below is mechanical and printed with the numbers it compared, so a
reader can repeat it. A check that cannot establish a fact is reported as NOTE,
never as PASS.

Output: verification/out/reconciliation.json
Run:    python3 verification/reconcile.py
"""

import collections
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "out")

S = {
    "standings": "https://www.nba.com/standings",
    "team_stats": "https://www.nba.com/stats/teams/traditional",
    "games": "https://www.nba.com/games?date=2026-11-04",
    "calendar": "https://www.nba.com/games?date=2026-10-20",
}

CHECKS = []


def check(cid, name, expected, actual, ok, source, note=""):
    CHECKS.append({
        "id": cid, "name": name,
        "expected": expected, "actual": actual,
        "status": "PASS" if ok else "FAIL",
        "source_url": source, "note": note,
    })


def note(cid, name, detail, source):
    CHECKS.append({"id": cid, "name": name, "expected": "", "actual": detail,
                   "status": "NOTE", "source_url": source, "note": ""})


def main():
    os.makedirs(OUT, exist_ok=True)
    live_s = json.load(open(os.path.join(DATA, "standings.json")))["rows"]
    live_t = json.load(open(os.path.join(DATA, "team_stats.json")))["rows"]
    fresh = json.load(open(os.path.join(DATA, "games_fresh.json")))["rows"]
    cal = json.load(open(os.path.join(DATA, "calendar.json")))["days"]
    old_s = json.load(open(os.path.join(ROOT, "official", "standings.json")))["rows"]
    old_t = json.load(open(os.path.join(ROOT, "official", "team_stats.json")))["rows"]
    old_g = json.load(open(os.path.join(ROOT, "official", "games.json")))["rows"]

    ls = {r["abbr"]: r for r in live_s}
    lt = {r["abbr"]: r for r in live_t}

    # ---- C01 two independent official pages must agree team by team ----
    mism = [a for a in ls if (ls[a]["W"], ls[a]["L"]) != (lt[a]["W"], lt[a]["L"])]
    check("C01", "Standings page and Teams-Traditional page agree on W-L for all 30 teams",
          "0 mismatched teams", "%d mismatched teams%s" % (len(mism), (" (%s)" % ", ".join(mism)) if mism else ""),
          not mism, S["standings"],
          "Two separately rendered official pages; agreement is evidence the transcription is faithful.")

    # ---- C02 league totals identity ----
    sumw = sum(r["W"] for r in live_s)
    suml = sum(r["L"] for r in live_s)
    check("C02", "League-wide wins equal league-wide losses (every game has one of each)",
          "%d = %d" % (sumw, sumw), "%d W vs %d L" % (sumw, suml), sumw == suml, S["standings"])

    sumgp = sum(r["GP"] for r in live_t)
    check("C03", "Sum of team GP is even and equals twice the number of games played",
          "even, %d team-games" % sumgp, "%d team-games -> %d games" % (sumgp, sumgp // 2),
          sumgp % 2 == 0 and sumgp // 2 == sumw, S["team_stats"])

    # ---- C04 team identity sets ----
    same_ids = set((r["abbr"], r["team_id"]) for r in live_s) == set((r["abbr"], r["team_id"]) for r in live_t)
    check("C04", "Both official pages list the same 30 team ids",
          "30 identical (abbr, id) pairs",
          "%d pairs, identical=%s" % (len(set((r['abbr'], r['team_id']) for r in live_s)), same_ids),
          same_ids and len(ls) == 30, S["team_stats"])

    # ---- C05 inherited snapshot -> live, team by team ----
    fw, fl = collections.Counter(), collections.Counter()
    for g in fresh:
        if g["home_pts"] > g["away_pts"]:
            fw[g["home"]] += 1; fl[g["away"]] += 1
        else:
            fw[g["away"]] += 1; fl[g["home"]] += 1
    os_ = {r["abbr"]: r for r in old_s}
    bad = []
    for a in sorted(ls):
        exp = (os_[a]["W"] + fw[a], os_[a]["L"] + fl[a])
        got = (ls[a]["W"], ls[a]["L"])
        if exp != got:
            bad.append((a, exp, got))
    check("C05", "Inherited 2026-11-02 records + the 29 freshly verified finals = live 2026-11-05 records",
          "0 teams disagree", "%d of 30 teams disagree%s" % (len(bad), (" " + str(bad[:4])) if bad else ""),
          not bad, S["games"],
          "30 independent team-by-team tests. Agreement corroborates both the inherited snapshot and the new transcription.")

    # ---- C06 per-date completeness of the inherited sample ----
    cnt = collections.Counter(g["date"] for g in old_g)
    gaps = {d: (cnt.get(d, 0), cal.get(d)) for d in cnt if cal.get(d) != cnt.get(d)}
    check("C06", "Every date in the inherited game sample holds exactly the number of games the official calendar lists",
          "no date short of the official count",
          "%d dates checked; mismatches=%s" % (len(cnt), gaps if gaps else "none"),
          not gaps, S["calendar"])

    # ---- C07 total coverage of the sample ----
    sample = len(old_g) + len(fresh)
    official = sumgp // 2
    missing_dates = {d: n for d, n in sorted(cal.items()) if cnt.get(d, 0) == 0 and d in cnt or (d not in cnt and n and d < "2026-11-02")}
    missing_games = sum(n for d, n in missing_dates.items() if d not in cnt)
    check("C07", "Games in the published sample vs games actually played",
          "%d games played as of the snapshot" % official,
          "%d in sample (%.1f%%); %d games on %d dates of the season are not in the sample"
          % (sample, 100.0 * sample / official, missing_games, len(missing_dates)),
          sample <= official, S["calendar"],
          "Coverage gap is published as flag F-COVERAGE; the model is fitted on the sample only.")

    # ---- C08 no team plays twice on one date, no duplicate game ids ----
    ids = [g["game_id"] for g in old_g] + [g["game_id"] for g in fresh]
    dup = [k for k, v in collections.Counter(ids).items() if v > 1]
    per_date_ok = True
    seen = collections.defaultdict(set)
    for g in old_g:
        for t in (g["team_a"], g["team_b"]):
            if t in seen[g["date"]]:
                per_date_ok = False
            seen[g["date"]].add(t)
    for g in fresh:
        for t in (g["away"], g["home"]):
            if t in seen[g["date"]]:
                per_date_ok = False
            seen[g["date"]].add(t)
    check("C08", "No duplicate game id and no team listed twice on the same date",
          "0 duplicates, no same-date repeat",
          "%d duplicates; same-date repeat=%s" % (len(dup), not per_date_ok),
          not dup and per_date_ok, S["games"])

    # ---- C09 every fresh row's deep link follows the official away-vs-home pattern ----
    ok = all(g["game_url"].endswith(g["game_id"]) and
             g["game_url"].split("/game/")[1].startswith(g["away"].lower() + "-vs-" + g["home"].lower())
             for g in fresh)
    check("C09", "Each fresh score's official game link is away-vs-home with the same game id",
          "29 links match the pattern", "all match" if ok else "at least one link does not match",
          ok, S["games"])

    # ---- C10 the published +/- column does not sum to zero ----
    pm = sum(r["plus_minus"] for r in live_t)
    mean_pts = sum(r["PTS"] for r in live_t) / 30.0
    mean_allowed = sum(r["PTS"] - r["plus_minus"] for r in live_t) / 30.0
    note("C10", "Published team +/- does not sum to zero",
         "sum of the 30 published +/- values = %+.1f; mean PTS %.2f vs mean implied points allowed %.2f "
         "(difference %+.2f). Because every game awards the same points to both sides the true sum is 0. "
         "Consistent with one-decimal rounding, but larger than the +/-1.5 bound that pure rounding allows, "
         "so it is reported, not corrected, and the column is not used as a model input (flag F-PLUSMINUS)."
         % (pm, mean_pts, mean_allowed, mean_pts - mean_allowed), S["team_stats"])

    # ---- C11 inherited snapshot internal consistency ----
    ots = {r["abbr"]: r for r in old_t}
    bad2 = [a for a in os_ if a in ots and (os_[a]["W"], os_[a]["L"]) != (ots[a]["W"], ots[a]["L"])]
    check("C11", "Within the inherited 2026-11-02 snapshot, standings and team stats agree on W-L",
          "0 mismatched teams", "%d mismatched" % len(bad2), not bad2,
          "https://github.com/sassnarep3-star/Own4/blob/main/official/standings.json")

    # ---- C12 inherited game rows: provenance recorded, not re-fetched ----
    note("C12", "The 56 inherited game rows were not individually re-fetched",
         "They carry their own official source URL and game link, and check C05/C06 corroborates them "
         "league-wide and date-by-date, but no row-by-row re-fetch was performed (flag F-INHERITED).",
         "https://www.nba.com/games?date=2026-10-21")

    # ---- C13 official page exposes an odds toggle ----
    note("C13", "The official games page renders an odds toggle but no odds values in the fetched text",
         "The page shows 'HIDE ODDS'; no price values were present in the retrieved page text, so no price was "
         "transcribed. Whether those prices are official NBA data or a partner feed is not established here; they "
         "are treated as unavailable and no ROI is computed (flag F-PRICE).",
         "https://www.nba.com/games?date=2026-11-05")

    result = {
        "snapshot": "2026-11-05",
        "checks": CHECKS,
        "summary": {
            "pass": sum(1 for c in CHECKS if c["status"] == "PASS"),
            "fail": sum(1 for c in CHECKS if c["status"] == "FAIL"),
            "note": sum(1 for c in CHECKS if c["status"] == "NOTE"),
            "sample_games": sample,
            "official_games": official,
            "coverage_pct": 100.0 * sample / official,
            "missing_games": missing_games,
            "missing_dates": sorted(d for d in missing_dates if d not in cnt),
        },
    }
    with open(os.path.join(OUT, "reconciliation.json"), "w") as f:
        json.dump(result, f, indent=1)
        f.write("\n")

    for c in CHECKS:
        print("%-4s %-6s %s" % (c["id"], c["status"], c["name"]))
    print("\n%d pass, %d fail, %d note; sample %d/%d games (%.1f%%) missing %d on dates %s"
          % (result["summary"]["pass"], result["summary"]["fail"], result["summary"]["note"],
             sample, official, result["summary"]["coverage_pct"], missing_games,
             result["summary"]["missing_dates"]))


if __name__ == "__main__":
    main()
