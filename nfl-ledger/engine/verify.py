#!/usr/bin/env python3
"""Verify nfl-ledger. Exits non-zero on any failure.
(1) every data-table row carries an https source link (tables marked class="ref" are definitions and are exempt);
(2) every internal href resolves to a file; (3) pages exist; (4) market columns are blank in every origination row;
(5) price store is empty and contains no numbers; (6) reconciliation is 32/32 and the Week 11 slate matches the
official schedule; (7) every correlation value carries n >= 1; (8) demotion engine unit tests pass (tests/)."""
import csv
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'data')
problems, notes = [], []
pages = [os.path.join(ROOT, 'index.html')] + sorted(glob.glob(os.path.join(ROOT, 'pages', '*.html')))
n_rows = n_linked = 0
for p in pages:
    if not os.path.exists(p):
        problems.append('missing page ' + p)
        continue
    src = open(p, encoding='utf-8').read()
    for tbl in re.findall(r'<table class="([^"]*)">(.*?)</table>', src, re.S):
        cls, body = tbl
        if 'ref' in cls.split():
            continue
        for tr in re.findall(r'<tbody>(.*?)</tbody>', body, re.S):
            for row in re.findall(r'<tr>(.*?)</tr>', tr, re.S):
                n_rows += 1
                if re.search(r'href="https://', row):
                    n_linked += 1
                else:
                    problems.append('UNSOURCED ROW in %s: %s' % (os.path.relpath(p, ROOT), re.sub('<[^>]+>', ' ', row)[:120]))
    for href in re.findall(r'href="([^"]+)"', src):
        if href.startswith(('http', '#', 'mailto:')):
            continue
        target = os.path.normpath(os.path.join(os.path.dirname(p), href.split('#')[0]))
        if not os.path.exists(target):
            problems.append('BROKEN LINK in %s: %s' % (os.path.relpath(p, ROOT), href))

expected = ['index.html'] + ['pages/%s.html' % x for x in [
    'executive-summary', 'results-feed', 'price-snapshots', 'origination', 'leaderboard', 'demotion',
    'replacement-depth', 'correlations', 'questions', 'suggestions', 'flagged', 'sources']]
for e in expected:
    if not os.path.exists(os.path.join(ROOT, e)):
        problems.append('MISSING expected page ' + e)

orig = json.load(open(os.path.join(DATA, 'originated_lines_week11.json')))
for r in orig['rows']:
    for k in ('step1_market_home_spread', 'step1_difference', 'step2_market_total', 'step2_difference',
              'step3_market_ml_home', 'step3_difference'):
        if r[k] not in ('', None):
            problems.append('market value present without official source: %s %s' % (r['game'], k))
if len(orig['rows']) != 13 or not orig['meta']['slate_matches_official_schedule']:
    problems.append('Week 11 slate does not match the 13 official games')

with open(os.path.join(DATA, 'price_snapshots.csv'), encoding='utf-8') as f:
    store = list(csv.DictReader(f))
if store:
    problems.append('price store has %d rows but no official price source is approved' % len(store))

rec = json.load(open(os.path.join(DATA, 'standings_reconciliation.json')))['meta']
if rec['reconciliation_matches'] != rec['reconciliation_total'] or rec['reconciliation_total'] != 32:
    problems.append('standings reconciliation not 32/32: %s' % rec)
res = json.load(open(os.path.join(DATA, 'results_feed.json')))
if len(res['rows']) != 137:
    problems.append('results feed has %d rows, expected 137' % len(res['rows']))
if not res['meta']['league_pf_equals_pa']:
    problems.append('league PF != PA')

cor = json.load(open(os.path.join(DATA, 'correlations.json')))
for r in cor['rows']:
    if not isinstance(r.get('n'), int) or r['n'] < 1:
        problems.append('correlation without n: ' + r['pair'])

t = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', os.path.join(ROOT, 'tests'), '-q'],
                   capture_output=True, text=True)
if t.returncode != 0:
    problems.append('demotion unit tests failed: ' + t.stderr[-400:])

print('pages: %d  data rows: %d  with https source link: %d' % (len(pages), n_rows, n_linked))
print('reconciliation %d/%d · results %d · week-11 slate ok=%s · price rows stored=%d · unit tests rc=%d' % (
    rec['reconciliation_matches'], rec['reconciliation_total'], len(res['rows']),
    orig['meta']['slate_matches_official_schedule'], len(store), t.returncode))
if problems:
    print('PROBLEMS: %d' % len(problems))
    for p in problems[:60]:
        print(' -', p)
    sys.exit(1)
print('VERIFY OK — every data row has a source link; no broken internal links; no unsourced market values.')
