# -*- coding: utf-8 -*-
"""Curated registers for the NFL audit (session arena/e2601583-own4).

Every row in every register below is tied to a source that was actually read in
this session on 2026-11-12 (see SOURCES). Registers contain NO invented
statistic: values are either quoted from the source or the cell is blank and the
row is listed on the Flagged-for-Review page.
"""

FETCHED = "2026-11-12"

# ---------------------------------------------------------------- sources ----
# id: (label, url, what it was used for, how it was read)
SOURCES = [
    ("S1", "Official NFL injury report — Week 10, 2026",
     "https://www.nfl.com/injuries/",
     "Player-by-player practice and game status for every Week 10 game.",
     "Full page read in this session; 276 published player rows transcribed verbatim."),
    ("S2", "Official NFL league standings 2026 REG",
     "https://www.nfl.com/standings/league/2026/REG",
     "W-L-T, PCT, PF, PA and net points for all 32 teams.",
     "Full page read; 32 rows transcribed."),
    ("S3", "Official NFL schedule — Week 9, 2026",
     "https://www.nfl.com/schedules/2026/by-week/week-9",
     "Final scores for all 15 Week 9 games.",
     "Full page read; every final score transcribed with its game link."),
    ("S4", "Official NFL schedule — Week 10, 2026",
     "https://www.nfl.com/schedules/2026/by-week/week-10",
     "The 14-game Week 10 slate, kickoff times, networks, international venue, byes.",
     "Full page read."),
    ("S5", "Official NFL schedule — Week 8, 2026",
     "https://www.nfl.com/schedules/2026/by-week/week-8",
     "Confirms CHI 34 @ SEA 17 on 2026-11-02 was still unplayed when the stored snapshot was written.",
     "Full page read."),
    ("S6", "nfl.com team depth chart (probe)",
     "https://www.nfl.com/teams/kansas-city-chiefs/depth-chart/",
     "Probe of the official depth-chart route. Returned a 404 'Flag on the Play' page.",
     "Fetched; 404 page returned. This is the evidence for flag F01."),
    ("S7", "nfl.com team roster (probe)",
     "https://www.nfl.com/teams/kansas-city-chiefs/roster/",
     "Roster, jersey numbers, position, experience — no depth ordering.",
     "Fetched; roster rendered with 3 chunks, active status only."),
    ("S8", "nfl.com player statistics 2026",
     "https://www.nfl.com/stats/player-stats/",
     "Season passing leaders; used as an independent check of one player row.",
     "Fetched."),
    ("S9", "nfl.com team statistics 2026",
     "https://www.nfl.com/stats/team-stats/",
     "Team offense passing table for all 32 teams; independent check of team identity.",
     "Fetched."),
    ("S10", "nfl.com player page with game logs",
     "https://www.nfl.com/players/patrick-mahomes/stats/",
     "Per-game logs (Recent Games) and career table — the official per-game player data route.",
     "Fetched; 8 game rows for 2026 plus career table."),
    ("S11", "nfl.com transactions 2026",
     "https://www.nfl.com/transactions/",
     "Mid-week trades and roster moves that change who is available to play.",
     "Fetched; 12 November trades transcribed."),
    ("S12", "nfl.com news — Darnold ruled out for Week 10",
     "https://www.nfl.com/news/sam-darnold-ruled-out-for-seahawks-week-10-game-vs-raiders-drew-lock-expected-to-start-again",
     "Confirmable statement that the Week 10 injury report is not final and that a backup QB will start.",
     "Fetched."),
    ("S13", "nfl.com news roundup — Thursday Nov 5",
     "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-thursday-nov-5",
     "Secondary official confirmation of IR placements and practice participation.",
     "Fetched (first chunk)."),
    ("S14", "NFL Football Operations",
     "https://operations.nfl.com/",
     "Official rules/policy portal (2026 Rulebook, important dates).",
     "Fetched."),
    ("S15", "NFL Next Gen Stats",
     "https://nextgenstats.nfl.com/",
     "Advanced official tracking metrics (separation, pass charts, participation).",
     "Fetched."),
    ("S16", "nfl.com — Week 9 injury report article",
     "https://www.nfl.com/news/nfl-week-9-injury-report-2026-season",
     "Linked from the official injury page as the Week 9 report.",
     "Referenced by S1; not transcribed in this session."),
    ("S17", "National Council on Problem Gambling — help",
     "https://www.ncpgambling.org/help-treatment",
     "Responsible-gambling helpline shown in the footer of every page.",
     "Standard citation used by every prior session in this repository."),
]

