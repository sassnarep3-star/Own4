#!/usr/bin/env python3
"""Questions, suggestions, flags, sources and the repository review for the daily desk."""
import json
import os

NS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INJ = "https://www.nfl.com/injuries/"
SCHED10 = "https://www.nfl.com/schedules/2026/by-week/week-10"
SCHED11 = "https://www.nfl.com/schedules/2026/by-week/week-11"
STAND = "https://www.nfl.com/standings/league/2026/REG"
RESERVE = "https://www.nfl.com/transactions/league/reserve-list/2026/11"
TX = "https://www.nfl.com/transactions/"
HIST = "https://www.nfl.com/injuries/league/2024/reg1"
GAME = "https://www.nfl.com/games/colts-at-texans-2026-reg-11"
REPO = "https://github.com/sassnarep3-star/Own4"


def q(i, question, why, have, missing, how, who, blocks, status):
    return {"id": i, "question": question, "why_it_matters": why, "what_we_have": have,
            "what_is_missing": missing, "how_to_find_out": how, "who_answers": who,
            "blocks": blocks, "status": status, "source_url": INJ}


QUESTIONS = [
 q("Q-01", "Do we price from a licensed market feed, from a named third-party archive, or never?",
   "It is the single decision that decides whether ROI, CLV, residuals, vig-free consensus and the "
   "staking half of the leaderboard can exist at all. Nine requirements are downstream of it.",
   "nfl.com publishes no prices (verified again on the Week 11 slate today: schedules, designations and "
   "scores only). nfl-markets already holds 12,573 archive rows whose closing column is filled on "
   "12,246 and whose opening column is filled on 2,587, each labelled to a third-party mirror; two "
   "other namespaces hold 0 price rows by policy and say why.",
   "A written policy. Nothing in the repo records an owner decision, and no capture job exists for "
   "either candidate source.",
   "Pick one option, then start the capture before using it: an archive is only worth having from the "
   "day you start keeping it. 1 decision record + 1 scheduled capture job.",
   "owner (licensing and re-use terms), not an agent",
   ["R-01", "R-04", "R-18", "R-20", "R-55", "R-57", "R-58"], "open - owner decision"),
 q("Q-02", "May official row-level data be re-published in the public site tree, or does it live in a private store?",
   "The brief asks for a public analysis layer and a private data layer. Today every namespace publishes "
   "row-level official tables in the Pages tree, so the split does not exist in any form.",
   "The injury report page is a public league document (read today: 253 rows for 24 clubs); the club "
   "depth pages belong to 32 different club web properties; the Game Book PDFs are a licensed product.",
   "A per-source terms read, and a store the Pages build cannot reach for anything that fails it.",
   "Classify the 5 source families we actually use (league report, club depth page, game centre, "
   "transactions ledger, reserve ledger) as publish/derived-only/private. 5 reads and 1 decision.",
   "owner, with counsel if the answer must be binding",
   ["R-39"], "open"),
 q("Q-03", "Does an official, retrievable weekly injury-report archive exist for past seasons?",
   "Without history, 'Questionable' can never be calibrated and the designation can never be scored for "
   "reliability - two requirements that look like modelling work and are really archive work.",
   "The live page exposes a per-week URL family (/injuries/league/2026/reg11 is the current week's page "
   "and it renders a dated report today), and the year/week selectors are present on the page.",
   "Whether that family resolves for past weeks and past seasons, and whether the render is stable enough "
   "to hash.",
   "Probe 4 URLs for one past week (e.g. 2024 reg1) and publish the result - status code, row count, "
   "sha256 of the render - either way. Under an hour, and it either unlocks two requirements or kills them.",
   "an agent can do this; the owner decides re-use",
   ["R-43", "R-51", "R-64"], "open - cheapest high-value experiment on the list"),
 q("Q-04", "Is there any official source for playing time (snap counts)?",
   "Three requirements insist depth must come from playing time, not jersey order. If the answer is no, "
   "the honest move is to drop the depth-deficiency feature rather than proxy it with rank.",
   "Nothing in the repository holds a snap-count table, and no official public snap-count page has been "
   "located by the sessions that looked. The parsed depth layer holds 897 slots across 31 clubs and 0 "
   "playing-time fields.",
   "A dated statement: which official surface was checked, on what date, with what result - so the "
   "absence becomes evidence instead of folklore.",
   "Either the Game Book participation tables (Q-05) or an explicit 'no official source, feature "
   "cancelled' line in the register.",
   "owner (if a licence is needed), agent (for the negative-evidence log)",
   ["R-06", "R-11", "R-54"], "open"),
 q("Q-05", "What is our access to official NFL Game Books, and in what format?",
   "The Game Book is the only official document that states participation - it is what turns 'suspected "
   "replacement' into 'confirmed replacement', and it is the correct source for actual starters.",
   "The brief instructs that Game Books be used for starters and game-day status; the repository holds "
   "zero Game Book files (verified by search of every namespace's data directory today).",
   "Access itself: licence, format (PDF per game), and a storage location that survives the 128 MB "
   "artifact cap.",
   "One week as a pilot: 13 game centres -> 13 Game Books -> parse the inactives and participation "
   "tables -> publish one confirmed-replacement row. That is the whole proof.",
   "owner", ["R-25", "R-30", "R-46"], "open"),
 q("Q-06", "Where are game-day inactives published, and is that page stable enough to capture?",
   "Every 'who actually did start' claim, and the reliability score of each designation, hangs on a list "
   "of 8 names per club that we currently do not store at all.",
   "The report page today carries no inactive data; the brief's own count (6 of 254 rows with a "
   "designation in a past week) matches what we measure now (16 of 253 today), so the gap is structural, "
   "not a one-week accident.",
   "A capture job for the game-day inactives (26 rows per 13-game week) with a hash per capture.",
   "Add one scheduled capture at 1 hour before each kickoff window and keep it for a week; then the "
   "designation-reliability feature has a denominator.",
   "an agent can build it; owner approves the storage", ["R-30", "R-43", "R-46", "R-51"], "open"),
 q("Q-07", "What do we do about the one club that publishes depth as an image?",
   "A single club is the difference between 'a feature for 31 teams' and 'a feature that can be trusted "
   "league-wide', and the brief forbids transcribing that image by eye.",
   "The peer sweep marks HOU as flagged_image_only with 0 parsed slots while 31 clubs parse as text "
   "(measured today from nfl-depth-sweep/data/parsed: 897 slots, 31 clubs verified_text).",
   "An authorised structured source for that club, or a decision to exclude it explicitly and label every "
   "league-wide statistic as n=31.",
   "Ask the club, use a licensed feed, or exclude - but publish the choice, because a silent 31/32 is how "
   "a league-wide number becomes a lie.",
   "owner", ["R-31", "R-50"], "open"),
 q("Q-08", "How should a depth slot be represented when a club lists several names in one slot, or none?",
   "The brief's requirement is to model slots as groups. If the register's schema cannot hold a group or "
   "an empty slot, then 'the starter' is a fiction produced by the parser rather than by the club.",
   "measured today from the peer parse: 897 slots, 15 rank-1 slots carrying a second name, 22 shared "
   "slots at any rank, and 0 empty slots recorded - the brief's figure of 149 multi-rank-1 slots is not "
   "reproducible from what is stored, and an empty slot appears to be dropped rather than represented.",
   "A schema decision (slot -> list of names + an explicit empty state) and one re-parse to test it.",
   "Re-parse the 31 stored transcripts under the group schema and publish both counts side by side; the "
   "difference between 15 and 149 is itself a finding about how the earlier number was defined.",
   "an agent", ["R-32", "R-49"], "open - flagged as a data-quality defect, not a modelling taste"),
 q("Q-09", "Is a repeated identical capture evidence of 'no change', or of a cached fetch?",
   "Every delta panel in the repository inherits this ambiguity. If we cannot tell, the honest cadence is "
   "'per publish event', not 'per day'.",
   "Two captures 7h15m apart today: the injury report differs in exactly one club block (11 rows appear) "
   "and exactly one player field (1 designation change) out of 241 shared players; the reserve ledger is "
   "identical in both (25 rows, 0 new). Neither page publishes its own last-updated marker in the raw "
   "document (searched for 'Updated'/'updated' in the 371,313-byte capture: 0 matches).",
   "A second observation point (a different client path, or the club's own release) to break ties.",
   "Count distinct document hashes per day instead of captures per day, and alert when a full report "
   "cycle produces a hash we have already seen on a publish day.",
   "an agent", ["R-21", "R-52", "R-53"], "open"),
 q("Q-10", "What exactly is the reward paying for, when staking is not possible?",
   "The brief frames this as a leaderboard competition with rewards for top strategies. If the reward is "
   "tied to ROI it pays for luck and for a data source we do not have; if it is tied to proper scores it "
   "pays for calibration, which is the thing we can actually measure.",
   "Every namespace in the repo that reached a verdict awarded 0 rewards; the frozen rule requires 300 "
   "graded pre-kickoff rows before any skill claim, and the largest pre-kickoff sample in the repository "
   "is 13 rows recorded by two independent registrations.",
   "A reward definition that a verifier can enforce mechanically (metric, sample floor, multiplicity "
   "correction, demotion), instead of a ranking that gets argued about later.",
   "Write 6 lines into the strategy register: metric, floor, correction, demotion, escrow, and what "
   "disqualifies a submission. Then let the leaderboard generator refuse any row that lacks them.",
   "owner", ["R-05", "R-36", "R-57", "R-63"], "open"),
 q("Q-11", "Which results feed is canonical for 2026, and what happens to the numbers built on the others?",
   "Two feeds, two sizes, and a league identity that matches neither today. Any backtest inherits the "
   "staleness of whichever feed its author picked.",
   "measured today: nfl-markets 2026 feed = 137 games (Week 10: 1 game); nfl-live-board corpus = 149; the "
   "official standings imply exactly 150 games played (sum(W+L+T)/2 = 150, and 32 rows' points-for total "
   "6,923 equals the corpus total points after adding LAC 23 at BAL 20).",
   "One canonical feed keyed by game_id, plus a CI assertion that its row count equals the standings "
   "identity every day.",
   "Point every namespace's corpus read at one file and make the build fail when the identity breaks - "
   "the identity check already exists in this desk's compute step and costs nothing to reuse.",
   "an agent (integration), owner (if a namespace must be declared obsolete)", ["R-02", "R-19"], "open"),
 q("Q-12", "Do we keep, measure, or replace the model's assumed SIGMA of 13.5 points?",
   "The registered model converts a margin into a probability through this one constant, so it sets every "
   "p_home in the shadow record - and therefore the Brier score the leaderboard will eventually use.",
   "the rule file labels it an assumption with no source and forbids editing it after a forecast is "
   "recorded; the second registered model derives its own residual SD (10.67 points) from the training "
   "corpus instead. The two records disagree on 2 of the 5 shared fixtures by 2.79 and 3.52 points.",
   "A v2 registration that measures the residual SD from the 150-game official corpus, frozen before it "
   "sees a Week 11 result.",
   "Estimate sigma on weeks 1-10 only, publish the estimate with n and an interval, register v2 as a new "
   "file, and run v1 and v2 side by side until one wins - which is also what the totals requirement asks "
   "for.",
   "an agent (measurement), owner (which version the leaderboard treats as the baseline)",
   ["R-34", "R-60", "R-65"], "open"),
 q("Q-13", "Who transcribes 13 venues, and from which page?",
   "Venue is a published game-centre fact and it feeds rest/travel/roof context; it is also the cheapest "
   "requirement on the list to satisfy, and it is still at 1 of 13.",
   "one venue (Reliant Stadium, IND at HOU) is in the repository with a game-centre read date of "
   "2026-11-17; today's official Week 11 page lists matchups, times, networks and the Munich venue tag "
   "for Week 10, but not a site per game.",
   "13 game-centre reads with a dated capture each.",
   "One session, 13 fetches, one table, and a rule that a blank venue fails the build - the drift alarm "
   "pattern already used for the injury parser.",
   "an agent", ["R-23"], "open"),
 q("Q-14", "Do we build the weather/roof overlay from NWS products, and accept the citation burden?",
   "It is the only feature family on the brief with no betting-market dependency, so it can be built and "
   "validated while the price question is still open.",
   "nothing in the repo: no venue attribute table, no forecast capture, no 90-minute roof designation. The "
   "fixture-context work explicitly excludes weather as un-sourced, which is the correct behaviour today.",
   "A venue attribute table (32 rows) + a forecast-capture rule + a stated latency limit (a forecast older "
   "than its own issue time is worse than none).",
   "Start with the venue table only, because a roof designation is a published fact and a forecast is a "
   "time series; do not mix them in one release.",
   "an agent, owner for the source policy", ["R-56"], "open"),
]


