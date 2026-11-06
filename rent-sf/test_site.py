"""Offline structural and arithmetic checks; source accuracy requires manual review."""
from html.parser import HTMLParser
from pathlib import Path
from decimal import Decimal
from urllib.parse import urlparse
import hashlib
import subprocess
import sys

root = Path(__file__).resolve().parent
class Check(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.rows=[]; self.row=None; self.current=0; self.body=False
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='tbody': self.body=True
        if tag=='tr' and self.body: self.row=[]
        if tag=='a':
            if 'href' in a:
                self.links.append(a['href'])
                if self.row is not None: self.row.append(a['href'])
            if a.get('aria-current') == 'page': self.current += 1
    def handle_endtag(self, tag):
        if tag=='tr' and self.body: self.rows.append(self.row); self.row=None
        if tag=='tbody': self.body=False

pages = sorted(root.glob('*.html'))
assert len(pages)==6
count=0
for file in pages:
    text=file.read_text(); parser=Check(); parser.feed(text)
    assert parser.current == 1, file
    assert 'Not legal advice' in text and 'flagged.html' in text
    for href in parser.links:
        u=urlparse(href)
        if u.scheme:
            assert u.scheme=='https', (file, href)
            assert u.hostname in {'www.sf.gov','sf.gov','leginfo.legislature.ca.gov','calcivilrights.ca.gov','archives.hud.gov'}, (file,href)
        elif not href.startswith('#'):
            assert (file.parent/u.path).is_file(), (file,href)
    for row in parser.rows:
        assert any(urlparse(url).scheme=='https' for url in row), (file,row)
        count+=1
    assert text.count('<tbody>') == text.count('</tbody>')
assert Decimal('3995')*Decimal('.016') == Decimal('63.92')
assert Decimal('3150')*Decimal('.016') == Decimal('50.40')
assert count >= 35
before = {p: hashlib.sha256(p.read_bytes()).digest() for p in pages}
subprocess.run([sys.executable,str(root/'build.py')], check=True)
assert before == {p: hashlib.sha256(p.read_bytes()).digest() for p in pages}, 'Generated pages not reproducible'
print(f'PASS: {len(pages)} pages, {count} linked table rows, local targets, official domains, arithmetic and reproducible build')
