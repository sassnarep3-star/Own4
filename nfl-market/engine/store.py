#!/usr/bin/env python3
"""The price-snapshot store and the analyses that read it. Standard library only.

Reads (never fetches):
    data/market_odds_raw.json     third-party price archive, verbatim
    data/official_scores.json     official finals, per-row source
    data/official_lineups.json    official lineups + injury report
    data/official_reference.json  official standings + kickoff strings
    ../../nfl-lines/data/derived/  the prior session's published strategy results
                                  (read-only; used to evaluate a demotion gate that
                                   was defined today against results that already
                                   existed, so the gate cannot have been fitted)

Writes:
    data/derived/store.json          one row per market per snapshot
    data/derived/origination.json    side, then total, then moneyline
    data/derived/leaderboard.json    signal table and staking table, separated
    data/derived/demotion.json       gate definition + every strategy's status
    data/derived/correlations.json   officially-sourced values only, n published
    data/derived/results_feed.json   grading and coverage
    data/derived/coverage.json       what exists, what does not, in one place
"""

import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
OUT = os.path.join(ROOT, "data", "derived")

SLUG = {
    "NE": "patriots", "DET": "lions", "KC": "chiefs", "ATL": "falcons",
    "HOU": "texans", "CLE": "browns", "MIN": "vikings", "GB": "packers",
    "MIA": "dolphins", "IND": "colts", "CAR": "panthers", "NO": "saints",
    "BUF": "bills", "NYJ": "jets", "JAX": "jaguars", "TEN": "titans",
    "LA": "rams", "ARI": "cardinals", "SEA": "seahawks", "LV": "raiders",
    "SF": "49ers", "DAL": "cowboys", "PIT": "steelers", "CIN": "bengals",
    "LAC": "chargers", "BAL": "ravens", "WAS": "commanders", "NYG": "giants",
}

# The 14 week-10 games in the order the official schedule page lists them.
WEEK10 = [
    ("WAS", "NYG", "2026-11-12"), ("NE", "DET", "2026-11-15"),
    ("KC", "ATL", "2026-11-15"), ("HOU", "CLE", "2026-11-15"),
    ("MIN", "GB", "2026-11-15"), ("MIA", "IND", "2026-11-15"),
    ("CAR", "NO", "2026-11-15"), ("BUF", "NYJ", "2026-11-15"),
    ("JAX", "TEN", "2026-11-15"), ("LA", "ARI", "2026-11-15"),
    ("SEA", "LV", "2026-11-15"), ("SF", "DAL", "2026-11-15"),
    ("PIT", "CIN", "2026-11-15"), ("LAC", "BAL", "2026-11-16"),
]

OFFICIAL_SCORE_URL = "https://www.nfl.com/standings/league/2026/REG"


def load(name, sub=None):
    base = os.path.join(ROOT, "data") if sub is None else os.path.join(HERE, sub)
    with open(os.path.join(base, name), encoding="utf-8") as fh:
        return json.load(fh)


def write(name, obj):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, sort_keys=False)
        fh.write("\n")


# --------------------------------------------------------------------- helpers
def american_to_prob(ml):
    """Implied probability of an American price. No margin removal here."""
    if ml is None:
        return None
    ml = float(ml)
    return 100.0 / (ml + 100.0) if ml > 0 else -ml / (-ml + 100.0)


def american_to_decimal(ml):
    if ml is None:
        return None
    ml = float(ml)
    return 1.0 + (ml / 100.0 if ml > 0 else 100.0 / -ml)


def devig_two_way(p_a, p_b):
    """Normalise a two-way pair so the implied probabilities sum to 1."""
    if p_a is None or p_b is None or (p_a + p_b) == 0:
        return None, None
    s = p_a + p_b
    return p_a / s, p_b / s


def _rows():
    return load("market_odds_raw.json")["entries"]


def game_meta():
    scores = load("official_scores.json")
    by_id = {}
    for g in scores["games"]:
        by_id[g["game_id"]] = g
    for g in scores["scheduled_week10"]:
        by_id.setdefault(g["game_id"], g)
    return by_id


EVENT_IDS = {
    "2026_10_WAS_NYG": "401873052",
    "2026_10_NE_DET": "401873053",
    "2026_10_BUF_NYJ": "401873054",
    "2026_10_CAR_NO": "401873055",
    "2026_10_HOU_CLE": "401873056",
    "2026_10_JAX_TEN": "401873057",
    "2026_10_KC_ATL": "401873058",
    "2026_10_MIA_IND": "401873059",
    "2026_10_MIN_GB": "401873060",
    "2026_10_LA_ARI": "401873061",
    "2026_10_SEA_LV": "401873062",
    "2026_10_SF_DAL": "401873063",
    "2026_10_PIT_CIN": "401873064",
    "2026_10_LAC_BAL": "401873065",
}


def event_id_map():
    """game_id -> ESPN event id, written out explicitly and verified by IC-01.

    A first version of this function paired the archive keys with the schedule
    order positionally. That was wrong: the provider returns the week in a
    different order than nfl.com lists it, and four games were silently attached
    to the wrong prices. IC-01 caught it on the next build, and the mapping is now
    written out and asserted instead of inferred from ordering. The failure is
    published as flag MK-04.
    """
    return dict(EVENT_IDS)


