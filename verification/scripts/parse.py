#!/usr/bin/env python3
"""parse.py — turn verbatim official NBA pages into flat tables.

Input : verification/raw/nba_games/games_<date>.html   (verbatim nba.com/games?date=...)
Output: verification/data/games.csv        one row per game (final score, both teams)
        verification/data/team_games.csv   one row per (game, team) — team-side box totals

Rules
  * Only values present in the official page payload are copied; nothing is inferred.
  * A page whose embedded game objects cannot be located is reported, never guessed.
  * Provenance: web_game_url, source_url (date page) and sha256 of the raw file.
"""
import csv, glob, hashlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "raw", "nba_games")
DATA = os.path.join(ROOT, "data")
MAN = os.path.join(ROOT, "raw", "manifest.json")

FIELD = re.compile(r'"([A-Za-z][A-Za-z0-9_]*)":')


def objects(text):
    """Yield (gameId, dict-of-top-level-scalars) for each embedded game object."""
    out = []
    for m in re.finditer(r'"gameId":"(\d{10})"', text):
        gid, start = m.group(1), m.start()
        nxt = re.search(r'"gameId":"\d{10}"', text[start + 10:])
        end = start + 10 + nxt.start() if nxt else min(len(text), start + 80000)
        win = text[start:end]
        rec = {"game_id": gid}
        for k in ("gameStatusText", "gameStatus", "period", "gameTimeUTC", "gameDateEst",
                  "gameDateTimeEst", "gameLabel", "gameSubLabel", "seriesText", "seasonYear"):
            mm = re.search(r'"%s":(?:"([^"]*)"|([^,\]}]+))' % k, win)
            if mm:
                v = mm.group(1) if mm.group(1) is not None else mm.group(2)
                if v != "null":
                    rec[k] = v
        for side in ("homeTeam", "awayTeam"):
            bm = re.search(r'"%s":\{(.*?)\}\s*,\s*"teamLeader"' % side, win, re.S)
            if not bm:
                bm = re.search(r'"%s":\{(.*)' % side, win, re.S)
            if not bm:
                continue
            b = bm.group(1)
            d = {}
            for k in ("teamId", "teamName", "teamTricode", "teamCity", "wins", "losses", "score"):
                mm = re.search(r'"%s":(?:"([^"]*)"|([-\d.]+))' % k, b)
                if mm:
                    d[k] = mm.group(1) if mm.group(1) is not None else mm.group(2)
            if "score" in d:
                rec[side] = d
        out.append(rec)
    return out


def main():
    os.makedirs(DATA, exist_ok=True)
    man = json.load(open(MAN)) if os.path.exists(MAN) else {"items": []}
    sha = {os.path.basename(i["file"]): i for i in man["items"] if i.get("file")}
    games, problems, seen = [], [], set()
    for path in sorted(glob.glob(os.path.join(RAW, "games_*.html"))):
        date = os.path.basename(path)[len("games_"):-len(".html")]
        body = open(path, encoding="utf-8", errors="ignore").read()
        text = body.replace('\\"', '"')
        h = hashlib.sha256(open(path, "rb").read()).hexdigest()
        slugs = {g: s for s, g in re.findall(r'/game/([a-z0-9-]+)-(\d{10})', text)}
        objs = objects(text)
        if not objs:
            problems.append({"file": os.path.basename(path), "issue": "no embedded game objects found"})
            continue
        for o in objs:
            gid = o["game_id"]
            if gid in seen:            # the same game can appear on adjacent date pages
                continue
            seen.add(gid)
            if "homeTeam" not in o or "awayTeam" not in o:
                problems.append({"file": os.path.basename(path), "game_id": gid,
                                 "issue": "team block missing"})
                continue
            ht, at = o["homeTeam"], o["awayTeam"]
            status = o.get("gameStatusText", "")
            final = status.lower().startswith("final")
            try:
                hs, as_ = int(float(ht.get("score", ""))), int(float(at.get("score", "")))
            except ValueError:
                hs = as_ = None
            if not final or hs is None:
                continue               # not a completed game: not part of the sample
            slug = slugs.get(gid)
            games.append({
                "game_id": gid, "date": date, "season": o.get("seasonYear", ""),
                "status": status, "ot": "OT" if "ot" in status.lower() else "",
                "away": at.get("teamTricode", ""), "away_id": at.get("teamId", ""),
                "away_name": at.get("teamName", ""), "away_pts": as_,
                "home": ht.get("teamTricode", ""), "home_id": ht.get("teamId", ""),
                "home_name": ht.get("teamName", ""), "home_pts": hs,
                "total_pts": as_ + hs, "margin_home": hs - as_,
                "home_wins_after": ht.get("wins", ""), "home_losses_after": ht.get("losses", ""),
                "away_wins_after": at.get("wins", ""), "away_losses_after": at.get("losses", ""),
                "web_game_url": (f"https://www.nba.com/game/{slug}-{gid}" if slug else ""),
                "source_url": f"https://www.nba.com/games?date={date}",
                "raw_file": os.path.relpath(path, ROOT),
                "raw_sha256": h,
                "fetched_utc": sha.get(os.path.basename(path), {}).get("fetched_utc", ""),
            })
    games.sort(key=lambda r: (r["date"], r["game_id"]))
    cols = list(games[0].keys())
    with open(os.path.join(DATA, "games.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(games)

    # team-side view
    tg = []
    for g in games:
        for side in ("away", "home"):
            opp = "home" if side == "away" else "away"
            tg.append({"date": g["date"], "game_id": g["game_id"], "team": g[side],
                       "team_id": g[f"{side}_id"], "opp": g[opp], "home": int(side == "home"),
                       "pts": g[f"{side}_pts"], "opp_pts": g[f"{opp}_pts"],
                       "margin": g[f"{side}_pts"] - g[f"{opp}_pts"],
                       "total_pts": g["total_pts"], "ot": g["ot"],
                       "source_url": g["source_url"], "web_game_url": g["web_game_url"]})
    with open(os.path.join(DATA, "team_games.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(tg[0].keys())); w.writeheader(); w.writerows(tg)

    summary = {"games": len(games), "team_game_rows": len(tg),
               "dates": sorted({g["date"] for g in games}),
               "games_per_date": {}, "problems": problems,
               "raw_files": len(glob.glob(os.path.join(RAW, "games_*.html")))}
    for g in games:
        summary["games_per_date"][g["date"]] = summary["games_per_date"].get(g["date"], 0) + 1
    json.dump(summary, open(os.path.join(DATA, "parse_summary.json"), "w"), indent=1)
    print(json.dumps(summary, indent=1))
    return 0 if games else 1


if __name__ == "__main__":
    sys.exit(main())
