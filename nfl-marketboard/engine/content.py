"""Decision-desk content for nfl-marketboard.

Everything here is either (a) a fact verified against an official source this
session, with the URL attached, or (b) explicitly labelled as a proposal awaiting
the owner's choice. Nothing is asserted as measured that was not measured.
"""

NFL = 'https://www.nfl.com/'
SCHED = 'https://www.nfl.com/schedules/2026/by-week/week-{w}'
STAND = 'https://www.nfl.com/standings/league/2026/REG'
STAND25 = 'https://www.nfl.com/standings/league/2025/REG'
INJ = 'https://www.nfl.com/injuries/'
NFLDATA = 'https://github.com/nflverse/nfldata'
NFLDATA_API = 'https://api.github.com/repos/nflverse/nfldata/contents/data'
DEPTH404 = 'https://www.nfl.com/teams/new-england-patriots/depth-chart'
STATSWEEK404 = 'https://www.nfl.com/stats/team-stats/offense/passing/2026/reg/9'
STATSALL = 'https://www.nfl.com/stats/team-stats/offense/passing/2026/reg/all'
OPERATIONS = 'https://operations.nfl.com/rules-officiating/2026-nfl-rulebook'

# ===========================================================================
# QUESTIONS REGISTER — what we know, what is missing, what would settle it
# ===========================================================================
QUESTIONS = [
    dict(id='Q-01', area='Prices',
         question='Where do the market numbers come from, and are they official?',
         what_we_know='The NFL publishes no odds on nfl.com. Every market number in this '
                      'workspace comes from the nflverse/nfldata archive, which is a '
                      'third-party CC BY 4.0 repository of historical closing lines. It is '
                      'reconciled here against official scores (136/136 exact), so the results '
                      'line up, but the prices themselves carry no official provenance.',
         what_is_missing='An official or licensed price feed. Without one, no published edge, '
                         'ROI or closing-line value can be described as verified.',
         how_to_settle='Licence a price feed (Sportradar or Genius are the NFL\'s authorised '
                       'distributors) or buy a commercial odds archive and re-run build.py '
                       'against it. Nothing else changes.',
         source_url=NFLDATA, status='open'),

    dict(id='Q-02', area='Prices',
         question='Can we record opening numbers, or only closing numbers?',
         what_we_know='No opening number exists for any 2026 market in any source available to '
                      'this repository. The nflverse archive files were enumerated directly: '
                      'closing_lines.csv ends at 2018, sc_lines.csv ends at 2020, and '
                      'initial_lines.csv covers 2021 only. That is 0 of 900 price rows with an '
                      'opening number.',
         what_is_missing='The entire opening side of the price-snapshot store for 2026.',
         how_to_settle='A feed that captures a timestamped price the moment a market is posted. '
                       'Until then the opening column stays blank on every row and the store is '
                       'half-built, which is exactly how it is published.',
         source_url=NFLDATA_API, status='open'),

    dict(id='Q-03', area='Prices',
         question='Is the market number we compare against a closing number or something else?',
         what_we_know='The archive snapshot carries one price per market per game, captured at '
                      'commit 6ea0be6 (2026-11-12). It is treated as the closing number. The '
                      'capture time is not published by the archive, so "closing" is an '
                      'assumption about the archive, not a verified timestamp.',
         what_is_missing='A verified capture timestamp, and therefore any guarantee that the '
                         'number was available before kickoff.',
         how_to_settle='Capture prices ourselves at a known time, or obtain a feed that '
                       'publishes its capture time.',
         source_url=NFLDATA, status='open'),

    dict(id='Q-04', area='Depth',
         question='How do we know whether a replacement is a 2nd, 3rd or 4th string player?',
         what_we_know='The NFL publishes no depth chart. The team depth-chart route on nfl.com '
                      'returns 404 (re-tested this session). The official injury report gives '
                      'player, position, injury, practice status and game status — and nothing '
                      'about depth order.',
         what_is_missing='The depth ordinal the brief asks for. It is blank on every row.',
         how_to_settle='Two official routes exist and neither is used yet: (1) the official '
                       'gamebook PDF for each game publishes that game\'s starting lineups, so '
                       'a player who started in week w-1 and is Out in week w has a replacement '
                       'who can be named from the week-w gamebook; (2) official per-game '
                       'participation gives an ordinal count of prior starts. Licensing a depth '
                       'chart is the fast route and is suggestion S-03.',
         source_url=DEPTH404, status='open'),

    dict(id='Q-05', area='Depth',
         question='Which players are actually starting for each team in Week 10?',
         what_we_know='Four replacements are named in official NFL.com news reports this week: '
                      'Drew Lock starts at QB for Seattle, Deshaun Watson for Cleveland, Carson '
                      'Beck for Arizona, and Kyle McCord is in line for his first start at QB '
                      'for Miami. Baltimore has lost two quarterbacks (Lamar Jackson, 6-10 '
                      'weeks; Tyler Huntley, out for the season) and the official reports read '
                      'this session do not name their replacement.',
         what_is_missing='The named replacement for every other unavailable starter, and the '
                         'depth ordinal for those that are named.',
         how_to_settle='Read the official gamebook for each Week 10 game after kickoff; the '
                       'starting lineup is printed there. Doing this for all 14 games costs 14 '
                       'fetches and would complete the register.',
         source_url=INJ, status='partially answered'),

    dict(id='Q-06', area='Model',
         question='Do our originated numbers beat the market numbers?',
         what_we_know='No. On 105 walk-forward graded games our originated spread misses the '
                      'official margin by 9.383 points on average against the market\'s 8.814 '
                      '(we are 0.569 worse, paired p = 0.138), and our total misses by 11.112 '
                      'against the market\'s 10.357 (we are 0.755 worse, paired p = 0.046). The '
                      'total gap is statistically significant in the wrong direction.',
         what_is_missing='A model that beats the market. There is not one in this workspace.',
         how_to_settle='This is settled as a negative result for the current model. The next '
                       'step is the modelling work in suggestion S-05, not more data.',
         source_url=SCHED.format(w='1-10'), status='answered (negative)'),

    dict(id='Q-07', area='Model',
         question='Is the model leaking future information?',
         what_we_know='Structurally no. A number originated for week w uses only official games '
                      'with week < w plus the official 2025 final standings, which were '
                      'published before the 2026 season began. The pipeline has no path by '
                      'which a later game can enter an earlier one.',
         what_is_missing='An independent adversarial check of the walk-forward boundary.',
         how_to_settle='Re-run build.py with week w+1 deleted from the input and confirm the '
                       'week-w numbers are byte-identical.',
         source_url=STAND25, status='answered'),

    dict(id='Q-08', area='Market behaviour',
         question='Why do home teams cover only 40.9% of the time in 2026?',
         what_we_know='Over 137 official results the mean market spread is +1.69 points to the '
                      'home team while the mean official home margin is -0.02. Home sides '
                      'therefore fail to cover far more often than half the time: 56 covers, 75 '
                      'losses, 6 pushes, a 40.9% cover rate. The sign convention was verified '
                      'three independent ways, so this is not a parsing error.',
         what_is_missing='Whether this is a durable 2026 effect or one season of noise about a '
                         'true 50% rate (z is about -2.1, so it is around the edge of '
                         'conventional significance on its own).',
         how_to_settle='Compute the same figure for 2019-2025 from an archived line source. If '
                       'the home-cover rate is stable near 41% across seasons it is an '
                       'exploitable structural effect; if it wanders around 50% it is noise.',
         source_url=SCHED.format(w='1-10'), status='open'),

    dict(id='Q-09', area='Validation',
         question='Can any strategy qualify for the leaderboard yet?',
         what_we_know='No. The pre-registered sample floor is 300 graded bets and the season has '
                      'produced 137 official results, so the largest bet count any strategy '
                      'reaches is 77. Separately, after Benjamini-Hochberg correction across '
                      'the eight-strategy family, the smallest q-value is 0.165 — nothing is '
                      'close to the 0.05 threshold.',
         what_is_missing='Sample. Nothing else is blocking qualification.',
         how_to_settle='Time, plus continuing to grade. Week 11 alone adds about 14 games.',
         source_url=SCHED.format(w='1-10'), status='answered'),

    dict(id='Q-10', area='Validation',
         question='How do we keep a lucky staking run from looking like a good signal?',
         what_we_know='By scoring them separately and publishing both. The clearest example this '
                      'week is S7, the two-leg cross-game parlay: 7 bets, a +56.1% flat ROI, and '
                      'a staking score of 61.0 that is HIGHER than its signal score of 53.0. On '
                      'ROI alone S7 is the best strategy in the house. With the two scores '
                      'separated it is visibly a 7-bet sample.',
         what_is_missing='Nothing. This is working as designed.',
         how_to_settle='n/a — the gate D3 (luck-test p above 0.20 sends a live strategy back to '
                       'paper) already fires on S7 at p = 0.219.',
         source_url=SCHED.format(w='1-10'), status='answered'),

    dict(id='Q-11', area='Props',
         question='Can player-prop combinations be originated at all?',
         what_we_know='No. Player props need a posted prop price, and neither the NFL nor any '
                      'other official source publishes one. The official player pages do publish '
                      'per-game logs, so outcomes are knowable; prices are not.',
         what_is_missing='Every prop price. The strategy registered for props, S8, has zero '
                         'bets because no price exists to originate against.',
         how_to_settle='Licence a prop price feed. The outcome side is already covered by the '
                       'official per-game logs.',
         source_url='https://www.nfl.com/players/drake-maye/stats', status='open'),

    dict(id='Q-12', area='Data',
         question='Can we build point-in-time team statistics from official sources?',
         what_we_know='Not from the team-stats pages. Those accept only the season-to-date '
                      'selection; the weekly variant returns 404 (re-tested this session). A '
                      'season-to-date table read today contains games that had not happened at '
                      'the time of any earlier week, so using it in a backtest would be '
                      'look-ahead bias.',
         what_is_missing='Official weekly splits for team statistics.',
         how_to_settle='Two options: sum the official per-game box scores (point-in-time by '
                       'construction, but one fetch per game), or reconstruct the splits from a '
                       'licensed feed. This workspace avoids the problem by using only official '
                       'final scores plus the prior-season standings as features.',
         source_url=STATSWEEK404, status='answered'),

    dict(id='Q-13', area='Data',
         question='Is the third-party archive complete and current?',
         what_we_know='Almost, but not quite. All 137 games played through Thursday 12 November '
                      'have a market line in the archive, but the archive carries no score for '
                      'the Week 10 WAS-NYG game — its snapshot predates that game. Official '
                      'results and archive scores agree exactly on the other 136 games.',
         what_is_missing='One game of settlement in the archive.',
         how_to_settle='Nothing to fix: this workspace takes results from nfl.com and prices '
                       'from the archive, so the gap does not propagate. It is recorded so that '
                       'nobody assumes the two files agree row for row.',
         source_url='https://www.nfl.com/games/commanders-at-giants-2026-reg-10',
         status='answered'),

    dict(id='Q-14', area='Governance',
         question='What sends a live strategy back to paper?',
         what_we_know='Six pre-registered demotion triggers, D1 to D6, published on the '
                      'Governance page. Five of the eight strategies currently trigger at least '
                      'one; D3 (luck-test p above 0.20) fires on seven of them.',
         what_is_missing='Nothing for the rules. All eight strategies are in PAPER status '
                         'anyway because none has ever passed promotion.',
         how_to_settle='n/a — the rules are implemented and running.',
         source_url=SCHED.format(w='1-10'), status='answered'),

    dict(id='Q-15', area='Repo',
         question='How many parallel NFL workspaces exist, and does that hurt decision-making?',
         what_we_know='Sixteen directories in this repository carry NFL work, each produced by a '
                      'different session: nfl, nfl-arena, nfl-audit, nfl-command, nfl-decision, '
                      'nfl-decisions, nfl-edge, nfl-hub, nfl-integration, nfl-intel, nfl-lab, '
                      'nfl-lines, nfl-origination, nfl-own, nfl-quant, nfl-research. They hold '
                      '387 published HTML pages. Numbers disagree between them because they were '
                      'built on different days from different snapshots.',
         what_is_missing='A single answer to "what is our number for X".',
         how_to_settle='A consolidation decision by the owner, which is suggestion S-01.',
         source_url='https://github.com/sassnarep3-star/Own4', status='open'),

    dict(id='Q-16', area='Repo',
         question='Does every published table row carry a source link, as the brief requires?',
         what_we_know='Not everywhere. Scanning all 387 published pages this session: 11,584 '
                      'tbody data rows, of which 534 (4.6%) contain no https link. They cluster '
                      'in nfl-lines (228), nfl-origination (87), nfl-decision (55), nfl (45) '
                      'and nfl-hub (35). Many of those rows are proposals rather than data, but '
                      'the mix cannot be separated automatically.',
         what_is_missing='A clean 100% row-source guarantee across the existing namespaces.',
         how_to_settle='A per-namespace triage: mark proposal rows explicitly, and attach a '
                       'source to every row that states a fact. Suggestion S-02.',
         source_url='https://github.com/sassnarep3-star/Own4', status='open'),

    dict(id='Q-17', area='Repo',
         question='Are there broken links anywhere on the published site?',
         what_we_know='No. Across 387 pages and 24,084 href/src references, 9,260 local '
                      'references were resolved against the filesystem and all 9,260 resolve. '
                      'This was checked this session, including the namespaces added by other '
                      'sessions.',
         what_is_missing='Nothing.',
         how_to_settle='n/a',
         source_url='https://github.com/sassnarep3-star/Own4', status='answered'),

    dict(id='Q-18', area='Operations',
         question='How fresh is the injury information, and can it change before kickoff?',
         what_we_know='The report read this session is the official Week 10 report and its news '
                      'module carries an item dated Saturday 14 November, so the page is live. '
                      'Designations are revised up to kickoff, and the official report publishes '
                      'blank cells that this workspace preserves as blanks rather than filling '
                      'them in.',
         what_is_missing='A guarantee that a designation captured now holds at kickoff.',
         how_to_settle='Re-read the report immediately before kickoff and store each read as a '
                       'new dated snapshot. That is suggestion S-04.',
         source_url=INJ, status='open'),
]

