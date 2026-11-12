#!/usr/bin/env python3
"""Build a static decision review. Proposals are not validated results."""
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NFL = 'https://www.nfl.com/news/nfl-week-10-injury-report-2026-season'
SCHED = 'https://www.nfl.com/schedules/2026/by-week/week-9'
NIST = 'https://www.itl.nist.gov/div898/handbook/ppc/section1/ppc136.htm'
TIME = 'https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html'
METRIC = 'https://scikit-learn.org/stable/modules/model_evaluation.html'
PAGE = 'https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages'
RULE = 'https://www.gaming.nv.gov/siteassets/content/divisions/administration/history/regulation-22.060-22.090-22.150-adp-01.29.2026-eff-02.28.2026.pdf'
STAT = 'https://www.nfl.com/stats/'
SPLIT = 'https://www.nfl.com/news/nfl-how-to-watch-week-10-nfl-games-schedule-munich-game-details-and-more'
GITHUB = 'https://github.com/sassnarep3-star/Own4/blob/main/'

# source URLs are background for proposals, and direct evidence for sourced observations.
pages = {
'index.html': ('NFL decision desk', 'A review-first workspace for originating lines', 'Executive view', [
 ('Current position', 'Research only. Existing NFL labs have snapshots and models, but this review does not certify current lines, live injuries, returns, reward eligibility, or an edge.', NFL),
 ('Highest-priority decision', 'Choose a canonical NFL dashboard and build a timestamped, rights-cleared data pipeline before using any model operationally. See Suggestions for alternatives.', PAGE),
 ('Opportunity', 'Test pregame team strength, availability, rest and matchup features as hypotheses; compare against frozen baselines on later games.', TIME),
 ('Risk', 'Luck cannot be removed; out-of-sample tests, uncertainty intervals and independent periods can help distinguish repeatable skill from noise.', NIST),
 ('Snapshot', 'The NFL Week 9 schedule displays final results after the NFL lab’s November 2 cutoff; its Week 9 lines are historical, not upcoming.', SCHED),
 ('Review scope', 'Focused review of selected NFL files and referenced sources; not a line-by-line audit of the entire repository or every historical data value.', STAT),
], 'Begin with the decision register, then inspect the flags. This site contains no live feed and no betting recommendations.'),
'suggestions.html': ('Suggestions', 'Review options before changes', 'Proposed paths', [
 ('1 · Canonical experience', 'Consolidate navigation onto one NFL entry point; preserve existing work and clearly label snapshots. Alternative: keep all four namespaces with a comparison index. Recommendation: comparison first, consolidation only after audit.', PAGE),
 ('2 · Data foundation', 'Use timestamped licensed official score, player and availability feeds with raw snapshots and immutable IDs. Alternative: manual official-page snapshots; cheaper but not automatic and vulnerable to layout changes. Recommendation: validate access and rights first.', STAT),
 ('3 · Availability tracker', 'Join dated team depth charts, injury designations, transactions and game-day inactives; display unknown replacement slots rather than guessing. Alternative: show injury report alone, with no impact claim.', NFL),
 ('4 · Singles', 'Benchmark a frozen team-strength model against simple baselines and price archive; evaluate future weeks and report calibration and uncertainty. Alternative: retain descriptive-only analysis.', TIME),
 ('5 · Parlays and props', 'Require joint outcome data, operator rules and price history before joint modeling; no independence assumption by default. Alternative: block these markets until evidence exists.', NIST),
 ('6 · Rewards', 'Paper leaderboard first; reward only gate-passing frozen strategies on a later evaluation period. Alternative: non-monetary recognition. Funding, eligibility and legal review are unresolved.', RULE),
 ('7 · Operations', 'Automate freshness, source/permission failures, data revision audit and publication checks; stop publishing live labels on stale data. Alternative: immutable snapshot only.', PAGE),
], 'These are proposals for review, not official source conclusions or already-implemented changes.'),
'questions.html': ('Decision register', 'Known, missing and how to discover it', 'Questions and evidence', [
 ('What data may be acquired and retained?', 'Known: NFL publishes player statistics. Missing: API access, field-level license, historical revisions and permitted storage. Obtain written terms or approved feed documentation before ingestion.', STAT),
 ('What was known before each kickoff?', 'Missing: archived publication and capture times for injuries, depth charts, rosters, weather and prices. Collect immutable dated snapshots; quarantine missing or post-cutoff records.', NFL),
 ('Who replaces a missing starter?', 'An injury designation is not a replacement announcement. Obtain contemporaneous team depth chart, inactive list and roster transactions; confirm actual role separately after the game.', NFL),
 ('Are our prices competitive?', 'Missing: historical executable operator prices, bid/ask, timing, availability, limits and settlement terms. Obtain a licensed archive and preserve full quotes and rules.', RULE),
 ('Does a signal generalize?', 'Missing: untouched multi-season evaluation, independent replications and multiple-testing controls. Freeze research choices and run chronological future-period tests.', TIME),
 ('How dependent are legs?', 'Missing: matched, contemporaneous leg outcomes and thresholds. Collect joint outcomes; estimate conditional or joint probabilities with uncertainty and compare to independence.', NIST),
 ('What constitutes a fair competition?', 'Missing: contest period, reward budget, entry and anti-gaming rules, jurisdiction and governance. Draft and review rules before inviting entries or promising prizes.', RULE),
 ('Is anything updating automatically?', 'This review is a static snapshot; no running injury service or scheduled source ingestion has been established. Test feed availability, scheduler, failure alerts and freshness SLA before describing it as live.', PAGE),
], 'Unknowns are explicitly unresolved; no values have been invented.'),
'strategies.html': ('Strategies & gates', 'Research candidates, not picks', 'Candidate strategy register', [
 ('S1 · Singles: team strength', 'Produce pregame win, margin and total distributions from prior games only. Compare with constant and simple rating baselines; account for neutral sites and ties. Proposed; no result verified here.', TIME),
 ('S2 · Availability-adjusted singles', 'Scenario-weight plausible lineups using only time-stamped evidence; measure incremental out-of-sample skill against S1. Do not claim a backup impact without sufficient data.', NFL),
 ('S3 · Rest and travel', 'Test schedule-derived rest and location independently and in combination with team strength. Confounding and multiple testing can turn apparent patterns into noise.', NIST),
 ('S4 · Cross-game parlays', 'Estimate the joint distribution from synchronized selections; compare with product of marginal probabilities only as a benchmark. Do not price when dependence or settlement is unknown.', NIST),
 ('S5 · Same-game player combos', 'Model usage, availability and correlated game script jointly; test joint calibration, not just single-leg hit rates. No player-prop observations or joint estimates verified in this review.', STAT),
], 'Suggested common gates: traceable rights and timestamps; frozen registry; leakage tests; preregistered sample/power and uncertainty; out-of-sample baseline improvement; calibration; joint calibration for combinations; price and settlement audit; independent replication. Any blocked gate means no reward eligibility.'),
'correlations.html': ('Dependence & leaderboard', 'Separate association from evidence of skill', 'Research register', [
 ('Rest differential / game outcome', 'Correlation: blank — unverified in this review. Existing nfl-lab estimates are descriptive, not a causal or validated betting edge; rerun against independently checked, timestamped games.', NIST),
 ('Player A / player B leg outcomes', 'Correlation: blank — unverified. Acquire matched game-level official outcomes and archived thresholds; report sample, interval, cutoff and joint calibration.', STAT),
 ('Home side / total', 'Correlation: blank — unverified. Compare same-game joint frequency with marginal-product benchmark and report uncertainty and selection criteria.', NIST),
 ('S1–S5 leaderboard', 'Rank: blank — unverified; reward: blank — unapproved. No independent head-to-head evaluation was performed in this review. Rank only eligible frozen strategies by a predeclared proper score; publish all failures.', METRIC),
 ('Luck controls', 'Use blocked-by-game/week uncertainty, pre-specified families and later holdouts; profit variability and selection bias remain. No finite gate eliminates luck.', NIST),
], 'Correlation does not establish causation; zero correlation alone does not establish independence. A Brier score does not measure calibration alone.'),
'injuries.html': ('Availability', 'Official report snapshot, not a live tracker', 'Examples from the NFL Week 10 report', [
 ('Washington · Colson Yankoff · TE', 'Out (knee). Report observation only; role, replacement and defensive/offensive impact are not verified.', NFL),
 ('Washington · Lucas Patrick · C', 'Out (concussion). Report observation only; replacement depth and actual snaps are not verified.', NFL),
 ('New York Giants · Malik Harrison · LB', 'Questionable (groin). Status is not a confirmed absence; replacement and impact are unverified.', NFL),
 ('New England · Ben Brown · OL', 'Out (knee). Replacement and position-specific lineup impact are unverified.', NFL),
 ('New England · Carlton Davis · CB', 'Out (knee). Replacement and defensive coverage impact are unverified.', NFL),
 ('New England · TreVeyon Henderson · RB', 'Out (illness). Replacement and offensive workload impact are unverified.', NFL),
], 'Source read 2026-11-12 UTC. The article changes over time. This is a small illustrative subset, not the full league report, a current inactive list or an automated tracker. Recheck the source before relying on a status.'),
'flagged.html': ('Flagged for review', 'Unresolved items and irregularities', 'Review queue', [
 ('F01 · No live feed', 'This site is a static research snapshot, not automatic injury, depth or line tracking. A stale snapshot can mislead. Obtain permissions and monitor retrieval before automation.', PAGE),
 ('F02 · Existing outputs are historical', 'nfl-lab executive summary describes Week 9 as upcoming at a November 2 cutoff; official Week 9 now shows finals. Do not use those projections as a current slate.', SCHED),
 ('F03 · Count discrepancy', 'nfl-lab/scripts/verify_data.py labels 32 × 13 comparisons, checks 11 fields plus pct and a combined membership check per row, but reports 32 × 15 cells. The claimed 480 is a hard-coded count, not an independently counted source verification. Inspect and correct in the owning namespace.', 'https://www.nfl.com/standings/league/2026/REG'),
 ('F04 · Reconciliation is not source verification', 'Matching internally transcribed game and standings data does not by itself prove every underlying value, capture date or source was independently checked. Full source-by-source NFL and repository audit remains open.', SCHED),
 ('F05 · Performance and correlation', 'Existing numerical outputs are model-derived, not official league values. This session has not independently verified input rows or statistical uncertainty; do not interpret correlations as causal or rewards as earned.', NIST),
 ('F06 · Official article conflict', 'NFL Week 10 injury article lists FOX for Patriots–Lions; NFL+ schedule article lists NFL Network. Broadcasting only; resolve using game-specific official listing before publishing a definitive channel.', NFL),
 ('F07 · Unknown data rights and operator terms', 'Historical price archive, permissible access, quote timing, rules, voids and costs are unverified. Nevada source is an example only, not legal advice or a ruling for another jurisdiction.', RULE),
 ('F08 · No integrated rewards or eligible ranking', 'Reward funding, jurisdiction, administration and independent evaluation remain open. Existing candidate results are not certified by this review.', METRIC),
 ('F09 · Navigation / peer ownership', 'Multiple NFL sections already exist. New decision desk is direct-link only pending canonical navigation owner review; this session does not overwrite peer-owned integration files.', PAGE),
 ('F10 · Replacement players and impact', 'Official injury designations alone do not establish starting lineups, depth order, actual replacements or ability. All such fields remain unverified.', NFL),
], 'F06 second official source: <a href="'+SPLIT+'">NFL+ Week 10 schedule</a>. Code for F03: <a href="'+GITHUB+'nfl-lab/scripts/verify_data.py">repository verifier</a>. Flags are non-blocking for publishing this review, but block reliance where stated.'),
}
NAV = [('index.html','Overview'),('suggestions.html','Suggestions'),('questions.html','Questions'),('strategies.html','Strategies & gates'),('correlations.html','Correlations & leaderboard'),('injuries.html','Availability'),('flagged.html','Flagged for review')]

