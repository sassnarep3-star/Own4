"""Shared loaders and integrity checks for the NFL Line Genesis hub.

Data provenance: data/source/games.csv and closing_lines.csv are snapshots of
github.com/nflverse/nfldata (see data/source/provenance.json). They are a
third-party archive, not an official NFL publication. The 2026 scores are
reconciled against NFL.com official standings in pipeline/run_all.py.
"""
from __future__ import annotations

import csv
import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
SOURCE = os.path.join(DATA, "source")

FIELDS = [
    "game_id", "season", "game_type", "week", "gameday", "away_team", "home_team",
    "away_score", "home_score", "result", "total", "spread_line", "total_line",
    "away_moneyline", "home_moneyline", "away_rest", "home_rest", "div_game",
]


def _num(v, cast=int):
    try:
        if v is None or str(v).strip() == "":
            return None
        return cast(str(v).strip())
    except (TypeError, ValueError):
        return None


def load_games(include_unplayed: bool = True):
    """Return regular-season games sorted chronologically, with typed fields."""
    out = []
    with open(os.path.join(SOURCE, "games.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("game_type") != "REG":
                continue
            g = {
                "game_id": r["game_id"],
                "season": _num(r["season"]),
                "week": _num(r["week"]),
                "date": r["gameday"],
                "away": r["away_team"],
                "home": r["home_team"],
                "away_score": _num(r["away_score"]),
                "home_score": _num(r["home_score"]),
                "result": _num(r["result"]),
                "total": _num(r["total"]),
                "spread": _num(r["spread_line"], float),
                "total_line": _num(r["total_line"], float),
                "away_ml": _num(r["away_moneyline"], float),
                "home_ml": _num(r["home_moneyline"], float),
                "away_spread_odds": _num(r["away_spread_odds"], float),
                "home_spread_odds": _num(r["home_spread_odds"], float),
                "over_odds": _num(r["over_odds"], float),
                "under_odds": _num(r["under_odds"], float),
                "away_rest": _num(r["away_rest"]),
                "home_rest": _num(r["home_rest"]),
                "div": _num(r["div_game"]) or 0,
            }
            if not include_unplayed and g["result"] is None:
                continue
            out.append(g)
    out.sort(key=lambda g: (g["season"], g["week"], g["date"], g["game_id"]))
    return out


def integrity_checks(games):
    """Gate G1: structural integrity of the archive. Returns a report dict."""
    ids = defaultdict(int)
    problems = []
    for g in games:
        ids[g["game_id"]] += 1
    dupes = [k for k, v in ids.items() if v > 1]
    if dupes:
        problems.append({"check": "unique game_id", "detail": f"{len(dupes)} duplicate ids", "severity": "fail"})

    bad_scores, bad_margin, bad_total, impossible = [], [], [], []
    for g in games:
        if g["result"] is None:
            continue
        if g["home_score"] is None or g["away_score"] is None:
            bad_scores.append(g["game_id"])
            continue
        m = g["home_score"] - g["away_score"]
        if g["result"] != m:
            bad_margin.append(g["game_id"])
        if g["total"] != g["home_score"] + g["away_score"]:
            bad_total.append(g["game_id"])
        if g["home_score"] < 0 or g["away_score"] < 0:
            impossible.append(g["game_id"])

    played = [g for g in games if g["result"] is not None]
    with_line = [g for g in played if g["spread"] is not None]
    with_total = [g for g in played if g["total_line"] is not None]
    with_ml = [g for g in played if g["home_ml"] is not None and g["away_ml"] is not None]

    seasons = sorted({g["season"] for g in games})
    report = {
        "gate": "G1",
        "duplicate_game_ids": len(dupes),
        "score_margin_mismatches": len(bad_margin),
        "total_mismatches": len(bad_total),
        "missing_scores": len(bad_scores),
        "negative_scores": len(impossible),
        "games_total": len(games),
        "games_played": len(played),
        "games_with_closing_spread": len(with_line),
        "games_with_closing_total": len(with_total),
        "games_with_both_moneylines": len(with_ml),
        "season_range": [seasons[0], seasons[-1]],
        "chronological": all(
            (a["season"], a["week"]) <= (b["season"], b["week"]) for a, b in zip(games, games[1:])
        ),
        "problems": problems,
        "passed": not problems and not bad_margin and not bad_total and not bad_scores and not impossible,
        "limits": [
            "Closing lines are a third-party archive; no official NFL odds publication exists.",
            "Moneyline/odds coverage differs by season and is reported rather than imputed.",
        ],
    }
    return report


def save_json(name, obj):
    path = os.path.join(DATA, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=False)
        f.write("\n")
    return path


def american_to_prob(odds):
    """Convert American odds to implied probability (with vig if paired)."""
    if odds is None:
        return None
    if odds < 0:
        return (-odds) / ((-odds) + 100.0)
    return 100.0 / (odds + 100.0)


def american_payout(odds):
    """Profit on a 1-unit stake at American odds (assumes win)."""
    if odds is None:
        return None
    return (100.0 / (-odds)) if odds < 0 else (odds / 100.0)
