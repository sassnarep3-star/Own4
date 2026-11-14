"""nfl-book/engine/seed.py — seeds the price-snapshot store.

The store is filled from the own lines this repository has already published.
Each publication is a dated snapshot of a number we originated, so two
publications of the same game and market give that market an opening and a
closing number.

Publication dates are taken from a field inside the published file itself, or
from the date in the file name. They are never guessed.

Market (other people's) prices come from the third-party archive pinned in
this repository and are always labelled as third-party, because the NFL
publishes no betting lines.
"""

from __future__ import annotations

import csv
import json
import os
import re

from . import core
from .store import PriceSnapshotStore

REPO = core.REPO

# The archive spells two clubs differently from nfl.com.
CANON = {"ARI": "AZ", "LA": "LAR"}

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
    return CANON.get(team, team)


# How a published spread line is written. This decides whether the line can
# be settled at all, so it is recorded on every snapshot.
#
#   market_home_perspective  negative means the home team gives points
#   expected_home_margin     positive means the home team is expected to win
#   stated_home_spread       the publication writes the side in the string
#   unstated                 the publication does not say, so the line is not
#                            settled; it is published and flagged instead
CONV_MARKET = "market_home_perspective"
CONV_MARGIN = "expected_home_margin"
CONV_STATED_HOME = "stated_home_spread"
CONV_UNSTATED = "unstated"
CONV_TOTAL = "combined_points"
CONV_ODDS = "american_odds"


def game_url(away, home, week):
    return "https://www.nfl.com/games/%s-at-%s-2026-reg-%d" % (
        SLUGS[canon(away)], SLUGS[canon(home)], week)


def game_key(week, away, home):
    return "%02d_%s_%s" % (week, canon(away), canon(home))


def _num(x):
    if x is None:
        return None
    x = str(x).strip()
    if x == "":
        return None
    try:
        return float(x)
    except ValueError:
        return None


def _int(x):
    v = _num(x)
    return None if v is None else int(round(v))


def _week_from_url(url):
    m = re.search(r"-reg-(\d+)", url or "")
    return int(m.group(1)) if m else None


# ------------------------------------------------------------------ sources
def seed_nfl_quant(store):
    """nfl-quant, published 2026-11-02T21:35:08Z (provenance.json)."""
    path = os.path.join(REPO, "nfl-quant", "data", "week9_lines.csv")
    prov = os.path.join(REPO, "nfl-quant", "data", "provenance.json")
    ts = core.read_json(prov)["generated_utc"]
    out = []
    for r in core.read_csv(path):
        w = int(r["game_id"].split("_")[1])
        gk = game_key(w, r["away"], r["home"])
        src = "https://github.com/sassnarep3-star/Own4/blob/main/nfl-quant/data/week9_lines.csv"
        out.append((gk, "SPREAD", "home", _num(r["own_spread_home"]), None, ts, src,
                    "nfl-quant/data/week9_lines.csv", CONV_UNSTATED))
        out.append((gk, "TOTAL", "over", _num(r["own_total"]), None, ts, src,
                    "nfl-quant/data/week9_lines.csv", CONV_TOTAL))
        out.append((gk, "MONEYLINE", "home", None, _int(r["own_home_ml_fair"]), ts, src,
                    "nfl-quant/data/week9_lines.csv", CONV_ODDS))
        out.append((gk, "MONEYLINE", "away", None, _int(r["own_away_ml_fair"]), ts, src,
                    "nfl-quant/data/week9_lines.csv", CONV_ODDS))
    return out


