#!/usr/bin/env python3
"""Parse the checked-in official NFL provenance snapshots into structured rows.

No network access. Every output row carries source_url(s) pointing at the official
page (or, for partner cross-check fields, an additional official NFL link). Values
that the official pages do not publish are left as empty strings and recorded in
data/nfl-origin/flags.json.
"""
from __future__ import annotations

import csv
import gzip
import html
import json
import os
import re
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "nfl-origin"
RAW = DATA / "raw"
MANIFEST = json.loads((RAW / "manifest.json").read_text())
NFL = "https://www.nfl.com"

OFFICIAL_HOSTS = {
    "www.nfl.com", "operations.nfl.com", "static.www.nfl.com", "media.nfl.com",
    "www.itl.nist.gov", "docs.github.com", "github.com", "api.github.com",
}

flags = []
report = {"checks": [], "counts": {}, "mismatches": []}


def add_flag(fid, title, detail, sources, fields=(), blocking=False):
    flags.append({
        "flag_id": fid,
        "title": title,
        "detail": detail,
        "status": "needs review",
        "blocking": blocking,
        "unverified_fields": list(fields),
        "source_urls": list(dict.fromkeys(sources)),
    })


def check(name, ok, detail, sources=()):
    report["checks"].append({"name": name, "result": "PASS" if ok else "REVIEW", "detail": detail, "source_urls": list(sources)})
    if not ok:
        report["mismatches"].append({"check": name, "detail": detail})
    return ok


def read_gz(rel):
    with gzip.open(ROOT / rel, "rt", encoding="utf-8", errors="replace") as f:
        return f.read()


def text(fragment):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def absolute(href):
    return urljoin(NFL + "/", href)


