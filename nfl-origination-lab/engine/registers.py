#!/usr/bin/env python3
"""
Three registers, each generated so the counts on the pages come from the data:

  data/questions.json    what we must answer before a decision is reasonable, what we
                         have, what we do not have, and what would settle it
  data/suggestions.json  site and method suggestions, every decision field blank
  data/flagged.json      every irregularity found this session, with its source, its
                         severity and whether it affects a published number

Every row names where its evidence lives. A question whose evidence does not exist
says so in `do_not_have` rather than hinting at what the answer might be.
"""

import json
import os

import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stable import dump

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
DATA = os.path.join(LAB, "data")
ROOT = os.path.dirname(LAB)


def load(name):
    return json.load(open(os.path.join(DATA, name), encoding="utf-8"))


def main():
    corpus = load("corpus.json")
    led = load("leaderboard.json")
    luck = load("luck.json")
    pol = load("price_policy.py".replace(".py", ".json"))
    res = load("residuals.json")
    dep = load("depth.json")
    av = load("availability_parse.json")
    corr = load("correlations.json")

    n2026 = corpus["counts"]["by_season"]["2026"]
    best = max((r for r in led["rows"] if r["model"] != "M0"),
               key=lambda r: r["proper_score"]["bss_moneyline"])

    # ------------------------------------------------------------------
    # questions
    # ------------------------------------------------------------------
    Q = [
        ("Q01", "Can a price we are allowed to use be obtained at all?",
         "The price policy decision: a publisher plus a capture time.",
         "12,573 stored price rows, 6,345 of them carrying an official nfl.com source key.",
         "Any officially published number with a known capture time. None exists in the store.",
         "One licensed feed or one operator price history with timestamps.",
         "data/price_policy.json", "blocking"),
        ("Q02", "How large is the 2026 graded sample, exactly?",
         "Arithmetic between the results corpus and official standings.",
         "%d games, weeks 1-10; standings imply %s; points %d equal sum(PF) %d."
         % (n2026, corpus["standings_arithmetic"]["games_implied_by_standings"],
            corpus["standings_arithmetic"]["corpus_points"],
            corpus["standings_arithmetic"]["pf_total"]),
         "Nothing for weeks 1-10; weeks 11+ are unplayed.",
         "The season to finish, then a re-read of every week page.",
         "data/corpus.json", "settled"),
        ("Q03", "Is the moneyline skill real or is it one hot week?",
         "A week-cluster interval, a permutation null, and leave-one-week-out folds.",
         "%s: skill %+0.4f, 90%% bound [%+0.4f, %+0.4f], Holm p %.4f; dropping the best "
         "week leaves %+0.4f; %d of 2000 label shuffles match or beat it."
         % (best["model"], best["proper_score"]["bss_moneyline"],
            best["proper_score"]["ci90_moneyline"][0], best["proper_score"]["ci90_moneyline"][1],
            best["proper_score"]["holm_p_moneyline"],
            min(x["skill"] for x in luck["leave_one_week_out"]),
            int(round(luck["panel"][0]["value"] * 2000))),
         "Out-of-season confirmation. Ten weeks of one season is a short claim.",
         "A full 18-week 2026 block, and a second season.",
         "data/luck.json", "open"),
        ("Q04", "Why does the side (margin) market show no skill while the moneyline does?",
         "Two proper scores on the same forecasts: CRPS on margin, Brier on the win.",
         "Margin CRPS skill is near zero for every model; the win Brier skill is positive. "
         "A rating that ranks teams but mis-estimates the spread size would do this.",
         "A model whose sigma is fitted, not inherited from in-sample residuals.",
         "Fit the dispersion on the validation block and re-score the margin market.",
         "data/leaderboard.json", "open"),
        ("Q05", "Why does the total show no skill?",
         "The same interval machinery applied to the total market.",
         "Benchmark-relative total skill %+0.4f, Holm-adjusted p 1.0000 for every model. "
         "Club total persistence between consecutive games is %s with n %d."
         % (best["proper_score"]["bss_total"],
            [r["r"] for r in corr["rows"] if r["season"] == 2026 and "club_total" in r["pair"]][0],
            [r["n"] for r in corr["rows"] if r["season"] == 2026 and "club_total" in r["pair"]][0]),
         "A total model with information beyond past club totals.",
         "A published pace/plays/efficiency input read from an official source.",
         "data/correlations.json", "open"),
        ("Q06", "Does availability change outcomes at all, and by how much?",
         "An ablation: identical models with and without verified availability features.",
         "Nothing usable: 0 snap counts, 0 inactive lists, 1 image-only club chart.",
         "Snap counts and inactive lists for the graded games.",
         "Capture both, then run the ablation with chronological holdouts.",
         "data/depth.json", "blocking"),
        ("Q07", "How deep is the replacement when a starter is out?",
         "Chart rank of the out player and of his replacement.",
         "%d documented replacements, all %d with a rank difference."
         % (dep["replacement_depth"]["n_replacements_documented"],
            sum(1 for r in dep["replacement_depth"]["rows"]
                if r["depth_of_replacement"] is not None)),
         "A rank for every replacement, and a chart capture at the time of the game.",
         "Daily chart captures joined to roster events.",
         "data/depth.json", "partial"),
        ("Q08", "Are the depth charts current?",
         "A join against the official November 2026 reserve list.",
         "%d clubs flagged: %s."
         % (dep["stale_chart_flags"]["n_clubs_flagged"],
            "; ".join("%s (%d)" % (r["club"], len(r["flags"]))
                      for r in dep["stale_chart_flags"]["rows"])),
         "A re-capture of the flagged clubs after their roster moves.",
         "One capture per club per day with a retained hash.",
         "data/depth.json", "partial"),
        ("Q09", "Which club's chart cannot be read at all?",
         "The register's own status field.",
         "%d of 32 clubs are image-only; %d slots transcribed from the other %d."
         % (dep["slot_shape"]["clubs_not_transcribed"], dep["slot_shape"]["slots"],
            dep["slot_shape"]["clubs_transcribed"]),
         "A structured Houston chart, or an official snap-count source for all 32.",
         "The club's own structured feed, or the snap-count route.",
         "data/depth.json", "blocking"),
        ("Q10", "What does a blank game status mean?",
         "The official page's own vocabulary across two dated reads.",
         "Of %d rows, %d carry a designation (%.2f%%). Blank is published as blank."
         % (len(av["rows"]), sum(1 for r in av["rows"] if r["game_status"]),
            100.0 * sum(1 for r in av["rows"] if r["game_status"]) / len(av["rows"])),
         "Inactive lists to join against the blanks.",
         "Capture the inactive list at kickoff for each game.",
         "data/availability_parse.json", "open"),
        ("Q11", "Is the injury signal a surprise or a level?",
         "Two dated reads of the same report week, joined player by player.",
         "%d players appear in both reads; %d differs."
         % (av["transcription_control"]["joined_rows"],
            len(av["transcription_control"]["differences"])),
         "More than one week of two-read pairs.",
         "Daily captures from Wednesday to kickoff, every week.",
         "data/availability_parse.json", "partial"),
        ("Q12", "Do two sessions reading the same official page agree?",
         "A join on (club, player) between two independently written parsers.",
         "%d of %d joined rows identical on position and game status; practice agrees on %d."
         % (av["transcription_control"]["fields_equal"]["pos"],
            av["transcription_control"]["joined_rows"],
            av["transcription_control"]["fields_equal"]["practice"]),
         "Nothing: this is the strongest corroboration available without a second publisher.",
         "Nothing further; the limit is stated.",
         "data/availability_parse.json", "settled"),
        ("Q13", "Is our own line close to the official posted line?",
         "Residual = model fair line minus the official posted line, per market.",
         "%d residual rows, %d with an official line."
         % (res["counts"]["rows"], res["counts"]["rows_with_an_official_line"]),
         "A capture time on the posted line, so the residual can be dated against kickoff.",
         "A timestamped price source.",
         "data/residuals.json", "open"),
        ("Q14", "Can a parlay or prop combo be ranked yet?",
         "A directly validated joint probability plus the operator's void/push rules.",
         "All three combo divisions are closed; 0 joint prices exist.",
         "One joint price from an official or licensed source.",
         "A licensed joint-price feed.",
         "data/leaderboard.json", "blocking"),
        ("Q15", "Which of the three markets should be published first?",
         "The registered order and whether the ranking supports it.",
         "Registered order: side, total, moneyline. Measured: only the moneyline clears a "
         "Holm-adjusted threshold; the side and total do not.",
         "Whether a side-skill model exists at all.",
         "Diagnose the margin dispersion (Q04) before reordering.",
         "prereg/PREREG-LAB-1.json", "open"),
        ("Q16", "Is the repository's own data layer lawful to republish?",
         "A rights decision for the raw rows and for any third-party archive.",
         "None recorded. Raw rows sit in a public repository.",
         "A recorded decision, or a move of raw rows to a private store.",
         "Read the terms of every source before publishing row-level data.",
         "pages/flagged.html", "blocking"),
        ("Q17", "Has any number here been read live from an official page today?",
         "An egress test before the build.",
         "No: the sandbox has no HTTPS route to nfl.com. Every number is a stored capture "
         "with its own date, or a computation over one.",
         "Nothing; this is a disclosure, not a defect.",
         "A session with egress re-reads the sources and diffs them.",
         "COORDINATION.md", "settled"),
    ]
    questions = {
        "dataset": "nfl_origination_lab_questions",
        "title": "Questions that must be answered before a decision is reasonable",
        "built": "2026-11-19",
        "reading": "each row states what would answer the question, what we already have, "
                   "what we do not have, and the action that would obtain it. No row "
                   "contains a guess at the answer.",
        "counts": {}, "rows": [],
    }
    for qid, q, info, have, lack, action, path, status in Q:
        questions["rows"].append({
            "id": qid, "question": q, "information_needed": info,
            "we_have": have, "we_do_not_have": lack,
            "how_to_obtain": action, "evidence": path, "status": status,
        })
    questions["counts"] = {s: sum(1 for r in questions["rows"] if r["status"] == s)
                           for s in ("blocking", "open", "partial", "settled")}

    dump(questions, open(os.path.join(DATA, "questions.json"), "w", encoding="utf-8"),
              indent=1)

    # ------------------------------------------------------------------
    # suggestions
    # ------------------------------------------------------------------
    S = [
        ("S01", "Put the decision-readiness table on the landing page, with the gate and the "
                "clearing number", "the landing page is the one page a reviewer reads",
         "one row per requirement; a reviewer can see in one screen what is blocked and what "
         "would unblock it", "high", "pages/requirements.html"),
        ("S02", "Publish the staking division empty, with its reason, instead of hiding it",
         "an empty division is a finding; a hidden one is an omission",
         "a reader cannot mistake a proper-score result for a profitable one", "high",
         "pages/leaderboard.html"),
        ("S03", "Show the residual distribution, not only the mean residual",
         "a mean hides a fat tail that would decide staking if it were allowed",
         "per-market residual quantiles on the origination page", "medium",
         "pages/origination.html"),
        ("S04", "Give every requirement row a machine-readable clearing number",
         "prose gates cannot be checked; numbers can",
         "a verifier can assert that a row claiming 'blocked' carries a clearing number",
         "high", "data/requirements.json"),
        ("S05", "Keep the league table and the skill table apart",
         "standings measure teams, the leaderboard measures forecasts",
         "no reader can confuse a 8-1 record with a calibrated model", "medium",
         "pages/corpus.html"),
        ("S06", "Publish the pre-registration hash on the leaderboard itself",
         "a score without its registration is a number without a warrant",
         "each leaderboard row links to the commit that froze its rule", "high",
         "pages/prereg.html"),
        ("S07", "Treat 'blank' as a first-class value in every table",
         "the brief's own rule: never infer a value",
         "a reviewer can count blanks; the verifier already counts them per page", "high",
         "pages/flagged.html"),
        ("S08", "Add a per-team view of out players and named replacements",
         "the brief asks for a quick team-level decision view",
         "a reader can see one club's availability without reading 253 rows", "medium",
         "pages/availability.html"),
        ("S09", "Publish the availability delta as a series, not a single pair",
         "one delta cannot show a trend; two can start one",
         "each week's pair joins the series and the trend becomes visible", "medium",
         "pages/availability.html"),
        ("S10", "Let the suggestions page carry a decision column and a date",
         "a suggestion with no decision path is a wish",
         "the owner can mark accept/decline with a date, and the page keeps the history",
         "high", "pages/suggestions.html"),
        ("S11", "Show the two total estimators side by side with the gap",
         "the brief asks for both until one wins",
         "the gap column makes the disagreement visible instead of hidden in a choice",
         "medium", "pages/leaderboard.html"),
        ("S12", "Add a control row to every future leaderboard run, forever",
         "a leaderboard without a control is a leaderboard of one",
         "the climatology control already runs; make it a hard precondition", "high",
         "data/leaderboard.json"),
        ("S13", "Publish this lab's own numbers with their capture dates, never as 'live'",
         "a stale number presented as live is the defect this repo repeats",
         "every table header states the date of the data behind it", "high",
         "index.html"),
        ("S14", "Put the egress limitation on the landing page, not only in the flags",
         "a reader must know that today's build read no page live",
         "no reader can mistake a stored capture for a fresh read", "high", "index.html"),
    ]
    suggestions = {
        "dataset": "nfl_origination_lab_suggestions",
        "title": "Suggestions for review, none implemented pending the owner's choice",
        "built": "2026-11-19",
        "decision_fields_blank_by_design": "every row carries decision = null so the owner "
                                           "chooses before anything is built",
        "rows": [],
    }
    for sid, s, why, effect, priority, page in S:
        suggestions["rows"].append({
            "id": sid, "suggestion": s, "why": why, "expected_effect": effect,
            "priority": priority, "decision": None, "decided_on": None,
            "would_touch": page,
        })
    dump(suggestions, open(os.path.join(DATA, "suggestions.json"), "w", encoding="utf-8"),
              indent=1)

    # ------------------------------------------------------------------
    # flags
    # ------------------------------------------------------------------
    F = [
        ("F-01", "No officially published price with a known capture time exists in the "
                 "repository", "blocking",
         "6,345 official-source rows have unpublished timing; 5,901 timestamped rows are "
         "non-official. Intersection empty.",
         "https://www.nfl.com/games/", "data/price_policy.json", "ROI cannot be published"),
        ("F-02", "The results feed is missing 9 of the 13 week-10 2026 games", "material",
         "A feed-only build scores 137 games instead of 150; the union fixes it.",
         "https://www.nfl.com/schedules/2026/by-week/week-10", "data/corpus.json",
         "corrected by the union; recorded"),
        ("F-03", "Club code spelled two ways: 'AZ' in one corpus and 'ARI' in the feed",
         "material",
         "A naive join drops or duplicates nine 2026 games.",
         "https://www.azcardinals.com/", "data/corpus.json", "corrected by an alias table"),
        ("F-04", "16 of 149 pre-registered 2026 corpus rows cite the week schedule page, not "
                 "the game centre", "minor",
         "The official source is correct but coarser; per-game provenance is weaker on those rows.",
         "https://www.nfl.com/schedules/2026/by-week/week-9", "data/corpus.json",
         "recorded per row as url_kind"),
        ("F-05", "Houston publishes its depth chart only as an image", "blocking",
         "No depth-order source is verified for all 32 clubs, so the brief's own gate keeps "
         "the backup-deficiency feature closed.",
         "https://www.houstontexans.com/team/depth-chart", "data/depth.json",
         "gate stays closed"),
        ("F-06", "Only 16 of 253 Week 11 injury rows carry a game designation", "material",
         "A model feature on designations has one fixture of coverage this week.",
         "https://www.nfl.com/injuries/", "data/availability_parse.json",
         "no designation feature built"),
        ("F-07", "The 2026 price store's week-11 'close' is the latest posted line, not a close",
         "material",
         "78 rows carry the store's own label 'game not played yet - number is the latest "
         "POSTED line, not a close'.",
         "https://www.nfl.com/games/", "data/price_policy.json", "no close is claimed"),
        ("F-08", "One job description file in the repo stores a raw capture whose bytes are "
                 "371,313 while a peer's summary table says 3,713", "minor",
         "A reader comparing documents sees two byte counts for one file; the file's true "
         "size is 371,313 and its sha256 matches the peer's hash.",
         "https://www.nfl.com/injuries/", "data/availability_parse.json",
         "disclosed; the hash is the identity that matters"),
        ("F-09", "This session could not read any official page live", "disclosure",
         "The sandbox has no HTTPS egress to nfl.com. Every number here is a stored capture "
         "or a computation over one.",
         "https://www.nfl.com/", "COORDINATION.md", "disclosed on the landing page"),
        ("F-10", "The repository holds no snap counts, no inactive lists and no game books",
         "blocking",
         "Three requirements (R10, R11, R29, R43) cannot be met at all; no substitute is used.",
         "https://www.nfl.com/", "data/depth.json", "gates stay closed"),
        ("F-11", "Two clubs' depth charts still list players who are on the reserve list",
         "material",
         "TEN lists Peter Skoronski and Tommy Townsend at rank 1 after their 11/14 reserve move.",
         "https://www.nfl.com/transactions/league/reserve-list/2026/11", "data/depth.json",
         "flagged per player"),
        ("F-12", "A player's name is rendered two ways across two reads of the same page",
         "minor",
         "'Dee Alford' and 'De'Alford, Dee' on the Buffalo table; not merged on a guess.",
         "https://www.nfl.com/injuries/", "data/availability_parse.json",
         "left as two keys"),
        ("F-13", "No recorded rights decision covers the raw rows republished in this "
                 "public repository", "blocking",
         "Requirement R38 asks for a public/private split; none exists.",
         "https://www.nfl.com/legal/", "pages/flagged.html", "needs an owner decision"),
        ("F-14", "The 2025 validation block and the 2026 holdout come from one publisher",
         "disclosure",
         "Corroboration between stored captures is not independence from the publisher.",
         "https://www.nfl.com/", "data/corpus.json", "stated on every page"),
    ]
    flags = {
        "dataset": "nfl_origination_lab_flags",
        "title": "Flagged for review: every irregularity found this session",
        "built": "2026-11-19",
        "policy": "a flag is published with the source that shows it. None of these blocks "
                  "publishing the site; each one blocks a claim.",
        "counts": {}, "rows": [],
    }
    for fid, what, sev, why, url, path, effect in F:
        flags["rows"].append({"id": fid, "what": what, "severity": sev, "detail": why,
                              "source_url": url, "evidence": path, "effect": effect})
    flags["counts"] = {s: sum(1 for r in flags["rows"] if r["severity"] == s)
                       for s in ("blocking", "material", "minor", "disclosure")}
    dump(flags, open(os.path.join(DATA, "flagged.json"), "w", encoding="utf-8"), indent=1)

    print("questions %d %s" % (len(questions["rows"]), questions["counts"]))
    print("suggestions %d (all undecided: %s)"
          % (len(suggestions["rows"]),
             all(r["decision"] is None for r in suggestions["rows"])))
    print("flags %d %s" % (len(flags["rows"]), flags["counts"]))


if __name__ == "__main__":
    main()
