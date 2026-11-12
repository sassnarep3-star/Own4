"""Question / information / answer register.

Every entry states: the question, what is KNOWN (with an official or repository link),
what is NOT known, why it blocks a decision, and the suggestion that would obtain it.
'answer' is filled only where a verified answer exists; otherwise it stays blank.
"""

KNOWN = "known"
PARTIAL = "partial"
UNKNOWN = "unknown"
BUY = "buy-or-license"
BUILD = "build-here"
DECIDE = "owner-decision"
BLOCKED = "blocked"

Q = [
 # ---- 1. the fundamental market question ------------------------------------
 dict(id="Q01", group="Market access", status=UNKNOWN, blocks="every betting strategy",
   question="Where do we get a legally usable, archived price history for NFL markets?",
   answer="",
   known="No official NFL source publishes betting lines; the league site renders an odds toggle but exposes no values. Archived closing lines exist only in third-party repositories.",
   known_sources=[
     ("nfl.com/news/competition-committee-approves-revisions-to-injury-report-0ap3000000688693", "https://www.nfl.com/games"),
     ("repo: nfl-quant/data/provenance.json (closing lines from nflverse/nfldata, third-party)", "https://github.com/nflverse/nfldata")],
   unknown="Whether a licensed price archive (or a sportsbook data agreement) is available, and under what terms it may be stored and republished.",
   why_it_blocks="Without archived prices every ROI is priced at an ASSUMED -110. Gate G7 can never pass, so no strategy can reach Gold and no reward can be paid honestly.",
   suggestion="S14 - buy or license an odds archive before spending more effort on model refinement."),

 dict(id="Q02", group="Market access", status=UNKNOWN, blocks="all rewards",
   question="What legal jurisdiction governs the project, and is commercial publication of derived lines permitted?",
   answer="",
   known="Public-advisory helplines exist and are cited site-wide as good practice.",
   known_sources=[("NCPG help and treatment", "https://www.ncpgambling.org/help-treatment")],
   unknown="Operating jurisdiction, licence status, and whether derived probabilities may be shown publicly.",
   why_it_blocks="Reward design, disclaimers and even the legality of publishing picks depend on it.",
   suggestion="S15 - obtain a written legal position before any reward is described as anything other than research points."),

 # ---- 2. the injury / depth question ---------------------------------------
 dict(id="Q03", group="Injuries and depth", status=PARTIAL, blocks="injury-adjusted lines",
   question="Can we obtain reliable 1st/2nd/3rd-string depth-chart labels for all 32 teams?",
   answer="No official NFL depth chart was found. https://www.nfl.com/depth-charts/ returns HTTP 404.",
   known="The official Week 10 injury report publishes practice status and game status per player for 28 of 32 clubs (LAC and BAL both read 'No Injuries Reported'). Official NFL.com news articles name specific replacements.",
   known_sources=[("Official NFL injury report, Week 10", "https://www.nfl.com/injuries/"),
                  ("NFL.com depth charts (404)", "https://www.nfl.com/depth-charts/")],
   unknown="A machine-readable string chart, and therefore the ability to distinguish '2nd string replaces starter' from 'starter returns'.",
   why_it_blocks="The brief asks for 2nd/3rd/4th-string deficiency tracking. Without official string labels, any such label would be invented by this project.",
   suggestion="S02 - publish only the 13 replacements that an official NFL.com article explicitly names, and label the rest BLOCKED."),

 dict(id="Q04", group="Injuries and depth", status=UNKNOWN, blocks="historical injury backtests",
   question="Is there an official archive of past-week practice reports?",
   answer="",
   known="nfl.com/injuries/ shows only the current week.",
   known_sources=[("Official NFL injury report", "https://www.nfl.com/injuries/")],
   unknown="Any official historical snapshot.",
   why_it_blocks="Injury effects cannot be measured, so no injury signal can pass any validation gate. Any claimed injury edge would be anecdote, not evidence.",
   suggestion="S16 - capture the official report into a dated JSON snapshot every week starting now, so a backtest becomes possible in a future season."),

 dict(id="Q05", group="Injuries and depth", status=UNKNOWN, blocks="depth-weighted ratings",
   question="How should a missing starter be converted into a points adjustment?",
   answer="",
   known="The official injury designations are defined by the Competition Committee and contain no numeric value.",
   known_sources=[("Competition Committee injury-report revisions", "https://www.nfl.com/news/competition-committee-approves-revisions-to-injury-report-0ap3000000688693")],
   unknown="A published, official points-per-player impact. None exists.",
   why_it_blocks="Any adjustment would be a modelling assumption. It must be pre-registered and treated as a hypothesis, never as a verified quantity.",
   suggestion="S03 - hold the adjustment at zero until the depth table has enough observations to estimate it."),

 # ---- 3. strategy / validation questions -----------------------------------
 dict(id="Q06", group="Strategy and validation", status=KNOWN, blocks="nothing - answered",
   question="Does a model built only from archived scores beat the closing line?",
   answer="No. Holdout (2018-2025): the best spread strategy returned +1.09% at an ASSUMED -110 with a 95% bootstrap CI of [-4.65%, +7.03%] and FDR q = 0.199. It cannot be distinguished from luck.",
   known="Full backtest in data/backtest.json; methodological detail on the Validation page.",
   known_sources=[("repo: nfl-decision/data/backtest.json", "https://github.com/sassnarep3-star/Own4/blob/main/nfl-decision/data/backtest.json")],
   unknown="Whether additional inputs (injuries, depth, pace, weather) would change this. That is a hypothesis, not a finding.",
   why_it_blocks="It does not block; it sets the honest baseline. 0 of 1000 reward points are awarded.",
   suggestion="S08 - stop refining the spread model and redirect effort to the forecast leaderboard, which is price-independent."),

 dict(id="Q07", group="Strategy and validation", status=PARTIAL, blocks="Gold tier for any strategy",
   question="What sample size do we need before a 55% hit rate is distinguishable from luck?",
   answer="At 80% power and a two-sided 5% test, detecting 55% against the 52.4% break-even needs roughly 620 bets.",
   known="Computed in 03_backtest.py; the holdout supplied 948 S1 bets but only across 8 seasons with 1 dominant season.",
   known_sources=[("repo: nfl-decision/data/backtest.json (G2/G5 diagnostics)", "https://github.com/sassnarep3-star/Own4/blob/main/nfl-decision/data/backtest.json")],
   unknown="Whether the owner is willing to fund a multi-season forward paper-trading period. That is the only way to reach that n honestly.",
   why_it_blocks="Rewards paid on fewer than 300 bets would be rewarding luck.",
   suggestion="S09 - pay forecast-skill rewards now and hold betting rewards until a forward record exists."),

 dict(id="Q08", group="Strategy and validation", status=PARTIAL, blocks="prop strategies",
   question="Are player-prop combos positively correlated enough to break independent pricing?",
   answer="Yes, strongly. P(QB pass-yards over) = 0.4645, P(WR1 rec-yards over) = 0.4072, joint = 0.2740 vs 0.1892 if independent - a lift of 1.45x, phi = 0.346 with a 95% CI of [0.284, 0.406].",
   known="Measured on 803 team-games from 2021-2022 archived per-player box scores. Thresholds are PROXY lines (rolling means), not sportsbook prices.",
   known_sources=[("repo: nfl-quant/data/prop_combo_legs.csv (third-party PFR-schema archive)", "https://github.com/fantasydatapros/LearnPythonWithFantasyFootball")],
   unknown="The price a sportsbook would charge for the same combo - books reprice correlated SGP legs, so the lift may already be in the price.",
   why_it_blocks="G7 blocks it: without archived SGP prices the +45% lift is not demonstrably tradeable.",
   suggestion="S10 - pursue archived SGP prices; this is the single most promising unpriced signal in the repo."),

 dict(id="Q09", group="Strategy and validation", status=KNOWN, blocks="nothing - answered",
   question="Can parlay legs be multiplied together as if independent?",
   answer="Yes for cross-game legs. phi between two same-week cover legs = -0.0057 with a bootstrap CI spanning 0, and the same-week cover-count chi-square/df ratio is close to 1.0 (no overdispersion). Same-game cover and over legs are also near-independent (phi = 0.0077).",
   known="Computed over 7,087 games and 472 weeks.",
   known_sources=[("repo: nfl-decision/data/correlations.json (D1, D1b, D2)", "https://github.com/sassnarep3-star/Own4/blob/main/nfl-decision/data/correlations.json")],
   unknown="Nothing for cross-game parlays. For same-game parlays, prop-level dependence is material (Q08) and must be priced.",
   why_it_blocks="It does not block; it licenses the S4 cross-game parlay construction.",
   suggestion="S11 - keep cross-game parlay multiplication and never multiply same-player prop legs without a repricing model."),

 dict(id="Q10", group="Strategy and validation", status=UNKNOWN, blocks="any claim of skill",
   question="What is our definition of 'skill' that cannot be faked by re-running the search?",
   answer="",
   known="The repo pre-registers gates (data/gates.json), freezes model knobs on 1999-2012, and scores 2018-2025 exactly once.",
   known_sources=[("repo: nfl-decision/data/gates.json", "https://github.com/sassnarep3-star/Own4/blob/main/nfl-decision/data/gates.json")],
   unknown="How many strategies may be tried before the family-wise error rate must be re-controlled, and who approves a new strategy as pre-registered.",
   why_it_blocks="Each new strategy tried silently multiplies the false-positive rate. Without a written cap, the leaderboard can be gamed by search.",
   suggestion="S12 - cap the registered family per season and require a written pre-registration before any new threshold is scored."),

 # ---- 4. data right / engineering ------------------------------------------
 dict(id="Q11", group="Data rights", status=UNKNOWN, blocks="publication",
   question="May third-party archives be redistributed on a public site?",
   answer="",
   known="All 2026 scores on the site reconcile 160/160 cells to nfl.com; historical lines and player data come from third-party repositories whose terms must be checked before production use.",
   known_sources=[("nflverse/nfldata terms", "https://github.com/nflverse/nfldata"),
                  ("fantasydatapros archive", "https://github.com/fantasydatapros/LearnPythonWithFantasyFootball")],
   unknown="The rights position on redistribution and on any commercial use.",
   why_it_blocks="Publishing derived tables may be restricted even if the underlying facts are not copyrightable.",
   suggestion="S13 - publish only derived aggregates and link to the archive; store raw data out of Git if a licence requires it."),

 dict(id="Q12", group="Data rights", status=KNOWN, blocks="nothing - answered",
   question="Do the 2026 numbers on this site match an official source?",
   answer="Yes. Every one of the 32 teams' W-L-T, points-for and points-against (160 cells) recomputes exactly from the 136-game log built here, and the game log was reconciled against nfl.com scores and standings.",
   known="01_results.py reproduces this on demand; 5/5 checks pass.",
   known_sources=[("2026 league standings", "https://www.nfl.com/standings/league/2026/REG"),
                  ("Week 9 scores", "https://www.nfl.com/scores/2026/REG9")],
   unknown="Nothing. Any later change to a score invalidates this and must be re-run.",
   why_it_blocks="It does not block; it is the provenance floor for everything else.",
   suggestion="S01 - re-run 01_results.py every week before publishing."),

 dict(id="Q13", group="Data rights", status=UNKNOWN, blocks="prop expansion",
   question="Can we obtain an official 2026 player-level box-score feed?",
   answer="",
   known="The repository's player data is 2021-2022 only. nfl.com/stats is client-rendered and the Stats download policy must be respected.",
   known_sources=[("NFL player stats", "https://www.nfl.com/stats/")],
   unknown="Whether an authorised feed or a licence can be obtained.",
   why_it_blocks="No 2026 props means the prop combos in Q08 cannot be extended to the current season.",
   suggestion="S17 - treat an official player feed as the highest-value data purchase."),

 # ---- 5. product / decision questions -------------------------------------
 dict(id="Q14", group="Product", status=UNKNOWN, blocks="reward design",
   question="What exactly does a 'reward' pay, and who funds it?",
   answer="",
   known="Only non-monetary research points exist today; 1000 betting points and 600 forecast points are proposed, with 0 awarded.",
   known_sources=[("repo: nfl-decision/data/gates.json (reward_policy)", "https://github.com/sassnarep3-star/Own4/blob/main/nfl-decision/data/gates.json")],
   unknown="Budget, funding source, and whether any reward can legally be tied to wagering performance.",
   why_it_blocks="A reward tied to betting ROI in a jurisdiction where that is regulated is a legal question, not a design question.",
   suggestion="S15 - decouple rewards from money; pay in reputation and compute credits until a legal opinion exists."),

 dict(id="Q15", group="Product", status=UNKNOWN, blocks="everything downstream",
   question="Which single dashboard is canonical?",
   answer="",
   known="The repository currently holds five NFL namespaces built by different sessions: nfl/, nfl-research/, nfl-lab/, nfl-quant/ and this nfl-decision/.",
   known_sources=[("repo root navigation", "https://github.com/sassnarep3-star/Own4")],
   unknown="Which one the owner will treat as the source of truth.",
   why_it_blocks="Duplicated, partially conflicting dashboards make it impossible to know which number is authoritative.",
   suggestion="S04 - adopt nfl-decision/ as the decision layer, keep the others as cited archives, and mark superseded pages."),

 dict(id="Q16", group="Product", status=PARTIAL, blocks="nothing - answered",
   question="Is the site actually live and does it build without broken links?",
   answer="Pages is served from the legacy branch build of main. This session verifies every generated page, every internal link and every table row's source before merge.",
   known="GitHub Pages API reported build_type 'legacy', source branch main, path /.",
   known_sources=[("GitHub Pages API", "https://api.github.com/repos/sassnarep3-star/Own4/pages")],
   unknown="Whether the legacy builder will succeed on the next push; it has failed for environmental reasons before.",
   why_it_blocks="It does not block design work, but it must be checked again after merge.",
   suggestion="S18 - verify the deployed URL after merge and record the run id."),
]