def s(i, problem, sug, a, b, c, rec, cost, unblocks, risk):
    return {"id": i, "problem": problem, "suggestion": sug,
            "options": {"A": a, "B": b, "C": c}, "recommended_path": rec, "cost": cost,
            "unblocks": unblocks, "risk_if_skipped": risk, "review_state": "proposed - awaiting owner",
            "source_url": SCHED11}


SUGGESTIONS = [
 s("S-01", "Thirty-plus NFL namespaces, and no screen tells a reader which artifact answers which "
           "question. Every session so far has added a namespace rather than retiring one.",
   "Publish a workspace registry on the landing page - namespace, what it is canonical for, last verified "
   "date, and a read-only banner for the rest - and stop minting new namespaces for refresh work.",
   "Registry table generated from a per-namespace manifest (1 new file, 0 new pages)",
   "Registry maintained by the integration session only",
   "Do nothing and keep appending namespaces",
   "A, because it can be regenerated and asserted; the registry should also carry the two disagreements "
   "found today (results feed size, shared-slot count) so a reader cannot pick a favourable one.",
   "1 session-hour, no new data", ["R-22", "P-01"],
   "Duplicate work, and a reader choosing between 137, 149 and 150 games by accident."),
 s("S-02", "The price-data question has been open in every session and it gates seven requirements, yet "
           "no capture is running even for the option nobody has rejected.",
   "Record the decision in one page, and start capturing under whichever option is chosen on the same day "
   "- an archive is worth nothing except from the day you begin.",
   "Never use market prices: publish fair lines and probabilities, keep ROI/CLV off the roadmap",
   "Licence a feed, capture open+close per market per game, publish residual from week 1",
   "Accept a named third-party archive for research, forbid it from the leaderboard and from any 'official' label",
   "B if a licence is obtainable, otherwise C with C's numbers excluded from every competitive surface. "
   "Option A is a legitimate answer and is cheaper than the argument; the unacceptable state is an open "
   "question while three stores pretend to be ready.",
   "1 owner decision + 1 scheduled capture job (small)",
   ["R-01", "R-04", "R-18", "R-20", "R-55", "R-57", "R-58"],
   "Every ROI-shaped number stays uncomputable, and namespaces keep filling the gap with conventions that "
   "look like data."),
 s("S-03", "Captures are counted per day, but the report changes per publish event - today's two captures "
           "7h15m apart differ in 1 field out of 241.",
   "Key capture cadence to the league's publish schedule (after each report release), record the document "
   "hash, and treat a repeat hash as 'no new information' rather than as a new data point.",
   "Keep daily captures and publish the duplicate as 'no change'",
   "Publish-anchored capture: fetch at 3 known publication windows per week, alert if a window yields a "
   "hash already seen",
   "Add an independent second observation point (club release) to break ties",
   "B now, C when the desk has spare capacity. 'No change' is a result and should be printed as one, but "
   "it must not be counted as three results.",
   "config only", ["R-21", "R-52", "R-53"],
   "A freshness panel that reports confidence it has not earned."),
 s("S-04", "Two requirements (calibrating 'Questionable', scoring designation reliability) are blocked on "
           "the same unknown: whether a past-season weekly report can be retrieved at all.",
   "Spend one hour on a historical probe of the per-week report URL family for a single past week, and "
   "publish the outcome as a dated finding whether it succeeds or fails.",
   "Probe one week of one past season; if it renders, probe a full season",
   "Buy an archive instead of probing",
   "Accept that designations cannot be calibrated and remove the two requirements from the roadmap",
   "A, because it converts an argument into a measurement for almost no cost, and a published negative "
   "result is as valuable as a positive one here.",
   "<1 hour", ["R-43", "R-51", "R-64"],
   "The availability feature stays a belief rather than a number, forever."),
 s("S-05", "Nothing in the repository stores game-day inactives, so no backup replacing a starter is ever "
           "confirmed - and the depth/slot requirements all quietly depend on that confirmation.",
   "Add an inactive-list capture as a first-class scraper (26 club lists per 13-game week), keyed by game "
   "centre, with the drift alarm attached.",
   "Capture the inactives from the game centre on game day",
   "Wait for Game Book access (Q-05) and do nothing meanwhile",
   "Derive 'did not play' from box-participation fields on the game centre where present",
   "A, with C as a labelled fallback. This is the highest-leverage new source: it turns several 'suspected' "
   "columns into 'confirmed' columns without any market data.",
   "1 scraper + 1 scheduled job", ["R-10", "R-25", "R-30", "R-46", "R-51"],
   "The availability graph keeps an 'expected' side and no 'actual' side, which is half a dataset."),
 s("S-06", "A registered model converts margin to probability with SIGMA = 13.5 points, an assumption the "
           "rule file itself says has no source.",
   "Register a v2 that estimates the residual SD from the 150-game official corpus, run both side by side, "
   "and collapse only after a walk-forward comparison - the same rule the totals requirement states.",
   "Leave v1 alone, register v2 next to it, publish the gap",
   "Edit v1's constant (breaks the registration)",
   "Never measure it",
   "A, unambiguously: B is the failure mode the pre-registration rule exists to prevent. The estimate "
   "should carry n and an interval, and the leaderboard should treat 'baseline' as a versioned object.",
   "1 hour of code, 1 new file", ["R-34", "R-60", "R-65"],
   "Every probability in the record - and therefore every future Brier score - rests on an unexamined "
   "constant."),
 s("S-07", "Home-field is treated as common sense, but the official 2026 numbers say home teams are losing "
           "more than they win.",
   "Put the control baselines (always-home, coin flip, favorites-only) on the landing page next to the "
   "skill claims, and recompute them weekly from the canonical corpus.",
   "Publish the controls as a permanent panel with n and the corpus date",
   "Keep them in a data file only",
   "Drop them as obvious",
   "A. Today's measured numbers are always-home %s over 150 games and 4 of 14 in Week 10 - below a coin "
   "flip - so a model that leans home is being rewarded for a negative edge unless the control is visible."
   % "0.473",
   "already computed here; 10 minutes to surface it", ["R-16", "R-55"],
   "A 'good' week that is actually a coin flip, or worse."),
 s("S-08", "Two of the three corpora in the repo disagree with the league's own arithmetic, and nobody "
           "noticed because each namespace checked itself.",
   "Declare one canonical 2026 results feed keyed by game_id, and make every namespace's build assert the "
   "same identity: row count == sum(W+L+T)/2 from that day's official standings page.",
   "One feed + one CI assertion everywhere",
   "Leave three feeds and add a note",
   "Recompute each namespace's numbers on its own feed and label the n",
   "A, reusing the assertion already written in this desk's compute step (150 == 150 today, and the "
   "points-for identity 6,923 == 6,923 holds).",
   "1 integration change", ["R-02", "R-19", "Q-11"],
   "Every backtest, correlation and rating in the repository inherits an off-by-thirteen sample."),
 s("S-09", "The depth register's schema drops the states that matter: it recorded 15 shared rank-1 slots "
           "and 0 empty slots where the brief describes 149 shared slots and an empty Washington slot.",
   "Re-parse the stored transcripts under a slot-as-group schema with an explicit empty state, and publish "
   "the before/after counts side by side.",
   "Re-parse with group + empty semantics, publish both counts",
   "Keep the flat register and label every 'starter' as 'first name in column 1'",
   "Delete the depth feature until a licensed structured source exists",
   "A, then B or C depending on what the re-parse shows. The brief's number and the stored number cannot "
   "both be right, and 'we measured both' is the only defensible answer.",
   "1 session-hour on existing captures", ["R-32", "R-49", "R-50", "F-DSK-09"],
   "A 'starter' that no club ever named, feeding a deficiency feature that looks verified."),
 s("S-10", "Club keys are not canonical: one registered record spells Arizona 'ARI' in its withheld list "
           "and 'AZ' in its rows, and the two renders of one player name ('Dee Alford' / \"De'Alford, Dee\") "
           "do not join at all.",
   "Freeze an identity layer: one 32-club abbreviation table, and player identity by the official player URL "
   "with display name kept as a rendered attribute, never as a key.",
   "Canonical club map + player-slug keys in every new store",
   "Patch each artifact as it is read",
   "Ignore it and accept silent join losses",
   "A. A 'first name in column 1' style bug is visible; a dropped fixture in a join is not, and the delta "
   "panel is exactly the kind of table where a dropped row looks like 'no change'.",
   "1 shared module", ["R-10", "R-12", "R-33", "F-DSK-06", "F-DSK-10"],
   "Undercounted deltas and phantom roster events, discovered a month from now."),
 s("S-11", "Requirements are satisfied by one-off session artifacts, so 'done' decays: the injury-surprise "
           "panel was blank for two days because it needed two captures and had one.",
   "Turn this desk into the scheduled job (capture, parse, diff, publish) and make the delta panel the "
   "landing page's first module, so the site's default view is 'what changed', not 'what someone wrote'.",
   "Schedule the desk; keep namespaces as reference layers",
   "Re-run sessions by hand each week",
   "Leave the site as a static archive of analyses",
   "A, with one guardrail: a scheduled job may only publish numbers its own parsers produced, and it must "
   "fail the build rather than blank a cell (the alarm pattern already exists here).",
   "1 workflow file", ["R-12", "R-21", "R-28", "R-38", "R-59"],
   "Every dated claim on the site quietly becomes a historical document."),
 s("S-12", "Small samples are being read as evidence: the largest pre-kickoff record in the repository is "
           "13 games, and the frozen rule's own floor for a skill claim is 300.",
   "Add a visible sample-size badge to every number on the site (n, plus 'refused' when n is below the "
   "registered floor), and have the generator refuse to render a skill claim without one.",
   "Badge every numeric cell with its n",
   "Badge only leaderboard cells",
   "Rely on prose caveats",
   "A. It costs a column, and it makes the brief's 'remove luck' instruction enforceable by a reader rather "
   "than by trust.",
   "1 build change", ["R-07", "R-16", "R-36", "R-37", "R-63"],
   "A lucky fortnight reads as a strategy."),
]


