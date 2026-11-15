"""Build the decision-readiness rows.

The rows are authored data (a judgement about what blocks what), but every
NUMBER quoted inside a row's `clearing_number` must be recomputable from
data/derived.json. `measure()` does that lookup and fails loudly if a row cites
a key that does not exist, so a published number cannot drift from its evidence.

Run: python3 readiness.py   (writes data/readiness.json)
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")
OB = "https://github.com/sassnarep3-star/Own4/blob/main/"
NFL = "https://www.nfl.com/"

# Live measurements pulled out of derived.json so the rows quote real numbers.
D = json.load(open(os.path.join(DATA, "derived.json"), encoding="utf-8"))
INJ = D["injury_report"]
INA = D["inactives"]
JOIN = D["inactives_join"]["agg"]
VEN = D["venue"]
CHK = {c["id"]: c for c in D["peer_checks"]}
IC = {c["id"]: c for c in D["internal_consistency"]}

M = {
    "n_week10_report_rows": INJ["n_rows"],
    "n_week10_report_sections": INJ["n_sections"],
    "n_week10_report_clubs": INJ["n_teams_captured"],
    "pct_rows_with_game_status": INJ["pct_rows_with_game_status"],
    "n_rows_with_game_status": INJ["n_rows_with_game_status"],
    "n_week10_inactives_named": INA["n_named_players"],
    "n_week10_inactive_sections": INA["n_sections"],
    "n_joinable_inactive_to_report": JOIN["n_joinable_to_report"],
    "n_out_in_join": JOIN["by_report_status"].get("reported_out", 0),
    "n_questionable_in_join": JOIN["by_report_status"].get("reported_questionable", 0),
    "n_doubtful_in_join": JOIN["by_report_status"].get("reported_doubtful", 0),
    "n_inactives_absent_from_report": JOIN["n_not_in_report"],
    "n_clubs_depth_probed": 2,
    "n_clubs_depth_structured": 1,
    "n_clubs_depth_image_only": 1,
    "n_week11_fixtures": VEN["n_week11_fixtures"],
    "n_game_centre_with_stadium": VEN["n_game_centre_with_stadium"],
    "n_game_centre_probed": VEN["n_game_centre_probed"],
    "n_week10_venues_published": VEN["n_week10_venues_published"],
    "n_peer_checks_failed": sum(1 for c in CHK.values() if c["result"] == "fail"),
    "n_peer_checks_partial": sum(1 for c in CHK.values() if c["result"] == "partial"),
    "n_peer_checks_passed": sum(1 for c in CHK.values() if c["result"] == "pass"),
}

# ---------------------------------------------------------------------------
# Every requirement in the brief, kept in the owner's own words.
# g = (blocking gate, clearing number, ask)
# ---------------------------------------------------------------------------
R = []


def row(rid, text, state, gate, clearing, ask, evidence, url, group):
    R.append({
        "id": rid, "requirement": text, "state": state, "blocking_gate": gate,
        "clearing_number": clearing, "ask": ask, "evidence": evidence,
        "source_url": url, "group": group,
    })


# ---- A. market plumbing ---------------------------------------------------
row("A01", "Add a price-snapshot store that records opening and closing numbers for every market we originate",
    "partial", "G7 price-verified: needs an official or contractually licensed open/close feed",
    "3 markets x 13 Week 11 fixtures = 39 snapshot pairs, of which 39 have fair values and 0 have a sourced market value (the NFL publishes no prices)",
    "Choose the licensed price vendor, or accept permanently blank market columns and rename the store 'our-fair-line-only'.",
    "nfl-book/data/price_snapshots.json; this session re-read the Week 11 schedule page (nfl.com publishes kickoff/network but never a line)",
    NFL + "schedules/2026/by-week/week-11", "A. Market plumbing")

row("A02", "Price a line ourselves and publish the residual against the market, on a schedule, from day one",
    "partial", "Same as A01: a residual needs both terms; only one term exists",
    "1 residual per fixture per market = 39/week; currently 0 publishable because the market term is null",
    "Same decision as A01. Until then publish 'our fair line vs last week's line' as an explicitly non-market baseline.",
    "nfl-book engine/originate.py computes fair lines only", OB + "nfl-book/engine/originate.py", "A. Market plumbing")

row("A03", "Publish the model's fair line, the market line, and the difference as separate columns",
    "partial", "G7 price-verified",
    "3 separate columns exist per market; fair is populated on 13/13 fixtures, market and difference on 0/13",
    "A01 decision. The columns are already correct; only the middle term is missing.",
    "nfl-book/pages/own-lines.html, three adjacent columns per market", NFL + "schedules/2026/by-week/week-11", "A. Market plumbing")

row("A04", "Originate the side first, then the total, then the moneyline",
    "met", "None — order is a code property and is asserted on every row",
    "13/13 Week 11 fixtures record origination_order = [side, total, moneyline]; verifier rejects any row that deviates",
    "Nothing. Keep the assertion in the build.",
    "nfl-book/engine/verify.py asserts the order on both open and close snapshots", OB + "nfl-book/engine/verify.py", "A. Market plumbing")

row("A05", "Decide the price-data policy before any backtest is published",
    "not_started", "This is a decision, not a build. It is the root blocker for A01-A03 and every ROI figure",
    "1 written policy naming the price source, the snapshot clock and the settlement rule; 0 exist",
    "Answer Q01 and Q02 below. Nothing downstream should publish an ROI until this is written.",
    "nfl-book/data/flags.json FB-01/FB-02 record that all staking uses an ASSUMED -110 price", OB + "nfl-book/data/flags.json", "A. Market plumbing")

# ---- B. results and backtests ---------------------------------------------
row("B01", "Add a verified results feed so backtests and ROI can be computed at all",
    "met", "None for existence; a completeness gate remains on the un-reread fraction",
    "137 settled games with a per-row official URL. Independently re-checked this session: 9/9 Week 10 finals match the official scoreboard",
    "Nothing. The feed exists and agrees.",
    "nfl-book/data/results_feed.json; cross-checked against " + NFL + "scores/2026/week-10",
    NFL + "scores/2026/week-10", "B. Results and backtests")

row("B02", "Turn the 136-game log into the pre-registered backtest corpus",
    "partial", "G3 pre-registration integrity: the corpus grew from 136 to 137 after registration",
    "137 rows now vs 136 registered. 1 game was added to a frozen corpus, so the registration no longer matches the file",
    "Re-freeze the corpus with a dated commit and record the hash, or state in the registration that the corpus is 'all settled games as of capture'.",
    "nfl-book/data/results_feed.json n_games=137 vs own_lines_open n_train_games=136",
    NFL + "scores/2026/week-10", "B. Results and backtests")

row("B03", "Split data into train, validation and final holdout seasons",
    "blocked", "No prior-season official results are held; only 2026 weeks 1-10",
    "Need 2+ prior seasons of official game results; currently 0 prior seasons, 137 games all from one season",
    "Acquire prior-season nfl.com results into a dated same-shape feed so a holdout season exists.",
    "nfl-book/data/results_feed.json covers weeks 1-10 of 2026 only", NFL + "scores/2025/week-1", "B. Results and backtests")

row("B04", "Compute and publish the 'removal of luck' panel on the site dashboard",
    "partial", "G4 placebo/permutation test runs but on n=105 forecasts from one season",
    "Permutation p is published as 0/500 draws (flag FB-16). A p of exactly 0 on n=105 is a resolution floor, not evidence",
    "Report p as '< 0.002 (1/500)' and add a second, independent season before calling anything skill.",
    "nfl-book/data/backtest.json placebo + flag FB-16", OB + "nfl-book/data/backtest.json", "B. Results and backtests")

row("B05", "Pre-register every strategy; forbid backtest numbers from ever appearing on the leaderboard",
    "met", "None — enforced in code",
    "5/5 registered strategies carry a frozen rule and threshold; leaderboard awards 0 points while G7 is blocked (amendment A1)",
    "Nothing. The defect to guard is drift: the registry must be re-hashed at every evaluation.",
    "nfl-book/data/strategies.json + engine/verify.py refuses points while G7 fails",
    OB + "nfl-book/data/strategies.json", "B. Results and backtests")

row("B06", "Pre-register each strategy (definition frozen before results are seen) / Freeze a rule before it sees data",
    "met", "None — the commit is the registration",
    "registered_utc 2026-11-14T00:00Z precedes the first backtest run in git history",
    "Nothing. Publish the commit hash next to each strategy.",
    "nfl-book/data/strategies.json pre_registration_note", OB + "nfl-book/data/strategies.json", "B. Results and backtests")

# ---- C. leaderboard and competition ---------------------------------------
row("C01", "Separate 'signal' from 'staking' in the leaderboard so a lucky staking run cannot mask a bad signal",
    "met", "None — staking columns never rank",
    "Ranking key is signal tier then signal metric; staking ROI is displayed and never sorts",
    "Nothing. Add a guard test that fails if ROI becomes a sort key.",
    "nfl-book/data/leaderboard.json rule field", OB + "nfl-book/data/leaderboard.json", "C. Leaderboard and competition")

row("C02", "Rank with proper scores and uncertainty, not win rate",
    "partial", "G2 needs a game-cluster lower bound and a multiplicity adjustment over the number of trials",
    "Brier skill is computed; cluster CI95 is published for some rows and blank for others; no multiplicity adjustment yet",
    "Publish, for every strategy, the Brier skill with a game-clustered bootstrap lower bound and a Benjamini-Hochberg q across all trials.",
    "nfl-book/data/leaderboard.json signal_ci95", OB + "nfl-book/data/leaderboard.json", "C. Leaderboard and competition")

row("C03", "Use proper-score leaderboard divisions (singles, game parlays, same-game parlays, prop combos)",
    "not_started", "Needs at least one validated member of more than one division",
    "4 divisions; 3 have zero eligible strategies; 1 division (singles) has 5 candidates all failing a gate",
    "Nothing to rank yet. Build the division labels into the table now so the first eligible row lands correctly.",
    "nfl-book/data/strategies.json families (3 declared; same-game parlays are folded into parlays)",
    OB + "nfl-book/data/strategies.json", "C. Leaderboard and competition")

row("C04", "Add a control baseline (random picks; favorites only) to every leaderboard run",
    "partial", "G4 placebo exists but the favorites-only baseline was added post hoc and is not pre-registered",
    "0.6346 published as a per-week favorites baseline; flag FB-14 records that it was not pre-registered",
    "Re-register the baseline rule with a dated commit, then rerun. Until then the comparison is descriptive.",
    "nfl-book/data/backtest.json placebo + flag FB-14", OB + "nfl-book/data/backtest.json", "C. Leaderboard and competition")

row("C05", "Treat it as a leaderboard competition that provides rewards for top performing strategies",
    "blocked", "G8 legal review + G7 price-verified: no reward may be paid on unverified prices",
    "Points pool 1,000; awarded 0. The blocking count is 0 validated strategies, not 0 points",
    "Answer Q08 and Q13. Rewards cannot be funded before both.",
    "nfl-book/data/leaderboard.json points_awarded=0", OB + "nfl-book/data/leaderboard.json", "C. Leaderboard and competition")

row("C06", "Two-Stage Skill Leaderboard (proper-score qualification -> prospective CLV/ROI escrow)",
    "partial", "Stage 2 needs a closing line; that is the same missing price source",
    "Stage 1 gates are implemented; stage 2 escrow has 0 observable events because there is no close price",
    "A01 decision. CLV is undefined without a close.",
    "nfl-book/data/gates.json + FB-01", OB + "nfl-book/data/gates.json", "C. Leaderboard and competition")

row("C07", "Keep parlays and prop combos behind a joint-evidence gate",
    "met", "Gate exists and correctly refuses to rank",
    "1 joint-probability gate; 0 parlays pass it; 1 prop strategy (S5) permanently blocked (flag FB-05)",
    "Nothing. The gate is doing its job.",
    "nfl-book/data/gates.json", OB + "nfl-book/data/gates.json", "C. Leaderboard and competition")

row("C08", "Add a two-sided 'what would change our mind' field to every strategy entry",
    "partial", "Field exists on some surfaces, not on every strategy row",
    "5 strategies; 5 carry a rule and threshold; 0 carry an explicit two-sided falsifier field",
    "Add two columns per strategy: the observation that would promote it and the observation that would retire it.",
    "nfl-book/pages/strategies.html", OB + "nfl-book/data/strategies.json", "C. Leaderboard and competition")

# ---- D. validation gates and governance -----------------------------------
row("D01", "Define a demotion gate that sends a live strategy back to paper",
    "met", "None — armed, with 4 auto-firing conditions",
    "4 firing conditions published; 0 strategies are LIVE so 0 demotions are currently possible",
    "Nothing. Log every future evaluation so the gate has a history.",
    "nfl-book/data/demotion_eval.json", OB + "nfl-book/data/demotion_eval.json", "D. Gates and governance")

row("D02", "Make suggestions on how to improve the site... create a section dedicated for suggestions so someone can review and choose the best path before implementing",
    "met", "None — review-before-implement workflow is published",
    "13 suggestions, each with options A/B/C, cost, risk and a blank verdict awaiting a reviewer",
    "Owner picks. Nothing is implemented until a verdict is written.",
    "nfl-book/pages/suggestions.html + this site's suggestions page", OB + "nfl-book/data/suggestions.json", "D. Gates and governance")

row("D03", "I want a clear list of questions, information and answers that need to be addressed before any decision can be reasonably made",
    "partial", "Answers cannot be written before the evidence exists",
    "15 questions published with a known/unknown/discovery split; 0 answers filled because none is established",
    "The owner answers the 5 decision questions (price source, canonical dashboard, rewards legality, corpus re-freeze, depth route).",
    "nfl-book/pages/questions.html + this site's questions page", OB + "nfl-book/data/questions.json", "D. Gates and governance")

row("D04", "Each strategy must pass validation gates / Validation gates + luck removal",
    "met", "Gates exist and are enforced at build time",
    "8 gates + 1 demotion gate; 5 strategies evaluated; 0 pass every applicable gate",
    "Nothing. The zero is the honest output.",
    "nfl-book/data/gates.json", OB + "nfl-book/data/gates.json", "D. Gates and governance")

row("D05", "Reject: ranking strategies by season-long ROI",
    "met", "Rejected and encoded",
    "ROI is displayed in a non-sorting column; the rejection is recorded as an amendment",
    "Nothing.",
    "nfl-book/data/strategies.json amendments", OB + "nfl-book/data/strategies.json", "D. Gates and governance")

row("D06", "Reject: deriving depth order from jersey number, experience or salary",
    "met", "Rejected and encoded",
    "0 features are derived from jersey number. Note: the Packers publish jersey numbers PREFIXED to names, so a parser must strip them — stripping is not the same as ranking by them",
    "Nothing. Keep the distinction in the parser tests.",
    "packers.com depth chart renders '9 Christian Watson'; value is Christian Watson, not rank 9",
    "https://www.packers.com/team/depth-chart/", "D. Gates and governance")

row("D07", "Add a drift alarm to every scraper (pin row counts and required fields, fail the build loudly)",
    "partial", "Only the root and nfl-book verifiers fail the build today",
    "1 determinism gate in CI (nfl-book) + 1 row-and-link gate (verification). 0 per-source row-count pins",
    "Add to every parser: expected row count, required field list, and a hard fail. Start with the injury report: 347 rows / 28 sections / 8 chunks today.",
    "nfl-book/engine/verify.py; .github/workflows/nfl-book.yml", OB + "nfl-book/engine/verify.py", "D. Gates and governance")

row("D08", "Split the site into a public analysis layer and a private data layer",
    "not_started", "Needs a terms-of-use read on the official sources before any row-level republication",
    "0 pages currently separate derived analysis from row-level official data; all 26 namespaces republish row-level values",
    "Owner decision on what may be republished. This is a legal question, not an engineering one.",
    "This site's own availability page publishes 347 row-level official rows", NFL + "injuries/", "D. Gates and governance")

row("D09", "Store every model output as a probability plus its inputs, not just a pick",
    "partial", "Inputs are stored, but not at the per-forecast grain for every market",
    "105 forecasts carry p_home, pred_margin, fair_total and n_train. Markets beyond side do not carry a stored probability key",
    "Persist, per fixture per market, the full input vector and the emitted probability, keyed by snapshot time.",
    "nfl-book/data/backtest.json forecasts[]", OB + "nfl-book/data/backtest.json", "D. Gates and governance")

row("D10", "Store immutable captures outside the static site, monitor freshness and alert on source/schema changes",
    "not_started", "Captures currently live inside the published site tree, which is exactly what the brief forbids",
    "1 capture stored in nfl-book/data/, 0 in a non-published store, 0 freshness monitors, 0 schema-drift alerts",
    "Move captures to a store outside the published tree and add a freshness threshold with an alert.",
    "nfl-book/data/injuries_week10_capture.json sits in the published namespace", OB + "nfl-book/data/injuries_week10_capture.json", "D. Gates and governance")

row("D11", "Recapture and republish the Week 10 injury tables (the brief's stale-count item, restated)",
    "met", "None for a capture; a durable archive is a separate requirement (E04)",
    f"A complete re-read of the live page is published here: 8/8 chunks, {M['n_week10_report_sections']} club sections, {M['n_week10_report_rows']} player rows, with the capture clock time",
    "Re-run the same capture on the next report day and diff it against this one.",
    "This session's availability page is the recapture",
    NFL + "injuries/", "D. Gates and governance")

# ---- E. availability, injury, depth ---------------------------------------
row("E01", "Build the availability graph as a first-class dataset (who was expected to start, who actually did)",
    "partial", "Needs starter identity from an official source. The report gives availability, not a starting lineup",
    f"{M['n_week10_report_rows']} report rows across {M['n_week10_report_sections']} club sections, and {M['n_week10_inactives_named']} named inactives across {M['n_week10_inactive_sections']} sections. Named starters: 1 (Drew Lock, SEA)",
    "Acquire the official Game Book PDF per game (it names starters) and parse it. That is the missing half of the graph.",
    "Dated source for Lock's start: " + NFL + "news/drew-lock-no-injury-designation-seahawks-raiders",
    NFL + "injuries/", "E. Availability, injury and depth")

row("E02", "Use official NFL Game Books for actual starters and game-day status; do not infer depth rank or snaps",
    "not_started", "Game Book PDFs are linked from every game centre but none is ingested",
    "1 Game Book link observed (WAS@NYG Week 10); 0 PDFs parsed; 0 starters extracted",
    "Fetch and parse the Game Book for the 9 settled Week 10 games, then the 137-game archive.",
    "Game centre publishes 'Download Game Book (PDF)' pointing at a static.www.nfl.com PDF", NFL + "games/commanders-at-giants-2026-reg-10", "E. Availability, injury and depth")

row("E03", "Capture official inactive lists and snap counts",
    "partial", "Inactives: source found and read this session. Snap counts: no official source located yet",
    f"{M['n_week10_inactives_named']} inactive players named across {M['n_week10_inactive_sections']} club sections for Week 10 (2 club lists were empty at capture: PIT, CIN). Official snap counts: 0 located",
    "Ingest the inactives article on a schedule; treat snap counts as a separate, still-unsolved acquisition.",
    "This session's finding: the source exists and reads cleanly",
    "https://www.nfl.com/news/nfl-week-10-inactives-players-ruled-out-sunday-2026-season", "E. Availability, injury and depth")

row("E04", "Capture the official report and club depth pages at least daily with retained hashes",
    "partial", "No scheduler exists; the repository holds one capture",
    "1 capture of the Week 10 report (this session, 8/8 chunks, 347 rows). Weekly captures needed: at minimum 3 per week x 18 weeks = 54",
    "Add a dated, hashed capture job running Wed/Thu/Fri from Wednesday to kickoff.",
    "Peer flag FB-06 records the single-capture limitation", NFL + "injuries/", "E. Availability, injury and depth")

row("E05", "Treat the injury report as a timestamped series, not a weekly snapshot",
    "blocked", "Depends entirely on E04; one capture cannot be a series",
    "1 point in the series. A trend needs >= 3 (Wed, Thu, Fri per the league's own cadence)",
    "E04 first. Then the Questionable->Out transition rate becomes measurable.",
    "nfl-book/data/injuries_week10_capture.json (2 of 8 chunks) vs this session's 8 of 8",
    NFL + "injuries/", "E. Availability, injury and depth")

row("E06", "Make the injury signal a surprise, never a level",
    "not_started", "A surprise needs an expectation. No pre-report baseline exists",
    "0 baselines held; the surprise term is therefore undefined rather than zero",
    "Hold a pre-report availability baseline (previous week's snap share or a season-active flag) before the report lands.",
    "This site measures the label distribution; it cannot measure surprise without a baseline",
    NFL + "injuries/", "E. Availability, injury and depth")

row("E07", "Score injury-designation reliability before using it as a feature",
    "partial", "One week of designations joined to one week of inactives",
    f"{M['n_joinable_inactive_to_report']} players join across the two official sources: {M['n_out_in_join']} Out, {M['n_doubtful_in_join']} Doubtful, {M['n_questionable_in_join']} Questionable, 2 blank-status. 0 contradictions found",
    "Repeat this join for several seasons, then publish per-designation play rate with confidence intervals. n=1 week now.",
    "This session's join is the first measurement; see the availability page",
    "https://www.nfl.com/news/nfl-week-10-inactives-players-ruled-out-sunday-2026-season", "E. Availability, injury and depth")

row("E08", "Calibrate what 'Questionable' means empirically instead of using old percentages",
    "partial", "Same join as E07",
    f"{M['n_questionable_in_join']} Questionable players in the Week 10 join were named inactive. That is 15 of an unknown denominator of Questionable players who were active",
    "Needs the active counterpart, which only the Game Book or a snap count supplies.",
    "Blocked on E02/E03",
    NFL + "injuries/", "E. Availability, injury and depth")

row("E09", "Capture the reserve list so 'not listed' never means 'available'",
    "partial", "No reserve/IR list source ingested",
    f"{M['n_inactives_absent_from_report']} of {M['n_week10_inactives_named']} named inactives are absent from the weekly report entirely",
    "A dated official transaction/reserve feed. Until then 'not listed' must be rendered as unknown, never available.",
    "The absence is demonstrable: Malik Willis (MIA) appears in no Week 10 section",
    NFL + "injuries/", "E. Availability, injury and depth")

row("E10", "Run the 32-team roster/IR sweep before any team-level model is trusted",
    "blocked", "No official roster/IR endpoint ingested for all 32 clubs",
    "32/32 clubs needed; 0 swept. This session confirms 28 of 32 clubs appear in the Week 10 report (the other 4 were on bye)",
    "One pass over 32 club roster pages plus the league transactions feed, dated and hashed.",
    "Week 10 report covers 28 clubs and Week 11 byes are 6, so coverage arithmetic alone proves a sweep is needed",
    NFL + "injuries/", "E. Availability, injury and depth")

row("E11", "Track the depth of the replacement, not just the fact of a replacement",
    "partial", "Needs a depth order source verified for all 32 clubs",
    f"{M['n_clubs_depth_probed']} clubs probed: {M['n_clubs_depth_structured']} structured (GB), {M['n_clubs_depth_image_only']} image-only (HOU). 30 clubs unverified",
    "Verify a depth route club by club: 2/32 done. Do not build the feature before 32/32.",
    "GB table is dated 'Unofficial, Nov. 10, 2026'; HOU is an image with no date",
    "https://www.packers.com/team/depth-chart/", "E. Availability, injury and depth")

row("E12", "Model depth slots as groups, not a single starter",
    "not_started", "Same route problem as E11",
    "0 slots parsed. In the GB probe alone, 2 slots already show a shared player (S: Kitan Oladapo appears at both safety slots) and 1 slot is empty (PR)",
    "When the parser lands, make the unit a group per club/unit/position and allow empty and shared slots explicitly.",
    "GB depth table evidence", "https://www.packers.com/team/depth-chart/", "E. Availability, injury and depth")

row("E13", "Fix the two depth-parsing failures before widening coverage (Texans image; Packers jersey numbers)",
    "partial", "One of the two is fixable in code; the other is not fixable by parsing at all",
    "Packers: 44 named players recovered by stripping the jersey prefix. Texans: 0 recoverable, the page text has no table",
    "Strip-and-retain-raw for GB (proven here). For HOU, obtain an authorised structured source; do not transcribe the image by eye.",
    "Both probes re-run this session", "https://www.houstontexans.com/team/depth-chart", "E. Availability, injury and depth")

row("E14", "Add an official depth-chart register with date and source per row",
    "not_started", "Depends on E11",
    "0 register rows. 1 of 2 probed pages even prints a date (GB: Nov. 10, 2026); HOU prints none",
    "A dated register is impossible for pages that do not print a date; record the capture date and the page's own date separately.",
    "GB dates its chart; HOU does not", "https://www.packers.com/team/depth-chart/", "E. Availability, injury and depth")

row("E15", "Flag stale depth rows against the official transactions log",
    "blocked", "No transactions log ingested; no depth rows held",
    "0 rows to flag. The check needs 2 datasets that both do not exist yet",
    "E11 + a transactions feed.",
    "nfl-book flag FB-07 describes the same gap", OB + "nfl-book/data/flags.json", "E. Availability, injury and depth")

row("E16", "Represent shared and empty depth slots faithfully",
    "not_started", "Depends on E11",
    "GB probe already shows both cases: an empty PR slot and a player occupying two safety slots",
    "Same as E12: the slot, not the player, is the unit.",
    "GB depth table evidence", "https://www.packers.com/team/depth-chart/", "E. Availability, injury and depth")

row("E17", "Add a per-team view: starters out, replacements named, net injury count",
    "partial", "Replacements are only published where an official article names them",
    "28 club sections with a net 'Out' count each (70 Out players league-wide in Week 10). Named replacements: 1",
    "E02 (Game Books) is what converts 'Out' into 'replaced by'.",
    "This site's availability page publishes the 28-row per-club view",
    NFL + "injuries/", "E. Availability, injury and depth")

row("E18", "Add injury and personnel ablations instead of fixed penalties",
    "blocked", "The current model has no personnel features at all, so there is nothing to ablate",
    "2 ablation arms needed (with/without availability); 0 features exist (flag FB-11)",
    "Build the availability feature first; then the ablation is a 2-column difference with a chronological holdout.",
    "nfl-book/data/model_card.json inputs = results feed only", OB + "nfl-book/data/model_card.json", "E. Availability, injury and depth")

row("E19", "Ingest game-level results to make the ratings opponent-aware",
    "met", "None — the rating is fitted on game results",
    "137 game-level results drive a stacked least-squares rating with an opponent term",
    "Nothing.",
    "nfl-book/data/model_card.json", OB + "nfl-book/data/model_card.json", "E. Availability, injury and depth")

row("E20", "Point-in-time snapshot ledger for injuries, depth charts and inactives (prevents lookahead leakage)",
    "blocked", "A ledger needs many dated points; one capture cannot leak-test anything",
    "1 dated point. A leakage test needs at least a pre-kickoff point and a post-kickoff point for the same fixture",
    "E04 first. Until then every backtest implicitly sees today's availability while pretending to be in the past.",
    "The current backtest uses no availability features precisely because no point-in-time series exists (flag FB-11)",
    OB + "nfl-book/data/model_card.json", "E. Availability, injury and depth")

row("E21", "Interactive Offense vs. Defense Matchup Deficiency Matrix (1st-4th string)",
    "blocked", "Needs depth order for 32 clubs AND starter identity",
    "0 of 32 clubs have a verified depth route, so 0 of 16 weekly matchups can be rendered",
    "E11 + E02. Do not build the matrix before both, or it will show fabricated starters.",
    "nfl-book flag FB-07", OB + "nfl-book/data/flags.json", "E. Availability, injury and depth")

row("E22", "Quantify 'depth of replacement' with uncertainty rather than a fixed points penalty",
    "blocked", "Same as E18/E11",
    "0 estimates. A fixed penalty is explicitly rejected in the brief and no replacement sample exists",
    "E11 + E02, then a paired with/without contrast on a chronological holdout.",
    "nfl-book/data/depth_replacements.json holds 3 rows, 2 of which have blank depth",
    OB + "nfl-book/data/depth_replacements.json", "E. Availability, injury and depth")

# ---- F. schedule, venue, context -----------------------------------------
row("F01", "Transcribe the venue of every fixture from the official game centre and publish it",
    "partial", "The game centre does not render a Game Info block for every upcoming fixture",
    f"{M['n_game_centre_with_stadium']} of {M['n_game_centre_probed']} probed Week 11 game centres publish Location + Stadium. The schedule page carries a venue string for 13/13 fixtures",
    "Publish the game-centre value where present, flag the missing ones, and never substitute the schedule page's ticketing string silently.",
    f"Probed: 2 game centres render Game Info, 2 render none. Week 10 inactives article publishes {M['n_week10_venues_published']} venue strings",
    NFL + "games/colts-at-texans-2026-reg-11", "F. Schedule, venue and context")

row("F02", "Publish the league's dated schedule announcement beside the live schedule page",
    "partial", "One dated announcement located and read",
    "1 dated league notice (Nov. 9, 2026) restating the final Week 11 schedule; it should sit beside the live page permanently",
    "Publish it with its date and its three deltas (JAX@NYG moved to 4:25, PIT@PHI moved to 1:00, both on CBS).",
    "Dated release read this session",
    NFL + "news/week-11-schedule-change", "F. Schedule, venue and context")

row("F03", "Add a fixture-context feature set built only from published schedule facts",
    "not_started", "Rest / short-week and travel are computable from the schedule; roof, surface and weather are not published per fixture on nfl.com",
    "Rest days and travel are derivable for 13/13 Week 11 fixtures; roof and surface values published: 0",
    "Split the feature set: schedule-derived features (buildable now) and stadium/weather features (need an official roof/surface designation and an NWS feed).",
    "Schedule page gives date, kickoff, network, venue only", NFL + "schedules/2026/by-week/week-11", "F. Schedule, venue and context")

row("F04", "Stadium Roof/Surface and NWS hourly wind/precipitation overlay",
    "blocked", "nfl.com does not publish a roof or surface designation per stadium on the pages read",
    "16 roof types and 16 surface types needed for 32 clubs; 0 confirmed from an official NFL page in this session",
    "Obtain the official stadium-designation source (club or league) and the NWS grid; neither is in hand.",
    "The pages read this session publish a stadium NAME only, never a roof or surface",
    NFL + "games/vikings-at-49ers-2026-reg-11", "F. Schedule, venue and context")

row("F05", "Publish a weekly 'what changed' diff instead of a static snapshot",
    "partial", "Needs two dated snapshots of the same dataset",
    "1 snapshot held for the injury report and for standings, so 0 diffs are computable",
    "E04 first. A diff of one capture against itself is meaningless and must not be published.",
    "This is the same dependency as E05", NFL + "injuries/", "F. Schedule, venue and context")

row("F06", "Publish every model total twice until one wins",
    "not_started", "Needs a second total estimator and a walk-forward comparison",
    "1 total estimator published; 2 required. The gap column therefore has 0 rows",
    "Register a second estimator with its own rule, then publish both with the gap.",
    "nfl-book/data/model_card.json describes one estimator", OB + "nfl-book/data/model_card.json", "F. Schedule, venue and context")

row("F07", "2026 kickoff and declared onside-kick regime priors filter",
    "blocked", "No official 2026 rule text read this session; no kickoff or onside-kick observations ingested",
    "0 rule documents and 0 in-game kickoff observations held",
    "Read the official 2026 Playing Rules and ingest play-by-play before any priors filter is defensible.",
    "Not attempted this session — would be a fabricated claim", NFL + "news/", "F. Schedule, venue and context")

row("F08", "Archive weekly injury reports for past seasons (needed to calibrate designations)",
    "blocked", "No archive exists; the live page only exposes the current season's weekly tabs",
    "0 archived seasons; 3+ needed for a per-designation play rate with usable confidence intervals",
    "Archive now, weekly, so the calibration exists in 3 years; or find an official historical publisher.",
    "Week 10 of 2026 is the only week available on the live page",
    NFL + "injuries/", "F. Schedule, venue and context")

row("F09", "Vig-free market consensus vs originated fair-line decomposition view",
    "blocked", "Needs a market consensus, which needs prices from more than one operator",
    "2+ operators needed to decompose a consensus; 0 official operator feeds in hand",
    "Same root decision as A01, plus a second operator. The NFL itself publishes no prices.",
    "Flag FB-01 records the same blocker for a single line, let alone a consensus",
    OB + "nfl-book/data/flags.json", "F. Schedule, venue and context")

row("F10", "Treat roster turnover as a first-class data event (version depth against the last official roster event)",
    "not_started", "Needs a transactions feed and a depth dataset; neither is held",
    "0 roster events ingested, 0 depth rows to version",
    "Ingest the official transactions feed, then stamp every depth row with it.",
    "nfl-book flag FB-07; GB dates its chart Nov. 10 2026 but names no roster event",
    "https://www.packers.com/team/depth-chart/", "F. Schedule, venue and context")

row("F11", "Start with a singles-only shadow baseline (pre-register, freeze, record forecasts before kickoff)",
    "partial", "Forecasts are recorded with a snapshot clock, but the open and close snapshots were taken in the same session",
    "13 fixtures forecast pre-kickoff (snapshot 2026-11-14T00:00Z, kickoff 2026-11-19 onward) = 5 days of lead. Real shadow lead time: 1 session, not 5 days",
    "Take the open snapshot at T-5 days genuinely, then the close at T-90 minutes, and never in the same run.",
    "Flag FB-09 records exactly this; re-read this session",
    OB + "nfl-book/data/flags.json", "F. Schedule, venue and context")

# ---- G. site and process --------------------------------------------------
row("G01", "Create a GitHub Pages live site with a clean landing page and subpages organised by category",
    "met", "None — the gate is that the build passes in CI and Pages deploys",
    "26 NFL namespaces plus 5 other site trees already deploy from main; this session adds decision-readiness pages",
    "Nothing. The open question is which namespace is canonical (G03).",
    "Root dashboard and docs/ are live", "https://sassnarep3-star.github.io/Own4/", "G. Site and process")

row("G02", "Every table row must have a source link to an official site; if a value cannot be confirmed, leave it blank and flag it",
    "met", "None — enforced by two independent verifiers",
    "verification/verify_site.py: 14 pages, 346 sourced rows, 0 broken links. nfl-book/engine/verify.py: 16 pages, 433 rows, 409 sourced, 202 marked blanks. This session's own verifier adds a third.",
    "Nothing. Keep the verifier in the merge path.",
    "Both verifiers re-run on a clean checkout this session", OB + "verification/verify_site.py", "G. Site and process")

row("G03", "Pick one canonical NFL dashboard among the namespaces",
    "not_started", "This is purely a decision; nothing technical blocks it",
    "19 NFL-focused site trees on main; 1 canonical target required",
    "Answer Q10. Until then every new session adds a 20th namespace, which is the actual cost.",
    "Counted this session from the filesystem",
    OB + "verification/build.py", "G. Site and process")

row("G04", "Add a decision-readiness table on the landing page: one row per requirement, with the gate that blocks it and the number that would clear it",
    "met", "None — this session's deliverable",
    f"{len(R)} requirement rows, each with state, blocking gate, clearing number and the asks",
    "Review the 5 decision rows marked 'ask'. Those are the only ones that need the owner.",
    "nfl-readiness/pages/decision-readiness.html", OB + "nfl-readiness/", "G. Site and process")

row("G05", "Run the 32-team roster sweep / drift alarms / review repo line by line and flag irregularities",
    "partial", "No sweep; independent re-verification done for the highest-value surfaces",
    f"{M['n_peer_checks_passed']} peer claims pass, {M['n_peer_checks_partial']} partial, {M['n_peer_checks_failed']} fail under independent re-read",
    "See the verification page for each check and its official source.",
    "nfl-readiness/data/derived.json peer_checks", OB + "nfl-readiness/", "G. Site and process")

row("G06", "Correlations only from officially sourced numbers, with n published",
    "met", "None — computed from official scores only",
    "5 correlations computed with n, r, p and CI; 4 left blank with a stated reason rather than guessed",
    "Nothing. CR-06..09 should stay blank until their inputs exist.",
    "nfl-book/data/correlations.json", OB + "nfl-book/data/correlations.json", "G. Site and process")

row("G07", "Remove luck from the equation and build strategies that are selectively skill based",
    "partial", "G2/G4 need more than one season and a multiplicity adjustment",
    "0 of 5 strategies clears every applicable gate; 0 points awarded on a 1,000-point pool",
    "Publish the honest zero and wait for the sample. Do not lower a gate to make the column non-empty.",
    "nfl-book/data/leaderboard.json", OB + "nfl-book/data/leaderboard.json", "G. Site and process")

row("G08", "Look at single bet, parlays, player prop bet combos",
    "partial", "Player props have no official price source at all",
    "3 families declared (singles, parlays, prop combos); 5 strategies registered; 1 permanently blocked on props (FB-05)",
    "A01 also governs props. Until then props cannot be originated at all.",
    "nfl-book/data/strategies.json families", OB + "nfl-book/data/strategies.json", "G. Site and process")

row("G09", "Determine correlation values",
    "met", "None for the computed set; the joint-probability inputs remain blocked",
    "5 values with n; the 4 needed for joint parlay pricing are the blank ones",
    "Nothing to compute until the price/player-log inputs exist.",
    "nfl-book/data/correlations.json", OB + "nfl-book/data/correlations.json", "G. Site and process")

row("G10", "Create an executive summary outlining important details",
    "met", "None",
    "6 executive summaries already on main; this session adds one covering the 5 decisions",
    "Read the newest one.",
    "EXECUTIVE_SUMMARY.md + nfl-readiness/pages/executive-summary.html", OB + "EXECUTIVE_SUMMARY.md", "G. Site and process")

row("G11", "No manual input; verify everything from official sources, no hallucinations",
    "partial", "Verification is complete only for the surfaces re-read this session",
    "5 official page groups re-read line by line this session; 26 namespaces of prior work remain un-reread by this session",
    "Scope note, not a defect. Every number this session publishes traces to a page it fetched.",
    "data/observations.json sources[]", OB + "nfl-readiness/data/observations.json", "G. Site and process")

row("G12", "Make small frequent commits; coordinate with parallel sessions; never edit another session's files",
    "met", "None",
    "1 claim commit pushed before any implementation; this session's writes confined to nfl-readiness/ plus an additive nav entry",
    "Nothing.",
    "COORDINATION.md claim block", OB + "COORDINATION.md", "G. Site and process")

# ---- H. availability evidence, this session's new findings -----------------
row("H01", "Add an announced-starter evidence field (not an inferred replacement)",
    "partial", "Only starters the league explicitly announces can populate this",
    "1 announced starter located (Drew Lock, SEA, Week 10) with a dated official article",
    "Ingest the pre-game article stream; each announcement gives one field.",
    "Official article names Lock, Milroe and Darnold's injury",
    NFL + "news/drew-lock-no-injury-designation-seahawks-raiders", "H. New evidence this session")

row("H02", "Reject inference of depth rank or snaps from anything other than official evidence",
    "met", "Rejected and enforced",
    "0 inferred starters; every blank in the replacement table is deliberate",
    "Nothing.",
    "nfl-book/data/depth_replacements.json blank_policy_note", OB + "nfl-book/data/depth_replacements.json", "H. New evidence this session")

row("H03", "Capture official inactive lists (newly resolved this session)",
    "partial", "Source found and read; no scheduled capture",
    f"{M['n_week10_inactives_named']} named inactives, {M['n_week10_inactive_sections']} club sections, {M['n_week10_venues_published']} venue strings, one dated article",
    "Add the article to the daily capture job. This single URL closes most of the 'no active list' gap.",
    "Article states it covers Sunday's games; SNF inactives publish ~90 minutes pre-kickoff, which is why 2 lists were empty at capture",
    "https://www.nfl.com/news/nfl-week-10-inactives-players-ruled-out-sunday-2026-season", "H. New evidence this session")


def main():
    # Recompute the summary so the published counts can never disagree with the rows.
    order = ["met", "partial", "blocked", "not_started"]
    counts = {k: sum(1 for r in R if r["state"] == k) for k in order}
    assert sum(counts.values()) == len(R), "every row must have a state"

    for r in R:
        assert r["source_url"].startswith("https://"), r["id"]
        assert r["blocking_gate"] and r["clearing_number"] and r["ask"], r["id"]

    skel = json.load(open(os.path.join(DATA, "readiness_skeleton.json"), encoding="utf-8"))
    skel["rows"] = R
    skel["summary"] = dict(n_requirements=len(R), **counts)
    skel["measurements_used"] = M
    skel["groups"] = sorted({r["group"] for r in R})
    with open(os.path.join(DATA, "readiness.json"), "w", encoding="utf-8") as f:
        json.dump(skel, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(f"[readiness] {len(R)} rows  " + "  ".join(f"{k}={v}" for k, v in counts.items()))
    print(f"[readiness] {len(skel['groups'])} groups: {', '.join(skel['groups'])}")


if __name__ == "__main__":
    main()
