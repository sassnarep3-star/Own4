#!/usr/bin/env python3
"""Build the static NFL research dashboard. No network requests or data scraping."""
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NFL = 'https://www.nfl.com/stats/'
RULES = 'https://operations.nfl.com/rules-officiating/2026-nfl-rulebook'
INJ = 'https://www.nfl.com/injuries/'
TERMS = 'https://www.nfl.com/legal/terms/'
NGS = 'https://nextgenstats.nfl.com/stats/receiving'
SK = 'https://scikit-learn.org/stable/modules/model_evaluation.html'
CV = 'https://scikit-learn.org/stable/modules/cross_validation.html'
CAL = 'https://scikit-learn.org/stable/modules/calibration.html'
NIST = 'https://www.itl.nist.gov/div898/handbook/eda/section3/eda35c.htm'
STAND = 'https://www.nfl.com/standings/division/2025/reg'
SUB = 'https://www.nfl.com/legal/subscriptions_terms'

def link(url, label='Official source'):
    return f'<a href="{escape(url, quote=True)}">{escape(label)}</a>'

def table(headers, rows):
    h = ''.join(f'<th scope="col">{escape(c)}</th>' for c in headers)
    r = ''.join('<tr>' + ''.join(f'<td>{c}</td>' for c in row) + '</tr>' for row in rows)
    return f'<div class="scroll"><table><thead><tr>{h}</tr></thead><tbody>{r}</tbody></table></div>'

def rows(data):
    return [[*(escape(x) for x in row[:-1]), link(row[-1])] for row in data]

pages = {}
pages['index.html'] = ('Executive summary', '''<div class="hero"><p class="eyebrow">OWN4 / NFL RESEARCH</p><h1>Better questions.<br><span>Before better lines.</span></h1><p>A disciplined research program for NFL singles, parlays and player props—built to separate evidence from speculation.</p><a class="button" href="strategies.html">Explore the strategies →</a></div><div class="metrics"><div><b>Research only</b><span>Strategy status</span></div><div><b>Not measured</b><span>NFL skill & correlations</span></div><div><b>Not operational</b><span>Rewards & live lines</span></div></div><h2>The executive view</h2><p>Use the official league record to define outcomes, then use permitted point-in-time data and historical offered prices to build and test forecasts. NFL rules do not establish a betting edge; a source link on a proposal is background, not proof of performance.</p>''' + table(['Priority','Finding / next action','Source'], rows([
('01 · Data rights','NFL.com terms restrict systematic retrieval to create collections without prior written consent. Do not build a scraping pipeline on the assumption of permission.',TERMS),
('02 · Forecast first','Test game and player hypotheses against frozen simple baselines using proper scores on future data. No NFL model or validated selections are present.',SK),
('03 · Joint risk','For parlays, price the joint event and account for settlement; correlation and probability of joint success are different quantities. No NFL dependence estimate is verified here.',NGS),
('04 · Rewards','Reward design is only a proposal; no pool, operator, entry, or actual leaderboard exists. Luck cannot be eliminated, only quantified and controlled.',CV),
])) + '''<div class="callout"><strong>Decision today: no strategy qualifies.</strong> Market prices, licensed point-in-time history, evaluated NFL models and independent prospective results are missing. See <a href="review.html">Flagged for Review</a>.</div><p class="muted">Not betting advice. No odds, returns, correlation coefficients, or reward amounts have been invented.</p>''')

