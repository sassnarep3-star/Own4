"""S5 — the requirement register, the suggestion register, the question register and the flag list.

Every requirement in the brief this namespace answers is one row: what was built, where it lives, what
official source verifies it, what still blocks it, and the number that would clear the block. A row is
never marked "done" on the strength of a document existing; the `evidence` column names the artefact
and the `gate` column names the test that the artefact passes or fails.
"""
import os

from common import DATA, REGISTERED_UTC, read_json, write_json

S = "https://www.nfl.com"

REQUIREMENTS = [
    # id, requirement, status, what was built (evidence), artifact, source url, gate, clearing number
    ("R01", "Add a price-snapshot store that records opening and closing numbers for every market we originate",
     "blocked",
     "Two dated snapshots per fixture (open = model through week 9, update = through week 10) for side, "
     "total and moneyline; the market column exists and is blank.",
     "data/lines.json", S + "/schedules/2026/by-week/week-11",
     "market column has no source", "any citable official or licensed price archive"),
    ("R02", "Add a verified results feed so backtests and ROI can be computed",
     "met",
     "148 games, weeks 1-10, every row transcribed from the official week page and every club record "
     "re-derived and checked against the official standings page (160 club-fields, 0 mismatches).",
     "data/results.json", S + "/standings/league/2026/REG", "G3 + independence check", "already met; n grows weekly"),
    ("R03", "Originate the side first, then the total, then the moneyline",
     "met", "Every fixture carries origination_order = [side, total, moneyline] and the build fails if the order changes.",
     "data/lines.json", S + "/schedules/2026/by-week/week-11", "order audit in verify.py", "already met"),
    ("R04", "Publish the model's fair line, the market line, and the difference as separate columns",
     "partial",
     "Fair line and fair total and fair moneyline are published per fixture per snapshot; the market and "
     "difference columns render blank with the reason on the row.",
     "data/lines.json", S + "/schedules/2026/by-week/week-11",
     "no official market source", "one citable price source"),
    ("R05", "Separate 'signal' from 'staking' in the leaderboard so a lucky staking run cannot mask a bad signal",
     "met",
     "Two stages: stage 1 ranks only proper scores (Brier skill with a week-cluster lower bound), stage 2 "
     "shows staking with the price printed on every row and ranked=false.",
     "data/backtest.json", S + "/schedules/2026/by-week/week-10", "G5", "already met"),
    ("R06", "Track the depth of the replacement, not just the fact of a replacement",
     "blocked",
     "Nothing is published: this namespace holds no depth rank or snap count for any club, and does not "
     "infer one from jersey number, salary, experience or draft slot.",
     "", S + "/injuries/", "no official depth source",
     "a verified depth rank or official snap counts for 32 of 32 clubs"),
    ("R07", "Compute correlations only from officially sourced numbers and publish n with each value",
     "met",
     "4 correlations computed on official scores/dates, each with n, p and a Fisher-z interval; a fifth "
     "shows group means with n and prints no r because n = 8.",
     "data/correlations.json", S + "/standings/league/2026/REG", "source audit", "already met"),
    ("R08", "Define a demotion gate that sends a live strategy back to paper",
     "met",
     "G7 is written: a live strategy failing G2 for 4 consecutive weeks returns to paper. No strategy is "
     "live, so the gate has nothing to demote — which is the honest state, not a pass.",
     "PREREGISTRATION.md", S + "/schedules/2026/by-week/week-10", "G7", "one live strategy to exercise it"),
    ("R09", "Pre-register every strategy; forbid backtest numbers from ever appearing on the leaderboard",
     "met",
     "PREREGISTRATION.md is committed (a4f26f5) before any number was computed, and names every strategy "
     "and every gate. The leaderboard's stage 1 shows proper scores; the build fails if a return figure is "
     "rendered there.",
     "PREREGISTRATION.md", S + "/schedules/2026/by-week/week-10", "verify.py L-check", "already met"),
    ("R10", "Build the availability graph as a first-class dataset (who was expected to start, who actually did)",
     "blocked",
     "Not built here. The official injury report gives a game status, not a starter list, and no official "
     "inactive list or game book was read by this namespace.",
     "", S + "/injuries/", "no official inactive/game-book source read",
     "32 clubs x 18 weeks of official game books, or one official inactive feed"),
    ("R11", "Do not model depth from jersey order; model it from playing time",
     "rejected-as-specified",
     "Rejected explicitly: neither jersey order nor playing time is available from an official source in "
     "this repository, so no depth model is fitted at all.",
     "", S + "/injuries/", "n/a", "official snap counts"),
    ("R12", "Make the injury signal a surprise, never a level",
     "blocked",
     "Not built: a surprise needs a prior expectation (a depth chart) and a realised outcome (an inactive "
     "list). This namespace has neither, so it publishes no injury feature.",
     "", S + "/injuries/", "no prior, no realisation",
     "one archived weekly report series plus inactive lists"),
    ("R13", "Run the 32-team roster/IR sweep before any team-level model is trusted",
     "blocked",
     "The team-level model here is trusted only for the ratings page, and its forecasts are gated by G1/G2. "
     "No roster sweep was run by this namespace.",
     "", S + "/teams/", "no roster sweep", "32 club roster pages read line by line, dated"),
    ("R14", "Add a fixture-context feature set built only from published schedule facts",
     "met",
     "Date, kickoff, network, the printed section (which is how the international flag is sourced), rest "
     "days from printed dates, and venue from the game centre — all per fixture.",
     "data/lines.json + data/correlations.json", S + "/schedules/2026/by-week/week-11", "source audit",
     "already met"),
    ("R15", "Store every model output as a probability plus its inputs, not just a pick",
     "met",
     "116 walk-forward rows + 26 Week 11 snapshot rows, each carrying p, mu, hfa, sigma, both clubs' "
     "ratings, the cutoff week and the training count.",
     "data/forecast_register.json", S + "/schedules/2026/by-week/week-10", "verify.py I-check", "already met"),
    ("R16", "Compute and publish the 'removal of luck' panel on the site dashboard",
     "met",
     "Five registered luck tests: label-shuffle placebo, coin-flip counterfactual, week-cluster bootstrap, "
     "half-sample persistence, and a fade control. All five are on the dashboard.",
     "data/backtest.json", S + "/schedules/2026/by-week/week-10", "G4", "already met"),
    ("R17", "Add a two-sided 'what would change our mind' field to every strategy entry",
     "met",
     "Every strategy row carries both directions: what would promote it and what would demote it, with the "
     "number attached.",
     "data/strategies.json", S + "/schedules/2026/by-week/week-10", "verify.py W-check", "already met"),
    ("R18", "Price a line ourselves and publish the residual against the market, on a schedule, from day one",
     "partial",
     "The pricing side is published (two dated snapshots, 13 fixtures, three markets). The residual is not, "
     "because there is no official market number to subtract.",
     "data/lines.json", S + "/schedules/2026/by-week/week-11", "no market source",
     "one citable closing-price archive"),
    ("R19", "Turn the 136-game log into the pre-registered backtest corpus",
     "met",
     "The official week pages print 16+16+16+16+15+14+14+14+15 = 136 FINAL games across weeks 1-9, which is "
     "exactly the brief's log, and 12 more in week 10 (two week-10 games were still unplayed at the read), "
     "for 148. The pre-registered corpus is the 136-game log, and the walk-forward window extends to 148 "
     "because those 12 games are also official and final.",
     "PREREGISTRATION.md + data/results.json", S + "/schedules/2026/by-week/week-9", "C1 per-week count",
     "already met"),
    ("R20", "Decide the price-data policy before any backtest is published",
     "met",
     "Policy is stated in the pre-registration before the backtest: no official price exists, so ROI is "
     "reported only at a labelled assumed price and is never ranked.",
     "PREREGISTRATION.md", S + "/schedules/2026/by-week/week-10", "policy audit", "already met"),
    ("R21", "Store every injury-hub read with its clock time and publish the delta, never the level",
     "blocked",
     "This namespace read no injury page, so it publishes no injury level and no delta. Peer namespaces hold "
     "the dated captures; this page links to them rather than copying them.",
     "", S + "/injuries/", "no capture in this namespace", "daily captures with hashes, 3+ weeks"),
    ("R22", "Put a decision-readiness table on the landing page: one row per requirement, with the gate that "
     "blocks it and the number that would clear it",
     "met", "The landing page is that table.", "index.html", S + "/schedules/2026/by-week/week-10",
     "verify.py R-check", "already met"),
    ("R23", "Transcribe the venue of every fixture from the official game centre and publish it",
     "met",
     "13 of 13 Week 11 fixtures, city and stadium exactly as printed, each with its game-centre URL.",
     "data/venues.json", S + "/games/colts-at-texans-2026-reg-11", "source audit", "already met"),
    ("R24", "Publish the league's dated schedule announcement beside the live schedule page",
     "partial",
     "The live schedule statement is linked and cited. A dated league announcement of the 2026 schedule was "
     "not read by this namespace, so it is not quoted.",
     "data/sources.json", S + "/schedules/2026/by-week/week-11", "no dated announcement read",
     "one dated nfl.com schedule-release article"),
    ("R25", "Use official NFL Game Books for actual starters and game-day status",
     "blocked", "No game book was read. Nothing on this site is derived from one.",
     "", S + "/scores/2026/week-10", "no game book read", "one official game book PDF per game"),
    ("R26", "Ingest game-level results to make the ratings opponent-aware",
     "met",
     "The ratings solve a two-sided system in which a club's offence is measured only through what it did "
     "against the defences it actually faced.",
     "data/model.json", S + "/schedules/2026/by-week/week-10", "G3", "already met"),
    ("R27", "Add injury and personnel ablations instead of fixed penalties",
     "blocked",
     "No ablation is run, because there is no availability feature to ablate. No fixed penalty for a "
     "missing starter exists anywhere in this namespace.",
     "", S + "/injuries/", "no availability feature", "one archived availability series"),
    ("R28", "Automate immutable multi-day availability snapshots",
     "not-started-here",
     "Out of scope for this namespace by design (no scheduled collector, no writes outside nfl-sources/). "
     "Peer namespaces hold the dated captures; the gap is real and is not claimed as closed.",
     "", S + "/injuries/", "no scheduler in this namespace", "a scheduled collector with hashes"),
    ("R29", "Fix the two depth-parsing failures before widening coverage",
     "not-started-here", "This namespace never parsed a depth chart, so it cannot have broken one.",
     "", S + "/injuries/", "n/a", "a depth source for 32 clubs"),
    ("R30", "Model depth slots as groups, not a single starter",
     "not-started-here", "Not modelled here at all (see R06).", "", S + "/injuries/", "n/a",
     "a depth source that preserves ties"),
    ("R31", "Treat roster turnover as a first-class data event",
     "not-started-here",
     "This namespace keys nothing to a roster version. Peer namespaces document two Week-10 trades; this "
     "page links to that evidence rather than restating it.",
     "", S + "/news/", "no roster-version join", "a dated transactions feed joined to depth rows"),
    ("R32", "Start with a singles-only shadow baseline",
     "met",
     "S1 is a singles-only shadow baseline: every forecast is recorded before kickoff and graded after, "
     "and no money is modelled.",
     "data/forecast_register.json", S + "/schedules/2026/by-week/week-10", "G1", "already met"),
    ("R33", "Keep parlays and prop combos behind a joint-evidence gate",
     "met",
     "G6 blocks them: no joint probability has been validated and no operator void/push rules are "
     "available, so no parlay is ranked.",
     "PREREGISTRATION.md", S + "/schedules/2026/by-week/week-10", "G6", "already met; n = 0 legs priced"),
    ("R34", "Use proper-score leaderboard divisions",
     "partial",
     "The leaderboard has one division (singles) because that is the only division with any graded rows. "
     "Game parlays, same-game parlays and prop combos have 0 rows each and say so.",
     "data/backtest.json", S + "/schedules/2026/by-week/week-10", "0 rows in 3 divisions",
     "at least one joint evidence set"),
    ("R35", "Rank with proper scores and uncertainty, not win rate",
     "met",
     "Ranking is by Brier skill with a week-cluster lower bound; accuracy is shown but never ranks, and the "
     "page shows why (the record-only control scores 0.652 accuracy).",
     "data/backtest.json", S + "/schedules/2026/by-week/week-10", "G2", "already met"),
    ("R36", "Add durable snapshot storage and alerts",
     "not-started-here",
     "Out of scope here. What this namespace does instead: every input is hashed in data/provenance.json "
     "so a silent edit to a transcription is detectable.",
     "data/provenance.json", S + "/schedules/2026/by-week/week-10", "no scheduler", "a scheduled collector"),
    ("R37", "Split the site into a public analysis layer and a private data layer",
     "partial",
     "This site publishes derived analysis (lines, probabilities, scores, correlations). Row-level raw data "
     "is limited to final scores, which are public facts quoted from the official page; no proprietary "
     "feed, no scraped availability data, and no player-level data are committed.",
     "nfl-sources/data/", S + "/schedules/2026/by-week/week-10", "policy review", "a licensing decision"),
    ("R38", "Add a per-team view: starters out, replacements named, net injury count",
     "blocked", "Not published: this namespace has no starters-out column it can verify.",
     "", S + "/injuries/", "no availability data", "official inactive lists"),
    ("R39", "Add an announced-starter evidence field (not an inferred replacement)",
     "not-started-here",
     "Not attempted here; the field needs the official announcements, which this namespace did not read.",
     "", S + "/news/", "n/a", "dated official starter announcements"),
    ("R40", "Add an official depth-chart register with date and source per row",
     "not-started-here", "Not attempted here.", "", S + "/injuries/", "n/a", "32 verified club depth pages"),
    ("R41", "Calibrate what 'Questionable' means empirically instead of using old percentages",
     "blocked",
     "The reliability bins published here are for the MODEL's probabilities, not for a designation. The "
     "designation calibration needs archived reports joined to inactive lists.",
     "data/backtest.json", S + "/injuries/", "no designation history",
     "3+ seasons of reports joined to inactive lists"),
    ("R42", "Interactive offence-vs-defence deficiency matrix (1st-4th string)",
     "blocked",
     "Not built: it requires a depth rank per club, which does not exist in this repository. Building it from "
     "anything else would fabricate starters.",
     "", S + "/injuries/", "no depth rank", "32 clubs x a verified depth source"),
    ("R43", "Flag stale depth rows against the official transactions log",
     "not-started-here", "No depth rows exist here to be stale.", "", S + "/news/", "n/a",
     "a dated transactions feed"),
    ("R44", "Point-in-time snapshot ledger for injuries, depth charts and inactives",
     "not-started-here",
     "This namespace's point-in-time ledger covers forecasts only: every forecast row records its cutoff "
     "week and is checked by G3 (mutating later results changes no earlier forecast).",
     "data/forecast_register.json", S + "/schedules/2026/by-week/week-10", "G3", "availability captures"),
    ("R45", "Populate the three missing Lions game-status designations",
     "not-this-namespace",
     "The peer capture is the record here; this namespace does not re-publish injury rows, so it neither "
     "confirms nor contradicts it. The live report was read once while checking a different claim; see FL-04.",
     "", S + "/injuries/", "owned by the availability namespaces", "their re-capture"),
    ("R46", "Re-capture and republish the Week 10 injury tables",
     "not-this-namespace", "Owned by the availability namespaces; see FL-04 for one observation made here.",
     "", S + "/injuries/", "peer scope", "their re-capture"),
    ("R47", "Reject: deriving depth order from jersey number, experience or salary",
     "rejected-as-specified",
     "Rejected in the pre-registration and in the code: no such derivation exists in this package.",
     "PREREGISTRATION.md", S + "/injuries/", "code audit", "not applicable"),
    ("R48", "Represent shared and empty depth slots faithfully",
     "not-started-here", "No depth data here, so nothing is flattened.", "", S + "/injuries/", "n/a",
     "a depth source that preserves ties and blanks"),
    ("R49", "Resolve the depth-order source before building the backup-deficiency feature",
     "blocked", "Not built, exactly as instructed.", "", S + "/injuries/", "route not verified",
     "one verified route for 32 of 32 clubs"),
    ("R50", "Score injury-designation reliability before using it as a feature",
     "blocked", "Not built; no designation history here.", "", S + "/injuries/", "no history",
     "several seasons of designations + inactives"),
    ("R51", "Snapshot the injury report every Wed, Thu and Fri and keep a dated history",
     "not-started-here", "Out of scope here.", "", S + "/injuries/", "no scheduler", "a scheduled collector"),
    ("R52", "Treat the injury report as a timestamped series, not a weekly snapshot",
     "not-started-here", "Out of scope here.", "", S + "/injuries/", "no captures", "daily capture series"),
    ("R53", "Use snap counts as the starter proxy when the depth chart is unavailable",
     "blocked", "No snap counts were read, so none are used.", "", S + "/injuries/", "no snap-count source",
     "an official snap-count source"),
    ("R54", "Add a control baseline (random picks; favourites only) to every leaderboard run",
     "met",
     "Two controls run on the same games: a coin flip and a record-only rule. Both are on the leaderboard "
     "page, and the record-only control is what shows the model's edge is not yet separable from zero.",
     "data/backtest.json", S + "/schedules/2026/by-week/week-10", "control present", "already met"),
    ("R55", "Stadium roof/surface and NWS hourly wind/precipitation overlay",
     "blocked",
     "Not built: the official game centre prints a descriptive weather word, not a roof/surface "
     "specification, and no NWS grid was read.",
     "", S + "/games/colts-at-texans-2026-reg-11", "no roof/surface or NWS source",
     "official stadium specifications + an NWS archive"),
    ("R56", "Two-stage skill leaderboard (proper-score qualification, then prospective CLV/ROI escrow)",
     "met",
     "Implemented as two stages; stage 2 is explicitly not ranked and prints the assumed price.",
     "data/backtest.json", S + "/schedules/2026/by-week/week-10", "G5", "already met"),
    ("R57", "Vig-free market consensus vs originated fair-line decomposition",
     "blocked",
     "The decomposition needs a market consensus. With no official price there is no vig to remove.",
     "", S + "/schedules/2026/by-week/week-11", "no market source", "a citable price archive"),
    ("R58", "Publish a weekly 'what changed' diff instead of a static snapshot",
     "met",
     "The lines page prints the open-to-update movement per fixture per market, and the ratings table "
     "prints both cutoffs side by side.",
     "data/lines.json", S + "/schedules/2026/by-week/week-11", "diff present", "already met"),
    ("R59", "Publish every model total twice until one wins",
     "met",
     "Two total estimators are published with their gap: (a) the fitted total, (b) the fitted total under "
     "the ridge-identified level split. The gap is published per fixture and neither is collapsed.",
     "data/lines.json", S + "/schedules/2026/by-week/week-11", "both published", "already met"),
    ("R60", "Add a drift alarm to every scraper",
     "met",
     "Every builder asserts its expected row count, club coverage and field set, and fails the build "
     "instead of publishing a blank. verify.py re-runs every gate.",
     "engine/verify.py", S + "/schedules/2026/by-week/week-10", "verify.py", "already met"),
    ("R61", "Capture the reserve list so 'not listed' never means 'available'",
     "not-started-here", "No reserve/IR list was read by this namespace.", "", S + "/injuries/", "no IR source",
     "an official roster/IR page read dated"),
    ("R62", "Reject: ranking strategies by season-long ROI",
     "rejected-as-specified",
     "Rejected in the pre-registration; ROI is printed only as an unranked sensitivity at a labelled price.",
     "PREREGISTRATION.md", S + "/schedules/2026/by-week/week-10", "code audit", "not applicable"),
    ("R63", "Archive weekly injury reports for past seasons",
     "not-started-here", "Out of scope here.", "", S + "/injuries/", "no archive", "an archived series"),
    ("R64", "Freeze a rule before it sees data (pre-registration)",
     "met",
     "PREREGISTRATION.md is committed as a4f26f5, before data/build_model.py existed. The commit is the "
     "registration and the site prints its hash.",
     "PREREGISTRATION.md", S + "/schedules/2026/by-week/week-10", "git history", "already met"),
    ("R65", "Split data into train, validation and final holdout seasons",
     "partial",
     "Within one season there is no second season to hold out. What is done instead: weekly walk-forward "
     "with the two earliest weeks burned in and never scored, plus a half-sample persistence test. A real "
     "final holdout needs a prior season that this namespace did not read.",
     "data/backtest.json", S + "/schedules/2026/by-week/week-10", "one season only",
     "one archived prior season (a 2025 results read)"),
    ("R66", "Create a suggestions section so suggestions can be reviewed and chosen before implementation",
     "met",
     "18 suggestions, each with options, cost, the number that would clear it, and an explicitly BLANK "
     "verdict — the reviewer chooses.",
     "data/suggestions.json", S + "/schedules/2026/by-week/week-10", "verdicts blank by rule", "already met"),
    ("R67", "Originate my own NFL lines and build a leaderboard competition with rewards",
     "partial",
     "Lines are originated for all 13 Week 11 fixtures and a leaderboard exists with rewards defined. No "
     "reward is awarded, because no strategy passes G1 or G2.",
     "data/backtest.json", S + "/schedules/2026/by-week/week-11", "G1 + G2", "n >= 300 graded games and a "
     "Brier-skill lower bound above 0"),
    ("R68", "Track injuries and know deficiencies where backups replace starters",
     "blocked",
     "Not built. This page states the block and the clearing number instead of approximating it.",
     "", S + "/injuries/", "no depth/snap source", "32 clubs x a verified depth or snap source"),
    ("R69", "Work line by line, verify from official sources, no hallucinations",
     "met",
     "Every figure on this site is produced by the package from a committed transcription; a row without an "
     "official source URL does not render, and unreadable values are blank + flagged.",
     "data/provenance.json", S + "/schedules/2026/by-week/week-10", "verify.py U-check", "already met"),
    ("R70", "Provide an executive summary with links for manual review",
     "met", "EXECUTIVE_SUMMARY.md and the Executive summary page, every claim linked to its source.",
     "EXECUTIVE_SUMMARY.md", S + "/schedules/2026/by-week/week-10", "link audit", "already met"),
]

