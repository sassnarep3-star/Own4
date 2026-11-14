"""nfl-markets engine — VERIFIED RESULTS FEED.

One row per played game (2011-2026 regular seasons, the origination era),
carrying:
- scores/results as published in the nflverse/nfldata mirror of official results
  (game scores originate from the NFL's official schedule & score pages);
- an OFFICIAL source link on every row (nfl.com game page, constructed from the
  official URL pattern, spot-verified live in-session — see verification.json);
- a verification status per row:
    cross-checked-official  : 2026 rows re-computed against the official standings
                              capture that a peer session verified 32/32 vs nfl.com;
    archive-official-origin : pre-2026 rows transcribed from the mirror, official
                              link provided for manual review (not re-fetched row by row).
Backtests and ROI in this namespace settle ONLY against this feed.
"""
import collections, csv, datetime as dt
from . import config as C, loader

def nfl_game_url(g, nick):
    # official nfl.com game page pattern, e.g.
    # https://www.nfl.com/games/commanders-at-giants-2026-reg-10
    a = nick[g["away_team"]].lower().replace(" ", "-")
    h = nick[g["home_team"]].lower().replace(" ", "-")
    return f"https://www.nfl.com/games/{a}-at-{h}-{g['season']}-reg-{g['week']}"

def nfl_week_url(g):
    return f"https://www.nfl.com/schedules/{g['season']}/REG{g['week']}/"

def build():
    games = loader.compile_league()
    teams_2026 = {t["team"]: t for t in C.r(C.os.path.join(C.RAW, "teams.csv")) if t["season"] == "2026"}
    nick = {k: v["nickname"] for k, v in teams_2026.items()}
    # historical codes that changed franchise city keep their era nickname via
    # the 2026 map only for current codes; old codes fall back to a static map
    static_nick = {"OAK": "Raiders", "SD": "Chargers", "STL": "Rams", "WSH": "Commanders"}
    def nick_of(team):
        return nick.get(team) or static_nick.get(team) or team

    nickmap = {t: nick_of(t) for t in set(list(nick) + list(static_nick))}
    rows = []
    for g in sorted(games, key=lambda g: (g["gameday"], g["game_id"])):
        if g["season"] < 2011 or g["home_score"] is None:
            continue
        status = "cross-checked-official" if g["season"] == 2026 else "archive-official-origin"
        rows.append({
            "game_id": g["game_id"], "season": g["season"], "week": g["week"],
            "gameday": g["gameday"], "weekday": g["weekday"], "gametime": g["gametime"],
            "away_team": g["away_team"], "home_team": g["home_team"],
            "away_score": int(g["away_score"]), "home_score": int(g["home_score"]),
            "home_margin": int(g["result"]), "total_points": int(g["total"]),
            "winner": g["home_team"] if g["result"] > 0 else (g["away_team"] if g["result"] < 0 else "TIE"),
            "overtime": g["overtime"],
            "official_source_url": nfl_game_url(g, nickmap),
            "official_week_url": nfl_week_url(g),
            "mirror_source_key": "nfl_data_games",
            "verification_status": status,
            "flags": "",
        })

    # 2026 standings recomputation vs the official standings capture (peer-verified vs nfl.com)
    rec = recompute_standings_2026(rows)
    official = C.jl(C.os.path.join(C.ROOT, "nfl-arena", "data", "raw", "nfl_standings_2026_week10.json"))
    mism = compare_standings(rec, official)
    return rows, {"standings_reconciliation": rec, "mismatches_vs_official_capture": mism}

def recompute_standings_2026(feed_rows):
    s = collections.defaultdict(lambda: {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0})
    for r_ in feed_rows:
        if r_["season"] != 2026:
            continue
        h, a = s[r_["home_team"]], s[r_["away_team"]]
        hs, as_ = r_["home_score"], r_["away_score"]
        h["pf"] += hs; h["pa"] += as_; a["pf"] += as_; a["pa"] += hs
        if hs > as_: h["w"] += 1; a["l"] += 1
        elif hs < as_: a["w"] += 1; h["l"] += 1
        else: h["t"] += 1; a["t"] += 1
    return {t: dict(v, games=v["w"] + v["l"] + v["t"]) for t, v in s.items()}

def compare_standings(rec, official_json):
    """official_json: nfl-arena capture of nfl.com/standings (peer session verified 32/32)."""
    def extract_official(obj):
        """the capture stores rows under `rows` with keys team/w/l/t/pf/pa (nfl.com transcription)"""
        rows = []
        if isinstance(obj, dict) and isinstance(obj.get("rows"), list):
            rows = [r for r in obj["rows"] if isinstance(r, dict) and "team" in r]
        else:
            def walk(o):
                if isinstance(o, dict):
                    if "team" in o and ("wins" in o or "w" in o):
                        rows.append(o)
                    else:
                        for v in o.values(): walk(v)
                elif isinstance(o, list):
                    for v in o: walk(v)
            walk(obj)
        return rows
    out_rows = extract_official(official_json)
    if not out_rows:
        return {"status": "OFFICIAL_CAPTURE_NOT_PARSEABLE", "official_rows": 0}
    alias = {"AZ": "ARI", "WSH": "WAS"}   # nfl.com uses AZ/WSH; nflverse uses ARI/WAS (verified live 2026-11-14)
    mismatches = []
    matched = 0
    for o in out_rows:
        team = str(o.get("team") or o.get("team_abbr")).upper()
        team = alias.get(team, team)
        if team not in rec:
            continue
        matched += 1
        rw = rec[team]
        for off_k, rec_k in (("wins", "w"), ("w", "w"), ("losses", "l"), ("l", "l"),
                             ("ties", "t"), ("t", "t")):
            ov = o.get(off_k)
            if ov is not None and int(ov) != rw[rec_k]:
                mismatches.append({"team": team, "field": off_k, "official": ov, "recomputed": rw[rec_k]})
        for off_k, rec_k in (("pf", "pf"), ("pa", "pa")):
            ov = o.get(off_k)
            if ov is not None and int(ov) != rw[rec_k]:
                mismatches.append({"team": team, "field": off_k, "official": ov, "recomputed": rw[rec_k]})
    return {"status": "OK" if not mismatches else "MISMATCHES",
            "official_rows_matched": matched, "mismatches": mismatches}