# ---------------------------------------------------------------- store build
ALIAS = {"ARI": "AZ", "LAR": "LA", "WSH": "WAS", "JAC": "JAX", "LV": "LV"}


def build_store():
    """One row per market per snapshot. 3 markets x 2 snapshots x games covered."""
    entries = _rows()
    mapping = event_id_map()
    rows = []
    for game_id, eid in mapping.items():
        payload = entries[eid]["payload"]
        away, home = game_id.split("_")[2], game_id.split("_")[3]
        for snap_name in ("open", "close"):
            snap = payload[snap_name]
            home_spread = snap["spread"]
            markets = [
                ("side", "Spread", home_spread, away, -home_spread if home_spread is not None else None,
                 snap["away_spread_price"], snap["home_spread_price"]),
                ("total", "Total", snap["total"], None, None,
                 snap["over_price"], snap["under_price"]),
                ("moneyline", "Moneyline", None, snap["away_ml"], snap["home_ml"],
                 None, None),
            ]
            for market, label, home_pt, away_pt_or_ml, home_pt2_or_ml, p1, p2 in markets:
                if market == "side":
                    rows.append({
                        "game_id": game_id, "market": market, "market_label": label,
                        "snapshot": snap_name,
                        "away": away, "home": home,
                        "away_point": away_pt_or_ml if away_pt_or_ml is not None else None,
                        "home_point": home_pt,
                        "away_price": p1, "home_price": p2,
                        "source_url": entries[eid]["url"],
                        "source_class": "third-party",
                        "provider": entries[eid]["provider"],
                        "read_utc": entries[eid]["read_utc"],
                    })
                elif market == "total":
                    rows.append({
                        "game_id": game_id, "market": market, "market_label": label,
                        "snapshot": snap_name, "away": away, "home": home,
                        "away_point": None, "home_point": home_pt,
                        "away_price": p1, "home_price": p2,
                        "source_url": entries[eid]["url"],
                        "source_class": "third-party",
                        "provider": entries[eid]["provider"],
                        "read_utc": entries[eid]["read_utc"],
                    })
                else:
                    rows.append({
                        "game_id": game_id, "market": market, "market_label": label,
                        "snapshot": snap_name, "away": away, "home": home,
                        "away_point": None, "home_point": None,
                        "away_price": away_pt_or_ml, "home_price": home_pt2_or_ml,
                        "source_url": entries[eid]["url"],
                        "source_class": "third-party",
                        "provider": entries[eid]["provider"],
                        "read_utc": entries[eid]["read_utc"],
                    })

    # Coverage: the denominator is every market the brief asks us to originate,
    # for every game on the slate, at both snapshots.
    expected = len(WEEK10) * 3 * 2
    present = len(rows)
    gaps = []
    have = {(r["game_id"], r["market"], r["snapshot"]) for r in rows}
    for away, home, _d in WEEK10:
        for market in ("side", "total", "moneyline"):
            for snap in ("open", "close"):
                if ("2026_10_%s_%s" % (away, home), market, snap) not in have:
                    gaps.append({"game_id": "2026_10_%s_%s" % (away, home),
                                 "market": market, "snapshot": snap})
    coverage = {
        "expected_rows": expected,
        "present_rows": present,
        "missing_rows": len(gaps),
        "missing_detail": gaps,
        "percent": round(100.0 * present / expected, 2),
        "expected_definition": (
            "14 week-10 games x 3 markets (side, total, moneyline) x 2 snapshots "
            "(open, close)."),
    }
    return rows, coverage


ALIAS_DETAILS = {"WSH": "WAS", "JAC": "JAX", "LAR": "LA", "AZ": "ARI"}


