"""Validate the small, primary-source-inscribed evidence set and create a receipt.

This does NOT scrape NBA.com or claim to re-fetch source truth in CI. The source
inspection was performed with the page-fetch tool on the recorded date. CI checks
provenance, schema, arithmetic and reproducibility against the committed extracts.
NBA FAQ says its stats are not available for general personal/academic download.
"""
from __future__ import annotations
import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
ALLOWED = ("nba.com", "official.nba.com", "help.bet365.com", "support.fanduel.com",
           "nist.gov", "scikit-learn.org", "nber.org", "ssrn.com")


def official(url):
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in ALLOWED)


def rows(name):
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    checks = []
    def check(name, condition, detail):
        checks.append({"name": name, "pass": bool(condition), "detail": detail})
    games, players, totals = rows("games.csv"), rows("players.csv"), rows("team_totals.csv")
    sources = json.loads((DATA / "sources.json").read_text())
    check("62 unique official game records", len(games) == 62 and len({g['game_id'] for g in games}) == 62, len(games))
    check("38 unique participating-player records", len(players) == 38 and len({(p['game_id'],p['player_id']) for p in players}) == 38, len(players))
    for label, dataset in (("games", games), ("players", players), ("team totals", totals), ("sources", sources)):
        check(label + " source domains", all(official(r.get('source_url', r.get('url', ''))) for r in dataset), len(dataset))
    check("game dates and IDs", all(g['source_url'] == 'https://www.nba.com/games?date=' + g['date'] and re.fullmatch(r'002240\d{4}', g['game_id']) for g in games), "Exact per-date official scoreboard URL")
    check("only completed official games", all(g['status'].startswith('Final') and int(g['score1']) != int(g['score2']) for g in games), "Final/OT retained; no future game results")
    expected_counts = {"2025-01-01":8,"2025-01-02":6,"2025-01-03":9,"2025-01-04":9,"2025-01-05":6,"2025-01-06":9,"2025-01-07":7,"2025-01-08":8}
    actual_counts = {d:sum(g['date'] == d for g in games) for d in expected_counts}
    check("complete inspected date samples", actual_counts == expected_counts, actual_counts)
    game_map = {g['game_id']:g for g in games}
    check("player game/date join", all(p['game_id'] in game_map and p['date'] == game_map[p['game_id']]['date'] for p in players), "No orphan player rows")
    sums = defaultdict(lambda:[0,0,0,0])
    for p in players:
        s = sums[(p['game_id'],p['team'])]
        for i,k in enumerate(('points','rebounds','assists')):s[i] += int(p[k])
        minutes, seconds = map(int,p['minutes'].split(':'))
        check(f"seconds range {p['player_id']}", 0 <= seconds < 60, p['minutes'])
        s[3] += 60 * minutes + seconds
    for t in totals:
        s = sums[(t['game_id'],t['team'])]
        check('player totals vs official ' + t['game_id'] + ' ' + t['team'], all(s[i] == int(t[k]) for i,k in enumerate(('points','rebounds','assists'))), s[:3])
        check('five player court positions ' + t['game_id'] + ' ' + t['team'], s[3] in (14400,14401), f"{s[3]} seconds; published per-player minutes retained")
    check("MIL one-second source irregularity disclosed", sums[('0022400465','MIL')][3] == 14401, "Sum is 240:01, not silently normalized to 240:00")
    manifest = {}
    for path in sorted(DATA.glob("*.csv")) + [DATA / 'sources.json', DATA / 'protocol.json']:
        manifest[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    report = {"checked_on":"2026-11-02", "external_verification":"Primary pages read by the agent via fetch_page; not a live CI fetch",
              "automated_checks":"Schema, source-domain policy, joins, completeness of inspected samples, arithmetic, hashes",
              "passed":sum(c['pass'] for c in checks), "total":len(checks), "checks":checks, "sha256":manifest}
    (DATA / 'evidence_receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f"Evidence checks: {report['passed']}/{report['total']} passed")
    if report['passed'] != report['total']:
        raise SystemExit(1)


if __name__ == '__main__':main()
