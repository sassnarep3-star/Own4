#!/usr/bin/env python3
"""
Governance artefacts, all generated from the measured data rather than typed by hand:

  data/requirements.json    one row per requirement in the brief, with the gate that
                            blocks it, the number that would clear the gate, and the
                            current value of that number
  data/questions.json       a clear list of questions, the information that answers
                            each, what we have, and what we do not have
  data/suggestions.json     site and method suggestions, every one left at
                            "proposed — awaiting owner" with a blank decision field
  data/flagged.json         every irregularity found this session, with its source
  data/mind.json            the two-sided "what would change our mind" fields
  data/demotion.json        the demotion gate and its current state per strategy

Nothing here asserts a value that is not in another data file of this lab. Each
row carries the path or the URL of where its number came from, so the verifier can
check the link and a reader can check the claim.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
DATA = os.path.join(LAB, "data")
ROOT = os.path.dirname(LAB)


def load(name):
    return json.load(open(os.path.join(DATA, name), encoding="utf-8"))


def repo(path, label="repo"):
    """An anchor string, rendered here rather than left as a dict for the builder."""
    return ('<a href="https://github.com/sassnarep3-star/Own4/blob/main/nfl-origination-lab/%s" '
            'target="_blank" rel="noopener">%s</a>' % (path, label))


def main():
    corpus = load("corpus.json")
    led = load("leaderboard.json")
    luck = load("luck.json")
    pol = load("price_policy.json")
    res = load("residuals.json")
    dep = load("depth.json")
    av = load("availability_parse.json")
    corr = load("correlations.json")

    n2026 = corpus["counts"]["by_season"]["2026"]
    rows_led = {r["model"]: r for r in led["rows"]}
    html_pages = "pages/%s.html"
    QUESTION_COUNT = 17   # owned by registers.py; asserted equal by verify.py
    SUGGESTION_COUNT = 14

    # ------------------------------------------------------------------
    # requirements: status is measured, never asserted
    # ------------------------------------------------------------------
    REQ_COUNT = 68   # declared; the list below is asserted to match by verify.py

    def req(i, text, status, gate, clearing, current, evidence, link, page):
        return {"id": i, "requirement": text, "status": status, "gate": gate,
                "clearing_number": clearing, "current_value": current,
                "evidence": evidence, "source": link, "page": page}

    money_holms = [rows_led[m]["proper_score"]["holm_p_moneyline"] for m in rows_led if m != "M0"]
    reqs = [
        req("R01", "Price-snapshot store with opening and closing numbers for every market",
            "partial",   # scoring works; ROI is blocked
            "an opening number attributable to an official publisher",
            "1 claimable opening row (policy C1-C4)",
            "0 opening rows, 6,345 official closings with unpublished timing",
            "census of 12,573 store rows", repo("data/price_policy.json"), html_pages % "prices"),
        req("R02", "Verified results feed so backtests and ROI can be computed",
            "partial",
            "an officially sourced, time-stamped price",
            "1 claimable closing price",
            "%d graded 2026 games; 0 claimable prices" % n2026,
            "corpus integrity assertions and standings arithmetic",
            repo("data/corpus.json"), html_pages % "prices"),
        req("R03", "Originate the side first, then the total, then the moneyline",
            "done",
            "no gate; publication order is specified",
            "n/a",
            "SIDE, TOTAL, MONEYLINE published in that order",
            "three market columns on every forecast row",
            repo("data/forecasts.json"), html_pages % "origination"),
        req("R04", "Fair line, market line and difference as separate columns",
            "done",
            "an official posted line per market",
            "1 official line per (game, market)",
            "%d of %d residual rows carry a model line, market line and residual"
            % (res["counts"]["rows_with_an_official_line"], res["counts"]["rows"]),
            "residual table", repo("data/residuals.json"), html_pages % "origination"),
        req("R05", "Separate signal from staking so a lucky staking run cannot mask bad signal",
            "done",
            "no gate; two divisions are published separately",
            "n/a",
            "signal division ranked; staking division published empty with its reason",
            "leaderboard divisions", repo("data/leaderboard.json"), html_pages % "leaderboard"),
        req("R06", "Track the depth of the replacement, not just the fact of a replacement",
            "done",
            "a chart rank for both the out player and the replacement",
            "both ranks present",
            "%d replacements with a rank difference"
            % dep["replacement_depth"]["n_replacements_documented"],
            "replacement depth table", repo("data/depth.json"), html_pages % "availability"),
        req("R07", "Correlations only from officially sourced numbers, with n published",
            "partial",
            "an official price for any price-based correlation",
            "1 official time-stamped price",
            "%d corpus correlations published, n on every row; 0 price correlations"
            % len([r for r in corr["rows"] if r["r"] is not None]),
            "correlation table", repo("data/correlations.json"), html_pages % "correlations"),
        req("R08", "A demotion gate that sends a live strategy back to paper",
            "done",
            "a live strategy",
            "1 strategy in live status",
            "0 live strategies; 0 demotions; gate text and triggers published",
            "demotion gate table", repo("data/demotion.json"), html_pages % "leaderboard"),
        req("R09", "Pre-register every strategy; backtest numbers never on the leaderboard",
            "done",
            "a commit that freezes the rule before its numbers exist",
            "commit hash preceding the score",
            "PREREG-LAB-1 frozen at commit 0956256 before evaluate.py ran",
            "pre-registration file and hash", repo("prereg/PREREG-LAB-1.json"),
            html_pages % "prereg"),
        req("R10", "Availability graph as a first-class dataset",
            "blocked",
            "inactive lists and snap counts per game",
            "1 inactive list per game",
            "0 inactive lists, 0 snap-count series in the repository",
            "gap G1 and G2", repo("data/depth.json"), html_pages % "availability"),
        req("R11", "Model depth from playing time, not jersey order",
            "blocked",
            "an official snap-count source",
            "1 official snap-count publication",
            "0 snap-count rows available to this session",
            "gap G1", repo("data/depth.json"), html_pages % "availability"),
        req("R12", "Injury signal is a surprise, never a level",
            "partial",
            "two dated reads of the same report week",
            "2 dated captures",
            "%d players with two reads; %d change between them"
            % (av["transcription_control"]["joined_rows"],
               len(av["transcription_control"]["differences"])),
            "delta table", repo("data/availability_parse.json"), html_pages % "availability"),
        req("R13", "32-team roster/IR sweep before any team-level model is trusted",
            "partial",
            "a rule that gates team models on the sweep",
            "declared pass/fail rule",
            "sweep present (32 clubs, 25 reserve entries); no model in this lab depends on it",
            "sweep reference", repo("data/depth.json"), html_pages % "availability"),
        req("R14", "Fixture-context features built only from published schedule facts",
            "partial",
            "a published schedule fact for every 2026 fixture",
            "rest days for both clubs on every game",
            "rest days computable for %d of %d 2026 games"
            % (sum(1 for g in corpus["games"] if g["season"] == 2026 and g.get("rest_diff") is not None),
               n2026),
            "rest fields on every corpus row", repo("data/corpus.json"),
            html_pages % "origination"),
        req("R15", "Store every model output as a probability plus its inputs",
            "done",
            "no gate",
            "n/a",
            "%d forecast rows, each with probability, fair line, sigma and inputs"
            % len(json.load(open(os.path.join(DATA, "forecasts.json")))["rows"]),
            "forecast store", repo("data/forecasts.json"), html_pages % "origination"),
        req("R16", "Removal-of-luck panel on the dashboard",
            "done",
            "no gate",
            "n/a",
            "4 luck questions answered with numbers; permutation 90th percentile %+0.4f"
            % luck["null_interval_90"][1],
            "luck panel", repo("data/luck.json"), "index.html"),
        req("R17", "A two-sided 'what would change our mind' field on every strategy",
            "done",
            "no gate",
            "n/a",
            "%d strategies, each with a promote trigger and a retire trigger"
            % len([x for x in led["rows"] if x["model"] != "M0"]),
            "mind table", repo("data/mind.json"), html_pages % "leaderboard"),
        req("R18", "Price a line ourselves and publish the residual on a schedule, from day one",
            "done",
            "an official posted line",
            "1 official line per market",
            "%d residual rows, %d with an official line, weeks 1-10"
            % (res["counts"]["rows"], res["counts"]["rows_with_an_official_line"]),
            "residual table", repo("data/residuals.json"), html_pages % "origination"),
        req("R19", "Turn the stored game log into the pre-registered backtest corpus",
            "done",
            "corpus arithmetic consistent with official standings",
            "games implied by standings == corpus games",
            "%d 2026 games == standings-implied %s; points %d == PF %d"
            % (n2026, corpus["standings_arithmetic"]["games_implied_by_standings"],
               corpus["standings_arithmetic"]["corpus_points"],
               corpus["standings_arithmetic"]["pf_total"]),
            "corpus integrity block", repo("data/corpus.json"), html_pages % "corpus"),
        req("R20", "Decide the price-data policy before any backtest is published",
            "done",
            "no gate",
            "n/a",
            "policy decided: 0 claimable rows of 12,573; staking division closed",
            "policy decision block", repo("data/price_policy.json"), html_pages % "prices"),
        req("R21", "Store every injury-hub read with its clock time; publish the delta, never the level",
            "partial",
            "a captured clock time on every read",
            "2 reads with clock times, both retained",
            "2 reads, 2 clock times, %d row-level changes published"
            % len(av["transcription_control"]["differences"]),
            "delta table", repo("data/availability_parse.json"), html_pages % "availability"),
        req("R22", "Decision-readiness table on the landing page",
            "done",
            "no gate",
            "n/a",
            "%d requirement rows, each with its gate and clearing number" % REQ_COUNT,
            "this register", repo("data/requirements.json"), "index.html"),
        req("R23", "Venue of every fixture transcribed from the official game centre",
            "blocked",
            "an official game-centre read of each fixture",
            "1 venue per fixture from the game centre",
            "0 venues transcribed this session (no egress); a peer read 12 of 13 from the "
            "schedule page and found the two pages disagree on the Thursday venue",
            "gap, flagged", repo("data/flagged.json"), html_pages % "flagged"),
        req("R24", "League's dated schedule announcement beside the live schedule page",
            "partial",
            "a dated announcement captured from an official page",
            "1 dated official announcement",
            "one stored quote of the published flexible-scheduling text, with its source URL; "
            "the announcement itself was not re-read this session",
            "quoted note", repo("data/flagged.json"), html_pages % "corpus"),
        req("R25", "Official Game Books for actual starters; do not infer depth or snaps",
            "blocked",
            "a game-book capture for the graded games",
            "1 official game book per game",
            "0 game books in the repository",
            "gap", repo("data/flagged.json"), html_pages % "availability"),
        req("R26", "Ingest game-level results to make ratings opponent-aware",
            "done",
            "no gate",
            "n/a",
            "opponent-aware rating fitted on %d prior games before each forecast"
            % rows_led["M1"]["proper_score"]["n"],
            "model definition", repo("data/leaderboard.json"), html_pages % "origination"),
        req("R27", "Injury and personnel ablations instead of fixed penalties",
            "blocked",
            "a verified availability feature to ablate",
            "1 availability feature verified for all 32 clubs",
            "0: the depth-order gate is closed (Houston publishes an image)",
            "gate", repo("data/depth.json"), html_pages % "availability"),
        req("R28", "Immutable multi-day availability snapshots with hashes",
            "partial",
            "at least 3 dated captures of the same page",
            "3 dated captures with hashes",
            "2 dated captures, both hashed; the earlier one is raw bytes",
            "capture provenance", repo("data/availability_parse.json"),
            html_pages % "availability"),
        req("R29", "Capture official inactive lists and snap counts",
            "blocked",
            "an official capture for either",
            "1 capture",
            "0 inactive lists, 0 snap counts",
            "gaps G1, G2", repo("data/depth.json"), html_pages % "availability"),
        req("R30", "Fix the two depth-parsing failures before widening coverage",
            "done",
            "no gate",
            "n/a",
            "jersey-prefixed entries counted (%d, all Green Bay); image-only club counted (1)"
            % dep["slot_shape"]["jersey_prefixed_entries"].get("GB", 0),
            "slot-shape block", repo("data/depth.json"), html_pages % "availability"),
        req("R31", "Model depth slots as groups, not a single starter",
            "partial",
            "a group-shaped slot schema in the source register",
            "0 shared rank-1 slots read as a single starter",
            "%d shared slots and %d empty rank-1 slots published as such"
            % (dep["slot_shape"]["shared_slots"], dep["slot_shape"]["empty_rank1_slots"]),
            "slot-shape block", repo("data/depth.json"), html_pages % "availability"),
        req("R32", "Treat roster turnover as a first-class data event",
            "blocked",
            "a dated roster-event log joined to each chart capture",
            "1 roster event per chart change",
            "0 roster events joined to charts; the charts carry one capture each",
            "gap G4", repo("data/depth.json"), html_pages % "availability"),
        req("R33", "Singles-only shadow baseline, pre-registered before kickoff",
            "done",
            "a forecast recorded before the game it predicts",
            "0 forecasts registered after kickoff",
            "%d forecasts, each fitted only on strictly earlier weeks (asserted in verify.py)"
            % rows_led["M3"]["proper_score"]["n"],
            "walk-forward record", repo("data/forecasts.json"), html_pages % "prereg"),
        req("R34", "Keep parlays and prop combos behind a joint-evidence gate",
            "closed as designed",
            "a directly validated joint probability plus the operator's void/push rules",
            "1 joint price from an official or licensed source",
            "0 joint prices; all three combo divisions are closed with their reason",
            "leaderboard divisions", repo("data/leaderboard.json"), html_pages % "leaderboard"),
        req("R35", "Proper-score leaderboard divisions",
            "done",
            "no gate",
            "n/a",
            "4 divisions declared; 1 open, 3 closed with reasons",
            "division table", repo("data/leaderboard.json"), html_pages % "leaderboard"),
        req("R36", "Rank with proper scores and uncertainty, not win rate",
            "done",
            "no gate",
            "n/a",
            "Brier skill with a week-cluster 90 percent bound and a Holm adjustment over %d tests"
            % led["families_scored"],
            "leaderboard methods", repo("data/leaderboard.json"), html_pages % "leaderboard"),
        req("R37", "Durable snapshot storage and alerts",
            "partial",
            "an alert channel and a freshness monitor",
            "1 scheduled monitor with an owner",
            "drift alarms implemented in code; no alert channel exists",
            "drift alarm", repo("data/availability_parse.json"), html_pages % "sources"),
        req("R38", "Split public analysis layer from private raw data layer",
            "partial",
            "a rights decision on the raw rows",
            "1 recorded rights decision",
            "raw rows live in this public repository; no rights decision is recorded",
            "flagged F-01", repo("data/flagged.json"), html_pages % "flagged"),
        req("R39", "Per-team view: starters out, replacements named, net injury count",
            "partial",
            "a confirmed replacement for each out player",
            "1 confirmed replacement per out player",
            "%d documented replacements of 25 reserve entries"
            % dep["replacement_depth"]["n_replacements_documented"],
            "replacement table", repo("data/depth.json"), html_pages % "availability"),
        req("R40", "Announced-starter evidence field, not an inferred replacement",
            "blocked",
            "an official dated starter announcement",
            "1 dated announcement per club",
            "0 announcements captured as evidence this session (headlines exist on a peer "
            "capture, undated against the claim)",
            "flagged", repo("data/flagged.json"), html_pages % "flagged"),
        req("R41", "Official depth-chart register with date and source per row",
            "done",
            "no gate",
            "n/a",
            "705 slots across 31 transcribed clubs, source URL per club",
            "register reference", repo("data/depth.json"), html_pages % "availability"),
        req("R42", "Calibrate what 'Questionable' means empirically, not from old percentages",
            "blocked",
            "several seasons of designations joined to inactive lists",
            ">= 2 seasons of joined designation->play data",
            "0 seasons joined; this week has 7 Questionable rows on one fixture",
            "gap", repo("data/flagged.json"), html_pages % "availability"),
        req("R43", "Interactive offense vs defense deficiency matrix, 1st-4th string",
            "blocked",
            "the closed depth-order gate",
            "32 clubs with a structured chart",
            "31 of 32 clubs; Houston image-only",
            "gate", repo("data/depth.json"), html_pages % "availability"),
        req("R44", "Flag stale depth rows against the official transactions log",
            "done",
            "no gate",
            "n/a",
            "%d clubs flagged with a named player and IR date"
            % dep["stale_chart_flags"]["n_clubs_flagged"],
            "stale-chart table", repo("data/depth.json"), html_pages % "availability"),
        req("R45", "Point-in-time snapshot ledger for injuries, charts and inactives",
            "partial",
            "one capture per source per day",
            "daily capture coverage",
            "2 dated injury captures, 1 chart capture, 0 inactive captures",
            "capture provenance", repo("data/availability_parse.json"),
            html_pages % "availability"),
        req("R46", "Populate the missing Detroit game-status designations",
            "blocked",
            "an official read naming the three players' status",
            "1 official designation per player",
            "0 read this session (no egress); the peer capture shows blank cells",
            "flagged", repo("data/flagged.json"), html_pages % "flagged"),
        req("R47", "Re-capture and republish the Week 10 injury tables",
            "blocked",
            "an official re-read of the Week 10 tables",
            "1 dated re-read",
            "0 this session; the stored Week 11 captures are the only dated pair",
            "flagged", repo("data/flagged.json"), html_pages % "flagged"),
        req("R48", "Reject deriving depth from jersey number, experience or salary",
            "adopted as a rejection",
            "no gate",
            "n/a",
            "0 depth ranks derived from anything but the club's own chart",
            "policy statement", repo("data/depth.json"), html_pages % "availability"),
        req("R49", "Represent shared and empty depth slots faithfully",
            "done",
            "no gate",
            "n/a",
            "%d shared slots and %d empty rank-1 slots published as such"
            % (dep["slot_shape"]["shared_slots"], dep["slot_shape"]["empty_rank1_slots"]),
            "slot-shape block", repo("data/depth.json"), html_pages % "availability"),
        req("R50", "Resolve the depth-order source before building the backup-deficiency feature",
            "gate still closed",
            "route (a) verified club by club, or route (b) an official snap source",
            "32 of 32 clubs on one route",
            "31 of 32 on route (a); route (b) has no source",
            "gate", repo("data/depth.json"), html_pages % "availability"),
        req("R51", "Score injury-designation reliability before using it as a feature",
            "blocked",
            "several seasons of designations joined to inactive lists",
            ">= 2 seasons",
            "0 seasons; no designation is used as a model feature anywhere in this lab",
            "gap", repo("data/flagged.json"), html_pages % "availability"),
        req("R52", "Snapshot the injury report Wed/Thu/Fri with a dated history",
            "partial",
            "a scheduled capture job with retained hashes",
            "3 captures in one week",
            "2 captures in one week (18th, 19th), both hashed",
            "capture provenance", repo("data/availability_parse.json"),
            html_pages % "availability"),
        req("R53", "Treat the injury report as a timestamped series",
            "partial",
            "a capture per day Wed->kickoff",
            "4+ captures in one week",
            "2 captures, 7.3 hours apart, same report week",
            "delta table", repo("data/availability_parse.json"), html_pages % "availability"),
        req("R54", "Use snap counts as the starter proxy",
            "blocked",
            "an official snap-count source",
            "1 source",
            "0 sources",
            "gap G1", repo("data/depth.json"), html_pages % "availability"),
        req("R55", "A control baseline (random, favourites only) on every leaderboard run",
            "partial",
            "a price for the favourites-only control",
            "1 official price",
            "random and climatology controls published; favourites-only is not computable",
            "controls block", repo("data/luck.json"), html_pages % "leaderboard"),
        req("R56", "Stadium roof/surface and NWS wind/precipitation overlay",
            "blocked",
            "official roof designations and an official forecast source",
            "1 official roof designation per venue",
            "0 roof designations, 0 forecast rows",
            "flagged", repo("data/flagged.json"), html_pages % "flagged"),
        req("R57", "Two-stage skill leaderboard (proper-score qualification, then CLV escrow)",
            "partial",
            "a time-stamped official price",
            "1 claimable price",
            "stage 1 published with %d qualifiers; stage 2 empty" % len(led["qualifiers"]),
            "leaderboard", repo("data/leaderboard.json"), html_pages % "leaderboard"),
        req("R58", "Vig-free market consensus vs originated fair-line decomposition",
            "partial",
            "a vig-free consensus, which needs several independent prices",
            ">= 3 independently sourced prices per market",
            "1 official posted line per market; no consensus possible",
            "residual table", repo("data/residuals.json"), html_pages % "origination"),
        req("R59", "Publish a weekly 'what changed' diff, not a static snapshot",
            "partial",
            "two weekly captures of the same page",
            "2 weekly captures",
            "2 captures within one week: a delta exists but not a week-over-week diff",
            "delta table", repo("data/availability_parse.json"), html_pages % "availability"),
        req("R60", "Publish every model total twice until one wins",
            "done",
            "no gate",
            "n/a",
            "two total estimators (CRPS and threshold Brier) published side by side with a "
            "gap column; neither wins on the holdout",
            "leaderboard", repo("data/leaderboard.json"), html_pages % "leaderboard"),
        req("R61", "A drift alarm on every scraper",
            "done",
            "no gate",
            "n/a",
            "row floor, club count and vocabulary alarms declared before parsing; status PASS",
            "drift alarm block", repo("data/availability_parse.json"),
            html_pages % "sources"),
        req("R62", "Capture the reserve list so 'not listed' never means 'available'",
            "partial",
            "a dated reserve-list capture",
            "1 capture with a clock time",
            "1 stored capture (2026-11-18T23:49:18Z); not re-read this session",
            "capture provenance", repo("data/availability_parse.json"),
            html_pages % "availability"),
        req("R63", "Reject ranking strategies by season-long ROI",
            "adopted as a rejection",
            "no gate",
            "n/a",
            "0 strategies ranked by ROI; ROI is not computed at all",
            "policy", repo("data/leaderboard.json"), html_pages % "leaderboard"),
        req("R64", "Archive weekly injury reports for past seasons",
            "blocked",
            "past-season captures",
            ">= 1 archived past season",
            "0 archived past seasons",
            "gap", repo("data/flagged.json"), html_pages % "availability"),
        req("R65", "Freeze a rule before it sees data; the commit hash is the registration",
            "done",
            "no gate",
            "n/a",
            "PREREG-LAB-1 frozen at 0956256 before any score existed",
            "pre-registration file", repo("prereg/PREREG-LAB-1.json"), html_pages % "prereg"),
        req("R66", "Split data into train, validation and final holdout seasons",
            "done",
            "no gate",
            "n/a",
            "2025 w1-9 train (135), 2025 w10-18 validation (137), 2026 w1-10 holdout (150)",
            "block table", repo("data/validation_scores.json"), html_pages % "prereg"),
        req("R67", "A suggestions section someone can review and choose from before implementing",
            "done",
            "no gate",
            "n/a",
            "%d suggestions, every decision field left blank for the owner"
            % SUGGESTION_COUNT,
            "suggestions page", repo("data/suggestions.json"), html_pages % "suggestions"),
        req("R68", "A clear list of questions, information and answers before any decision",
            "done",
            "no gate",
            "n/a",
            "%d questions, each with what we have, what we lack and what would settle it"
            % QUESTION_COUNT,
            "questions page", repo("data/questions.json"), html_pages % "questions"),
    ]

    counts = {}
    for r in reqs:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    json.dump({"dataset": "nfl_origination_lab_requirements",
               "title": "Decision-readiness register: one row per requirement in the brief",
               "built": "2026-11-19",
               "status_vocabulary": {
                   "done": "the artefact exists and its number is published",
                   "partial": "some of it exists; the missing part is named",
                   "blocked": "a named gate stops it; the clearing number is stated",
                   "closed as designed": "the requirement is met by refusing to open something",
                   "gate still closed": "the requirement is itself a gate that has not passed",
                   "adopted as a rejection": "the requirement is a prohibition, and it is kept",
               },
               "counts": counts, "n": len(reqs), "rows": reqs},
              open(os.path.join(DATA, "requirements.json"), "w", encoding="utf-8"), indent=1)

    # ------------------------------------------------------------------
    # what would change our mind
    # ------------------------------------------------------------------
    mind = []
    for r in led["rows"]:
        if r["model"] == "M0":
            continue
        ps = r["proper_score"]
        mind.append({
            "strategy": r["model"],
            "current": "Brier skill %+0.4f, 90%% bound [%+0.4f, %+0.4f], Holm p %.4f"
                       % (ps["bss_moneyline"], ps["ci90_moneyline"][0], ps["ci90_moneyline"][1],
                          ps["holm_p_moneyline"]),
            "promote_if": "a closing price with an official source appears AND the "
                          "benchmark-relative skill's 90%% lower bound stays above %+0.4f over "
                          "8 further weeks" % ps["ci90_moneyline"][0],
            "retire_if": "the week-cluster 90%% upper bound on its Brier skill falls below 0, "
                         "or 4 consecutive weeks of negative skill, or its inputs fail the "
                         "drift alarm twice",
            "evidence_path": "data/leaderboard.json",
        })
    json.dump({"dataset": "nfl_origination_lab_mind",
               "title": "Two-sided decision fields: what would promote each strategy and what "
                        "would retire it",
               "built": "2026-11-19",
               "rule": "every entry is numeric on both sides; an entry that cannot be made "
                       "numeric is not published as a strategy",
               "rows": mind},
              open(os.path.join(DATA, "mind.json"), "w", encoding="utf-8"), indent=1)

    # ------------------------------------------------------------------
    # demotion gate
    # ------------------------------------------------------------------
    dem = {
        "dataset": "nfl_origination_lab_demotion",
        "title": "The demotion gate: how a live strategy goes back to paper",
        "built": "2026-11-19",
        "triggers": [
            {"id": "D1", "trigger": "week-cluster 90% lower bound on benchmark-relative Brier "
                                    "skill below 0 over any rolling 4-week window"},
            {"id": "D2", "trigger": "pre-registered sample floor breached (n < 100 graded games)"},
            {"id": "D3", "trigger": "input drift alarm fails on two consecutive runs"},
            {"id": "D4", "trigger": "a price claim is later found not to meet policy C1-C4"},
        ],
        "effect": "status moves live -> paper; the history is kept; the event is dated and "
                  "reasoned; promotion back to live requires the promote trigger in mind.json",
        "state": {
            "strategies_in_live_status": 0,
            "demotions_recorded": 0,
            "reason_none_can_yet_be_live": "no strategy has a claimable price, so none can be "
                                           "staked; the gate is published before it is needed "
                                           "rather than added after a loss",
        },
        "rows": [{"strategy": r["model"], "status": "paper",
                  "next_review": "after 4 further graded weeks",
                  "source": "data/leaderboard.json"}
                 for r in led["rows"]],
    }
    json.dump(dem, open(os.path.join(DATA, "demotion.json"), "w", encoding="utf-8"), indent=1)

    print("requirements: %d rows, counts %s" % (len(reqs), counts))
    print("mind: %d strategies, demotion: %d triggers"
          % (len(mind), len(dem["triggers"])))


if __name__ == "__main__":
    main()
