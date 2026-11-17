#!/usr/bin/env python3
"""Own4 · nfl-live-board · L-04 — build the requirement register from the brief text.

One row per requirement line in the owner's 2026-11-17 brief. The columns are the ones the
brief itself asks for: status, the gate that blocks it, and the number that would clear it.

Status vocabulary (nothing here is a judgement call):
  MET       a published artefact in this repository satisfies it and is linked in `evidence`
  PARTIAL   part of it exists; the missing part is named in `gate`
  BLOCKED   no source exists that could satisfy it today; the gate names what is missing
  REJECTED  the brief itself rejects the approach; row records the rejection and its reason
  PROCESS   a rule about how the work is done, satisfied by the repository's own practices

Run: python3 nfl-live-board/engine/requirements.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")

R = []          # (id, group, text, status, gate, clearing_number, evidence, evidence_url)


def add(**kw):
    R.append(kw)


G = "Data foundations"
add(id="R01", group=G, text="Add a price-snapshot store that records opening and closing numbers for every market we originate.",
    status="BLOCKED",
    gate="No official page publishes an opening or closing price. The store is built and empty by policy (F-01).",
    clearing_number="1 official price source with stated re-use terms; 2 closes per market per game (open, close) x 3 markets x 13 Week 11 games = 78 rows.",
    evidence="data/price_snapshots.json", evidence_url="pages/prices.html")
add(id="R02", group=G, text="Add a verified results feed so backtests and ROI can be computed at all.",
    status="MET",
    gate="ROI additionally needs a price (F-01); the feed itself is complete through Week 10.",
    clearing_number="149 games reconciled: 192/192 standings checks pass and the games-played identity holds exactly.",
    evidence="data/corpus_2026.json", evidence_url="pages/results.html")
add(id="R03", group=G, text="Turn the 136-game log into the pre-registered backtest corpus.",
    status="MET",
    gate="None for the corpus. ROI on it is blocked by F-01.",
    clearing_number="The brief's 136 games are weeks 1-9 exactly; adding the 13 Week-10 finals gives 149, which equals the 149 games the official standings imply.",
    evidence="data/corpus_2026.json", evidence_url="pages/results.html")
add(id="R04", group=G, text="Decide the price-data policy before any backtest is published.",
    status="BLOCKED",
    gate="Owner decision. The three candidate policies and their consequences are written out; none is adopted.",
    clearing_number="One decision: (a) licensed feed, (b) archive-only with a hash per close, or (c) no prices ever. Each has a stated cost in the register.",
    evidence="data/questions.json", evidence_url="pages/questions.html")

add(id="R05", group="Origination", text="Originate the side first, then the total, then the moneyline.",
    status="MET", gate="None.",
    clearing_number="13 Week 11 fixtures originated in that order, each row carrying the three stages in separate columns.",
    evidence="data/origination_week11.json", evidence_url="pages/origination.html")
add(id="R06", group="Origination", text="Publish the model's fair line, the market line, and the difference as separate columns.",
    status="PARTIAL",
    gate="The fair line is published. The market line and the difference are blank because no official price exists (F-01).",
    clearing_number="A market line for each of the 13 fixtures; the difference column is computed the moment one exists.",
    evidence="data/origination_week11.json", evidence_url="pages/origination.html")
add(id="R07", group="Origination", text="Price a line ourselves and publish the residual against the market, on a schedule, from day one.",
    status="PARTIAL",
    gate="We price the line. The residual needs the market (F-01); the schedule exists as CI but has no price to capture.",
    clearing_number="Residual per game per week = fair - market; needs one price source and one scheduled capture.",
    evidence="data/origination_week11.json", evidence_url="pages/origination.html")
add(id="R08", group="Origination", text="Publish every model total twice until one wins.",
    status="MET", gate="None.",
    clearing_number="Two estimators are published side by side with the gap column; the collapse rule is written down.",
    evidence="data/origination_week11.json", evidence_url="pages/origination.html")
add(id="R09", group="Origination", text="Add a fixture-context feature set built only from published schedule facts.",
    status="MET", gate="Rest, short week and neutral site are computable from the schedule; stadium roof is not published as a field.",
    clearing_number="Context features per fixture: rest days (both sides), short-week flag, neutral-site flag, kickoff window. 4 features x 13 games.",
    evidence="data/fixture_context.json", evidence_url="pages/context.html")
add(id="R10", group="Origination", text="Transcribe the venue of every fixture from the official game centre and publish it.",
    status="PARTIAL",
    gate="nfl.com states the stadium in a titled Game Info block only on future games. Played games do not restate it, and club sites are not a league source.",
    clearing_number="A venue string for 13/13 Week 11 fixtures from a titled official field (1 of 13 captured so far: Reliant Stadium, IND at HOU).",
    evidence="data/fixtures_2026.json", evidence_url="pages/context.html")
add(id="R11", group="Origination", text="Store every model output as a probability plus its inputs, not just a pick.",
    status="MET", gate="None.",
    clearing_number="Every forecast row carries p, home/away, the model's margin and total, the residual SD and the training-game count.",
    evidence="data/origination_week11.json", evidence_url="pages/origination.html")

G2 = "Competition"
add(id="R12", group=G2, text="Separate 'signal' from 'staking' in the leaderboard so a lucky staking run cannot mask a bad signal.",
    status="MET", gate="Staking is blank because it needs a price (F-01); the separation itself is enforced.",
    clearing_number="Stage 1 (proper score) decides ranking; stage 2 (CLV/ROI) is an empty escrow. No strategy can be promoted by stage 2.",
    evidence="data/leaderboard.json", evidence_url="pages/leaderboard.html")
add(id="R13", group=G2, text="Rank with proper scores and uncertainty, not win rate.",
    status="MET", gate="None.",
    clearing_number="Brier Skill Score with a week-clustered 90% interval and a Holm-adjusted p, published with the number of trials.",
    evidence="data/leaderboard.json", evidence_url="pages/leaderboard.html")
add(id="R14", group=G2, text="Add durable snapshot storage and alerts.",
    status="PARTIAL",
    gate="Peer namespaces run the scheduled capture with hashes and a drift alarm; this namespace consumes rather than duplicates it.",
    clearing_number="A hash-chained capture per scheduled run and a build that fails on schema drift - both already run in nfl-collector and nfl-readiness-register.",
    evidence="../nfl-collector/pages/captures.html", evidence_url="pages/repo-review.html")
add(id="R15", group=G2, text="Pre-register every strategy; forbid backtest numbers from ever appearing on the leaderboard.",
    status="MET", gate="None.",
    clearing_number="Five strategies registered with rule text and model parameters before scoring; the rule file's SHA-256 is recorded and re-checked.",
    evidence="prereg/PREREG-LB.md", evidence_url="pages/leaderboard.html")
add(id="R16", group=G2, text="Keep parlays and prop combos behind a joint-evidence gate.",
    status="MET", gate="No parlay is registered, so nothing can slip through.",
    clearing_number="A directly estimated joint probability for the same game plus the operator's void/push rules; without both, the division stays empty.",
    evidence="prereg/PREREG-LB.md", evidence_url="pages/leaderboard.html")
add(id="R17", group=G2, text="Use proper-score leaderboard divisions.",
    status="MET", gate="Only the singles division is populated.",
    clearing_number="Four divisions declared: singles (populated), game parlays, same-game parlays, prop combos (all empty and labelled empty).",
    evidence="data/leaderboard.json", evidence_url="pages/leaderboard.html")
add(id="R18", group=G2, text="Start with a singles-only shadow baseline.",
    status="MET", gate="None.",
    clearing_number="A pre-registered, frozen single-market baseline is scored on a walk-forward window before any Week 11 game.",
    evidence="prereg/PREREG-LB.md", evidence_url="pages/leaderboard.html")
add(id="R19", group=G2, text="Define a demotion gate that sends a live strategy back to paper.",
    status="MET", gate="No live strategy exists to demote yet.",
    clearing_number="Four demotion triggers with a minimum prospective sample of 30 forecasts, registered before any live forecast.",
    evidence="prereg/PREREG-LB.md", evidence_url="pages/leaderboard.html")
add(id="R20", group=G2, text="Add a two-sided 'what would change our mind' field to every strategy entry.",
    status="MET", gate="None.",
    clearing_number="Each strategy row carries the observation that would promote it and the observation that would retire it.",
    evidence="data/leaderboard.json", evidence_url="pages/leaderboard.html")
add(id="R21", group=G2, text="Rank by benchmark-relative Brier skill with a game-cluster lower bound and a multiplicity adjustment for the number of trials.",
    status="MET", gate="None.",
    clearing_number="0 of 5 strategies qualify. The best point estimate is +0.1273 with a cluster interval [0.0159, 0.2412] and a Holm-adjusted p of 0.1375.",
    evidence="data/leaderboard.json", evidence_url="pages/leaderboard.html")
add(id="R22", group=G2, text="Compute and publish the 'removal of luck' panel on the site dashboard.",
    status="MET", gate="One component cannot be removed: availability edge needs point-in-time availability the repository does not hold (F-04).",
    clearing_number="Five luck channels closed and named; one open and named. The control floor is computed, not asserted.",
    evidence="data/leaderboard.json", evidence_url="pages/luck.html")
add(id="R23", group=G2, text="Reject: ranking strategies by season-long ROI.",
    status="REJECTED",
    gate="Rejection recorded with its reason: a season of ROI at n<50 bets cannot distinguish skill from variance.",
    clearing_number="n/a - recorded so the alternative is not silently reintroduced.",
    evidence="prereg/PREREG-LB.md", evidence_url="pages/leaderboard.html")

G3 = "Availability and depth"
add(id="R24", group=G3, text="Track the depth of the replacement, not just the fact of a replacement.",
    status="BLOCKED",
    gate="No official depth chart and no official snap-count table (F-07).",
    clearing_number="A verified official depth source for 32/32 clubs, or an official snap-count table; either one unlocks all 32 rows.",
    evidence="data/depth_status.json", evidence_url="pages/availability.html")
add(id="R25", group=G3, text="Build the availability graph as a first-class dataset (who was expected to start, who actually did).",
    status="BLOCKED",
    gate="'Actually started' needs participation records: game books exist but 1 of 14 Week-10 fixtures is parsed (peer finding).",
    clearing_number="14 of 14 Week-10 game books parsed into starter/non-starter rows, then 149 games for a season corpus.",
    evidence="data/depth_status.json", evidence_url="pages/availability.html")
add(id="R26", group=G3, text="Do not model depth from jersey order; model it from playing time.",
    status="MET", gate="No depth model exists, so the prohibition is satisfied trivially and recorded.",
    clearing_number="Participation share per player per game, from an official source, replaced for the inference that is banned.",
    evidence="data/depth_status.json", evidence_url="pages/availability.html")
add(id="R27", group=G3, text="Make the injury signal a surprise, never a level.",
    status="BLOCKED",
    gate="A surprise needs at least two dated snapshots of the same report; this season has one (F-08).",
    clearing_number="2 further dated captures of the same report (Wed, Thu) so expected vs observed can be subtracted.",
    evidence="data/injury_surprise.json", evidence_url="pages/availability.html")
add(id="R28", group=G3, text="Run the 32-team roster/IR sweep before any team-level model is trusted.",
    status="PARTIAL",
    gate="The reserve list is transcribed (27 November moves). Full roster + IR counts per club are not captured.",
    clearing_number="32/32 clubs with roster size, IR count and reserve status from an official page on one date.",
    evidence="data/reserve_list_2026_11.json", evidence_url="pages/availability.html")
add(id="R29", group=G3, text="Store every injury-hub read with its clock time and publish the delta, never the level.",
    status="BLOCKED",
    gate="This namespace re-read the page once. Peer namespaces hold three dated reads of the same week with zero field deltas - a real but single-week delta.",
    clearing_number="A fourth dated read with at least one field change, or a second week captured at two time points.",
    evidence="data/availability_verification.json", evidence_url="pages/availability.html")
add(id="R30", group=G3, text="Capture official inactive lists and snap counts.",
    status="BLOCKED",
    gate="Inactive lists are published per game, not per week, and were not read here. No snap-count table exists on nfl.com (F-07).",
    clearing_number="13 Week-11 inactive lists (one per game) plus any official snap-count table - 0 of 13 captured at registration.",
    evidence="data/depth_status.json", evidence_url="pages/availability.html")
add(id="R31", group=G3, text="Capture the reserve list so 'not listed' never means 'available'.",
    status="MET", gate="None.",
    clearing_number="27 reserve-list moves transcribed with player URLs. Malik Willis (MIA, 11/10) and TreVeyon Henderson (NE, 11/14) are on it while absent from the weekly report.",
    evidence="data/reserve_list_2026_11.json", evidence_url="pages/availability.html")
add(id="R32", group=G3, text="Model depth slots as groups, not a single starter.",
    status="MET", gate="No depth table is published, so no slot can be flattened into a false starter.",
    clearing_number="A depth source that exposes multi-player slots; the register will store each slot as a set, never as a rank-1 name.",
    evidence="data/depth_status.json", evidence_url="pages/availability.html")
add(id="R33", group=G3, text="Treat roster turnover as a first-class data event.",
    status="PARTIAL",
    gate="The dated reserve list is captured; the trades ledger is not re-read in this session.",
    clearing_number="Every trade and IR move as a dated event joined to the lineup evidence, so depth is versioned against the last roster event.",
    evidence="data/reserve_list_2026_11.json", evidence_url="pages/availability.html")
add(id="R34", group=G3, text="Use official NFL Game Books for actual starters and game-day status; do not infer depth rank or snaps.",
    status="BLOCKED",
    gate="Game books are reachable only through the game centre and only 1 fixture is parsed (peer finding RC-07).",
    clearing_number="14 of 14 Week-10 game books parsed with zero join collisions, then the full season.",
    evidence="../nfl-collector/pages/gamebook.html", evidence_url="pages/repo-review.html")
add(id="R35", group=G3, text="Add injury and personnel ablations instead of fixed penalties.",
    status="BLOCKED",
    gate="An ablation needs the same model run with and without availability features over many weeks; one snapshot cannot supply that (F-04).",
    clearing_number="At least 8 weeks of dated availability joined to results, then two identical models differing only in the availability features.",
    evidence="data/depth_status.json", evidence_url="pages/availability.html")
add(id="R36", group=G3, text="Score injury-designation reliability before using it as a feature.",
    status="BLOCKED",
    gate="Reliability needs designations joined to inactive lists over seasons; neither the archive nor the join exists here.",
    clearing_number="Several seasons of designations joined to official inactive lists, then a play rate per designation with a confidence interval.",
    evidence="data/depth_status.json", evidence_url="pages/availability.html")
add(id="R37", group=G3, text="Calibrate what 'Questionable' means empirically instead of using old percentages.",
    status="BLOCKED",
    gate="The join to inactive lists exists only in a peer namespace for one week at tiny n.",
    clearing_number="n >= 300 Questionable designations with known active/inactive outcomes, then a play rate with a 95% interval.",
    evidence="data/depth_status.json", evidence_url="pages/availability.html")
add(id="R38", group=G3, text="Interactive Offense vs. Defense Matchup Deficiency Matrix (1st-4th string).",
    status="BLOCKED",
    gate="Identical blocker to R24: no depth ranks, so no 2nd/3rd/4th string can be named (F-07).",
    clearing_number="Depth ranks for both sides of every Week 11 matchup (13 games x 2 units), from one verified official source.",
    evidence="data/depth_status.json", evidence_url="pages/availability.html")
add(id="R39", group=G3, text="Add a per-team view: starters out, replacements named, net injury count.",
    status="PARTIAL",
    gate="Out/Doubtful/Questionable counts are verified. 'Starters out' and 'replacements named' need a depth source (F-07).",
    clearing_number="A verified starter list per club; without it the decline columns stay blank rather than being inferred.",
    evidence="data/depth_status.json", evidence_url="pages/availability.html")
add(id="R40", group=G3, text="Reject: deriving depth order from jersey number, experience or salary.",
    status="REJECTED",
    gate="Rejection recorded. The rank columns are blank; no roster attribute is used as a depth proxy.",
    clearing_number="n/a - the prohibition is recorded in the depth status file per row.",
    evidence="data/depth_status.json", evidence_url="pages/availability.html")
add(id="R41", group=G3, text="Flag stale depth rows against the official transactions log.",
    status="BLOCKED",
    gate="Nothing is published to be stale yet; the check becomes possible once R24 is unblocked.",
    clearing_number="A depth row older than its club's latest roster event, joined from the transactions log.",
    evidence="data/reserve_list_2026_11.json", evidence_url="pages/availability.html")
add(id="R42", group=G3, text="Snapshot the nfl.com injury report every Wed, Thu and Fri and keep a dated history.",
    status="PARTIAL",
    gate="Peer namespaces run the scheduled capture; this namespace has one read.",
    clearing_number="3 dated captures per week with hashes retained, which peer CI already schedules.",
    evidence="../nfl-collector/pages/captures.html", evidence_url="pages/repo-review.html")
add(id="R43", group=G3, text="Treat the injury report as a timestamped series, not a weekly snapshot.",
    status="BLOCKED",
    gate="One snapshot exists for this season in this namespace (F-08).",
    clearing_number="The same report captured at three points in one week; designations then have a series, not a state.",
    evidence="data/injury_surprise.json", evidence_url="pages/availability.html")
add(id="R44", group=G3, text="Populate the three missing Lions game-status designations (Kerby Joseph, Cade Mays, D.J. Reed).",
    status="MET", gate="None. Verified live on 2026-11-17.",
    clearing_number="All three read as 'Out' with Knee, Ankle and Hip respectively, matching the official article.",
    evidence="data/availability_verification.json", evidence_url="pages/availability.html")
add(id="R45", group=G3, text="Re-capture and republish the Week 10 injury tables (published counts were stale).",
    status="MET", gate="None. The capture is re-verified here row by row.",
    clearing_number="96 rows re-read across 8 clubs, 96 agreements, 0 disagreements.",
    evidence="data/availability_verification.json", evidence_url="pages/availability.html")
add(id="R46", group=G3, text="Archive weekly injury reports for past seasons.",
    status="BLOCKED",
    gate="Past-season pages are reachable only by URL guessing; no session has verified one.",
    clearing_number="1 verified archive season, every week's page read and hashed.",
    evidence="data/questions.json", evidence_url="pages/questions.html")
add(id="R47", group=G3, text="Capture the official inactive lists so a backup's replacement of a starter can be confirmed.",
    status="BLOCKED",
    gate="See R30. Peer namespaces hold one week of inactives from the game pages, not this one.",
    clearing_number="13 of 13 Week-11 inactive lists, then the same for every played week.",
    evidence="data/depth_status.json", evidence_url="pages/availability.html")
add(id="R48", group=G3, text="Fix the two depth-parsing failures before widening coverage (Texans image, Packers jersey numbers).",
    status="BLOCKED",
    gate="Requires a depth source to parse. nfl.com publishes none; the failing parsers are club-page parsers owned by peers.",
    clearing_number="An authorized structured source for the 32 clubs, then number-stripping that keeps the raw string beside the parsed name.",
    evidence="data/depth_status.json", evidence_url="pages/availability.html")
add(id="R49", group=G3, text="Automate immutable multi-day availability snapshots with retained hashes.",
    status="PARTIAL",
    gate="Peer CI does this; this namespace reads rather than runs the capture.",
    clearing_number="A hash per capture per day with the raw bytes retained outside the site layer.",
    evidence="../nfl-collector/pages/captures.html", evidence_url="pages/repo-review.html")

G4 = "Evidence and the site"
add(id="R50", group=G4, text="Compute correlations only from officially sourced numbers and publish n with each value.",
    status="PARTIAL",
    gate="Correlations of results are computable. Correlations that need prices or props are not.",
    clearing_number="Every correlation row prints n, the pair definition and its two official sources; no row without both.",
    evidence="data/correlations.json", evidence_url="pages/correlations.html")
add(id="R51", group=G4, text="Publish a weekly 'what changed' diff instead of a static snapshot.",
    status="BLOCKED",
    gate="A diff needs two weekly snapshots of the same table; this namespace has one.",
    clearing_number="Two consecutive dated snapshots of the same dataset.",
    evidence="data/questions.json", evidence_url="pages/questions.html")
add(id="R52", group=G4, text="Add a drift alarm to every scraper.",
    status="MET", gate="None for the parsers this namespace owns; the verifier fails on a broken row or link.",
    clearing_number="engine/verify.py exits non-zero when any table row loses its source link, any link breaks, or any page loses its navigation.",
    evidence="verify.py", evidence_url="pages/repo-review.html")
add(id="R53", group=G4, text="Publish the league's dated schedule announcement beside the live schedule page.",
    status="MET", gate="None.",
    clearing_number="The Week 11 page read is dated and its flexible-scheduling notice is transcribed beside the fixture table.",
    evidence="data/fixtures_2026.json", evidence_url="pages/context.html")
add(id="R54", group=G4, text="Put a decision-readiness table on the landing page: one row per requirement, the gate that blocks it, and the number that would clear it.",
    status="MET", gate="None.",
    clearing_number="All requirement rows carry those three fields; the landing page renders the table.",
    evidence="index.html", evidence_url="../index.html")
add(id="R55", group=G4, text="Split the site into a public analysis layer and a private data layer.",
    status="PARTIAL",
    gate="The public layer is derived analysis only. Row-level raw data lives in this repository because no private store is configured.",
    clearing_number="A private store with access control before any row-level licensed data is ingested; until then no licensed data is ingested at all.",
    evidence="index.html", evidence_url="../index.html")
add(id="R56", group=G4, text="Stadium roof/surface and NWS hourly wind/precipitation overlay.",
    status="BLOCKED",
    gate="Roof designation is not a field on the official page; NWS is outside the allowed hosts for this session.",
    clearing_number="A published roof/surface designation per stadium (32 rows) and an hourly forecast feed.",
    evidence="data/fixtures_2026.json", evidence_url="pages/context.html")
add(id="R57", group=G4, text="Two-stage skill leaderboard (proper-score qualification, then prospective CLV/ROI escrow).",
    status="MET", gate="Stage 2 is an empty escrow by design until a price exists.",
    clearing_number="Stage 1 is scored for 5 strategies; stage 2 is blank with the reason printed.",
    evidence="data/leaderboard.json", evidence_url="pages/leaderboard.html")
add(id="R58", group=G4, text="Vig-free market consensus vs originated fair-line decomposition view.",
    status="BLOCKED",
    gate="Needs a market consensus, which needs prices (F-01).",
    clearing_number="At least two independent price sources so a vig-free consensus can be formed.",
    evidence="data/price_snapshots.json", evidence_url="pages/prices.html")
add(id="R59", group=G4, text="Make suggestions to improve the site and create a section to review them before implementing.",
    status="MET", gate="None.",
    clearing_number="A suggestions board where every entry is unclaimed and carries the decision it asks for.",
    evidence="data/suggestions.json", evidence_url="pages/suggestions.html")
add(id="R60", group=G4, text="Provide a clear list of questions, information and answers needed before a decision.",
    status="MET", gate="None.",
    clearing_number="Each question states what is known, what is missing, and what would answer it.",
    evidence="data/questions.json", evidence_url="pages/questions.html")
add(id="R61", group=G4, text="Create an executive summary outlining the important details.",
    status="MET", gate="None.",
    evidence="EXECUTIVE_SUMMARY.md", evidence_url="pages/executive-summary.html",
    clearing_number="One page: what is proven, what is blocked, and the three decisions that unblock the most.")
add(id="R62", group=G4, text="Verify line by line from official sources and provide links for manual review.",
    status="MET", gate="Every published row carries an https source; the verifier enforces it.",
    clearing_number="0 rows without a source link, 0 broken internal links, checked by engine/verify.py on every build.",
    evidence="engine/verify.py", evidence_url="pages/sources.html")
add(id="R63", group=G4, text="Flag irregularities for review; unconfirmable values stay blank.",
    status="MET", gate="None.",
    clearing_number="Every blank column carries its reason in the same row; the flagged page lists each one with a link.",
    evidence="data/flags.json", evidence_url="pages/flagged.html")
add(id="R64", group=G4, text="Review the repo, work line by line, flag irregularities.",
    status="MET", gate="None.",
    clearing_number="36 NFL namespaces surveyed; contradictions and stale claims recorded with file paths.",
    evidence="data/audit_repo.json", evidence_url="pages/repo-review.html")
add(id="R65", group=G4, text="Coordinate with parallel sessions via COORDINATION.md; never edit another session's scope.",
    status="MET", gate="None.",
    clearing_number="Claim pushed before implementation; three concurrent merges absorbed without discarding peer work.",
    evidence="../COORDINATION.md", evidence_url="pages/repo-review.html")
add(id="R66", group=G4, text="Open a PR, merge without waiting, confirm GitHub Pages deploys.",
    status="PROCESS", gate="Recorded after the merge; see the coordination entry.",
    clearing_number="PR merged and the Pages run success confirmed on the live URL.",
    evidence="../COORDINATION.md", evidence_url="pages/repo-review.html")
add(id="R67", group=G4, text="No manual input from the owner; finish all tasks in the session.",
    status="PROCESS", gate="Decisions that are legally the owner's (price-data policy) are recorded as open, not taken.",
    clearing_number="n/a - the one thing that cannot be automated is a licence decision.",
    evidence="data/questions.json", evidence_url="pages/questions.html")
add(id="R68", group=G4, text="Do not merge a broken site.",
    status="PROCESS", gate="Enforced by engine/verify.py exiting non-zero.",
    clearing_number="Verifier run before every push; a failure stops the merge.",
    evidence="verify.py", evidence_url="pages/repo-review.html")
add(id="R69", group=G4, text="Reject fixed-point injury penalties; test the same model with and without personnel features.",
    status="BLOCKED",
    gate="Same blocker as R35: needs many weeks of dated availability joined to results.",
    clearing_number="Paired forecasts from two identical models over >= 8 weeks, then the difference with its interval.",
    evidence="data/depth_status.json", evidence_url="pages/availability.html")
add(id="R70", group=G4, text="Publish n with every correlation value.",
    status="MET", gate="None.",
    clearing_number="Every correlation row prints n beside r.",
    evidence="data/correlations.json", evidence_url="pages/correlations.html")

GROUPS = []
for r in R:
    if not GROUPS or GROUPS[-1][0] != r["group"]:
        GROUPS.append((r["group"], []))
    GROUPS[-1][1].append(r["id"])

summary = {
    "total": len(R),
    "met": sum(1 for r in R if r["status"] == "MET"),
    "partial": sum(1 for r in R if r["status"] == "PARTIAL"),
    "blocked": sum(1 for r in R if r["status"] == "BLOCKED"),
    "rejected": sum(1 for r in R if r["status"] == "REJECTED"),
    "process": sum(1 for r in R if r["status"] == "PROCESS"),
}

out = {
    "dataset": "nfl_live_board_requirements",
    "title": "Requirement register for the 2026-11-17 brief",
    "built_utc": "2026-11-17",
    "columns": ["id", "group", "text", "status", "gate", "clearing_number", "evidence", "evidence_url"],
    "policy": "A requirement is MET only when an artefact in this repository satisfies it and the artefact is linked. "
              "It is BLOCKED when no source exists that could satisfy it today; the gate names the missing source, "
              "not a missing effort.",
    "summary": summary,
    "groups": [{"group": g, "ids": ids} for g, ids in GROUPS],
    "rows": R,
}

with open(os.path.join(DATA, "requirements.json"), "w") as f:
    json.dump(out, f, indent=1)

print("requirements: %d  met=%d partial=%d blocked=%d rejected=%d process=%d"
      % (summary["total"], summary["met"], summary["partial"], summary["blocked"],
         summary["rejected"], summary["process"]))
for r in R:
    if r["status"] == "BLOCKED":
        print("  BLOCKED %-4s %s" % (r["id"], r["gate"][:96]))
