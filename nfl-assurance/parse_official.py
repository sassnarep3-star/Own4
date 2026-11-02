#!/usr/bin/env python3
"""Extract factual NFL fields from saved official pages. No imputation.

The NFL site embeds React Flight rows in self.__next_f.push([1,"..."]).
We decode those JSON strings, locate the schedule query whose queryKey matches
the requested season/week, and transcribe explicit fields only. Derived model
values are produced elsewhere and never written back into this factual table.
"""
from __future__ import annotations
import csv
import gzip
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'sources'
DATA = ROOT / 'data'


def flight_objects(html: str):
    decoder = json.JSONDecoder()
    chunks = []
    for match in re.finditer(r'self\.__next_f\.push\(', html):
        try:
            value, _ = decoder.raw_decode(html[match.end():])
            if isinstance(value, list) and len(value) > 1 and isinstance(value[1], str):
                chunks.append(value[1])
        except (ValueError, TypeError):
            continue
    objects = []
    for line in ''.join(chunks).splitlines():
        match = re.match(r'^([0-9a-f]+):(.*)$', line)
        if not match:
            continue
        try:
            objects.append(json.loads(match.group(2)))
        except ValueError:
            continue
    return objects


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def read_snapshot(key: str) -> str:
    return gzip.decompress((RAW / f'{key}.html.gz').read_bytes()).decode('utf-8')


def external(game, source):
    for item in game.get('externalIds') or []:
        if item.get('source') == source:
            return item.get('id')
    return None


def logo_code(team):
    logo = team.get('currentLogo') or ''
    match = re.search(r'/logos/([A-Z0-9]+)$', logo)
    return match.group(1) if match else None


def score_fields(summary_side):
    score = (summary_side or {}).get('score') or {}
    return {key: score.get(key) for key in ('q1', 'q2', 'q3', 'q4', 'ot', 'total')}


def parse_schedule(key: str, source_url: str, season: int, week: int):
    objects = flight_objects(read_snapshot(key))
    candidates = []
    for obj in objects:
        for node in walk(obj):
            query = node.get('queryKey')
            state = node.get('state')
            if not isinstance(query, list) or len(query) < 2 or not isinstance(query[1], dict):
                continue
            params = query[1]
            data = (state or {}).get('data') if isinstance(state, dict) else None
            if (str(params.get('season')) == str(season)
                    and str(params.get('week')) == str(week)
                    and params.get('seasonType') == 'REG'
                    and isinstance(data, list)
                    and all(isinstance(g, dict) and 'homeTeam' in g and 'awayTeam' in g for g in data)):
                candidates.append(data)
    if not candidates:
        raise ValueError(f'No official schedule query found in {key}')
    # Prefer the richer game-summary query over a broadcast-only query.
    games = max(candidates, key=lambda rows: sum('summary' in g for g in rows))
    rows, issues = [], []
    for game in games:
        summary = game.get('summary') or {}
        phase = summary.get('phase')
        final = phase in ('FINAL', 'FINAL_OVERTIME')
        home, away = game['homeTeam'], game['awayTeam']
        hs, as_ = score_fields(summary.get('homeTeam')), score_fields(summary.get('awayTeam'))
        slug = external(game, 'slug')
        row = {
            'game_id': game.get('id'), 'season': game.get('season'), 'week': game.get('week'),
            'date': game.get('date'), 'scheduled_time_utc': game.get('time'),
            'actual_start_utc': summary.get('startTime'), 'phase': phase, 'is_final': final,
            'home_team': logo_code(home), 'away_team': logo_code(away),
            'home_team_id': home.get('id'), 'away_team_id': away.get('id'),
            'home_team_name': home.get('fullName'), 'away_team_name': away.get('fullName'),
            'neutral_site': game.get('neutralSite'), 'venue': (game.get('venue') or {}).get('name'),
            'home_score': hs['total'] if final else None, 'away_score': as_['total'] if final else None,
            'home_q1': hs['q1'] if final else None, 'home_q2': hs['q2'] if final else None,
            'home_q3': hs['q3'] if final else None, 'home_q4': hs['q4'] if final else None,
            'home_ot': hs['ot'] if final else None,
            'away_q1': as_['q1'] if final else None, 'away_q2': as_['q2'] if final else None,
            'away_q3': as_['q3'] if final else None, 'away_q4': as_['q4'] if final else None,
            'away_ot': as_['ot'] if final else None,
            'weather_official': summary.get('weather'), 'gamebook_url': summary.get('gameBookUrl'),
            'gsis_id': external(game, 'gsis'), 'elias_id': external(game, 'elias'),
            'source_url': source_url,
            'game_url': f'https://www.nfl.com/games/{slug}' if slug else None,
            'verification': 'unverified',
        }
        checks = []
        if final:
            for side, scores in (('home', hs), ('away', as_)):
                parts = [scores[q] for q in ('q1', 'q2', 'q3', 'q4', 'ot')]
                if scores['total'] is None or any(p is None for p in parts):
                    checks.append(f'{side}: missing score component')
                elif sum(parts) != scores['total']:
                    checks.append(f'{side}: quarter sum {sum(parts)} != official total {scores["total"]}')
            if row['home_team'] is None or row['away_team'] is None:
                checks.append('missing official team logo code')
            if row['home_team'] == row['away_team']:
                checks.append('identical team codes')
        if not row['game_id'] or not row['source_url']:
            checks.append('missing identifier/source')
        if checks:
            issues.append({'game_id': row['game_id'], 'issues': checks, 'source_url': source_url})
            row['verification'] = 'flagged'
        else:
            row['verification'] = 'official-explicit; integrity checks passed' if final else 'official schedule; not final'
        rows.append(row)
    return rows, issues


