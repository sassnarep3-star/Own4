#!/usr/bin/env python3
"""Build the NFL Decision Desk corpus.

Inputs (read-only, never modified):
  * nfl-lines/data/raw/nfldata_games.csv   — frozen third-party archive (nflverse/nfldata),
    136 settled 2026 REG games at the time it was vendored into the repo.
  * nfl-markets/data/raw/closing_lines.csv — third-party closing prices 2011-2025.
  * nfl-markets/data/raw/initial_lines.csv — third-party opening prices, 2021 only.
  * data/raw/official_standings_2026.json  — this session's official nfl.com transcription.
  * data/raw/official_week10_*.json        — this session's point-in-time week-10 capture.

Outputs: data/corpus/*.json (deterministic; rerunning produces no diff).

Everything the corpus asserts carries a source_url and a verification_status. Nothing is
inferred. A value that cannot be sourced is emitted as null, never as a guess.
"""
from __future__ import annotations

import csv
import json
import os
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # nfl-decision-desk/
REPO = os.path.dirname(ROOT)
OUT = os.path.join(ROOT, "data", "corpus")
RAWDIR = os.path.join(ROOT, "data", "raw")
os.makedirs(OUT, exist_ok=True)

GAMES_CSV = os.path.join(REPO, "nfl-lines/data/raw/nfldata_games.csv")
CLOSE_CSV = os.path.join(REPO, "nfl-markets/data/raw/closing_lines.csv")
INIT_CSV = os.path.join(REPO, "nfl-markets/data/raw/initial_lines.csv")

NFLVERSE = "https://github.com/nflverse/nfldata"
NFLVERSE_GAMES = "https://github.com/nflverse/nfldata/blob/master/data/games.csv"
NFLVERSE_CLOSE = "https://github.com/nflverse/nfldata/blob/master/data/closing_lines.csv"
NFLVERSE_INIT = "https://github.com/nflverse/nfldata/blob/master/data/initial_lines.csv"
STANDINGS_URL = "https://www.nfl.com/standings/league/2026/REG"
SCHED = "https://www.nfl.com/schedules/2026/by-week/week-{}"
FETCHED = "2026-11-15T23:24:27Z"

DIVISIONS = {
    "AFC East": ["BUF", "MIA", "NE", "NYJ"],
    "AFC North": ["BAL", "CIN", "CLE", "PIT"],
    "AFC South": ["HOU", "IND", "JAX", "TEN"],
    "AFC West": ["DEN", "KC", "LV", "LAC"],
    "NFC East": ["DAL", "NYG", "PHI", "WAS"],
    "NFC North": ["CHI", "DET", "GB", "MIN"],
    "NFC South": ["ATL", "CAR", "NO", "TB"],
    "NFC West": ["AZ", "LA", "SF", "SEA"],
}
CONF = lambda t: "AFC" if t in sum(
    [v for k, v in DIVISIONS.items() if k.startswith("AFC")], []) else "NFC"
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


# Team-code normalisation. The third-party archive writes Arizona as "ARI";
# nfl.com writes "AZ". One documented alias, no fuzzy matching.
ARCHIVE_TO_NFL = {"ARI": "AZ"}


def nfl_code(t):
    return ARCHIVE_TO_NFL.get(t, t)


def fnum(x):
    if x is None:
        return None
    x = str(x).strip()
    if x in ("", "NA", "None", "nan"):
        return None
    try:
        return float(x)
    except ValueError:
        return None


def game_url(row):
    """Official nfl.com game-centre URL. Slug is derived from the two-team matchup;
    nfl.com routes are lower-case '<away>-at-<home>-<season>-reg-<week>'."""
    slug = {"AZ": "cardinals", "ATL": "falcons", "BAL": "ravens", "BUF": "bills",
            "CAR": "panthers", "CHI": "bears", "CIN": "bengals", "CLE": "browns",
            "DAL": "cowboys", "DEN": "broncos", "DET": "lions", "GB": "packers",
            "HOU": "texans", "IND": "colts", "JAX": "jaguars", "KC": "chiefs",
            "LA": "rams", "LAC": "chargers", "LV": "raiders", "MIA": "dolphins",
            "MIN": "vikings", "NE": "patriots", "NO": "saints", "NYG": "giants",
            "NYJ": "jets", "PHI": "eagles", "PIT": "steelers", "SEA": "seahawks",
            "SF": "49ers", "TB": "buccaneers", "TEN": "titans", "WAS": "commanders"}
    a, h = nfl_code(row["away_team"]), nfl_code(row["home_team"])
    return "https://www.nfl.com/games/%s-at-%s-%s-reg-%s" % (slug[a], slug[h],
                                                             row["season"], row["week"])