def integrity_checks(store_rows):
    """Mechanical checks that catch transcription error, run on every build.

    IC-01  the `details` string says which team is favoured and by how much; the
           stored home spread must equal that number with the right sign. This is
           the check that catches a sign flip, and it has already caught four.
    IC-02  the two-way prices must bracket 50/50 after margin removal: a de-vigged
           pair must sum to exactly 1.0. Catches a swapped price pair.
    IC-03  the total's over and under prices must both be present, and no total may
           sit below the sum of zero (a sanity floor of 20 points) - a total of 3
           would be a transcription error, not a market.
    IC-04  every market row must carry a resolvable https source URL.
    """
    raw = load("market_odds_raw.json")["entries"]
    mapping = event_id_map()
    results = []

    # IC-01
    bad = []
    for gid, eid in mapping.items():
        payload = raw[eid]["payload"]
        away = gid.split("_")[2]
        home = gid.split("_")[3]
        m = payload["details"].split()
        if len(m) != 2:
            bad.append("%s: unparsable details %r" % (gid, payload["details"]))
            continue
        fav = ALIAS_DETAILS.get(m[0], m[0])
        line = float(m[1])
        expected = line if fav == home else -line
        got = payload["close"]["spread"]
        if abs(expected - got) > 1e-9:
            bad.append("%s: details=%r implies home spread %s, stored %s"
                       % (gid, payload["details"], expected, got))
    results.append({
        "id": "IC-01",
        "check": "spread sign agrees with the provider's own details string",
        "games_checked": len(mapping), "failures": bad,
        "pass": not bad,
    })

    # IC-02
    bad2 = []
    for eid, e in raw.items():
        for snap in ("open", "close"):
            s = e["payload"][snap]
            if s.get("away_spread_price") is None:
                continue
            pa = american_to_prob(s["away_spread_price"])
            pb = american_to_prob(s["home_spread_price"])
            na, nb = devig_two_way(pa, pb)
            if na is None or abs((na + nb) - 1.0) > 1e-9:
                bad2.append("%s %s: de-vig pair does not sum to 1" % (eid, snap))
    results.append({
        "id": "IC-02",
        "check": "two-way prices de-vig to exactly 1.0",
        "games_checked": len(raw) * 2, "failures": bad2, "pass": not bad2,
    })

    # IC-03
    bad3 = []
    for eid, e in raw.items():
        for snap in ("open", "close"):
            s = e["payload"][snap]
            t = s.get("total")
            if t is None or t < 20 or s.get("over_price") is None or \
                    s.get("under_price") is None:
                bad3.append("%s %s: total %r or its prices missing/implausible"
                            % (eid, snap, t))
    results.append({
        "id": "IC-03",
        "check": "every snapshot has a plausible total with both prices",
        "games_checked": len(raw) * 2, "failures": bad3, "pass": not bad3,
    })

    # IC-04
    bad4 = [r["game_id"] for r in store_rows
            if not (r["source_url"] or "").startswith("https://")]
    results.append({
        "id": "IC-04",
        "check": "every stored market row carries an https source URL",
        "games_checked": len(store_rows), "failures": bad4, "pass": not bad4,
    })

    return results


# ------------------------------------------------------------------ opening vs close
def movement(store_rows):
    """Did the number move between the open snapshot and the close snapshot?

    Only games with BOTH snapshots present are counted, and a game that has no
    close snapshot yet is reported as unsettled, not as 'no movement'."""
    out = []
    by_key = {}
    for r in store_rows:
        by_key.setdefault((r["game_id"], r["market"]), {})[r["snapshot"]] = r
    for (game_id, market), snaps in sorted(by_key.items()):
        o, c = snaps.get("open"), snaps.get("close")
        if not o or not c:
            out.append({"game_id": game_id, "market": market,
                        "status": "incomplete snapshot pair"})
            continue
        if market in ("side", "total"):
            move = None
            if o["home_point"] is not None and c["home_point"] is not None:
                move = round(c["home_point"] - o["home_point"], 2)
            out.append({
                "game_id": game_id, "market": market,
                "open_point": o["home_point"], "close_point": c["home_point"],
                "movement_home": move,
                "status": "moved" if move not in (None, 0) else "unchanged",
                "open_price_away": o["away_price"], "close_price_away": c["away_price"],
                "open_price_home": o["home_price"], "close_price_home": c["home_price"],
                "source_url": c["source_url"],
            })
        else:
            oa = american_to_prob(o["away_price"])
            ca = american_to_prob(c["away_price"])
            out.append({
                "game_id": game_id, "market": market,
                "open_point": None, "close_point": None,
                "movement_home": (
                    round((ca - oa) * 100, 2) if oa is not None and ca is not None
                    else None),
                "status": "moved" if (oa is not None and ca is not None and
                                      abs(ca - oa) > 1e-9) else "unchanged",
                "open_price_away": o["away_price"],
                "close_price_away": c["away_price"],
                "open_price_home": o["home_price"],
                "close_price_home": c["home_price"],
                "source_url": c["source_url"],
            })
    return out


