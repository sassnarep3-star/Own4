#!/usr/bin/env python3
"""Parse official NFL player category tables and game logs without imputation."""
from __future__ import annotations
import csv
import gzip
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'sources'
DATA = ROOT / 'data'

class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self.table = None
        self.row = None
        self.cell = None
        self.links = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'table':
            self.table = []
        elif tag == 'tr' and self.table is not None:
            self.row = []
            self.links = []
        elif tag in ('td', 'th') and self.row is not None:
            self.cell = []
        elif tag == 'a' and self.cell is not None and 'href' in a:
            self.links.append(a['href'])
    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)
    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.cell is not None:
            self.row.append((''.join(self.cell).strip(), list(self.links)))
            self.cell = None
            self.links = []
        elif tag == 'tr' and self.row is not None:
            self.table.append(self.row)
            self.row = None
        elif tag == 'table' and self.table is not None:
            self.tables.append(self.table)
            self.table = None

def read(key):
    return gzip.decompress((RAW / f'{key}.html.gz').read_bytes()).decode()

def num(text):
    text = text.strip()
    if text in ('', '--', '—'):
        return None
    try:
        return float(text) if '.' in text else int(text)
    except ValueError:
        return None

def category_rows(key):
    html = read(key)
    parser = TableParser(); parser.feed(html)
    table = max(parser.tables, key=len)
    headers = [c[0] for c in table[0]]
    rows = []
    for row in table[1:]:
        if not row:
            continue
        name, links = row[0]
        slug = None
        for href in links:
            m = re.match(r'/players/([^/]+)/?$', href)
            if m:
                slug = m.group(1); break
        values = [c[0] for c in row[1:]]
        rows.append({'name': name, 'slug': slug, 'values': values, 'headers': headers})
    return rows

def build_panel():
    manifest = json.loads((RAW / 'manifest-references.json').read_text())
    urls = {i['id']: i['source_url'] for i in manifest['items']}
    panel, seen = [], set()
    for key, category, count in [('receiving-leaders', 'receiving', 10), ('passing-leaders', 'passing', 5), ('rushing-leaders', 'rushing', 5)]:
        rows = category_rows(key)
        for rank, row in enumerate(rows[:count], start=1):
            if not row['slug']:
                continue
            if row['slug'] not in seen:
                seen.add(row['slug'])
                panel.append({'slug': row['slug'], 'name': row['name'], 'selection': f'{category} yards rank {rank}',
                              'category': category, 'source_url': urls[key]})
            else:
                for p in panel:
                    if p['slug'] == row['slug']:
                        p['selection'] += f'; {category} yards rank {rank}'
    # Official game-center skill leaders for the next scheduled game (explicit links).
    game_url = urls['upcoming-game']
    for slug, name, role in [
        ('caleb-williams', 'Caleb Williams', 'CHI passing leader'),
        ('dandre-swift', "D'Andre Swift", 'CHI rushing leader'),
        ('luther-burden-iii', 'Luther Burden III', 'CHI receiving leader'),
        ('sam-darnold', 'Sam Darnold', 'SEA passing leader'),
        ('emanuel-wilson', 'Emanuel Wilson', 'SEA rushing leader'),
        ('jaxon-smith-njigba', 'Jaxon Smith-Njigba', 'SEA receiving leader'),
    ]:
        if slug not in seen:
            seen.add(slug)
            panel.append({'slug': slug, 'name': name, 'selection': f'next-game official game-center {role}',
                          'category': 'passing' if 'passing' in role else 'rushing' if 'rushing' in role else 'receiving',
                          'source_url': game_url})
        else:
            for p in panel:
                if p['slug'] == slug:
                    p['selection'] += f'; next-game official game-center {role}'
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / 'player_panel.json').write_text(json.dumps(panel, indent=2) + '\n')
    print(f'panel: {len(panel)} players')
    return panel

def logs_table(html):
    # Isolate the Regular Season section, then its first table.
    m = re.search(r'<h3[^>]*>\s*Regular Season\s*</h3>', html)
    if not m:
        return None, None
    section = html[m.end():]
    tm = re.search(r'<table.*?</table>', section, re.S)
    if not tm:
        return None, None
    parser = TableParser(); parser.feed(tm.group(0))
    if not parser.tables:
        return None, None
    table = parser.tables[0]
    headers = [c[0] for c in table[0]]
    return headers, table[1:]

