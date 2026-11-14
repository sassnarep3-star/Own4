"""nfl-markets engine — PRICE-SNAPSHOT STORE.

The user requirement: "records opening and closing numbers for every market we
originate". This module emits one row per (game × market) with:

  market_seq        origination order: 1 = side (spread), 2 = total, 3 = moneyline
  model_fair_line   this repository's walk-forward model number (engine/model.py)
  market_open_line  opening number from the archive (blank when no archive exists)
  market_close_line closing number from the archive (blank pre-close for future games)
  diff_open_line    model_fair_line − market_open_line   (separate column)
  diff_close_line   model_fair_line − market_close_line  (separate column)
  *_source_key      which registered source the number came from
  verification_status  one of:
      VERIFIED-ARCHIVE   number read from the named archive file (third-party,
                         labelled; the archive itself is the evidence)
      UNPUBLISHED-TIMING number read from an archive whose capture time the
                         source does not publish (sc_lines.csv) — extra flag
      UNVERIFIED-BLANK   no archive exists → value left BLANK and flagged
                         (never inferred)

Moneylines: no opening archive exists anywhere (flagged) — open column stays
blank for every ML row. Close ML odds: closing_lines.csv 2011-2018; games.csv
moneyline fields 2019+.
"""
from . import config as C, loader, model as M, results_feed as F

MARKETS = [("SIDE", 1), ("TOTAL", 2), ("MONEYLINE", 3)]

def _close_from_archive(g):
    """returns dict per market from closing_lines.csv (2011-2018 coverage)"""
    arch = g["close_archive"]
    if not arch:
        return {}
    out = {}
    home, away = g["home_team"], g["away_team"]
    for row in arch["rows"]:
        t = row["type"]
        if t == "SPREAD" and row["side"] in (home, away):
            out.setdefault("SPREAD", {})[row["side"]] = {
                "line": float(row["line"]), "odds": row["odds"], "outcome": row["outcome"]}
        elif t == "TOTAL":
            out.setdefault("TOTAL", {})[row["side"]] = {
                "line": float(row["line"]), "odds": row["odds"], "outcome": row["outcome"]}
        elif t == "MONEYLINE" and row["side"] in (home, away):
            out.setdefault("MONEYLINE", {})[row["side"]] = {
                "odds": float(row["odds"]), "outcome": row["outcome"]}
    return out