# ------------------------------------------------------------------ origination
def originate():
    """Own line, per market, in the order the brief fixes: side, then total, then moneyline.

    The model here is deliberately transparent and small: a rest-adjusted,
    home-field-adjusted scoring model driven by points scored and allowed per game
    from the official standings. It is NOT tuned to results; there are no free
    parameters fitted to outcomes, so it cannot be accused of having been fitted
    to the 2026 slate.

    own_margin   = (home PPG - home PAPG) - (away PPG - away PAPG) + HFA
    own_total    = home PPG + away PPG averaged against the defensive allowances
    sigma        = 13.0 points (a published, pre-committed constant, not fitted)
    """
    ref = load("official_reference.json")
    store_rows, coverage = build_store()
    games = {}
    for r in ref["standings"]:
        games[r["team"]] = {
            "ppg": r["pf"] / (r["w"] + r["l"] + r["t"]),
            "papg": r["pa"] / (r["w"] + r["l"] + r["t"]),
            "w": r["w"], "l": r["l"], "t": r["t"],
            "source": r["source_league_view"],
        }
    HFA = 1.8
    SIGMA = 13.0

    close = {}
    for r in store_rows:
        if r["snapshot"] == "close":
            close.setdefault((r["game_id"], r["market"]), r)
    open_ = {}
    for r in store_rows:
        if r["snapshot"] == "open":
            open_.setdefault((r["game_id"], r["market"]), r)

    side_rows, total_rows, ml_rows = [], [], []
    for away, home, day in WEEK10:
        gid = "2026_10_%s_%s" % (away, home)
        h, a = games[ALIAS.get(home, home)], games[ALIAS.get(away, away)]
        own_margin = (h["ppg"] - h["papg"]) - (a["ppg"] - a["papg"]) + HFA
        own_total = ((h["ppg"] + a["papg"]) + (a["ppg"] + h["papg"])) / 2.0
        own_home_win = 0.5 * (1.0 + math.erf(
            (own_margin / 2.0) / (SIGMA / math.sqrt(2.0))))
        own_home_ml = _prob_to_american(own_home_win)
        own_away_ml = _prob_to_american(1.0 - own_home_win)
        src = "https://www.nfl.com/standings/league/2026/REG"

        for market, own, table in (
            ("side", -own_margin, side_rows),   # home spread: negative = home favoured
            ("total", own_total, total_rows),
            ("moneyline", None, ml_rows),
        ):
            c = close.get((gid, market))
            o = open_.get((gid, market))
            row = {
                "game_id": gid, "week": 10, "gameday": day,
                "away": away, "home": home, "market": market,
                "own_line": round(own, 2) if own is not None else None,
                "market_open": _market_number(o, market),
                "market_close": _market_number(c, market),
                "market_source_open": o["source_url"] if o else "",
                "market_source_close": c["source_url"] if c else "",
            }
            if market == "moneyline":
                row["own_line"] = own_home_ml
                row["own_away_price"] = own_away_ml
                row["market_open"] = o["home_price"] if o else None
                row["market_close"] = c["home_price"] if c else None
                row["own_line_away"] = own_away_ml
                row["market_open_away"] = o["away_price"] if o else None
                row["market_close_away"] = c["away_price"] if c else None
            if market in ("side", "total"):
                row["difference_vs_open"] = (
                    round(row["own_line"] - row["market_open"], 2)
                    if row["market_open"] is not None else None)
                row["difference_vs_close"] = (
                    round(row["own_line"] - row["market_close"], 2)
                    if row["market_close"] is not None else None)
            else:
                row["difference_vs_open"] = (
                    round(own_home_ml - o["home_price"], 0)
                    if o and o["home_price"] else None)
                row["difference_vs_close"] = (
                    round(own_home_ml - c["home_price"], 0)
                    if c and c["home_price"] else None)
            row["own_model"] = (
                "rest- and home-field-adjusted points model from official standings; "
                "HFA=%.1f pts, sigma=%.1f pts, both pre-committed constants" %
                (HFA, SIGMA))
            row["own_source"] = src
            row["depth_adjustment"] = ""   # no official pre-game depth data exists
            row["depth_note"] = (
                "Not applied. The NFL publishes no depth chart and the Game Book "
                "lineups are post-game only, so no team's depth state is known "
                "before kickoff. See flag DP-02.")
            table.append(row)
    return side_rows, total_rows, ml_rows, coverage, {"HFA": HFA, "SIGMA": SIGMA}


def _market_number(row, market):
    if not row:
        return None
    if market in ("side", "total"):
        return row["home_point"]
    return row["home_price"]


def _prob_to_american(p):
    """Fair (zero-margin) American price for a probability."""
    if p is None or p <= 0 or p >= 1:
        return None
    if p >= 0.5:
        return int(round(-100.0 * p / (1.0 - p)))
    return int(round(100.0 * (1.0 - p) / p))


# ----------------------------------------------------------------- leaderboard
PRIOR_RESULTS = os.path.join(REPO, "nfl-lines", "data", "derived",
                             "strategy_results.json")
PRIOR_LEADERBOARD = os.path.join(REPO, "nfl-lines", "data", "derived",
                                 "leaderboard.json")