# ===========================================================================
# SUGGESTIONS — each with options, so the owner picks a path
# ===========================================================================
SUGGESTIONS = [
    dict(id='S-01', title='Pick one canonical NFL workspace and freeze the rest',
         problem='Sixteen NFL directories hold 387 pages built by different sessions on '
                 'different days. They disagree with each other, and there is no way for a '
                 'reader to tell which number is current. Every new session adds another.',
         options=[
             dict(id='a', label='Consolidate into one namespace, archive the other fifteen',
                  pros='One answer per question; the site becomes usable; future sessions have '
                       'one place to update.',
                  cons='A large one-off integration job; risks losing a peer session\'s '
                       'detail unless each page is migrated deliberately.'),
             dict(id='b', label='Keep all sixteen, but publish an index that says which is '
                                'authoritative for what',
                  pros='Cheap; no content is lost.',
                  cons='Does not fix the underlying disagreement; the reader still has to '
                       'cross-check sixteen sources.'),
             dict(id='c', label='Freeze everything except one, and let new work land only '
                                'there',
                  pros='Stops the sprawl growing; no migration cost.',
                  cons='Leaves the existing contradictions in place.'),
         ],
         recommendation='Option (a) if you intend to keep using this repo; option (c) if you '
                        'only want a stopgap. Option (b) alone is not enough.',
         effort='large / medium / small', status='awaiting decision',
         source_url='https://github.com/sassnarep3-star/Own4'),

    dict(id='S-02', title='Triage the 534 rows with no source link',
         problem='The brief requires a source link on every row. 534 published rows do not have '
                 'one. Some are proposals and legitimately have no external source; some state '
                 'facts and should be sourced.',
         options=[
             dict(id='a', label='Split every row into DATA or PROPOSAL and display the class',
                  pros='Makes the distinction explicit; proposals stop looking unsourced and '
                       'data rows without a source become obvious.',
                  cons='Needs a pass over each namespace.'),
             dict(id='b', label='Attach a source to every row, including proposals',
                  pros='Literal compliance.',
                  cons='Forces a link onto rows where no link is meaningful, which is its own '
                       'kind of noise.'),
             dict(id='c', label='Leave as is',
                  pros='No work.',
                  cons='The verification rule stays unmet.'),
         ],
         recommendation='Option (a). It satisfies the rule honestly instead of cosmetically.',
         effort='medium', status='awaiting decision',
         source_url='https://github.com/sassnarep3-star/Own4'),

    dict(id='S-03', title='Fill the replacement-depth column',
         problem='The brief asks whether a replacement is a 2nd, 3rd or 4th string player. The '
                 'NFL publishes no depth chart, so the column is blank on every row and the '
                 'requirement is unmet.',
         options=[
             dict(id='a', label='Licence a depth-chart feed',
                  pros='Directly answers the question; cheapest in engineering time.',
                  cons='Costs money; the provider becomes a dependency.'),
             dict(id='b', label='Derive depth from official gamebooks: count a replacement\'s '
                                'prior starts this season',
                  pros='Fully official, free, and it produces an ordinal that actually means '
                       'something: a replacement with zero prior starts is deeper on the chart '
                       'than one with eight.',
                  cons='One gamebook fetch per game per week — about 14 a week, or 270 a '
                       'season. Needs automation.'),
             dict(id='c', label='Track only the fact of replacement, not its depth',
                  pros='Almost free; works today from the official injury report.',
                  cons='Explicitly does not meet the brief, which asks for depth.'),
         ],
         recommendation='Option (b) if you want it free and official; option (a) if you want it '
                        'fast. Option (c) is what is published now, and it is labelled as such.',
         effort='medium (b) / small (a)', status='awaiting decision',
         source_url=DEPTH404),

    dict(id='S-04', title='Snapshot the injury report on a schedule, not once',
         problem='One read per week cannot show when a designation changed, and designations '
                 'change right up to kickoff. A single read also cannot be audited later.',
         options=[
             dict(id='a', label='Store a dated snapshot on every read and graph the changes',
                  pros='Turns a static table into a timeline; makes "when did we know" '
                       'answerable, which matters for any claim about timing an edge.',
                  cons='Needs a scheduler and more storage.'),
             dict(id='b', label='Keep one read per week but record the exact read time',
                  pros='Minimal change; removes the ambiguity about freshness.',
                  cons='Still no change history.'),
         ],
         recommendation='Option (a). Knowing when a designation changed is the whole point of '
                        'tracking injuries.',
         effort='medium', status='awaiting decision', source_url=INJ),

    dict(id='S-05', title='Fix the model before adding more data',
         problem='The current model is measurably worse than the market: 0.569 points worse on '
                 'the spread and 0.755 worse on the total. Collecting more games will make the '
                 'measurement more precise, not make the model better.',
         options=[
             dict(id='a', label='Add the features the model is missing: QB availability, '
                                'replacement depth, rest, travel, and weather',
                  pros='These are the obvious gaps and two of them (QB availability, '
                       'replacement depth) are already partly sourced here.',
                  cons='Each feature needs its own official source and its own leakage '
                       'control.'),
             dict(id='b', label='Replace the hand-built model with a fitted one on the same '
                                'walk-forward harness',
                  pros='The harness already exists and enforces the time boundary; swapping the '
                       'estimator is contained.',
                  cons='Risks overfitting at n=137; still needs the sample floor before any '
                       'claim.'),
             dict(id='c', label='Stop originating and buy a benchmark model instead',
                  pros='Removes the whole modelling problem.',
                  cons='Then you are no longer originating your own lines, which was the point.'),
         ],
         recommendation='Option (a) first, then (b) once QB availability and depth are real '
                        'columns rather than blanks.',
         effort='large', status='awaiting decision', source_url=SCHED.format(w='1-10')),

    dict(id='S-06', title='Get opening prices, or stop promising them',
         problem='Zero of 900 price rows have an opening number. Any metric that needs line '
                 'movement — closing-line value, steam, open-to-close drift — is impossible '
                 'until that changes.',
         options=[
             dict(id='a', label='Licence a feed that captures the opening post',
                  pros='Unlocks line-movement metrics, which are the most robust evidence of '
                       'skill available in this domain.',
                  cons='Cost; and the historical backlog is still empty, so the metrics start '
                       'from the licence date.'),
             dict(id='b', label='Backfill 2021, where the archive does hold both ends',
                  pros='Free and available today: the archive has Westgate opening lines and '
                       'closing lines for the 2021 season, 272 games. That is enough to measure '
                       'how far lines actually move.',
                  cons='It is one season, from one book, five years ago.'),
             dict(id='c', label='Publish the column blank and revisit',
                  pros='Honest; no cost.',
                  cons='Line movement stays unmeasurable, which caps how convincingly skill can '
                       'ever be demonstrated.'),
         ],
         recommendation='Both (a) and (b): (b) gives you a movement prior this week, (a) gives '
                        'you the real thing going forward.',
         effort='medium', status='awaiting decision', source_url=NFLDATA_API),

    dict(id='S-07', title='Lower the 300-bet floor, or accept that nothing qualifies all season',
         problem='The pre-registered floor of 300 graded bets cannot be met this season: a '
                 '17-week NFL season produces at most about 272 games, and a filtered strategy '
                 'bets far fewer than that. As written, no single-season strategy can ever '
                 'qualify.',
         options=[
             dict(id='a', label='Keep 300 and let qualification span multiple seasons',
                  pros='Statistically defensible; 300 is a reasonable floor for a hit-rate '
                       'claim.',
                  cons='Nothing can be awarded for roughly two years.'),
             dict(id='b', label='Add a provisional tier at n>=100 with a stricter p-value and a '
                                'smaller reward',
                  pros='Gives the competition something to actually compete for this season '
                       'without weakening the standard.',
                  cons='Adds complexity; a provisional tier can be mistaken for a real one.'),
             dict(id='c', label='Score on out-of-sample prediction error instead of bet count',
                  pros='Uses every game rather than only the bets, so 137 results carry real '
                       'weight; independent of staking entirely.',
                  cons='Needs a new scoring definition and its own calibration.'),
         ],
         recommendation='Option (c) alongside (a). Prediction error is the better signal '
                        'measure anyway, and it solves the sample problem without lowering any '
                        'standard.',
         effort='medium', status='awaiting decision', source_url=SCHED.format(w='1-10')),

    dict(id='S-08', title='Put a single front door on the site',
         problem='The brief asks for suggestions, questions, injuries, depth, a leaderboard and '
                 'an executive summary. All of that now exists in more than one namespace, in '
                 'more than one copy, reached by different navigation paths.',
         options=[
             dict(id='a', label='One landing page with one canonical link per category',
                  pros='A reader can answer "what do we know and what do we not know" without '
                       'visiting sixteen places.',
                  cons='Requires deciding what is canonical, which is S-01.'),
             dict(id='b', label='A search box over all namespaces',
                  pros='No canonical decision needed.',
                  cons='Search does not resolve contradictions; it surfaces more of them.'),
         ],
         recommendation='Option (a), after S-01.',
         effort='small', status='awaiting decision',
         source_url='https://github.com/sassnarep3-star/Own4'),

    dict(id='S-09', title='Automate the weekly loop end to end',
         problem='Every number here was produced by a session that had to be asked. Scores, '
                 'lines, injuries and grades should refresh themselves after each game without '
                 'anyone prompting.',
         options=[
             dict(id='a', label='A scheduled job: fetch official scores and the injury report, '
                                're-originate, re-grade, rebuild, push',
                  pros='The store stops going stale, which is currently its main weakness.',
                  cons='Needs a runner and a secret for the push; the sandbox forbids long '
                       'running processes, so this has to be GitHub Actions.'),
             dict(id='b', label='Keep it manual but document the exact command sequence',
                  pros='No infrastructure.',
                  cons='Depends on someone remembering; gaps appear between runs.'),
         ],
         recommendation='Option (a). The repository already has GitHub Actions workflows for '
                        'other namespaces, so the pattern exists.',
         effort='medium', status='awaiting decision', source_url=SCHED.format(w='1')),

    dict(id='S-10', title='Write down what would change your mind',
         problem='Eight strategies are being scored against six gates, but nobody has recorded '
                 'in advance what result would cause you to abandon a strategy rather than '
                 'keep explaining it.',
         options=[
             dict(id='a', label='Pre-register an abandonment rule per strategy, dated and '
                                'frozen before the next grading window',
                  pros='Removes the temptation to reinterpret a bad run as bad luck; this is '
                       'the single cheapest anti-self-deception measure available.',
                  cons='Takes an hour of writing.'),
             dict(id='b', label='Rely on the existing demotion gates',
                  pros='Already implemented.',
                  cons='Gates act on results; they do not stop a human from re-framing the '
                       'story around the results.'),
         ],
         recommendation='Option (a). It costs almost nothing and it is the difference between a '
                        'research programme and a narrative.',
         effort='small', status='awaiting decision', source_url=SCHED.format(w='1-10')),
]

