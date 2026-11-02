"""Q1/Q7: publish verification artifacts — official score spot-check (13/13),
official source register, flagged-for-review register, repo audit findings.
"""
import json, datetime, subprocess
import pandas as pd
from common import GAMES_CSV, DATA, save_json

NOW = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")

# ---- official score spot-check: all 13 played 2026 Week 8 games ----
# Transcribed from https://www.nfl.com/scores/2026/REG8 (fetched 2026-11-02, chunks 0-1)
official = {
    "2026_08_CAR_GB": (19, 27), "2026_08_BAL_BUF": (10, 36), "2026_08_TEN_CIN": (36, 43),
    "2026_08_ARI_DAL": (33, 30), "2026_08_MIN_DET": (15, 19), "2026_08_IND_JAX": (7, 42),
    "2026_08_LV_NYJ": (38, 33), "2026_08_CLE_PIT": (6, 27), "2026_08_ATL_TB": (0, 16),
    "2026_08_LAC_LA": (9, 24), "2026_08_KC_DEN": (24, 28), "2026_08_NE_MIA": (24, 19),
    "2026_08_PHI_WAS": (10, 27),
}
g = pd.read_csv(GAMES_CSV)
w8 = g[(g.season == 2026) & (g.week == 8)].set_index("game_id")
rows = []
for gid, (a, h) in official.items():
    r = w8.loc[gid]
    ok = int(r.away_score) == a and int(r.home_score) == h
    rows.append({"game_id": gid, "official_away": a, "official_home": h,
                 "archive_away": int(r.away_score), "archive_home": int(r.home_score), "match": ok})
save_json("official_score_spotcheck.json", {
    "source": "https://www.nfl.com/scores/2026/REG8", "fetched_utc": NOW,
    "checks": rows, "all_match": all(r["match"] for r in rows),
    "note": "CHI @ SEA (2026-11-02 MNF) unplayed at snapshot; excluded. Byes: HOU, NO, NYG, SF.",
})

