#!/usr/bin/env python3
"""
Own4 · nfl-live-board · L-02/L-03

Build the pre-registered backtest corpus and reconcile it, game by game, against the
official league standings read on 2026-11-17.

Two independent official facts are placed side by side:

  A. the corpus  — weeks 1-9 inherited from the repository's per-game-URL feed
     (nfl-book/data/results_feed.json, identical to nfl-command/data/games_2026_verified.json
     as checked by engine/crosscheck_peer.py), plus the 12 Week-10 finals transcribed in this
     session from https://www.nfl.com/scores/2026/week-10 ;
  B. the standings — 32 rows transcribed from https://www.nfl.com/standings/league/2026/REG
     into data/standings_2026-11-17.json .

The reconciliation is arithmetic on official values only:
  * games played per team (W+L+T) must equal the number of corpus games that team appears in;
  * W/L/T per team must equal the wins/losses/ties the corpus scores imply;
  * PF and PA per team must equal the points the corpus awards that team and its opponents.

A wrong score anywhere moves PF and PA for two teams at once, so this test is a
whole-corpus check, not a sampled one.

Nothing is inferred. If a check cannot be made it is reported as a skip, never as a pass.

Run: python3 nfl-live-board/engine/reconcile.py
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")

PEER_FEED = os.path.join(os.path.dirname(ROOT), "nfl-book", "data", "results_feed.json")

# Week 10 finals, transcribed 2026-11-17 from https://www.nfl.com/scores/2026/week-10
# (away, home, away_pts, home_pts, date). Order follows the official page.
WEEK10 = [
    ("WAS", "NYG", 24, 21, "2026-11-12"),
    ("NE",  "DET", 10, 35, "2026-11-15"),
    ("KC",  "ATL", 35, 13, "2026-11-15"),
    ("HOU", "CLE", 24, 27, "2026-11-15"),
    ("MIN", "GB",  30, 10, "2026-11-15"),
    ("MIA", "IND", 22, 24, "2026-11-15"),
    ("CAR", "NO",  20, 17, "2026-11-15"),
    ("BUF", "NYJ", 31, 12, "2026-11-15"),
    ("JAX", "TEN", 40, 23, "2026-11-15"),
    ("LA",  "AZ",  34,  6, "2026-11-15"),
    ("SEA", "LV",  21, 13, "2026-11-15"),
    ("SF",  "DAL", 46, 40, "2026-11-15"),
    ("PIT", "CIN", 18, 38, "2026-11-15"),
]
W10_URL = "https://www.nfl.com/scores/2026/week-10"
W10_SLUG = {
    ("WAS", "NYG"): "commanders-at-giants-2026-reg-10",
    ("NE", "DET"):  "patriots-at-lions-2026-reg-10",
    ("KC", "ATL"):  "chiefs-at-falcons-2026-reg-10",
    ("HOU", "CLE"): "texans-at-browns-2026-reg-10",
    ("MIN", "GB"):  "vikings-at-packers-2026-reg-10",
    ("MIA", "IND"): "dolphins-at-colts-2026-reg-10",
    ("CAR", "NO"):  "panthers-at-saints-2026-reg-10",
    ("BUF", "NYJ"): "bills-at-jets-2026-reg-10",
    ("JAX", "TEN"): "jaguars-at-titans-2026-reg-10",
    ("LA", "AZ"):   "rams-at-cardinals-2026-reg-10",
    ("SEA", "LV"):  "seahawks-at-raiders-2026-reg-10",
    ("SF", "DAL"):  "49ers-at-cowboys-2026-reg-10",
    ("PIT", "CIN"): "steelers-at-bengals-2026-reg-10",
}


def load(p):
    with open(p) as f:
        return json.load(f)


def game_id(week, away, home):
    return "W%02d-%s-%s" % (week, away, home)


def build_corpus():
    peer = load(PEER_FEED)["rows"]
    inherited = [r for r in peer if r["week"] <= 9]
    rows = []
    for r in inherited:
        rows.append({
            "game_id": r.get("game_id") or game_id(r["week"], r["away"], r["home"]),
            "week": r["week"], "date": r.get("date", ""),
            "away": r["away"], "home": r["home"],
            "away_pts": r["away_pts"], "home_pts": r["home_pts"],
            "source_url": r.get("source_url", ""),
            "week_page_url": r.get("week_page_url", ""),
            "provenance": "inherited_per_game_url_feed (weeks 1-9)",
            "neutral": r.get("neutral", False),
        })
    for away, home, a, h, date in WEEK10:
        rows.append({
            "game_id": game_id(10, away, home), "week": 10, "date": date,
            "away": away, "home": home, "away_pts": a, "home_pts": h,
            "source_url": "https://www.nfl.com/games/" + W10_SLUG[(away, home)],
            "week_page_url": W10_URL,
            "provenance": "transcribed 2026-11-17 from the official Week 10 scores page",
            "neutral": (away, home) in {("NE", "DET")},   # Munich game, official page logo
        })
    rows.sort(key=lambda r: (r["week"], r["away"], r["home"]))
    return rows


def main():
    corpus = build_corpus()
    standings = load(os.path.join(DATA, "standings_2026-11-17.json"))["rows"]
    st = {r["team"]: r for r in standings}

    # ---- corpus-level scalars -------------------------------------------------
    n = len(corpus)
    total_points = sum(r["away_pts"] + r["home_pts"] for r in corpus)
    weeks = sorted({r["week"] for r in corpus})

    # ---- per-team aggregates from the corpus ---------------------------------
    agg = {}
    for r in corpus:
        for team, pts, opp_pts in (
            (r["away"], r["away_pts"], r["home_pts"]),
            (r["home"], r["home_pts"], r["away_pts"]),
        ):
            a = agg.setdefault(team, {"gp": 0, "w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0})
            a["gp"] += 1
            a["pf"] += pts
            a["pa"] += opp_pts
            if pts > opp_pts:
                a["w"] += 1
            elif pts < opp_pts:
                a["l"] += 1
            else:
                a["t"] += 1

    checks = []
    for team in sorted(st):
        s, a = st[team], agg.get(team, {"gp": 0, "w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0})
        for field, official, computed in (
            ("games played", s["w"] + s["l"] + s["t"], a["gp"]),
            ("wins", s["w"], a["w"]),
            ("losses", s["l"], a["l"]),
            ("ties", s["t"], a["t"]),
            ("points for", s["pf"], a["pf"]),
            ("points against", s["pa"], a["pa"]),
        ):
            checks.append({
                "team": team, "field": field,
                "standings": official, "corpus": computed,
                "result": "pass" if official == computed else "FAIL",
                "source": "https://www.nfl.com/standings/league/2026/REG",
            })
    # a team in the corpus that is absent from the standings table would be a defect
    for team in sorted(agg):
        if team not in st:
            checks.append({"team": team, "field": "present in standings", "standings": None,
                           "corpus": agg[team]["gp"], "result": "FAIL",
                           "source": "https://www.nfl.com/standings/league/2026/REG"})

    fails = [c for c in checks if c["result"] != "pass"]

    # ---- the "136-game log" question, answered with arithmetic ----------------
    per_week = {}
    for r in corpus:
        per_week.setdefault(r["week"], 0)
        per_week[r["week"]] += 1
    inherited_n = sum(1 for r in corpus if r["provenance"].startswith("inherited"))
    games_played_official = (sum(s["w"] + s["l"] + s["t"] for s in standings)) // 2

    summary = {
        "corpus_games": n,
        "corpus_weeks": weeks,
        "corpus_per_week": {str(k): per_week[k] for k in sorted(per_week)},
        "corpus_total_points": total_points,
        "inherited_games": inherited_n,
        "week10_transcribed_games": len(WEEK10),
        "official_games_played": games_played_official,
        "official_games_played_source": "sum(W+L+T)/2 over the 32 transcribed standings rows",
        "arithmetic_identity": "official_games_played == corpus_games",
        "identity_holds": games_played_official == n,
        "checks": len(checks), "pass": len(checks) - len(fails), "fail": len(fails),
        "unplayed_not_in_corpus": [{
            "week": 10, "away": "LAC", "home": "BAL",
            "game_url": "https://www.nfl.com/games/chargers-at-ravens-2026-reg-10",
            "why": "official page showed records, not a score, at read time 2026-11-17; "
                   "the standings of the same day also exclude it",
        }],
    }

    out = {
        "dataset": "nfl_live_board_corpus_reconciliation",
        "title": "Pre-registered backtest corpus (weeks 1-10, 2026) reconciled to official standings",
        "built_utc": "2026-11-17",
        "policy": "Every corpus row carries the official URL it was read from. Reconciliation is "
                  "arithmetic between two independently read official pages; it infers nothing.",
        "summary": summary,
        "checks": checks,
        "corpus": corpus,
    }
    with open(os.path.join(DATA, "corpus_2026.json"), "w") as f:
        json.dump(out, f, indent=1)
    with open(os.path.join(DATA, "corpus_rows_only.json"), "w") as f:
        json.dump({"rows": corpus}, f, indent=1)

    print("corpus games: %d  (weeks %s)" % (n, weeks))
    print("per week:     %s" % summary["corpus_per_week"])
    print("inherited weeks 1-9: %d   Week 10 transcribed: %d" % (inherited_n, len(WEEK10)))
    print("official games played per standings: %d   identity holds: %s"
          % (games_played_official, summary["identity_holds"]))
    print("checks: %d   pass: %d   fail: %d" % (len(checks), len(checks) - len(fails), len(fails)))
    for c in fails:
        print("  FAIL %-4s %-18s standings=%-5s corpus=%-5s" %
              (c["team"], c["field"], c["standings"], c["corpus"]))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
