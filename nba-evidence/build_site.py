"""Build a static, accessible dashboard. Every data row carries a source link."""
from __future__ import annotations
import csv
import html
import json
import shutil
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
SITE = ROOT / 'site'
DATA = ROOT / 'data'
R = json.loads((DATA / 'research.json').read_text())
SOURCES = json.loads((DATA / 'sources.json').read_text())
FLAGS = json.loads((DATA / 'flags.json').read_text())
REQS = json.loads((DATA / 'requirements.json').read_text())
AUDIT = json.loads((DATA / 'repo_audit.json').read_text())
RECEIPT = json.loads((DATA / 'evidence_receipt.json').read_text())
SOURCE_MAP = {s['id']:s for s in SOURCES}
GAMES = list(csv.DictReader((DATA/'games.csv').open()))
PLAYERS = list(csv.DictReader((DATA/'players.csv').open()))
PAGES = {}
NBA = 'https://www.nba.com/games?date=2025-01-05'
REPO = 'https://github.com/sassnarep3-star/Own4'
ALLOWED = ('nba.com','help.bet365.com','support.fanduel.com','nist.gov','scikit-learn.org','nber.org','ssrn.com','github.com','docs.github.com')

NAV = [('Research',[('index.html','▦','Overview'),('executive-summary.html','▤','Executive summary'),('leaderboard.html','♧','Leaderboard'),('strategies.html','◈','Strategies'),('validation.html','✓','Validation gates')]),
       ('Lines & markets',[('lines.html','↗','Own lines'),('parlays.html','⧉','Parlays'),('props.html','○','Player props'),('correlations.html','⌁','Correlations')]),
       ('Evidence',[('games.html','▦','Game results'),('players.html','♙','Player data'),('sources.html','▧','Source register'),('verification.html','✓','Verification')]),
       ('Governance',[('requirements.html','☷','Requirements'),('repo-audit.html','⌕','Repo audit'),('flagged.html','⚑','Flagged for review'),('methodology.html','ƒ','Methodology')])]


def e(x): return html.escape(str(x),quote=True)

def fmt(x, digits=3):
    if x is None: return '<span class="blank">blank · unverified</span>'
    if isinstance(x,float): return f'{x:.{digits}f}'
    return e(x)

def pct(x,d=1): return '—' if x is None else f'{100*x:.{d}f}%'

def badge(text,kind=''): return f'<span class="badge {kind}">{e(text)}</span>'

def link(url,label='Official source ↗'):
    if not url: return '<span class="blank">unverified</span>'
    return f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">{e(label)}</a>'

def links(urls,label='Official inputs ↗'):
    if isinstance(urls,str): urls=[urls]
    urls=list(dict.fromkeys(urls or []))
    if not urls:return '<span class="blank">unverified</span>'
    if len(urls)==1:return link(urls[0],label)
    return ' '.join(link(u,f'Source {i} ↗') for i,u in enumerate(urls,1))

def table(id,headers,rows):
    head=''.join(f'<th scope="col">{h}</th>' for h in headers+['Reference'])
    body=''.join('<tr>'+''.join(f'<td>{c}</td>' for c in row)+'</tr>' for row in rows)
    return f'''<div class="table-toolbar"><input class="search" type="search" placeholder="Search this table…" aria-label="Search {id}" data-table-search="{id}"><span class="table-count" data-count-for="{id}"></span></div><div class="table-wrap"><table id="{id}"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table><div class="empty" hidden>No matching entries.</div></div>'''

def card(title,content,aside=''):
    return f'<section class="card"><div class="cardhead"><h2>{title}</h2>{aside}</div>{content}</section>'

def notice(text):return f'<div class="notice"><span class="notice-icon">◉</span><div>{text}</div></div>'

def kpi(label,value,note,kind=''):
    return f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-note {kind}">{note}</div></div>'

def prose(text):return f'<div class="prose">{text}</div>'

def source_row(req):
    s=SOURCE_MAP[req['source_id']]
    return [req['id'],e(req['requirement']),badge(req['status'],'green' if req['status'] in ('implemented','delivered','enforced') else 'amber'),e(req['evidence']),link(s['url'])]