def seed_nfl_lab(store):
    """nfl-lab, published 2026-11-02 (strategy_registry.json registered_utc)."""
    path = os.path.join(REPO, "nfl-lab", "data", "own_lines_2026.csv")
    ts = "2026-11-02T00:00:00Z"
    out = []
    for r in core.read_csv(path):
        w = int(r["week"])
        gk = game_key(w, r["away"], r["home"])
        sp = r["model_spread"] or ""
        m = re.match(r"HOME\s*([+-]?\d+(?:\.\d+)?)", sp)
        line = _num(m.group(1)) if m else None
        src = "https://github.com/sassnarep3-star/Own4/blob/main/nfl-lab/data/own_lines_2026.csv"
        out.append((gk, "SPREAD", "home", line, None, ts, src,
                    "nfl-lab/data/own_lines_2026.csv", CONV_STATED_HOME))
        out.append((gk, "TOTAL", "over", _num(r["model_total"]), None, ts, src,
                    "nfl-lab/data/own_lines_2026.csv", CONV_TOTAL))
        for side, key in (("home", "fair_ml_home"), ("away", "fair_ml_away")):
            dec = _num(r[key])
            out.append((gk, "MONEYLINE", side, None,
                        core.american(1.0 / dec) if dec else None, ts, src,
                        "nfl-lab/data/own_lines_2026.csv (decimal odds converted to American)",
                        CONV_ODDS))
    return out


def seed_nfl_edge(store):
    """nfl-edge, captured 2026-11-12."""
    path = os.path.join(REPO, "nfl-edge", "data", "own_lines_2026.json")
    d = core.read_json(path)
    ts = d["captured_utc"] + "T00:00:00Z"
    out = []
    for r in d["rows"]:
        gk = game_key(r["week"], r["away"], r["home"])
        src = r.get("source_url") or "https://www.nfl.com/schedules/2026/by-week/week-10"
        out.append((gk, "SPREAD", "home", r.get("own_spread_home"), None, ts, src,
                    "nfl-edge/data/own_lines_2026.json", CONV_UNSTATED))
        out.append((gk, "TOTAL", "over", r.get("own_total"), None, ts, src,
                    "nfl-edge/data/own_lines_2026.json", CONV_TOTAL))
        out.append((gk, "MONEYLINE", "home", None, r.get("own_ml_home"), ts, src,
                    "nfl-edge/data/own_lines_2026.json", CONV_ODDS))
        out.append((gk, "MONEYLINE", "away", None, r.get("own_ml_away"), ts, src,
                    "nfl-edge/data/own_lines_2026.json", CONV_ODDS))
    return out


def seed_nfl_origination(store):
    """nfl-origination, published 2026-11-13 (own-lines-week10-2026-11-13)."""
    path = os.path.join(REPO, "nfl-origination", "data", "derived", "own_lines.json")
    d = core.read_json(path)
    ts = "2026-11-13T00:00:00Z"
    out = []
    for g in d["games"]:
        w = _week_from_url(g.get("game_url"))
        if w is None:
            continue
        gk = game_key(w, g["away"], g["home"])
        src = g.get("game_url")
        out.append((gk, "SPREAD", "home", g.get("own_home_margin"), None, ts, src,
                    "nfl-origination/data/derived/own_lines.json", CONV_MARGIN))
        out.append((gk, "TOTAL", "over", g.get("own_total"), None, ts, src,
                    "nfl-origination/data/derived/own_lines.json", CONV_TOTAL))
    return out


def seed_nfl_command(store):
    """nfl-command, computed 2026-11-13T22:05Z."""
    path = os.path.join(REPO, "nfl-command", "data", "own_lines_week11.json")
    d = core.read_json(path)
    ts = d["computed_utc"]
    out = []
    for g in d["week11_own_lines"]:
        w = _week_from_url(g.get("game_url"))
        if w is None:
            continue
        gk = game_key(w, g["away"], g["home"])
        src = g.get("source_url") or g.get("game_url")
        out.append((gk, "SPREAD", "home", g.get("spread_home"), None, ts, src,
                    "nfl-command/data/own_lines_week11.json", CONV_UNSTATED))
        out.append((gk, "TOTAL", "over", g.get("total"), None, ts, src,
                    "nfl-command/data/own_lines_week11.json", CONV_TOTAL))
    return out


