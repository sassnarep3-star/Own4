#!/usr/bin/env python3
"""Build a self-contained, source-linked static NFL research dashboard."""
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
S = {
 'nfl': ('NFL 2026 rulebook', 'https://static.www.nfl.com/image/upload/fl_attachment/league/tqivdkzt9mu6wdgsh1ku.pdf'),
 'injury': ('NFL 2026 important dates / injury reports', 'https://media.nfl.com/content/dam/communications/football-communications/2026/news/07%2007%2026%20-%20Important%20Dates.pdf'),
 'timesplit': ('scikit-learn TimeSeriesSplit', 'https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html'),
 'calibration': ('scikit-learn calibration', 'https://scikit-learn.org/stable/auto_examples/calibration/plot_calibration.html'),
 'nist': ('NIST: correlation and causality', 'https://www.itl.nist.gov/div898/handbook/ppc/section1/ppc136.htm'),
 'pages': ('GitHub Pages documentation', 'https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages'),
 'stats': ('NFL statistics', 'https://www.nfl.com/stats/'),
 'odds': ('Nevada Gaming Control Board regulations', 'https://www.gaming.nv.gov/siteassets/content/home/features/Regulation22.pdf'),
}
# Proposals are our designs, not assertions that sources endorse the strategy.
PAGES = {
'index': ('Executive summary', '''<p class="eyebrow">NFL RESEARCH · 02 NOV 2026</p><h1>Build lines. Measure skill.</h1><p class="lead">A transparent research plan for singles, parlays and player props—without inventing prices, correlations or betting edges.</p><div class="cards"><div><strong>0</strong><span>validated strategies</span></div><div><strong>—</strong><span>measured NFL correlations</span></div><div><strong>—</strong><span>live fair lines</span></div></div><div class="notice"><strong>Research only.</strong> No NFL dataset, timestamped market quotes, fitted model, funded rewards or production feed was verified for this work. There are no recommendations to bet. Luck cannot be eliminated; uncertainty can only be measured and reduced.</div><h2>What matters</h2><p>The existing repository is primarily NBA research. It is not evidence of NFL strategy performance. This NFL section preserves that work and proposes an isolated, auditable process. <a href="review.html">Review the limitations</a>.</p>''', ['Priority','Finding','Source'], [
 ('Data','Acquire licensed, timestamped game, player, availability and market records before fitting; source access and usage rights remain unverified.','stats'),
 ('Models','Generate full outcome distributions, including ties, pushes and settlement rules, rather than a single point estimate. Proposed framework, not a tested edge.','nfl'),
 ('Validation','Freeze features and compare predictions on later games; evaluate calibration and uncertainty before ranking.','timesplit'),
 ('Reward','Only a proposal: rank eligible strategies on out-of-sample probabilistic skill; no reward program exists here.','calibration'),
 ]),
'strategies': ('Strategy candidates', '''<h1>Strategy candidates</h1><p class="lead">Research hypotheses only. Source links provide background, not evidence of profitability or efficacy.</p><div class="notice">All candidates are unvalidated. No signal, price or bet selection is currently available.</div>''', ['Candidate','Proposed signal and pricing','Status','Source'], [
 ('S1 · Moneyline','Estimate home, away and tie probabilities using pre-game team strength and availability. Fair decimal win price with ties refunded: 1 + P(loss)/P(win); match actual settlement rules.','Not tested','nfl'),
 ('S2 · Spread / total','Model joint final scores. At each offered threshold calculate P(win), P(loss), P(push); fair decimal price is 1 + P(loss)/P(win).','Not tested','nfl'),
 ('S3 · Player prop','Model availability, participation, volume and per-opportunity efficiency jointly; condition on actual void rules and the quoted threshold.','Not tested','injury'),
 ('S4 · Cross-game parlay','Model joint leg outcomes rather than blindly multiplying probabilities. Price from the full payout distribution including voids and pushes.','Not tested','nist'),
 ('S5 · Same-game prop combo','Simulate shared game state, attempts, targets and player outcomes jointly; compare to independent-leg baseline as a diagnostic, not as a price.','Not tested','nist'),
 ]),
'validation': ('Validation gates', '''<h1>Validation gates</h1><p class="lead">All gates are proposed project policy, not externally prescribed requirements. A strategy advances only after every applicable gate passes.</p>''', ['Gate','Pass criteria','Status','Source'], [
 ('G1 · Provenance','Permitted source, raw snapshots, timestamps, source version, coverage and audit trail for each observation.','Not assessed','stats'),
 ('G2 · Point-in-time','For every feature and quote, publication and collection precede the decision timestamp; no post-game or revised information.','Not assessed','timesplit'),
 ('G3 · Integrity','Reconcile game IDs, player IDs, outcomes, missingness, duplicates, settlement, injuries and rule changes; quarantine discrepancies.','Not assessed','nfl'),
 ('G4 · Protocol','Register model, selection rules, sample size, baseline, splits, metrics and multiple-testing correction before evaluation; keep a final untouched holdout.','Not assessed','timesplit'),
 ('G5 · Forecast quality','On walk-forward predictions, beat prespecified baseline on paired out-of-sample log loss; report Brier score and reliability with uncertainty.','Not assessed','calibration'),
 ('G6 · Economics','Use executable timestamped prices and actual limits/fees/settlement; demonstrate positive conservative game-clustered confidence bound on returns after selection adjustment.','Not assessed','odds'),
 ('G7 · Stability','Check separate seasons, weeks, market types and injury regimes; reject brittle or underpowered samples and report selection bias.','Not assessed','nist'),
 ('G8 · Forward trial','Freeze version and run prospective paper trial; verify auditability and continued performance before any live use.','Not assessed','timesplit'),
 ]),
'correlations': ('Correlation & pricing', '''<h1>Dependence, not guesswork</h1><p class="lead">Empirical coefficients are blank: no verified paired NFL observations were acquired. Correlation does not establish causation.</p><h2>Estimation protocol</h2><p>For binary settled legs calculate φ = (p11 − p1p2) / √[p1(1−p1)p2(1−p2)] on the same sample, excluding voids under a predeclared policy. Report sample size, event definition, missingness and game-clustered bootstrap intervals; the statistic is undefined when a marginal is constant. Continuous residuals can use Pearson r, fitted only on training data. Stratify by era and position, shrink sparse estimates and validate joint probabilities on later games.</p><p>For two non-void legs, p11 = p1p2 + φ√[p1(1−p1)p2(1−p2)]; enforce probability bounds. Pairwise correlations alone do not determine a three-leg joint distribution. Simulate the complete joint outcome and settlement, including pushes and voids. With decimal payout d and no push, expected net return per unit is p·d − 1. Do not multiply leg probabilities unless independence is justified out of sample.</p>''', ['Pair to investigate','Coefficient','Sample','Status','Source'], [
 ('QB passing yards / receiver yards','','','Unverified; not estimated','nist'),
 ('Game total / combined passing yards','','','Unverified; not estimated','nist'),
 ('Two different game winners','','','Unverified; not estimated','nist'),
 ('Same-player receptions / receiving yards','','','Unverified; not estimated','nist'),
 ]),
'leaderboard': ('Leaderboard', '''<h1>Leaderboard & rewards</h1><p class="lead">Competition rules are a proposal; there are no participants, rankings, prizes, or funded reward pool.</p><h2>Proposed ranking</h2><p>Freeze each forecast and candidate set before kickoff. For a common set of settled binary outcomes, rank gate-passing models by improvement in mean log loss versus a frozen baseline; clip probabilities by a preregistered epsilon. Report Brier score, reliability, game-clustered confidence intervals, coverage and net returns separately. Rank comparable markets separately; abstention cannot silently change the evaluation universe. Require a preregistered sample-size and precision/power plan before seeing the holdout. Apply a prespecified multiple-comparison procedure to promotion decisions. No gate pass means no eligible rank.</p><p>Potential reward policy: a fixed, externally funded pool may be split among eligible top ranks after a delayed audit. Funding, eligibility, ties, disputes, legal compliance and operator identity must be established first. This site makes no promise of compensation.</p>''', ['Strategy','Eligible rank','Skill estimate','Result','Source'], [
 ('S1 · Moneyline','','','No evaluation','calibration'),('S2 · Spread / total','','','No evaluation','calibration'),('S3 · Player prop','','','No evaluation','calibration'),('S4 · Cross-game parlay','','','No evaluation','calibration'),('S5 · Same-game combo','','','No evaluation','calibration')]),
'review': ('Flagged for review', '''<h1>Flagged for review</h1><p class="lead">Blank values are unknown—not zero. Background sources do not validate the proposed methods or establish access rights.</p>''', ['ID','Irregularity / action','Status','Source'], [
 ('F01','Existing dashboards, datasets and historical session claims concern NBA, not NFL. Do not reuse their performance as NFL evidence. Full repository-wide row audit has not been completed.','Needs review','stats'),
 ('F02','No authenticated or permitted NFL historical game/player data was ingested or checked row by row; data completeness and usage rights unknown.','Needs review','stats'),
 ('F03','No timestamped, executable bookmaker odds, limits, archive rights, or settlement rules verified. No actual market edge or line can be calculated.','Needs review','odds'),
 ('F04','No NFL paired sample or confidence interval is available; all correlation values are blank.','Needs review','nist'),
 ('F05','No NFL strategy has been trained, tested, scored or passed gates; no funded competition or reward program exists.','Needs review','calibration'),
 ('F06','NFL important-dates PDF injury report excerpt located through search, but full direct retrieval failed in this environment; confirm exact current reporting schedules and data access.','Needs review','injury'),
 ('F07','Search result for a team stats page returned inconsistent season context; direct page fetch returned a 404 page. No statistics copied.','Needs review','stats'),
 ('F08','Repository contains several independent NBA dashboards; ownership scopes prevent changing the shared root navigation in this session. Direct NFL URL is available after deployment.','Needs review','pages'),
 ('F09','Rulebook search excerpt verified title and contents; detailed overtime and bet settlement have not been verified in full. Book settlement is not determined by the NFL rulebook.','Needs review','nfl'),
 ])
}

