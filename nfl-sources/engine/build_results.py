"""S1 — build the page-verified results corpus from the committed raw transcriptions.

Input : nfl-sources/raw/week{1..10}.txt   (transcribed from the official week schedule pages)
        nfl-sources/raw/standings.txt     (transcribed from the official league standings page)
        nfl-book/data/results_feed.json   (the inherited feed, for reconciliation only)
Output: nfl-sources/data/results.json

Nothing here talks to the network. Every row carries the URL of the official page it was read from.
"""
import os
import re

from common import (DATA, RAW, REGISTERED_UTC, REGISTRATION_COMMIT, read_text, write_json,
                    sha256_file)

WEEK_URL = "https://www.nfl.com/schedules/2026/by-week/week-%d"
STANDINGS_URL = "https://www.nfl.com/standings/league/2026/REG"

TEAM_NAMES = {
    "AZ": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "LA": "Los Angeles Rams", "LAC": "Los Angeles Chargers",
    "LV": "Las Vegas Raiders", "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings",
    "NE": "New England Patriots", "NO": "New Orleans Saints", "NYG": "New York Giants",
    "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers",
    "SEA": "Seattle Seahawks", "SF": "San Francisco 49ers", "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
}


def parse_week(path):
    rows = []
    for line in read_text(path).splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        w, date, section, away, ap, home, hp, url = line.split("|")
        rows.append({
            "week": int(w),
            "date_as_printed": date,
            "section_as_printed": section,
            "away": away, "home": home,
            "away_pts": int(ap), "home_pts": int(hp),
            "game_url": url,
            "week_page_url": WEEK_URL % int(w),
        })
    return rows


def parse_standings(path):
    rows = []
    for line in read_text(path).splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        t, w, l, tie, pct, pf, pa, net = line.split("|")
        rows.append({"team": t, "w": int(w), "l": int(l), "t": int(tie),
                     "pct": float(pct), "pf": int(pf), "pa": int(pa), "net": int(net)})
    return rows


def derived_records(games):
    rec = {t: {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0} for t in TEAM_NAMES}
    for g in games:
        a, h = g["away"], g["home"]
        rec[a]["pf"] += g["away_pts"]
        rec[a]["pa"] += g["home_pts"]
        rec[h]["pf"] += g["home_pts"]
        rec[h]["pa"] += g["away_pts"]
        if g["away_pts"] == g["home_pts"]:
            rec[a]["t"] += 1
            rec[h]["t"] += 1
        elif g["away_pts"] > g["home_pts"]:
            rec[a]["w"] += 1
            rec[h]["l"] += 1
        else:
            rec[h]["w"] += 1
            rec[a]["l"] += 1
    return rec