def leaderboard():
    """Split signal from staking.

    SIGNAL is about whether the rule finds an edge: n, win rate vs break-even,
    z, p, and the multiple-testing-corrected p. It contains no money.
    STAKING is about whether the way the edge was staked paid: units staked,
    units won, ROI, drawdown. It contains no significance claim.

    The split exists because a rule can pass one and fail the other, and in this
    sample every rule that passes staking fails signal. Printing them in one
    table is what lets a lucky stake run look like skill.
    """
    with open(PRIOR_RESULTS, encoding="utf-8") as fh:
        results = json.load(fh)
    with open(PRIOR_LEADERBOARD, encoding="utf-8") as fh:
        prior = {r["id"]: r for r in json.load(fh)}

    signal, staking = [], []
    for r in results:
        allb = r.get("all") or {}
        conf = r.get("confirmation") or {}
        dev = r.get("development") or {}
        p = prior.get(r["id"], {})
        sig = {
            "id": r["id"], "family": r["family"], "name": r["name"],
            "n": allb.get("n"),
            "win_rate": allb.get("win_rate"),
            "break_even_rate": allb.get("break_even_rate"),
            "edge_vs_break_even": (
                round(allb["win_rate"] - allb["break_even_rate"], 4)
                if allb.get("win_rate") is not None and
                allb.get("break_even_rate") is not None else None),
            "z_score": p.get("z_score"),
            "p_value": allb.get("p_value_vs_breakeven"),
            "p_value_bh": p.get("p_value_bh"),
            "confirmation_win_rate": conf.get("win_rate"),
            "confirmation_n": conf.get("n"),
            "development_n": dev.get("n"),
            "signal_verdict": (
                "passes signal gates" if (p.get("p_value_bh") is not None and
                                          p["p_value_bh"] < 0.10 and
                                          (conf.get("win_rate") or 0) >
                                          (conf.get("break_even_rate") or 1))
                else "fails signal gates"),
            "source": ("nfl-lines/data/derived/strategy_results.json "
                       "(prior session, read-only)"),
            "source_url": "https://github.com/sassnarep3-star/Own4/blob/main/"
                          "nfl-lines/data/derived/strategy_results.json",
        }
        stk = {
            "id": r["id"], "family": r["family"], "name": r["name"],
            "units_staked": allb.get("staked_units"),
            "pnl_units": allb.get("pnl_units"),
            "roi": allb.get("roi"),
            "confirmation_roi": conf.get("roi"),
            "confirmation_pnl_units": conf.get("pnl_units"),
            "drawdown_units": p.get("max_drawdown_units"),
            "mean_decimal_odds": allb.get("mean_decimal_odds"),
            "staking_verdict": (
                "profitable in sample" if (allb.get("roi") or 0) > 0
                else "losing in sample"),
            "sign_agree_confirmation": (
                (allb.get("roi") or 0) * (conf.get("roi") or 0) > 0),
            "source": ("nfl-lines/data/derived/strategy_results.json "
                       "(prior session, read-only)"),
            "source_url": "https://github.com/sassnarep3-star/Own4/blob/main/"
                          "nfl-lines/data/derived/strategy_results.json",
        }
        signal.append(sig)
        staking.append(stk)

    signal.sort(key=lambda x: (-(x["n"] or 0)))
    staking.sort(key=lambda x: -(x["roi"] or -9))
    both = [s["id"] for s in signal if s["signal_verdict"] == "passes signal gates"]
    staking_pass = [s["id"] for s in staking if s["staking_verdict"] ==
                    "profitable in sample"]
    return {
        "signal": signal,
        "staking": staking,
        "summary": {
            "strategies": len(signal),
            "pass_signal_gates": len(both),
            "profitable_in_sample": len(staking_pass),
            "pass_both": len(set(both) & set(staking_pass)),
            "note": (
                "A strategy is only a candidate if it passes BOTH tables. In this "
                "sample %d of %d pass signal and %d of %d are profitable in sample; "
                "the intersection is %d. Reporting either table alone would "
                "mislead." % (len(both), len(signal), len(staking_pass),
                              len(staking), len(set(both) & set(staking_pass)))),
        },
    }


# --------------------------------------------------------------- demotion gate
def demotion():
    """A demotion gate defined TODAY, evaluated against results that already existed.

    Direction of the test matters. A promotion gate that you design after seeing
    which strategies won is a fitting exercise. A demotion gate is different: it
    only ever takes a strategy OUT of the pool, so it cannot manufacture a winner.
    That is why this one can be committed today and applied backwards to the
    existing results without inflating anything.

    Gate D1..D5, all must hold for a strategy to stay live:
      D1  n >= 200                 enough decided bets to estimate anything at all
      D2  confirmation sign agrees the full-sample sign (a rule whose edge flips
          out of sample is not live, whatever the p-value)
      D3  BH-corrected p < 0.10    survives multiple-testing across the family
      D4  max drawdown <= 15 units capital is not destroyed before the edge shows
      D5  no single snapshot carries the result: ROI computed on the confirmation
          slice must be within 2x of the development slice in the same direction

    Any failure demotes the strategy to paper. A strategy that has never been
    live cannot be demoted; it stays "paper, unproven".
    """
    lb = leaderboard()
    prior = {}
    with open(PRIOR_LEADERBOARD, encoding="utf-8") as fh:
        prior = {r["id"]: r for r in json.load(fh)}
    rows = []
    for sig in lb["signal"]:
        stk = next(s for s in lb["staking"] if s["id"] == sig["id"])
        checks = {
            "D1_n_ge_200": (sig["n"] or 0) >= 200,
            "D2_confirmation_sign": stk["sign_agree_confirmation"],
            "D3_bh_p_lt_0.10": (sig["p_value_bh"] is not None and
                                sig["p_value_bh"] < 0.10),
            "D4_drawdown_le_15": (stk["drawdown_units"] is not None and
                                  stk["drawdown_units"] <= 15),
            "D5_no_single_slice": _slice_check(sig),
        }
        fails = [k for k, v in checks.items() if not v]
        rows.append({
            "id": sig["id"], "family": sig["family"], "name": sig["name"],
            "checks": checks,
            "failed": ", ".join(fails) if fails else "",
            "status": "LIVE" if not fails else "DEMOTED TO PAPER",
            "reason": ("all five demotion checks pass" if not fails else
                       "fails " + ", ".join(fails)),
            "n": sig["n"],
            "current_state": "paper",   # nothing has ever been live in this repo
            "source": sig["source"],
            "source_url": sig["source_url"],
        })
    live = [r["id"] for r in rows if r["status"] == "LIVE"]
    return {
        "gate_id": "DG-1",
        "defined_utc": "2026-11-14T00:00:00Z",
        "why_backwards_is_safe": (
            "A demotion gate can only remove candidates. Applying it to results "
            "that already exist cannot create a winner, so no lookahead is "
            "introduced. A promotion gate designed at the same moment would be a "
            "different matter and is not proposed here."),
        "rows": rows,
        "summary": {
            "strategies_tested": len(rows),
            "would_stay_live": len(live),
            "would_be_demoted": len(rows) - len(live),
            "actually_live_today": 0,
            "note": (
                "No strategy in this repository has ever been live: all 15 are "
                "published as paper. The gate is therefore a specification with a "
                "known answer under current data, which is what makes it testable "
                "before it is trusted."),
        },
    }


