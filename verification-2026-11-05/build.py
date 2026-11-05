#!/usr/bin/env python3
"""Reproduce a bounded, static audit of published HTML. No network or factual truth certification."""
from collections import defaultdict
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
NBA_MODULES = {'index.html', 'pages', 'docs', 'lab', 'lines-lab', 'nba-evidence',
               'own4-dashboard', 'pipeline', 'status'}
# A fixed inherited-page universe keeps the report stable across regeneration.
MODULES = NBA_MODULES | {'nfl', 'nfl-lab', 'nfl-quant', 'nfl-research'}
REPO = 'https://github.com/sassnarep3-star/Own4/blob/main/'
FAQ = 'https://www.nba.com/stats/help/faq'
GAMES = 'https://www.nba.com/games?date=2025-01-05'
RULE = 'https://official.nba.com/rule-no-5-scoring-and-timing/'
PAGES_DOC = 'https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site'

class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = []
        self.links = []
        self.row = None
        self.body = 0
        self.header = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'tbody': self.body += 1
        if tag == 'tr' and self.body:
            self.row = []
            self.header = False
        if tag == 'th' and self.row is not None: self.header = True
        if tag in ('a', 'link', 'script', 'img'):
            u = a.get('href') or a.get('src')
            if u:
                self.links.append(u)
                if tag == 'a' and self.row is not None: self.row.append(u)
    def handle_endtag(self, tag):
        if tag == 'tr' and self.row is not None:
            if not self.header: self.rows.append(self.row)
            self.row = None
        if tag == 'tbody': self.body = max(0, self.body-1)


def is_nba(url):
    host = (urlsplit(url).hostname or '').lower()
    return host == 'nba.com' or host.endswith('.nba.com')


def scan(paths):
    by_module = defaultdict(lambda: {'pages': 0, 'rows': 0, 'external_source_rows': 0,
                                     'nba_source_rows': 0, 'missing': 0, 'broken': 0})
    missing = []
    broken = []
    for path in paths:
        rel = path.relative_to(ROOT).as_posix()
        key = rel.split('/')[0]
        stats = by_module[key]
        stats['pages'] += 1
        p = Links(); p.feed(path.read_text(encoding='utf-8'))
        stats['rows'] += len(p.rows)
        for n, row in enumerate(p.rows, 1):
            external = [u for u in row if u.startswith('https://')]
            if external: stats['external_source_rows'] += 1
            else:
                stats['missing'] += 1
                missing.append({'file': rel, 'row': n})
            if any(is_nba(u) for u in external): stats['nba_source_rows'] += 1
        for u in p.links:
            if u.startswith(('http://', 'https://', '//', '#', 'mailto:', 'tel:', 'data:', 'javascript:')):
                continue
            parsed = urlsplit(u)
            if parsed.path.startswith('/Own4/'):
                target = ROOT / unquote(parsed.path[len('/Own4/'):])
            elif parsed.path.startswith('/'):
                # A root-relative link outside the project's Pages base cannot work on project Pages.
                target = ROOT / '__outside_project_root__'
            else:
                target = path.parent / unquote(parsed.path) if parsed.path else path
            if not target.is_file():
                stats['broken'] += 1
                broken.append({'file': rel, 'href': u})
    return dict(sorted(by_module.items())), missing, broken


def a(url, label):
    return f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{escape(label)} ↗</a>'


def frame(title, section, body):
    nav = [('index.html','Overview'), ('coverage.html','Module coverage'),
           ('flagged.html','Flagged for Review')]
    links = ''.join(f'<a class="{"active" if section == name else ""}" href="{name}">{label}</a>' for name,label in nav)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Bounded verification of the Own4 research site, with source-linked findings and explicit limits"><title>{escape(title)} · Own4 Audit</title><link rel="stylesheet" href="style.css"></head><body><a class="skip" href="#main">Skip to main content</a><aside><a class="brand" href="index.html"><span class="mark">O4</span><span>Own4 <small>VERIFICATION DESK</small></span></a><nav aria-label="Audit navigation">{links}</nav><p class="side-note">Snapshot 05 Nov 2026.<br>Research, not betting advice.<br>Published findings are bounded.</p><a class="back" href="../index.html">← Main dashboard</a></aside><div class="content"><header><span>OWN4 / NBA RESEARCH / VERIFICATION</span><span class="tag">INDEPENDENT CHECK · 05 NOV 2026</span></header><main id="main">{body}<footer>Own4 · No official NBA endorsement. A source link is not a validation of the row's claim. · {a(FAQ, 'NBA data-use FAQ')}</footer></main></div></body></html>'''