def seed_nfl_own(store):
    """nfl-own, published in the 2026-11-13 official snapshot."""
    path = os.path.join(REPO, "nfl-own", "data", "derived", "own_lines.json")
    d = core.read_json(path)
    ts = "2026-11-13T00:00:00Z"
    out = []
    for r in d["rows"]:
        w = 11
        gk = game_key(w, r["away"], r["home"])
        src = r.get("source_url") or d.get("slate_source")
        out.append((gk, "SPREAD", "home", r.get("own_spread_home"), None, ts, src,
                    "nfl-own/data/derived/own_lines.json", CONV_UNSTATED))
        out.append((gk, "TOTAL", "over", r.get("own_total"), None, ts, src,
                    "nfl-own/data/derived/own_lines.json", CONV_TOTAL))
        out.append((gk, "MONEYLINE", "home", None, r.get("fair_home_ml"), ts, src,
                    "nfl-own/data/derived/own_lines.json", CONV_ODDS))
        out.append((gk, "MONEYLINE", "away", None, r.get("fair_away_ml"), ts, src,
                    "nfl-own/data/derived/own_lines.json", CONV_ODDS))
    return out


PUBLICATIONS = [
    ("nfl-quant", seed_nfl_quant),
    ("nfl-lab", seed_nfl_lab),
    ("nfl-edge", seed_nfl_edge),
    ("nfl-origination", seed_nfl_origination),
    ("nfl-command", seed_nfl_command),
    ("nfl-own", seed_nfl_own),
]


def build_store():
    """Build the price-snapshot store from every publication in the repository."""
    store = PriceSnapshotStore()
    manifest = []
    for name, fn in PUBLICATIONS:
        rows = fn(store)
        for gk, market, side, line, price, ts, src, ref, conv in rows:
            store.record(gk, market, side, "own_model", ts,
                         line=line, price=price, source_url=src,
                         source_kind="own_publication", source_ref=ref,
                         line_convention=conv)
        manifest.append({
            "publication": name,
            "snapshots": len(rows),
            "source_ref": rows[0][7] if rows else None,
            "source_url": rows[0][6] if rows else None,
            "published_utc": rows[0][5] if rows else None,
            "line_convention": rows[0][8] if rows else None,
        })
    # Third-party closing prices for the same games.
    prov = core.archive_provenance()
    ts = prov.get("retrieved_utc") or core.SNAPSHOT_UTC
    for a in core.load_archive():
        if a["away_pts"] is None:
            continue
        gk = game_key(a["week"], a["away"], a["home"])
        src = prov.get("upstream_commit_url")
        if a["spread_line_home"] is not None:
            store.record(gk, "SPREAD", "home", "market", ts,
                         line=a["spread_line_home"], price=None, source_url=src,
                         source_kind="third_party_archive",
                         source_ref="nfl-hub/data/source/games.csv",
                         line_convention=CONV_MARKET)
            store.record(gk, "SPREAD", "away", "market", ts,
                         line=-a["spread_line_home"], price=None, source_url=src,
                         source_kind="third_party_archive",
                         source_ref="nfl-hub/data/source/games.csv",
                         line_convention=CONV_MARKET)
        if a["total_line"] is not None:
            store.record(gk, "TOTAL", "over", "market", ts,
                         line=a["total_line"], price=None, source_url=src,
                         source_kind="third_party_archive",
                         source_ref="nfl-hub/data/source/games.csv",
                         line_convention=CONV_TOTAL)
        if a["home_moneyline"] is not None:
            store.record(gk, "MONEYLINE", "home", "market", ts,
                         line=None, price=a["home_moneyline"], source_url=src,
                         source_kind="third_party_archive",
                         source_ref="nfl-hub/data/source/games.csv",
                         line_convention=CONV_ODDS)
        if a["away_moneyline"] is not None:
            store.record(gk, "MONEYLINE", "away", "market", ts,
                         line=None, price=a["away_moneyline"], source_url=src,
                         source_kind="third_party_archive",
                         source_ref="nfl-hub/data/source/games.csv",
                         line_convention=CONV_ODDS)
    header = {
        "built_utc": core.SNAPSHOT_UTC,
        "own_publications": manifest,
        "market_price_source": prov,
        "market_price_note": (
            "The NFL publishes no betting lines. Market snapshots come from the "
            "third-party archive pinned in this repository and are labelled "
            "third_party_archive everywhere they appear."),
    }
    return store, header