def f(i, sev, area, item, detail, evidence, src, status="flagged"):
    return {"id": i, "severity": sev, "area": area, "item": item, "detail": detail,
            "evidence": evidence, "source_url": src, "status": status}


FLAGS = [
 f("F-DSK-01", "high", "Price",
   "No official or licensed market price exists, so every residual, CLV and ROI column is blank",
   "nfl.com publishes schedules, scores and designations only. The desk publishes fair lines with a null "
   "market column and a reason; it does not use an assumed -110, which an earlier namespace did.",
   "nfl-daily-desk/data/shadow_cohorts.json (market_line null + reason); nfl-markets/data/flags.json "
   "(FLAG-M1, third-party archive disclosed per column)", SCHED11),
 f("F-DSK-02", "medium", "Capture fidelity",
   "Two captures 7h15m apart are near-identical, and no publish-time marker exists on the page to say why",
   "241 of 242 shared player rows agree on every field, 11 rows appear for one club, and the string "
   "'Updated'/'updated' appears 0 times in the 371,313-byte raw document. A no-change read and a cached "
   "read are indistinguishable from this evidence alone.",
   "nfl-daily-desk/data/availability_delta.json (reads, row_level_delta); "
   "nfl-readiness-register/snapshots/2026-11-18/injury_report-2026-11-18T234917Z.html", INJ),
 f("F-DSK-03", "high", "Availability coverage",
   "Only 16 of 253 report rows (6.3%) carry a game designation, and all 16 belong to one fixture",
   "The Sunday slate has practice designations and blank game statuses at this hour; blank is not "
   "'available'. Any model feature built on the designation level this week has one game of coverage.",
   "nfl-daily-desk/data/availability_delta.json (reads.capture_b.summary), nfl-daily-desk/data/"
   "drift_expectations.json", INJ),
 f("F-DSK-04", "medium", "Source rendering",
   "The official league standings page renders its heading as '$year$ NFL $displayname$ Standings'",
   "Because the rendered header is missing, the column order of the home/road/division/conference/streak "
   "split columns could not be established from today's read. Only W, L, T, PCT, PF, PA and NET are "
   "transcribed - each checked with two identities - and the rest is omitted rather than guessed.",
   "nfl-daily-desk/data/standings.json (columns_not_transcribed); "
   "nfl-daily-desk/captures/2026-11-19/standings-league-2026-reg.md", STAND),
 f("F-DSK-05", "medium-high", "Model integrity",
   "A registered model's probability scale (SIGMA = 13.5 points) is an assumption with no source",
   "The rule file says so itself and forbids editing after a forecast is recorded - which is correct - but "
   "it means every p_home in the record, and every future Brier score, inherits an unmeasured constant. "
   "The second registered model uses 10.67 from its own training residuals; the two differ by 2.79 and "
   "3.52 points on two of the five shared fixtures.",
   "nfl-daily-desk/data/shadow_cohorts.json (rule.constants); "
   "nfl-readiness/prereg/SHADOW_BASELINE_v1.md; nfl-live-board/data/origination_week11.json", STAND),
 f("F-DSK-06", "medium", "Identity",
   "Display names are not a stable join key across renderings of the same official page",
   "One Bills defensive back appears as 'Dee Alford' in the raw document and as \"De'Alford, Dee\" in the "
   "rendered read of the same row (same player URL, same position, same designations). The desk reports the "
   "pair as a candidate and does not merge it, because merging on a guess is how an availability graph "
   "starts lying.",
   "nfl-daily-desk/data/availability_delta.json (candidate_same_player_pairs)", INJ),
 f("F-DSK-07", "high", "Missing source",
   "No game-day inactive list is stored anywhere in the repository",
   "So no backup replacing a starter is confirmed by any artifact in this repo; every 'replacement' column "
   "in every namespace is either blank or an inference. The correct response is a capture job, not a model.",
   "nfl-daily-desk/data/readiness.json (R-30, R-41); nfl-live-board/data/depth_status.json", GAME),
 f("F-DSK-08", "high", "Corpus integrity",
   "Three 2026 corpus sizes circulate: 137, 149 and (correctly) 150 games",
   "nfl-markets' 2026 feed holds 137 games (Week 10: 1 game), nfl-live-board's corpus 149, and the "
   "official standings imply 150 after Monday-night's result. Any backtest or rating built on the first two "
   "excludes games that the league counts as played. Today's re-read settles all 14 Week 10 games, and the "
   "13 already in the live-board corpus agree with the official page 13 of 13 on score.",
   "nfl-daily-desk/data/corpus_extension.json (identity, already_in_corpus); "
   "nfl-markets/data/results_feed.csv; nfl-live-board/data/corpus_2026.json", STAND),
 f("F-DSK-09", "medium", "Schema fidelity",
   "The depth register cannot represent an empty slot, and its shared-rank-1 count does not match the brief",
   "Measured from the peer sweep's own parsed layer (31 clubs, 897 slots, read today): 15 rank-1 slots "
   "carry a second name, 22 slots are shared at any rank, and 0 empty slots are recorded - while the brief "
   "describes 149 multi-rank-1 slots and an explicitly empty Washington slot. Either the parser drops the "
   "state or the 149 figure counts something else; both possibilities are published.",
   "nfl-depth-sweep/data/parsed/*.json (recomputed by this session); nfl-daily-desk/data/repo_review.json", INJ),
 f("F-DSK-10", "low-medium", "Identity",
   "Club abbreviations are not canonical inside one registered artifact",
   "The cohort-1 record names Arizona 'AZ' in its forecast rows and 'ARI' in its withheld list; a join on "
   "abbreviation drops that fixture silently. Same class of bug as F-DSK-06, different table.",
   "nfl-readiness/data/shadow_week11.json (forecasts vs withheld)", SCHED11),
 f("F-DSK-11", "medium", "Provenance",
   "Backtest rows carry a synthetic capture timestamp and must not be read as a pre-registration",
   "nfl-markets' 816 2026 price rows stamp the model line as '2026-09-08T12:00:00Z (origination convention: "
   "day before kickoff)' - a convention, not an event. The namespace discloses its third-party pricing in "
   "its own flags file, which is why this is a labelling requirement, not an accusation: those numbers are "
   "a backtest, and the brief forbids a backtest on a leaderboard.",
   "nfl-markets/data/price_snapshots.csv (model_captured_at, verified by this session's read of the file); "
   "nfl-markets/data/flags.json", SCHED11),
 f("F-DSK-12", "low", "Source semantics",
   "'No Injuries Reported' is an official state that a naive scraper stores as 'no data'",
   "Two Week 11 clubs (Bengals, Commanders) publish that state for Monday night, and a third (Chargers) "
   "published it in the earlier capture before 11 rows appeared. The desk keeps the state as a value, which "
   "is the only reason the appearance was reportable at all.",
   "nfl-daily-desk/data/availability_delta.json (club_block_transitions); nfl-daily-desk/engine/parse.py", INJ),
 f("F-DSK-13", "low", "Source gaps",
   "The official reserve ledger publishes the Position column blank on all 25 November rows",
   "Confirmed in the raw document, not a transcription gap. Any join that needs a position must come from "
   "the roster or the report, so the reserve list alone cannot flag which unit a club lost.",
   "nfl-daily-desk/captures/2026-11-19/reserve-list-november-2026.md; "
   "nfl-daily-desk/data/reserve_delta.json (caveats)", RESERVE),
 f("F-DSK-14", "medium", "Home-field prior",
   "Home teams are 0.473 in the 2026 official corpus, and 4 of 14 in Week 10",
   "Not an error in the data - an error waiting in the models. Any workspace that treats home as a positive "
   "constant, or a reader who assumes a home baseline beats a coin flip, is wrong for this season: "
   "the always-home control is below 0.5, so a home-leaning pick is a negative-skill signal.",
   "nfl-daily-desk/data/controls.json; nfl-daily-desk/data/corpus_extension.json", SCHED10),
 f("F-DSK-16", "medium", "Venue",
   "Two official NFL pages give different venue names for the same Thursday game",
   "The Week 11 schedule page's stadium link for IND at HOU reads 'NRG Stadium' while the official game "
   "centre Game Info reads 'Reliant Stadium (HOUSTON, TX)'. This desk transcribed neither: it records the "
   "disagreement because the venue requirement names the game centre as the source, and because a venue "
   "feeds roof and travel context that a model would otherwise consume without question. One fixture, two "
   "official names - which one wins has to be a stated rule, not a preference.",
   "nfl-verify-2026-11-19/data/schedule_week11_2026_11_19.json (venue, game_centre_venue and both URLs on "
   "the same row); nfl-daily-desk/data/cross_session.json (week11_slate.venue_label_disagreements)",
   "https://www.nfl.com/games/colts-at-texans-2026-reg-11"),
 f("F-DSK-17", "medium", "Verification",
   "Two same-day reads of one official page disagree on 2 of 111 rows, and neither carries enough to order them",
   "The differing fields are a Carolina practice status (this desk: Limited Participation in Practice; the "
   "peer read: Full Participation in Practice) and one practice string that differs only in capitalisation "
   "(this desk pins the byte-exact official casing; the peer row is title-cased). The peer read carries no "
   "clock time, by its own flag, so the two cannot be sequenced; this desk's two dated captures place the "
   "Carolina change between 2026-11-18T23:49:17Z and 2026-11-19T07:05:00Z. A field that moves inside a day "
   "is exactly why a capture without a time is not evidence.",
   "nfl-daily-desk/data/cross_session.json (injury_report.field_differences, practice_vocab_note); "
   "nfl-daily-desk/data/availability_delta.json (row_level_delta.changes); "
   "nfl-verify-2026-11-19/data/flags.json (VF-03 'no clock time')", INJ),
 f("F-DSK-15", "medium", "Site process",
   "This desk's first run failed its own drift alarm on three rows before anything was published",
   "The transcription of the rendered read wrote 'Did Not Participate in Practice' (lower-case 'in') for "
   "three Buffalo rows and mis-set one Carolina row; the parser refused because the value fell outside the "
   "official vocabulary, and the corrected capture now reproduces the raw-byte capture on 241 of 241 "
   "shared players. Recorded so a reader can see the gate working rather than only the polished output.",
   "nfl-daily-desk/data/availability_delta.json (drift_alarm); nfl-daily-desk/engine/parse.py", INJ),
]