pages['strategies.html'] = ('Strategies', '''<p class="eyebrow">01 / SIGNAL RESEARCH</p><h1>Strategy candidates</h1><p>Each is a testable hypothesis, not an observed NFL effect. Sources provide sport context only; none confirms predictive power.</p>''' + table(['ID / market','Proposed signal and forecast','Baseline and disqualifier','Status','Source'], rows([
('S1 · Moneyline','Opponent-adjusted team strength with shrinkage and pregame availability; forecast win / tie / loss probabilities.','Preseason or rolling team-strength baseline; reject if improvement does not persist in held-out data.','Research',NFL),
('S2 · Spread','Model full score-margin distribution, including integer outcomes and tie/push probabilities.','Compare with simple pregame margin distribution; reject without calibrated tail probabilities and real settlement terms.','Research',RULES),
('S3 · Total','Model joint team scores, conditional on offensive/defensive strength and pregame conditions.','Compare with a frozen historical score distribution; reject if game-level calibration fails.','Research',RULES),
('S4 · Single player prop','Model participation and opportunities first, then conditional production. Use only timestamped rosters and injury status.','Compare with a trailing player baseline fitted before cutoff; reject if inactive/void treatment or source timing is unknown.','Research',INJ),
('S5 · Cross-game parlay','Jointly forecast selected legs; shared news, teams and schedule dependencies must be evaluated.','Compare direct joint probabilities against any independence model; reject without actual payout and settlement rules.','Research',NFL),
('S6 · Same-game player combo','Simulate shared game scenarios and player opportunity allocation, preserving shared-team and game dependence.','Compare held-out joint forecasts against marginal-product baseline; reject if joint calibration or offered payout is missing.','Research',NGS),
])) + '''<h2>Fair pricing specification</h2><p>For a binary no-push event with probability p, fair decimal odds are 1/p. With push and void outcomes, use the full settlement-state payout distribution; 1/p alone is not sufficient. Compare expected net return against the actual executable price, with all settlement terms and fees. Model prices are derived estimates—not NFL-published facts—and none are available here.</p>''')

pages['validation.html'] = ('Validation & leaderboard', '''<p class="eyebrow">02 / GOVERNANCE</p><h1>Validation &amp; leaderboard</h1><p>Proposed gates are requirements, not claims about results. Freeze thresholds, minimum effective sample size, family of hypotheses and primary endpoint before viewing the final test.</p>''' + table(['Gate','Pass requirement','Current','Official context'], rows([
('G1 · Rights and lineage','Permission for collection and publication; retain immutable source, revision and as-of time.','Not established',TERMS),
('G2 · Time integrity','At each prediction cutoff, use only data available then. Split chronologically; keep all outcomes from the same game in one fold.','No dataset',CV),
('G3 · Reproducibility','Version code, inputs, rules, timestamps and random seeds; record all trial variants, failed or not.','No NFL trial',NFL),
('G4 · Baselines & calibration','Predeclare baseline and loss; compare matched forecasts using Brier or log loss; examine calibration and coverage separately.','No NFL forecasts',SK),
('G5 · Statistical uncertainty','Estimate uncertainty on paired loss differences with blocks at game/week or season as appropriate; report sample size and sensitivity.','Not evaluated',NIST),
('G6 · Selection & multiplicity','Register model families and selection rules; correct for multiple testing; retain an untouched final test.','Not evaluated',CV),
('G7 · Settlement & price','Record time, bookmaker, offered price, limits and rule version; include pushes, voids, overtime and corrections. Score net returns only when verifiable.','No price archive',RULES),
('G8 · Joint outcomes','For combinations evaluate held-out joint calibration and actual repriced payout; test conditional dependence and sparse regimes.','No joint sample',NGS),
('G9 · Prospective replication','Freeze model and candidate universe; evaluate on a later independent period without retuning.','Not performed',CV),
('G10 · Competition integrity','Specify lawful operator, funding, eligible entrants, conflict and tie rules, cutoffs, equal access and disqualification appeals.','Not implemented',TERMS),
])) + '''<h2>Proposed ranking policy</h2><p>Qualify only when all applicable gates pass. Rank matched out-of-sample forecasts by improvement in mean proper loss versus the same baseline, lower loss being better; display uncertainty and eligible sample size. Compare separate market cohorts, not unlike prop and game targets. Treat ties as unresolved if the preregistered tie rule says so. Rewards require separate funding and legal approval; scores do not guarantee profit.</p><div class="callout">Randomness is irreducible. Forecast scores, clustered uncertainty, multiple-testing controls and prospective replication help distinguish skill from noise; they cannot prove an individual result was luck-free.</div>''')