def write_json(name, obj):
    (DATA / name).write_text(json.dumps(obj, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_csv(name, rows):
    if not rows:
        return
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with (DATA / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            rr = {}
            for k, v in r.items():
                if isinstance(v, (list, dict)):
                    rr[k] = json.dumps(v, ensure_ascii=False)
                else:
                    rr[k] = v
            w.writerow(rr)


def manifest_item(kind, url_contains):
    for i in MANIFEST["items"]:
        if i["kind"] == kind and url_contains in i["source_url"]:
            return i
    raise KeyError((kind, url_contains))


def parse_standings(year):
    item = manifest_item("standings", f"/standings/league/{year}/reg")
    s = read_gz(item["output"])
    ths = [text(x) for x in re.findall(r"<th[^>]*>(.*?)</th>", s, re.S | re.I)]
    # Duplicate "Pct" headers belong to DIV and CONF blocks.
    headers = ["TEAM", "W", "L", "T", "PCT", "PF", "PA", "NET_PTS", "HOME", "ROAD",
               "DIV", "DIV_PCT", "CONF", "CONF_PCT", "NON_CONF", "STRK", "LAST5"]
    rows = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", s, re.S | re.I):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S | re.I)
        if len(cells) != 17:
            continue
        first = cells[0]
        abbr_m = re.search(r"logos/([A-Z0-9]{2,4})", first)
        full_m = re.search(r'd3-o-club-fullname[^>]*>(.*?)<', first, re.S | re.I)
        short_m = re.search(r'd3-o-club-shortname[^>]*>(.*?)<', first, re.S | re.I)
        href_m = re.search(r'href="([^"]*teams/[^"]+)"', first)
        if not (abbr_m and full_m and short_m and href_m):
            continue
        vals = [text(c) for c in cells[1:]]
        rows.append({
            "season": year,
            "team": text(full_m.group(1)),
            "short_name": text(short_m.group(1)),
            "abbr": abbr_m.group(1),
            "W": vals[0], "L": vals[1], "T": vals[2], "PCT": vals[3],
            "PF": vals[4], "PA": vals[5], "NET_PTS": vals[6],
            "HOME": vals[7], "ROAD": vals[8], "DIV": vals[9], "DIV_PCT": vals[10],
            "CONF": vals[11], "CONF_PCT": vals[12], "NON_CONF": vals[13],
            "STRK": vals[14], "LAST5": vals[15],
            "headers": headers,
            "source_url": absolute(href_m.group(1)),
            "source_url_table": item["source_url"],
            "raw_path": item["output"],
            "verified": True,
            "value_type": "OFFICIAL — transcribed from NFL.com table",
        })
    check(f"standings_{year}_rows", len(rows) == 32, f"{len(rows)} official standings rows parsed", [item["source_url"]])
    return rows


standings_2025 = parse_standings(2025)
standings_2026 = parse_standings(2026)

full_to_abbr = {}
short_to_abbr = {}
abbr_to_team = {}
abbr_to_team_url = {}
for r in standings_2026:
    full_to_abbr[r["team"].lower()] = r["abbr"]
    slug = re.sub(r"[^a-z0-9]+", "-", r["short_name"].lower()).strip("-")
    short_to_abbr[slug] = r["abbr"]
    abbr_to_team[r["abbr"]] = r["team"]
    abbr_to_team_url[r["abbr"]] = r["source_url"]

check("team_alias_map", len(short_to_abbr) == 32, f"{len(short_to_abbr)} official team short-name aliases", [manifest_item("standings", "/standings/league/2026/reg")["source_url"]])


def load_espn_events():
    events = {}
    espn_abbr_to_official = {}
    for year in (2025, 2026):
        item = next(i for i in MANIFEST["items"] if i["kind"] == "partner_scoreboard" and f"dates={year}&" in i["source_url"])
        payload = json.loads(read_gz(item["output"]))
        for e in payload.get("events", []):
            season = e.get("season", {})
            if season.get("year") not in (2025, 2026) or season.get("type") != 2:
                continue
            comps = e.get("competitions", [{}])[0].get("competitors", [])
            by_side = {}
            for c in comps:
                t = c.get("team", {})
                disp = t.get("displayName", "")
                official = full_to_abbr.get(disp.lower())
                if official:
                    espn_abbr_to_official[t.get("abbreviation", "")] = official
                by_side[c.get("homeAway")] = {
                    "espn_abbr": t.get("abbreviation", ""),
                    "display_name": disp,
                    "official": official,
                    "score": c.get("score"),
                    "winner": c.get("winner"),
                }
            away, home = by_side.get("away", {}), by_side.get("home", {})
            if not (away.get("official") and home.get("official")):
                continue
            key = (season["year"], e.get("week", {}).get("number"), away["official"], home["official"])
            events[key] = {
                "event_id": e.get("id"),
                "date": e.get("date"),
                "week": e.get("week", {}).get("number"),
                "season_year": season["year"],
                "away_espn": away["espn_abbr"], "home_espn": home["espn_abbr"],
                "away_official": away["official"], "home_official": home["official"],
                "away_score": away.get("score"), "home_score": home.get("score"),
                "completed": e.get("status", {}).get("type", {}).get("completed"),
                "neutral_site": e.get("competitions", [{}])[0].get("neutralSite"),
                "venue": e.get("competitions", [{}])[0].get("venue", {}).get("fullName", ""),
                "source_url": item["source_url"],
            }
    # Known abbreviation differences are derived by matching ESPN displayName to official full name.
    return events, espn_abbr_to_official


espn_events, espn_abbr_to_official = load_espn_events()


def parse_schedule(year, week):
    item = manifest_item("schedule", f"/schedules/{year}/by-week/week-{week}")
    s = read_gz(item["output"])
    by_slug = {}
    for m in re.finditer(r'<a[^>]+href="([^"]*/games/[^"]+)"[^>]*>(.*?)</a>', s, re.S | re.I):
        href, inner = m.groups()
        label = text(inner)
        slug = href.rstrip("/").split("/")[-1]
        sm = re.match(r"(.+)-at-(.+)-(\d{4})-reg-(\d+)$", slug)
        if not sm:
            continue
        if "FINAL" not in label and " at " not in label:
            continue
        # Prefer the explicit score/matchup summary link over generic team-card links.
        by_slug[slug] = (slug, label)
    rows = []
    for slug, (_, label) in by_slug.items():
        sm = re.match(r"(.+)-at-(.+)-(\d{4})-reg-(\d+)$", slug)
        away_slug, home_slug, yr, wk = sm.groups()
        away_abbr = short_to_abbr.get(away_slug)
        home_abbr = short_to_abbr.get(home_slug)
        game_url = f"{NFL}/games/{slug}"
        rec = {
            "season": int(yr), "week": int(wk), "game_slug": slug,
            "game_url": game_url,
            "away_team": away_abbr or "", "home_team": home_abbr or "",
            "away_short": away_slug, "home_short": home_slug,
            "away_score": "", "home_score": "", "total": "", "margin": "",
            "status": "", "official_date_text": "", "day_of_week": "",
            "month": "", "day_of_month": "", "time_text": "", "network": "",
            "kickoff_utc": "", "neutral_site": "", "venue": "",
            "source_url": game_url,
            "source_url_schedule": item["source_url"],
            "raw_path": item["output"],
            "verified": True,
            "value_type": "OFFICIAL — transcribed from NFL.com schedule/game links",
            "unverified_fields": [],
        }
        fm = re.match(r"^(.+?)\s+(\d+),\s+(.+?)\s+(\d+),\s+FINAL,\s+(\w+),\s+(\w+)\s+(\d+)(?:st|nd|rd|th)?$", label)
        um = re.match(r"^(.+?)\s+at\s+(.+?),\s+(\w+),\s+(\w+)\s+(\d+)(?:st|nd|rd|th)?,\s+([\d:]+\s+[AP]M),\s+(.+)$", label)
        if fm:
            a_name, a_score, h_name, h_score, dow, mon, day = fm.groups()
            rec.update(
                status="final", away_short_text=a_name, home_short_text=h_name,
                away_score=int(a_score), home_score=int(h_score),
                total=int(a_score) + int(h_score), margin=int(h_score) - int(a_score),
                day_of_week=dow, month=mon, day_of_month=day,
                official_date_text=f"{dow}, {mon} {day}",
            )
        elif um:
            a_name, h_name, dow, mon, day, tm, net = um.groups()
            rec.update(
                status="scheduled", away_short_text=a_name, home_short_text=h_name,
                day_of_week=dow, month=mon, day_of_month=day, time_text=tm, network=net,
                official_date_text=f"{dow}, {mon} {day}, {tm}, {net}",
                unverified_fields=["away_score", "home_score", "total", "margin"],
            )
        else:
            rec["verified"] = False
            rec["unverified_fields"].append("score_or_matchup")
            report["mismatches"].append({"check": "schedule_link_parse", "detail": label})
        key = (int(yr), int(wk), away_abbr, home_abbr)
        ev = espn_events.get(key)
        if ev:
            rec["kickoff_utc"] = ev["date"] or ""
            rec["neutral_site"] = "" if ev["neutral_site"] is None else str(ev["neutral_site"]).lower()
            rec["venue"] = ev["venue"] or ""
            rec["partner_source_url"] = ev["source_url"]
            rec["partner_event_id"] = ev["event_id"] or ""
            if rec["status"] == "final" and ev["completed"]:
                ok = (str(rec["away_score"]) == str(ev["away_score"]) and str(rec["home_score"]) == str(ev["home_score"]))
                rec["cross_check"] = "MATCH" if ok else "MISMATCH"
                if not ok:
                    rec["verified"] = False
                    report["mismatches"].append({"check": "espn_score_cross_check", "detail": f"{slug}: NFL {rec['away_score']}-{rec['home_score']} vs ESPN {ev['away_score']}-{ev['home_score']}"})
            else:
                rec["cross_check"] = "SCHEDULED" if rec["status"] == "scheduled" else "STATUS_MISMATCH"
        else:
            rec["cross_check"] = "NO_PARTNER_EVENT"
            rec["unverified_fields"].append("kickoff_utc")
        rows.append(rec)
    return rows


games_2025, games_2026 = [], []
for year, max_week, out in ((2025, 18, games_2025), (2026, 9, games_2026)):
    for week in range(1, max_week + 1):
        out.extend(parse_schedule(year, week))
games_2025.sort(key=lambda r: (r["week"], r["game_slug"]))
games_2026.sort(key=lambda r: (r["week"], r["game_slug"]))


def recompute_standings(games, season):
    stats = defaultdict(lambda: {"W": 0, "L": 0, "T": 0, "PF": 0, "PA": 0, "HOME_W": 0, "HOME_L": 0, "HOME_T": 0, "ROAD_W": 0, "ROAD_L": 0, "ROAD_T": 0})
    for g in games:
        if g["season"] != season or g["status"] != "final" or not g["away_team"] or not g["home_team"]:
            continue
        a, h = g["away_team"], g["home_team"]
        sa, sh = int(g["away_score"]), int(g["home_score"])
        for t, f, ag in ((a, sa, sh), (h, sh, sa)):
            stats[t]["PF"] += f
            stats[t]["PA"] += ag
        side = "HOME" if t == h else "ROAD"  # last t is home; handled explicitly below
        # Explicit W/L/T and home/road records.
        if sa > sh:
            winner, loser = a, h
        elif sh > sa:
            winner, loser = h, a
        else:
            winner = loser = None
        if winner:
            stats[winner]["W"] += 1
            stats[loser]["L"] += 1
            for t, wl in ((winner, "W"), (loser, "L")):
                stats[t][("HOME" if t == h else "ROAD") + "_" + wl] += 1
        else:
            for t in (a, h):
                stats[t]["T"] += 1
                stats[t][("HOME" if t == h else "ROAD") + "_T"] += 1
    return stats


recomputed_2026 = recompute_standings(games_2026, 2026)
standings_by_abbr = {r["abbr"]: r for r in standings_2026}
mismatches = []
for abbr, srow in standings_by_abbr.items():
    c = recomputed_2026.get(abbr, {})
    for key in ("W", "L", "T", "PF", "PA", "NET_PTS"):
        if key == "NET_PTS":
            derived = c.get("PF", 0) - c.get("PA", 0)
        else:
            derived = c.get(key, 0)
        if str(srow[key]) != str(derived):
            mismatches.append(f"{abbr} {key}: official {srow[key]} vs recomputed {derived}")
check("standings_2026_recompute", not mismatches, f"{len(standings_by_abbr)} teams × 6 cells; {len(mismatches)} mismatches", [manifest_item("standings", "/standings/league/2026/reg")["source_url"], "https://www.nfl.com/schedules/2026/by-week/week-8"])
report["counts"]["standings_recompute_mismatches"] = len(mismatches)

# Full official game counts.
final_2025 = [g for g in games_2025 if g["status"] == "final"]
final_2026 = [g for g in games_2026 if g["status"] == "final"]
scheduled_2026 = [g for g in games_2026 if g["status"] == "scheduled"]
report["counts"].update({
    "official_sources": MANIFEST["ok_count"],
    "official_sources_failed": MANIFEST["fail_count"],
    "standings_2025_rows": len(standings_2025),
    "standings_2026_rows": len(standings_2026),
    "games_2025_rows": len(games_2025),
    "games_2025_final": len(final_2025),
    "games_2026_rows": len(games_2026),
    "games_2026_final": len(final_2026),
    "games_2026_scheduled": len(scheduled_2026),
    "espn_cross_check_match": sum(1 for g in games_2025 + games_2026 if g.get("cross_check") == "MATCH"),
    "espn_cross_check_mismatch": sum(1 for g in games_2025 + games_2026 if g.get("cross_check") == "MISMATCH"),
    "espn_cross_check_no_event": sum(1 for g in games_2025 + games_2026 if g.get("cross_check") == "NO_PARTNER_EVENT"),
})
check("espn_score_cross_check_all", report["counts"]["espn_cross_check_mismatch"] == 0, f"{report['counts']['espn_cross_check_match']} final scores matched ESPN partner JSON; {report['counts']['espn_cross_check_mismatch']} mismatches", ["https://www.nfl.com/schedules/2026/by-week/week-8", "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=2026&limit=500"])


def parse_stat_table(item, category, kind):
    s = read_gz(item["output"])
    headers = [text(x) for x in re.findall(r"<th[^>]*>(.*?)</th>", s, re.S | re.I)]
    rows = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", s, re.S | re.I):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S | re.I)
        if len(cells) < 2 or len(cells) != len(headers):
            continue
        first = cells[0]
        vals = [text(c) for c in cells[1:]]
        rec = {
            "season": 2026, "category": category, "headers": headers[1:],
            "values": vals,
            "source_url_table": item["source_url"],
            "raw_path": item["output"],
            "verified": True,
            "value_type": "OFFICIAL — transcribed from NFL.com stats table",
        }
        if kind == "team":
            am = re.search(r"logos/([A-Z0-9]{2,4})", first)
            if not am:
                continue
            rec.update(
                abbr=am.group(1), team=abbr_to_team.get(am.group(1), ""),
                team_short=text(first), source_url=abbr_to_team_url.get(am.group(1), item["source_url"]),
            )
        else:
            pm = re.search(r'href="([^"]*/players/[^"]+)"[^>]*>(.*?)</a>', first, re.S | re.I)
            if not pm:
                continue
            rec.update(
                player=text(pm.group(2)), player_url=absolute(pm.group(1)),
                team="", team_status="UNVERIFIED — official stats table does not publish team",
                source_url=absolute(pm.group(1)),
                unverified_fields=["team"],
            )
        rows.append(rec)
    return rows


team_stats = []
for cat in ("passing", "rushing", "receiving", "scoring", "downs"):
    item = manifest_item("team_stats", f"/offense/{cat}/2026/reg/all")
    rows = parse_stat_table(item, cat, "team")
    check(f"team_stats_{cat}_rows", len(rows) == 32, f"{len(rows)} official team rows for {cat}", [item["source_url"]])
    team_stats.extend(rows)

player_stats = []
player_specs = [
    ("passing", "/category/passing/2026/reg/all/passingyards/desc"),
    ("rushing", "/category/rushing/2026/reg/all/rushingyards/desc"),
    ("receiving", "/category/receiving/2026/reg/all/receivingreceptions/desc"),
]
for cat, needle in player_specs:
    item = manifest_item("player_stats", needle)
    rows = parse_stat_table(item, cat, "player")
    check(f"player_stats_{cat}_rows", len(rows) >= 20, f"{len(rows)} official player rows for {cat}", [item["source_url"]])
    player_stats.extend(rows)


class InjuryParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.heading = ""
        self._heading_parts = []
        self._in_heading = False
        self.current_team = ""
        self._in_table = False
        self._in_row = False
        self._in_cell = False
        self._cell_parts = []
        self._cell_href = ""
        self._row = []
        self.rows = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("h2", "h3", "h4"):
            self._in_heading = True
            self._heading_parts = []
        if tag == "table":
            self._in_table = True
            h = self.heading.strip()
            slug = re.sub(r"[^a-z0-9]+", "-", h.lower()).strip("-")
            self.current_team = short_to_abbr.get(slug, "")
        if tag == "tr" and self._in_table:
            self._in_row = True
            self._row = []
        if tag in ("td", "th") and self._in_row:
            self._in_cell = True
            self._cell_parts = []
            self._cell_href = ""
        if tag == "a" and self._in_cell and a.get("href"):
            self._cell_href = absolute(a["href"])

    def handle_data(self, data):
        if self._in_heading:
            self._heading_parts.append(data)
        if self._in_cell:
            self._cell_parts.append(data)

    def handle_endtag(self, tag):
        if tag in ("h2", "h3", "h4") and self._in_heading:
            self.heading = " ".join(html.unescape(" ".join(self._heading_parts)).split())
            self._in_heading = False
        if tag in ("td", "th") and self._in_cell:
            self._row.append({"text": " ".join(html.unescape(" ".join(self._cell_parts)).split()), "href": self._cell_href})
            self._in_cell = False
        if tag == "tr" and self._in_row:
            if len(self._row) >= 5 and self._row[0]["text"].lower() != "player":
                self.rows.append({"team_abbr": self.current_team, "heading": self.heading, "cells": self._row[:5]})
            self._in_row = False
        if tag == "table" and self._in_table:
            self._in_table = False


injury_item = manifest_item("injuries", "/injuries/")
ip = InjuryParser()
ip.feed(read_gz(injury_item["output"]))
injuries = []
for r in ip.rows:
    c = r["cells"]
    game_status = c[4]["text"]
    if not game_status:  # only official rows with a published game status
        continue
    injuries.append({
        "season": 2026, "week": 8,
        "team_abbr": r["team_abbr"],
        "team": abbr_to_team.get(r["team_abbr"], ""),
        "player": c[0]["text"], "player_url": c[0]["href"] or injury_item["source_url"],
        "position": c[1]["text"], "injury": c[2]["text"],
        "practice_status": c[3]["text"], "game_status": game_status,
        "source_url": injury_item["source_url"],
        "source_url_player": c[0]["href"] or injury_item["source_url"],
        "raw_path": injury_item["output"],
        "verified": True,
        "value_type": "OFFICIAL — transcribed from NFL.com week-8 injury report",
    })
check("injury_rows_with_game_status", len(injuries) > 0, f"{len(injuries)} official injury rows with Out/Questionable/game status", [injury_item["source_url"]])


def parse_game_centers():
    checks = []
    by_slug = {g["game_slug"]: g for g in games_2025 + games_2026}
    for item in MANIFEST["items"]:
        if item["kind"] != "game_center":
            continue
        slug = item["source_url"].rstrip("/").split("/")[-1]
        u = read_gz(item["output"]).replace('\\"', '"')
        found = None
        for m in re.finditer(r'"gamePhaseOrYear":"(?:Final|\d{4})"', u):
            seg = u[max(0, m.start() - 2500): m.end() + 1500]
            scores = re.findall(r'"recordOrScoreText":"(\d+)"', seg)
            abbrs = re.findall(r'"abbreviation":"([A-Z]{2,4})"', seg)
            times = re.findall(r'"gameTime":"([^"]+)"', seg)
            if len(scores) >= 2 and len(abbrs) >= 2:
                found = (int(scores[0]), int(scores[1]), abbrs[0], abbrs[1], times[0] if times else "")
                break
        g = by_slug.get(slug)
        rec = {
            "game_slug": slug, "source_url": item["source_url"],
            "away_score": found[0] if found else "",
            "home_score": found[1] if found else "",
            "away_abbr": found[2] if found else "",
            "home_abbr": found[3] if found else "",
            "game_time_utc": found[4] if found else "",
            "schedule_away_score": g["away_score"] if g else "",
            "schedule_home_score": g["home_score"] if g else "",
            "cross_check": "",
            "verified": False,
        }
        if found and g and g["status"] == "final":
            ok = (found[0] == int(g["away_score"]) and found[1] == int(g["home_score"]) and found[2] == g["away_team"] and found[3] == g["home_team"])
            rec["cross_check"] = "MATCH" if ok else "MISMATCH"
            rec["verified"] = ok
        checks.append(rec)
    return checks


game_center_checks = parse_game_centers()
gc_match = sum(1 for c in game_center_checks if c["cross_check"] == "MATCH")
check("game_center_sample", gc_match == len(game_center_checks), f"{gc_match}/{len(game_center_checks)} official game-center final scores match official schedule link text", [c["source_url"] for c in game_center_checks[:3]])

# Source register. Titles are read from the saved raw HTML, not invented.
sources = []
for i in MANIFEST["items"]:
    title = ""
    if i["output"] and i["output"].endswith(".html.gz"):
        m = re.search(r"<title[^>]*>(.*?)</title>", read_gz(i["output"]), re.S | re.I)
        if m:
            title = text(m.group(1))
    rec = {
        "source_id": i["source_id"],
        "source_url": i["source_url"],
        "official": bool(i["official"]),
        "kind": i["kind"],
        "http_status": i["http_status"],
        "sha256": i["sha256"],
        "bytes": i["bytes"],
        "raw_path": i["output"],
        "fetched_at": i["fetched_at"],
        "title": title,
        "note": i["note"],
        "verified_fact": "",
        "verified_fact_status": "BLANK — no fact transcribed into this source register row",
    }
    if not i["official"]:
        rec["official_link"] = "https://www.nfl.com/schedules/"
        rec["unverified_fields"] = ["verified_fact"]
    sources.append(rec)
check("source_manifest_all_200", MANIFEST["fail_count"] == 0, f"{MANIFEST['ok_count']}/{len(MANIFEST['items'])} sources returned HTTP 200", ["https://www.nfl.com/standings/league/2026/reg"])

# Initial flags; model/site scripts append more.
add_flag("IR-NFL-01", "Repository is NBA-focused and has multiple NFL specification dashboards", "The brief says NFL lines; the inherited repo is largely NBA research. Prior sessions published nfl/**, nfl-research/**, nfl-lab/**, nfl-quant/** and nfl-study/** claims. This session uses the unclaimed nfl-origin/** namespace.", ["https://github.com/sassnarep3-star/Own4", "https://www.nfl.com/"])
add_flag("IR-NFL-02", "COORDINATION.md contains literal merge-conflict markers", "Lines inherited from earlier sessions contain unresolved <<<<<<< / ======= / >>>>>>> markers. They are preserved verbatim and flagged, not silently edited.", ["https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md"])
add_flag("IR-NFL-03", "README.md contains unresolved merge-conflict markers", "The inherited root README includes an unresolved conflict section and describes NBA research. It is outside this session's scope and is not edited.", ["https://github.com/sassnarep3-star/Own4/blob/main/README.md"])
add_flag("IR-NFL-04", "No official NFL betting-line or price archive", "NFL.com publishes schedules, standings, stats and integrity policy but no official odds/closing-line archive. All market-price cells are blank.", ["https://www.nfl.com/news/nfl-draftkings-fanduel-fanatics-sports-betting-partners", "https://www.nfl.com/schedules/"], ["market_moneyline", "market_spread", "market_total", "closing_line_value", "roi"])
add_flag("IR-NFL-05", "Week 9 injury report not yet published", "The official injuries portal still showed week 8 at retrieval. No injury adjustment is applied to upcoming lines.", ["https://www.nfl.com/injuries/"], ["week9_injury_status"])
add_flag("IR-NFL-06", "Listed home team may not be true home team at neutral sites", "Official game URLs use an 'away-at-home' listing order. ESPN partner JSON neutralSite flags are used only as a cross-check; no home-field advantage is applied where the partner marks a game neutral.", ["https://www.nfl.com/schedules/2026/by-week/week-1", "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=2026&limit=500"], ["official_home_designation"])
add_flag("IR-NFL-07", "Official schedule body hides scores but game links expose them", "Week-18 and some scoreboard tiles show 'Hidden Score' in the rendered body; the accessible official game-link text contains the final score. Parsed rows use the official link text.", ["https://www.nfl.com/schedules/2025/by-week/week-18", "https://www.nfl.com/schedules/2026/by-week/week-8"])
add_flag("IR-NFL-08", "Kickoff ISO timestamps are partner-sourced", "NFL.com link text gives weekday/month/day but not a full ISO timestamp; ESPN partner JSON supplies kickoff UTC for rest calculations. It is labelled partner-sourced, not an NFL publication.", ["https://www.nfl.com/schedules/2026/by-week/week-9", "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=2026&limit=500"], ["kickoff_utc"])
add_flag("IR-NFL-09", "Player stats table does not publish team affiliation", "NFL.com player category tables list player and aggregate values but no team column; team cells are blank.", ["https://www.nfl.com/stats/player-stats/category/passing/2026/reg/all/passingyards/desc"], ["team"])
add_flag("IR-NFL-10", "No funded leaderboard reward pool is defined by an official source", "The brief describes a leaderboard competition with rewards, but no official NFL or repository source defines a prize pool or reward points. Reward fields are blank.", ["https://github.com/sassnarep3-star/Own4", "https://www.nfl.com/news/nfl-draftkings-fanduel-fanatics-sports-betting-partners"], ["reward_points", "prize_pool"])
add_flag("IR-NFL-11", "Derived model outputs are not official NFL publications", "Elo ratings, fair lines, correlations, Brier scores and leaderboard scores are reproducible computations from official inputs; they are not published NFL values.", ["https://www.nfl.com/standings/league/2026/reg", "https://www.nfl.com/schedules/2026/by-week/week-8", "https://www.itl.nist.gov/div898/handbook/prc/section2/prc24.htm"], ["elo_rating", "fair_moneyline", "fair_spread", "fair_total", "correlation", "brier", "skill_score"])
add_flag("IR-NFL-12", "2026 out-of-sample holdout is below 300 games", f"Only {len(final_2026)} 2026 regular-season games were final at retrieval; the pre-registered G1 gate requires at least 300 holdout observations.", ["https://www.nfl.com/standings/league/2026/reg", "https://www.nfl.com/schedules/2026/by-week/week-8"], ["validated_strategy_count"])
add_flag("IR-NFL-13", "Root navigation does not link nfl-origin/", "Root index.html already links the earlier nfl/ module. A root link to this section is logged as a shared-output request rather than editing another session's navigation.", ["https://github.com/sassnarep3-star/Own4/blob/main/index.html", "https://sassnarep3-star.github.io/Own4/nfl/"])
add_flag("IR-NFL-14", "2025 ESPN calendar file mixes seasons", "The ESPN dates=2025 response includes 2024 week 18 and 2024 postseason events; parsing filters on season.year and season.type==2.", ["https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=2025&limit=500", "https://www.nfl.com/standings/league/2025/reg"])
add_flag("IR-NFL-15", "Official standings heading contains template placeholders", "The 2026 NFL.com standings page renders '$year$ NFL $displayname$ Standings' in its heading. The table values are used; the heading artifact is not.", ["https://www.nfl.com/standings/league/2026/reg"])
add_flag("IR-NFL-16", "One week-8 game was still scheduled at retrieval", "Chicago at Seattle (2026 week 8) had not kicked off; it is excluded from completed-game verification and included in the upcoming own-line slate.", ["https://www.nfl.com/games/bears-at-seahawks-2026-reg-8", "https://www.nfl.com/schedules/2026/by-week/week-8"], ["bears_seahawks_final_score"])
add_flag("IR-NFL-17", "Player-level game logs and prop prices are unavailable from official sources", "Official NFL.com publishes season player tables, not a downloadable official game-log/prop-price archive. Player-prop combo correlations remain blank.", ["https://www.nfl.com/stats/player-stats/", "https://www.nfl.com/news/nfl-draftkings-fanduel-fanatics-sports-betting-partners"], ["player_prop_correlation", "prop_combo_price"])

# Persist structured outputs.
write_json("standings_2025.json", standings_2025)
write_json("standings_2026.json", standings_2026)
write_json("games_2025.json", games_2025)
write_json("games_2026.json", games_2026)
write_json("upcoming.json", scheduled_2026)
write_json("team_stats_2026.json", team_stats)
write_json("player_stats_2026.json", player_stats)
write_json("injuries_2026_week8.json", injuries)
write_json("game_center_checks.json", game_center_checks)
write_json("sources.json", sources)
write_json("flags.json", flags)
write_json("parse_report.json", report)

write_csv("standings_2025.csv", standings_2025)
write_csv("standings_2026.csv", standings_2026)
write_csv("games_2025.csv", games_2025)
write_csv("games_2026.csv", games_2026)
write_csv("upcoming.csv", scheduled_2026)
write_csv("team_stats_2026.csv", team_stats)
write_csv("player_stats_2026.csv", player_stats)
write_csv("injuries_2026_week8.csv", injuries)
write_csv("game_center_checks.csv", game_center_checks)
write_csv("sources.csv", sources)
write_csv("flags.csv", flags)

print(json.dumps(report["counts"], indent=2))
print("checks:", Counter(c["result"] for c in report["checks"]))
print("flags:", len(flags))
if report["mismatches"]:
    print("mismatches sample:", report["mismatches"][:5])