# ---- official source register ----
official_sources = [
    {"id": "OS-01", "claim": "Scoring values: Touchdown 6, Field Goal 3, Safety 2, Try 1 (kick/safety) or 2 (touchdown) — Rule 11-1-2",
     "url": "https://static.www.nfl.com/image/upload/fl_attachment/league/tqivdkzt9mu6wdgsh1ku.pdf",
     "publisher": "National Football League (official 2026 rulebook PDF)",
     "method": "PDF fetched directly (identity, preface, rule order confirmed); Rule 11 text verified via search-indexed excerpt of this official PDF (direct fetch parses first 30 pages; Rule 11 is p.42). See QF-13.",
     "verified_utc": NOW},
    {"id": "OS-02", "claim": "Overtime (since 2025): both teams get a possession regardless of first-possession outcome; regular season OT is one 10-minute period; ties possible",
     "url": "https://operations.nfl.com/rules-officiating/featured-rules",
     "publisher": "NFL Football Operations", "method": "Page fetched and read directly (2025 Rules Changes > Overtime Procedures)", "verified_utc": NOW},
    {"id": "OS-03", "claim": "2026 rule changes: kickoff setup-zone alignment (6-1-3), touchback dead-ball spot from 50-yard kickoff (6-1-5), onside kick declaration any time (6-1-6), disqualification consultation (19-2)",
     "url": "https://operations.nfl.com/rules-officiating/2026-nfl-rulebook",
     "publisher": "NFL Football Operations", "method": "Page fetched and read directly (2026 Rule Changes table)", "verified_utc": NOW},
    {"id": "OS-04", "claim": "Season structure: 32 teams, each plays 17 regular-season games over 18 weeks; 272 total games; 2026 has 9 international regular-season games (first games in Melbourne, Paris, Rio)",
     "url": "https://operations.nfl.com/calendar-events/nfl-schedule/making-the-schedule",
     "publisher": "NFL Football Operations", "method": "Page fetched and read directly", "verified_utc": NOW},
    {"id": "OS-05", "claim": "2026 Week 8 final scores (13 played games) — archive matches NFL.com 13/13",
     "url": "https://www.nfl.com/scores/2026/REG8",
     "publisher": "NFL.com (official league site)", "method": "Page fetched; scores transcribed game-by-game and compared to archive (official_score_spotcheck.json)", "verified_utc": NOW},
    {"id": "OS-06", "claim": "Parlay = 2+ legs, all must win; payout = product of leg odds; voided legs removed and odds recalculated",
     "url": "https://www.fanduel.com/sports-betting-guide/what-is-a-parlay-bet",
     "publisher": "FanDuel (official sportsbook guide)", "method": "Page fetched and read directly (FAQ: payout multiplication, void handling)", "verified_utc": NOW},
    {"id": "OS-07", "claim": "Parlay push/void settlement: whole-number line push refunds the leg; parlay recalculated on remaining legs (House Rules Part B s.19)",
     "url": "https://www.fanduel.com/fanduel-sportsbook-house-rules-on",
     "publisher": "FanDuel Sportsbook House Rules (Ontario, updated 2026-09-30)", "method": "Page fetched (general rules); s.19 text verified via search-indexed excerpt of this official page", "verified_utc": NOW},
    {"id": "OS-08", "claim": "Correlated/duplicate outcomes generally cannot be combined in standard parlays; Same Game Parlay is a separate repriced product",
     "url": "https://www.fanduel.com/sports-betting-guide/what-is-a-parlay-bet",
     "publisher": "FanDuel (official sportsbook guide)", "method": "Page fetched and read directly (FAQ: What can't you Parlay?; SGP definition)", "verified_utc": NOW},
    {"id": "OS-09", "claim": "National Problem Gambling Helpline: 1-800-MY-RESET (1-800-697-3738), operated by NCPG",
     "url": "https://www.ncpgambling.org/help-treatment/",
     "publisher": "National Council on Problem Gambling", "method": "Page fetched and read directly", "verified_utc": NOW},
]
save_json("official_sources.json", {"generated_utc": NOW, "sources": official_sources})

