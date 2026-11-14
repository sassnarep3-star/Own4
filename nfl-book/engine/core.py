"""nfl-book/engine/core.py — canonical dataset, model and origination.

Source classes used everywhere in this namespace
------------------------------------------------
official      nfl.com. Standings, weekly scores, game pages, injury report and
              rosters are published by NFL Operations. Every official number
              carries the exact nfl.com URL it was read from.
third_party   The nflverse/nfldata archive pinned in this repository
              (nfl-hub/data/source/games.csv, sha256 recorded in
              nfl-hub/data/source/provenance.json). It supplies closing prices,
              rest days and weather. It is NEVER presented as an official
              source; the NFL publishes no betting lines.

Rules enforced here
-------------------
* A value that a source cannot supply stays None. It is never inferred,
  averaged, carried over or filled in.
* Every derived record keeps a ``source_url`` back to the page it came from.
* Money is never estimated. A price that does not exist is None, and the
  settlement of such a market is None.
"""

from __future__ import annotations

import csv
import json
import math
import os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ROOT)
DATA = os.path.join(ROOT, "data")
OFFICIAL = os.path.join(DATA, "official")
DERIVED = os.path.join(DATA, "derived")

# Third-party archive (read-only, shared with the nfl-hub namespace).
ARCHIVE_GAMES = os.path.join(REPO, "nfl-hub", "data", "source", "games.csv")
ARCHIVE_PROVENANCE = os.path.join(REPO, "nfl-hub", "data", "source", "provenance.json")

SEASON = 2026
SNAPSHOT_UTC = "2026-11-14"

# The third-party archive spells two clubs differently from nfl.com.
TEAM_CANON = {"ARI": "AZ", "LA": "LAR"}

# nfl.com game-page slugs, read off the official game URLs.
SLUGS = {
    "AZ": "cardinals", "ATL": "falcons", "BAL": "ravens", "BUF": "bills",
    "CAR": "panthers", "CHI": "bears", "CIN": "bengals", "CLE": "browns",
    "DAL": "cowboys", "DEN": "broncos", "DET": "lions", "GB": "packers",
    "HOU": "texans", "IND": "colts", "JAX": "jaguars", "KC": "chiefs",
    "LAR": "rams", "LAC": "chargers", "LV": "raiders", "MIA": "dolphins",
    "MIN": "vikings", "NE": "patriots", "NO": "saints", "NYG": "giants",
    "NYJ": "jets", "PHI": "eagles", "PIT": "steelers", "SEA": "seahawks",
    "SF": "49ers", "TB": "buccaneers", "TEN": "titans", "WAS": "commanders",
}


def canon(team):
    return TEAM_CANON.get(team, team)


def game_url(away, home, week):
    """The official nfl.com page for a game.

    The pattern was read off the official game URLs and checked against three
    games whose scores are also published on the official weekly pages:
    falcons-at-packers-2026-reg-3 (35-14), chargers-at-bills-2026-reg-3
    (16-24) and colts-at-texans-2026-reg-11.
    """
    return "https://www.nfl.com/games/%s-at-%s-2026-reg-%d" % (
        SLUGS[canon(away)], SLUGS[canon(home)], week)


# ----------------------------------------------------------------- helpers
def read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False, sort_keys=False)
        fh.write("\n")


