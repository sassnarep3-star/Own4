"""Structural publication tests, not external factual certification."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json
P=Path(__file__).resolve().parent
class Audit(HTMLParser):
 def __init__(self):
  super().__init__(); self.links=[]; self.rows=[]; self.row=None
 def handle_starttag(self,t,a):
  d=dict(a)
  if t=='tr': self.row={'data':False,'official':False}
  if t=='td' and self.row is not None: self.row['data']=True
  if t in ('a','link','script'):
   u=d.get('href',d.get('src',''));self.links.append(u)
   if self.row is not None and urlsplit(u).hostname in {'www.nfl.com','scikit-learn.org'}:self.row['official']=True
 def handle_endtag(self,t):
  if t=='tr' and self.row is not None:self.rows.append(self.row);self.row=None
rows=0
for f in P.glob('*.html'):
 a=Audit();a.feed(f.read_text())
 for r in a.rows:
  if r['data']:assert r['official'],f'{f}: row missing official context';rows+=1
 for u in a.links:
  s=urlsplit(u)
  if not s.scheme and s.path:assert (f.parent/unquote(s.path)).exists(),(f,u)
 assert 'name="viewport"' in f.read_text()
 assert 'Flagged for Review' in f.read_text()
assert '<td></td>' in (P/'metrics.html').read_text()
data=json.loads((P/'review-register.json').read_text())
assert len(data['suggestions'][1])==8
assert all(r['status']=='Proposed — not approved' for r in data['suggestions'][1])
assert len(list(P.glob('*.html')))==8
print(f'PASS: 8 pages, {rows} source-linked data rows; links resolve; suggestions remain unapproved; missing metrics blank.')