def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text('')
        return
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    manifest = json.loads((RAW / 'manifest-schedules.json').read_text())
    all_rows, issues, seen = [], [], set()
    for item in manifest['items']:
        if item['http_status'] != 200:
            issues.append({'source_url': item['source_url'], 'issues': [f'HTTP {item["http_status"]}']})
            continue
        match = re.match(r'schedule-(\d{4})-(\d{2})', item['id'])
        season, week = int(match.group(1)), int(match.group(2))
        rows, problems = parse_schedule(item['id'], item['source_url'], season, week)
        for row in rows:
            if row['game_id'] in seen:
                issues.append({'game_id': row['game_id'], 'issues': ['duplicate game id']})
                continue
            seen.add(row['game_id'])
            all_rows.append(row)
        issues.extend(problems)
    all_rows.sort(key=lambda r: (r['season'], r['week'], r['scheduled_time_utc'] or '', r['game_id']))
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / 'games.json').write_text(json.dumps(all_rows, indent=2) + '\n')
    write_csv(DATA / 'games.csv', all_rows)
    finals = [r for r in all_rows if r['is_final'] and r['verification'].startswith('official-explicit')]
    report = {
        'source_pages': len(manifest['items']), 'pages_http_200': sum(i['http_status'] == 200 for i in manifest['items']),
        'games': len(all_rows), 'final_games': sum(r['is_final'] for r in all_rows),
        'verified_final_games': len(finals), 'upcoming_or_nonfinal': sum(not r['is_final'] for r in all_rows),
        'by_season': {str(y): {'games': sum(r['season'] == y for r in all_rows),
                               'final': sum(r['season'] == y and r['is_final'] for r in all_rows)} for y in (2024, 2025, 2026)},
        'issues': issues,
        'policy': 'Scores are explicit official fields, not inferred. Non-final scores are blank. Quarter-sum failures are flagged and excluded from modeling.',
    }
    (DATA / 'parse_report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'issues'}, indent=2))
    if issues:
        print(f'{len(issues)} source/integrity issues recorded')


if __name__ == '__main__':
    main()
