"""Static-site release checks: local links, anchors, row sources and null policy."""
from __future__ import annotations
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
import json
import re

ROOT=Path(__file__).resolve().parent
SITE=ROOT/'site'
ALLOWED=('nba.com','help.bet365.com','support.fanduel.com','nist.gov','scikit-learn.org','nber.org','ssrn.com','github.com','docs.github.com')

def official(url):
    try: host=(urlparse(url).hostname or '').lower()
    except ValueError:return False
    return any(host==d or host.endswith('.'+d) for d in ALLOWED)

class Page(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[];self.ids=set();self.rows=[];self.row=None;self.header=False;self.lang=None;self.title=False;self.title_text='';self.inputs=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='html':self.lang=a.get('lang')
        if tag=='title':self.title=True
        if 'id' in a:self.ids.add(a['id'])
        if tag=='a' and 'href' in a:self.links.append(a['href'])
        if tag=='tr':self.row=[];self.header=False
        if tag=='th':self.header=True
        if tag=='a' and self.row is not None:self.row.append(a.get('href',''))
        if tag=='input':self.inputs.append(a)
    def handle_endtag(self,tag):
        if tag=='title':self.title=False
        if tag=='tr' and self.row is not None:
            self.rows.append((self.row,self.header));self.row=None
    def handle_data(self,data):
        if self.title:self.title_text+=data

def main():
    errors=[];pages={};rows=0;local_links=0;external=set()
    for path in sorted(SITE.glob('*.html')):
        p=Page();p.feed(path.read_text());pages[path.name]=p
        if p.lang!='en':errors.append(f'{path.name}: missing lang=en')
        if not p.title_text.strip():errors.append(f'{path.name}: missing title')
        for inp in p.inputs:
            if not inp.get('aria-label'):errors.append(f'{path.name}: unlabeled input')
        for i,(links,header) in enumerate(p.rows):
            if header:continue
            rows+=1
            if not any(official(u) for u in links):errors.append(f'{path.name}: row {i+1} lacks official source')
    for name,p in pages.items():
        for url in p.links:
            if url.startswith(('https://','http://')):
                external.add(url)
                if not official(url):errors.append(f'{name}: non-allowlisted source {url}')
                continue
            if url.startswith(('data:','mailto:','#')):continue
            parsed=urlparse(url);target=(SITE/unquote(parsed.path)).resolve() if parsed.path else SITE/name
            local_links+=1
            if not target.is_file():errors.append(f'{name}: broken local link {url}');continue
            if parsed.fragment and target.suffix=='.html':
                other=pages.get(target.name)
                if other and parsed.fragment not in other.ids:errors.append(f'{name}: missing anchor {url}')
    for name in ('index.html','flagged.html','executive-summary.html','sources.html','verification.html'):
        if name not in pages:errors.append('missing '+name)
    for name,p in pages.items():
        for target in ('flagged.html','sources.html','index.html'):
            if target not in p.links:errors.append(f'{name}: navigation missing {target}')
    r=json.loads((SITE/'data/research.json').read_text())
    if r['qualified_strategies']!=0 or r['rewards_awarded']!=0:errors.append('pilot unexpectedly claims qualified strategies/rewards')
    for row in r['predictions']:
        if row['book_decimal'] is not None or row['estimated_price_edge'] is not None:errors.append('invented market value')
    if (SITE/'data/research.json').read_bytes()!=(ROOT/'data/research.json').read_bytes():errors.append('stale research export')
    report={'pages':len(pages),'table_rows':rows,'local_links_checked':local_links,'unique_external_links':len(external),
            'errors':errors,'external_link_policy':'Primary-source domain allowlist; not a live HTTP availability check',
            'status':'pass' if not errors else 'fail'}
    (ROOT/'data/site_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='errors'},indent=2))
    for error in errors:print('ERROR',error)
    if errors:raise SystemExit(1)

if __name__=='__main__':main()
