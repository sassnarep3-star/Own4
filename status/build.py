"""Read-only inherited-repository inventory; writes only status/ outputs.
Not factual verification: source links and hashes cannot establish truth.
Run python status/build.py, then python status/test_status.py.
"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import subprocess, hashlib, json, html
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'status'
BASE = 'https://github.com/sassnarep3-star/Own4/blob/a363c75356658db670445bb42541d3c5d30a2298/'
OFFICIAL = ('nba.com','nist.gov','scikit-learn.org','github.com','docs.github.com','help.bet365.com','support.fanduel.com','nber.org','ssrn.com')

def primary(url):
    host = urlsplit(url).hostname or ''
    return url.startswith('https://') and any(host == d or host.endswith('.'+d) for d in OFFICIAL)

class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.rows=[]; self.row=None; self.header=False
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag in ('a','link','script','img'):
            u=a.get('href', a.get('src'))
            if u: self.links.append(u)
        if tag=='tr': self.row=[]; self.header=False
        if tag=='th': self.header=True
        if tag=='a' and self.row is not None: self.row.append(a.get('href',''))
    def handle_endtag(self, tag):
        if tag=='tr' and self.row is not None:
            if not self.header: self.rows.append(self.row)
            self.row=None

def resolve(path, url):
    p=urlsplit(url)
    if p.scheme or p.netloc or not p.path: return None
    raw=unquote(p.path)
    if raw.startswith('/Own4/'): target=ROOT/raw[len('/Own4/'):]
    elif raw.startswith('/'): target=ROOT/raw.lstrip('/')
    else: target=path.parent/raw
    if target.is_dir(): target=target/'index.html'
    return target.resolve()

def inventory():
    names=subprocess.check_output(['git','ls-tree','-r','--name-only','a363c75356658db670445bb42541d3c5d30a2298'],cwd=ROOT,text=True).splitlines()
    files=[]; pages=[]
    for name in names:
        path=ROOT/name
        raw=subprocess.check_output(['git','show','a363c75356658db670445bb42541d3c5d30a2298:'+name],cwd=ROOT)
        try: text=raw.decode('utf-8'); lines=len(text.splitlines())
        except UnicodeDecodeError: lines=None
        files.append(dict(path=name,sha256=hashlib.sha256(raw).hexdigest(),lines=lines,bytes=len(raw),factual_status='not independently reverified'))
        if path.suffix!='.html' or name.startswith('data/raw/'): continue
        p=Page();p.feed(text)
        broken=[]
        for url in p.links:
            target=resolve(path,url)
            if target is not None and not target.is_file(): broken.append(url)
        missing=[i+1 for i,links in enumerate(p.rows) if not any(primary(u) for u in links)]
        pages.append(dict(path=name,rows=len(p.rows),rows_without_allowlisted_link=missing,broken_local_targets=sorted(set(broken))))
    return dict(snapshot='a363c75356658db670445bb42541d3c5d30a2298',policy='Mechanical UTF-8 line/hash, static HTML source-link and local target inventory only. No factual certification; archived data/raw HTML excluded from site-link checks; no JS-rendered rows, HTTP status or fragment checks.',files=files,pages=pages)

def esc(v): return html.escape(str(v),quote=True)
def link(url,text): return f'<a href="{esc(url)}">{esc(text)}</a>'
def table(headers,rows):
    return '<div class="scroll"><table><thead><tr>'+''.join('<th scope="col">'+esc(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(x)+'</td>' for x in r)+'</tr>' for r in rows)+'</tbody></table></div>'
def page(name,title,body):
    nav=''.join(link(f'{p}.html',t) for p,t in [('index','Overview'),('research','Research & gates'),('audit','Repository audit'),('flagged','Flagged for Review')])
    (OUT/(name+'.html')).write_text(f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} · NBA Evidence Status</title><link rel="stylesheet" href="style.css"><body><header><a class="brand" href="index.html">OWN4 <span>/ NBA RESEARCH</span></a><nav aria-label="Main">{nav}</nav></header><main><p class="eyebrow">EVIDENCE STATUS · 5 NOVEMBER 2026</p><h1>{esc(title)}</h1>{body}</main><footer>Research only. No betting execution or funded prizes. Links are evidence pointers, not proof of efficacy. {link('../nba-evidence/site/index.html','Open detailed pilot →')}</footer></body></html>''')

def main():
    report=inventory(); (OUT/'inventory.json').write_text(json.dumps(report,indent=2)+'\n')
    pages=report['pages']; missing=sum(len(p['rows_without_allowlisted_link']) for p in pages); broken=sum(len(p['broken_local_targets']) for p in pages)
    repo=link(BASE+'nba-evidence/data/research.json','Research artifact (derived, not official NBA prices)')
    page('index','Evidence before edge',f'''<p class="lead">A reproducible NBA line-origination pilot, with a hard distinction between research ideas and validated betting skill.</p><div class="notice"><strong>Decision: do not release betting strategies.</strong> The inherited pilot reports no qualified strategies and no rewards. Historical executable market prices are absent.</div><section class="cards"><article><h2>Singles first</h2><p>Chronological baselines, calibration and matched price evaluation.</p></article><article><h2>Dependence matters</h2><p>Parlays and prop combinations need joint distributions, not blind multiplication.</p></article><article><h2>Fail closed</h2><p>Missing evidence prevents reward eligibility, not publication of research.</p></article></section><h2>Executive summary</h2>'''+table(['Finding','Evidence status','Source'],[
    ['Existing pilot','62 game rows, 38 participating-player rows; January 2025 convenience sample, not current NBA coverage.',repo],
    ['Model performance','Inherited test Brier 0.3076 vs baseline 0.2720 (lower is better). Underperformance; not a validated edge.',repo],
    ['Own lines','Historical model estimates exist. They are derived calculations, not official bookmaker quotes.',link('../nba-evidence/site/lines.html','Pilot lines')+' · '+repo],
    ['Luck and skill','Luck cannot be removed. Frozen trials, uncertainty and prospective replication are required by project policy.',link(BASE+'nba-evidence/docs/METHODOLOGY.md','Project methodology')],
    ['Fresh verification','FAQ download restriction, covariance definition and calibration caveat re-read today. All inherited rows were NOT independently refetched.',link('flagged.html','Verification limits')+' · '+link('https://www.nba.com/stats/help/faq','NBA FAQ')],
    ['Repository coverage',f'{len(report["files"])} inherited files inventoried; {len(pages)} static HTML pages inspected mechanically. {missing} rows lack an audit-allowlisted link; {broken} page-local missing-target entries.',link('inventory.json','Full mechanical inventory')+' · '+link(BASE,'Official repository snapshot')]
    ])+f'<p>{link("../nba-evidence/site/executive-summary.html","Detailed executive summary →")} · {link("../nba-evidence/site/leaderboard.html","Diagnostic leaderboard →")}</p>')
    page('research','Research, not recommendations','<p class="lead">Existing hypotheses and validation gates are preserved. Source documentation supports methods—not strategy profitability.</p>'+table(['Category','Proposed workflow / eligibility','Source'],[
    ['Single bets','Rolling team strength and totals; freeze timestamped features; compare probabilities with a training-only baseline before comparing to executable prices.',link(BASE+'nba-evidence/docs/METHODOLOGY.md','Methodology')],
    ['Cross-game parlays','Measure joint outcomes and shared exposure; test any independence approximation rather than assume it.',link('https://www.itl.nist.gov/div898/handbook/pmc/section5/pmc541.htm','NIST covariance')],
    ['Same-game parlays','Use joint distributions and operator-specific payouts and settlement. Pairwise correlations alone do not determine multileg joint probabilities.',link(BASE+'nba-evidence/nba_lab/engine.py','Project calculation implementation')],
    ['Player prop combinations','Current pooled two-game player correlations are exploratory, not within-player dependence forecasts. Deployment coefficients remain blank.',link(BASE+'nba-evidence/data/research.json','Derived correlation register')],
    ['Calibration','Brier reflects discrimination and uncertainty as well as calibration. Lower Brier alone is not proof of improved calibration.',link('https://scikit-learn.org/stable/modules/calibration.html','Official scikit-learn documentation; opening section read')],
    ['Release gates','Require authorized point-in-time data, locked holdouts, sample adequacy, calibration, multiplicity control, dependence validation, net execution economics, prospective replication and risk controls. Exact ten-gate protocol is in the pilot.',link(BASE+'nba-evidence/data/protocol.json','Frozen project protocol')],
    ['Leaderboard and rewards','Separate diagnostic ranking from betting eligibility. Proposed non-monetary research points only; all gates required. No funded reward promise.',link(BASE+'nba-evidence/data/research.json','Leaderboard and gate results')]
    ])+'<p>'+link('../nba-evidence/site/strategies.html','Strategy catalog')+' · '+link('../nba-evidence/site/validation.html','Gate-by-gate results')+' · '+link('../nba-evidence/site/correlations.html','Exploratory correlation estimates')+'</p>')
    rows=[]
    for p in pages:
        if p['rows_without_allowlisted_link'] or p['broken_local_targets']:
            rows.append([esc(p['path']),str(len(p['rows_without_allowlisted_link'])),esc('; '.join(p['broken_local_targets'])),link(BASE+p['path'],'Repository file')])
    page('audit','Repository audit','<p class="lead">Every inherited tracked file was read for a checksum and text-line inventory. That is NOT line-by-line factual verification.</p><p>Archived data/raw HTML is inventoried but excluded from site-link checks because its relative links belong to the original publisher. Static HTML checks cover existing local targets (including assets) and a conservative primary-domain link allowlist. They do not execute JavaScript, verify fragments or fetch every external source. A missing allowlisted link is a review candidate, not proof of false content.</p>'+table(['File','Rows lacking allowlisted source','Missing local targets','Source'],rows)+f'<p>{link("inventory.json","Download complete file hashes, line counts and page-level results")}</p>')
    page('flagged','Flagged for Review','<div class="notice">Unverified external facts and missing market inputs must not be treated as deployable betting signals. Blank means unavailable—not zero.</div>'+table(['Issue','Status / action','Source'],[
    ['Whole-repository factual revalidation','UNVERIFIED. Mechanical line coverage is complete for the inherited snapshot; independent factual verification of every inherited row is not. Prior session claims are not adopted as fresh checks.',link('inventory.json','Inventory')+' · '+link(BASE,'Repository snapshot')],
    ['Historical executable sportsbook odds','UNVERIFIED. Leave price, ROI and CLV unavailable until authorized operator records and timestamps exist.',link(BASE+'nba-evidence/data/research.json','Missing-market register')],
    ['Expanded NBA data rights','NEEDS REVIEW. NBA FAQ says stats are not available for academic or personal download. Read 2026-11-05; no bulk collection performed by this session. No legal authorization inferred for inherited extracts.',link('https://www.nba.com/stats/help/faq','NBA official FAQ')],
    ['Source freshness','Partial reads only: glossary chunk 0 of 10, calibration chunk 0 of 3, FAQ chunk 0 of 2. Only visible claims used. NIST covariance page read completely.',link('https://www.nba.com/stats/help/glossary','NBA glossary')+' · '+link('https://scikit-learn.org/stable/modules/calibration.html','Calibration')+' · '+link('https://www.itl.nist.gov/div898/handbook/pmc/section5/pmc541.htm','NIST')],
    ['Spot check, not full player revalidation','NBA box-score chunk 3 confirms Dort 38:49, 14 points, 6 rebounds, 1 assist and Boston totals 92 points. Other player rows were not all freshly rechecked.',link('https://www.nba.com/game/bos-vs-okc-0022400487/box-score','Official NBA box score')],
    ['Model generalization and correlation','No validated betting edge. Small convenience sample; pooled player correlations cannot be used as personalized same-game dependence. Confidence intervals remain unavailable where suppressed.',link(BASE+'nba-evidence/data/research.json','Derived research output')],
    ['Inherited site irregularities','Local target and source-link candidates are published without editing peer namespaces. Existing pages may contain legacy source policies or claims; use the detailed flags before relying on them.',link('audit.html','Audit findings')+' · '+link(BASE,'Repository snapshot')]
    ])+'<p>'+link('../nba-evidence/site/flagged.html','All inherited pilot flags →')+'</p>')
    print(f'Inventoried {len(report["files"])} files and {len(pages)} HTML pages; missing-source candidates={missing}; missing-local-target entries={broken}')
if __name__=='__main__': main()
