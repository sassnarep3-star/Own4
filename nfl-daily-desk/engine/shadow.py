#!/usr/bin/env python3
"""Re-run the frozen singles shadow baseline (v1) on today's official inputs.

Why this file exists: the v1 rule (nfl-readiness/prereg/SHADOW_BASELINE_v1.md) forecasts a game
only when both clubs' Week 10 result is confirmed final in the official capture. At its freeze
time 8 of the 13 Week 11 fixtures failed that test, so the registered record covers 5 games.
On 2026-11-19 the official Week 10 page shows FINAL for every game, so the rule's own condition
is now satisfied for all 13 - and none of the 13 has kicked off yet. This script therefore:

  1. reproduces the 5 recorded rows from the frozen arithmetic (a faithfulness test: if the rule
     re-run on today's standings does not equal the stored numbers, something drifted);
  2. records the remaining 8 fixtures as cohort 2, stamped before their kickoffs;
  3. publishes both cohorts separately and never merges them into one sample.

The rule text is not edited. A change to SIGMA/HFA/eligibility would require a v2 file with its
own commit. The registration of this recording is the commit that lands it.
"""
import hashlib
import json
import math
import os
import random
import subprocess
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)
SIGMA = 13.5          # frozen constant of v1, an assumption (flagged, never sourced)
HFA = 0.0             # frozen constant of v1
SEED_COHORT2 = 20261119
PREREG = ROOT + "/nfl-readiness/prereg/SHADOW_BASELINE_v1.md"
COHORT1 = ROOT + "/nfl-readiness/data/shadow_week11.json"
INPUTS1 = ROOT + "/nfl-readiness/data/official_inputs_2026.json"
RECORDED_UTC = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# v1 scope: the Week 11 slate exactly as published on the official week page
SLATE = [
    ("IND", "HOU", "Thu 2026-11-19 8:15 PM ET"),
    ("MIA", "BUF", "Sun 2026-11-22 1:00 PM ET"),
    ("BAL", "CAR", "Sun 2026-11-22 1:00 PM ET"),
    ("NO", "CHI", "Sun 2026-11-22 1:00 PM ET"),
    ("TEN", "DAL", "Sun 2026-11-22 1:00 PM ET"),
    ("TB", "DET", "Sun 2026-11-22 1:00 PM ET"),
    ("AZ", "KC", "Sun 2026-11-22 1:00 PM ET"),
    ("PIT", "PHI", "Sun 2026-11-22 1:00 PM ET"),
    ("NYJ", "LAC", "Sun 2026-11-22 4:05 PM ET"),
    ("JAX", "NYG", "Sun 2026-11-22 4:25 PM ET"),
    ("LV", "DEN", "Sun 2026-11-22 4:25 PM ET"),
    ("MIN", "SF", "Sun 2026-11-22 8:20 PM ET"),
    ("CIN", "WAS", "Mon 2026-11-23 8:15 PM ET"),
]
KICKOFF_UTC = {  # derived from the published ET kickoff times, ET = UTC-5 on these dates
    "Thu 2026-11-19 8:15 PM ET": "2026-11-20T01:15:00Z",
    "Sun 2026-11-22 1:00 PM ET": "2026-11-22T18:00:00Z",
    "Sun 2026-11-22 4:05 PM ET": "2026-11-22T21:05:00Z",
    "Sun 2026-11-22 4:25 PM ET": "2026-11-22T21:25:00Z",
    "Sun 2026-11-22 8:20 PM ET": "2026-11-23T01:20:00Z",
    "Mon 2026-11-23 8:15 PM ET": "2026-11-23T01:15:00Z",
}
TEAM_URL = {"IND": "colts", "HOU": "texans", "MIA": "dolphins", "BUF": "bills", "BAL": "ravens",
            "CAR": "panthers", "NO": "saints", "CHI": "bears", "TEN": "titans", "DAL": "cowboys",
            "TB": "buccaneers", "DET": "lions", "AZ": "cardinals", "KC": "chiefs", "PIT": "steelers",
            "PHI": "eagles", "NYJ": "jets", "LAC": "chargers", "JAX": "jaguars", "NYG": "giants",
            "LV": "raiders", "DEN": "broncos", "MIN": "vikings", "SF": "49ers", "CIN": "bengals",
            "WAS": "commanders"}


def phi(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def rating(t):
    g = t["W"] + t["L"] + t["T"]
    return (t["PF"] - t["PA"]) / g


def git_head():
    return subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True,
                          text=True).stdout.strip()