def table(headers, rows):
    return '<div class="table-wrap"><table><thead><tr>' + ''.join(f'<th scope="col">{escape(h)}</th>' for h in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>' for r in rows) + '</tbody></table></div>'


def build():
    inherited = sorted(p for p in ROOT.rglob('*.html')
                       if p.relative_to(ROOT).parts[0] in MODULES
                       and 'data' not in p.relative_to(ROOT).parts
                       and '.git' not in p.parts)
    modules, missing, broken = scan(inherited)
    nba = [v for k,v in modules.items() if k in NBA_MODULES]
    count = lambda key: sum(v[key] for v in nba)
    report = {
        'as_of': '2026-11-05', 'scope': 'Tracked/inherited rendered HTML pages in named site modules, excluding raw NBA source HTML and this audit',
        'modules': modules, 'nba_pages': count('pages'), 'nba_table_rows': count('rows'),
        'nba_rows_with_https_link': count('external_source_rows'),
        'nba_rows_with_nba_domain_link': count('nba_source_rows'),
        'missing_external_source_rows': missing, 'broken_internal_links': broken,
        'limits': 'Structural source-link and file-existence checks only. URL reachability, per-row factual support, data licensing, financial returns and causality are NOT verified.'
    }
    HERE.joinpath('report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    # All facts in the audit point to the repo record for counts, and primary sources for context.
    cards = f'''<div class="kpis"><article><small>NBA published pages</small><strong>{count('pages')}</strong><span>HTML paths inspected</span></article><article><small>NBA table rows</small><strong>{count('rows'):,}</strong><span>{count('external_source_rows'):,} have an HTTPS link</span></article><article><small>NBA-domain links</small><strong>{count('nba_source_rows'):,}</strong><span>Row-level syntax, not truth</span></article><article><small>Validated edge</small><strong>—</strong><span>Unverified · no official price archive</span></article></div>'''
    summary_rows = [
        ('Published NBA HTML', f'{count("pages")} pages, {count("rows"):,} table rows; {count("external_source_rows"):,} rows include an HTTPS link. This is a code-level check, not independent confirmation of every value.', a(REPO+'verification-2026-11-05/build.py','Reproduce scan')),
        ('Official reference', 'The NBA FAQ states that its stats are not available for academic or personal download. The site has not acquired a licensed full historical dataset.', a(FAQ,'NBA FAQ')),
        ('Historical sample spot-check', 'Official Jan 5, 2025 scoreboard displays Celtics 92, Thunder 105. This verifies this score only; the other 61 inherited sample games were not re-fetched in this session.', a(GAMES,'NBA scoreboard')),
        ('Competition status', 'Do not promote a provisional proxy result to an executable betting edge. Market prices, operator settlement and prospective replication remain unverified; no reward is awarded by this audit.', a(FAQ,'NBA access policy')+' · '+a(REPO+'nba-evidence/data/research.json','Pilot results')),
        ('Site publication', 'A static project site can publish from the main branch root; deployment must be checked after merging, not inferred from a local build.', a(PAGES_DOC,'GitHub Pages docs')),
    ]
    intro = f'''<div class="eyebrow">Evidence before rankings</div><h1>Verification desk</h1><p class="lede">A source-aware quality check for an existing multi-workspace NBA research repository. No new bet prices or results have been invented. See the {a('flagged.html','review register')} for items not supported.</p><div class="notice"><strong>Executive decision · no qualified betting strategy is established here.</strong><br>Inherited dashboards disagree about provisional proxy results and pilot forecasts. Neither supplies verified executable odds and prospective evidence. Luck cannot be removed; it can only be bounded by locked tests, clustered uncertainty and replication.</div>{cards}<section><h2>Executive summary</h2>{table(['Area','Verified scope / decision','Inspect source'],summary_rows)}</section><section class="grid"><a class="tile" href="coverage.html"><b>Module coverage →</b><span>Per-workspace page and row counts, with precise limits.</span></a><a class="tile" href="flagged.html"><b>Flagged for Review →</b><span>Broken links, unsupported source rows, stale or contradictory results.</span></a><a class="tile" href="../nba-evidence/site/index.html"><b>NBA Evidence →</b><span>Historical lines, singles, parlays, props, correlations and gates; read its own limitations.</span></a><a class="tile" href="../pages/competition.html"><b>Root competition →</b><span>Existing dashboard. Treat all model numbers as derived, not official lines.</span></a></section>'''
    HERE.joinpath('index.html').write_text(frame('Overview','index.html',intro), encoding='utf-8')
    cover = []
    for module,s in modules.items():
        src = REPO + ('index.html' if module=='index.html' else module+'/')
        cover.append((f'<code>{escape(module)}</code>',str(s['pages']),str(s['rows']),str(s['external_source_rows']),str(s['nba_source_rows']) if module in NBA_MODULES else '—',str(s['broken']),a(src,'Repository'))) 
    coverage = f'''<div class="eyebrow">Structural checks</div><h1>Module coverage</h1><p class="lede">All inherited published HTML under known modules; raw captured NBA pages in <code>data/raw/</code> are input artifacts, not this site's own output. A linked URL is only a candidate source, not proof it supports the cell.</p>{table(['Module','Pages','Rows','Rows with HTTPS link','Rows linking NBA','Broken links','Repository source'],cover)}<div class="notice">NBA rows with missing HTTPS link: {sum(modules[k]['missing'] for k in NBA_MODULES if k in modules)}. Non-NBA rows with missing HTTPS link: {sum(v['missing'] for k,v in modules.items() if k not in NBA_MODULES)}. See the {a('flagged.html','review register')}. These counts do not establish that linked pages verify each row.</div><p>Official NBA rules describe scoring and timing, not sportsbook bet settlement: {a(RULE,'NBA Rule 5')}. NBA Stats access restrictions: {a(FAQ,'NBA FAQ')}.</p>'''
    HERE.joinpath('coverage.html').write_text(frame('Module coverage','coverage.html',coverage), encoding='utf-8')
    flags = [
        ('V-01','No certified executable market prices','Unverified', 'Historical official odds, timestamps and settlement rules are not established by an NBA score source. Price edge / ROI / rewards:', '', a(FAQ,'NBA FAQ')+' · '+a(REPO+'nba-evidence/site/flagged.html','Pilot flags')),
        ('V-02','Proxy / pilot conclusions differ','Needs review','The inherited root summary reports provisional proxy winners; the NBA Evidence pilot reports zero qualified strategies. They are distinct samples and gate definitions, not a verified sportsbook edge. Compare rather than combine.', '',a(REPO+'EXECUTIVE_SUMMARY.md','Root summary')+' · '+a(REPO+'nba-evidence/data/research.json','Pilot results')),
        ('V-03','Independent row-value validation incomplete','Needs review','This audit checked the Jan 5 BOS 92–OKC 105 score and the access FAQ. Other inherited row values and per-row citation relevance were not re-fetched or certified.', '',a(GAMES,'NBA scoreboard')+' · '+a(FAQ,'NBA FAQ')),
        ('V-04','Source usage and bulk rights','Needs review','NBA Stats says its statistics are for viewing and enjoying on NBA.com/Stats, not for personal or academic download. Obtain authorized access before scaled collection.', '',a(FAQ,'NBA FAQ')),
        ('V-05','Research snapshot is stale','Needs review','Inherited score, injury, and leader snapshots are dated Nov 2 or earlier; not verified as current Nov 5 data. Live pregame pricing is not available.', '',a(REPO+'nba-evidence/data/sources.json','Source register')),
        ('V-06','Root verification includes raw vendor HTML','Needs review','engine/verify.py scans data/raw/nba/*.html as if those were site pages, causing three failed checks unrelated to published navigation. Exclude source snapshots in a future owner-approved verifier change; do not call a failing run a pass.', '',a(REPO+'engine/verify.py','Verifier code')),
    ]
    if broken:
        files = ', '.join(escape(x['file']+': '+x['href']) for x in broken[:5])
        flags.append(('V-07','Broken local navigation','Needs repair',f'{len(broken)} inherited broken link(s) found: {files}. Publication requires repair.', '',a(REPO+'nfl/pages/','Affected pages')))
    if missing:
        from collections import Counter
        summary = ', '.join(f'{escape(k)} ({v})' for k,v in sorted(Counter(x['file'] for x in missing).items()))
        flags.append(('V-08','Table rows without external source','Needs review',f'{len(missing)} inherited row(s) lack an HTTPS link: {summary}. Keep factual values unverified until the owning module supplies an exact supporting primary source.', '',a(REPO+'nfl/','Affected module')))
    review = '<div class="eyebrow">Transparent limits</div><h1>Flagged for Review</h1><p class="lede">Open issues are non-blocking for publishing the audit but block unsupported claims. Blank values mean no verified value, not zero.</p>' + table(['ID','Issue','Status','Finding / next action','Unverified value','Official / repository reference'],[(f'<code>{x[0]}</code>',escape(x[1]),f'<span class="badge">{escape(x[2])}</span>',x[3],x[4],x[5]) for x in flags])
    HERE.joinpath('flagged.html').write_text(frame('Flagged for Review','flagged.html',review), encoding='utf-8')
    self_modules, self_missing, self_broken = scan(sorted(HERE.glob('*.html')))
    if self_missing or self_broken:
        raise SystemExit(f'audit site broken: missing rows={self_missing}, links={self_broken}')
    print(f"Inherited: {len(inherited)} pages; NBA {count('rows')} rows ({count('external_source_rows')} HTTPS); {len(missing)} missing source rows; {len(broken)} broken local links. Audit: {sum(s['rows'] for s in self_modules.values())} sourced rows, zero broken links.")

if __name__=='__main__': build()
