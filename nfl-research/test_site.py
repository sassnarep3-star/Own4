from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
import unittest
import build

ROOT = Path(__file__).resolve().parent
class Parser(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.in_row=False; self.in_td=False; self.row_links=[]; self.rows=[]
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if tag=='tr': self.in_row=True; self.row_links=[]
        if tag=='td': self.in_td=True
        if tag=='a':
            self.links.append(attrs.get('href',''))
            if self.in_row and self.in_td: self.row_links.append(attrs.get('href',''))
    def handle_endtag(self, tag):
        if tag=='td': self.in_td=False
        if tag=='tr':
            if self.row_links: self.rows.append(self.row_links)
            self.in_row=False
class SiteTest(unittest.TestCase):
    def test_generated_rows_and_links(self):
        for name, (_,_,_,rows) in build.PAGES.items():
            p=Parser(); p.feed((ROOT / (name+'.html')).read_text())
            self.assertEqual(len(p.rows),len(rows),name)
            for row in p.rows:
                self.assertTrue(any(urlparse(x).scheme=='https' for x in row),name)
            for link in p.links:
                if not urlparse(link).scheme and not link.startswith('#'):
                    self.assertTrue((ROOT / link.split('#')[0]).exists(),link)
    def test_unknown_numbers_are_blank(self):
        for key in ('correlations','leaderboard'):
            for row in build.PAGES[key][3]:
                self.assertEqual(row[1:3], ('',''))
if __name__=='__main__': unittest.main()