# ===========================================================================
# FLAGS — irregularities and blanks, all non-blocking
# ===========================================================================
FLAGS = [
    dict(id='P-01', area='Price store',
         what='0 of 900 price rows have an opening number.',
         why='The open-to-close chain — the only way to measure line movement and closing-line '
             'value — cannot be built. Every opening cell is blank and will stay blank until a '
             'feed is licensed or 2021 is backfilled.',
         source_url=NFLDATA_API),
    dict(id='P-02', area='Prices',
         what='Every market price in this workspace is third-party, not official.',
         why='The NFL publishes no odds. Any edge, ROI or closing-line value computed here '
             'inherits that provenance and must not be described as officially verified.',
         source_url=NFLDATA),
    dict(id='P-03', area='Prices',
         what='The archive carries no score for the Week 10 WAS-NYG game.',
         why='Its snapshot predates Thursday 12 November. Results do not depend on the archive, '
             'so nothing breaks, but the two files no longer agree row for row.',
         source_url='https://www.nfl.com/games/commanders-at-giants-2026-reg-10'),
    dict(id='P-04', area='Depth',
         what='No official NFL depth chart exists; the team route returns 404.',
         why='The depth ordinal the brief asks for (2nd/3rd/4th string) cannot be sourced. '
             'Every depth cell is blank.',
         source_url=DEPTH404),
    dict(id='P-05', area='Props',
         what='No official player-prop prices exist anywhere.',
         why='Strategy S8, the prop-combination strategy, has zero bets. Its entire row set is '
             'blank by construction, not by omission.',
         source_url='https://www.nfl.com/players/drake-maye/stats'),
    dict(id='P-06', area='Market behaviour',
         what='Home teams cover only 40.9% of the time across 137 official results.',
         why='This is a large deviation from the 50% a calibrated market should produce. The '
             'sign convention was verified three ways so it is not a parsing error, but it may '
             'be one season of noise. It needs multi-season confirmation before anyone trades '
             'on it.',
         source_url=SCHED.format(w='1-10')),
    dict(id='P-07', area='Model',
         what='The originated numbers are worse than the market numbers.',
         why='Spread: 9.383 MAE versus the market\'s 8.814 (p = 0.138). Total: 11.112 versus '
             '10.357 (p = 0.046). Published as a negative result rather than buried.',
         source_url=SCHED.format(w='1-10')),
    dict(id='P-08', area='Validation',
         what='137 official results against a pre-registered floor of 300 graded bets.',
         why='Nothing can qualify this season. Also, after Benjamini-Hochberg correction the '
             'smallest q-value across the eight strategies is 0.165.',
         source_url=SCHED.format(w='1-10')),
    dict(id='P-09', area='Data',
         what='nfl.com publishes only season-to-date team statistics; the weekly split returns '
             '404.',
         why='Cumulative official stats cannot be used as walk-forward features without '
             'look-ahead bias. This workspace uses only official final scores plus the '
             'prior-season standings.',
         source_url=STATSWEEK404),
    dict(id='P-10', area='Injuries',
         what='The official injury report publishes blank cells.',
         why='They are preserved as blanks here. Filling them would be inference, which the '
             'verification rule forbids.',
         source_url=INJ),
    dict(id='P-11', area='Injuries',
         what='Only four replacements are officially named for Week 10.',
         why='Seattle, Cleveland, Arizona and Miami have a named starting quarterback in an '
             'official NFL.com report. Baltimore has lost two quarterbacks and no official '
             'report read this session names their replacement.',
         source_url=INJ),
    dict(id='P-12', area='Repo',
         what='534 of 11,584 published table rows carry no https source link.',
         why='The brief requires one per row. The count and method are published on the '
             'Repository review page so it can be re-run and checked.',
         source_url='https://github.com/sassnarep3-star/Own4'),
    dict(id='P-13', area='Repo',
         what='Sixteen parallel NFL namespaces exist in one repository.',
         why='They were built on different days from different snapshots and disagree with each '
             'other. Confirmed by directory enumeration this session.',
         source_url='https://github.com/sassnarep3-star/Own4'),
    dict(id='P-14', area='Repo',
         what='COORDINATION.md still opens with "Shared Task Board (Own4 / NBA Line '
             'Origination Research)".',
         why='Carried forward from earlier sessions. It is a peer file; this session appends '
             'only and does not edit it.',
         source_url='https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md'),
    dict(id='P-15', area='Repo',
         what='Seven pull requests are open, one of them NFL and more than 60 minutes old with '
             'no commits (PR #93, nfl-command).',
         why='Left untouched this session because its file scope does not overlap this work. '
             'Recorded so it is not forgotten.',
         source_url='https://github.com/sassnarep3-star/Own4/pull/93'),
]