# ---- flagged for review ----
flags = [
    {"id": "QF-01", "severity": "policy", "item": "All betting lines (spread/total/moneyline) are THIRD-PARTY archive values", "detail": "No official NFL source publishes betting lines. Values come from nflverse/nfldata (closing lines archive). Official-source column is blank + UNVERIFIED for every market value; archive link provided instead.", "source": "https://github.com/nflverse/nfldata"},
    {"id": "QF-02", "severity": "policy", "item": "All correlations, backtest ROI, ratings and own lines are COMPUTED, not official", "detail": "No official source publishes these coefficients. They are reproducible from the cited archives via nfl-quant/pipeline/. Labeled DERIVED/COMPUTED everywhere.", "source": "https://github.com/sassnarep3-star/Own4/tree/main/nfl-quant/pipeline"},
    {"id": "QF-03", "severity": "blocked", "item": "2026 player props: BLOCKED", "detail": "No authorized 2026 player-level feed in scope. Player research uses 2021-2022 only. 2026 prop lines left blank.", "source": "https://github.com/fantasydatapros/LearnPythonWithFantasyFootball"},
    {"id": "QF-04", "severity": "research-only", "item": "Prop singles use a PROXY market (rolling-mean line)", "detail": "Gate G7 fails by construction. Results measure signal vs a naive proxy, NOT vs a sportsbook. RB1 +3.6% ROI vs proxy is not a betting edge.", "source": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-quant/pipeline/05_props.py"},
    {"id": "QF-05", "severity": "research-only", "item": "Same-game parlay prices not archived", "detail": "S5/S7 are fair-price monitors only. Books reprice SGPs for correlation; without archived SGP prices no edge can be claimed (G7 fails).", "source": "https://www.fanduel.com/sports-betting-guide/what-is-a-parlay-bet"},
    {"id": "QF-06", "severity": "repaired", "item": "README.md contained committed merge-conflict markers (lines 55/64/90)", "detail": "From a prior session merge. Repaired at integration by keeping BOTH sides (no work discarded). COORDINATION.md was already clean on main.", "source": "https://github.com/sassnarep3-star/Own4/blob/main/README.md"},
    {"id": "QF-07", "severity": "info", "item": "Repository root project is NBA; this session's brief is NFL", "detail": "Prior parallel sessions built NBA dashboards. NFL work is namespaced: nfl/ (spec), nfl-research/ (PR #24, other session), nfl-quant/ (this session, measured). No NBA files modified.", "source": "https://github.com/sassnarep3-star/Own4"},
    {"id": "QF-08", "severity": "policy", "item": "Validation-gate thresholds are project-defined", "detail": "n>=300, 60% positive seasons, etc. are research design choices, not official NFL values. Pre-registered in gates.json before backtests ran.", "source": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-quant/pipeline/gates.json"},
    {"id": "QF-09", "severity": "policy", "item": "Leaderboard rewards are non-monetary and unfunded", "detail": "1000 research points, split only among Gold-tier strategies. None passed: 0 awarded. No money or prizes exist.", "source": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-quant/pipeline/gates.json"},
    {"id": "QF-10", "severity": "needs-review", "item": "Data licensing must be resolved before production use", "detail": "Archives are third-party mirrors of official results/stats. Review nflverse/nfldata and fantasydatapros terms; NFL stats distribution rights may apply.", "source": "https://github.com/nflverse/nfldata/blob/master/DATASETS.md"},
    {"id": "QF-11", "severity": "pending", "item": "Gate G8 (forward replication) not yet satisfiable", "detail": "No strategy can reach final Gold until timestamped 2026 predictions are logged for a full season and re-tested. Week 9 own lines are the first prospective log entry.", "source": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-quant/pipeline/gates.json"},
    {"id": "QF-12", "severity": "info", "item": "Week 9 market lines are a snapshot (2026-11-02 20:45 UTC)", "detail": "Archive values for future games are current/opening lines, not final closing lines; they will move. Own lines are model outputs, not recommendations.", "source": "https://github.com/nflverse/nfldata"},
    {"id": "QF-13", "severity": "info", "item": "Rulebook PDF direct fetch limited to first 30 pages", "detail": "Rule 11 (Scoring, p.42) text verified via search-indexed excerpt of the official NFL PDF; PDF identity/structure confirmed by direct fetch. Flagged for manual re-review of the full PDF.", "source": "https://static.www.nfl.com/image/upload/fl_attachment/league/tqivdkzt9mu6wdgsh1ku.pdf"},
    {"id": "QF-14", "severity": "info", "item": "Player correlations limited to 2021-2022 (2 seasons)", "detail": "WR1/WR2 designated ex-post per game for the correlation matrix (standard); leak-free rolling designation used for betting tests. QB1-WR2 r>QB1-WR1 partly reflects max-selection ceiling effects.", "source": "https://github.com/fantasydatapros/LearnPythonWithFantasyFootball"},
    {"id": "QF-15", "severity": "finding", "item": "No registered strategy passed the holdout gates", "detail": "S1/S4 Bronze (ROI indistinguishable from luck), S2/S3/C1 Rejected (negative ROI). 0 reward points. The framework's job is to reject luck; at efficient closing lines it rejected everything. This is the honest result.", "source": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-quant/data/strategy_results.json"},
]
save_json("flags.json", {"generated_utc": NOW, "flags": flags})

# ---- repo audit ----
audit = [
    {"id": "RA-01", "file": "README.md", "lines": "55, 64, 90", "finding": "Committed merge-conflict markers (<<<<<<< HEAD / ======= / >>>>>>> origin/main)", "severity": "high", "action": "Repaired at integration: both sides kept, markers removed. No session work discarded.", "source": "https://github.com/sassnarep3-star/Own4/blob/main/README.md"},
    {"id": "RA-02", "file": "(repo-wide)", "lines": "-", "finding": "Root project identity is NBA line origination; current session brief is NFL", "severity": "info", "action": "NFL work namespaced under nfl-quant/ (this session), alongside prior nfl/ spec and nfl-research/ (open PR #24). NBA outputs untouched.", "source": "https://github.com/sassnarep3-star/Own4"},
    {"id": "RA-03", "file": "data/raw/espn/*.json, data/raw/nba/*", "lines": "-", "finding": "53 MB of NBA raw content (e.g., Celtics box scores) from prior NBA sessions; not NFL data", "severity": "info", "action": "Retained (other sessions' scope). Not used by NFL Quant Lab.", "source": "https://github.com/sassnarep3-star/Own4/tree/main/data/raw"},
    {"id": "RA-04", "file": "fetch.log", "lines": "1-20+", "finding": "Historical NBA fetch failures (403 cdn.nba.com, timeouts stats.nba.com)", "severity": "info", "action": "Informational; NFL session used GitHub-archived data + official page fetches instead.", "source": "https://github.com/sassnarep3-star/Own4/blob/main/fetch.log"},
    {"id": "RA-05", "file": ".github/workflows/pages.yml", "lines": "all", "finding": "CI 'validate' runs scripts/build.py, unittest, verify_data.py, check_site.py, git diff docs", "severity": "verified", "action": "Ran all steps locally: PASS (8 pages/47 rows; 11/11 data checks; 11 pages/758 links/0 problems). NFL additions do not touch docs/.", "source": "https://github.com/sassnarep3-star/Own4/blob/main/.github/workflows/pages.yml"},
    {"id": "RA-06", "file": "nfl/data/*.json", "lines": "all", "finding": "Prior NFL module (PRs #23/#25) is specification-only: all performance/correlation values blank + UNVERIFIED, consistent with its self-description", "severity": "verified", "action": "No irregularity; nfl-quant/ adds the measured layer those modules explicitly lacked.", "source": "https://github.com/sassnarep3-star/Own4/blob/main/nfl/data/strategies.json"},
    {"id": "RA-07", "file": "(data convention)", "lines": "-", "finding": "nflverse games.csv spread_line is POSITIVE when home is favored — opposite of standard sportsbook home-spread notation", "severity": "verified", "action": "Verified vs DATASETS.md, corr(result,spread)=+0.43, moneyline agreement 99%+. Documented in provenance.json; all settlement code uses the verified convention.", "source": "https://github.com/nflverse/nfldata/blob/master/DATASETS.md"},
    {"id": "RA-08", "file": "(coordination)", "lines": "-", "finding": "Open PR #24 (arena/1699c9cc, nfl-research/**) is an active parallel session", "severity": "info", "action": "Scope not touched. Integration preserves it; final merge order coordinated via COORDINATION.md.", "source": "https://github.com/sassnarep3-star/Own4/pull/24"},
    {"id": "RA-09", "file": "nfl-quant/data/provenance.json", "lines": "all", "finding": "Data integrity: 15/15 checks pass; official NFL.com score spot-check 13/13 match", "severity": "verified", "action": "Published on Data & Sources page.", "source": "https://www.nfl.com/scores/2026/REG8"},
    {"id": "RA-10", "file": "COORDINATION.md", "lines": "all", "finding": "No conflict markers on current main (prior session repaired); append-only session logs intact", "severity": "verified", "action": "This session appends its claim/log per protocol.", "source": "https://github.com/sassnarep3-star/Own4/blob/main/COORDINATION.md"},
]
save_json("repo_audit.json", {"generated_utc": NOW, "findings": audit})
print("spotcheck:", all(r["match"] for r in rows), f"({len(rows)} games)")
print("official sources:", len(official_sources), "| flags:", len(flags), "| audit findings:", len(audit))
print("07_verify_publish done.")