def main():
    games = []
    for w in range(1, 11):
        games.extend(parse_week(os.path.join(RAW, "week%d.txt" % w)))

    # game id, integrity of the (week, clubs) key
    month = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
             "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
    for g in games:
        if not re.match(r"https://www\.nfl\.com/games/[a-z0-9\-]+-2026-reg-\d+$", g["game_url"]):
            raise SystemExit("unexpected game url %r" % g["game_url"])
        g["game_id"] = "W%02d-%s-%s" % (g["week"], g["away"], g["home"])
        m, d = g["date_as_printed"].split()  # only the printed "Mon D" is used; the year is in the URL
        g["date_iso"] = "2026-%02d-%02d" % (month[m], int(d))
        g["international_game"] = g["section_as_printed"].startswith("International Game")
        g["home_stadium"] = None  # filled from the venue read where available, never guessed
        g["neutral_flag_source"] = ("section_as_printed on the official week page reads "
                                    "'%s'" % g["section_as_printed"])
    ids = [g["game_id"] for g in games]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate game_id in corpus")
    for g in games:
        if not (0 <= g["away_pts"] <= 100 and 0 <= g["home_pts"] <= 100):
            raise SystemExit("implausible score in %s" % g["game_id"])

    # per-team participation: expected games = 10 weeks - byes printed on the same pages.
    byes = {}
    for line in read_text(os.path.join(RAW, "byes.txt")).splitlines():
        if not line.strip() or line.startswith("#") or line.startswith("week|"):
            continue
        w, team = line.split("|")
        byes.setdefault(int(w), set()).add(team)
    counts = {t: 0 for t in TEAM_NAMES}
    for g in games:
        counts[g["away"]] += 1
        counts[g["home"]] += 1
    unplayed = {"PIT": 1, "CIN": 1, "LAC": 1, "BAL": 1}  # the two week-10 games not printed FINAL
    participation = []
    for t in sorted(TEAM_NAMES):
        expected = 10 - sum(1 for w, teams in byes.items() if t in teams) - unplayed.get(t, 0)
        participation.append({"team": t, "byes": sorted(w for w, teams in byes.items() if t in teams),
                              "expected_games": expected, "corpus_games": counts[t],
                              "match": expected == counts[t]})
    bad = [p for p in participation if not p["match"]]
    if bad:
        raise SystemExit("bye-adjusted participation mismatch: %r" % bad)
    if len(games) != 148:
        raise SystemExit("corpus size changed: %d" % len(games))

    rec = derived_records(games)
    official = parse_standings(os.path.join(RAW, "standings.txt"))

    mismatches = []
    for o in official:
        d = rec[o["team"]]
        for k in ("w", "l", "t", "pf", "pa"):
            if d[k] != o[k]:
                mismatches.append({"team": o["team"], "field": k,
                                   "derived_from_corpus": d[k], "official_standings": o[k]})
    official_games_decided = sum(o["w"] for o in official)
    tie_games_official = sum(o["t"] for o in official) // 2
    tie_games_corpus = sum(1 for g in games if g["away_pts"] == g["home_pts"])

    # reconciliation against the inherited feed
    feed_path = os.path.join(os.path.dirname(DATA), "..", "nfl-book", "data", "results_feed.json")
    feed_path = os.path.normpath(feed_path)
    feed_rows, feed_note = [], ""
    if os.path.exists(feed_path):
        feed = __import__("json").load(open(feed_path, encoding="utf-8"))
        feed_rows = feed.get("rows", [])
        feed_note = feed.get("provenance_note", "")
    feed_by_pair = {}
    for r in feed_rows:
        feed_by_pair.setdefault((r["week"], frozenset((r["away"], r["home"]))), []).append(r)

    matched, disagree, missing_from_feed, extra_in_feed = 0, [], [], []
    seen = set()
    for g in games:
        key = (g["week"], frozenset((g["away"], g["home"])))
        seen.add(key)
        cands = feed_by_pair.get(key, [])
        if not cands:
            missing_from_feed.append(g["game_id"])
            continue
        r = cands[0]
        ok = (r["away"] == g["away"] and r["home"] == g["home"]
              and r["away_pts"] == g["away_pts"] and r["home_pts"] == g["home_pts"]
              and r["date"] == g["date_iso"])
        if ok:
            matched += 1
        else:
            disagree.append({
                "game_id": g["game_id"],
                "feed": {"away": r["away"], "away_pts": r["away_pts"], "home": r["home"],
                         "home_pts": r["home_pts"], "date": r.get("date"),
                         "verification": r.get("verification")},
                "this_read": {"away": g["away"], "away_pts": g["away_pts"], "home": g["home"],
                              "home_pts": g["home_pts"], "date": g["date_iso"]},
                "official_source": g["game_url"],
            })
    for key, rows in feed_by_pair.items():
        if key not in seen:
            for r in rows:
                extra_in_feed.append({"feed_game_id": r.get("game_id"), "week": r.get("week"),
                                      "matchup": "%s at %s" % (r.get("away"), r.get("home")),
                                      "feed_verification": r.get("verification")})

    out = {
        "dataset": "nfl_sources_results_corpus",
        "title": "2026 regular season, weeks 1-10, page-verified against the official week schedule pages",
        "built_utc": REGISTERED_UTC,
        "preregistration": "nfl-sources/PREREGISTRATION.md (registration commit %s)" % REGISTRATION_COMMIT,
        "source": {
            "publisher": "NFL Enterprises (nfl.com)",
            "week_pages": [WEEK_URL % w for w in range(1, 11)],
            "standings_page": STANDINGS_URL,
            "read_utc": REGISTERED_UTC,
            "method": ("Transcribed line by line from the official week schedule page for each week. A game "
                       "enters the corpus only if the page prints it as FINAL with both scores; a game the "
                       "page prints as live or unplayed is excluded and carries no score. Every row keeps "
                       "the game-centre URL printed on the page."),
        },
        "input_hashes": {("raw/week%d.txt" % w): sha256_file(os.path.join(RAW, "week%d.txt" % w))
                                 for w in range(1, 11)},
        "n_games": len(games),
        "n_weeks": 10,
        "excluded_not_final": [
            {"game_id": "W10-PIT-CIN", "printed_as": "0-0, Q1, NBC — Live at read time",
             "source_url": "https://www.nfl.com/games/steelers-at-bengals-2026-reg-10",
             "score": None},
            {"game_id": "W10-LAC-BAL", "printed_as": "Chargers at Ravens, Monday, November 16th, 8:15 PM, ESPN",
             "source_url": "https://www.nfl.com/games/chargers-at-ravens-2026-reg-10",
             "score": None},
        ],
        "participation_check": participation,
        "byes_as_printed": {str(k): sorted(v) for k, v in sorted(byes.items())},
        "independence_check": {
            "check": ("Every club's W-L-T, PF and PA derived from this corpus is compared with the official "
                      "league standings page, which was transcribed before the derived records were computed."),
            "source_url": STANDINGS_URL,
            "clubs_checked": len(official),
            "fields_checked": len(official) * 5,
            "mismatches": mismatches,
            "result": "pass" if not mismatches else "FAIL",
            "aggregate": {
                "official_total_wins": official_games_decided,
                "official_tie_games": tie_games_official,
                "corpus_games": len(games),
                "corpus_tie_games": tie_games_corpus,
                "official_pf_total": sum(o["pf"] for o in official),
                "official_pa_total": sum(o["pa"] for o in official),
            },
        },
        "reconciliation_vs_inherited_feed": {
            "inherited_file": "nfl-book/data/results_feed.json",
            "inherited_rows": len(feed_rows),
            "inherited_line_by_line": sum(1 for r in feed_rows if r.get("verification", "").startswith("line_by_line")),
            "inherited_note": feed_note,
            "page_verified_rows_this_read": len(games),
            "matched": matched,
            "disagreements": disagree,
            "in_corpus_not_in_feed": missing_from_feed,
            "in_feed_not_in_corpus": extra_in_feed,
            "rule": ("Neither file is silently preferred. A disagreement is published with both values and the "
                     "official page URL so it can be re-read by hand."),
        },
        "rows": games,
    }
    write_json(os.path.join(DATA, "results.json"), out)
    print("corpus games:", len(games))
    print("independence check:", out["independence_check"]["result"],
          "club-field mismatches:", len(mismatches))
    for m in mismatches:
        print("   MISMATCH", m)
    print("reconciliation: matched", matched, "disagree", len(disagree),
          "missing_from_feed", len(missing_from_feed), "extra_in_feed", len(extra_in_feed))
    for d in disagree:
        print("   DISAGREE", d["game_id"], d["feed"], "vs", d["this_read"])
    for x in extra_in_feed:
        print("   FEED-ONLY", x)


if __name__ == "__main__":
    main()