# ===========================================================================
# REPOSITORY REVIEW — measured this session
# ===========================================================================
REPO_REVIEW = dict(
    method='Directory walk and HTML scan of the repository at commit 02a8bdf plus this '
           'session\'s additions, run 2026-11-14 UTC. Raw provenance archives under '
           'data/raw/** are excluded from page counts because they are stored source '
           'documents, not published pages.',
    pages_scanned=387,
    href_src_references=24084,
    local_references=9260,
    broken_local_links=0,
    tbody_data_rows=11584,
    rows_without_https_source_link=534,
    rows_without_pct=4.61,
    nfl_namespaces=16,
    nfl_directories=['nfl', 'nfl-arena', 'nfl-audit', 'nfl-command', 'nfl-decision',
                     'nfl-decisions', 'nfl-edge', 'nfl-hub', 'nfl-integration', 'nfl-intel',
                     'nfl-lab', 'nfl-lines', 'nfl-origination', 'nfl-own', 'nfl-quant',
                     'nfl-research'],
    open_pull_requests=[
        '#93 arena/582300df-own4 (NFL Command Center)',
        '#59 SF Outer Sunset rental dashboard', '#56 SF rental review site',
        '#47 SF rent increase dashboard', '#43 NBA line lab',
        '#39 NBA data refresh and settlement', '#29 COORDINATION record'],
    row_source_gap_by_namespace=[
        ('nfl-lines', 228), ('nfl-origination', 87), ('nfl-decision', 55), ('nfl', 45),
        ('nfl-hub', 35), ('verification-2026-11-13', 22), ('rental-99ca004d-own4', 21),
        ('rental-own4', 18), ('rental-f1dbaea0', 15), ('nfl-intel', 4), ('nfl-arena', 3),
        ('rental-sf', 1)],
    note_on_prior_count='An earlier session recorded 50 unsourced rows out of 9,279. This '
                        'session counts 534 out of 11,584. The difference is method, not '
                        'necessarily disagreement: this scan accepts single-quoted href '
                        'attributes and counts every <tr> containing a <td> inside every '
                        '<tbody>, including proposal and specification rows. Both counts are '
                        'published so the owner can adjudicate; neither is presented as the '
                        'definitive figure.',
    source_url='https://github.com/sassnarep3-star/Own4',
)