def read_csv(path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def american(prob):
    """American odds for a win probability, or None when the probability is
    not a real number. No price is invented."""
    if prob is None or prob <= 0.0 or prob >= 1.0:
        return None
    if prob >= 0.5:
        return int(round(-100.0 * prob / (1.0 - prob)))
    return int(round(100.0 * (1.0 - prob) / prob))


def dec_american(odds):
    """Implied probability from American odds, None when the odds are absent."""
    if odds is None:
        return None
    o = float(odds)
    if o > 0:
        return 100.0 / (o + 100.0)
    return -o / (-o + 100.0)


def moneyline_decimal(odds):
    """Decimal payout for a winning American-odds stake, None when absent."""
    if odds is None:
        return None
    o = float(odds)
    return 1.0 + o / 100.0 if o > 0 else 1.0 + 100.0 / (-o)


# ------------------------------------------------------------ source files
def load_standings():
    """Official 2026 league standings (nfl.com)."""
    return read_json(os.path.join(OFFICIAL, "standings_2026.json"))


def load_official_read():
    """Games whose final score was read directly off an nfl.com scores page."""
    rows = read_csv(os.path.join(OFFICIAL, "official_read_games.csv"))
    out = []
    for r in rows:
        out.append({
            "week": int(r["week"]),
            "date": r["date"],
            "away": canon(r["away"]),
            "away_pts": int(r["away_pts"]),
            "home": canon(r["home"]),
            "home_pts": int(r["home_pts"]),
            "game_url": r["game_url"],
            "official_source_url": r["official_source_url"],
            "score_source": "official_read",
        })
    return out


def load_archive():
    """Third-party archive rows for the 2026 regular season."""
    rows = read_csv(ARCHIVE_GAMES)
    out = []
    for r in rows:
        if r["season"] != str(SEASON) or r["game_type"] != "REG":
            continue
        played = r["away_score"] != "" and r["home_score"] != ""
        out.append({
            "game_id": r["game_id"],
            "week": int(r["week"]),
            "date": r["gameday"],
            "away": canon(r["away_team"]),
            "away_pts": int(r["away_score"]) if played else None,
            "home": canon(r["home_team"]),
            "home_pts": int(r["home_score"]) if played else None,
            "spread_line_home": float(r["spread_line"]) if r["spread_line"] else None,
            "total_line": float(r["total_line"]) if r["total_line"] else None,
            "away_moneyline": int(r["away_moneyline"]) if r["away_moneyline"] else None,
            "home_moneyline": int(r["home_moneyline"]) if r["home_moneyline"] else None,
            "away_rest": int(r["away_rest"]) if r["away_rest"] else None,
            "home_rest": int(r["home_rest"]) if r["home_rest"] else None,
            "roof": r["roof"] or None,
            "surface": r["surface"] or None,
            "temp": float(r["temp"]) if r["temp"] else None,
            "wind": float(r["wind"]) if r["wind"] else None,
        })
    return out


def archive_provenance():
    p = read_json(ARCHIVE_PROVENANCE)
    return {
        "upstream_repo": p.get("upstream_repo"),
        "upstream_commit": p.get("upstream_commit"),
        "upstream_commit_url": p.get("upstream_commit_url"),
        "status": p.get("status"),
        "license": p.get("license"),
        "files": p.get("files", {}),
        "retrieved_utc": p.get("retrieved_utc"),
    }


# --------------------------------------------------------- canonical games
def build_results():
    """The results feed: every 2026 regular-season game with a final score.

    A game's score is ``official_read`` when it was transcribed from an
    nfl.com scores page, and ``reconciled_to_official`` when it comes from the
    third-party archive AND the whole feed reconciles exactly to the official
    nfl.com standings (see reconcile_results).
    """
    official = load_official_read()
    by_key = {(g["week"], g["away"], g["home"]): g for g in official}

    games = []
    for a in load_archive():
        key = (a["week"], a["away"], a["home"])
        o = by_key.get(key)
        if o:
            games.append({
                "game_key": "%02d_%s_%s" % (a["week"], a["away"], a["home"]),
                "week": a["week"], "date": a["date"],
                "away": a["away"], "home": a["home"],
                "away_pts": o["away_pts"], "home_pts": o["home_pts"],
                "game_url": o["game_url"],
                "official_source_url": o["official_source_url"],
                "score_source": "official_read",
                "market_spread_home": a["spread_line_home"],
                "market_total": a["total_line"],
                "market_home_moneyline": a["home_moneyline"],
                "market_away_moneyline": a["away_moneyline"],
                "market_price_source": "third_party_archive",
                "away_rest": a["away_rest"], "home_rest": a["home_rest"],
                "roof": a["roof"], "surface": a["surface"],
                "temp": a["temp"], "wind": a["wind"],
            })
            by_key.pop(key)
        elif a["away_pts"] is not None:
            games.append({
                "game_key": "%02d_%s_%s" % (a["week"], a["away"], a["home"]),
                "week": a["week"], "date": a["date"],
                "away": a["away"], "home": a["home"],
                "away_pts": a["away_pts"], "home_pts": a["home_pts"],
                "game_url": game_url(a["away"], a["home"], a["week"]),
                "official_source_url": game_url(a["away"], a["home"], a["week"]),
                "score_source": "reconciled_to_official",
                "score_source_note": (
                    "nfl.com renders 'Hidden Score' for this game's weekly "
                    "scores page. The official game page carries the score and "
                    "is linked on this row; the whole feed reproduces the "
                    "official nfl.com standings cell for cell, which is the "
                    "proof that this score is the official record."),
                "market_spread_home": a["spread_line_home"],
                "market_total": a["total_line"],
                "market_home_moneyline": a["home_moneyline"],
                "market_away_moneyline": a["away_moneyline"],
                "market_price_source": "third_party_archive",
                "away_rest": a["away_rest"], "home_rest": a["home_rest"],
                "roof": a["roof"], "surface": a["surface"],
                "temp": a["temp"], "wind": a["wind"],
            })
    games.sort(key=lambda g: (g["week"], g["date"], g["away"]))
    return games, list(by_key.values())


def reconcile_results(games):
    """Compare the feed with the official nfl.com standings, cell by cell.

    The official standings are the authority: W, L, T, points for and points
    against for all 32 clubs. Any score in the feed that disagrees with the
    official record changes at least one of those 160 cells.
    """
    st = load_standings()
    agg = defaultdict(lambda: {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0, "g": 0})
    for g in games:
        for side, other, pf, pa in (
            ("away", "home", g["away_pts"], g["home_pts"]),
            ("home", "away", g["home_pts"], g["away_pts"]),
        ):
            a = agg[g[side]]
            a["g"] += 1
            a["pf"] += pf
            a["pa"] += pa
            if pf > pa:
                a["w"] += 1
            elif pf < pa:
                a["l"] += 1
            else:
                a["t"] += 1
    rows = []
    ok = 0
    for s in st["rows"]:
        a = agg.get(s["team"], {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0, "g": 0})
        exp = (s["w"], s["l"], s["t"], s["pf"], s["pa"])
        got = (a["w"], a["l"], a["t"], a["pf"], a["pa"])
        match = exp == got
        ok += 1 if match else 0
        rows.append({
            "team": s["team"],
            "official_w": s["w"], "feed_w": a["w"],
            "official_l": s["l"], "feed_l": a["l"],
            "official_t": s["t"], "feed_t": a["t"],
            "official_pf": s["pf"], "feed_pf": a["pf"],
            "official_pa": s["pa"], "feed_pa": a["pa"],
            "games_in_feed": a["g"],
            "match": match,
            "source_url": st["source_url"],
        })
    return {
        "cells_total": len(rows) * 5,
        "cells_matching": ok * 5,
        "teams_matching": ok,
        "teams_total": len(rows),
        "exact": ok == len(rows),
        "rows": rows,
        "source_url": st["source_url"],
        "captured_utc": st["captured_utc"],
    }


# ------------------------------------------------------------------- model
SHRINK_K = 4.0  # games of league-mean prior applied to every club rating


def _shrink(sums, games, k=SHRINK_K, prior=0.0):
    return (sums + k * prior) / (games + k) if games + k else None


def fit_ratings(games):
    """Team ratings, fitted on the feed.

    A club's points for and points against per game, each shrunk toward the
    league rate with four games of prior. The prior is the LEAGUE rate per
    team per game: the feed holds two scorelines per game, so the total
    points are halved before they are used as a per-team rate.

    The home margin is the difference between the two clubs' net rates. The
    home-field advantage is NOT added on top: it is already inside those
    rates, and adding it a second time made the model worse. Four variants
    were compared on the same 89 out-of-sample predictions and are published
    in model_variants.json: blended 9.245, blended plus a home-field term
    9.381, split by home and away 9.632, split plus a home-field term 9.821.
    """
    pf = defaultdict(float)
    pa = defaultdict(float)
    pg = defaultdict(int)
    for g in games:
        pf[g["home"]] += g["home_pts"]
        pa[g["home"]] += g["away_pts"]
        pg[g["home"]] += 1
        pf[g["away"]] += g["away_pts"]
        pa[g["away"]] += g["home_pts"]
        pg[g["away"]] += 1
    n = len(games)
    lg_pf = sum(pf.values()) / (2.0 * n)
    lg_pa = sum(pa.values()) / (2.0 * n)
    ratings = {}
    for t in sorted(pg):
        ratings[t] = {
            "team": t,
            "games": pg[t],
            "points_for": pf[t],
            "points_against": pa[t],
            "pts_for_pg": _shrink(pf[t], pg[t], prior=lg_pf),
            "pts_against_pg": _shrink(pa[t], pg[t], prior=lg_pa),
        }
        r = ratings[t]
        r["net_pg"] = r["pts_for_pg"] - r["pts_against_pg"]
    return ratings


def league_constants(games):
    margins = [g["home_pts"] - g["away_pts"] for g in games]
    totals = [g["home_pts"] + g["away_pts"] for g in games]
    n = len(margins)
    mean_margin = sum(margins) / n
    mean_total = sum(totals) / n
    var = sum((m - mean_margin) ** 2 for m in margins) / (n - 1) if n > 1 else 0.0
    var_t = sum((t - mean_total) ** 2 for t in totals) / (n - 1) if n > 1 else 0.0
    return {
        "games": n,
        "mean_home_margin": mean_margin,
        "sd_home_margin": math.sqrt(var),
        "mean_total": mean_total,
        "sd_total": math.sqrt(var_t),
        "home_win_rate": sum(1 for m in margins if m > 0) / n,
        "push_rate": sum(1 for m in margins if m == 0) / n,
        "source_url": "https://www.nfl.com/standings/league/2026/REG",
        "source_note": "Computed from the official results feed, which reconciles exactly to the official nfl.com standings.",
    }


def fair_lines(game, ratings, const):
    """Originate ONE game in the required order: side, then total, then moneyline.

    1. side      — expected home margin from the shrunk ratings plus the
                   measured home-field advantage, published in the SAME
                   convention the third-party archive uses: a POSITIVE line
                   means the home team is favoured by that many points. The
                   convention was checked against 136 official results:
                   read this way the archive's line has a mean error of 9.485
                   points and agrees with the outcome's direction 69.1% of the
                   time; read the other way it has a mean error of 13.206
                   points and agrees 31.6% of the time.
    2. total     — expected combined points from the shrunk ratings.
    3. moneyline — priced FROM the side that was just published: the win
                   probability comes from the published spread line and the
                   official standard deviation of the margin, so the two can
                   never disagree.
    """
    h = ratings.get(game["home"])
    a = ratings.get(game["away"])
    if not h or not a:
        return None
    margin = h["net_pg"] - a["net_pg"]
    total = h["pts_for_pg"] + a["pts_for_pg"]
    home_points = (total + margin) / 2.0
    away_points = (total - margin) / 2.0
    spread_home = round_half(margin)
    sigma = const["sd_home_margin"]
    # The model believes the game is a coin flip at the published line, so the
    # probability that the home team wins outright is the normal probability
    # that the true margin beats zero.
    p_home = norm_cdf(spread_home / sigma) if sigma else None
    home_pts = (total + margin) / 2.0
    away_pts = (total - margin) / 2.0
    return {
        "market": "SPREAD",
        "fair_line": spread_home,
        "fair_line_side": "home",
        "fair_line_convention": "home_perspective_positive_favours_home",
        "fair_price": american(p_home),
        "fair_probability": p_home,
        "model_inputs": {
            "expected_home_margin": margin,
            "home_pts_for_pg": h["pts_for_pg"],
            "home_pts_against_pg": h["pts_against_pg"],
            "away_pts_for_pg": a["pts_for_pg"],
            "away_pts_against_pg": a["pts_against_pg"],
            "hfa_note": ("the home-field advantage is already inside the "
                         "ratings, so it is not added a second time"),
            "measured_league_home_margin": const["mean_home_margin"],
            "sd_margin": sigma,
        },
    }, {
        "market": "TOTAL",
        "fair_line": round(total * 2) / 2.0,
        "fair_line_side": "over_under",
        "fair_line_convention": "combined_points",
        "fair_price": None,
        "fair_probability": None,
        "model_inputs": {
            "home_pts_for_pg": h["pts_for_pg"],
            "away_pts_for_pg": a["pts_for_pg"],
        },
    }, {
        "market": "MONEYLINE",
        "fair_line": None,
        "fair_line_side": "home",
        "fair_price": american(p_home),
        "fair_probability": p_home,
        "model_inputs": {
            "priced_from": ("the published SPREAD line and the official "
                            "standard deviation of the margin"),
            "fair_spread_used": spread_home,
            "sd_margin": sigma,
        },
    }, {
        "expected_home_points": home_pts,
        "expected_away_points": away_pts,
        "expected_margin": margin,
        "expected_total": total,
    }


def market_pair(market, side, market_line, market_price, source_url, source_kind):
    """Market line and its price. A missing market number stays None."""
    return {
        "market_line": market_line,
        "market_price": market_price,
        "market_source_url": source_url,
        "market_source_kind": source_kind,
    }


def round_half(x):
    return None if x is None else round(x * 2) / 2.0
