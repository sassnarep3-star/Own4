#!/usr/bin/env python3
"""Offline structural, calculation, and reproducibility checks; not legal verification."""
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import hashlib, subprocess, sys

ROOT = Path(__file__).resolve().parent
PAGES = sorted(ROOT.glob('*.html'))
ALLOWED = {'www.sf.gov', 'sf.gov', 'media.api.sf.gov', 'calcivilrights.ca.gov', 'www.hud.gov'}
class Scan(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows = []; self.row = None; self.body = False; self.links = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'tbody': self.body = True
        if tag == 'tr' and self.body: self.row = []
        url = a.get('href') or a.get('src')
        if url and tag in ('a','link','script','img'):
            self.links.append(url)
            if tag == 'a' and self.row is not None: self.row.append(url)
    def handle_endtag(self, tag):
        if tag == 'tr' and self.row is not None: self.rows.append(self.row); self.row = None
        if tag == 'tbody': self.body = False

def digest(): return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in PAGES}
before = digest(); subprocess.run([sys.executable, str(ROOT/'build.py')], check=True); assert before == digest(), 'Rebuild changed generated pages'
assert len(PAGES)==5
rows = 0
for p in PAGES:
    html = p.read_text(); parser = Scan(); parser.feed(html)
    assert '<html lang="en">' in html and 'aria-label="Main navigation"' in html
    assert 'aria-current="page"' in html and 'No attorney review has occurred' in html
    for row in parser.rows:
        assert any(urlsplit(u).scheme == 'https' and urlsplit(u).hostname in ALLOWED for u in row), (p.name, row)
    rows += len(parser.rows)
    for u in parser.links:
        x = urlsplit(u)
        if x.scheme or u.startswith('#'): continue
        assert (p.parent / unquote(x.path)).is_file(), (p.name, u)
assert Decimal('3995')*Decimal('.016') == Decimal('63.92')
assert Decimal('3150')*Decimal('.016') == Decimal('50.40')
print(f'PASS: {len(PAGES)} pages, {rows} source-linked rows, local links, arithmetic, deterministic rebuild')