pages['correlations.html'] = ('Correlation & joint risk', '''<p class="eyebrow">03 / DEPENDENCE</p><h1>Correlation &amp; joint risk</h1><p>All numeric result cells below are intentionally blank: no official NFL coefficient for the specified population and conditioning has been verified. An official statistics portal is a source of context, not evidence for a calculated value.</p>''' + table(['Pair / target','Coefficient','N','Protocol / limitation','Source'], rows([
('Receptions ↔ receiving yards','','','Same player-game; Pearson and rank correlations across a defined population; exclude or separately handle nonparticipants.',NGS),
('Quarterback passing yards ↔ receiver yards','','','Same team-game; identify actual quarterback, target player, cutoff and player participation.','https://www.nfl.com/stats/player-stats/'),
('Game total ↔ player yardage','','','Game-level observations; conditional results and prespecified strata, not a universal coefficient.',NFL),
('Team win ↔ spread outcome','','','Binary outcomes and explicit pushes; coefficient alone does not identify every settlement payout.',RULES),
('Two prop overs · joint probability','','','Measure joint hit rate and calibration directly; report P(A and B) versus P(A)P(B), with game/week clustered intervals.',NGS),
])) + '''<h2>Why correlation is not a parlay price</h2><p>For binary legs, P(A and B) = P(A)P(B) + Cov(1A, 1B). If both variances are nonzero, covariance equals phi × √[pA(1−pA)pB(1−pB)]. Estimates vary by line, player, availability and game state. Even zero correlation in one sample does not establish conditional independence in another. More than two legs require the full joint distribution, not just pairwise coefficients. Push, void and bookmaker repricing alter settlement.</p><p>No sample size, confidence interval, coefficient or derived price is provided until independently verifiable inputs are permitted and available.</p>''')

pages['review.html'] = ('Flagged for Review', '''<p class="eyebrow">04 / OPEN ITEMS</p><h1>Flagged for Review</h1><p>All rows remain needs review and do not represent verified model findings. Links identify relevant official context; where no source verifies a missing value, the corresponding value remains blank.</p>''' + table(['ID','Irregularity / limitation','Consequence','Source'], rows([
('F01 · Scope','Root dashboards and most datasets concern NBA, not NFL. Existing NBA correlations and ratings are not NFL evidence.','No cross-sport transfer asserted.',NFL),
('F02 · Rights','NFL.com general terms section 1.3 prohibits systematic retrieval to create compilations absent express prior written consent; applicability and any license require review.','No automated historical collection configured.',TERMS),
('F03 · Market data','No licensed timestamped NFL odds, limits, bookmaker settlement rules or complete archive in this research section.','No bet edge, ROI or actual fair market comparison.',NFL),
('F04 · Empirical evidence','No NFL prediction sample, model outputs, held-out tests or measured dependence coefficients have been verified in this section.','No leaderboard qualifier, selections, or published correlation.',NGS),
('F05 · Existing NFL supplement','Several rows in nfl/correlation.html have no source link in the row; validation.html V8 and V9 have no official source link in the row.','Falls short of the every-row-link requirement; request correction from owning session.',NFL),
('F06 · Terms link redirect','nfl/sources.html links /terms, which redirected to subscription terms during inspection. General terms are at /legal/terms/.','Review applicable terms for each specific service.',TERMS),
('F07 · Injury history','NFL injury page shows week reports, but no immutable historical as-of archive is established here.','Cannot use present-day report as a point-in-time backtest.',INJ),
('F08 · User intent vs build','Reward competition, financial rewards, automatic licensed input pipeline and wager execution are not implemented or funded.','Competition is a design, not an operating service.',TERMS),
('F09 · Navigation','The root now links to the NFL module; this independent NFL section is not linked from shared navigation.','Request a root integrator link to this section; direct section URLs remain available.',NFL),
('F10 · External link checks','Some official sites can block automated clients or change content. Static local link validation cannot establish every third-party destination or source claim.','Review manually; do not claim full external-link crawl.',NFL),
('F11 · Broken links in existing NFL module','nfl/pages/flagged.html links to pages/leaderboard.html; nfl/pages/validation.html links twice to pages/correlations.html. These paths resolve below nfl/pages/pages/, where targets do not exist.','Merge blocked pending correction by owner and full local recheck.','https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site'),
])) + '''<p>Other workstreams have their own flags; see the <a href="../nfl/review.html">previous NFL review</a> and <a href="../index.html">repository root</a>. No claim is made that the entire NBA repository has been re-verified in this session.</p>''')