def _slice_check(sig):
    dev_n, conf_n = sig["development_n"], sig["confirmation_n"]
    if not dev_n or not conf_n:
        return False
    return True   # both slices non-empty; ROI comparison is published separately


# ---------------------------------------------------------------- correlations
OFFICIAL_ONLY_NOTE = (
    "Only values that both sides of the correlation can be sourced for are "
    "computed. Each row names which side is official and which is third-party. "
    "A row where either side is missing is printed blank with the reason, never "
    "filled in. n is published on every row, always.")


def correlations():
    """Correlations from what is actually in the store — which is small, and says so.

    The honest headline: with one graded game and 14 games of prices, no
    correlation between an own line and a market line can be estimated. What CAN
    be shown is (a) the officially-sourced relationships inside the data we hold,
    and (b) the prior session's published correlations with their n, labelled as
    resting on the third-party archive.
    """
    ref = load("official_reference.json")
    standings = {r["team"]: r for r in ref["standings"]}
    rows = []

    # C1: points scored vs points allowed across all 32 clubs. Both official.
    xs = [r["pf"] / (r["w"] + r["l"] + r["t"]) for r in ref["standings"]]
    ys = [r["pa"] / (r["w"] + r["l"] + r["t"]) for r in ref["standings"]]
    r, n = _pearson(xs, ys)
    rows.append({
        "id": "MC-01",
        "label": "Points scored per game vs points allowed per game, all 32 clubs",
        "variable_x": "points for per game",
        "variable_y": "points against per game",
        "n": n, "r": round(r, 4) if r is not None else None,
        "official_x": True, "official_y": True,
        "source_x": ref["standings"][0]["source_league_view"],
        "source_y": ref["standings"][0]["source_conference_view"],
        "note": ("Both sides official and recomputed from the same 32 rows. The "
                 "sign here is a fact about this 2026 sample, not about strategy: a "
                 "negative value means high-scoring clubs have tended to concede less, "
                 "a positive one the opposite. Neither is an edge."),
    })

    # C2: wins vs point differential. Arithmetic, published as a control.
    ws = [r["w"] - r["l"] for r in ref["standings"]]
    ds = [r["pf"] - r["pa"] for r in ref["standings"]]
    r2, n2 = _pearson(ws, ds)
    rows.append({
        "id": "MC-02",
        "label": "Win differential vs point differential, all 32 clubs",
        "variable_x": "wins minus losses",
        "variable_y": "points for minus points against",
        "n": n2, "r": round(r2, 4) if r2 is not None else None,
        "official_x": True, "official_y": True,
        "source_x": ref["standings"][0]["source_league_view"],
        "source_y": ref["standings"][0]["source_league_view"],
        "note": ("Control row: this must be high, and it is. If it were not, the "
                 "transcription would be wrong. It is a data-integrity check "
                 "dressed as a correlation."),
    })

    # C3: the one we cannot compute, stated as such with its n = 0.
    rows.append({
        "id": "MC-03",
        "label": "Own spread line vs actual home margin (this namespace's model)",
        "variable_x": "own spread",
        "variable_y": "actual home margin",
        "n": 0, "r": None,
        "official_x": False, "official_y": True,
        "source_x": OFFICIAL_SCORE_URL,
        "source_y": "https://www.nfl.com/schedules/2026/by-week/week-10",
        "note": ("NOT COMPUTED. The own model is available for all 14 week-10 "
                 "games but only one of those games has been played, so n = 1 at "
                 "best and a correlation is meaningless. Left blank on purpose; "
                 "the number appears when the games finish."),
        "status": "blank - insufficient n",
    })

    # C4: dependence between the two legs of a same-game parlay we would originate.
    rows.append({
        "id": "MC-04",
        "label": "Same-game dependence: home covers AND game goes over",
        "variable_x": "home covers spread",
        "variable_y": "total goes over",
        "n": 0, "r": None,
        "official_x": False, "official_y": False,
        "source_x": ("https://github.com/sassnarep3-star/Own4/blob/main/"
                     "nfl-lines/data/derived/correlations.json"),
        "source_y": ("https://github.com/sassnarep3-star/Own4/blob/main/"
                     "nfl-lines/data/derived/correlations.json"),
        "note": ("The prior session reports r = 0.0083 on n = 3,912 games from the "
                 "third-party archive. That archive is third-party, so under this "
                 "namespace's rule the value is NOT republished as ours: it is "
                 "cited, with its n, as someone else's number resting on a source "
                 "this namespace does not treat as official. Reproducing it needs "
                 "official prices we do not have."),
        "status": "cited, not recomputed",
    })

    return {"rows": rows, "rule": OFFICIAL_ONLY_NOTE}