def render(filename, item):
 title, subtitle, caption, rows, note = item
 nav = ''.join(f'<a {"aria-current=page" if f == filename else ""} href="{f}">{escape(label)}</a>' for f,label in NAV)
 table = ''.join(f'<tr><th scope="row">{escape(a)}</th><td>{escape(b)}</td><td><a href="{escape(url, quote=True)}">Official source ↗</a></td></tr>' for a,b,url in rows)
 return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)} · NFL Decision Desk</title><link rel="stylesheet" href="style.css"></head><body><a class="skip" href="#main">Skip to content</a><header><div class="head"><a class="brand" href="index.html"><span class="mark">N</span><span>NFL <small>DECISION DESK</small></span></a><span class="status">RESEARCH SNAPSHOT · 12 NOV 2026</span></div><nav aria-label="Main navigation">{nav}</nav></header><main id="main"><div class="eyebrow">OWN4 / NFL RESEARCH</div><h1>{escape(title)}</h1><p class="lead">{escape(subtitle)}</p><div class="notice"><strong>Review first.</strong> No live feed, certified edge or funded rewards. Data may be stale; verify sources before use.</div><section><div class="section-head"><div><div class="eyebrow">DECISION WORKSPACE</div><h2>{escape(caption)}</h2></div><span>{len(rows):02d} ITEMS</span></div><div class="scroll"><table><caption class="sr">{escape(caption)}</caption><thead><tr><th scope="col">Item</th><th scope="col">Finding / next step</th><th scope="col">Source</th></tr></thead><tbody>{table}</tbody></table></div><p class="note">{note}</p></section><aside><h2>Existing NFL work</h2><p>Historical, separately maintained research. Values and results there are not certified by this review.</p><div class="links"><a href="../nfl-lab/">NFL lab ↗</a><a href="../nfl-quant/">NFL quant ↗</a><a href="../nfl-research/">NFL research ↗</a><a href="../nfl/">NFL dashboard ↗</a><a href="../index.html">Own4 home ↗</a></div></aside></main><footer>Research only · No guarantee of performance · Official source links support the stated facts or provide background for clearly labeled proposals.</footer></body></html>'''

if __name__ == '__main__':
 for name, page in pages.items():
  (ROOT / name).write_text(render(name, page), encoding='utf-8')
 print(f'Built {len(pages)} pages')