def build():
    (SITE / 'data').mkdir(parents=True, exist_ok=True)
    # Overview
    t=R['test']; s=R['sample']
    content=f'''<div class="hero"><span class="badge green">Evidence before edge</span><h2>Build the line.<br>Question the advantage.</h2><p>A transparent NBA research workspace for originating fair lines, testing strategy hypotheses and separating reproducible analysis from unsupported betting claims.</p><div class="actions"><a class="button" href="lines.html">Explore own lines ↗</a><a class="button secondary" href="executive-summary.html">Read the findings</a></div></div>'''
    content+=notice('<strong>No validated betting edge.</strong> The locked 24-game test underperformed its baseline. Official historical prices are unavailable; no betting ROI or rewards are claimed.')
    content+='<div class="kpis">'+kpi('Official game records',s['games'],'8 date samples · Jan 1–8, 2025','good')+kpi('Own historical lines',len(R['predictions']),'15 validation + 24 test','good')+kpi('Qualified strategies','0 / 8','Every release remains gated','warn')+kpi('Rewards awarded','0 pts','1,000-point pool unallocated','warn')+'</div>'
    rows=[]
    for x in R['leaderboard']:
        rows.append([f"#{x['diagnostic_rank']}",f"<strong>{e(x['name'])}</strong>",fmt(x['brier'],4),fmt(x['log_loss'],4),e(x['n']),badge('Diagnostic only','amber'),link(NBA)])
    left=card('Forecast leaderboard',table('overview-rank',['Rank','Model','Brier ↓','Log loss ↓','Games','Status'],rows)+'<p class="source-note">Ranking forecast accuracy is not evidence of betting profitability. Lower is better.</p>',link('leaderboard.html','Full leaderboard →'))
    right=card('The validation standard','<div class="steps"><div class="step"><span class="stepnum">1</span><div><strong>Verify the inputs</strong><p>Official NBA results, explicit source links and arithmetic checks.</p></div></div><div class="step"><span class="stepnum">2</span><div><strong>Freeze the forecast</strong><p>No same-day or future outcomes in the feature set.</p></div></div><div class="step"><span class="stepnum">3</span><div><strong>Price before selection</strong><p>Missing official prices mean no bet, not an assumed −110.</p></div></div><div class="step"><span class="stepnum">4</span><div><strong>Replicate before reward</strong><p>Joint calibration, multiple-testing control and prospective evidence.</p></div></div></div>',link('validation.html','10 gates →'))
    content+=f'<div class="grid2">{left}{right}</div>'
    content+='<h2 style="margin:28px 0 16px">Explore the research</h2><div class="grid3">'
    for href,title,desc in [('lines.html','Own lines','Historical fair spreads, totals and moneylines with full prediction records.'),('parlays.html','Parlays & dependence','Same-game joint estimates and cross-game examples—not multiplied blind.'),('props.html','Player prop combinations','Points, rebounds, assists and PRA experiments with explicit sample limits.'),('correlations.html','Correlation analysis','Computed relationships, scope labels and suppressed short-sample intervals.'),('sources.html','Official source register','Primary NBA, operator and statistical references available for review.'),('flagged.html','Flagged for review','Missing prices, small samples, source irregularities and policy boundaries.')]:
        content+=f'<a class="category" href="{href}"><span class="arrow">↗</span><h3>{title}</h3><p>{desc}</p></a>'
    content+='</div>'
    PAGES['index.html']=('Overview','A disciplined starting point for NBA line origination.',content,'Research / Overview')

    # Executive summary
    summary=f'''<div class="prose"><h2>The headline: a working research system, not a proven edge</h2><p>This release contains {s['games']} official NBA game records, {s['players']} participating-player records from two complete box scores, {len(R['predictions'])} reproducible historical fair-line sets, eight strategy hypotheses and ten release gates. It is a deliberately bounded pilot, not a complete NBA database or a current betting slate.</p><div class="callout"><strong>Decision:</strong> do not deploy capital based on this pilot. No strategy passes all gates; no reward points are awarded. The model's test Brier score is {t['brier']:.4f}, worse than the frozen baseline's {t['baseline_brier']:.4f}.</div><h2>What the evidence supports</h2><ul><li><strong>Reproducibility:</strong> features use earlier dates only; training, validation and test windows are separated. All 100 input records link to official NBA pages.</li><li><strong>Line origination:</strong> shrunk scoring-for/against estimates generate team scores, margins and totals. Logistic probabilities produce zero-margin fair decimal prices. These are model outputs, not sportsbook quotes.</li><li><strong>Dependence matters:</strong> the same-game residual experiment scored {R['sgp']['joint_estimate_brier']:.4f} Brier versus {R['sgp']['independent_brier']:.4f} for multiplying marginals on the same 24 games. That is an exploratory comparison, not proof of a stable joint model.</li><li><strong>Player combinations:</strong> pooled player correlations change after removing a linear minutes effect. Two games cannot identify player-specific conditional distributions or personalized prop value.</li><li><strong>Luck remains:</strong> a proper score, baseline comparison and leakage tests are useful controls. They do not eliminate variance, hidden selection or non-stationarity.</li></ul><h2>What is missing</h2><p>Authorized point-in-time sportsbook quotes, limits and ticket rules; a larger multi-season sample; pregame injury/lineup/rest/venue information; repeated player histories; and a genuinely prospective frozen prediction log. Unsupported values remain blank.</p><h2>Competition design</h2><p>The diagnostic leaderboard ranks probability forecasts on the same locked test set. A separate betting division requires every gate to pass before eligibility. The proposed 1,000-point non-monetary pool would split 60% / 30% / 10% among the top three eligible strategies; with zero eligible strategies, the entire pool remains unawarded. No funded prize is represented.</p><h2>Repository and publication integrity</h2><p>Concurrent sessions added several dashboards while this work was in progress. Their files are preserved. This workspace is isolated under <code>nba-evidence/</code>. The repository audit distinguishes a mechanical scan of every tracked text line from targeted primary-source checks; it does not claim every inherited number was independently re-fetched.</p><h2>Recommended next research sequence</h2><ol><li>Resolve access rights and obtain official operator price history.</li><li>Expand the league-verified, point-in-time dataset without using future information.</li><li>Freeze a future protocol and log every prediction and every research trial.</li><li>Validate singles first; then joint distributions and actual quoted parlay prices.</li><li>Require dependence-aware out-of-sample improvement and prospective replication before any reward or deployment.</li></ol></div>'''
    summary+=card('Evidence and references',table('summary-ref',['Evidence','Scope','Status'],[
        ['Locked forecast test','24 games / 3 dates','Underperformed baseline',link(NBA)],
        ['Official player extracts','38 players / 2 games','Arithmetic checked',link(SOURCE_MAP['NBA-BOSOKC']['url'])],
        ['Historical market prices','No verified records','Blank · unverified',link(SOURCE_MAP['BET365-BB']['url'])],
        ['Selection-bias controls','Project policy','Prospective replication missing',link(SOURCE_MAP['DSR']['url'])]]))
    PAGES['executive-summary.html']=('Executive summary','The findings, decision and limits—without the sales pitch.',summary,'Research / Executive summary')

    # Leaderboard
    content=notice('<strong>Two different questions:</strong> “Which forecast scored better?” and “Which strategy is validated for betting?” This pilot answers only the first, descriptively. Betting eligibility is zero.')
    content+=card('Division A · forecast diagnostics',table('leaderboard',['Rank','Model','Test games','Brier ↓','Log loss ↓','Betting eligible','Reward pts'],[[x['diagnostic_rank'],e(x['name']),x['n'],fmt(x['brier'],4),fmt(x['log_loss'],4),badge('No','amber'),x['reward_points'],link(NBA)] for x in R['leaderboard']]))
    content+=card('Division B · strategy release',table('strategy-rank',['ID','Strategy','Market','Passed gates','Status','Measured ROI','Reward pts'],[[x['id'],e(x['name']),e(x['family']),f"{sum(g['status']=='pass' for g in x['gates'])} / 10",badge('Not eligible','amber'),fmt(None),0,link(x['source_url'])] for x in R['strategies']]))
    content+=card('Reward rule',prose('<p>The research pool is <strong>1,000 non-monetary points</strong>. Only strategies passing all ten gates enter the reward ranking. If at least three qualify, award 600 / 300 / 100 points by frozen prospective risk-adjusted net return, with ties sharing the affected places. If fewer qualify, leave their shares unawarded. This release has zero qualifiers and zero awards.</p><p>No money, token, payment, sportsbook credit or guaranteed prize is offered. Diagnostic Brier rank never substitutes for the release gates.</p>'),link(SOURCE_MAP['DSR']['url'],'Selection-bias reference ↗'))
    PAGES['leaderboard.html']=('Leaderboard','Forecast diagnostics and reward eligibility are deliberately separate.',content,'Research / Leaderboard')

    # Strategies
    rows=[]
    for x in R['strategies']:
        rows.append([x['id'],f"<strong>{e(x['name'])}</strong><br><span class='subtle'>{e(x['family'])}</span>",e(x['signal']),e(x['test_plan']),badge('Not eligible','amber'),fmt(None),link(x['source_url'])])
    content=notice('These are <strong>research hypotheses</strong>, not recommendations. A source supports a definition or method; it does not verify that a strategy is profitable.')
    content+=card('Strategy catalog',table('strategies',['ID','Strategy','Signal / entry rule','Required evidence','Release','Market ROI'],rows))
    content+=card('Selection discipline',prose('<p>Record every candidate and failed experiment. Freeze feature definitions, thresholds and model versions before the evaluation window. Compare against a matched baseline on identical observations. Use the actual available price—not a convenient assumed price—and account for pushes, voids, limits and correlated exposure.</p><p>For parlays, model the joint event. For player combinations, condition on the same player, role and pregame information. A positive correlation is not automatically a positive expected return.</p>'))
    PAGES['strategies.html']=('Strategy catalog','Eight testable hypotheses across singles, parlays and player props.',content,'Research / Strategies')

    # Validation
    content='<div class="kpis">'+kpi('Release gates','10','All must explicitly pass')+kpi('Eligible strategies','0','Fail-closed by design','warn')+kpi('Official price records','0','No assumed −110','warn')+kpi('Prospective tickets','0','Retrospective pilot only','warn')+'</div>'
    content+=card('Gate definitions',table('gates',['Gate','Requirement','Threshold / evidence','Current result','Basis'],[[g['id'],f"<strong>{e(g['name'])}</strong>",e(g['requirement']),badge(g['status'],'green' if g['status']=='pass' else 'amber'),link(SOURCE_MAP['DSR']['url'] if g['id'] in ('G06','G07','G09','G10') else NBA)] for g in R['gates']]))
    matrix=[]
    for x in R['strategies']:
        matrix.append([x['id'],e(x['name'])]+[badge(g['status'],'green' if g['status']=='pass' else 'red' if g['status']=='fail' else 'amber') for g in x['gates']]+[link(x['source_url'])])
    content+=card('Strategy × gate matrix',table('gate-matrix',['ID','Strategy']+[g['id'] for g in R['gates']],matrix))
    content+=notice('A passing provenance or leakage check is not a passing strategy. “Unverified” never counts as “pass.” Flagged items may be published, but they cannot unlock a betting-release claim.')
    PAGES['validation.html']=('Validation gates','No evidence, no eligibility. No exceptions for an attractive backtest.',content,'Research / Validation')

    # Own lines
    rows=[]
    for x in R['predictions']:
        rows.append([e(x['date']),badge(x['split'],'amber' if x['split']=='test' else ''),f"<strong>{e(x['team1'])} / {e(x['team2'])}</strong><br><span class='subtle'>{x['game_id']}</span>",fmt(x['mean1'],1),fmt(x['mean2'],1),fmt(x['spread1'],1),fmt(x['total_line'],1),pct(x['p1']),fmt(x['fair_decimal1']),fmt(x['book_decimal']),e(x['bet_decision']),link(x['source_url'])])
    content=notice('<strong>Historical replay, not today’s picks.</strong> These lines were reconstructed from earlier dates in a January 2025 sample. Fair prices have no sportsbook margin. Official price and price-edge fields remain blank.')
    content+=card('Pre-outcome feature and line ledger',table('own-lines',['Date','Window','Team1 / Team2','Proj. pts 1','Proj. pts 2','Team1 spread','Total line','P(team1)','Fair dec. 1','Book price','Decision'],rows))
    prior_k=R['protocol']['shrinkage_prior_games']; prior_points=R['prior']['team_points']
    content+=card('How the line is made',f'<div class="formula">offₜ = (prior points scored + k·league mean) / (prior games + k)\ndefₜ = (prior points allowed + k·league mean) / (prior games + k)\nE[team1] = (off₁ + def₂) / 2\nE[team2] = (off₂ + def₁) / 2\nmargin = E[team1] − E[team2]\ntotal = E[team1] + E[team2]\np(team1) = frozen logistic(margin)\nfair decimal = 1 / p</div><p class="source-note">k = {prior_k}; training league mean = {prior_points:.4f}. Half-point display lines use floor(x)+0.5. No venue or context adjustment is inferred.</p>',link(SOURCE_MAP['SK-CAL']['url'],'Probability reference ↗'))
    PAGES['lines.html']=('Own NBA lines','Every historical line, its inputs, its window and its abstention.',content,'Lines & markets / Own lines')

    # Parlays
    content=notice('Joint probability is not the product of marginals unless independence is justified. Neither example below has an official ticket price; neither produces a betting ROI.')
    m=R['sgp']
    content+='<div class="kpis">'+kpi('Same-game test events',m['n'],'Favorite + over own total')+kpi('Joint residual Brier',f"{m['joint_estimate_brier']:.4f}",'Exploratory estimate')+kpi('Independence Brier',f"{m['independent_brier']:.4f}",'Matched comparison')+kpi('Training residual r',f"{m['residual_correlation']:.3f}",'23 training pairs · not a copula')+'</div>'
    content+=card('Same-game · favorite + over',table('sgp',['Date','Game','Favorite','P favorite','P over','Joint estimate','Product estimate','Observed hit','Official price'],[[x['date'],f"{x['team1']} / {x['team2']}",x['favorite'],pct(x['p_favorite']),pct(x['p_over']),pct(x['p_sgp']),pct(x['p_sgp_independent']),badge('Hit','green') if x['sgp_hit'] else badge('Miss',''),fmt(None),link(x['source_url'])] for x in R['predictions'] if x['split']=='test']))
    content+=card('Cross-game · disjoint-team examples',table('cross-parlay',['ID','Dates','Leg 1','Leg 2','Product under assumption','Both hit','Ticket price','ROI'],[[x['id'],e(x['date']),e(x['leg1']),e(x['leg2']),pct(x['p_independent_assumption']),badge('Yes','green') if x['hit'] else badge('No','red'),fmt(None),fmt(None),links(x['source_urls'])] for x in R['cross_game']]))
    content+=card('Interpretation',prose('<p>The joint residual method shifts training margin/total residual pairs to each pregame forecast and counts simultaneous hits, with 0.5 smoothing. It preserves the observed training residual pairing but is highly uncertain with 23 pairs. The lower test Brier is a hypothesis-generating result, not a validated advantage.</p><p>Cross-game examples use different dates and no shared teams. Shared league-wide shocks can still create dependence. The examples also reuse teams across separate tickets, so ticket results are not independent observations. No aggregate significance test is applied.</p>'))
    PAGES['parlays.html']=('Parlays & joint probability','Singles first. Joint distributions before combinations.',content,'Lines & markets / Parlays')

    # Props
    content=notice('<strong>Cohort experiments, not personalized prop picks.</strong> Thresholds come from the earlier two-team player sample and are tested on the later two-team sample. Only one game per window is available; role, availability and matchup shifts are not modeled.')
    content+=card('Experimental thresholds and outcomes',table('prop-summary',['ID','Cohort threshold','Train players','Test players','Train joint hit','Test joint hit','Test hits','Official quote','ROI'],[[x['id'],e(x['line']),x['train_n'],x['test_n'],pct(x['train_joint_rate']),pct(x['test_joint_rate']),x['test_hits'],fmt(None),fmt(None),links(x['source_urls'])] for x in R['props']]))
    rows=[]
    for x in R['props']:
        if x['test_binary']:
            b=x['test_binary']
            rows.append([x['id'],e(x['line']),pct(b['p_a']),pct(b['p_b']),pct(b['p_joint']),pct(b['independent_joint']),fmt(b['phi']),fmt(b['joint_lift']),links(x['source_urls'])])
    content+=card('Test-window binary dependence',table('prop-dependence',['ID','Threshold','P(A)','P(B)','Observed joint','A×B','φ','Joint / product'],rows))
    rows=[]
    for p in PLAYERS:
        pra=int(p['points'])+int(p['rebounds'])+int(p['assists'])
        rows.append([p['date'],f"<strong>{e(p['player'])}</strong>",p['team'],p['minutes'],p['points'],p['rebounds'],p['assists'],pra,link(p['source_url'])])
    content+=card('Underlying player evidence',table('prop-players',['Date','Player','Team','MIN','PTS','REB','AST','PRA (derived)'],rows))
    PAGES['props.html']=('Player prop combinations','Observed player production and explicitly limited combo experiments.',content,'Lines & markets / Player props')

    # Correlations
    content=notice('Correlation estimates are <strong>derived calculations</strong>, not official NBA statistics. Confidence intervals are blank because these short, clustered samples do not support the planned dependence-aware interval. No correlation is approved for parlay pricing.')
    rows=[]
    for x in R['correlations']:
        rows.append([f"<strong>{e(x['id'])}</strong>",x['n'],x['clusters'],fmt(x['r']),fmt(x.get('raw_r')),fmt(None),e(x['scope']),links(x['source_urls'])])
    content+=card('Computed relationships',table('correlations',['Relationship','n','Clusters','Adjusted / primary r','Raw r','95% CI','Interpretation boundary'],rows))
    content+=card('Why the adjustment matters',prose('<p>For each player statistic, fit a linear relationship with minutes across the pooled player sample, then correlate the residuals. This removes a shared opportunity proxy, not all role or game-state confounding. Points/rebounds falls from the raw pooled estimate to the minutes-residualized estimate; points/assists is near zero in this tiny sample.</p><p>These are <em>between-player</em> observations in two games. A same-player parlay needs repeated within-player residuals conditional on pregame information. Neither Pearson r nor binary φ alone specifies the joint tail probability that determines a parlay payout.</p>'),link(SOURCE_MAP['NIST-COV']['url'],'Covariance reference ↗'))
    PAGES['correlations.html']=('Correlation analysis','Measured relationships—with their scope and uncertainty intact.',content,'Lines & markets / Correlations')

    # Games
    rows=[]
    for g in GAMES:
        rows.append([g['date'],g['game_id'],f"<strong>{g['team1']}</strong>",g['score1'],f"<strong>{g['team2']}</strong>",g['score2'],int(g['score1'])+int(g['score2']),badge(g['status'],'green')])
    # add source cell
    rows=[row+[link(g['source_url'])] for row,g in zip(rows,GAMES)]
    content=notice('Team1/team2 preserve official scoreboard display order. Home/away is not inferred. Final scores include the overtime shown by the official page. This is an eight-date convenience sample.')
    content+=card('Official final-score ledger',table('games',['Date','Game ID','Team1','Pts1','Team2','Pts2','Total (derived)','Status'],rows))
    PAGES['games.html']=('Official game results','62 final scores, each linked to its exact NBA date page.',content,'Evidence / Games')

    # Players
    rows=[[p['date'],f"<strong>{e(p['player'])}</strong>",p['team'],p['minutes'],p['points'],p['rebounds'],p['assists'],p['game_id'],link(p['source_url'])] for p in PLAYERS]
    content=notice('Only players who appeared in the two inspected box scores are included. DNP is not encoded as a zero-stat performance. Milwaukee’s published minutes sum to 240:01; the discrepancy is retained and flagged.')
    content+=card('Participating-player ledger',table('players',['Date','Player','Team','MIN','PTS','REB','AST','Game ID'],rows))
    totals=list(csv.DictReader((DATA/'team_totals.csv').open()))
    content+=card('Official team-total cross-check',table('team-totals',['Game','Team','PTS','REB','AST','Player sums'],[[t['game_id'],t['team'],t['points'],t['rebounds'],t['assists'],badge('Match','green'),link(t['source_url'])] for t in totals]))
    PAGES['players.html']=('Official player data','38 participating-player records from two complete box scores.',content,'Evidence / Players')

    # Sources
    content=notice('“Verified” means the cited primary page was read and the stated claim was checked on the recorded date. It does not mean the source endorses this project, its model or any betting strategy. Dynamic pages can change.')
    content+=card('Primary-source register',table('sources',['ID','Publisher / title','Checked','What it supports','Method / boundary','Status'],[[s['id'],f"<strong>{e(s['publisher'])}</strong><br>{e(s['title'])}",s['checked_on'],e(s['supports']),e(s['method']),badge(s['status'],'green'),link(s['url'],'Read official page ↗')] for s in SOURCES]))
    content+=card('Exact game-source coverage',table('date-sources',['Date','Games inspected','Source type','Verification'],[[d,sum(g['date']==d for g in GAMES),'NBA official date scoreboard','All displayed result chunks read',link('https://www.nba.com/games?date='+d)] for d in sorted({g['date'] for g in GAMES})]))
    PAGES['sources.html']=('Source register','Primary sources, exact links and explicit verification boundaries.',content,'Evidence / Sources')

    # Verification
    content='<div class="kpis">'+kpi('Input records',len(R['source_rows']),'62 games + 38 players','good')+kpi('Evidence checks',f"{RECEIPT['passed']}/{RECEIPT['total']}",'Schema, joins, totals and hashes','good')+kpi('Unit tests','22','Pricing, settlement, statistics, leakage','good')+kpi('Official market records','0','No invented betting returns','warn')+'</div>'
    content+=notice('CI verifies the committed extracts and reproducibility. It does <strong>not</strong> independently re-fetch NBA truth. Primary-page inspection was performed separately with the page-fetch tool and is recorded here.')
    content+=card('Input provenance receipts',table('provenance',['Type','Record','Inspection date','Verification scope','Record SHA-256'],[[x['kind'],x['id'],x['checked_on'],e(x['verification']),f"<code>{x['normalized_record_sha256'][:16]}…</code>",link(x['source_url'])] for x in R['source_rows']]))
    content+=card('Automated evidence checks',table('evidence-checks',['Check','Result','Detail','Reference'],[[e(c['name']),badge('Pass','green') if c['pass'] else badge('Fail','red'),e(c['detail']),link(NBA)] for c in RECEIPT['checks']]))
    content+=card('Reproduce',prose('<p>From <code>nba-evidence/</code>, run the commands below. Python 3.11+; no third-party runtime dependencies.</p><div class="formula">python collect_evidence.py\npython -m unittest discover -s tests -v\npython -m nba_lab.analysis\npython build_site.py\npython verify_site.py</div><p>The source CSVs and protocol are the inputs. <code>research.json</code>, the static pages and verification reports are generated outputs. Hashes identify normalized local records, not a hash of a remote NBA page.</p>'))
    PAGES['verification.html']=('Verification ledger','What was checked, how it was checked and what remains unverified.',content,'Evidence / Verification')

    # Requirements
    content=card('Requirements traceability',table('requirements',['ID','Requirement','Status','Evidence / boundary'],[source_row(x) for x in REQS]))
    content+=notice('Requirement delivery is not the same as strategy validation. A complete dashboard can honestly report that no betting edge has been established.')
    PAGES['requirements.html']=('Requirements register','Every requested capability mapped to evidence and its delivery boundary.',content,'Governance / Requirements')

    # Repo audit
    content=notice(f"<strong>{AUDIT['files']} tracked files · {AUDIT['text_lines']:,} text lines scanned.</strong> This is a mechanical full-repository inventory plus targeted official cross-checks—not a claim that every inherited numeric row was externally re-verified.")
    content+=card('Irregularities and review requests',table('repo-findings',['ID','Finding','Detail','Location / reference'],[[x['id'],f"<strong>{e(x['title'])}</strong>",e(x['detail']),link(x['source_url'],'Repository record ↗')+'<br>'+link(x['official_reference'],'Primary reference ↗')] for x in AUDIT['findings'] if 'id' in x]))
    content+=card('Targeted primary-source cross-checks',table('repo-crosschecks',['Subject','Observed result','Verification boundary'],[[e(x['subject']),e(x['result']),'Selected records only; not universal re-verification',link(x['source_url'])] for x in AUDIT['primary_crosschecks']]))
    content+=card('Inherited command results',table('repo-commands',['Command','Exit','Interpretation','Reference'],[[f"<code>{e(x['command'])}</code>",x['exit'],('Passed' if x['exit']==0 else 'Review required; archive lacks Git history and root directory coverage is incomplete'),link(REPO+'/actions')] for x in json.loads((DATA/'inherited_checks.json').read_text())]))
    content+=card('Tracked-file inventory',table('repo-inventory',['Path','Lines','Bytes','SHA-256','Official URL mentions','Other URL mentions'],[[f"<code>{e(x['path'])}</code>",fmt(x['lines']),x['bytes'],f"<code>{x['sha256'][:16]}…</code>",x['official_urls'],x['other_urls'],link(x['source_url'],'Repository file ↗')] for x in AUDIT['inventory']]))
    PAGES['repo-audit.html']=('Repository audit','Preserve concurrent work. Make verification gaps visible.',content,'Governance / Repo audit')

    # Flags
    content=notice('<strong>Flagged for Review is non-blocking for site publication.</strong> These items are not hidden in a log. They remain visible here with source links and may block a specific factual or betting claim.')
    content+=card('Open review register',table('flags',['ID','Severity','Finding','Detail','Next action','Status'],[[x['id'],badge(x['severity'],'amber'),f"<strong>{e(x['title'])}</strong>",e(x['detail']),e(x['action']),badge('Needs review','amber'),link(x['source_url'])] for x in FLAGS]))
    PAGES['flagged.html']=('Flagged for review','Unverified values, source irregularities and methodological limits.',content,'Governance / Flagged for review')

    # Methodology
    content=prose('''<h2>1. Source and target definitions</h2><p>Use official NBA final scores and participating-player box scores. Preserve display order rather than inventing home/away. Keep overtime in final scores. The target for probability scoring is a team1 win; it is not a home-win target. Player PRA is the arithmetic sum of points, rebounds and assists.</p><h2>2. Chronology and feature construction</h2><p>January 1–3, 2025 is training (23 games); January 4–5 is validation (15); January 6–8 is locked test (24). All games on a date are predicted before any result from that date updates team states. Training means and logistic coefficients are frozen before validation. Later outcomes may update scoring histories for subsequent dates, but never the current date's features.</p><h2>3. Probability and price</h2><p>Shrink each team's scoring-for and scoring-against means toward the training league mean with five prior games. Fit a two-parameter L2 logistic model on training-only pregame margin features. Fair decimal odds equal 1/p. A sportsbook selection additionally needs an official executable price and a predeclared minimum edge; none is available here.</p><h2>4. Evaluation</h2><p>Use Brier score and log loss for probabilities, plus margin/total MAE for point forecasts. Compare with the frozen training team1 base rate and training total on exactly the same test games. A lower Brier score alone does not establish calibration or profitability. Show reliability bins and sample counts before claiming calibration.</p><div class="formula">Brier = mean((p − y)²)\nLog loss = −mean(y·log(p) + (1−y)·log(1−p))\nEV per unit = p·(decimal−1) − (1−p)\nFair decimal = 1/p</div><h2>5. Correlation and combinations</h2><p>Pearson correlation uses sample covariance normalized by both standard deviations. Player residuals remove a fitted linear minutes relationship across the pooled sample. Binary dependence reports observed joint hits, the product of marginals, φ and joint/product lift. These are descriptive—not a full joint distribution. Same-game experiments resample paired training residuals; cross-game products are explicitly conditional on an unverified independence assumption.</p><h2>6. Skill, luck and selection</h2><p>There is no honest way to remove all luck. Freeze the full trial registry, prevent leakage, use matched baselines, resample whole dates rather than individual games, control the complete hypothesis family, and require prospective multi-season replication. Suppress the planned bootstrap interval below 20 distinct dates. Even a valid interval would not capture every regime change or hidden dependency.</p><p>The Holm primitive is tested but no family-wise significant strategy claim is made: the pilot lacks the required sample and price series. Deflated Sharpe is not computed from invented returns. The financial-paper thresholds are not copied into NBA as official facts.</p><h2>7. Settlement and risk</h2><p>Settlement must use the operator and market rules in force when the price was accepted. Pushes and voids can reduce a ticket's multiplier; a loss loses the ticket. The engine tests these mechanics but does not assert universal sportsbook rules. Kelly is capped at 1% in the research primitive and is not a recommendation to stake. No actual wager is placed.</p><h2>8. Release policy</h2><p>All ten gates must pass. Missing evidence is unverified, never a pass. Forecast diagnostics may be ranked without rewards; betting eligibility and reward allocation require the full evidence chain. The current release has no eligible strategy.</p>''')
    content+=card('Method references',table('method-refs',['Topic','Primary reference','Use'],[[x['id'],e(x['title']),e(x['supports']),link(x['url'])] for x in SOURCES if x['id'] in ('NIST-COV','NIST-WILSON','SK-TIME','SK-CAL','SK-METRICS','NBER-MULTIPLE','DSR')]))
    PAGES['methodology.html']=('Methodology','Definitions, equations, evaluation policy and reasons to abstain.',content,'Governance / Methodology')

    # Write common shell
    for filename,(title,subtitle,content,path) in PAGES.items():
        nav=''
        for group,items in NAV:
            nav+=f'<div class="navgroup"><div class="navlabel">{group}</div>'
            for href,icon,label in items:
                active=' active' if href==filename else ''
                current = ' aria-current="page"' if active else ''
                nav+=f'<a class="navlink{active}" href="{href}"{current}><span class="icon" aria-hidden="true">{icon}</span>{label}</a>'
            nav+='</div>'
        actions='<div class="actions"><a class="button secondary" href="data/research.json" download>↓ Research data</a><a class="button" href="flagged.html">Review flags ↗</a></div>' if filename=='index.html' else '<div class="actions"><a class="button secondary" href="sources.html">View sources ↗</a></div>'
        doc=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Evidence-first NBA line origination research, official source links and explicit validation gates."><title>{e(title)} · NBA Evidence</title><link rel="stylesheet" href="assets/style.css"><link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'%3E%3Crect width='40' height='40' rx='10' fill='%23143c32'/%3E%3Ctext x='20' y='27' text-anchor='middle' font-size='24' fill='white'%3EN%3C/text%3E%3C/svg%3E"></head><body><a class="skip-link" href="#main">Skip to content</a><aside class="sidebar" aria-label="Main navigation"><a class="brand" href="index.html"><span class="brandmark">N</span><span>NBA Evidence<small>RESEARCH WORKSPACE</small></span></a>{nav}<div class="sidebar-foot">Independent research.<br>No sportsbook affiliation.<br><br>Snapshot · 02 Nov 2026<br>Historical sample · Jan 2025</div></aside><div class="main"><header class="topbar"><button class="mobile-menu" aria-label="Open navigation" aria-expanded="false">☰</button><div class="breadcrumb">{e(path)}</div><div class="topmeta"><span><i class="statusdot"></i>Static research snapshot</span><span>Official-source linked</span></div></header><main class="content" id="main"><div class="pagehead"><div><div class="eyebrow">NBA line origination research</div><h1>{e(title)}</h1><p class="lede">{e(subtitle)}</p></div>{actions}</div>{content}<footer class="footer"><span>NBA Evidence · Session 91dfd6a4 · Model outputs are not official NBA lines.</span><span>Research only · No wagering execution · <a href="flagged.html">Limitations & review</a></span></footer></main></div><script src="assets/app.js"></script></body></html>'''
        (SITE/filename).write_text(doc,encoding='utf-8')
    (SITE/'.nojekyll').write_text('')
    shutil.copy(DATA/'research.json',SITE/'data/research.json')
    for name in ('games.csv','players.csv','sources.json','flags.json','requirements.json','repo_audit.json','evidence_receipt.json'):
        shutil.copy(DATA/name,SITE/'data'/name)
    write_docs()
    print(f'Built {len(PAGES)} static pages')


def write_docs():
    t=R['test']
    text=f'''# NBA Evidence — Executive Summary

