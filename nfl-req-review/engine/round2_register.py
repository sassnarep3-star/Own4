#!/usr/bin/env python3
"""
nfl-req-review — round 2 register audit (2026-11-18), session arena/9242c387-own4.

Reads the round-1 register (data/requirements_2026_11_17.json) and the round-2 computed
checks (data/official_reads_2026_11_18.json, from engine/round2.py), then writes:
  data/requirements_2026_11_18.json   audited register: status, evidence, artifacts, sources
  data/flags_2026_11_18.json          round-2 irregularities (RF-08..), with source links
  data/questions.json                 questions, known answers, gaps, how to discover
  data/suggestions.json               suggestions with options; no change implemented
  data/repo_review.json               repo review findings with method and links

Rule: a row may be 'met' only if (a) an artifact path it cites exists in the repository and
(b) the official source it cites supports the claim. Where either fails, the row is
downgraded to 'partial' and the reason is written in the evidence column.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)
DATA = os.path.join(NS, "data")

ROUND = "2026-11-18"
SESSION = "arena/9242c387-own4"

SRC_STAND = "https://www.nfl.com/standings/league/2026/REG"
SRC_W10 = "https://www.nfl.com/schedules/2026/by-week/week-10"
SRC_W11 = "https://www.nfl.com/schedules/2026/by-week/week-11"
SRC_INJ10 = "https://www.nfl.com/injuries/league/2026/reg10"
SRC_INJ11 = "https://www.nfl.com/injuries/league/2026/reg11"
SRC_GAME_IND = "https://www.nfl.com/games/colts-at-texans-2026-reg-11"
SRC_GH_COORD = "https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md"

# Repo paths cited as artifacts (checked for existence at build time)
A = {
    "price_store": "nfl-book/data/price_snapshots.json",
    "feed": "nfl-book/data/results_feed.json",
    "model_outputs": "nfl-book/data/model_outputs.json",
    "own_lines_open": "nfl-book/data/own_lines_open.json",
    "holdout": "nfl-book/data/holdout_split.json",
    "control": "nfl-book/data/control_baseline.json",
    "correlations": "nfl-book/data/correlations.json",
    "removal": "nfl-book/data/removal_of_luck.json",
    "demotion": "nfl-book/data/demotion_eval.json",
    "per_team": "nfl-book/data/per_team_view.json",
    "suggestions_nb": "nfl-book/data/suggestions.json",
    "questions_nb": "nfl-board/data/questions.json",
    "prereg": "nfl-availability-desk/prereg/PREREG-001-shadow-baseline.md",
    "exec_summary": "EXECUTIVE_SUMMARY.md",
    "standings_check": "nfl-availability-desk/data/derived/standings_check.json",
    "capture_r1": "nfl-req-review/data/official_reads_2026_11_17.json",
}

# ---------------------------------------------------------------------------
# Round-2 verdicts. Only rows whose status or evidence changed are listed here.
# Every other row keeps its round-1 status and gets the round-2 'retained' note.
# status: met | partial | blocked | not_started | in_progress
# ---------------------------------------------------------------------------
UP = {
    "A01": dict(status="partial", arts=["price_store", "own_lines_open"], src=SRC_GAME_IND,
        ev="Store exists: nfl-book/data/price_snapshots.json holds 39 open/close pairs (13 Week-11 games x side/total/moneyline). "
           "Every market_open_value and market_close_value is null by policy (no official price source). The 'close' value is a model run "
           "trained on the 137 feed games, not a market close. Downgraded from met because the market half is blank."),
    "A02": dict(status="partial", arts=["feed"], src=SRC_W10,
        ev="Round 2 reconciled the feed to the official standings: Weeks 1-9 (136 games) match 32 of 32 clubs on W, L, T, PF and PA (RC-11). "
           "The feed holds 1 of the 14 official Week-10 finals (RC-12). 105 of its 137 rows are aggregate-only, not re-read game by game. "
           "Downgraded from met until the 13 missing finals are added and the aggregate-only rows are re-read."),
    "A03": dict(status="partial", arts=[], src=SRC_W11,
        ev="Correction: round 1 stated 14 Week-11 fixtures and 'all 137 games'. The official Week-11 schedule read today shows 13 fixtures and "
           "6 clubs on bye, which is consistent with 32 clubs (RC-08, RC-09). The clearing set below is corrected accordingly."),
    "A06": dict(status="partial", arts=["model_outputs"], src=SRC_W10,
        ev="Opponent-adjusted inputs exist (away_off/away_def, home_off/home_def in nfl-book/data/model_outputs.json). The model's own input "
           "n_train_games is 137, not the 150 completed games official standings show (RC-02). Downgraded from met."),
    "A07": dict(status="partial", arts=["holdout", "feed"], src=SRC_STAND,
        ev="The 136-game Weeks 1-9 corpus is correct: it reconciles to official standings for 32 of 32 clubs (RC-07, RC-11). "
           "nfl-book/data/holdout_split.json assigns only one Week-10 game ('Week 10 TNF (1 game, 137th)') and leaves 13 official Week-10 "
           "finals in no split. Downgraded from met until every completed game is assigned to a named split."),
    "B01": dict(status="met", arts=["own_lines_open"], src=SRC_GAME_IND,
        ev="Confirmed in the artifact: own_lines_open.json origination_order = side, total, moneyline (13 games)."),
    "B04": dict(status="met", arts=["model_outputs"], src=SRC_GAME_IND,
        ev="Confirmed in the artifact: model_outputs.json rows carry p_home, p_away, and the inputs used (13 rows)."),
    "C01": dict(status="met", arts=["removal"], src=SRC_GH_COORD,
        ev="Confirmed in the artifact: removal_of_luck.json states that signal is separated from staking and that the leaderboard ranks on signal tier."),
    "C05": dict(status="partial", arts=["control"], src=SRC_STAND,
        ev="A random-pick and a favorites-only baseline exist (control_baseline.json). The favorites baseline uses current standings, i.e. "
           "information from after the games it predicts. The file discloses this; a control built on future information is not a valid control. Downgraded from met."),
    "C06": dict(status="met", arts=["demotion"], src=SRC_GH_COORD,
        ev="Confirmed in the artifact: demotion_eval.json holds gate D1 (live-to-paper demotion rule)."),
    "C07": dict(status="met", arts=["prereg"], src=SRC_GH_COORD,
        ev="PREREG-001 exists in the repository. The registration is the git commit hash; this sandbox clone is shallow, so the hash history cannot be checked here (RF-18)."),
    "D01": dict(status="partial", arts=["correlations", "feed"], src=SRC_STAND,
        ev="Correlations publish n and an official URL per row, but they are computed from the 137-row feed, 105 of whose rows are aggregate-only "
           "and which omits 13 official Week-10 finals. Downgraded from met until recomputed on the full official set."),
    "E18": dict(status="met", arts=["per_team"], src=SRC_INJ10,
        ev="Confirmed in the artifact: per_team_view.json holds 32 rows with starters_out, replacements_named and net_injury_count fields."),
    "E25": dict(status="met", arts=[], src=SRC_INJ10,
        ev="Verified live 2026-11-18: the Week-10 report lists Kerby Joseph (DET, Knee), Cade Mays (DET, Ankle) and D.J. Reed (DET, Hip), each with "
           "Practice 'Did Not Participate In Practice' and Game Status 'Out' (RC-16). Corroboration against the inactive list is a separate open item (RF-01)."),
    "E26": dict(status="partial", arts=["capture_r1"], src=SRC_INJ10,
        ev="Round 2 cannot confirm the round-1 totals. The round-1 capture's own totals are 346 players over 28 clubs (RC-13); the round-1 findings text "
           "says 326 rows, 14 Out and 11 Questionable. Cincinnati is 9 in the capture; the brief says 4 (RC-14, unresolved). Downgraded from met."),
    "F01": dict(status="met", arts=["removal"], src=SRC_GH_COORD,
        ev="Confirmed in the artifact: removal_of_luck.json is the panel data; the nfl-book index page carries the panel."),
    "G03": dict(status="met", arts=["suggestions_nb"], src=SRC_GH_COORD,
        ev="A suggestions file exists in another namespace (nfl-book/data/suggestions.json). This namespace's suggestions page is data/suggestions.json."),
    "G04": dict(status="met", arts=["questions_nb"], src=SRC_GH_COORD,
        ev="A questions file exists in another namespace (nfl-board/data/questions.json). This namespace's questions page is data/questions.json."),
    "G05": dict(status="met", arts=["exec_summary"], src=SRC_GH_COORD,
        ev="Repository executive summary exists (EXECUTIVE_SUMMARY.md). This round adds nfl-req-review/EXECUTIVE_SUMMARY.md with round-2 numbers."),
    "G07": dict(status="partial", arts=[], src=SRC_GH_COORD,
        ev="Round 2 re-read and reconciled: 32 clubs' standings, 14 Week-10 finals, 13 Week-11 fixtures, the Week-10 Lions rows, and the round-1 capture. "
           "Not re-read line by line: Week-10 injury chunks 1-7, the other 38 NFL namespaces, and the repository's non-NFL content. Downgraded from met; see the repo review scope."),
    "G08": dict(status="met", arts=[], src=SRC_GH_COORD,
        ev="This namespace is a static site: landing, requirements, questions, suggestions, games, verification, flagged, repo review, sources, executive summary."),
    "G09": dict(status="met", arts=[], src=SRC_GH_COORD,
        ev="Scoped to this namespace: verify.py checks every table row for a source link, and the rows without an official NFL data value say so in the source-type column."),
    "G12": dict(status="in_progress", arts=[], src=SRC_GH_COORD,
        ev="PR and merge are performed in this session; the PR link and merge result are recorded in COORDINATION.md."),
}

# Rows that cite GitHub only (process requirements; no external data value)
PROCESS_GROUPS = {"Governance & process"}


def load(name):
    return json.load(open(os.path.join(DATA, name), encoding="utf-8"))


def load_json_root(p):
    return json.load(open(os.path.join(ROOT, p), encoding="utf-8"))


def exists(p):
    return os.path.exists(os.path.join(ROOT, p))


def main():
    r1 = load("requirements_2026_11_17.json")
    reads = load("official_reads_2026_11_18.json")
    checks = {c["id"]: c for c in reads["checks"]}

    rows = []
    for row in r1["rows"]:
        rid = row["id"]
        old = row["status"]
        u = UP.get(rid)
        if u:
            new = u["status"]
            arts = u["arts"]
            src = u["src"]
            ev = u["ev"]
        else:
            new = old
            arts = []
            src = row["source"]
            ev = "Retained from round 1 (2026-11-17); not re-read in round 2."
        artifacts = [dict(path=A[k], exists=exists(A[k])) for k in arts]
        # the verdict rule: met needs every cited artifact to exist
        if new == "met" and not all(a["exists"] for a in artifacts):
            raise SystemExit("rule violated: %s is met but an artifact is missing" % rid)
        src_type = "process (repository)" if row["group"] in PROCESS_GROUPS else (
            "official nfl.com" if src.startswith("https://www.nfl.com") else "repository")
        rows.append(dict(
            id=rid, group=row["group"], requirement=row["requirement"],
            status_2026_11_17=old, status=new, status_change=(new != old),
            gate=row["gate"], clears=row["clears"],
            source=src, source_type=src_type,
            evidence=ev, artifacts=artifacts,
            round2_reviewed=bool(u),
        ))

    # clearing text corrections (A03 counts, A02/A07 clearing sets)
    for rr in rows:
        if rr["id"] == "A03":
            rr["clears"] = ("venue for every scheduled 2026 regular-season game, transcribed from its official game page; "
                            "the number of games is to be computed from the official schedule, not typed")
        if rr["id"] == "A02":
            rr["clears"] = ("the 13 missing official Week-10 finals added (transcribed with URLs on the Games page), and a line-by-line "
                            "re-read of the 105 aggregate-only rows")
        if rr["id"] == "A07":
            rr["clears"] = ("a split table that assigns every completed game to train, validation or holdout, or a dated freeze at 136 "
                            "with Week 10 named as a prospective window")
        if rr["id"] == "A06":
            rr["clears"] = "refit on all 150 official completed games (or 136 + 14 Week-10 finals) and publish the refit date"
        if rr["id"] == "C05":
            rr["clears"] = "favorites baseline computed from standings as of each game's pre-kickoff date"
        if rr["id"] == "D01":
            rr["clears"] = "correlations recomputed on the full official completed-game set, with n published"
        if rr["id"] == "E26":
            rr["clears"] = "full re-read of all 8 report chunks; per-club counts and the capture's sha256 published together"

    counts = {}
    for rr in rows:
        counts[rr["status"]] = counts.get(rr["status"], 0) + 1
    changed = [rr["id"] for rr in rows if rr["status_change"]]

    reg = dict(
        dataset="nfl_req_review_register",
        round=ROUND, session=SESSION,
        title="Requirement register — round 2 audit (2026-11-18)",
        base_register="data/requirements_2026_11_17.json (round 1, 73 rows)",
        rule="met requires an existing artifact path and an official source that supports the claim; otherwise partial with the reason stated.",
        statuses={"met": "implemented, cited artifact exists, official source supports it",
                  "partial": "implemented but limited by a documented evidence gap (blank and flagged)",
                  "blocked": "cannot be completed from official sources; blank and flagged",
                  "not_started": "no implementation exists",
                  "in_progress": "under way in this session"},
        counts=counts,
        changed_this_round=changed,
        rows=rows,
    )
    with open(os.path.join(DATA, "requirements_2026_11_18.json"), "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=2, ensure_ascii=False); f.write("\n")

    # -----------------------------------------------------------------------
    # Flags (round 2). Each: id, severity, title, detail, sources, owner, status.
    # -----------------------------------------------------------------------
    fr = reads["feed_reconciliation"]
    flags = [
        dict(id="RF-08", severity="correction", owner="nfl-req-review (round 1, corrected here)",
             title="Week 11 has 13 fixtures, not 14",
             detail="Round 1 stated 14 Week-11 fixtures in the venue row (A03) and '137 games' in its clearing text. The official Week-11 "
                    "schedule shows 13 fixtures and six clubs on bye (ATL, CLE, GB, LAR, NE, SEA). The venue row is corrected.",
             sources=[SRC_W11]),
        dict(id="RF-09", severity="irregularity", owner="nfl-book (peer namespace; logged, not edited)",
             title="The verified results feed omits 13 official Week-10 games",
             detail="nfl-book/data/results_feed.json holds 136 games for Weeks 1-9, which reconcile to official standings for 32 of 32 clubs, "
                    "and one Week-10 game (W10-WAS-NYG). The other 13 Week-10 finals read today are missing. Downstream: model_outputs "
                    "n_train_games = 137, correlations n = 137, and the holdout window names 137 games.",
             sources=[SRC_W10, "https://github.com/sassnarep3-star/Own4/blob/main/nfl-book/data/results_feed.json"]),
        dict(id="RF-10", severity="irregularity", owner="nfl-availability-desk (peer namespace; logged, not edited)",
             title="A standings check reports 133 games through Week 9; the official arithmetic gives 136",
             detail="nfl-availability-desk/data/derived/standings_check.json reports 145 games credited and 12 Week-10 games credited, so 133 through "
                    "Week 9. Its own 'week10_final_at_read' is 9, so the credited games through Week 9 are 145 - 9 = 136. Today's official "
                    "standings give 150 completed games and the Week-10 page shows 14 finals, so 150 - 14 = 136. Its reviewer claim that no file "
                    "publishes 136 is contradicted by the standings arithmetic here.",
             sources=[SRC_STAND, SRC_W10, "https://github.com/sassnarep3-star/Own4/blob/main/nfl-availability-desk/data/derived/standings_check.json"]),
        dict(id="RF-11", severity="irregularity", owner="nfl-book (peer namespace; logged, not edited)",
             title="The holdout split leaves 13 completed Week-10 games in no split",
             detail="nfl-book/data/holdout_split.json: train = Weeks 1-9 (136 games); validation = 'Week 10 TNF (1 game, 137th)'. The other 13 "
                    "official Week-10 finals are not assigned to any split.",
             sources=[SRC_W10, "https://github.com/sassnarep3-star/Own4/blob/main/nfl-book/data/holdout_split.json"]),
        dict(id="RF-12", severity="stale source", owner="nfl-req-review (round 1; superseded)",
             title="Round-1 standings capture is one game stale for two clubs",
             detail="The round-1 capture (official_reads_2026_11_17.json) shows BAL 4-5 (189 PF, 236 PA) and LAC 0-8 (121 PF, 219 PA). Today's standings "
                    "show BAL 4-6 (209, 259) and LAC 1-8 (144, 239), after Monday's Chargers 23, Ravens 20 game. The round-1 read predates that game.",
             sources=[SRC_STAND, SRC_W10]),
        dict(id="RF-13", severity="irregularity", owner="nfl-req-review (round 1; superseded)",
             title="Round-1 injury totals in the findings text do not match the capture's own totals",
             detail="Round-1 text: '326 rows; 14 Out; 11 Questionable; 0 Doubtful'. The round-1 capture's totals: 346 players listed over 28 clubs, "
                    "70 Out, 90 Questionable, 11 Doubtful. The text was typed by hand; the totals are computed. The capture is kept; the text is superseded.",
             sources=[SRC_INJ10]),
        dict(id="RF-14", severity="unresolved", owner="nfl-req-review (round 2)",
             title="Cincinnati's Week-10 listed count: 9 in the capture, 4 in the brief",
             detail="The brief states Cincinnati lists 4 players on the Week-10 report. The capture lists 9. The Cincinnati section falls in chunks 2-7, "
                    "which were not re-read this round. Not resolved; not inferred.",
             sources=[SRC_INJ10]),
        dict(id="RF-15", severity="stale source", owner="nfl-req-review (continues RF-02)",
             title="The Week-11 injury report is not yet published",
             detail="At the 2026-11-18 read, nfl.com/injuries/league/2026/reg11 still displays the Week-10 report, and the hub shows Week 10. "
                    "No Week-11 designations are recorded here.",
             sources=[SRC_INJ11, "https://www.nfl.com/injuries/"]),
        dict(id="RF-16", severity="irregularity", owner="nfl-book (peer namespace; logged, not edited)",
             title="The favorites-only control is not point-in-time",
             detail="control_baseline.json states the favorites-only baseline uses current standings win%. Standings after a game use that game's result, so "
                    "the control uses information it could not have had. The file discloses this; it still needs replacing.",
             sources=[SRC_STAND]),
        dict(id="RF-17", severity="clarification", owner="nfl-book (peer namespace; logged, not edited)",
             title="The 'closing' values in the price store are model runs, not market closes",
             detail="price_snapshots.json defines close = 'final run at publication (train through Week 10 TNF)', and all market_* fields are null "
                    "(FB-01). The store is therefore a log of the model's own numbers at two times, not a price history.",
             sources=[SRC_GAME_IND]),
        dict(id="RF-18", severity="limitation", owner="repository (all sessions)",
             title="This sandbox clone is shallow; pre-registration commits cannot be checked here",
             detail="`git rev-parse --is-shallow-repository` returns true in this checkout. 'The commit hash is the registration' cannot be verified "
                    "from this clone; the check needs full history.",
             sources=[SRC_GH_COORD]),
        dict(id="RF-19", severity="scope", owner="repository (all sessions)",
             title="Several NFL pull requests were open at the read time, touching overlapping NFL content",
             detail="At the read time, 15 pull requests were open, of which four (#158 to #161) were opened in the 03:13-03:16 UTC window on 2026-11-18 "
                    "by other sessions and touch NFL content. This round does not edit them.",
             sources=["https://github.com/sassnarep3-star/Own4/pulls"]),
    ]
    flags_out = dict(dataset="nfl_req_review_flags_round2", round=ROUND, session=SESSION,
                     rule="Published, non-blocking, with source links. Corrections and peer-owned issues are logged here and not edited in peer namespaces.",
                     flags=flags)
    with open(os.path.join(DATA, "flags_2026_11_18.json"), "w", encoding="utf-8") as f:
        json.dump(flags_out, f, indent=2, ensure_ascii=False); f.write("\n")

    # -----------------------------------------------------------------------
    # Questions: question, known answer, gap, how to discover, sources
    # -----------------------------------------------------------------------
    q = [
        ("Q01", "Is there an official source for betting lines (opening and closing prices)?",
         "Not found. None of the official pages read this round shows a betting line, and every market_* field in the price store is null (RF-17).",
         "An official or owner-approved price source (decision SG-01). Options are in suggestion S-02.",
         "Owner decision. Search nfl.com terms and data-licence pages for any price feed before choosing.", [SRC_GAME_IND]),
        ("Q02", "How many completed 2026 regular-season games are there?",
         "150 through Week 10 (RC-02). 136 through Week 9 (RC-07).",
         "Week 11 onward, as they complete.",
         "Re-read the standings each week and recompute sum(W+L+T)/2 (engine/round2.py).", [SRC_STAND]),
        ("Q03", "Does the verified results feed contain every completed game?",
         "All 136 Weeks 1-9 games reconcile to official standings for 32 of 32 clubs. 1 of 14 Week-10 finals is present (RC-11, RC-12).",
         "13 Week-10 finals. 105 rows are aggregate-only.",
         "Add the 13 finals (already transcribed with URLs on the Games page); re-read the aggregate-only rows game by game.", [SRC_W10]),
        ("Q04", "Which Week-11 games are scheduled, and where are they played?",
         "13 fixtures and six byes (RC-08, RC-09). Kickoff times and networks are as printed on the schedule page. Venues were not re-read in round 2.",
         "Venue for each of the 13 games from its official game page; roof and surface are not on the pages read.",
         "Open each game page; record the venue as printed, or leave blank.", [SRC_W11, SRC_GAME_IND]),
        ("Q05", "Has the Week-11 injury report been published?",
         "Not at the 2026-11-18 read. The Week-11 URL shows the Week-10 report (RF-15).",
         "The Week-11 designations and their timestamps.",
         "Daily capture from Wednesday to kickoff, with fetch time and hash (suggestion S-05).", [SRC_INJ11]),
        ("Q06", "Are the six 'Out' designations on the final Week-10 report corroborated by an official list?",
         "Round 1 found six 'Out' rows that are on neither the official Week-10 inactive list nor the November reserve list (RF-01).",
         "An official inactive list for each of those games, or the reason they are absent.",
         "Compare the Week-11 inactive list when it is published, and retain the Week-10 comparison as it stands.", [SRC_INJ10]),
        ("Q07", "Does a 'Questionable' designation predict that a player plays?",
         "Not measured. Round 1 joined one Sunday's report to the inactive list (n and Wilson intervals on the Verification page). That is one week, not a rate.",
         "Play rate per designation across several seasons, with confidence intervals (E14, E21).",
         "Retrieve prior seasons' injury reports from the official archive, then join them to inactive lists. Archive availability is unconfirmed here.", [SRC_INJ10]),
        ("Q08", "Is there an official depth-chart source for all 32 clubs?",
         "Not established. The league route is closed (404). Per the depth-sweep namespace (not re-read here), 31 club pages are text and Houston publishes an image.",
         "A machine-readable Houston depth surface, or an authorised structured source (E13).",
         "Owner decision on an authorised source. Transcribing an image by eye is not allowed by the brief.", [SRC_W11]),
        ("Q09", "Do official NFL Game Books contain snap counts, so that starters can be measured?",
         "Not verified. Round 1 recorded that the Game Book route is reachable; the contents were not checked against snap counts.",
         "Confirmation that a Game Book lists snaps per player, and coverage for all 32 clubs (E06, A05).",
         "Open one official Game Book PDF for a completed game and read it line by line.", [SRC_W10]),
        ("Q10", "Is the control baseline point-in-time?",
         "No. The favorites-only baseline uses end-of-period standings (RF-16).",
         "Standings as of each game's pre-kickoff date.",
         "Capture a weekly standings snapshot from now on (its hash and time), then recompute the baseline.", [SRC_STAND]),
        ("Q11", "Can the pre-registration commits be verified?",
         "Not from this clone. It is shallow (RF-18).",
         "Full git history, and the commit hash for each registered rule.",
         "Run the registration check in an environment with full history (or CI with fetch-depth 0).", [SRC_GH_COORD]),
        ("Q12", "How large a sample do the leaderboard gates need?",
         "The register states n >= 300 graded games per strategy (C02). This season has 150 completed games.",
         "At least two more full seasons, or the owner's changed threshold.",
         "Owner decision on the threshold and on the number of seasons to collect.", [SRC_STAND]),
        ("Q13", "Which page is the public entry point for the NFL work?",
         "The root site is the NBA dashboard. NFL work is in 39 separate namespaces (repo review RR-01).",
         "Owner decision on one entry point, and the root navigation change.",
         "Suggestion S-01 and S-08.", [SRC_GH_COORD]),
        ("Q14", "How many players does Cincinnati list on the Week-10 report?",
         "9 in the round-1 capture. The brief says 4. The rest of the report was not re-read (RF-14).",
         "The Cincinnati section, read in full.",
         "Full re-read of Week-10 chunks 2-7 (suggestion S-10).", [SRC_INJ10]),
    ]
    qs = [dict(id=i, question=a, known_answer=b, gap=c, how_to_discover=d, sources=e) for i, a, b, c, d, e in q]
    with open(os.path.join(DATA, "questions.json"), "w", encoding="utf-8") as f:
        json.dump(dict(dataset="nfl_req_review_questions", round=ROUND, rows=qs), f, indent=2, ensure_ascii=False); f.write("\n")

    # -----------------------------------------------------------------------
    # Suggestions: options and a recommended path. Nothing here is implemented.
    # -----------------------------------------------------------------------
    s = [
        ("S-01", "One NFL entry point; freeze the other namespaces",
         "39 NFL namespaces publish contradictory numbers (RR-01, RR-02).",
         ["(a) Keep all namespaces as they are", "(b) Freeze peers, make this namespace the entry point, and link each peer from a sitemap", "(c) Delete peers"],
         "(b)", "Owner decision. No peer file is changed in this round."),
        ("S-02", "Price-data policy (decision SG-01)",
         "No official price source found. Market columns are blank (Q01).",
         ["(a) License an official or authorised price feed", "(b) Accept blank market columns; publish own lines only", "(c) Manual screenshots of third-party prices"],
         "(b) now; revisit if (a) is found", "Owner decision. Option (c) has no verifiable provenance and conflicts with the brief's official-source rule."),
        ("S-03", "Add the 13 missing Week-10 finals to the results feed",
         "The feed reconciles for Weeks 1-9 and omits 13 Week-10 finals (RF-09).",
         ["(a) Add the 13 finals transcribed here, with their URLs", "(b) Wait for the next scheduled refresh"],
         "(a)", "Owner of nfl-book to apply; the transcription and URLs are in data/official_reads_2026_11_18.json."),
        ("S-04", "Make the split table cover every completed game",
         "13 completed games are in no split (RF-11).",
         ["(a) Freeze at 136 and name Week 10 as the first prospective window", "(b) Extend the train set to all 150 games and re-run the walk-forward test"],
         "(a)", "Owner decision. Option (b) changes a pre-registered corpus and needs a new registration."),
        ("S-05", "Capture the injury report from Wednesday to kickoff, with hashes",
         "No daily series exists; Week 11 is not yet published (RF-15).",
         ["(a) Scheduled CI job (Wed-Sat) that fetches nfl.com and commits a hashed capture", "(b) Manual capture by the owner", "(c) Do not capture"],
         "(a)", "Owner approval for a scheduled job. The sandbox cannot reach nfl.com with curl; CI runners are a separate network path, to be confirmed."),
        ("S-06", "Replace the favorites-only control with a point-in-time one",
         "The current control uses future information (RF-16).",
         ["(a) Compute favorites from standings as of each pre-kickoff date", "(b) Remove the favorites control"],
         "(a)", "Needs weekly standings captures, which S-05 style capture would supply."),
        ("S-07", "Make 'met' impossible without an artifact and an official source",
         "Round 2 downgraded 8 'met' rows that did not meet this test.",
         ["(a) Keep the round-2 rule in this namespace only", "(b) Apply the same verifier across all namespaces"],
         "(b)", "Owner decision. The verifier here is engine/verify_r2.py."),
        ("S-08", "Link this namespace from the root landing page",
         "The root page does not link the NFL work.",
         ["(a) Add a root navigation entry (integration session)", "(b) Leave it unlinked"],
         "(a)", "Logged in COORDINATION.md for the root-nav owner. Not edited here."),
        ("S-09", "Split COORDINATION.md into an archive and an active board",
         "COORDINATION.md is 569,341 bytes; claims and logs from many sessions sit in one file (RR-10).",
         ["(a) Move completed logs to COORDINATION-ARCHIVE.md", "(b) Keep as is"],
         "(a)", "Owner decision. Changing the file is a separate task."),
        ("S-10", "Re-read the whole Week-10 injury report and publish per-club counts",
         "Round 1 totals disagree with its own text, and Cincinnati is unresolved (RF-13, RF-14).",
         ["(a) Re-read all eight chunks and publish per-club counts with the capture hash", "(b) Keep the round-1 capture unchanged"],
         "(a)", "Next round. It does not block the merge."),
    ]
    SUG_SRC = {
        "S-01": ["https://github.com/sassnarep3-star/Own4/tree/main", "https://github.com/sassnarep3-star/Own4/blob/main/nfl-req-review/data/repo_review.json"],
        "S-02": ["https://www.nfl.com/", SRC_GAME_IND],
        "S-03": [SRC_W10, "https://github.com/sassnarep3-star/Own4/blob/main/nfl-book/data/results_feed.json"],
        "S-04": [SRC_W10, "https://github.com/sassnarep3-star/Own4/blob/main/nfl-book/data/holdout_split.json"],
        "S-05": [SRC_INJ11, "https://www.nfl.com/injuries/"],
        "S-06": [SRC_STAND, "https://github.com/sassnarep3-star/Own4/blob/main/nfl-book/data/control_baseline.json"],
        "S-07": ["https://github.com/sassnarep3-star/Own4/blob/main/nfl-req-review/engine/verify_r2.py"],
        "S-08": ["https://sassnarep3-star.github.io/Own4/"],
        "S-09": [SRC_GH_COORD],
        "S-10": [SRC_INJ10],
    }
    sg = [dict(id=i, title=a, why=b, options=c, recommended=d, decision_owner=e, decision="", sources=SUG_SRC[i]) for i, a, b, c, d, e in s]
    with open(os.path.join(DATA, "suggestions.json"), "w", encoding="utf-8") as f:
        json.dump(dict(dataset="nfl_req_review_suggestions", round=ROUND, rule="Suggestions only. Choose a path before any implementation. The decision field is left blank for the owner.", rows=sg), f, indent=2, ensure_ascii=False); f.write("\n")

    # -----------------------------------------------------------------------
    # Repo review (scope, method, findings)
    # -----------------------------------------------------------------------
    _feed = load_json_root("nfl-book/data/results_feed.json")
    FEED_ROWS = len(_feed["rows"])
    NFL_SRC_ROWS = sum(1 for r in _feed["rows"] if str(r.get("source_url", "")).startswith("https://www.nfl.com"))
    nfl_dirs = sorted(d for d in os.listdir(ROOT) if d.startswith("nfl") and os.path.isdir(os.path.join(ROOT, d)))
    open_prs = [158, 159, 160, 161, 150, 132, 127, 119, 93, 59, 56, 47, 43, 39, 29]
    rr = [
        ("RR-01", "39 top-level directories are named nfl* (computed).",
         "Overlapping namespaces publish different figures for the same questions.",
         "Directory listing at the repository root.", "https://github.com/sassnarep3-star/Own4/tree/main", "irregular"),
        ("RR-02", "Four different game counts appear for the same 2026 season: 133, 136, 137 and 150.",
         "150 completed through Week 10 is the official value; 136 is Weeks 1-9; 137 is the feed's Weeks 1-9 plus one Week-10 game; 133 is an arithmetic error (RF-10).",
         "RC-02, RC-07, RC-11, RC-12.", "https://www.nfl.com/standings/league/2026/REG", "irregular"),
        ("RR-03", "The holdout split names 137 games and leaves 13 in no split.",
         "See RF-11.", "nfl-book/data/holdout_split.json", "https://github.com/sassnarep3-star/Own4/blob/main/nfl-book/data/holdout_split.json", "irregular"),
        ("RR-04", "Round-1 Week-11 venue row says 14 fixtures; the official schedule shows 13.",
         "See RF-08. Corrected in round 2.", "RC-08, RC-09.", SRC_W11, "corrected"),
        ("RR-05", "Round-1 standings capture is one game stale for BAL and LAC.",
         "See RF-12. Superseded by the round-2 read.", "RC-15.", SRC_STAND, "stale source"),
        ("RR-06", "Round-1 injury totals in the text disagree with the capture's own totals.",
         "See RF-13.", "RC-13.", SRC_INJ10, "irregular"),
        ("RR-07", "Cincinnati's listed count differs between the brief (4) and the capture (9).",
         "See RF-14. Unresolved.", "RC-14.", SRC_INJ10, "unresolved"),
        ("RR-08", "The sandbox clone is shallow.",
         "Pre-registration commit history cannot be verified here (RF-18).",
         "`git rev-parse --is-shallow-repository` returns true.", SRC_GH_COORD, "limitation"),
        ("RR-09", "Open pull requests at read time: %d." % len(open_prs),
         "Four were opened in the 03:13-03:16 UTC window on 2026-11-18 and touch NFL content (RF-19).",
         "gh pr list --state open (read 2026-11-18). PR numbers: %s." % ", ".join("#%d" % n for n in open_prs),
         "https://github.com/sassnarep3-star/Own4/pulls", "scope"),
        ("RR-10", "COORDINATION.md is 569,341 bytes.",
         "A single file carries claims and logs from many sessions. Hard to audit (S-09).",
         "Measured 2026-11-18 on the claim branch before this round's log entries.", SRC_GH_COORD, "maintenance"),
        ("RR-11", "No credential values in the repository.",
         "A scan for ghp_, github_pat_, AKIA and PEM private-key headers matched one file: repo_review/REVIEW-2026-11-06.md, which names the patterns without a value.",
         "grep over all text files, excluding .git (2026-11-18).", "https://github.com/sassnarep3-star/Own4/blob/main/repo_review/REVIEW-2026-11-06.md", "clean"),
        ("RR-12", "Large raw captures sit in the repository.",
         "data/raw holds 53 MB of earlier-session captures (ESPN and NBA). This namespace uses none of them.",
         "du -sh on the paths, 2026-11-18.", "https://github.com/sassnarep3-star/Own4/tree/main/data/raw", "size"),
        ("RR-13", "Pages is built from the legacy configuration, branch main, path /.",
         "Read via the GitHub API at the read time: status built.",
         "gh api repos/sassnarep3-star/Own4/pages (2026-11-18).", "https://sassnarep3-star.github.io/Own4/", "verified"),
        ("RR-14", "Round-1 verifier still passes on its own pages.",
         "Ran the round-1 verify.py on the committed tree before this round: PASS.",
         "python3 nfl-req-review/engine/verify.py (2026-11-18, before round 2 files).", "https://sassnarep3-star.github.io/Own4/nfl-req-review/", "verified"),
        ("RR-15", "The results feed cites an official nfl.com URL for each row.",
         "Every row has a source_url field; 32 rows are marked line_by_line and 105 aggregate-only (feed provenance note). %d of %d rows carry an nfl.com source_url." % (NFL_SRC_ROWS, FEED_ROWS),
         "nfl-book/data/results_feed.json.", "https://github.com/sassnarep3-star/Own4/blob/main/nfl-book/data/results_feed.json", "partly verified"),
        ("RR-16", "Round-1 'met' verdicts were not all supported by their own artifacts.",
         "Round 2 downgraded %d rows (see requirements page, 'changed this round')." % len(changed),
         "Requirements page; each downgrade has its reason.", SRC_GH_COORD, "corrected"),
        ("RR-18", "The build sandbox cannot reach nfl.com directly.",
         "Reads on 2026-11-18 used the page-fetch tool. A direct request returned no response, while github.com answered. CI runners are a separate network path and are not tested here.",
         "curl -sS --max-time 10 https://www.nfl.com/injuries/ returned HTTP 000 on 2026-11-18; the same call to https://github.com returned 200.", "https://www.nfl.com/injuries/", "limitation"),
        ("RR-17", "Scope of this review.",
         "Reviewed: 32 club standings, 14 Week-10 finals, 13 Week-11 fixtures, the Week-10 Lions rows, the round-1 capture, the results feed, the holdout split, the control baseline, the price store, model outputs, removal-of-luck and demotion files. Not reviewed: Week-10 injury chunks 1-7, every other namespace line by line, and non-NFL content.",
         "This page and data/repo_review.json.", SRC_GH_COORD, "scope"),
    ]
    rv = dict(dataset="nfl_req_review_repo_review", round=ROUND, session=SESSION,
              method="Mechanical checks (directory listing, grep, du, gh api, git plumbing) plus the round-2 reconciliations. Measured values are recorded with their date.",
              nfl_namespace_count=len(nfl_dirs), open_pr_numbers=open_prs,
              rows=[dict(id=a, finding=b, detail=c, evidence=d, source=e, class_=f) for a, b, c, d, e, f in rr])
    with open(os.path.join(DATA, "repo_review.json"), "w", encoding="utf-8") as f:
        json.dump(rv, f, indent=2, ensure_ascii=False); f.write("\n")

    print("requirements:", len(rows), counts, "changed:", changed)
    print("flags:", len(flags), "questions:", len(qs), "suggestions:", len(sg), "repo rows:", len(rr))


if __name__ == "__main__":
    main()