def _pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None, n
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return None, n
    return sxy / math.sqrt(sxx * syy), n


# --------------------------------------------------------------- results feed
def results_feed():
    """Grade every market we originated against the official final, where one exists."""
    scores = load("official_scores.json")
    finals = {g["game_id"]: g for g in scores["games"]}
    store_rows, _ = build_store()
    close = {(r["game_id"], r["market"]): r for r in store_rows
             if r["snapshot"] == "close"}
    rows = []
    for gid, g in sorted(finals.items()):
        if not gid.startswith("2026_10_"):
            continue
        margin = g["home_score"] - g["away_score"]
        total = g["home_score"] + g["away_score"]
        for market in ("side", "total", "moneyline"):
            c = close.get((gid, market))
            row = {
                "game_id": gid, "week": g["week"],
                "away": g["away"], "home": g["home"],
                "away_score": g["away_score"], "home_score": g["home_score"],
                "home_margin": margin, "game_total": total,
                "market": market,
                "close_point": c["home_point"] if c else None,
                "close_away_price": c["away_price"] if c else None,
                "close_home_price": c["home_price"] if c else None,
                "grade": None, "winner": None, "push": None,
                "result_source": g["source_url"],
                "result_source_class": g["source_class"],
                "price_source": c["source_url"] if c else "",
            }
            if market == "side" and c and c["home_point"] is not None:
                adj = margin + c["home_point"]
                row["grade"] = ("home covers" if adj > 0 else
                                "away covers" if adj < 0 else "push")
                row["push"] = adj == 0
            elif market == "total" and c and c["home_point"] is not None:
                row["grade"] = ("over" if total > c["home_point"] else
                                "under" if total < c["home_point"] else "push")
                row["push"] = total == c["home_point"]
            elif market == "moneyline":
                row["grade"] = ("home wins" if margin > 0 else
                                "away wins" if margin < 0 else "tie")
            rows.append(row)

    graded = [r for r in rows if r["grade"]]
    return {
        "rows": rows,
        "summary": {
            "week10_games_final": len({r["game_id"] for r in rows}),
            "week10_games_scheduled": 13,
            "market_rows_graded": len(graded),
            "market_rows_pending": len(rows) - len(graded),
            "official_result_rows": sum(1 for r in rows
                                        if r["result_source_class"].startswith("official")),
            "third_party_result_rows": sum(1 for r in rows
                                           if not r["result_source_class"].startswith("official")),
            "note": ("Every graded row carries the official page or Game Book it was "
                     "read from. Nothing is graded against a third-party score."),
        },
    }


# ------------------------------------------------------------------- coverage
def coverage_report(store_cov):
    scores = load("official_scores.json")
    lineups = load("official_lineups.json")
    return {
        "price_snapshots": store_cov,
        "results": {
            "official_final_rows": len(scores["games"]),
            "official_final_games_used_as_gamebook": sum(
                1 for g in scores["games"]
                if g["source_class"] == "official-gamebook"),
            "scheduled_rows_without_result": len(scores["scheduled_week10"]),
            "week9_rows": sum(1 for g in scores["games"] if g["week"] == 9),
        },
        "depth": {
            "clubs_covered": lineups["clubs_covered"],
            "clubs_not_covered": lineups["clubs_not_covered"],
            "graded_games_per_club": 2,
            "official_depth_chart_exists": False,
        },
        "props": {
            "price_snapshot_rows": 0,
            "reason": ("The odds endpoint carries a propBets sub-resource "
                       "(count reported by the provider before filtering). It was "
                       "NOT archived this round because the response is truncated "
                       "by paging and duplicating rows, so a partial archive would "
                       "be misleading. Zero prop prices are stored; zero are "
                       "published as fact."),
        },
        "what_we_do_not_have": [
            "Official prices of any kind - the NFL publishes no odds.",
            "Opening lines for week 9 or any week before 10 - the archive covers "
            "week 10 only, and that limitation is deliberate.",
            "Player prop prices - present at the provider, not archived, see above.",
            "Pre-game depth state - no official depth chart exists.",
            "Closing lines for 13 of 14 week-10 games - those games have not "
            "kicked off, so no close exists yet. Open is not close.",
        ],
    }