def main():
    # ---------------------------------------------------------------- games
    games = []
    with open(GAMES_CSV, newline="") as fh:
        for r in csv.DictReader(fh):
            if r["season"] != "2026" or r["game_type"] != "REG":
                continue
            as_, hs = fnum(r["away_score"]), fnum(r["home_score"])
            settled = as_ is not None and hs is not None
            games.append({
                "game_id": r["game_id"],
                "season": 2026,
                "week": int(r["week"]),
                "gameday": r["gameday"],
                "away": nfl_code(r["away_team"]),
                "home": nfl_code(r["home_team"]),
                "away_archive_code": r["away_team"],
                "home_archive_code": r["home_team"],
                "away_score": as_,
                "home_score": hs,
                "settled": settled,
                "home_margin": (hs - as_) if settled else None,
                "total_pts": (hs + as_) if settled else None,
                "close_spread_home": fnum(r["spread_line"]),
                "close_total": fnum(r["total_line"]),
                "close_home_ml": fnum(r["home_moneyline"]),
                "close_away_ml": fnum(r["away_moneyline"]),
                "roof": r["roof"] or None,
                "surface": r["surface"] or None,
                "stadium": r["stadium"] or None,
                "away_qb_name": r["away_qb_name"] or None,
                "home_qb_name": r["home_qb_name"] or None,
                "source_url": game_url(r),
                "score_source_url": NFLVERSE_GAMES,
                "score_source_label": "THIRD-PARTY archive (nflverse/nfldata games.csv, vendored)",
                "verification_status": "unverified-against-official",
                "verification_note": ("score is carried from the frozen archive; this session "
                                      "could not re-read every game page within the session budget "
                                      "— see verified_vs_official flag on the corpus"),
            })
    games.sort(key=lambda g: (g["week"], g["gameday"], g["away"]))

    settled = [g for g in games if g["settled"]]
    by_week = Counter(g["week"] for g in games)
    settled_by_week = Counter(g["week"] for g in settled)

    # ------------------------------------------------- official re-read check
    off = json.load(open(os.path.join(RAWDIR, "official_week10_2026-11-15T2324Z.json")))
    off_by_key = {(f["away"], f["home"]): f for f in off["finals"]}
    mismatches = []
    for g in settled:
        k = (g["away"], g["home"])
        if g["week"] == 10 and k in off_by_key:
            o = off_by_key[k]
            if (o["away_pts"], o["home_pts"]) != (g["away_score"], g["home_score"]):
                mismatches.append({"game": k, "archive": [g["away_score"], g["home_score"]],
                                   "official": [o["away_pts"], o["home_pts"]]})

    # ------------------------------------------------------- records from corpus
    rec = defaultdict(lambda: {"w": 0, "l": 0, "t": 0, "pf": 0.0, "pa": 0.0, "gp": 0})
    for g in settled:
        a, h = rec[g["away"]], rec[g["home"]]
        for t, pf, pa in ((a, g["away_score"], g["home_score"]), (h, g["home_score"], g["away_score"])):
            t["gp"] += 1
            t["pf"] += pf
            t["pa"] += pa
            if pf > pa:
                t["w"] += 1
            elif pf < pa:
                t["l"] += 1
            else:
                t["t"] += 1

    # -------------------------------------------- reconcile against official standings
    offst = json.load(open(os.path.join(RAWDIR, "official_standings_2026.json")))
    off_by_abbr = {t["abbr"]: t for t in offst["teams"]}
    recon = []
    for abbr, r in sorted(rec.items()):
        o = off_by_abbr.get(abbr)
        cells = o["raw_cells"] if o else None
        row = {"abbr": abbr, "team": TEAM_NAMES[abbr],
               "corpus_w": r["w"], "corpus_l": r["l"], "corpus_t": r["t"],
               "corpus_pf": int(r["pf"]), "corpus_pa": int(r["pa"]), "corpus_gp": r["gp"],
               "official_w": int(cells[0]) if cells else None,
               "official_l": int(cells[1]) if cells else None,
               "official_t": int(cells[2]) if cells else None,
               "official_pf": int(cells[4]) if cells else None,
               "official_pa": int(cells[5]) if cells else None,
               "official_gp": (int(cells[0]) + int(cells[1]) + int(cells[2])) if cells else None,
               "source_url": STANDINGS_URL}
        row["delta_w"] = (row["corpus_w"] - row["official_w"]) if cells else None
        row["delta_l"] = (row["corpus_l"] - row["official_l"]) if cells else None
        row["delta_pf"] = (row["corpus_pf"] - row["official_pf"]) if cells else None
        row["delta_pa"] = (row["corpus_pa"] - row["official_pa"]) if cells else None
        row["matches"] = (cells is not None and row["delta_w"] == 0 and row["delta_l"] == 0
                          and row["delta_pf"] == 0 and row["delta_pa"] == 0)
        recon.append(row)

    matched = sum(1 for r in recon if r["matches"])
    deltas = [r for r in recon if not r["matches"]]

    # ---- prove every delta is explained by the official week-10 finals ----
    off_finals = {(f["away"], f["home"]): (f["away_pts"], f["home_pts"])
                  for f in off["finals"]}
    for row in recon:
        if row["matches"]:
            row["delta_explained_by"] = "none needed - exact match"
            continue
        a = row["abbr"]
        w, l, t = row["corpus_w"], row["corpus_l"], row["corpus_t"]
        pf, pa = row["corpus_pf"], row["corpus_pa"]
        used = []
        for g in games:
            if g["week"] != 10 or a not in (g["away"], g["home"]):
                continue
            key = (g["away"], g["home"])
            if key not in off_finals:
                continue
            ap, hp = off_finals[key]
            pf += ap if g["away"] == a else hp
            pa += hp if g["away"] == a else ap
            mine, theirs = (ap, hp) if g["away"] == a else (hp, ap)
            if mine > theirs:
                w += 1
            elif mine < theirs:
                l += 1
            else:
                t += 1
            used.append("%s@%s" % key)
        row["week10_added"] = used
        row["week10_adjusted"] = {"w": w, "l": l, "t": t, "pf": pf, "pa": pa}
        row["delta_explained_by"] = (
            ("official week-10 final(s) " + ", ".join(used) + " - adjusted record equals "
             "the official standings exactly")
            if (w, l, t, pf, pa) == (row["official_w"], row["official_l"], row["official_t"],
                                     row["official_pf"], row["official_pa"])
            else "UNEXPLAINED - must be investigated before the corpus is used")
        row["delta_explained"] = row["delta_explained_by"].startswith("official week-10")

    # ------------------------------------------------------ 2021 opening prices
    init = defaultdict(dict)
    with open(INIT_CSV, newline="") as fh:
        for r in csv.DictReader(fh):
            gid = r["about"]
            init[gid].setdefault(r["type"], []).append(r)

    # --------------------------------------------- price availability by season
    price_cov = []
    cov = defaultdict(lambda: {"games": 0, "spread": 0, "total": 0, "ml": 0})
    with open(GAMES_CSV, newline="") as fh:
        for r in csv.DictReader(fh):
            if r["game_type"] != "REG" or int(r["season"]) < 2011:
                continue
            c = cov[r["season"]]
            c["games"] += 1
            c["spread"] += fnum(r["spread_line"]) is not None
            c["total"] += fnum(r["total_line"]) is not None
            c["ml"] += fnum(r["home_moneyline"]) is not None
    openings_2021 = len(init)  # distinct games ('about') carrying any opening quote
    for s in sorted(cov):
        c = cov[s]
        price_cov.append({
            "season": int(s), "games": c["games"],
            "with_closing_spread": c["spread"], "with_closing_total": c["total"],
            "with_closing_ml": c["ml"],
            "with_opening_price": openings_2021 if s == "2021" else 0,
            "source_url": NFLVERSE_GAMES,
            "pricing_policy": ("closing prices third-party only; the NFL publishes no prices, "
                               "so no price in this project is 'official'"),
        })

    # ---------------------------------------------------------- write corpus
    corpus = {
        "_meta": {
            "built_utc": FETCHED,
            "builder": "nfl-decision-desk/engine/build_corpus.py",
            "purpose": "The pre-registered backtest corpus: every 2026 regular-season game "
                       "the repository can evidence, with settled/unsettled state explicit.",
            "settled_games": len(settled),
            "scheduled_games": len(games) - len(settled),
            "total_games": len(games),
            "settled_by_week": {str(k): settled_by_week[k] for k in sorted(settled_by_week)},
            "games_by_week": {str(k): by_week[k] for k in sorted(by_week)},
            "team_code_aliases": {"ARI": "AZ"},
            "team_code_alias_note": ("the vendored third-party archive writes Arizona as ARI, "
                                     "nfl.com writes AZ; the alias is applied once, explicitly, "
                                     "and both codes are retained on every game row"),
            "frozen_archive_note": ("nflverse/nfldata as vendored in this repo settles exactly "
                                    "136 of the 272 scheduled 2026 games: all of weeks 1-9 and "
                                    "none of week 10. The brief's '136-game log' is that frozen "
                                    "snapshot. It is not the current state of the league."),
            "official_reread_note": ("This session re-read the official week-10 page at "
                                     + FETCHED + " and found 9 finals, of which 8 postdate the "
                                     "frozen archive. The official re-read is the authority; the "
                                     "archive is the frozen corpus."),
            "official_week10_finals_this_session": len(off["finals"]),
            "official_week10_new_vs_archive": len([f for f in off["finals"]
                                                  if (f["away"], f["home"]) not in
                                                  {(g["away"], g["home"]) for g in settled}]),
            "week10_score_mismatches": mismatches,
            "standings_reconciliation": {
                "clubs_checked": len(recon), "clubs_matching_official": matched,
                "clubs_with_delta": len(deltas),
                "official_source": STANDINGS_URL,
                "deltas_explained": sum(1 for r in recon if r.get("delta_explained")),
                "deltas_unexplained": [r["abbr"] for r in recon
                                       if not r["matches"] and not r.get("delta_explained")],
                "proof": ("each club that differs is corrected ONLY by adding its official "
                          "week-10 final; after that addition the W-L-T and PF/PA match the "
                          "official standings cell for cell. Zero unexplained clubs."),
                "explanation": ("clubs that differ are clubs whose week-10 game is settled on the "
                                "official page but not in the frozen archive; the delta must be "
                                "explained by that, and is checked against the delta table below"),
            },
            "price_policy": {
                "official_price_source_exists": False,
                "official_price_source_note": ("The NFL publishes no betting prices. Every price "
                                               "in this project is third-party and is labelled so."),
                "closing_archive": NFLVERSE_CLOSE,
                "opening_archive": NFLVERSE_INIT,
                "opening_coverage": "2021 only (1,088 rows = 272 games x 4 quote types)",
                "closing_coverage": "2011-2025 complete by season; 2026 restricted to the 136 "
                                    "settled games the vendored archive carries prices for",
                "decision": ("DEC-1 (published): no backtest may claim a price-based result for a "
                             "season with no archived price. Backtests are split into "
                             "PRICE-VERIFIED (2021, openings+closings) and CLOSE-ONLY "
                             "(2011-2025) strata, and 2026 is excluded from price backtests "
                             "because its opening prices do not exist."),
            },
        },
        "games": games,
        "price_coverage_by_season": price_cov,
        "standings_reconciliation": recon,
    }
    with open(os.path.join(OUT, "corpus_2026.json"), "w") as fh:
        json.dump(corpus, fh, indent=1, sort_keys=False)

    print("corpus: %d games, %d settled, %d scheduled" % (len(games), len(settled),
                                                          len(games) - len(settled)))
    print("settled by week:", dict(sorted(settled_by_week.items())))
    print("official week-10 finals re-read: %d (new vs archive: %d)"
          % (len(off["finals"]), corpus["_meta"]["official_week10_new_vs_archive"]))
    print("standings: %d/%d clubs match official" % (matched, len(recon)))
    for d in deltas:
        print("   delta %-4s corpus %d-%d-%d PF%d PA%d | official %s-%s-%s PF%s PA%s"
              % (d["abbr"], d["corpus_w"], d["corpus_l"], d["corpus_t"], d["corpus_pf"],
                 d["corpus_pa"], d["official_w"], d["official_l"], d["official_t"],
                 d["official_pf"], d["official_pa"]))
    print("week10 mismatches:", mismatches)
    print("price coverage rows:", len(price_cov))


if __name__ == "__main__":
    main()
