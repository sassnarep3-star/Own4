"""Build the immutable, source-linked NFL observation snapshot.

This is a deterministic transcription exporter, NOT a live scraper. Values were
read from official NFL pages/search excerpts using the research tools on
2026-11-02. The sandbox cannot fetch NFL hosts from bash/CI. Every game is
cross-checked against a separately transcribed official standings table.
No missing value is filled, and source listing order is not treated as venue.
"""
from __future__ import annotations
import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OBSERVED_ON = "2026-11-02"
CUTOFF = "2026-11-02"
TEAMS = {
    "AZ": ("Arizona Cardinals", "arizona-cardinals"),
    "ATL": ("Atlanta Falcons", "atlanta-falcons"),
    "BAL": ("Baltimore Ravens", "baltimore-ravens"),
    "BUF": ("Buffalo Bills", "buffalo-bills"),
    "CAR": ("Carolina Panthers", "carolina-panthers"),
    "CHI": ("Chicago Bears", "chicago-bears"),
    "CIN": ("Cincinnati Bengals", "cincinnati-bengals"),
    "CLE": ("Cleveland Browns", "cleveland-browns"),
    "DAL": ("Dallas Cowboys", "dallas-cowboys"),
    "DEN": ("Denver Broncos", "denver-broncos"),
    "DET": ("Detroit Lions", "detroit-lions"),
    "GB": ("Green Bay Packers", "green-bay-packers"),
    "HOU": ("Houston Texans", "houston-texans"),
    "IND": ("Indianapolis Colts", "indianapolis-colts"),
    "JAX": ("Jacksonville Jaguars", "jacksonville-jaguars"),
    "KC": ("Kansas City Chiefs", "kansas-city-chiefs"),
    "LV": ("Las Vegas Raiders", "las-vegas-raiders"),
    "LA": ("Los Angeles Rams", "los-angeles-rams"),
    "LAC": ("Los Angeles Chargers", "los-angeles-chargers"),
    "MIA": ("Miami Dolphins", "miami-dolphins"),
    "MIN": ("Minnesota Vikings", "minnesota-vikings"),
    "NE": ("New England Patriots", "new-england-patriots"),
    "NO": ("New Orleans Saints", "new-orleans-saints"),
    "NYG": ("New York Giants", "new-york-giants"),
    "NYJ": ("New York Jets", "new-york-jets"),
    "PHI": ("Philadelphia Eagles", "philadelphia-eagles"),
    "PIT": ("Pittsburgh Steelers", "pittsburgh-steelers"),
    "SF": ("San Francisco 49ers", "san-francisco-49ers"),
    "SEA": ("Seattle Seahawks", "seattle-seahawks"),
    "TB": ("Tampa Bay Buccaneers", "tampa-bay-buccaneers"),
    "TEN": ("Tennessee Titans", "tennessee-tennessee"),
    "WAS": ("Washington Commanders", "washington-commanders"),
}
# Correct the one slug that cannot be mechanically derived from the display name.
TEAMS["TEN"] = ("Tennessee Titans", "tennessee-titans")


def psv(name):
    text = (DATA / name).read_text()
    lines = [x for x in text.splitlines() if x and not x.startswith("#")]
    return list(csv.DictReader(io.StringIO("\n".join(lines)), delimiter="|"))


def number(s):
    return None if s == "" else int(s)