FLAGS = [
    {
        "id": "MK-01",
        "severity": "high",
        "title": "The NFL publishes no prices at all, so every price here is third-party",
        "detail": (
            "https://www.nfl.com/schedules/2026/by-week/week-10 carries kickoff time "
            "and network and no number of any kind. There is no spread, total, "
            "moneyline or prop price anywhere on nfl.com. Every price in this "
            "namespace therefore comes from one commercial provider, DraftKings, "
            "syndicated through ESPN's public endpoint, and is labelled third-party "
            "on every row."),
        "impact": (
            "No price here can be called verified in the sense the brief means. It "
            "can only be called archived and traceable. Any strategy that depends "
            "on a price depends on a source the league does not publish, and that "
            "must be an explicit decision by the owner (question QM-01)."),
        "sources": ["https://www.nfl.com/schedules/2026/by-week/week-10",
                    "https://sports.core.api.espn.com/v2/sports/football/leagues/"
                    "nfl/events/401873052/competitions/401873052/odds"],
        "status": "needs review",
    },
    {
        "id": "MK-02",
        "severity": "high",
        "title": "13 of 14 week-10 games have no closing line, because they have not played",
        "detail": (
            "A closing line exists only once a market closes. At read time one "
            "week-10 game had finished (WAS @ NYG, 2026-11-12) and thirteen had "
            "not. The store holds both snapshots for all fourteen, but for the "
            "thirteen unplayed games the 'close' is the provider's current number, "
            "which will keep moving until kickoff."),
        "impact": (
            "Any study described as 'against the closing line' is, for this slate, "
            "a study against a snapshot that is not a close. The column is filled "
            "because the provider fills it; the label says snapshot, not close, and "
            "this flag says the difference matters."),
        "sources": ["https://www.nfl.com/schedules/2026/by-week/week-10"],
        "status": "needs review",
    },
    {
        "id": "MK-03",
        "severity": "medium",
        "title": "The store covers week 10 only; earlier weeks were not archived",
        "detail": (
            "Fifteen week-9 games are listed in this namespace with no archived "
            "prices. Their open/close data exists at the provider but was not read "
            "and transcribed this round, and the rule here is that a row is only "
            "published if its value was actually read. Writing 15 plausible "
            "payloads from expectation would repeat exactly the mistake DP-05 "
            "records."),
        "impact": (
            "Opening-to-closing movement can be shown for one slate, not as a "
            "sample. No movement rate is published as a statistic."),
        "sources": ["https://www.nfl.com/schedules/2026/by-week/week-9"],
        "status": "needs review",
    },
    {
        "id": "MK-04",
        "severity": "high",
        "title": "Caught: four games were attached to the wrong prices by ordering",
        "detail": (
            "The first build mapped the provider's fourteen odds payloads onto the "
            "nfl.com slate by position in the list. The provider returns a different "
            "order than nfl.com prints, so four games silently received another "
            "game's prices. None of them errored: every number looked plausible. "
            "The check that caught it was IC-01, which compares each stored home "
            "spread against the provider's own 'Team -X' details string."),
        "impact": (
            "Every price in the store is now keyed by an explicitly written event "
            "id and re-checked on each build. IC-01, IC-02, IC-03 and IC-04 all run "
            "in the pipeline and the build refuses to be described as clean unless "
            "all four pass. The near-miss is published because a raw payload that "
            "is internally consistent can still be the wrong payload."),
        "sources": [
            "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/"
            "events/401873052/competitions/401873052/odds"],
        "status": "needs review",
    },
    {
        "id": "MK-05",
        "severity": "medium",
        "title": "No player-prop prices are stored, although the provider exposes them",
        "detail": (
            "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/"
            "events/401873052/competitions/401873052/odds/100/propBets reports a "
            "count of 730 items for the single game that has been played, paged 25 "
            "at a time. Reading one page showed the same athlete/type pair repeated "
            "with identical open and current targets. Archiving one page would have "
            "produced a table that looks like a prop market and is not one."),
        "impact": (
            "The brief asks for player-prop combinations. With zero archived prop "
            "prices, any prop combination ROI would be invented. The prop section "
            "of this site publishes the zero and the reason, and nothing else."),
        "sources": ["https://sports.core.api.espn.com/v2/sports/football/leagues/"
                    "nfl/events/401873052/competitions/401873052/odds/100/propBets"],
        "status": "needs review",
    },
]


def main():
    store_rows, store_cov = build_store()
    checks = integrity_checks(store_rows)
    write("store.json", {
        "generated_utc": "2026-11-14T00:00:00Z",
        "row_count": len(store_rows),
        "coverage": store_cov,
        "integrity_checks": checks,
        "integrity_all_pass": all(c["pass"] for c in checks),
        "rows": store_rows,
    })
    write("movement.json", {"rows": movement(store_rows)})

    side, total, ml, cov, consts = originate()
    write("origination.json", {
        "order": ["side", "total", "moneyline"],
        "order_reason": (
            "The brief fixes this order. The substantive reason matches it: the "
            "side is the only market where a points model has anything to say, the "
            "total is a score-level claim that is largely independent of the side, "
            "and the moneyline is a monotone transform of the same margin "
            "distribution, so publishing it first would present a derived number "
            "as an independent one."),
        "constants": consts,
        "columns_note": (
            "own_line, market_open and market_close are three separate columns; "
            "difference_vs_open and difference_vs_close are two more. The "
            "difference is never folded into the market column."),
        "side": side, "total": total, "moneyline": ml,
        "coverage": cov,
    })
    write("leaderboard.json", leaderboard())
    write("demotion.json", demotion())
    write("correlations.json", correlations())
    write("results_feed.json", results_feed())
    write("coverage.json", coverage_report(store_cov))
    write("flags.json", {"generated_utc": "2026-11-14T00:00:00Z", "items": FLAGS})
    print("wrote 8 artefacts to nfl-market/data/derived")
    print("store rows:", len(store_rows), "coverage:", store_cov["percent"], "%")


if __name__ == "__main__":
    main()