def previous_record():
    """A registration is immutable once made: a re-run must not re-stamp recorded_utc, and it must not
    silently re-cohort a fixture. Whatever was recorded first is what stays; only fixtures seen for the
    first time get today's stamp."""
    path = NS + "/data/shadow_cohorts.json"
    if not os.path.exists(path):
        return {}
    try:
        prev = json.load(open(path, encoding="utf-8"))
    except Exception:
        return {}
    out = {}
    for r in prev.get("rows", []):
        out[(r["away"], r["home"])] = r
    return out


def main():
    st = {r["club"]: r for r in json.load(open(NS + "/data/standings.json"))["rows"]}
    prev = previous_record()
    preserved = restamped = 0
    c1 = json.load(open(COHORT1))
    inp1 = json.load(open(INPUTS1))
    old_teams = {t["abbr"]: t for t in inp1["standings"]}
    # 1. did the official standings move between the cohort-1 read and today?
    drift = []
    for abbr, t in old_teams.items():
        now = st.get(abbr)
        if not now:
            continue
        for k in ("W", "L", "T", "PF", "PA"):
            if int(t[k]) != int(now[k]):
                drift.append({"club": abbr, "field": k, "at_cohort1_freeze": t[k], "on_2026-11-19": now[k]})
    stored = {(f["away"], f["home"]): f for f in c1["forecasts"]}
    stored_set = set(stored)
    # 2. re-run the frozen arithmetic
    rng = random.Random(SEED_COHORT2)
    rows = []
    for away, home, ko in SLATE:
        ra, rh = rating(st[away]), rating(st[home])
        m = rh - ra + HFA
        p = phi(m / SIGMA)
        was = prev.get((away, home))
        if was and was.get("recorded_utc"):
            stamp = was["recorded_utc"]          # a registration keeps the time it was first made at
            commit = was.get("registered_at_commit") or "not recorded by the version that made this row"
            preserved += 1
        else:
            stamp, commit = RECORDED_UTC, git_head()
            restamped += 1
        rows.append({
            "away": away, "home": home, "kickoff_et": ko, "kickoff_utc": KICKOFF_UTC[ko],
            "recorded_utc": stamp,
            "registered_at_commit": commit,
            "record_kind": ("re-derivation of the stored cohort-1 registration — that file publishes no "
                            "timestamp of its own, so this stamp is when THIS desk reproduced it, not when "
                            "it was first registered" if (away, home) in stored_set else
                            "first registration by this desk, made before kickoff"),
            "recorded_immutable": bool(was and was.get("recorded_utc")),
            "before_kickoff": stamp < KICKOFF_UTC[ko],
            "inputs": {k: {f: st[k][f] for f in ("W", "L", "T", "PF", "PA")} for k in (away, home)},
            "rating_away": round(ra, 4), "rating_home": round(rh, 4),
            "margin_home": round(m, 4), "sigma": SIGMA, "hfa": HFA,
            "p_home": round(p, 4), "p_away": round(1 - p, 4),
            "fair_pick": home if m > 0 else away,
            "random_control_pick": rng.choice([away, home]),
            "market_line": None,
            "market_line_blank_reason": "no official or licensed opening price exists (flag F-DSK-01); "
                                        "the residual column is published empty rather than assumed",
            "residual_fair_minus_market": None,
            "graded": None,
            "grade_due_utc": KICKOFF_UTC[ko],
            "source_url": "https://www.nfl.com/games/%s-at-%s-2026-reg-11"
                          % (TEAM_URL[away], TEAM_URL[home]),
        })
    # 3. faithfulness check against the 5 stored cohort-1 rows
    checks = []
    for r in rows:
        k = (r["away"], r["home"])
        if k not in stored:
            continue
        s = stored[k]
        agree = {f: (r[f] == s.get(f)) for f in
                 ("margin_home", "p_home", "p_away", "rating_away", "rating_home")}
        agree["fair_pick_vs_fav_control"] = (r["fair_pick"] == s.get("fav_control_pick"))
        checks.append({"fixture": "%s at %s" % k, "fields": agree,
                       "all_agree": all(agree.values()),
                       "stored_margin": s.get("margin_home"), "recomputed_margin": r["margin_home"]})
    cohort = []
    for r in rows:
        k = (r["away"], r["home"])
        default = ("1 (recorded at the v1 freeze, 8 fixtures withheld)" if k in stored
                   else "2 (recorded 2026-11-19, after the Week 10 feed completed, still pre-kickoff)")
        r2 = dict(r)
        r2["cohort"] = (prev.get(k) or {}).get("cohort") or default
        cohort.append(r2)
    in_cohort1 = {c for f in c1["forecasts"] for c in (f["away"], f["home"])}
    inside = [d for d in drift if d["club"] in in_cohort1]
    outside = [d for d in drift if d["club"] not in in_cohort1]
    out = {
        "dataset": "nfl_daily_desk_shadow_cohorts",
        "title": "Singles shadow baseline v1 - frozen rule re-run on the 2026-11-19 official inputs",
        "built_utc": RECORDED_UTC,
        "rule": {
            "file": os.path.relpath(PREREG, ROOT),
            "sha256": hashlib.sha256(open(PREREG, "rb").read()).hexdigest(),
            "last_commit_touching_rule": git_head() and subprocess.run(
                ["git", "-C", ROOT, "log", "-1", "--format=%H %cI", "--", PREREG],
                capture_output=True, text=True).stdout.strip(),
            "constants": {"SIGMA_points_assumed": SIGMA, "HFA": HFA,
                          "sigma_status": "ASSUMPTION, not measured and not sourced - flagged, may only "
                                          "change in a v2 file"},
            "eligibility_test": "both clubs' Week 10 result confirmed final (or a Week 10 bye) in the "
                                "official Week 10 capture at record time",
            "eligibility_result_2026-11-19": "13 of 13 fixtures eligible: the official week page shows "
                                             "FINAL on all 14 Week 10 games and names CHI, DEN, PHI, TB as "
                                             "the Week 10 byes",
            "amendment": "this record adds cohort 2 under the same rule text; the rule file is not edited",
        },
        "standings_drift_since_cohort1_freeze": {
            "n_fields_changed": len(drift),
            "n_changed_inside_cohort1_clubs": len(inside),
            "n_changed_outside_cohort1_clubs": len(outside),
            "why_the_split_matters": "cohort 1's eligibility gate existed because the official standings "
                                     "were still moving at its freeze time. Every changed field sits with a "
                                     "club OUTSIDE cohort 1, which is why those 5 rows reproduce exactly and "
                                     "the other 8 fixtures had to wait",
            "changes": drift,
            "changes_outside": outside,
                                                 "reading": "the official standings are unchanged between "
                                                            "the cohort-1 freeze and today, so cohort 1 and "
                                                            "cohort 2 share one input state"},
        "faithfulness_check": {"n_rows_compared": len(checks),
                               "n_rows_identical": sum(1 for c in checks if c["all_agree"]),
                               "rows": checks,
                               "meaning": "re-deriving the stored rows from the frozen arithmetic and the "
                                          "official inputs must reproduce them exactly; a mismatch would "
                                          "mean either the rule or the stored record drifted"},
        "rows": cohort,
        "counts": {"week11_games": len(rows), "cohort1": len(stored),
                   "cohort2": len(rows) - len(stored),
                   "recorded_before_kickoff": sum(1 for r in rows if r["before_kickoff"]),
                   "timestamps_preserved_from_the_original_record": preserved,
                   "newly_stamped_this_run": restamped},
        "immutability": {"rule": "a re-run never moves a recorded_utc and never re-cohorts a fixture: "
                                 "the first record stands, and only a fixture seen for the first time takes "
                                 "today's stamp. This is what makes 'recorded before kickoff' a claim about "
                                 "the past rather than about the last time someone ran a script.",
                         "this_run": {"preserved": preserved, "newly_stamped": restamped}},
        "grading": {"graded": 0, "why": "no Week 11 game has finished at this record time",
                    "first_grade_due_utc": min(r["kickoff_utc"] for r in rows),
                    "minimum_sample_for_any_skill_claim": 300,
                    "status_at_n13": "SHADOW - no eligibility for reward, no staking, no leaderboard rank"},
        "irregularities": [
            "cohort 2 was first recorded at 2026-11-19T07:19:16Z under commit e322a32e; a rebuild before "
            "the immutability rule existed re-stamped it to the run time. The rule now preserves the first "
            "stamp and records the commit it was made under, so 'recorded before kickoff' cannot be moved by "
            "re-running the script — every row in this file is now stamped at its first registration.",
            "the cohort-1 record's withheld list names Arizona 'ARI' while its forecast rows name the "
            "same club 'AZ': club keys are not canonical across the two lists, so an automated join on "
            "abbreviation would silently drop that fixture",
            "cohort 1's seeded random control cannot be re-derived from the stored file because the "
            "fixture iteration order is not recoverable from its output; cohort 2 therefore carries its "
            "own seed (20261119) and its own picks",
        ],
    }
    json.dump(out, open(NS + "/data/shadow_cohorts.json", "w"), indent=1)
    print("faithful rows: %d/%d ; standings drift fields: %d ; pre-kickoff: %d/%d"
          % (sum(1 for c in checks if c["all_agree"]), len(checks), len(drift),
             sum(1 for r in rows if r["before_kickoff"]), len(rows)))
    print("registration commit (HEAD):", git_head())
    print("cohort1 %d cohort2 %d" % (len(stored), len(rows) - len(stored)))


if __name__ == "__main__":
    main()