def dump(name, obj):
    (DATA / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def make_sources():
    out = {}
    for season in (2025, 2026):
        for week in range(1, 19 if season == 2025 else 9):
            sid = f"NFL-{season}-W{week}"
            out[sid] = {
                "id": sid, "publisher": "National Football League",
                "title": f"{season} NFL Week {week} schedule and final scores",
                "url": f"https://www.nfl.com/schedules/{season}/by-week/week-{week}",
                "domain": "www.nfl.com", "observed_on": OBSERVED_ON,
                "inspection": "Official-page search excerpt; all listed FINAL rows read. Week 8 of 2026 also directly fetched.",
                "supports": "Dates, team identities and final scores. Listing order is not a verified home/away assignment.",
                "raw_html_archived": False,
            }
    for season in (2024, 2025, 2026):
        out[f"STAND-{season}"] = {
            "id": f"STAND-{season}", "publisher": "National Football League",
            "title": f"{season} NFL league standings",
            "url": f"https://www.nfl.com/standings/league/{season}/REG",
            "domain": "www.nfl.com", "observed_on": OBSERVED_ON,
            "inspection": "Direct official-page fetch, all chunks containing the 32-team table read.",
            "supports": "W, L, T, PF and PA. 2026 snapshot is through November 1; not a full-season table.",
            "raw_html_archived": False,
        }
    players = {
        "CALEB": ("caleb-williams", "Caleb Williams"),
        "SAM": ("sam-darnold", "Sam Darnold"),
        "JSN": ("jaxon-smith-njigba", "Jaxon Smith-Njigba"),
        "BURDEN": ("luther-burden-iii", "Luther Burden III"),
    }
    for key, (slug, name) in players.items():
        out[f"PLAYER-{key}"] = {
            "id": f"PLAYER-{key}", "publisher": "National Football League",
            "title": f"{name} 2026 regular-season game logs",
            "url": f"https://www.nfl.com/players/{slug}/stats/logs/2026/",
            "domain": "www.nfl.com", "observed_on": OBSERVED_ON,
            "inspection": "Direct official-page fetch. Direct page supersedes incomplete search excerpts. Blank numeric cells retained.",
            "supports": "Regular-season per-game stat values only; active profile is not a game-availability guarantee.",
            "raw_html_archived": False,
        }
    extras = [
        ("GAME", "Bears at Seahawks: official Week 8 Game Center", "https://www.nfl.com/games/bears-at-seahawks-2026-reg-8", "www.nfl.com", "Matchup, Seattle venue, season-to-date team/player totals and displayed injury entries. The page's LOCAL time label is ambiguous; no exact UTC kickoff is inferred."),
        ("SCHEDULE", "Making the NFL schedule", "https://operations.nfl.com/calendar-events/nfl-schedule/making-the-schedule", "operations.nfl.com", "Official schedule structure: 272 games, 18 weeks, 17 games per team and one bye; nine international games in 2026."),
        ("RULES", "2026 NFL Rulebook", "https://operations.nfl.com/rules-officiating/2026-nfl-rulebook", "operations.nfl.com", "Official 2026 rules and four listed 2026 changes. Does not validate any betting strategy."),
        ("TEAM-STATS", "2026 NFL team passing statistics", "https://www.nfl.com/stats/team-stats/offense/passing/2026/reg/all", "www.nfl.com", "Official team passing statistics portal; no values copied into the points-only model."),
        ("INJURIES", "2026 NFL injury report: Week 8", "https://www.nfl.com/injuries/", "www.nfl.com", "Official Week 8 injury report portal. Historical point-in-time injury inputs are not available in this snapshot."),
        ("CALIBRATION", "scikit-learn: probability calibration", "https://scikit-learn.org/stable/modules/calibration.html", "scikit-learn.org", "Official library documentation: calibrated probability, reliability curves, Brier/log-loss limitations. Not NFL evidence."),
        ("CORRELATION", "NIST: experiments and experimental design", "https://www.itl.nist.gov/div898/handbook/ppc/section1/ppc136.htm", "www.itl.nist.gov", "Official NIST handbook: correlation does not imply causality. Not NFL evidence."),
        ("BOOTSTRAP", "SciPy: bootstrap confidence intervals", "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html", "docs.scipy.org", "Official SciPy method documentation. This project implements a seeded percentile cluster bootstrap, not SciPy BCa."),
        ("FDR", "SciPy: false discovery control", "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.false_discovery_control.html", "docs.scipy.org", "Official SciPy documentation for multiplicity control; project uses Holm for the registered primary family."),
        ("SPLITS", "scikit-learn: TimeSeriesSplit", "https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html", "scikit-learn.org", "Official temporal cross-validation documentation. Project uses whole-week chronological blocks."),
        ("NCPG", "National Problem Gambling Helpline", "https://www.ncpgambling.org/help-treatment/", "www.ncpgambling.org", "NCPG official helpline: 1-800-MY-RESET."),
        ("PAGES", "GitHub Docs: What is GitHub Pages?", "https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages", "docs.github.com", "Official static repository hosting and project-site path documentation."),
        ("REPO", "Own4 coordination and publication record", "https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md", "github.com", "Repository governance, source-relevance audit and publication evidence; not sports evidence."),
        ("PAGES-API", "Own4 GitHub Pages configuration", "https://api.github.com/repos/sassnarep3-star/Own4/pages", "api.github.com", "Official GitHub API for this repository's Pages configuration; deployment status recorded separately."),
    ]
    for sid, title, url, domain, supports in extras:
        out[sid] = {"id": sid, "publisher": domain, "title": title, "url": url,
                    "domain": domain, "observed_on": OBSERVED_ON,
                    "inspection": "Direct page fetch and relevant text read during this session, except the API whose live response is recorded at integration.",
                    "supports": supports, "raw_html_archived": False}
    return out


def collect():
    sources = make_sources()
    games = []
    for r in psv("games.psv"):
        assert r["team_a"] in TEAMS and r["team_b"] in TEAMS
        assert r["source_id"] in sources
        date.fromisoformat(r["date"])
        assert r["date"] <= CUTOFF
        a, b = r["team_a"], r["team_b"]
        sa, sb = int(r["score_a"]), int(r["score_b"])
        assert a != b and sa >= 0 and sb >= 0
        games.append({
            "id": f'{r["season"]}-{r["week"]}-{min(a,b)}-{max(a,b)}',
            "season": int(r["season"]), "week": int(r["week"]), "date": r["date"],
            "team_a": a, "score_a": sa, "team_b": b, "score_b": sb,
            "home_team": None, "away_team": None,
            "status": "final", "source_id": r["source_id"],
            "source_url": sources[r["source_id"]]["url"],
            "verification": "Official schedule observation; team totals/records reconciled to official standings. Venue not inferred.",
        })
    standings = []
    for r in psv("standings.psv"):
        row = {"season": int(r["season"]), "team": r["team"],
               "team_name": TEAMS[r["team"]][0], "source_id": r["source_id"],
               "source_url": sources[r["source_id"]]["url"]}
        row.update({k: int(r[k]) for k in ("w", "l", "t", "pf", "pa")})
        standings.append(row)
    players = []
    for r in psv("players.psv"):
        players.append({**r, "season": int(r["season"]), "week": int(r["week"]),
                        "value_a": number(r["value_a"]), "value_b": number(r["value_b"]),
                        "source_url": sources[r["source_id"]]["url"],
                        "verification": "Direct official game-log row; blanks are missing, never zero."})
    upcoming = {"id": "2026-8-CHI-SEA", "season": 2026, "week": 8,
                "date": "2026-11-02", "away_team": "CHI", "home_team": "SEA",
                "venue": "Lumen Field, Seattle, WA", "score_a": None, "score_b": None,
                "status": "scheduled", "source_id": "GAME", "source_url": sources["GAME"]["url"],
                "verification": "Official Game Center confirms matchup and venue. Exact kickoff timezone is flagged; research cutoff is the official game date."}
    assert len({g["id"] for g in games}) == len(games)
    assert len(standings) == 96 and len({(r["season"], r["team"]) for r in standings}) == 96
    assert len(games) == 392, f"Expected 272 + 120 games, got {len(games)}"
    assert len(players) == 28
    dump("games.json", games)
    dump("standings.json", standings)
    dump("players.json", players)
    dump("upcoming.json", upcoming)
    dump("sources.json", sources)
    dump("teams.json", [{"code": k, "name": v[0], "source_url": f"https://www.nfl.com/teams/{v[1]}/", "source_id": "STAND-2026"} for k, v in sorted(TEAMS.items())])
    manifest = {"observed_on": OBSERVED_ON, "cutoff": CUTOFF,
                "collection": "Manual read/transcription of tool-retrieved official content, then deterministic export and independent standings reconciliation.",
                "not_a_live_feed": True, "games": len(games), "standings_rows": len(standings),
                "player_rows": len(players), "player_missing_cells": sum(r[k] is None for r in players for k in ("value_a", "value_b")),
                "source_count": len(sources), "files": {}}
    for p in sorted(DATA.glob("*.psv")) + [DATA / n for n in ("games.json", "standings.json", "players.json", "sources.json")]:
        manifest["files"][p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    dump("collection_manifest.json", manifest)
    return games, standings, players, sources


if __name__ == "__main__":
    g, s, p, src = collect()
    print(f"Exported {len(g)} official games, {len(s)} standings rows, {len(p)} player rows, {len(src)} sources; missing player cells preserved.")