SUGGESTIONS = [
    ("SUG-01", "Adopt a licensed price archive, or state formally that no price column will ever be published",
     "R01/R04/R18/R57", "A: buy a licensed archive. B: state the policy and delete the column. C: keep the "
     "column blank and flagged (current).",
     "Every residual, every ROI and every CLV number in the repository is currently unfalsifiable.",
     "A: cost of a licence + legal review. B: no cost, loses the residual. C: no cost, the site keeps a "
     "permanently blank column.", "one citable price source", ""),
    ("SUG-02", "Add a prior season to create a real final holdout",
     "R65", "A: read 2025 week pages the same way (17 weeks of pages). B: refit the model to and hold out "
     "the second half of 2026 only.",
     "The current half-sample persistence test is weaker than a season-level holdout.",
     "A: ~18 more page reads, one session. B: no cost, weaker evidence.", "one archived prior season", ""),
    ("SUG-03", "Publish a walk-forward multi-season rating with uncertainty bands per club",
     "R26", "A: bootstrap the ratings by resampling games. B: report a fitted-rating interval analytically.",
     "The ratings page shows point estimates only; a two-point gap between clubs is not yet distinguishable.",
     "A: one engine function + 2 000 resamples (~1 s). B: closed form, no bootstrap.",
     "a published per-club interval", ""),
    ("SUG-04", "Extend the walk-forward register to Weeks 11-18 as the season is played",
     "R32/R35", "A: append each week after it is final. B: one end-of-season rebuild.",
     "Prospective samples are the only ones that cannot be overfit; the current 116 forecasts are in-sample "
     "for the season but out-of-sample per week.",
     "A: one page read per week. B: 18 page reads at the end.", "n >= 300 graded games", ""),
    ("SUG-05", "Register and test a rest-day-aware model as a separate, pre-registered strategy",
     "R14/R35", "A: add rest differential as a term in a NEW registered model. B: leave the baseline alone.",
     "CR-04 is the strongest signal found (r = 0.373, n = 132) and the baseline ignores it.",
     "A: one model variant + the same gates. B: zero.", "a registered variant that clears G2", ""),
    ("SUG-06", "Decide what a 'reward' is before any strategy can earn one",
     "R67", "A: none (research only). B: non-monetary recognition. C: a defined scoring currency.",
     "A reward policy that cannot be exercised is untested policy.",
     "A: zero. B/C: a policy decision that is the owner's, not this session's.", "an owner decision", ""),
    ("SUG-07", "Consolidate the 30+ NFL namespaces into one navigable site",
     "R22/R69", "A: keep the root dashboard as the only entry point and deprecate the rest. "
     "B: merge data files. C: leave as is.",
     "A reader currently has to choose between namespaces that disagree about the same facts (see FL-10).",
     "A: a navigation decision. B: a merge conflict risk across sessions. C: zero.", "an integration decision",
     ""),
    ("SUG-08", "Reconcile the two Week 10 injury row counts and publish one dated number",
     "R45/R46", "A: one owner re-reads the page and publishes the count with a timestamp. B: publish both "
     "counts with both timestamps.",
     "This namespace observed 348 player rows while peers publish 347 and 279; see FL-04.",
     "A: one page read. B: zero (both are already timestamped).", "a dated, single-owner re-capture", ""),
    ("SUG-09", "Publish the season-to-date record for every club from the corpus, with the official page beside it",
     "R02", "A: add a standings page generated from the corpus. B: link to nfl.com only.",
     "The corpus already passes an exact 160-field check against the official standings, so a generated "
     "table costs nothing and makes the check visible.",
     "A: one engine function. B: zero.", "already met", ""),
    ("SUG-10", "Add the 2025 season to the correlation set to test whether CR-04 replicates",
     "R07", "A: read 2025 week pages. B: wait for 2026 to finish.",
     "One season's r = 0.373 with n = 132 is suggestive, not established.",
     "A: ~18 page reads. B: 8 more weeks.", "a replicated CR-04", ""),
    ("SUG-11", "Replace the normal-approximation p-values with exact t quantiles",
     "R07", "A: implement the incomplete beta function (stdlib). B: keep the approximation and disclose it.",
     "The p column is disclosed as approximate; at n = 8 that matters.",
     "A: ~40 lines of careful maths + tests. B: zero.", "not blocking", ""),
    ("SUG-12", "Publish the model's own calibration with intervals, not just bins",
     "R16", "A: add a week-cluster bootstrap to each reliability bin. B: keep the table as a diagnostic.",
     "Two of the five bins are visibly off the diagonal and it is not yet possible to say whether that is "
     "noise.",
     "A: one function, reuses the bootstrap. B: zero.", "a binned interval", ""),
    ("SUG-13", "Make the international-game flag a sourced column rather than a derivation",
     "R14", "A: quote the official section heading on every row (done) and stop calling it neutral "
     "(done). B: also record whether the printed home club is the designated host.",
     "The NFL does not print 'neutral'; a derivation that silently becomes a fact is exactly the failure "
     "mode this repository keeps finding.",
     "A: done. B: needs one more read per fixture.", "already met (A)", ""),
    ("SUG-14", "Add a per-club model page with the inputs and the interval",
     "R15", "A: one page per club generated from model.json. B: one table on the ratings page.",
     "A scout-style reader wants one club, not 32 rows.",
     "A: 32 pages. B: one table (cheaper).", "an owner preference", ""),
    ("SUG-15", "Test the model against the closing line once a price archive exists",
     "R01", "A: recompute residuals against closing prices. B: do nothing until a source exists.",
     "Until then, the residual column is blank and any claimed edge is unfalsifiable.",
     "A: depends on SUG-01. B: zero.", "a price archive", ""),
    ("SUG-16", "Publish the excluded games as a first-class table, not a footnote",
     "R02", "A: one table of games not yet final with the time read. B: a footnote (current).",
     "Two Week 10 games are deliberately absent from every metric; a reader deserves to see which.",
     "A: already in results.json, needs a render. B: done.", "already available", ""),
    ("SUG-17", "Add a stability check: how much do the Week 11 lines move when one game is removed?",
     "R26/R59", "A: leave-one-game-out on the Week 11 lines. B: leave-one-week-out on the ratings.",
     "A line that moves 2 points when one Week 10 game is deleted is not a line, it is noise.",
     "A: 148 refits (~1 s). B: 10 refits.", "a published stability number", ""),
    ("SUG-18", "Reconcile the corpus size phrasing across the repository: 136 IS weeks 1-9",
     "R19", "A: describe the archive as '136 games, weeks 1-9' everywhere. B: keep an unqualified number and "
     "footnote the window.",
     "The brief's 136 is exactly right for weeks 1-9; only an unqualified '148' or '137' would be wrong. Naming "
     "the window costs one clause and removes a recurring confusion.",
     "A: a text edit in each peer namespace (not owned here). B: zero.", "one number with its window, one owner",
     ""),
]

