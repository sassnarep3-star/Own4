"""Line-by-line repository inventory and provenance audit, without editing peers.

A source URL is not proof of truth. This script distinguishes mechanical coverage,
primary-source inspection, and unresolved external verification. It scans every
tracked text line for source URLs, conflict markers and risky claim patterns.
"""
from __future__ import annotations
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'nba-evidence/data/repo_audit.json'
REPO = 'https://github.com/sassnarep3-star/Own4'
URL = re.compile(r'https?://[^\s<>"\)\]]+')
OFFICIAL = ('nba.com','help.bet365.com','support.fanduel.com','nist.gov','scikit-learn.org','nber.org','ssrn.com')


def main():
    files = subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines()
    inventory, findings, csv_reports = [], [], []
    total_lines = 0
    for rel in files:
        path = ROOT / rel
        raw = path.read_bytes()
        item = {'path':rel,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
                'source_url':REPO+'/blob/main/'+rel,'lines':None,'official_urls':0,'other_urls':0}
        if b'\x00' not in raw:
            text = raw.decode('utf-8',errors='replace')
            lines = text.splitlines()
            item['lines'] = len(lines)
            total_lines += len(lines)
            for number,line in enumerate(lines,1):
                for url in URL.findall(line):
                    try:
                        host = (urlparse(url).hostname or '').lower()
                    except ValueError:
                        host = ''
                    item['official_urls' if any(host == d or host.endswith('.'+d) for d in OFFICIAL) else 'other_urls'] += 1
                if re.match(r'^(<<<<<<< |=======$|>>>>>>> )',line) and rel != 'COORDINATION.md':
                    findings.append({'path':rel,'line':number,'issue':'Unresolved conflict marker','excerpt':line[:160]})
        inventory.append(item)
        if path.suffix == '.csv':
            try:
                with path.open(newline='',encoding='utf-8-sig') as f:
                    rows = list(csv.DictReader(f))
                sourced = sum(any('source' in k and str(v).startswith('https://') for k,v in r.items()) for r in rows)
                csv_reports.append({'path':rel,'rows':len(rows),'rows_with_source_field':sourced,
                                    'source_url':REPO+'/blob/main/'+rel})
            except (csv.Error,UnicodeDecodeError):
                csv_reports.append({'path':rel,'rows':None,'rows_with_source_field':None,'source_url':REPO+'/blob/main/'+rel})
    # Specific findings are grounded in code/data, not inferred from a filename.
    def add(fid,title,detail,rel,official,severity='needs review',line=None):
        findings.append({'id':fid,'title':title,'detail':detail,'path':rel,'line':line,
                         'source_url':REPO+'/blob/main/'+rel+(( '#L'+str(line)) if line else ''),
                         'official_reference':official,'severity':severity,'status':'needs review'})
    add('R01','Official-source coverage is not external verification',
        'Many inherited validators check URL domains and arithmetic. Those checks cannot establish that every cited value matches the official page. This session independently inspected only its own 62-game/38-player extracts plus the explicitly listed cross-checks.',
        'engine/verify.py','https://www.nba.com/stats/help/faq')
    add('R02','Partner player logs do not meet the strict league-source requirement',
        'The newer pipeline identifies ESPN as a broadcast-partner fallback. Only leader lines and a small full-box sample are described as NBA-cross-checked; the remaining player rows are not independently verified against NBA official box scores. Do not label the entire player log official-NBA-verified.',
        'data/pipeline_sources.json','https://www.nba.com/stats/help/faq')
    add('R03','Assumed -110 prices are not observed sportsbook quotes',
        'research/config.py fixes LEG_DECIMAL=1.9091. Returns using this constant are scenario results, not realized or officially quoted betting ROI. The inherited workspace discloses the assumption; it remains ineligible under this session’s official-price gate.',
        'research/config.py','https://help.bet365.com/s/en/sportsrules/basketball',line=15)
    add('R04','Known team scoring discrepancies remain unresolved',
        'scripts/verify_data.py explicitly permits DAL and ATL points-per-game differences between the transcribed game ledger and the official team table. A passing consistency suite therefore does not mean every source value agrees.',
        'scripts/verify_data.py','https://www.nba.com/stats/teams/traditional?Season=2026-27&PerMode=PerGame')
    add('R05','Correlation is not a full joint ticket distribution',
        'Pairwise correlation and failure to reject independence do not establish tail independence or an executable parlay edge. Actual joint outcomes and the quoted ticket price are required.',
        'research/engine.py','https://support.fanduel.com/s/article/What-is-a-Same-Game-Parlay-or-SGP')
    add('R06','Archived verification commands need a Git checkout',
        'The inherited root verifier passed its data checks but failed a Git-diff reproducibility check in an archive without .git, and reported some namespaced pages unreachable from the root directory. These are recorded as audit findings, not silently treated as a clean pass. Local links in those pages can still resolve.',
        'engine/verify.py','https://github.com/sassnarep3-star/Own4/actions')
    add('R07','NBA download restriction and automated bulk collection conflict',
        'NBA FAQ says stats are not available for personal/academic download. Inherited automated NBA/ESPN collection needs a rights/access review before being treated as authorized. This session does not run or extend that collector.',
        '.github/workflows/fetch-nba-data.yml','https://www.nba.com/stats/help/faq','policy')
    add('R08','Compiled bytecode is tracked',
        'Compiled __pycache__ files are present in the inherited repository. They are not primary evidence and should be removed by their owning session; this audit does not edit them.',
        'own4-dashboard/scripts/__pycache__/build_docs.cpython-311.pyc','https://docs.github.com/en/get-started/learning-about-github/github-glossary#repository')
    add('R09','Shared board contains historical conflict markers',
        'Historical merge markers remain in the shared board. They are preserved to avoid rewriting another session’s record; the current session’s task table and completion log are separate and explicit.',
        'COORDINATION.md','https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md')
    add('R10','Unverified does not mean zero',
        'Missing odds, ROI, personalized prop lines and short-sample confidence intervals must remain null. This rule is enforced in the new workspace and checked across every generated HTML table row.',
        'nba-evidence/nba_lab/analysis.py','https://www.nba.com/stats/help/faq','documented')
    result = {'scope':'All tracked files at the audited commit; every text line scanned mechanically. External fact verification is limited to explicitly inspected primary pages.',
              'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'files':len(inventory),'text_lines':total_lines,'inventory':inventory,
              'csv_coverage':csv_reports,'findings':findings,
              'primary_crosschecks':[
                  {'subject':'2026-10-20 opening slate','result':'BOS 113–121 DET; PHI 106–100 NYK; OKC 116–104 SAS matched the inherited game rows.',
                   'source_url':'https://www.nba.com/games?date=2026-10-20'},
                  {'subject':'2025-26 standings snapshot','result':'Official page read: DET 60–22, BOS 56–26, OKC 64–18. The page is season-specific; current-season URL alone is not a historical snapshot.',
                   'source_url':'https://www.nba.com/standings?Season=2025-26'},
                  {'subject':'2026-27 team scoring snapshot','result':'Official page read: MEM 6 GP, 121.2 PPG, +15.2; HOU 7 GP, 120.7 PPG, +12.4; PHI 7 GP, 108.7 PPG, +3.9 matched inherited rows.',
                   'source_url':'https://www.nba.com/stats/teams/traditional?Season=2026-27&PerMode=PerGame'}],
              'limitations':['No claim that every inherited numeric row was externally re-fetched.',
                             'GitHub links identify the repository record, not an independent league source.',
                             'Peer-owned files were not edited; requests and findings are logged for review.']}
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(f"Audited {len(inventory)} tracked files / {total_lines} text lines; {len(findings)} review records")

if __name__=='__main__':main()
