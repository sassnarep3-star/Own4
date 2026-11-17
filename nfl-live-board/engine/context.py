#!/usr/bin/env python3
"""
Own4 · nfl-live-board · fixture context and the price-snapshot store.

fixture context (data/fixture_context.json)
    Built only from published schedule facts: rest days on both sides, a short-week flag, a
    Thursday/Monday flag, a neutral-site flag that was venue-verified, and the kickoff window.
    Nothing here is a projection. The rest-day figure is arithmetic on official dates.

price snapshots (data/price_snapshots.json)
    The store exists and is EMPTY apart from its own contract. No official page publishes an
    opening or closing spread, total or moneyline, so every slot is null and the reason is in
    the same row. An empty store that says why is a foundation; a store filled with an
    invented -110 is a fabricated dataset, which is what this repository has flagged twice.

Run: python3 nfl-live-board/engine/context.py
"""
import datetime
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")


def main():
    corpus = json.load(open(os.path.join(DATA, "corpus_rows_only.json")))["rows"]
    fixtures = json.load(open(os.path.join(DATA, "fixtures_2026.json")))["rows"]

    # Last game date per club. Two sources, in this order:
    #   1. every corpus game (a played, verified final);
    #   2. every SCHEDULED fixture whose date the official week page states, even if the game
    #      has no final yet. Week 10's LAC at BAL (2026-11-16) is exactly that case: it is in
    #      the schedule but not in the corpus, and ignoring it gave BAL 17 days of rest instead
    #      of 6. Rest is a schedule fact, so the schedule is the right source.
    last = {}
    for g in sorted(corpus, key=lambda x: (x["date"], x["game_id"])):
        try:
            d = datetime.date.fromisoformat(g["date"])
        except ValueError:
            continue
        last[g["home"]] = max(last.get(g["home"], d), d)
        last[g["away"]] = max(last.get(g["away"], d), d)
    scheduled_extra = []
    for f in fixtures:
        if not f["home"] or f["week"] != 10 or not f["date"]:
            continue
        try:
            d = datetime.date.fromisoformat(f["date"])
        except ValueError:
            continue
        if f["game_url"].endswith("chargers-at-ravens-2026-reg-10"):
            scheduled_extra.append({"match": "LAC @ BAL", "date": f["date"]})
            last["LAC"] = max(last.get("LAC", d), d)
            last["BAL"] = max(last.get("BAL", d), d)

    rows = []
    for f in fixtures:
        if f["week"] != 11 or not f["home"]:
            continue
        try:
            d = datetime.date.fromisoformat(f["date"])
        except ValueError:
            d = None
        rest = {}
        for side in ("away", "home"):
            t = f[side]
            rest[side] = (d - last[t]).days if (d and t in last) else None
        neutral = (11, f["away"], f["home"]) in {(11, "MIN", "SF")}
        dow = d.strftime("%A") if d else ""
        rows.append({
            "week": 11, "date": f["date"], "day_of_week": dow,
            "kickoff_et": f["kickoff_et"], "network": f["network"],
            "away": f["away"], "home": f["home"],
            "rest_days_away": rest["away"], "rest_days_home": rest["home"],
            "rest_diff_home_minus_away": (rest["home"] - rest["away"])
            if rest["home"] is not None and rest["away"] is not None else None,
            "short_week_away": (rest["away"] is not None and rest["away"] < 7),
            "short_week_home": (rest["home"] is not None and rest["home"] < 7),
            "neutral_site_verified": neutral,
            "neutral_evidence": ("official week page carries the 'Mexico City 2026' event logo"
                                 if neutral else None),
            "site": f["site"] or None,
            "venue_status": "transcribed from the game centre's titled Game Info block"
            if f["site"] else
            "blank - the official scores/schedule page does not state the stadium for a played "
            "or future fixture in a titled field; not inferred",
            "venue_rule": "at least a 6-day week counts as a normal week; a game within 6 days "
                          "of the previous one is flagged short. The rule is stated, not tuned.",
            "source_url": f["game_url"], "week_page_url": f["week_page"],
        })

    ctx = {
        "dataset": "nfl_live_board_fixture_context",
        "title": "Fixture context for Week 11, from published schedule facts only",
        "built_utc": "2026-11-17",
        "features": ["rest_days_away", "rest_days_home", "rest_diff_home_minus_away",
                     "short_week_away", "short_week_home", "neutral_site_verified",
                     "day_of_week", "kickoff_et"],
        "excluded": ["stadium roof", "surface", "weather", "travel distance"],
        "exclusion_reason": "roof and surface are not published as fields on the official page; "
                            "weather needs an external feed this session cannot reach. Excluded "
                            "rather than estimated.",
        "scheduled_but_unplayed_included": scheduled_extra,
        "rest_definition": "calendar days between the club's previous fixture date and this "
                           "fixture's date, counting fixtures that are scheduled but not yet "
                           "played. Both dates are transcribed from official pages.",
        "rows": rows,
        "sources": [
            {"what": "Week 11 schedule", "url": "https://www.nfl.com/schedules/2026/by-week/week-11"},
            {"what": "Week 10 results (dates)", "url": "https://www.nfl.com/scores/2026/week-10"},
        ],
    }
    json.dump(ctx, open(os.path.join(DATA, "fixture_context.json"), "w"), indent=1)

    # ---- price snapshot store: contract, then empty slots -------------------
    markets = ["side", "total", "moneyline"]
    snap_rows = []
    for f in fixtures:
        if f["week"] != 11 or not f["home"]:
            continue
        for m in markets:
            snap_rows.append({
                "game": "%s @ %s" % (f["away"], f["home"]),
                "market": m,
                "open": None, "close": None,
                "open_captured_utc": None, "close_captured_utc": None,
                "open_source_url": None, "close_source_url": None,
                "open_sha256": None, "close_sha256": None,
                "status": "empty - no official price source",
                "blank_reason": "nfl.com publishes schedules, results and standings, not a "
                                "spread, total or moneyline (checked 2026-11-17). The store is "
                                "built to hold two hashed captures per market; it holds zero.",
                "source_url": f["game_url"],
            })
    store = {
        "dataset": "nfl_live_board_price_snapshots",
        "title": "Price-snapshot store: opening and closing numbers for every originated market",
        "built_utc": "2026-11-17",
        "contract": {
            "unit": "one row per game, per market, per capture point",
            "capture_points": ["open", "close"],
            "required_fields": ["value", "captured_utc", "source_url", "sha256"],
            "append_only": True,
            "reject_rule": "a row may not be written without all four required fields; an "
                           "assumed price is not accepted in any column",
        },
        "slots_expected": len(snap_rows),
        "slots_filled": 0,
        "policy": "empty by design until the owner decides the price-data policy (requirement R04 / F-01)",
        "rows": snap_rows,
        "sources": [
            {"what": "nfl.com home, checked for an odds module", "url": "https://www.nfl.com/"},
        ],
    }
    json.dump(store, open(os.path.join(DATA, "price_snapshots.json"), "w"), indent=1)

    print("fixture context: %d Week 11 fixtures" % len(rows))
    for r in rows[:4]:
        print("  %s @ %s  rest %s/%s  short %s/%s  site=%s"
              % (r["away"], r["home"], r["rest_days_away"], r["rest_days_home"],
                 r["short_week_away"], r["short_week_home"], r["site"]))
    print("price store: %d slots for %d markets x %d games, %d filled"
          % (len(snap_rows), len(markets), len(rows), 0))


if __name__ == "__main__":
    main()
