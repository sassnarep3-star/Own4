#!/usr/bin/env python3
"""Verify dashboard rows, local links, and reproducible generated pages offline."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
SITE = ROOT.parent
ALLOWED = {'nfl.com', 'www.nfl.com', 'operations.nfl.com', 'nextgenstats.nfl.com', 'scikit-learn.org', 'www.itl.nist.gov'}

class Audit(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.in_body=False; self.in_row=False; self.row_links=[]; self.rows=[]
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'tbody': self.in_body=True
        if tag == 'tr' and self.in_body: self.in_row=True; self.row_links=[]
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])
            if self.in_row: self.row_links.append(attrs['href'])
        if tag == 'link' and 'href' in attrs: self.links.append(attrs['href'])
    def handle_endtag(self, tag):
        if tag == 'tr' and self.in_row: self.rows.append(self.row_links); self.in_row=False
        if tag == 'tbody': self.in_body=False

def main():
    before = {p.name: p.read_bytes() for p in ROOT.glob('*.html')}
    subprocess.run([sys.executable, str(ROOT / 'build.py')], check=True)
    after = {p.name: p.read_bytes() for p in ROOT.glob('*.html')}
    errors=[]
    if before != after: errors.append('Generated pages were stale or missing')
    count=0
    for path in sorted(ROOT.glob('*.html')):
        audit=Audit(); audit.feed(path.read_text(encoding='utf-8')); count += len(audit.rows)
        for i, row in enumerate(audit.rows, 1):
            if not any(urlsplit(h).scheme == 'https' and urlsplit(h).hostname in ALLOWED for h in row):
                errors.append(f'{path.name}: row {i} lacks an approved official publisher link')
        for href in audit.links:
            parts=urlsplit(href)
            if parts.scheme or parts.netloc or not parts.path: continue
            target=(path.parent / unquote(parts.path)).resolve()
            if not target.is_relative_to(SITE) or not target.is_file(): errors.append(f'{path.name}: broken local link {href}')
    if len(after) != 6: errors.append('Expected six generated pages')
    if errors:
        print('\n'.join(errors)); return 1
    print(f'PASS: {len(after)} generated pages; {count} body rows have official publisher links; local links resolve. External pages not crawled.')
    return 0
if __name__ == '__main__': raise SystemExit(main())