def table(head, rows):
    out = ['<div class="table-wrap"><table><thead><tr>' + ''.join('<th scope="col">'+escape(h)+'</th>' for h in head) + '</tr></thead><tbody>']
    for row in rows:
        *cells, source = row
        assert len(cells) == len(head)-1 and source in S
        label, url = S[source]
        out.append('<tr>' + ''.join('<td>'+escape(str(c))+'</td>' for c in cells) + '<td><a href="'+escape(url, quote=True)+'">'+escape(label)+'</a></td></tr>')
    return ''.join(out) + '</tbody></table></div>'

def build():
    nav = ''.join(f'<a href="{key}.html">{escape(val[0])}</a>' for key,val in PAGES.items())
    for key,(title,body,head,rows) in PAGES.items():
        html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)} | NFL Research</title><link rel="stylesheet" href="style.css"></head><body><header><div class="top"><a class="brand" href="index.html">OWN4 <span>/ NFL RESEARCH</span></a><a href="../index.html">NBA project ↗</a></div><nav aria-label="Research sections">{nav}</nav></header><main>{body}{table(head,rows)}<footer>Research snapshot · 2 November 2026 · Sources link to primary publishers; proposed policies are not publisher recommendations.</footer></main></body></html>'''
        (ROOT / f'{key}.html').write_text(html, encoding='utf-8')
if __name__ == '__main__': build()
