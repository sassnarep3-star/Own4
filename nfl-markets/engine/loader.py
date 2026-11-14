"""nfl-markets engine — data loading, joining, and convention conversion.

Every loader records which file each field came from (provenance is carried
into the snapshot store columns *_source_key). Nothing is invented: fields
that a file does not contain are simply absent.
"""
import csv, datetime as dt
from . import config as C

# ---- raw loading ------------------------------------------------------------

def load_games():
    """games.csv rows (nflverse/nfldata). Regular-season only, parsed types."""
    out = []
    for row in C.r(C.os.path.join(C.RAW, "games.csv")):
        if row["game_type"] != "REG":
            continue
        def num(k):
            v = row[k]
            return float(v) if v not in ("", None) else None
        out.append({
            "game_id": row["game_id"],                 # nflverse id, e.g. 2026_10_BUF_NYJ
            "old_game_id": row["old_game_id"],          # numeric id, e.g. 2026101200 (joins closing_lines/sc_lines)
            "season": int(row["season"]), "week": int(row["week"]),
            "gameday": row["gameday"], "weekday": row["weekday"], "gametime": row["gametime"],
            "away_team": row["away_team"], "home_team": row["home_team"],
            "away_score": num("away_score"), "home_score": num("home_score"),
            "result": num("result"),                     # home margin, official-origin
            "total": num("total"),                       # combined points, official-origin
            "overtime": row["overtime"],
            # THIRD-PARTY market numbers (nflverse archive; capture time not published by source):
            "spread_line": num("spread_line"),           # home-margin convention (see config.py)
            "total_line": num("total_line"),
            "home_moneyline": num("home_moneyline"), "away_moneyline": num("away_moneyline"),
            "away_rest": num("away_rest"), "home_rest": num("home_rest"),
            "div_game": row["div_game"], "roof": row["roof"], "surface": row["surface"],
            "temp": num("temp"), "wind": num("wind"),
            "home_qb_name": row["home_qb_name"], "away_qb_name": row["away_qb_name"],
            "stadium": row["stadium"],
        })
    return out

def load_closing_lines():
    """closing_lines.csv (2006-2018): per-side SPREAD/TOTAL/MONEYLINE with odds+outcome.

    `line` here is the TEAM's line (negative = that team favored). We store raw;
    conversion to home-margin happens in snapshots.py after team lookup via alt_game_id.
    """
    bygame = {}
    for row in C.r(C.os.path.join(C.RAW, "closing_lines.csv")):
        g = bygame.setdefault(row["alt_game_id"], {"game_id": row["alt_game_id"],
                                                   "old_game_id": row["game_id"], "rows": []})
        g["rows"].append({"type": row["type"], "side": row["side"],
                          "line": row["line"], "odds": row["odds"], "outcome": row["outcome"]})
    return bygame

def load_team_lines(path, keyfield):
    """initial_lines.csv / sc_lines.csv: per-team spread (initial_lines also TOTAL).

    Returns dict game_key -> {"SPREAD": {team: line}, "TOTAL": {team: line}}
    team convention: line<0 = that team favored by |line| (bookmaker display).
    """
    bygame = {}
    for row in C.r(C.os.path.join(C.RAW, path)):
        g = bygame.setdefault(row[keyfield], {})
        # sc_lines.csv has no `type` column — every row is a spread (verified in-session)
        g.setdefault(row.get("type", "SPREAD"), {})[row["side"]] = float(row["line"])
    return bygame

def implied_prob(american):
    """Vig-included implied probability from American odds (no vig removal — documented)."""
    if american is None or american == "":
        return None
    a = float(american)
    return (abs(a)) / (abs(a) + 100.0) if a < 0 else 100.0 / (a + 100.0)

def team_spread_to_home_margin(line, side, home_team, away_team):
    """Bookmaker per-team line -> expected HOME margin.

    Team line L for side S (L<0 means S favored by |L|):
      S == home -> home margin = -L ; S == away -> home margin = +L.
    Verified in-session against games.csv spread_line on the 2021 season
    (median |open-converted − close| reported in snapshots QC; sign sanity 100%).
    """
    if side == home_team:
        return -line
    if side == away_team:
        return line
    return None

# ---- compiled league dataset -------------------------------------------------

def compile_league():
    """Join games + closing archive + open archives. One dict per game."""
    games = load_games()
    closes = load_closing_lines()
    opens_2021 = load_team_lines("initial_lines.csv", "about")
    opens_2013 = load_team_lines("sc_lines.csv", "game_id")
    for g in games:
        g["close_archive"] = closes.get(g["game_id"])          # 2006-2018 (rich: odds+outcome)
        g["open_archive_2021"] = opens_2021.get(g["game_id"])  # 2021 WSGT spread+total
        g["open_archive_2013"] = opens_2013.get(g["old_game_id"])  # 2013-2020 spreads
    return games
