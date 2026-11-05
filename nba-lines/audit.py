#!/usr/bin/env python3
"""
Own4 / nba-lines — audit register (session arena-7a06a47e-own4).

Writes two registers that the Flagged-for-Review page renders verbatim:
  data/repo_review.json  — line-by-line review of the inherited repository
  data/flags.json        — every unverified, blank or provisional value

Every entry carries at least one link so a human can check it. Nothing in here
is a guess: each finding names the exact file or official page that shows it.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

REPO_REVIEW = [
    {
        "id": "R01", "severity": "high", "status": "flagged",
        "finding": "Eight separate NBA workspaces coexist with overlapping scope and no single canonical dataset.",
        "evidence": "docs/, lab/, lines-lab/, nba-evidence/, own4-dashboard/, pages/ + official/, research/ + data/, and the pre-existing root dashboard. 158 HTML pages in total.",
        "links": [
            {"label": "README.md (six different 'live' entry points)", "url": "https://github.com/sassnarep3-star/Own4/blob/main/README.md"},
            {"label": "COORDINATION.md", "url": "https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md"},
        ],
        "resolution": "This session publishes one canonical dashboard at /nba-lines/site/ and one clean root landing page; earlier workspaces are preserved and labelled, not deleted.",
    },
    {
        "id": "R02", "severity": "high", "status": "needs review",
        "finding": "Correlation coefficients are published for a 49,226 player-game dataset spanning 2010-11 to 2023-24, but that dataset is not in the repository and cannot be rebuilt from anything committed.",
        "evidence": "data/correlations_computed.json cites dataset_commit a5f108b5b1f08074d78b9e8e901926a9ce4c06c5 with n=49226. No file of that size or shape exists in the repo (largest data file: data/player_gamelogs.json, 2,509 rows).",
        "links": [
            {"label": "data/correlations_computed.json", "url": "https://github.com/sassnarep3-star/Own4/blob/main/data/correlations_computed.json"},
            {"label": "research/README.md", "url": "https://github.com/sassnarep3-star/Own4/blob/main/research/README.md"},
        ],
        "resolution": "Either commit the dataset with its licence, or withdraw the coefficients. This session does not rely on them: every correlation it publishes is recomputed from files committed here.",
    },
    {
        "id": "R03", "severity": "medium", "status": "resolved-by-gate",
        "finding": "The committed 'raw' nba.com pages cannot regenerate the results dataset: the server-rendered game cards contain empty score containers, so scores are only present after client-side rendering.",
        "evidence": "data/raw/nba/games_2026-11-01.html contains GameCardMatchup_matchupScoreCardWrapper with no score text, and MatchupCardTeamRecord_record rendered as '-'.",
        "links": [
            {"label": "data/raw/nba/ (committed captures)", "url": "https://github.com/sassnarep3-star/Own4/tree/main/data/raw/nba"},
            {"label": "Official games page", "url": "https://www.nba.com/games?date=2026-11-01"},
        ],
        "resolution": "Verification instead uses an aggregate reconciliation: the 121 committed finals reproduce all 30 official W-L records exactly (30/30, zero mismatches).",
    },
    {
        "id": "R04", "severity": "medium", "status": "needs review",
        "finding": "Several source manifest entries record HTTP 403 or timeouts against cdn.nba.com and stats.nba.com, yet parts of the documentation describe those endpoints as if they had been used.",
        "evidence": "data/manifest.json: scheduleLeagueV2 and todaysScoreboard_00 return 403; stats.nba.com leaguestandingsv3 returns TimeoutError; fetch.log repeats the failures.",
        "links": [
            {"label": "data/manifest.json", "url": "https://github.com/sassnarep3-star/Own4/blob/main/data/manifest.json"},
            {"label": "fetch.log", "url": "https://github.com/sassnarep3-star/Own4/blob/main/fetch.log"},
        ],
        "resolution": "Treat 403/timeout entries as failures, not as sources. This session records only pages it actually read.",
    },
    {
        "id": "R05", "severity": "high", "status": "needs review",
        "finding": "An automated collector downloaded roughly 47 MB of ESPN box-score JSON, which is in tension with the league's stated restriction on downloading its statistics, and ESPN is not the league.",
        "evidence": "data/raw/espn holds 121 JSON files (47 MB). The NBA Stats FAQ states the league's stats 'are not available for download for either academic or personal use'.",
        "links": [
            {"label": "NBA Stats FAQ (restriction)", "url": "https://www.nba.com/stats/help/faq"},
            {"label": "scripts/fetch_official.py", "url": "https://github.com/sassnarep3-star/Own4/blob/main/scripts/fetch_official.py"},
            {"label": "data/raw/espn/", "url": "https://github.com/sassnarep3-star/Own4/tree/main/data/raw/espn"},
        ],
        "resolution": "This session performs no automated league harvesting; its captures are 121 finals, 30 standings rows, 2 slate entries and 13 availability rows transcribed from displayed pages. Whether to keep the ESPN extract is a decision for the repository owner.",
    },
    {
        "id": "R06", "severity": "medium", "status": "needs review",
        "finding": "A workflow is hard-coded to another session's branch and therefore never runs against main; its commit step also rebases onto that dead branch.",
        "evidence": ".github/workflows/fetch-nba-data.yml pins ref and push targets to arena/75685c60-own4.",
        "links": [
            {"label": ".github/workflows/fetch-nba-data.yml", "url": "https://github.com/sassnarep3-star/Own4/blob/main/.github/workflows/fetch-nba-data.yml"},
        ],
        "resolution": "Repoint to main and add a licence/terms check before re-enabling, or disable it. Left untouched here because it is outside this session's file scope.",
    },
    {
        "id": "R07", "severity": "low", "status": "flagged",
        "finding": "Two different 'Flagged for Review' pages exist with different contents, so 'the flagged list' is ambiguous.",
        "evidence": "pages/flagged.html and pages/flagged-for-review.html.",
        "links": [
            {"label": "pages/flagged.html", "url": "https://sassnarep3-star.github.io/Own4/pages/flagged.html"},
            {"label": "pages/flagged-for-review.html", "url": "https://sassnarep3-star.github.io/Own4/pages/flagged-for-review.html"},
        ],
        "resolution": "The canonical flagged list for this session is /nba-lines/site/governance/flagged.html.",
    },
    {
        "id": "R08", "severity": "low", "status": "flagged",
        "finding": "The shared board records contradictory outcomes for the same pull request in two different session entries.",
        "evidence": "One entry states 'PR #5 merge was rejected as not cleanly mergeable'; a later entry in the same section states 'PR #5 merged during PR #4 checks'.",
        "links": [
            {"label": "COORDINATION.md", "url": "https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md"},
        ],
        "resolution": "Read the GitHub PR timeline, not the board, for merge state. This session appends its own record without altering earlier entries.",
    },
    {
        "id": "R09", "severity": "medium", "status": "resolved-by-gate",
        "finding": "data/signals.json attributes a computed home-win rate to the standings page, which is a provenance mislabel: a standings table does not contain per-game home/away outcomes.",
        "evidence": "data/signals.json item SIG-01 'Home win rate (2026-27 to date)' with value 0.5217, k=48, n=92, source_url https://www.nba.com/standings.",
        "links": [
            {"label": "data/signals.json", "url": "https://github.com/sassnarep3-star/Own4/blob/main/data/signals.json"},
        ],
        "resolution": "Computed values must cite the per-game source, not an aggregate page. This session cites the game page on every result row.",
    },
    {
        "id": "R10", "severity": "low", "status": "passes-internal-check",
        "finding": "The 2025-26 prior-season team table is a hand transcription; it passes internal consistency (30 teams, every GP=82, sum of plus-minus per game = -0.2) but was not re-read page by page in this session.",
        "evidence": "data/team_stats_2025-26.csv; engine.prior_check() result published in the verification report.",
        "links": [
            {"label": "data/team_stats_2025-26.csv", "url": "https://github.com/sassnarep3-star/Own4/blob/main/data/team_stats_2025-26.csv"},
            {"label": "Official 2025-26 team stats", "url": "https://www.nba.com/stats/teams/traditional?Season=2025-26"},
        ],
        "resolution": "Re-read and re-transcribe before relying on it for anything beyond a shrinkage prior.",
    },
    {
        "id": "R11", "severity": "medium", "status": "flagged",
        "finding": "Individual player game logs stop at 2026-11-01, so the player-level layer is three days stale relative to the 2026-11-05 slate.",
        "evidence": "data/player_gamelogs.json covers 13 dates, 2026-10-20 through 2026-11-01; the results set reaches 2026-11-04.",
        "links": [
            {"label": "data/player_gamelogs.json", "url": "https://github.com/sassnarep3-star/Own4/blob/main/data/player_gamelogs.json"},
        ],
        "resolution": "Props in this release are anchored on the official season averages from the slate page; the log layer is used only for volatility and correlation.",
    },
    {
        "id": "R12", "severity": "low", "status": "resolved-consistent",
        "finding": "Two rosters disagree with 2025-26 expectations (Giannis Antetokounmpo listed with Miami, Tyler Herro with Milwaukee). Checked rather than assumed: three independent official pages agree.",
        "evidence": "The 11/05 injury PDF lists Antetokounmpo under Miami Heat; the 11/02 recap lists Herro under MIL; the 11/05 slate card lists Antetokounmpo as MIA season leader.",
        "links": [
            {"label": "11/05 4:00 PM ET injury report", "url": "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-05_04_00PM.pdf"},
            {"label": "2026-11-02 games page", "url": "https://www.nba.com/games?date=2026-11-02"},
            {"label": "2026-11-05 slate", "url": "https://www.nba.com/games?date=2026-11-05"},
        ],
        "resolution": "Not an irregularity in this repo; recorded so a reader does not mistake it for a transcription error.",
    },
    {
        "id": "R13", "severity": "info", "status": "passes",
        "finding": "The inherited canonical site does pass its own link checker: 11 pages, 758 links, 438 table rows, 0 problems.",
        "evidence": "python3 scripts/check_site.py output, re-run during this review.",
        "links": [
            {"label": "scripts/check_site.py", "url": "https://github.com/sassnarep3-star/Own4/blob/main/scripts/check_site.py"},
        ],
        "resolution": "Recorded as a positive control: the earlier workspaces are internally consistent even where their claims are unverifiable.",
    },
    {
        "id": "R14", "severity": "low", "status": "flagged",
        "finding": "The overtime flag on inherited result rows is a transcription convention (blank means 'not marked OT on the page'), not an independently verified field.",
        "evidence": "data/games_2026-27.csv marks exactly 4 games 'OT' and leaves 88 blank; this session's 3 captured overtime finals are marked from pages that render 'Final/OT'.",
        "links": [
            {"label": "data/games_2026-27.csv", "url": "https://github.com/sassnarep3-star/Own4/blob/main/data/games_2026-27.csv"},
        ],
        "resolution": "Treat the column as informative only; it is never used as a model input.",
    },
    {
        "id": "R16", "severity": "high", "status": "needs review",
        "finding": "Two workspaces in the same repository publish opposite headline results for the same question. "
                   "The root executive summary reports 1 trial and 5 of 11 parlay constructions passing every gate; "
                   "the nba-evidence workspace reports zero qualified strategies and zero rewards; the lab reports "
                   "that no strategy passes its pre-registered gates.",
        "evidence": "EXECUTIVE_SUMMARY.md lines 10-11 vs nba-evidence/docs/EXECUTIVE_SUMMARY.md line 5 and "
                    "nba-evidence/README.md. The summary's inputs (4,144 holdout games, 10,327 dev games) are not "
                    "in the repository, so neither side of the contradiction can be adjudicated from committed data.",
        "links": [
            {"label": "EXECUTIVE_SUMMARY.md (root)", "url": "https://github.com/sassnarep3-star/Own4/blob/main/EXECUTIVE_SUMMARY.md"},
            {"label": "nba-evidence/docs/EXECUTIVE_SUMMARY.md", "url": "https://github.com/sassnarep3-star/Own4/blob/main/nba-evidence/docs/EXECUTIVE_SUMMARY.md"},
            {"label": "lab/ dashboard", "url": "https://sassnarep3-star.github.io/Own4/lab/"},
        ],
        "resolution": "This session's summary replaces the root file with a canonical, reproducible result and "
                      "retains the earlier text verbatim in an appendix labelled superseded. The contradiction is "
                      "recorded rather than silently resolved: the earlier claim cannot be verified because its "
                      "dataset is absent.",
    },
    {
        "id": "R15", "severity": "info", "status": "passes",
        "finding": "The board already contains a documented self-correction of a doubled '/site/site/' publication path, and the corrected path resolves.",
        "evidence": "Closing entry of session 91dfd6a4 records the correction to /nba-evidence/site/.",
        "links": [
            {"label": "nba-evidence dashboard", "url": "https://sassnarep3-star.github.io/Own4/nba-evidence/site/"},
            {"label": "COORDINATION.md", "url": "https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md"},
        ],
        "resolution": "No action; recorded so this review is not silent about it.",
    },
]

FLAGS = [
    {
        "id": "F01", "severity": "blocking-for-rewards", "theme": "Market prices",
        "item": "No official or verifiable price archive exists in this repository, so no expected value, ROI or closing-line value can be computed.",
        "why_blank": "A model's own fair line is not a market price; comparing it to itself is circular.",
        "links": [
            {"label": "NBA Stats FAQ (no download; no odds product)", "url": "https://www.nba.com/stats/help/faq"},
        ],
        "resolution": "Ingest a licensed historical price feed with timestamps, then re-run gate G9.",
    },
    {
        "id": "F02", "severity": "blocking-for-rewards", "theme": "Sample size",
        "item": "96 graded out-of-sample predictions, against a pre-registered requirement of 300.",
        "why_blank": "Skill estimates on 96 games have confidence intervals roughly ±0.15 wide.",
        "links": [{"label": "Validation gates", "url": "https://sassnarep3-star.github.io/Own4/nba-lines/site/research/gates.html"}],
        "resolution": "Continue grading nightly; the 2026-27 season reaches 300 graded games around mid-December.",
    },
    {
        "id": "F03", "severity": "needs review", "theme": "Calibration",
        "item": "Expected calibration error is 0.104 against a 0.05 gate, although the reliability slope is 0.90 (inside [0.80, 1.20]).",
        "why_blank": "Probabilities are under-confident at the extremes; the gate is not met and no reward is claimed.",
        "links": [{"label": "Calibration method", "url": "https://scikit-learn.org/stable/modules/calibration.html"}],
        "resolution": "Fit an isotonic or Platt calibration step on a locked holdout and re-test.",
    },
    {
        "id": "F04", "severity": "needs review", "theme": "Model estimate",
        "item": "Estimated home-court advantage is 1.11 points on 121 games. The repository's own 2025-26 table implies 1.725 points per game over 1,225 home games, so the 2026-27 estimate is low but not outlandish.",
        "why_blank": "The value is reported as computed and treated as provisional. No long-run league norm is asserted because no official source publishes one; the only comparison offered is internally derived and labelled as such.",
        "links": [{"label": "Official standings (used for reconciliation)", "url": "https://www.nba.com/standings"}],
        "resolution": "Re-estimate after ~400 games or with multiple seasons of official finals.",
    },
    {
        "id": "F05", "severity": "needs review", "theme": "Player props",
        "item": "Prop probabilities use a normal approximation centred on the player's official season average, scaled by a pooled within-player residual standard deviation.",
        "why_blank": "Player-specific variance is not estimable: the four players on tonight's slate have 4-6 logged games each.",
        "links": [{"label": "Official slate + season leaders", "url": "https://www.nba.com/games?date=2026-11-05"}],
        "resolution": "Requires player-level logs over a full season, from an official or licensed source.",
    },
    {
        "id": "F06", "severity": "needs review", "theme": "Player props",
        "item": "The pooled residual distributions behind the prop bands come from a partner-sourced sample of 92 games (2026-10-20 to 2026-11-01), not from league data.",
        "why_blank": "The league does not offer downloadable statistics; the alternative source is flagged as tier-2.",
        "links": [
            {"label": "NBA Stats FAQ", "url": "https://www.nba.com/stats/help/faq"},
            {"label": "data/player_gamelogs.json", "url": "https://github.com/sassnarep3-star/Own4/blob/main/data/player_gamelogs.json"},
        ],
        "resolution": "Replace with licensed play-by-play or official per-player logs.",
    },
    {
        "id": "F07", "severity": "needs review", "theme": "Correlations",
        "item": "Player-level correlations (PTS/REB, PTS/AST, REB/AST, teammate stacking) are computed from partner-sourced rows, not league-official rows.",
        "why_blank": "League box scores are viewable but not downloadable per the FAQ; only the team-market correlations use league-official finals.",
        "links": [
            {"label": "NBA Stats FAQ", "url": "https://www.nba.com/stats/help/faq"},
            {"label": "NBA stat glossary (definitions)", "url": "https://www.nba.com/stats/help/glossary"},
        ],
        "resolution": "Recompute from licensed box scores; the estimator is already in engine.py.",
    },
    {
        "id": "F08", "severity": "do-not-use", "theme": "Correlations",
        "item": "Teammate points correlation is -0.139 (95% CI -0.278 to 0.006, p=0.060, BH q=0.075) — not significant.",
        "why_blank": "A negative teammate correlation is the expected usage trade-off, but this sample cannot establish it; the S11 stack strategy is therefore ungraded.",
        "links": [{"label": "BH-FDR method (publisher record)", "url": "https://doi.org/10.1111/j.2517-6161.1995.tb02031.x"}],
        "resolution": "More games; a full season gives roughly 2,460 team-games and a usable CI.",
    },
    {
        "id": "F09", "severity": "needs review", "theme": "Parlays",
        "item": "Cross-game legs are priced as independent. A same-day probe gives r=0.184 (p=0.059, q=0.075) between consecutive games' totals, which does not reject independence but does not confirm it either.",
        "why_blank": "No verified mechanism for cross-game dependence was found in official material.",
        "links": [{"label": "Official games index", "url": "https://www.nba.com/games"}],
        "resolution": "Test with a larger same-day sample; if dependence is real, price cross-game parlays with it.",
    },
    {
        "id": "F10", "severity": "informational", "theme": "Availability",
        "item": "The 11/05 4:00 PM ET report is a point-in-time snapshot; 17 team entries for the 11/06 games read NOT YET SUBMITTED.",
        "why_blank": "Statuses change up to tip-off; no later edition was read for this release.",
        "links": [
            {"label": "Injury report policy + index", "url": "https://official.nba.com/nba-injury-report-2026-27-season/"},
            {"label": "11/05 4:00 PM ET PDF", "url": "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-05_04_00PM.pdf"},
        ],
        "resolution": "Read the last pre-tip edition before using any status.",
    },
    {
        "id": "F11", "severity": "informational", "theme": "Prior season",
        "item": "The 2025-26 prior-season team table was inherited, not re-read this session.",
        "why_blank": "It passes internal checks (30 teams, GP=82 each, plus-minus sums to -0.2) but internal consistency is not external verification.",
        "links": [{"label": "Official 2025-26 team stats", "url": "https://www.nba.com/stats/teams/traditional?Season=2025-26"}],
        "resolution": "Re-transcribe from the official page and diff before the next release.",
    },
    {
        "id": "F12", "severity": "informational", "theme": "Player props",
        "item": "Official season-leader figures are published for only the four players the league displays on each game card.",
        "why_blank": "No official per-player season average is published on the pages read for any other player on these two teams.",
        "links": [{"label": "2026-11-05 slate", "url": "https://www.nba.com/games?date=2026-11-05"}],
        "resolution": "Read the official players pages for full rosters if wider prop coverage is required.",
    },
    {
        "id": "F13", "severity": "do-not-use", "theme": "Lineups",
        "item": "Starting lineups and minutes projections are unavailable from the pages read.",
        "why_blank": "Pre-game official pages show availability status, not lineups.",
        "links": [{"label": "Injury report index", "url": "https://official.nba.com/nba-injury-report-2026-27-season/"}],
        "resolution": "Needs an official or licensed lineup feed.",
    },
    {
        "id": "F14", "severity": "not-implemented", "theme": "Strategy",
        "item": "S12 (opponent-adjusted props) is specified but not implemented: it needs possession-level pace and defensive data.",
        "why_blank": "Pace/possession tables on stats.nba.com are viewable but the FAQ forbids downloading them, and no other official pace product was read.",
        "links": [{"label": "NBA Stats FAQ", "url": "https://www.nba.com/stats/help/faq"}],
        "resolution": "Implement only with licensed data; keep the strategy ungraded until then.",
    },
    {
        "id": "F15", "severity": "informational", "theme": "PRA markets",
        "item": "The league states that a combined PTS+REB+AST statistic is unavailable on its stats site, so a PRA market price must be constructed by the operator.",
        "why_blank": "Because operators construct it themselves, settlement rules differ and no single official rule was verified here.",
        "links": [{"label": "NBA Stats FAQ (combined PTS+REB+AST)", "url": "https://www.nba.com/stats/help/faq"}],
        "resolution": "Verify the specific operator's settlement rules before pricing a PRA market.",
    },
    {
        "id": "F16", "severity": "informational", "theme": "Overtime",
        "item": "The overtime column on inherited rows encodes 'not marked OT', not a verified 'no overtime'.",
        "why_blank": "The transcription convention is not an independent observation.",
        "links": [{"label": "data/games_2026-27.csv", "url": "https://github.com/sassnarep3-star/Own4/blob/main/data/games_2026-27.csv"}],
        "resolution": "Re-derive from final scores versus regulation expectations if it ever becomes a model input.",
    },
    {
        "id": "F17", "severity": "informational", "theme": "Data terms",
        "item": "All league values in this release come from reading publicly displayed pages; the league's FAQ states its stats are not available for download for academic or personal use.",
        "why_blank": "The volume here is tiny (121 finals, 30 standings rows, 2 slate entries, 13 availability rows) but the restriction still governs any future automated collection.",
        "links": [{"label": "NBA Stats FAQ", "url": "https://www.nba.com/stats/help/faq"}],
        "resolution": "Obtain a licence before any bulk collection; keep the manual-transcription discipline otherwise.",
    },
    {
        "id": "F18", "severity": "not-implemented", "theme": "Rewards",
        "item": "No monetary reward is funded or awarded. Reward points are defined but nobody is eligible.",
        "why_blank": "Eligibility requires gates G3, G4, G5, G8 and G9 together; three of those fail.",
        "links": [{"label": "Leaderboard", "url": "https://sassnarep3-star.github.io/Own4/nba-lines/site/competition/leaderboard.html"}],
        "resolution": "Rewards activate only after every gate passes; the policy is pre-registered so it cannot be relaxed after the fact.",
    },
]


def main():
    with open(os.path.join(DATA, "repo_review.json"), "w", encoding="utf-8") as fh:
        json.dump({"compiled_at": "2026-11-05", "compiled_by": "session arena-7a06a47e-own4",
                   "scope": "Every finding was produced by reading the committed files or the linked official page during this session.",
                   "rows": REPO_REVIEW}, fh, indent=1)
    with open(os.path.join(DATA, "flags.json"), "w", encoding="utf-8") as fh:
        json.dump({"compiled_at": "2026-11-05", "compiled_by": "session arena-7a06a47e-own4",
                   "policy": "Unverifiable values are left blank on the site and listed here with the reason and a source link. Flagged items do not block publication.",
                   "rows": FLAGS}, fh, indent=1)
    print(f"repo_review: {len(REPO_REVIEW)} findings; flags: {len(FLAGS)}")


if __name__ == "__main__":
    main()