def src(url, title, method, supports):
    return {"url": url, "title": title, "read_utc": "2026-11-19", "method": method,
            "supports": supports}


SOURCES = {
 "dataset": "nfl_daily_desk_sources",
 "title": "Every source this desk used, with what it supports",
 "built_utc": "2026-11-19T07:45:00Z",
 "policy": "official NFL pages for values; repository artifacts for inherited numbers, each with its own "
           "read date; a value with neither is blank",
 "official": [
  src(INJ, "Official NFL injury report, Week 11 of the 2026 season",
      "platform-rendered read, 7 chunks, transcribed to captures/2026-11-19/injury-report-week11.md",
      "the availability table, the delta panel, the designation coverage numbers, the dated news headlines "
      "used as announced-starter evidence"),
  src(RESERVE, "2026 NFL reserve list, November",
      "platform-rendered read, 2 chunks, transcribed to captures/2026-11-19/reserve-list-november-2026.md",
      "the 25-row November IR ledger, the per-club counts, the 'not listed is not available' caveat"),
  src(SCHED10, "NFL Week 10 schedule 2026 (all games FINAL)",
      "platform-rendered read, 2 chunks, transcribed to captures/2026-11-19/week10-finals.md",
      "all 14 Week 10 finals, the byes, the dated schedule-announcement text, the corpus extension"),
  src(STAND, "2026 NFL league standings (regular season)",
      "platform-rendered read, 2 chunks, transcribed to captures/2026-11-19/standings-league-2026-reg.md",
      "the 32 standings rows, the games-played identity (150), the points identity (6,923), the shadow "
      "record's input verification"),
  src(SCHED11, "NFL Week 11 schedule 2026",
      "read as the slate identity for the Week 11 record (fixtures/kickoffs also carried on the report page)",
      "the 13-fixture slate, kickoff times, the grading queue's first due time"),
  src("https://www.nfl.com/legal/flexible-scheduling-procedures", "NFL flexible scheduling procedures",
      "linked from the official week page; not re-read today",
      "the dated-announcement requirement's legal source"),
  src(GAME, "Colts at Texans game centre (Week 11)",
      "used as the per-game identity link for the Thursday fixture",
      "the per-fixture source URL in the shadow record"),
  src(HIST, "Per-week injury report URL family (2024 reg1)",
      "not fetched by this session - named as the probe target in Q-03/S-04",
      "the historical-archive question that gates designation calibration"),
 ],
 "repository": [
  {"path": "nfl-readiness-register/snapshots/2026-11-18/injury_report-2026-11-18T234917Z.html",
   "sha256": "e1bbea1bf036c949825106a9a9e51de307da86680583d201a091682d7d012e7b", "bytes": 371313,
   "used_for": "the earlier read of the same report, parsed from raw bytes - the authority the day's "
               "transcription is reconciled against"},
  {"path": "nfl-readiness-register/snapshots/2026-11-18/reserve_list-2026-11-18T234918Z.html",
   "sha256": "afb62a8311e810419a8e6e2cf0bfc907df80b9c131cbac9a448af987d77ed1f5", "bytes": 247942,
   "used_for": "the earlier reserve-list read for the IR delta"},
  {"path": "nfl-live-board/data/corpus_rows_only.json",
   "used_for": "the inherited 149-game 2026 corpus each of whose rows carries its own game-centre URL"},
  {"path": "nfl-readiness/data/shadow_week11.json",
   "used_for": "cohort 1 of the shadow record (5 fixtures) and its 8 withheld fixtures with reasons"},
  {"path": "nfl-readiness/prereg/SHADOW_BASELINE_v1.md",
   "used_for": "the frozen rule text, re-implemented and reproduced 5 of 5 by this session"},
  {"path": "nfl-live-board/data/origination_week11.json",
   "used_for": "the second registered Week 11 record (13 fixtures, three stages, blank market columns)"},
  {"path": "nfl-markets/data/price_snapshots.csv",
   "used_for": "the 12,573-row price store, read to establish exactly how much of it is filled and from "
               "where (F-DSK-11)"},
  {"path": "nfl-markets/data/results_feed.csv",
   "used_for": "the 4,056-game 2011-2026 feed, and the 137-game 2026 count that contradicts the standings "
               "identity (F-DSK-08)"},
  {"path": "nfl-depth-sweep/data/readiness.json",
   "used_for": "the per-club depth-route state (31 of 32 verified, HOU image-only) and the roster/IR sweep"},
  {"path": "nfl-depth-sweep/data/parsed/",
   "used_for": "the parsed depth transcripts re-counted by this session for the shared/empty slot finding"},
  {"path": "nfl-book/data/price_snapshots.json",
   "used_for": "the 39-row store of OUR originated open/close numbers with the market columns null by policy"},
  {"path": "nfl-availability-desk/data/price_snapshots.json",
   "used_for": "a 0-row store whose why_empty field states the same conclusion independently"},
 ],
 "note": "no source outside nfl.com, the repository's own dated artifacts, and github.com was used to "
          "produce a number on this site",
}