# ------------------------------------------------------- verification rows ---
# Built in build.py from the CSV files (standings reconciliation, results, slate).

# ------------------------------------------------------------ injury flags ---
# Everything here is a count over the 276 transcribed rows of S1.
INJURY_NOTES = [
    ("Practice status", "Every one of the 276 rows carries a practice status: "
     "104 Did Not Participate, 98 Limited, 74 Full."),
    ("Game status", "Only 6 of 276 rows carry a game status (5 Out, 1 Questionable). "
     "The other 270 cells are blank on the official page — the page does not publish a "
     "game designation for them, and this site does not infer one."),
    ("Injury column", "Only 6 of 276 rows name an injury (3 Knee, 1 Concussion, 1 Groin, 1 Illness). "
     "The other 270 are blank on the official page."),
    ("Practice date", "The page does not state which practice day the statuses describe. "
     "Because the report can change every day, no practice-date claim is made (flag F02)."),
    ("Teams covered", "26 of 32 teams have at least one row. LAC and BAL are published as "
     "'No Injuries Reported' for Monday Night Football, and CHI, DEN, PHI and TB are on bye."),
    ("Report vs news", "The official report is not final: a separate official article (S12) "
     "states Sam Darnold is ruled out for Week 10 and Drew Lock is expected to start, "
     "while the report lists Darnold as a non-participant without a game status (flag F10)."),
]