## Decision

**No validated betting edge. No strategy released. No rewards awarded.**

This is a bounded, reproducible research pilot—not a current betting slate or a complete NBA database.

## What was built

- {R['sample']['games']} official final scores from eight NBA date pages, January 1–8, 2025.
- {R['sample']['players']} official participating-player rows from two complete box scores.
- {len(R['predictions'])} historical fair-line sets: 15 validation and 24 locked test games.
- Eight strategy hypotheses across singles, cross-game parlays, same-game parlays and player-prop combinations.
- Ten fail-closed release gates; a diagnostic leaderboard; a 1,000-point non-monetary reward pool with zero awards.
- A source-linked static dashboard, input receipts, unit tests and a repository audit.

## Findings

- Test Brier: **{t['brier']:.4f}**, versus **{t['baseline_brier']:.4f}** for the frozen training team1 base rate. The model underperformed.
- Test log loss: **{t['log_loss']:.4f}**, versus **{t['baseline_log_loss']:.4f}** for the baseline.
- Margin MAE: **{t['margin_mae']:.3f}** points. Total-line MAE: **{t['total_mae']:.3f}**, versus **{t['baseline_total_mae']:.3f}** for the training mean. This tiny difference is not evidence of edge.
- Same-game joint residual Brier: **{R['sgp']['joint_estimate_brier']:.4f}**, versus **{R['sgp']['independent_brier']:.4f}** for a product estimate. Exploratory only; 23 training residual pairs and 24 test events.
- Player correlations are pooled between-player estimates from two games, not within-player parlay dependence. Short-sample confidence intervals are suppressed.