QUESTIONS = [
    ("Q01", "Which price source, if any, will be authorised?",
     "Nothing market-related can be published without it. The site's residual, ROI and CLV columns are all "
     "blank or labelled hypothetical until this is answered.",
     "Owner", "blocks R01, R04, R18, R57"),
    ("Q02", "Is a licensed feed acceptable, or must every number come from a free public page?",
     "Changes the entire collection design, and the answer decides whether the depth/snap items are "
     "reachable at all.", "Owner", "blocks R06, R49, R53, R68"),
    ("Q03", "What counts as a 'reward' in the competition?",
     "No reward has been awarded and none will be until the owner defines one.",
     "Owner", "blocks R67"),
    ("Q04", "Should this site replace the root dashboard, or live beside it?",
     "There are now more than 30 NFL namespaces. One entry point is a product decision.",
     "Owner", "affects navigation only"),
    ("Q05", "Should the leaderboard's official sample be frozen at the 136-game log (weeks 1-9) or extended each week?",
     "The arithmetic now matches the brief exactly (weeks 1-9 = 136 final games). What is still the owner's "
     "call is whether the graded sample may grow past 136 as week 10+ results arrive, or whether a frozen "
     "136-game sample is the permanent reference.",
     "Owner", "affects R19, R65, G1"),
    ("Q06", "Will the owner permit a scheduled collector to run in this repository?",
     "Without it there is no multi-day history, so no surprise-based injury feature and no honest ablation.",
     "Owner", "blocks R21, R27, R28, R51, R52"),
    ("Q07", "How much compute and wall-clock time per week is acceptable?",
     "The bootstrap and placebo tests are cheap now (under two seconds); a per-club interval plus a "
     "leave-one-game-out stability check multiplies that, still seconds.", "Owner", "not blocking"),
    ("Q08", "Is the club abbreviation set in this namespace the one the owner wants displayed?",
     "nfl.com prints AZ and LA rather than ARI and LAR; this site keeps what the official page prints.",
     "Owner", "cosmetic"),
    ("Q09", "Should a tie be scored as half a win in any accuracy figure?",
     "The official standings count ties as half a win, but an accuracy metric counting a tie as 'correct' "
     "would be a modelling claim, not a fact. This namespace excludes them and publishes the count.",
     "Owner", "affects R35"),
    ("Q10", "Does the owner want the excluded/incomplete games shown prominently?",
     "Two Week 10 fixtures are absent from every metric. They are listed on the results page and in the "
     "data; prominence is a design choice.", "Owner", "cosmetic"),
    ("Q11", "What is the minimum evidence the owner will accept as 'skill'?",
     "The registered gate is a week-cluster lower bound on Brier skill. If a different bar is intended "
     "(e.g. a full season of prospective forecasts), it should be registered before the season ends.",
     "Owner", "affects G2"),
    ("Q12", "Are the peer namespaces' availability numbers to be treated as verified?",
     "This namespace found 348 player rows where peers publish 347 and 279. One of those is wrong, or the "
     "page changed; the owner should pick one canonical capture.", "Owner + peer sessions", "affects R45/R46"),
]