# --------------------------------------------------------------- questions ---
# (id, question, why_it_matters, what_we_have, what_is_missing, discovery, blocks)
QUESTIONS = [
    ("Q01", "Where do official historical prices (spread, total, moneyline, prop odds) come from?",
     "Without a price, no bet can be graded, so no ROI, edge or skill claim is computable. "
     "This single missing input blocks the whole leaderboard.",
     "nfl.com publishes schedules, scores, standings, rosters and injury reports — and no prices.",
     "Any official price archive. None exists on nfl.com in the pages read on 2026-11-12.",
     "License a market-data vendor (the league's official betting-data distributor or a commercial "
     "odds vendor) or use a book's own historical API under its terms. Record the licence id, the "
     "snapshot time and the settlement rule for every price.",
     "Yes — blocks ROI, edge and reward eligibility."),
    ("Q02", "What are the licence terms of the third-party archive the repo already uses?",
     "nfl-quant ingests nflverse/nfldata from GitHub and its own provenance file says the lines are "
     "third-party and that rights must be verified before production use.",
     "A pinned commit hash and a SHA-256 of the downloaded archive in nfl-quant/data/provenance.json.",
     "A written licence/permission covering commercial use and redistribution.",
     "Read the archive's DATASETS.md and README, keep the commit pin, and get written permission "
     "before publishing any derived price or ROI.",
     "Yes — blocks any priced result that is not licensed."),
    ("Q03", "Can 2nd/3rd/4th-string depth be established from an official source?",
     "The task asks for defensive and offensive deficiency tracking when backups replace starters.",
     "Official roster (S7) with jersey number, position and experience; official injury report (S1); "
     "official transactions (S11); Next Gen Stats player pages (S15).",
     "An official depth chart. https://www.nfl.com/teams/kansas-city-chiefs/depth-chart/ returns a 404 "
     "on 2026-11-12 (S6), so string position is not obtainable from that route.",
     "Either (a) license a depth-chart feed, or (b) publish a documented proxy: 'listed starter unknown "
     "— rank not published', plus injury-driven exposure counts only. Do not infer a string from "
     "experience or jersey number.",
     "Yes — blocks a verified depth-deficiency model; does not block an injury-exposure count."),
    ("Q04", "What does a blank game status mean?",
     "If blank means 'will play', treating it as doubtful is wrong; if blank means 'not yet known', "
     "treating it as available is also wrong.",
     "The official report prints blank cells for 270 of 276 rows (S1).",
     "The league's own documentation of the report's column semantics for 2026.",
     "Read the 2026 league policy/rulebook (S14) and the report's own help text; if semantics remain "
     "unclear, publish the cell as blank and score strategies both ways to test sensitivity.",
     "Yes — blocks any injury-adjusted projection until resolved."),
    ("Q05", "Which practice day does the published report describe?",
     "Practice participation is only predictive if we know whether it is Wednesday, Thursday or the "
     "final Friday report.",
     "The page is titled 'Injuries - WEEK 10' and gives one status per player (S1).",
     "An explicit report date on the page, or a timestamped archive of each day's report.",
     "Snapshot the page every day at a fixed UTC time and store the raw HTML with a hash; compare days "
     "to measure how often statuses change (a real, measurable quantity).",
     "Yes — blocks any 'late-week news' signal."),
    ("Q06", "How many out-of-sample games are needed before a strategy can be rewarded?",
     "The repo's own gate G1 demands 300 graded games. A 272-game season cannot supply that in one year.",
     "An explicitly pre-registered 300-game floor in the existing workspaces.",
     "A decision: multi-season history (with official results) or a lower, justified floor.",
     "Assemble 3+ seasons of official results from nfl.com schedules, then pre-register the floor and "
     "the holdout before any evaluation. Do not lower the floor after seeing results.",
     "Yes — blocks reward eligibility."),
    ("Q07", "May per-game player logs be collected at all?",
     "Prop and prop-combo research needs per-game player data, not season totals.",
     "nfl.com exposes per-game 'Recent Games' tables on player pages (S10) and season leader tables (S8).",
     "The site terms that govern automated collection, and a licence for redistribution.",
     "Read nfl.com/terms and robots policy, then choose: manual transcription of small samples, "
     "licensed bulk data, or no player-level research. Record the decision with its source.",
     "Yes — blocks prop and prop-combo strategy work."),
    ("Q08", "What is actually being rewarded?",
     "A leaderboard that pays money is regulated activity in most jurisdictions; points are not.",
     "A leaderboard design with zero rewards because nothing passed the gates.",
     "A decision from the owner: cash, credits, or recognition only. Plus the legal review for the "
     "chosen option and the jurisdiction.",
     "Write the reward rules down (currency, eligibility, tax, jurisdiction), then have counsel review "
     "before the first payout. Until then the leaderboard pays nothing.",
     "Yes — blocks competition launch."),
    ("Q09", "Can same-game parlay dependence be measured from official data?",
     "Multiplying leg probabilities assumes independence; in the same game the legs are correlated, so "
     "an independence price is wrong in a direction that matters.",
     "Official final scores for 137 team-games and official per-game player tables (S10) for a few players.",
     "A player-game panel wide enough to estimate pairwise joint distributions, and a market price for "
     "each leg.",
     "Build a player-game panel from licensed data, then estimate pairwise correlations with confidence "
     "intervals and use them in the joint price; publish the interval, not just the point estimate.",
     "Yes — blocks SGP/prop-combo eligibility."),
    ("Q10", "Which of the four NFL workspaces is canonical?",
     "nfl/, nfl-research/, nfl-lab/ and nfl-quant/ publish overlapping dashboards with different claims. "
     "A reader cannot tell which one to trust.",
     "All four exist in the repository and are linked from different places.",
     "One owner decision plus a redirect from the other three.",
     "Pick one canonical NFL dashboard, mark the others 'retained/archived' with a banner, and keep a "
     "single source register.",
     "No — but it confuses every reader until decided."),
    ("Q11", "What timestamp defines 'before kickoff'?",
     "A signal that uses information published after the snap cannot be traded; lookahead is the most "
     "common way a backtest looks skilful.",
     "Kickoff times from the official schedule (S4) are known; injury-report publication times are not "
     "published on the page.",
     "A recorded capture time for every input, in UTC, with the raw payload hashed.",
     "Make every ingest write (captured_utc, source_url, sha256) and make the backtest refuse any input "
     "captured after the kickoff it is used to predict.",
     "Yes — blocks any honest backtest."),
    ("Q12", "How stale may a snapshot be?",
     "The stored nfl-lab snapshot is from 2026-11-02 (Week 8) and today is Week 10. It is not wrong — "
     "it reconciles exactly — but it is six days old.",
     "A byte-identical reconciliation of the stored Week 8 standings plus the 15 official Week 9 "
     "results plus the Week 8 Monday game against today's official standings: 32 of 32 teams match.",
     "A refresh policy: how often, and what triggers a rebuild.",
     "Refresh on a schedule (daily during the season, after each game window) and stamp every page with "
     "the capture time; fail the build if the stamp is older than the policy allows.",
     "No — the staleness is documented; the policy is the decision."),
    ("Q13", "Is 'no injuries reported' the same as 'no injuries'?",
     "LAC and BAL print 'No Injuries Reported'. Treating that as zero is an assumption.",
     "The exact string on the official page for both teams (S1).",
     "A statement of what the league means by that string.",
     "Keep the string verbatim, count it as 'not reported' rather than zero, and test whether the "
     "distinction changes any injury-based feature.",
     "No — handled by not inferring."),
    ("Q14", "What would make the owner reject a suggestion?",
     "The suggestions page asks the owner to choose a path; without an explicit cost ceiling and risk "
     "budget, every option looks equally good.",
     "Fourteen suggestions with effort, risk and prerequisites listed on the Suggestions page.",
     "The owner's constraints: budget, time, appetite for data licensing, and whether real money is "
     "involved.",
     "Record the answer once on the Suggestions page; every future suggestion is scored against it.",
     "Yes — blocks a final choice, not the analysis."),
]