## Missing evidence

No verified historical executable sportsbook quotes, limits or accepted-ticket rules. No large multi-season point-in-time dataset, pregame context features, repeated player histories or prospective frozen ticket log. Market ROI and personalized prop prices remain blank.

Luck cannot be eliminated. Leakage controls, baselines, dependence-aware evaluation, a complete trial registry and prospective replication can reduce false discoveries; none proves certainty.

## Sources and verification

Every input row links to an official NBA page. The primary pages were read on 2026-11-02. CI checks the committed extracts, arithmetic, schema, source coverage and reproducibility; it does not independently re-fetch remote truth. See the source register and verification ledger.

The Milwaukee player-minute values sum to 240:01. This source irregularity is retained and flagged; points/rebounds/assists reconcile.

## Competition

Forecast diagnostics are ranked separately from betting eligibility. All ten gates must pass before a strategy can receive rewards. The proposed 60/30/10 allocation of 1,000 research points is non-monetary and currently entirely unawarded.

## Repository coordination

Concurrent work is preserved in its original namespaces. This session works only in `nba-evidence/` plus its isolated workflow and append-only coordination records. Arena's fixed branch constraint is documented. The repository audit scans every tracked text line but does not claim every inherited numeric row was externally re-verified.

## Next steps

1. Resolve authorized access to official operator price history and expanded league data.
2. Freeze a genuinely prospective protocol and record every trial.
3. Validate singles against matched baselines and actual prices.
4. Validate joint distributions and quoted parlay payouts before combinations.
5. Require multi-season replication and explicit risk/execution checks before rewards or deployment.

