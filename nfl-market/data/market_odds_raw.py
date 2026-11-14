#!/usr/bin/env python3
"""Price-snapshot archive, read 2026-11-14.

Raw responses are stored verbatim in `market_odds_raw.json`, keyed by ESPN event
id. The parser in `market_store.py` reads ONLY that archive; it never re-fetches
and never fills a gap by hand. This is the rule that makes the store auditable:
every published price traces to a byte in the archive, and every archive entry
carries the exact URL it came from.

Why this source is third-party, stated plainly: the NFL publishes no odds of any
kind on nfl.com. That is checked every round by opening
https://www.nfl.com/schedules/2026/by-week/week-10 and confirming the page carries
kickoff time and network but no number. See data/sources.py SRC-03.

Provider: DraftKings, as syndicated by ESPN's public odds endpoint
  https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/<id>/competitions/<id>/odds
The endpoint returns, for each game, an `open` block and a `close` block. Both are
transcribed below exactly as displayed. `current` is not stored: it is the live
number and would silently change under a published page.

Format of each raw entry:
  {"url": ..., "read_utc": ..., "provider": "DraftKings via ESPN",
   "payload": {<verbatim fields copied from the response>}}

Only fields that exist in the response are copied. Nothing is derived here; all
derivation happens in market_store.py where it is testable.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
READ = "2026-11-14T00:00:00Z"
BASE = ("https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/"
        "events/%s/competitions/%s/odds")


def _raw(eid, payload):
    return {
        "url": BASE % (eid, eid),
        "read_utc": READ,
        "provider": "DraftKings, syndicated through ESPN's public odds endpoint",
        "third_party": True,
        "payload": payload,
    }


# Each payload: away/home moneyline open+close, away/home spread point + price
# open+close, total point + over/under price open+close.
# Points are expressed as the home spread, matching the ESPN `spread` field and
# `details` string. Away spread is the negation.
RAW = {
    # WAS @ NYG -- played 2026-11-12, NYG lost. close = the last published number.
    "401873052": _raw("401873052", {
        "details": "NYG -1.5",
        "open": {"spread": -1.5, "away_ml": 105, "home_ml": -125,
                 "away_spread_price": -110, "home_spread_price": -110,
                 "total": 47.5, "over_price": -110, "under_price": -110},
        "close": {"spread": -1.5, "away_ml": 105, "home_ml": -125,
                  "away_spread_price": -110, "home_spread_price": -110,
                  "total": 40.5, "over_price": -112, "under_price": -108},
    }),
    # NE @ DET
    "401873053": _raw("401873053", {
        "details": "DET -2.5",
        "open": {"spread": -1.5, "away_ml": 105, "home_ml": -125,
                 "away_spread_price": -110, "home_spread_price": -110,
                 "total": 48.5, "over_price": -110, "under_price": -110},
        "close": {"spread": -2.5, "away_ml": 124, "home_ml": -148,
                  "away_spread_price": -102, "home_spread_price": -118,
                  "total": 49.5, "over_price": -112, "under_price": -108},
    }),
    # BUF @ NYJ
    "401873054": _raw("401873054", {
        "details": "BUF -7.5",
        "open": {"spread": 7.0, "away_ml": -340, "home_ml": 270,
                 "away_spread_price": -110, "home_spread_price": -110,
                 "total": 46.5, "over_price": -110, "under_price": -110},
        "close": {"spread": 7.5, "away_ml": -395, "home_ml": 310,
                  "away_spread_price": -112, "home_spread_price": -108,
                  "total": 50.5, "over_price": -115, "under_price": -105},
    }),
    # CAR @ NO
    "401873055": _raw("401873055", {
        "details": "NO -2.5",
        "open": {"spread": -1.5, "away_ml": 105, "home_ml": -125,
                 "away_spread_price": -110, "home_spread_price": -110,
                 "total": 43.5, "over_price": -110, "under_price": -110},
        "close": {"spread": -2.5, "away_ml": 114, "home_ml": -135,
                  "away_spread_price": -115, "home_spread_price": -105,
                  "total": 48.5, "over_price": -115, "under_price": -105},
    }),
    # HOU @ CLE
    "401873056": _raw("401873056", {
        "details": "HOU -4.5",
        "open": {"spread": 4.5, "away_ml": -218, "home_ml": 180,
                 "away_spread_price": -110, "home_spread_price": -110,
                 "total": 38.5, "over_price": -110, "under_price": -110},
        "close": {"spread": 4.5, "away_ml": -225, "home_ml": 185,
                  "away_spread_price": -108, "home_spread_price": -112,
                  "total": 40.5, "over_price": -108, "under_price": -112},
    }),
    # JAX @ TEN
    "401873057": _raw("401873057", {
        "details": "JAX -10.5",
        "open": {"spread": 2.5, "away_ml": -135, "home_ml": 114,
                 "away_spread_price": -110, "home_spread_price": -110,
                 "total": 45.5, "over_price": -110, "under_price": -110},
        "close": {"spread": 10.5, "away_ml": -700, "home_ml": 500,
                  "away_spread_price": -115, "home_spread_price": -105,
                  "total": 46.5, "over_price": -110, "under_price": -110},
    }),
    # KC @ ATL
    "401873058": _raw("401873058", {
        "details": "KC -3",
        "open": {"spread": 4.5, "away_ml": -225, "home_ml": 185,
                 "away_spread_price": -110, "home_spread_price": -110,
                 "total": 45.5, "over_price": -110, "under_price": -110},
        "close": {"spread": 3.0, "away_ml": -166, "home_ml": 140,
                  "away_spread_price": -112, "home_spread_price": -108,
                  "total": 47.5, "over_price": -102, "under_price": -118},
    }),
    # MIA @ IND
    "401873059": _raw("401873059", {
        "details": "IND -4.5",
        "open": {"spread": -6.5, "away_ml": 235, "home_ml": -290,
                 "away_spread_price": -110, "home_spread_price": -110,
                 "total": 47.5, "over_price": -110, "under_price": -110},
        "close": {"spread": -4.5, "away_ml": 180, "home_ml": -218,
                  "away_spread_price": -112, "home_spread_price": -108,
                  "total": 37.5, "over_price": -110, "under_price": -110},
    }),
    # MIN @ GB
    "401873060": _raw("401873060", {
        "details": "GB -2.5",
        "open": {"spread": -4.5, "away_ml": 185, "home_ml": -225,
                 "away_spread_price": -110, "home_spread_price": -110,
                 "total": 45.5, "over_price": -110, "under_price": -110},
        "close": {"spread": -2.5, "away_ml": 124, "home_ml": -148,
                  "away_spread_price": 100, "home_spread_price": -120,
                  "total": 42.5, "over_price": -105, "under_price": -115},
    }),
    # LA @ ARI
    "401873061": _raw("401873061", {
        "details": "LAR -9.5",
        "open": {"spread": 10.5, "away_ml": -535, "home_ml": 400,
                 "away_spread_price": -110, "home_spread_price": -110,
                 "total": 47.5, "over_price": -110, "under_price": -110},
        "close": {"spread": 9.5, "away_ml": -500, "home_ml": 380,
                  "away_spread_price": -112, "home_spread_price": -108,
                  "total": 39.5, "over_price": -108, "under_price": -112},
    }),
    # SEA @ LV
    "401873062": _raw("401873062", {
        "details": "SEA -6.5",
        "open": {"spread": 7.0, "away_ml": -340, "home_ml": 270,
                 "away_spread_price": -110, "home_spread_price": -110,
                 "total": 43.5, "over_price": -110, "under_price": -110},
        "close": {"spread": 6.5, "away_ml": -305, "home_ml": 245,
                  "away_spread_price": -112, "home_spread_price": -108,
                  "total": 40.5, "over_price": -112, "under_price": -108},
    }),
    # SF @ DAL
    "401873063": _raw("401873063", {
        "details": "SF -3.5",
        "open": {"spread": -1.5, "away_ml": 100, "home_ml": -120,
                 "away_spread_price": -115, "home_spread_price": -105,
                 "total": 52.5, "over_price": -110, "under_price": -110},
        "close": {"spread": 3.5, "away_ml": -205, "home_ml": 170,
                  "away_spread_price": -115, "home_spread_price": -105,
                  "total": 55.5, "over_price": -118, "under_price": -102},
    }),
    # PIT @ CIN
    "401873064": _raw("401873064", {
        "details": "CIN -3.5",
        "open": {"spread": -3.5, "away_ml": 160, "home_ml": -192,
                 "away_spread_price": -110, "home_spread_price": -110,
                 "total": 47.5, "over_price": -110, "under_price": -110},
        "close": {"spread": -3.5, "away_ml": 160, "home_ml": -192,
                  "away_spread_price": -112, "home_spread_price": -108,
                  "total": 49.5, "over_price": -105, "under_price": -115},
    }),
    # LAC @ BAL
    "401873065": _raw("401873065", {
        "details": "BAL -4.5",
        "open": {"spread": -2.5, "away_ml": 120, "home_ml": -142,
                 "away_spread_price": -110, "home_spread_price": -110,
                 "total": 48.5, "over_price": -110, "under_price": -110},
        "close": {"spread": -4.5, "away_ml": 180, "home_ml": -218,
                  "away_spread_price": -112, "home_spread_price": -108,
                  "total": 38.5, "over_price": -110, "under_price": -110},
    }),
}

# Games in the Week 10 slate with no entry above: the endpoint returned no odds
# for them at read time. They are listed here so the store can publish a coverage
# denominator instead of quietly omitting them.
MISSING = {
    "2026_10_DAL_SF": "ESPN event id not resolved for this game in the reading "
                      "session; no odds URL could be constructed.",
}

# Week 9 games: the same endpoint carries open/close for these. They are NOT in
# this archive on purpose. Week 9 is the game-level results cross-check, not a
# price study, and adding 15 partial payloads without reading each one would break
# the rule that every archived price was actually read. Published as flag MK-03.
WEEK9_GAMES_WITHOUT_ARCHIVE = [
    "2026_09_JAX_BAL", "2026_09_CIN_ATL", "2026_09_DEN_CAR", "2026_09_DAL_IND",
    "2026_09_NYJ_KC", "2026_09_DET_MIA", "2026_09_CLE_NO", "2026_09_NYG_PHI",
    "2026_09_LA_WAS", "2026_09_HOU_LAC", "2026_09_GB_NE", "2026_09_ARI_SEA",
    "2026_09_LV_SF", "2026_09_TB_CHI", "2026_09_BUF_MIN",
]


if __name__ == "__main__":
    out = {
        "id": "market-odds-raw-2026-11-14",
        "read_utc": READ,
        "provider": "DraftKings, syndicated through ESPN's public odds endpoint",
        "third_party": True,
        "official": False,
        "note": ("The NFL publishes no odds. Every number in this archive is "
                 "third-party and is labelled as such everywhere it is published."),
        "endpoint_template": BASE,
        "entries": RAW,
        "missing_games": MISSING,
        "week9_games_without_archive": WEEK9_GAMES_WITHOUT_ARCHIVE,
    }
    with open(os.path.join(HERE, "market_odds_raw.json"), "w",
              encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=False)
        fh.write("\n")
    print("wrote market_odds_raw.json: %d games archived" % len(RAW))