SOURCES = [
    dict(id='SRC-01', name='NFL.com 2026 standings (league view)',
         url=STAND, used_for='Official 2026 win/loss/tie, points for and points against for all '
                             '32 clubs; the reconciliation target for the results feed.',
         status='live, read 2026-11-14'),
    dict(id='SRC-02', name='NFL.com 2026 schedule by week (weeks 1-10)',
         url=SCHED.format(w='1'), used_for='Every official final score and kickoff date in the '
                                          'results feed, plus the official per-game URL used as '
                                          'the source link on every result row.',
         status='live, read 2026-11-14'),
    dict(id='SRC-03', name='NFL.com 2025 final standings',
         url=STAND25, used_for='The pre-season prior for the walk-forward model. Published '
                               'before the 2026 season, so it cannot leak.',
         status='live, read 2026-11-14'),
    dict(id='SRC-04', name='NFL.com official Week 10 injury report',
         url=INJ, used_for='Every row of the injury register: player, position, injury, practice '
                           'status, game status. Transcribed verbatim including published blanks.',
         status='live, read 2026-11-14'),
    dict(id='SRC-05', name='NFL.com player pages (per-game logs exist)',
         url='https://www.nfl.com/players/drake-maye/stats',
         used_for='Confirms that official per-game player logs are published, which is why prop '
                  'outcomes are knowable even though prop prices are not.',
         status='live'),
    dict(id='SRC-06', name='NFL.com team depth-chart route',
         url=DEPTH404, used_for='Re-tested this session: returns 404. This is the evidence '
                                'behind flag P-04 that no official depth chart exists.',
         status='404 — the finding, not a broken link on our side'),
    dict(id='SRC-07', name='NFL.com team stats (weekly split)',
         url=STATSWEEK404, used_for='Re-tested this session: returns 404. Only the season-to-date '
                                    'selection resolves.',
         status='404 — the finding behind flag P-09'),
    dict(id='SRC-08', name='NFL.com team stats (season to date)',
         url=STATSALL, used_for='Read for context. Deliberately NOT used as a model feature, '
                                'because a season-to-date table cannot be reconstructed '
                                'point-in-time without look-ahead bias.',
         status='live, read 2026-11-14; excluded from the model'),
    dict(id='SRC-09', name='nflverse/nfldata (third-party archive, CC BY 4.0)',
         url=NFLDATA, used_for='All market prices: closing spread, total, moneylines and the '
                               'attached prices. Also the secondary cross-check on 136 official '
                               'scores.',
         status='third party — the NFL publishes no odds'),
    dict(id='SRC-10', name='nflverse/nfldata data directory listing (GitHub API)',
         url=NFLDATA_API, used_for='Enumerated the archive files to establish that no 2026 '
                                   'opening lines exist: closing_lines.csv ends at 2018, '
                                   'sc_lines.csv at 2020, initial_lines.csv covers 2021 only.',
         status='live, read 2026-11-14'),
    dict(id='SRC-11', name='NFL Football Operations 2026 rulebook',
         url=OPERATIONS, used_for='Rulebook reference for the site footer. Not used to derive '
                                  'any number.',
         status='referenced'),
]
