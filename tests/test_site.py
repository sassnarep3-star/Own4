import unittest,json
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
class Parser(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[];self.rows=[];self.row=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='tr':self.row=[]
        if tag=='a' and 'href' in a:
            self.links.append(a['href'])
            if self.row is not None:self.row.append(a['href'])
    def handle_endtag(self,tag):
        if tag=='tr':self.rows.append(self.row);self.row=None
class Site(unittest.TestCase):
    def test_pages_and_links(self):
        pages=list((ROOT/'docs').glob('*.html'));self.assertEqual(len(pages),8)
        for f in pages:
            p=Parser();p.feed(f.read_text())
            for link in p.links:
                if not link.startswith(('https://','#')):self.assertTrue((f.parent/link).is_file(),(f,link))
            for row in p.rows[1:]:
                self.assertTrue(any(x.startswith('https://') for x in row),(f,row))
    def test_official_sources(self):
        d=json.loads((ROOT/'docs/data/research.json').read_text())
        for url,_ in d['sources'].values():
            self.assertIn(urlparse(url).hostname,['www.nba.com','official.nba.com','www.itl.nist.gov','www.nist.gov','scikit-learn.org'])
    def test_unverified_metrics_blank(self):
        d=json.loads((ROOT/'docs/data/research.json').read_text())
        for r in d['pages']['correlations'][4]:self.assertEqual(r[2:5],['','',''])
        for r in d['pages']['leaderboard'][4]:self.assertEqual(r[2:5],['','',''])
if __name__=='__main__':unittest.main()
