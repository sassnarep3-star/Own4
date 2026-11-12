"""Dataset loading, official cross-verification and integrity checks.

Every number produced by this module is either
  (a) read from an official NFL.com page transcribed into data/official/*.json, or
  (b) read from the third-party archive data/raw/nfldata_games.csv, which is
      spot-checked against official NFL.com score pages before use.
Nothing is inferred, imputed or synthesised.
"""
from __future__ import annotations

import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
RAW = os.path.join(DATA, "raw")
OFFICIAL = os.path.join(DATA, "official")
DERIVED = os.path.join(DATA, "derived")

ARCHIVE_FILE = os.path.join(RAW, "nfldata_games.csv")


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def dump_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, sort_keys=False)
        fh.write("\n")


def load_archive():
    """Return the raw third-party game archive as a list of dicts."""
    with open(ARCHIVE_FILE, "r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _int(v):
    if v is None or v == "" or v == "NA":
        return None
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def _float(v):
    if v is None or v == "" or v == "NA":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def normalise_archive(rows):
    """Project the archive onto the fields used here. No value is invented."""
    out = []
    for r in rows:
        home, away = r["home_team"], r["away_team"]
        hs, as_ = _int(r["home_score"]), _int(r["away_score"])
        out.append({
            "game_id": r["game_id"],
            "season": _int(r["season"]),
            "game_type": r["game_type"],
            "week": _int(r["week"]),
            "gameday": r["gameday"],
            "home": home,
            "away": away,
            "home_score": hs,
            "away_score": as_,
            "margin": None if (hs is None or as_ is None) else hs - as_,
            "total": None if (hs is None or as_ is None) else hs + as_,
            "location": r["location"],
            "roof": r["roof"],
            "surface": r["surface"],
            "temp": _int(r["temp"]),
            "wind": _int(r["wind"]),
            "home_rest": _float(r["home_rest"]),
            "away_rest": _float(r["away_rest"]),
            "div_game": _int(r["div_game"]),
            "home_qb": r["home_qb_name"],
            "away_qb": r["away_qb_name"],
            "spread_line": _float(r["spread_line"]),
            "total_line": _float(r["total_line"]),
            "home_moneyline": _float(r["home_moneyline"]),
            "away_moneyline": _float(r["away_moneyline"]),
            "home_spread_odds": _float(r["home_spread_odds"]),
            "away_spread_odds": _float(r["away_spread_odds"]),
            "over_odds": _float(r["over_odds"]),
            "under_odds": _float(r["under_odds"]),
        })
    return out


def verify_against_official(games):
    """Compare the archive to the official NFL.com transcription, game by game."""
    sc = load_json(os.path.join(OFFICIAL, "score_spotcheck_2026.json"))
    by_key = {}
    for g in games:
        if g["season"] == 2026 and g["game_type"] == "REG":
            by_key[(g["week"], g["away"], g["home"])] = g

    checks, matched, mismatched, missing = [], 0, 0, 0
    for row in sc["games"]:
        # NFL.com writes the Rams as LA and the Cardinals as ARI in some tables;
        # the archive writes LA (Rams) and ARI (Cardinals).
        _AB = {"AZ": "ARI", "ARI": "AZ", "LA": "LAR", "LAR": "LA"}
        key = (row["week"], row["away"], row["home"])
        alt = (row["week"], _AB.get(row["away"], row["away"]), _AB.get(row["home"], row["home"]))
        g = by_key.get(key) or by_key.get(alt)
        rec = {
            "week": row["week"],
            "matchup": f'{row["away"]} @ {row["home"]}',
            "source": sc["source_urls"]["week_%d" % row["week"]],
            "official_away_score": row["away_score"],
            "official_home_score": row["home_score"],
        }
        if g is None:
            rec.update(archive_away_score=None, archive_home_score=None, result="missing_in_archive")
            missing += 1
        else:
            rec.update(archive_away_score=g["away_score"], archive_home_score=g["home_score"])
            if g["away_score"] == row["away_score"] and g["home_score"] == row["home_score"]:
                rec["result"] = "match"
                matched += 1
            else:
                rec["result"] = "mismatch"
                mismatched += 1
        checks.append(rec)

    return {
        "weeks_checked": sc["weeks_checked"],
        "games_compared": len(checks),
        "matched": matched,
        "mismatched": mismatched,
        "missing_in_archive": missing,
        "match_rate": round(matched / len(checks), 4) if checks else None,
        "checks": checks,
        "weeks_attempted_not_usable": sc["weeks_attempted_not_usable"],
    }


def integrity_checks(games, standings):
    """Self-consistency checks that do not require any external value."""
    out = []

    def add(cid, desc, passed, detail):
        out.append({"id": cid, "check": desc, "passed": bool(passed), "detail": detail})

    reg26 = [g for g in games if g["season"] == 2026 and g["game_type"] == "REG"]
    played = [g for g in reg26 if g["margin"] is not None]
    add("IC-01", "2026 regular-season schedule contains 272 games",
        len(reg26) == 272, "found %d" % len(reg26))
    add("IC-02", "No 2026 regular-season game is missing a final score beyond the current week",
        all(g["margin"] is not None for g in reg26 if g["week"] <= 9),
        "%d of %d Week 1-9 games have final scores"
        % (sum(1 for g in reg26 if g["week"] <= 9 and g["margin"] is not None),
           sum(1 for g in reg26 if g["week"] <= 9)))
    add("IC-03", "No Week 10+ 2026 game has a score (season is at Week 10)",
        all(g["margin"] is None for g in reg26 if g["week"] >= 10),
        "%d future/this-week games carry no score"
        % sum(1 for g in reg26 if g["week"] >= 10 and g["margin"] is None))

    # standings derived from the archive vs the official standings table
    derived = {}
    for g in played:
        for side, opp in (("home", "away"), ("away", "home")):
            d = derived.setdefault(g[side], {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0})
            d["pf"] += g[side + "_score"]
            d["pa"] += g[opp + "_score"]
            if g["margin"] == 0:
                d["t"] += 1
            elif (g["margin"] > 0) == (side == "home"):
                d["w"] += 1
            else:
                d["l"] += 1

    _AB = {"AZ": "ARI", "LA": "LAR"}
    rows = {}
    for r in standings["rows"]:
        rows[r[1]] = {"w": r[2], "l": r[3], "t": r[4], "pf": r[6], "pa": r[7]}

    bad = []
    for abbr, off in rows.items():
        got = derived.get(abbr) or derived.get(_AB.get(abbr, abbr))
        if got is None:
            bad.append("%s missing from played games" % abbr)
            continue
        if (got["w"], got["l"], got["t"], got["pf"], got["pa"]) != (
                off["w"], off["l"], off["t"], off["pf"], off["pa"]):
            bad.append("%s archive %s vs official %s" % (abbr, got, off))
    add("IC-04", "W/L/T/PF/PA recomputed from the game archive match the official standings table for all 32 teams",
        not bad, "all 32 teams match" if not bad else "; ".join(bad))

    total_pf = sum(r[6] for r in standings["rows"])
    total_pa = sum(r[7] for r in standings["rows"])
    add("IC-05", "Official standings points-for equals points-against across the league",
        total_pf == total_pa, "PF=%d PA=%d" % (total_pf, total_pa))

    with_line = [g for g in played if g["spread_line"] is not None]
    add("IC-06", "Every completed 2026 game in the archive carries a closing spread",
        len(with_line) == len(played), "%d of %d" % (len(with_line), len(played)))

    hist = [g for g in games if g["game_type"] == "REG" and g["margin"] is not None]
    seasons = sorted(set(g["season"] for g in hist))
    add("IC-07", "Archive covers 1999-2026 regular seasons",
        seasons[0] == 1999 and seasons[-1] == 2026, "seasons %d-%d" % (seasons[0], seasons[-1]))

    return out


def team_name_map():
    """Join NFL.com team names to archive abbreviations."""
    st = load_json(os.path.join(OFFICIAL, "standings_2026.json"))
    return {r[0]: r[1] for r in st["rows"]}
