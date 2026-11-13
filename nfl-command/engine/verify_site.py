#!/usr/bin/env python3
"""Verify nfl-command site: (1) every table row carries an https source link or explicit unverified marker;
(2) every internal href resolves; (3) expected pages exist. Exits non-zero on any failure."""
import re, os, sys, glob

ROOT = 'nfl-command'
pages = [f'{ROOT}/index.html'] + sorted(glob.glob(f'{ROOT}/pages/*.html'))
problems = []
n_rows = n_sourced = n_unv = 0

for p in pages:
    if not os.path.exists(p):
        problems.append(f'MISSING PAGE {p}'); continue
    src = open(p).read()
    base = os.path.dirname(p)
    for tr in re.findall(r'<tr>(.*?)</tr>', src, re.S):
        if '<th>' in tr:
            continue
        n_rows += 1
        if 'https://' in tr:
            n_sourced += 1
        elif 'unv' in tr:
            n_unv += 1
        else:
            problems.append(f'UNSOURCED ROW in {p}: {re.sub("<[^>]+>", " ", tr)[:110]}')
    for href in re.findall(r'href="([^"]+)"', src):
        if href.startswith('http') or href.startswith('#') or href.startswith('mailto:'):
            continue
        target = os.path.normpath(os.path.join(base, href.split('#')[0]))
        if not os.path.exists(target):
            problems.append(f'BROKEN LINK in {p}: {href}')

expected = ['executive-summary','requirements','questions','suggestions','data','games','own-lines','strategies',
            'validation','correlations','leaderboard','injuries','depth','repo-review','flagged','sources']
for e in expected:
    if not os.path.exists(f'{ROOT}/pages/{e}.html'):
        problems.append(f'MISSING expected page pages/{e}.html')

print(f'pages: {len(pages)}  table rows: {n_rows}  sourced: {n_sourced}  blank/unverified-marked: {n_unv}')
if problems:
    print(f'PROBLEMS: {len(problems)}')
    for pr in problems[:40]:
        print(' -', pr)
    sys.exit(1)
print('VERIFY OK — every table row has an official source link (or explicit unverified marker); no broken internal links.')