# -------------------------------------------------------------- suggestions --
# (id, area, suggestion, why, tradeoff, effort, risk, prereq, recommendation)
SUGGESTIONS = [
    ("S01", "Site / navigation",
     "Publish one canonical NFL dashboard and demote the four older NFL workspaces to a clearly-labelled "
     "'retained experiments' section.",
     "Right now a reader can land on nfl/, nfl-research/, nfl-lab/ or nfl-quant/ and see four different "
     "framings of the same question. Decision-making needs one front door.",
     "Some prior sessions' layouts disappear from the main path — they remain online, one click away.",
     "Low", "Low — no data changes.",
     "Q10", "Recommended"),
    ("S02", "Decision support",
     "Give every suggestion a decision column (Accept / Defer / Reject) plus effort, risk and the question "
     "it depends on, so a reviewer can choose a path in one pass.",
     "This is the page you asked for: a place to review options before any code changes.",
     "Adds review work up front; the list has to be maintained.",
     "Low", "Low.",
     "Q14", "Recommended"),
    ("S03", "Data integrity",
     "Stamp every page and every table with its capture time and a SHA-256 of the raw source, and fail "
     "the build when a table row has no source link.",
     "Turns 'we think this is right' into 'this is what the official page said at this moment'.",
     "Slightly noisier pages; requires storing raw payloads.",
     "Medium", "Low.",
     "Q11, Q12", "Recommended"),
    ("S04", "Lookahead control",
     "Add a 'known before kickoff?' column to every input table and refuse to score a strategy that uses "
     "an input captured after the kickoff.",
     "Lookahead is the cheapest way to fake skill; the injury report is exactly the kind of input that "
     "moves after the game starts.",
     "Some rows become unusable, which shrinks the sample — the honest outcome.",
     "Medium", "Low.",
     "Q11", "Recommended"),
    ("S05", "Strategy governance",
     "Keep pre-registration: commit the strategy list, the gate thresholds and the holdout window to git "
     "before the first evaluation run, and never edit them afterwards without a version bump.",
     "nfl-lab already did this and it is the only reason its zero-reward result can be trusted.",
     "You cannot quietly tune a losing strategy.",
     "Low", "Low.",
     "Q06", "Recommended"),
    ("S06", "Luck removal",
     "Score every strategy with a walk-forward holdout, a permutation test on the realised metric, "
     "Benjamini-Hochberg control across all strategies tested, and a bootstrap interval on the edge.",
     "A single p-value over many tested strategies is a luck detector, not a skill detector.",
     "Wider intervals and more 'fails' — which is the point.",
     "Medium", "Low.",
     "Q06", "Recommended"),
    ("S07", "Injuries",
     "Build an injury-exposure table now (counts by team, position group and status) and leave the "
     "string-position column blank until an official depth source exists.",
     "It captures what is verifiable today: who is not practising, at which position, on which team.",
     "It is not yet a depth-deficiency model; a reader could over-read it.",
     "Low", "Low.",
     "Q03, Q04", "Recommended"),
    ("S08", "Injuries",
     "Add transactions to the injury join: a player traded on 11/10 must not be counted against his old "
     "team's depth.",
     "November trades moved a dozen players, including starters, between teams that play this week.",
     "More moving parts in the join.",
     "Medium", "Low.",
     "Q03", "Recommended"),
    ("S09", "Line origination",
     "Publish a transparent baseline fair line (points-based rating + measured home-field advantage) with "
     "its walk-forward error, before any market price is licensed.",
     "It gives an honest, reproducible starting point and a floor that any fancy model must beat.",
     "A crude baseline will look weak next to a market line; that is the correct comparison.",
     "Medium", "Low.",
     "Q01", "Recommended"),
    ("S10", "Line origination",
     "Do not publish an edge until a licensed price exists; publish only the model line, the error and the "
     "gate status.",
     "nfl-quant's own provenance file says its lines are third-party with no official league source. An "
     "edge computed against those is a claim about a vendor, not about the market.",
     "Slower progress toward a bettable product.",
     "Low", "Low.",
     "Q01, Q02", "Recommended"),
    ("S11", "Combinations",
     "Price parlays and prop combos with a measured dependence term, and publish the interval; block the "
     "product while the dependence estimate is missing.",
     "Independence pricing is a silent error that gets worse as legs are added.",
     "No parlay product until the panel exists.",
     "High", "Medium — the panel is a data purchase.",
     "Q09", "Recommended"),
    ("S12", "Leaderboard",
     "Award nothing until a strategy clears every gate; show the failure reason per gate instead of a "
     "rank.",
     "A leaderboard that pays the top of a small sample pays for luck and teaches the wrong lesson.",
     "The board looks empty — which is the truthful state.",
     "Low", "Low.",
     "Q06, Q08", "Recommended"),
    ("S13", "Leaderboard",
     "Score on out-of-sample games only, weight by number of graded bets, and require a minimum graded "
     "count before a strategy appears at all.",
     "Stops a 3-for-3 start from outranking a 200-bet record.",
     "Slower leaderboard movement.",
     "Low", "Low.",
     "Q06", "Recommended"),
    ("S14", "Missing information",
     "Run this questions register as the project backlog: every unknown gets an owner, a discovery method "
     "and a blocked-or-not flag, and the site shows the count of blocking unknowns.",
     "It converts 'we don't know' into a finite, prioritised list someone can actually work.",
     "Needs a weekly pass to stay honest.",
     "Low", "Low.",
     "—", "Recommended"),
    ("S15", "Publication",
     "Keep the GitHub Pages build as a hard gate: a broken link, an unsourced row or a stale stamp fails "
     "the deploy.",
     "The repository's Pages build has been reporting 'errored' since 2026-11-06. A site nobody can load "
     "cannot support a decision.",
     "A red build blocks publication until fixed.",
     "Medium", "Low.",
     "Q12", "Recommended"),
]