FLAGS = [
    ("FL-01", "The inherited results feed is 73% unverified",
     "nfl-book/data/results_feed.json marks 105 of 137 rows aggregate_only, i.e. not re-read page by page. "
     "This namespace re-read all 148 and found every shared row correct, so the feed is right but was not "
     "certified. Reconciliation now exists.",
     "https://sassnarep3-star.github.io/Own4/nfl-book/", "resolved by this read (reconciliation published)"),
    ("FL-02", "The brief's 136-game log is exactly weeks 1-9; the site's corpus is 148 because week 10 is also final",
     "Resolved in the source's favour: 16+16+16+16+15+14+14+14+15 = 136 FINAL games across weeks 1-9, and 12 "
     "more final games in week 10 (PIT at CIN and LAC at BAL were still live/unplayed at the read). Peer "
     "pages that describe a 136-game archive are therefore describing weeks 1-9, and are consistent with "
     "this read; a page that says 137 is off by one.",
     "https://www.nfl.com/schedules/2026/by-week/week-9", "resolved (arithmetic on official counts)"),
    ("FL-03", "Arrowhead Stadium is printed as 'ARROWHEAD STADIUM' on the Week 11 game centre",
     "The game centre prints 'StadiumSTADIUMARROWHEAD STADIUM' for the Cardinals at Chiefs fixture, while "
     "the ticket link on the same page names 'GEHA Field at Arrowhead Stadium'. Transcribed exactly as the "
     "Game Info block prints it; the discrepancy is recorded, not corrected.",
     "https://www.nfl.com/games/cardinals-at-chiefs-2026-reg-11", "flagged: naming discrepancy"),
    ("FL-04", "Peer availability captures disagree with each other: 347 rows vs 279 rows, 107 rows for one",
     "Two peer namespaces publish different totals for the same Week 10 report. "
     "nfl-availability-desk/data/availability_snapshot_2026-11-15.csv holds 347 player rows across 28 clubs "
     "with 171 game-status cells filled; the oldest capture in nfl-book holds 107 rows and states on its "
     "face that 6 of 8 page chunks were never read. The owner's brief cites 279 rows / 2 no-injury sections "
     "as a later state of the same page, and 254 as an earlier one. A page regenerated through the week "
     "produces different counts at different clocks, so the counts are not necessarily wrong — but nothing "
     "in the repository shows which clock produced which number. Needs one owner-ordered re-capture with a "
     "timestamp, not a fourth number.",
     "https://www.nfl.com/injuries/", "flagged: peer counts disagree (SUG-08, Q12)"),
    ("FL-05", "The model's Brier skill interval includes zero",
     "The walk-forward Brier skill vs the coin-flip baseline is 0.1198 with a week-cluster 95% interval of "
     "[-0.0148, 0.2635]. The accuracy-vs-0.500 interval clears, but as the page shows, a model-free "
     "better-record rule also clears it. By the registered gate the model is NOT skilful yet.",
     "https://sassnarep3-star.github.io/Own4/nfl-sources/pages/backtest.html", "flagged: gate not cleared"),
    ("FL-06", "The record-only control is not separable from the model",
     "S3 (pick the better win-loss record) beats the model on 25 games and the model beats it on 25; the "
     "paired accuracy difference is +0.026 with an interval of [-0.037, +0.085]. Any claim that the ratings "
     "add value is unsupported on this sample.",
     "https://sassnarep3-star.github.io/Own4/nfl-sources/pages/backtest.html", "flagged: no separation"),
    ("FL-07", "An ARROWHEAD-style naming issue on WA/Washington: game centre prints 'NORTHWEST STADIUM'",
     "The Commanders' Week 11 game centre prints 'StadiumSTADIUMNORTHWEST STADIUM', a former name, while the "
     "ticket link on the same page uses the current sponsorship name. Transcribed as printed.",
     "https://www.nfl.com/games/bengals-at-commanders-2026-reg-11", "flagged: naming discrepancy"),
    ("FL-08", "RELIANT STADIUM is printed for a 2026 Texans home game",
     "The Week 11 Colts at Texans game centre prints 'StadiumSTADIUMRELIANT STADIUM'. That is the stadium's "
     "former name; the page's own ticket link names NRG Stadium. Transcribed as printed and flagged, not "
     "silently corrected.",
     "https://www.nfl.com/games/colts-at-texans-2026-reg-11", "flagged: naming discrepancy"),
    ("FL-09", "The NFL publishes no 'neutral site' designation",
     "International fixtures are printed inside an 'International Game' section on the week page and the "
     "game centre prints a foreign city. This namespace uses that printed section as its only source for "
     "the 0-home-field flag and says so on every row; it never claims the league calls a game neutral.",
     "https://www.nfl.com/schedules/2026/by-week/week-11", "flagged: sourced, but a derivation"),
    ("FL-10", "Rest is the strongest signal found and it is not in the baseline model",
     "CR-04: rest-day differential vs home margin, r = 0.3727, n = 132, 95% CI [0.216, 0.511]. 63% of "
     "games have zero rest differential, so the correlation is carried by 49 games; leave-one-week-out "
     "ranges from 0.329 to 0.426, and the sign split is monotone (+7.48 mean margin with a home rest edge, "
     "-4.65 against). Registered as SUG-05, NOT slipped into the baseline.",
     "https://sassnarep3-star.github.io/Own4/nfl-sources/pages/correlations.html", "flagged: candidate, untested"),
    ("FL-11", "Two Week 10 games are unfinished, so the corpus is 148 not 150",
     "PIT at CIN was printed 'Q1 ... Live' and LAC at BAL was printed as unplayed when read. Both are "
     "excluded from every metric with no score recorded. A later reader will see a different corpus size "
     "for the same code; this is expected and is why the read timestamp is on every page.",
     "https://www.nfl.com/schedules/2026/by-week/week-10", "informational (time-dependent)"),
    ("FL-12", "The assumed -110 price overstates any real return",
     "The staking figures are computed at a flat -110 for consistency with the inherited workspaces. A "
     "winner-picking strategy is settled at a moneyline, and the mean fair price of S1's own picks is about "
     "-273, so the 'ROI' at -110 is not a claim about money. It is not ranked anywhere.",
     "https://sassnarep3-star.github.io/Own4/nfl-sources/pages/backtest.html", "flagged: label on every row"),
    ("FL-13", "The Week 11 bye list could not be confirmed from the page read",
     "The Week 11 page's 'Teams on Bye' block was not rendered in the read window, so no bye list is "
     "asserted for Week 11 even though the fixture list implies six idle clubs. Asserted nowhere; flagged.",
     "https://www.nfl.com/schedules/2026/by-week/week-11", "flagged: unread"),
    ("FL-14", "The tie rule for accuracy is a choice, not a fact",
     "nfl.com counts a tie as half a win in standings; this site excludes ties from accuracy and publishes "
     "the count (2 tie games in the corpus). Different choices would move accuracy by up to one game.",
     "https://www.nfl.com/standings/league/2026/REG", "flagged: policy (Q09)"),
    ("FL-15", "CR-05 prints group means with n = 8 and no r",
     "Eight international games is too few for a correlation. The group means are shown because they are "
     "arithmetic on official scores; no coefficient is printed because it would be noise with a decimal "
     "point. This is a deliberate blank.",
     "https://www.nfl.com/schedules/2026/by-week/week-10", "informational"),
]