pages['sources.html'] = ('Source register', '''<p class="eyebrow">05 / EVIDENCE</p><h1>Source register</h1><p>Verified source descriptions were checked on 2026-11-02. Method references are official publisher documentation, not official NFL facts. They do not prove a strategy is profitable.</p>''' + table(['Publisher / page','Checked content','Scope / limit','Link'], rows([
('NFL · stats','Official NFL stats portal.','Portal only; data access and use rights require review.',NFL),
('NFL · injury report','Week report shows player, injury, practice and game status.','Current page is not a timestamped historical archive.',INJ),
('NFL · 2026 rulebook','The 2026 rule changes include an onside kick declaration at any time.','Playing rules do not establish sportsbook settlement.',RULES),
('NFL · 2025 standings','Page shows regular-season standings and W, L, T, PF and PA legend.','End-of-season table is not valid pregame data for that same season.',STAND),
('NFL · Next Gen Stats','Receiving stats are an NFL portal.','No dependence estimate was verified.',NGS),
('NFL · general terms','Section 1.3 describes restrictions on use and systematic retrieval.','Not legal advice or a data license.',TERMS),
('NFL · subscription terms','Lists subscription-product restrictions and personal non-commercial use.','Applies to described products; jurisdiction and service matter.',SUB),
('scikit-learn · model evaluation','Documentation identifies Brier and log loss as probability scoring functions.','Method context, not an NFL performance source.',SK),
('scikit-learn · cross-validation','Documentation warns against testing on training data and repeatedly tuning on test data.','Split design here is a proposal.',CV),
('scikit-learn · calibration','Documentation explains probability calibration.','Calibration alone does not establish a betting edge.',CAL),
('NIST · autocorrelation','Handbook discusses dependence between values of a time series at different times.','Does not provide NFL correlation values or validate the proposed block bootstrap.',NIST),
])) + '''<p>Existing NFL research: <a href="../nfl/index.html">NFL module</a> and <a href="../nfl/sources.html">earlier source register</a>. Previous work contains additional NBA materials; links do not make those materials NFL evidence.</p>''')

nav = [('index.html','Overview'),('strategies.html','Strategies'),('validation.html','Validation'),('correlations.html','Correlation'),('review.html','Flagged for Review'),('sources.html','Sources')]
for filename, (title, content) in pages.items():
    menu = ''.join(f'<a {"aria-current=page" if target == filename else ""} href="{target}">{label}</a>' for target, label in nav)
    doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)} · Own4 NFL</title><link rel="stylesheet" href="style.css"></head><body><header><div class="bar"><a class="brand" href="index.html"><span class="mark">O</span> OWN4 <small> / NFL</small></a><nav aria-label="NFL sections">{menu}</nav></div></header><main>{content}</main><footer>Independent research · As of 02 Nov 2026 · <a href="../nfl/index.html">NFL module</a> · <a href="../index.html">Repository home</a></footer></body></html>'''
    (ROOT / filename).write_text(doc + '\n', encoding='utf-8')