# -------------------------------------------------------------------- flags ---
# (id, item, finding, evidence, status)
FLAGS = [
    ("F01", "Official depth charts",
     "The official nfl.com depth-chart route returns a 404 'Flag on the Play' page, so 2nd/3rd/4th-string "
     "ordering cannot be verified from an official source in this session.",
     "S6", "Open — blocks the depth model; an injury-exposure proxy is published instead."),
    ("F02", "Practice date on the injury report",
     "The Week 10 injury page does not state which practice day the statuses describe, and it changes "
     "during the week.",
     "S1", "Open — no practice-date claim is made anywhere on this site."),
    ("F03", "Blank game status",
     "270 of 276 injury rows have a blank game status; only 5 Out and 1 Questionable are published.",
     "S1", "Open — blanks are kept blank; nothing is inferred."),
    ("F04", "Blank injury type",
     "270 of 276 rows do not name an injury.",
     "S1", "Open — injury type is only shown where the official page prints it."),
    ("F05", "Stale stored snapshot",
     "The nfl-lab snapshot is dated 2026-11-02 (Week 8). It reconciles exactly to today's standings "
     "after adding the 15 Week 9 results and the Week 8 Monday game, so it is stale, not wrong.",
     "S2, S3, S5", "Explained — a refresh policy is proposed (Q12/S03)."),
    ("F06", "Four parallel NFL workspaces",
     "nfl/, nfl-research/, nfl-lab/ and nfl-quant/ all publish NFL dashboards with different claims.",
     "repository", "Open — canonical choice is Q10/S01."),
    ("F07", "Third-party inputs in nfl-quant",
     "nfl-quant ingests nflverse/nfldata from GitHub. Its own provenance file labels the lines THIRD-PARTY "
     "and says no official league source exists for them.",
     "S11 (transactions) shows the repo can reach official data, but no official price archive exists.",
     "Open — do not present nfl-quant prices or ROI as official; see Q01/Q02."),
    ("F08", "No official price",
     "No price, spread, total or prop line appears on the official pages read in this session.",
     "S1-S10", "Open — every price, edge and ROI cell on this site is blank by rule."),
    ("F09", "Report is not final",
     "The official report lists Sam Darnold as a non-participant with no game status, while an official "
     "news article states he is ruled out and a backup will start.",
     "S1, S12", "Open — late-week official news must be joined to the report before projecting."),
    ("F10", "Trades during the week",
     "Twelve trades were recorded between 11/06 and 11/10, including starters moving to teams playing "
     "in Week 10.",
     "S11", "Open — the injury/depth join must be trade-aware (S08)."),
    ("F11", "Team code mismatch",
     "The official standings use LA and WAS while other pages use LAR and WSH.",
     "S2, S9", "Resolved in this site by normalising to LA/WAS and recording the mapping."),
    ("F12", "Injury report scope",
     "CHI, DEN, PHI and TB are on bye and LAC/BAL print 'No Injuries Reported'; the report therefore has "
     "no row for six teams.",
     "S1, S4", "Explained — absence of a row is not zero injuries (Q13)."),
    ("F13", "Concurrent sessions",
     "Two peer sessions claim the same path nfl-decision/** and two claim the root index.html in "
     "COORDINATION.md at the same time.",
     "COORDINATION.md (this session's claim entry)", "Open — logged; this session edits none of those paths."),
    ("F14", "GitHub Pages build status",
     "The repository's legacy Pages build reports status 'errored' ('Page build failed') on the latest "
     "build for commit a10610b, dated 2026-11-06.",
     "GitHub Pages API (builds/latest)", "Open — must be rechecked after this session's merge."),
    ("F15", "Stored team codes vs official",
     "The stored nfl-lab standings are consistent with official values for every cell checked, but the "
     "stored file has no capture timestamp column.",
     "S2 + repository file", "Explained — freshness is published per page instead."),
]