def main():
    json.dump({"dataset": "nfl_daily_desk_questions",
               "title": "The questions that must be answered before any of this can be decided",
               "built_utc": "2026-11-19T07:45:00Z",
               "policy": "every row separates what we have from what is missing, names the discovery route, "
                         "and says whether an agent or the owner can answer it; an answer already in the "
                         "repository is quoted with its artifact, not paraphrased",
               "n_open": len(QUESTIONS),
               "rows": QUESTIONS},
              open(os.path.join(NS, "data", "questions.json"), "w"), indent=1)
    json.dump({"dataset": "nfl_daily_desk_suggestions",
               "title": "Suggestions for improving the site and the decisions it supports - for review "
                        "BEFORE anything is implemented",
               "built_utc": "2026-11-19T07:45:00Z",
               "policy": "nothing here is implemented; each row states the problem, the options, the "
                         "recommended path, the cost, what it unblocks and what breaks if it is skipped. "
                         "Sorted by what it unblocks, not by how easy it is. review_state becomes "
                         "accepted / deferred / rejected only by the owner.",
               "ranking_rule": "expected decisions unblocked per unit of cost, ties broken by whether the "
                               "current state produces a wrong number rather than no number",
               "rows": SUGGESTIONS},
              open(os.path.join(NS, "data", "suggestions.json"), "w"), indent=1)
    json.dump({"dataset": "nfl_daily_desk_flags",
               "title": "Flagged for review - irregularities, unverifiable values and open defects",
               "built_utc": "2026-11-19T07:45:00Z",
               "policy": "flagged items do not block the merge; they block a claim. A row here is a thing "
                         "the site refuses to smooth over",
               "severity_counts": {"high": sum(1 for x in FLAGS if x["severity"].startswith("high")),
                                   "medium-or-worse": sum(1 for x in FLAGS
                                                          if not x["severity"].startswith("low"))},
               "rows": FLAGS},
              open(os.path.join(NS, "data", "flags.json"), "w"), indent=1)
    json.dump(SOURCES, open(os.path.join(NS, "data", "sources.json"), "w"), indent=1)

    review = [
     {"namespace": "nfl-daily-desk", "owner_session": "arena-92c458e6-own4",
      "canonical_for": "the 2026-11-19 dated reads, the first two-capture availability delta, the corpus "
                       "extension and identity checks, the shadow-record reconciliation",
      "verified_by_this_session": "everything in data/ is produced by engine/ from captures/ and the two "
                                  "2026-11-18 raw files, and re-checked by engine/verify.py",
      "notes": "single-day desk by design; it should be scheduled, not extended into a new analysis layer"},
     {"namespace": "nfl-live-board", "owner_session": "arena/925796f5-own4",
      "canonical_for": "the Week 11 three-stage origination record (13 fixtures, frozen 2026-11-17), the "
                       "walk-forward model stats, the requirements register, the blank-by-policy price store",
      "verified_by_this_session": "corpus row count (149) and 13 of 13 Week 10 rows re-checked against "
                                  "today's official page - all agree; the price store's 0 rows confirmed",
      "notes": "its snapshot label (2026-11-17) is now 2 days old; its injury-surprise panel is blank for a "
               "reason this desk resolves (two dated captures now exist)"},
     {"namespace": "nfl-readiness-register", "owner_session": "session 63ebae0e",
      "canonical_for": "the full requirement register from the 2026-11-15 brief (73 rows) and the scheduled "
                       "capture workflow + raw snapshots with hashes",
      "verified_by_this_session": "manifest entries, both raw files' sha256 recomputed, and their content "
                                  "parsed by this desk's parser - the 23-club / 242-row state is real",
      "notes": "the only namespace whose captures are byte-exact; every delta in this repo should hang off "
               "it rather than re-fetching"},
     {"namespace": "nfl-readiness", "owner_session": "(readiness session)",
      "canonical_for": "the frozen singles shadow baseline v1 (rule + code) and its Week 11 cohort-1 record",
      "verified_by_this_session": "the rule was re-implemented and reproduced 5 of 5 stored rows exactly "
                                  "from today's official standings; the 8 withheld rows are all now eligible",
      "notes": "SIGMA=13.5 is disclosed as an assumption in the rule file - see F-DSK-05"},
     {"namespace": "nfl-markets", "owner_session": "(markets session)",
      "canonical_for": "the only multi-season archive in the repo: 4,056 games 2011-2026 and 12,573 price "
                       "rows with per-column provenance labels",
      "verified_by_this_session": "row counts (2026 games 137, price rows 12,573, open filled 2,587, close "
                                  "filled 12,246), the third-party labelling in its own flags file, and the "
                                  "synthetic capture-time convention on its 816 2026 rows",
      "notes": "its 2026 feed is 13 games short of the league identity; its numbers are a disclosed "
               "backtest and must stay off a leaderboard"},
     {"namespace": "nfl-depth-sweep", "owner_session": "arena/76537469-own4",
      "canonical_for": "the 32-club depth-route verification (31 text, 1 image-only) and the November "
                       "roster/IR sweep with stale-depth flags",
      "verified_by_this_session": "parsed layer re-counted: 897 slots, 15 shared rank-1, 22 shared at any "
                                  "rank, 0 empty slots; capture_status distribution; HOU 0 slots",
      "notes": "the shared/empty slot representation is the defect to fix before the deficiency feature"},
     {"namespace": "nfl-availability-desk", "owner_session": "(availability session)",
      "canonical_for": "capture audit, drift expectations and a deliberately empty price store",
      "verified_by_this_session": "price store row count (0) and its why_empty field",
      "notes": "its single-capture limitation, stated in the brief, is now resolved by the register workflow"},
     {"namespace": "nfl-book", "owner_session": "arena/f7037afe-own4",
      "canonical_for": "a 137-game verified results feed and a 39-row store of our own open/close numbers",
      "verified_by_this_session": "row counts and the null market columns with the policy note; its 137-game "
                                  "count matches nfl-markets and is 13 short of the standings identity",
      "notes": "useful structure, stale data - the same staleness the daily desk exists to prevent"},
     {"namespace": "nfl-verify-2026-11-19", "owner_session": "arena/6c8bbde6-own4",
      "canonical_for": "the 2026-11-19 fresh verification round: standings, Week 11 slate with 12 venues, "
                       "reserve and trade ledgers, a 70-row readiness register, and ten reconciliation checks",
      "verified_by_this_session": "its injury rows were re-joined against this desk's read of the same page "
                                  "(111 of 111 joined, 109 identical on every field, all 10 per-club counts "
                                  "equal); its standings agree on 192 of 192 fields and give the same "
                                  "150-game count; its reserve ledger reconciles 25 of 25; its slate gives "
                                  "the same 13 fixtures",
      "notes": "the second same-day read in the repo, which is what makes the cross-session comparison "
               "possible at all; its flags (VF-01 venue label, VF-03 no clock time) are carried into this "
               "desk's own flag list as F-DSK-16 and F-DSK-17 rather than duplicated"},
     {"namespace": "nfl-repo-inventory", "owner_session": "arena/4f78a318-own4",
      "canonical_for": "the machine inventory of 40 nfl* namespaces and the record of running every "
                       "namespace verifier on a clean export",
      "verified_by_this_session": "not re-run here; its inventory is the reason this desk ships its own "
                                  "verifier rather than relying on scripts/check_site.py, which walks only lab/",
      "notes": "its F04/F10 findings (unlinked namespaces, an append-only board that collides on every "
               "merge) are the same two problems this desk's S-01 suggestion is about"},
     {"namespace": "nfl (portal)", "owner_session": "several",
      "canonical_for": "the NFL entry point and its suggestions page",
      "verified_by_this_session": "navigation links, including the two added toward the live board's snapshot",
      "notes": "the portal now also routes to this desk; it should route to the desk first on a game day"},
     {"namespace": "nfl-req-review", "owner_session": "arena/ca159db5-own4 / arena/9242c387-own4",
      "canonical_for": "the two-round requirement review registers (round 1 and round 2)",
      "verified_by_this_session": "not re-read today; the daily desk's readiness table is keyed to the "
                                  "2026-11-19 brief instead, and says so",
      "notes": "three registers now cover the same brief with different ids (REQ-xx, Rxx, R-xx); a reader "
               "needs the registry in S-01 to choose"},
     {"namespace": "nfl-readiness (questions) / nfl-req-review (questions) / nfl-live-board (questions)",
      "owner_session": "several",
      "canonical_for": "nothing - three questions registers exist and none is marked canonical",
      "verified_by_this_session": "file presence only",
      "notes": "this desk publishes a fourth; the fix is not another register but a pointer table (S-01) "
               "and a merge in an integration session"},
    ]
    json.dump({"dataset": "nfl_daily_desk_repo_review",
               "title": "Line-by-line repository review, 2026-11-19 - what each NFL namespace is, and what "
                        "this session checked",
               "built_utc": "2026-11-19T07:45:00Z",
               "policy": "'verified by this session' means the session read the file or recomputed the "
                         "number; anything else is stated as presence-only, never as confirmed. No "
                         "namespace's data was edited to make this review true.",
               "rows": review,
               "repo_url": REPO},
              open(os.path.join(NS, "data", "repo_review.json"), "w"), indent=1)
    print("questions", len(QUESTIONS), "suggestions", len(SUGGESTIONS), "flags", len(FLAGS),
          "review rows", len(review))


if __name__ == "__main__":
    main()