# The official page each question / suggestion is about. A question with no page behind it would be
# opinion; these are all about something printed somewhere official.
Q_SOURCE = {
    "Q01": S + "/schedules/2026/by-week/week-11",
    "Q02": S + "/schedules/2026/by-week/week-11",
    "Q03": S + "/schedules/2026/by-week/week-10",
    "Q04": S + "/schedules/2026/by-week/week-10",
    "Q05": S + "/schedules/2026/by-week/week-9",
    "Q06": S + "/injuries/",
    "Q07": S + "/schedules/2026/by-week/week-10",
    "Q08": S + "/standings/league/2026/REG",
    "Q09": S + "/standings/league/2026/REG",
    "Q10": S + "/schedules/2026/by-week/week-10",
    "Q11": S + "/schedules/2026/by-week/week-10",
    "Q12": S + "/injuries/",
    "SUG-01": S + "/schedules/2026/by-week/week-11",
    "SUG-02": S + "/schedules/2026/by-week/week-9",
    "SUG-03": S + "/schedules/2026/by-week/week-10",
    "SUG-04": S + "/schedules/2026/by-week/week-11",
    "SUG-05": S + "/schedules/2026/by-week/week-10",
    "SUG-06": S + "/schedules/2026/by-week/week-10",
    "SUG-07": S + "/schedules/2026/by-week/week-10",
    "SUG-08": S + "/injuries/",
    "SUG-09": S + "/standings/league/2026/REG",
    "SUG-10": S + "/schedules/2026/by-week/week-9",
    "SUG-11": S + "/schedules/2026/by-week/week-10",
    "SUG-12": S + "/schedules/2026/by-week/week-10",
    "SUG-13": S + "/schedules/2026/by-week/week-10",
    "SUG-14": S + "/standings/league/2026/REG",
    "SUG-15": S + "/schedules/2026/by-week/week-11",
    "SUG-16": S + "/schedules/2026/by-week/week-10",
    "SUG-17": S + "/schedules/2026/by-week/week-11",
    "SUG-18": S + "/schedules/2026/by-week/week-9",
}