def position(html):
    m = re.search(r'\b(QB|RB|WR|TE)\b\s*(?:•|&bull;|·)', html)
    if m:
        return m.group(1)
    m = re.search(r'<span[^>]*>\s*(QB|RB|WR|TE)\s*</span>', html)
    return m.group(1) if m else None

def team_name(html):
    m = re.search(r'href="/teams/[^"]+"[^>]*>\s*([^<]+?)\s*</a>', html)
    return m.group(1).strip() if m else None

def parse_log_row(headers, cells, pos):
    text = [c[0] for c in cells]
    if len(text) < 4:
        return None
    week, date, opp, result = text[:4]
    stats = text[4:]
    out = {'week': num(week), 'game_date': date, 'opponent': opp, 'result': result,
           'team_win': 1 if result.startswith('W') else 0 if result.startswith('L') else None}
    rm = re.match(r'([WLT])\s*(\d+)\s*-\s*(\d+)', result)
    if rm:
        out['team_score'] = int(rm.group(2)); out['opponent_score'] = int(rm.group(3))
    def take(names):
        for name in names:
            if stats:
                out[name] = num(stats.pop(0))
            else:
                out[name] = None
    if pos == 'QB':
        take(['completions', 'pass_attempts', 'pass_yards', 'pass_avg', 'pass_td', 'interceptions', 'sacks', 'sack_yards', 'passer_rating',
              'rush_attempts', 'rush_yards', 'rush_avg', 'rush_td', 'fumbles', 'fumbles_lost'])
    elif pos == 'RB':
        take(['rush_attempts', 'rush_yards', 'rush_avg', 'rush_long', 'rush_td',
              'receptions', 'receiving_yards', 'receiving_avg', 'receiving_long', 'receiving_td', 'fumbles', 'fumbles_lost'])
    else:
        take(['receptions', 'receiving_yards', 'receiving_avg', 'receiving_long', 'receiving_td',
              'rush_attempts', 'rush_yards', 'rush_avg', 'rush_long', 'rush_td', 'fumbles', 'fumbles_lost'])
    return out

def parse_logs():
    panel = json.loads((DATA / 'player_panel.json').read_text())
    manifest = json.loads((RAW / 'manifest-players.json').read_text())
    urls = {i['id']: i['source_url'] for i in manifest['items']}
    games = json.loads((DATA / 'games.json').read_text())
    team_code = {}
    for g in games:
        team_code[g['home_team_name']] = g['home_team']; team_code[g['away_team_name']] = g['away_team']
    rows, issues = [], []
    for player in panel:
        key = f"player-{player['slug']}"
        item = next((i for i in manifest['items'] if i['id'] == key), None)
        if not item or item['http_status'] != 200:
            issues.append({'player': player['slug'], 'issue': 'source unavailable'}); continue
        html = read(key)
        pos = position(html)
        team = team_name(html)
        headers, table = logs_table(html)
        if not table:
            issues.append({'player': player['slug'], 'issue': 'no regular-season log table'}); continue
        for cells in table:
            row = parse_log_row(headers, cells, pos)
            if not row or row['week'] is None:
                continue
            row.update({'player_id': player['slug'], 'player': player['name'], 'position': pos,
                        'team_name': team, 'team': team_code.get(team), 'season': 2026,
                        'source_url': urls[key], 'selection': player['selection'],
                        'verification': 'official-explicit; blank stats remain null'})
            rows.append(row)
    rows.sort(key=lambda r: (r['player_id'], r['week']))
    (DATA / 'player_logs.json').write_text(json.dumps(rows, indent=2) + '\n')
    with (DATA / 'player_logs.csv').open('w', newline='') as handle:
        if rows:
            w = csv.DictWriter(handle, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    report = {'players': len(panel), 'player_game_rows': len(rows),
              'rows_with_receiving': sum(r.get('receptions') is not None for r in rows),
              'rows_with_rushing': sum(r.get('rush_attempts') is not None for r in rows),
              'rows_with_passing': sum(r.get('pass_yards') is not None for r in rows),
              'issues': issues, 'policy': 'Current-season official logs only; selected-leader panel is descriptive, not a population prop validation.'}
    (DATA / 'parse_report_players.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    import sys
    if '--panel' in sys.argv:
        build_panel()
    else:
        parse_logs()