def build(model, games):
    rows = []
    for g in sorted(games, key=lambda g: (g["gameday"], g["game_id"])):
        m = model.get(g["game_id"])
        if m is None:
            continue
        season = g["season"]
        home, away = g["home_team"], g["away_team"]
        ca = _close_from_archive(g)
        o21 = g["open_archive_2021"] or {}
        o13 = g["open_archive_2013"] or {}

        # ---- market open (side) ----
        open_spread, open_src, open_status, open_flag = "", "", "UNVERIFIED-BLANK", "no opening archive"
        if season == 2021 and "SPREAD" in o21:
            for side, line in o21["SPREAD"].items():
                hm = loader.team_spread_to_home_margin(line, side, home, away)
                if hm is not None:
                    open_spread, open_src, open_status, open_flag = hm, "nfl_data_initial", "VERIFIED-ARCHIVE", ""
        elif season in C.OPEN_ARCHIVE_SEASONS and "SPREAD" in o13:
            for side, line in o13["SPREAD"].items():
                hm = loader.team_spread_to_home_margin(line, side, home, away)
                if hm is not None:
                    open_spread, open_src, open_status = hm, "nfl_data_sc", "UNPUBLISHED-TIMING"
                    open_flag = "source does not publish capture time; pre-close archive assumed"
        # ---- market open (total) ----
        open_total, open_total_src, open_total_status, open_total_flag = "", "", "UNVERIFIED-BLANK", "no opening archive"
        if season == 2021 and "TOTAL" in o21:
            vals = {v for v in o21["TOTAL"].values()}
            if len(vals) == 1:
                open_total, open_total_src, open_total_status, open_total_flag = vals.pop(), "nfl_data_initial", "VERIFIED-ARCHIVE", ""

        # ---- market close ----
        close_spread = close_spread_src = close_spread_odds = ""
        close_total = close_total_src = close_total_odds = ""
        close_ml_home = close_ml_away = close_ml_src = ""
        close_spread_status = close_total_status = close_ml_status = "VERIFIED-ARCHIVE"
        if 2011 <= season <= 2018 and ca:
            pass  # archive rows handled below; fallbacks applied after
            sp = ca.get("SPREAD", {}); hm_row = sp.get(home)
            if hm_row is not None:
                close_spread = -hm_row["line"]          # team line -> home margin convention
                close_spread_odds = hm_row["odds"]
                close_spread_src = "nfl_data_closing"
            tt = ca.get("TOTAL", {})
            if tt:
                first = next(iter(tt.values()))
                close_total, close_total_odds, close_total_src = first["line"], first["odds"], "nfl_data_closing"
            mlh = ca.get("MONEYLINE", {}).get(home); mla = ca.get("MONEYLINE", {}).get(away)
            if mlh is not None and mla is not None:
                close_ml_home, close_ml_away, close_ml_src = mlh["odds"], mla["odds"], "nfl_data_closing"
        # fallback to the games.csv line where the closing archive lacks this market
        if close_spread == "" and g["spread_line"] is not None:
            close_spread, close_spread_src, close_spread_status = g["spread_line"], "nfl_data_games", "ARCHIVE-UNPUBLISHED-TIMING"
        if close_total == "" and g["total_line"] is not None:
            close_total, close_total_src, close_total_status = g["total_line"], "nfl_data_games", "ARCHIVE-UNPUBLISHED-TIMING"
        if close_ml_home == "" and g["home_moneyline"] not in (None, ""):
            close_ml_home, close_ml_away, close_ml_src = g["home_moneyline"], g["away_moneyline"], "nfl_data_games"
            close_ml_status = "ARCHIVE-UNPUBLISHED-TIMING"
        if season >= 2019:
            if g["spread_line"] is not None:
                close_spread, close_spread_src = g["spread_line"], "nfl_data_games"
                close_spread_status = "ARCHIVE-UNPUBLISHED-TIMING"
            if g["total_line"] is not None:
                close_total, close_total_src = g["total_line"], "nfl_data_games"
                close_total_status = "ARCHIVE-UNPUBLISHED-TIMING"
            if g["home_moneyline"] not in (None, ""):
                close_ml_home, close_ml_away, close_ml_src = g["home_moneyline"], g["away_moneyline"], "nfl_data_games"
                close_ml_status = "ARCHIVE-UNPUBLISHED-TIMING"

        official_url = F.nfl_game_url(g, _nickmap())
        captured = m["model_origination_cutoff"] + "T12:00:00Z (origination convention: day before kickoff)"

        for market, seq in MARKETS:
            if market == "SIDE":
                fair, open_v, open_st = m["fair_spread"], open_spread, open_status
                open_src_k, open_fl = open_src, open_flag
                close_v, close_src_k, close_odds = close_spread, close_spread_src, close_spread_odds
                units = "points (home-margin convention)"
            elif market == "TOTAL":
                fair, open_v, open_st = m["fair_total"], open_total, open_total_status
                open_src_k, open_fl = open_total_src, open_total_flag
                close_v, close_src_k, close_odds = close_total, close_total_src, close_total_odds
                units = "points"
            else:
                fair, open_v, open_st = m["fair_home_winprob"], "", "UNVERIFIED-BLANK"
                open_src_k, open_fl = "", "no opening ML archive exists anywhere (flagged)"
                close_v, close_src_k, close_odds = close_ml_home, close_ml_src, ""
                units = "home win probability (fair) / American odds (market)"

            diff_open = round(fair - open_v, 2) if open_v not in ("", None) else ""
            if market == "MONEYLINE":
                diff_close = ""
                if close_v not in ("", None):
                    imp = loader.implied_prob(close_v)
                    if imp is not None:
                        diff_close = round(fair - imp, 4)   # probability points, vig included
            else:
                diff_close = round(fair - close_v, 2) if close_v not in ("", None) else ""

            rows.append({
                "snapshot_id": f"{g['game_id']}_{market}",
                "game_id": g["game_id"], "season": season, "week": g["week"],
                "gameday": g["gameday"], "away_team": away, "home_team": home,
                "market_seq": seq, "market": market, "units": units,
                "model_fair_line": fair,
                "market_open_line": open_v, "market_open_source_key": open_src_k,
                "market_close_line": close_v, "market_close_source_key": close_src_k,
                "market_close_odds_american": close_odds,
                "diff_open_line": diff_open, "diff_close_line": diff_close,
                "open_verification_status": open_st, "open_flags": open_fl,
                "close_verification_status": (
                    "PENDING-CLOSE" if g["home_score"] is None else (
                        ({"SIDE": close_spread_status, "TOTAL": close_total_status, "MONEYLINE": close_ml_status}[market]
                         if close_v not in ("", None) else "UNVERIFIED-BLANK"))),
                "close_flags": ("game not played yet — number is the latest POSTED line, not a close"
                                if g["home_score"] is None and close_v not in ("", None) else
                                ("" if close_v not in ("", None) else "no close archived yet")),
                "model_captured_at": captured,
                "model_source_key": "repo_engine",
                "official_source_url": official_url,
                "mirror_source_key": "nfl_data_games",
            })
    return rows

_NICK = None
def _nickmap():
    global _NICK
    if _NICK is None:
        static = {"OAK": "Raiders", "SD": "Chargers", "STL": "Rams", "WSH": "Commanders"}
        cur = {t["team"]: t["nickname"] for t in C.r(C.os.path.join(C.RAW, "teams.csv")) if t["season"] == "2026"}
        _NICK = {**static, **cur}
    return _NICK