def main():
    rows = []
    for (rid, req, status, built, artifact, src, gate, clearing) in REQUIREMENTS:
        rows.append({"id": rid, "requirement": req, "status": status, "built": built,
                     "artifact": artifact, "source_url": src, "blocking_gate": gate,
                     "clearing_number": clearing})

    statuses = ["met", "partial", "blocked", "not-started-here", "not-this-namespace",
                "rejected-as-specified"]
    counts = {s: sum(1 for r in rows if r["status"] == s) for s in statuses}

    write_json(os.path.join(DATA, "requirements.json"), {
        "dataset": "nfl_sources_requirements",
        "title": "One row per requirement in the brief, with its blocking gate and the number that clears it",
        "built_utc": REGISTERED_UTC,
        "statuses": {
            "met": "built here, source-linked, and gated by an automated check",
            "partial": "partially built here; the missing part is named in blocking_gate",
            "blocked": "cannot be built from an official source available to this namespace; the clearing number is stated",
            "not-started-here": "deliberately out of this namespace's scope; not claimed (peer namespaces may hold it)",
            "not-this-namespace": "owned by the availability namespaces; not re-published here",
            "rejected-as-specified": "the brief itself rejects it, or it is rejected in the pre-registration",
        },
        "counts": counts, "n_rows": len(rows), "rows": rows,
    })

    write_json(os.path.join(DATA, "suggestions.json"), {
        "dataset": "nfl_sources_suggestions",
        "title": "Suggestions for the owner to review and choose between before anything is implemented",
        "built_utc": REGISTERED_UTC,
        "workflow": ("A suggestion is a decision, not an action. Each row names the options, what the option "
                     "buys, what it costs and the number that would clear the underlying block. The verdict "
                     "column is BLANK by rule: choosing is the reviewer's job, and a session that fills it in "
                     "is making the owner's decision for them."),
        "verdict_rule": "verdict is empty on every row until the owner chooses",
        "rows": [{"id": i, "suggestion": st, "requirements": r, "options": o, "why": w, "cost": c,
                  "clearing_number": n, "verdict": v,
                  "source_url": Q_SOURCE.get(i, S + "/schedules/2026/by-week/week-10")}
                 for (i, st, r, o, w, c, n, v) in SUGGESTIONS],
    })

    write_json(os.path.join(DATA, "questions.json"), {
        "dataset": "nfl_sources_questions",
        "title": "Questions, information needed and the answer that unblocks each decision",
        "built_utc": REGISTERED_UTC,
        "rule": ("A question appears here only if a decision actually depends on it. Each row names who can "
                 "answer it and what it unblocks; none of them is answered by this session on the owner's "
                 "behalf."),
        # every row names the official page the question is about, so a reviewer can check the premise
        "rows": [{"id": i, "question": q, "why_it_matters": w, "who_can_answer": a, "unblocks": u,
                  "source_url": Q_SOURCE.get(i, S + "/schedules/2026/by-week/week-10")}
                 for (i, q, w, a, u) in QUESTIONS],
    })

    write_json(os.path.join(DATA, "flags.json"), {
        "dataset": "nfl_sources_flags",
        "title": "Flagged for review: irregularities, discrepancies and deliberate blanks",
        "built_utc": REGISTERED_UTC,
        "rule": ("Nothing on this list blocks publication. Each item says what was observed, what was not "
                 "done about it, and where to look. Items marked 'naming discrepancy' are transcribed as "
                 "printed and not corrected: a site that silently fixes the source cannot be audited."),
        "n_rows": len(FLAGS),
        "rows": [{"id": i, "title": t, "detail": d, "source_url": u, "status": s}
                 for (i, t, d, u, s) in FLAGS],
    })
    print("requirements:", len(rows), counts)
    print("suggestions:", len(SUGGESTIONS), "questions:", len(QUESTIONS), "flags:", len(FLAGS))


if __name__ == "__main__":
    main()
