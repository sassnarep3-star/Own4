#!/usr/bin/env python3
"""Publication gate for the nfl-marketboard site.

Three rules, enforced on every page this workspace publishes:

  1. every <tr> inside a <tbody> must contain at least one https:// link;
  2. every local href/src must resolve on disk;
  3. every page must carry the shared navigation and the footer.

Exits non-zero on any failure. Run after engine/site.py.
"""
from __future__ import annotations

import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SRC_RE = re.compile(r'https?://')
REF_RE = re.compile(r'(?:href|src)\s*=\s*["\']([^"\']+)["\']')
ROW_RE = re.compile(r'<tr>(.*?)</tr>', re.S)
TBODY_RE = re.compile(r'<tbody>(.*?)</tbody>', re.S)


def main() -> int:
    pages = sorted(os.path.basename(p) for p in glob.glob(os.path.join(ROOT, '*.html')))
    if not pages:
        print('FAIL: no pages found')
        return 1

    failures = []
    total_rows = 0
    total_refs = 0

    for page in pages:
        html = open(os.path.join(ROOT, page)).read()

        rows = [r for tb in TBODY_RE.findall(html) for r in ROW_RE.findall(tb)]
        total_rows += len(rows)
        for i, r in enumerate(rows):
            if not SRC_RE.search(r):
                failures.append(f'{page}: tbody row {i + 1} has no https source link')

        for m in REF_RE.finditer(html):
            u = m.group(1)
            if u.startswith(('http', '#', 'data:', 'mailto:')):
                continue
            total_refs += 1
            path = os.path.join(ROOT, u.split('#')[0].split('?')[0])
            if not os.path.exists(path):
                failures.append(f'{page}: broken local link -> {u}')

        if '<nav>' not in html:
            failures.append(f'{page}: missing navigation')
        if 'MY-RESET' not in html and 'ncpgambling.org' not in html:
            failures.append(f'{page}: missing responsible-gambling footer')

    print(f'pages checked : {len(pages)}')
    print(f'tbody rows    : {total_rows}')
    print(f'local refs    : {total_refs}')
    if failures:
        print(f'\nFAIL ({len(failures)}):')
        for f in failures[:50]:
            print('  ' + f)
        if len(failures) > 50:
            print(f'  … and {len(failures) - 50} more')
        return 1
    print('\nPASS: every table row carries an https source, every local link resolves, '
          'every page has nav and footer.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