Research only; not wagering advice or an offer of prizes.
'''
    (ROOT/'docs/EXECUTIVE_SUMMARY.md').write_text(text)
    (ROOT/'README.md').write_text('''# NBA Evidence\n\nEvidence-first NBA line-origination pilot. Open `site/index.html` or the published GitHub Pages workspace.\n\n## Reproduce\n\nPython 3.11+, standard library only:\n\n```sh\npython collect_evidence.py\npython -m unittest discover -s tests -v\npython -m nba_lab.analysis\npython audit_repo.py\npython build_site.py\npython verify_site.py\n```\n\nRun from this directory. `audit_repo.py` scans the enclosing Git checkout without editing peer files. The static site is committed so legacy root-based Pages can serve it without a build step.\n\n## Read first\n\n- `docs/EXECUTIVE_SUMMARY.md`\n- `docs/METHODOLOGY.md`\n- `docs/REQUIREMENTS.md`\n- `docs/SOURCES.md`\n- `site/flagged.html`\n\nNo validated betting edge, official historical market prices, personalized player forecasts, actual wagers or funded rewards are claimed. Missing values stay null. See the published Flagged for Review page.\n''')
    # Methodology and source documents are generated from the same content as the site.
    import re
    meth=PAGES['methodology.html'][2]
    plain=re.sub('<[^>]+>','\n',meth)
    (ROOT/'docs/METHODOLOGY.md').write_text('# Methodology\n\n'+'\n'.join(l.strip() for l in plain.splitlines() if l.strip())+'\n')
    (ROOT/'docs/SOURCES.md').write_text('# Primary source register\n\n'+'\n'.join(f"- [{s['publisher']}: {s['title']}]({s['url']}) — checked {s['checked_on']}. {s['supports']}" for s in SOURCES)+'\n')
    (ROOT/'docs/REQUIREMENTS.md').write_text('# Requirements traceability\n\n| ID | Requirement | Status | Evidence |\n|---|---|---|---|\n'+'\n'.join(f"| {r['id']} | {r['requirement']} | {r['status']} | {r['evidence']} |" for r in REQS)+'\n')

if __name__=='__main__':build()
