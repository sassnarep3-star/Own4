from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import re
import subprocess
import unittest
from decimal import Decimal
P = Path(__file__).resolve().parent
class Parser(HTMLParser):
 def __init__(self):
  super().__init__(); self.hrefs=[]; self.rows=[]; self.inrow=False; self.rowlinks=[]; self.rowhead=False
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if tag=='tr': self.inrow=True; self.rowlinks=[]; self.rowhead=False
  if tag=='th' and self.inrow: self.rowhead=True
  if tag=='a' and 'href' in d:
   self.hrefs.append(d['href'])
   if self.inrow:self.rowlinks.append(d['href'])
 def handle_endtag(self,tag):
  if tag=='tr':
   if not self.rowhead:self.rows.append(self.rowlinks)
   self.inrow=False
class TestSite(unittest.TestCase):
 def test_sources_and_internal_links(self):
  pages=list(P.glob('*.html')); self.assertEqual(len(pages),6)
  rows=0
  for p in pages:
   x=Parser(); x.feed(p.read_text())
   for row in x.rows:
    rows+=1; self.assertTrue(any(urlsplit(u).hostname in ('www.sf.gov','leginfo.legislature.ca.gov','www.hud.gov','calcivilrights.ca.gov') for u in row),(p,row))
   for u in x.hrefs:
    q=urlsplit(u)
    if q.scheme or not q.path: continue
    self.assertTrue((p.parent / unquote(q.path)).is_file(),(p,u))
  self.assertGreater(rows,40)
 def test_conditional_calculations(self):
  self.assertEqual(Decimal('3995')*Decimal('.016'),Decimal('63.92'))
  self.assertEqual(Decimal('3150')*Decimal('.016'),Decimal('50.40'))
  self.assertEqual(Decimal('3995')*Decimal('.014'),Decimal('55.930'))
 def test_reproducible(self):
  before={p.name:p.read_bytes() for p in P.glob('*.html')}; subprocess.run(['python3',str(P/'build.py')],check=True)
  self.assertEqual(before,{p.name:p.read_bytes() for p in P.glob('*.html')})
 def test_privacy_and_caveats(self):
  text=' '.join(p.read_text() for p in P.glob('*.html'))
  self.assertNotRegex(text,r'\b(?:L O|V N|J[Pp]|M T|E R|I S)\b')
  self.assertIn('not independently verified',text)
  self.assertIn('No tenant lawyer has reviewed',text)
if __name__=='__main__': unittest.main()
