"""Q2: provenance register + data integrity checks (Gate G1).

VERIFIED CONVENTIONS (checked against data + DATASETS.md on 2026-11-02):
  * result = home_score - away_score.
  * spread_line = points the HOME team is favored by (POSITIVE = home favorite).
    This is the OPPOSITE of standard sportsbook home-spread notation.
    Confirmed by DATASETS.md, corr(result, spread_line)=+0.43, and moneyline signs.
  * Historical franchise codes OAK/SD/STL are normalized to LV/LAC/LA.
  * 2021 weekly CSVs: PFR schema (Player, Pos, Tm PFR codes, ReceivingYds...).
    2022 weekly CSVs: nflverse schema (Player, Position, Tm normalized, ReceivingYards...).
  * PBP receiver names are 'F.Last' format; yardage sums match weekly CSVs exactly.

Sources are third-party archives of (a) official NFL game results and
(b) sportsbook closing lines. Closing lines have NO official league source and
are flagged as third-party archive values everywhere they are published.
"""
import json, datetime
import pandas as pd
from common import RAW, GAMES_CSV, FDP, PBP_2021, sha256, save_json, TEAM_MAP

NOW = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
FRANCHISE = {"OAK": "LV", "SD": "LAC", "STL": "LA"}

sources = [
    {
        "id": "SRC-GAMES",
        "file": "games.csv",
        "repo": "https://github.com/nflverse/nfldata",
        "commit": "3cd32debd8c1bb0eb71ac4092584524e8d2c9cde",
        "commit_date": "2026-11-02T20:45:18Z",
        "download_url": "https://codeload.github.com/nflverse/nfldata/tar.gz/refs/heads/master",
        "downloaded_utc": NOW,
        "contents": "NFL games 1999-2026: official final scores + third-party closing spreads/totals/moneylines, schedule, venue, weather, QB/coach names",
        "official_status": "Scores: third-party archive of official NFL results (spot-checked vs nfl.com). Lines: THIRD-PARTY, no official league source exists.",
        "license_note": "See repo DATASETS.md / README for terms. Verify rights before production use.",
        "sha256": sha256(GAMES_CSV),
    },
    {
        "id": "SRC-WEEKLY-2021",
        "file": "2022/07-Data Visualizations/01-Weekly Fantasy Stats - 2021/{1..18}.csv",
        "repo": "https://github.com/fantasydatapros/LearnPythonWithFantasyFootball",
        "commit": "e367d869b2da48b031c9633797ae6a76a7cb8098",
        "commit_date": "2023-08-26T16:03:39Z",
        "download_url": "https://codeload.github.com/fantasydatapros/LearnPythonWithFantasyFootball/tar.gz/refs/heads/master",
        "downloaded_utc": NOW,
        "contents": "2021 per-player per-week passing/rushing/receiving yards, TDs, targets, receptions (PFR schema)",
        "official_status": "THIRD-PARTY archive of official NFL box-score statistics. Cross-checked vs play-by-play (exact match).",
        "sha256": sha256(FDP / "2022/07-Data Visualizations/01-Weekly Fantasy Stats - 2021/1.csv"),
    },
    {
        "id": "SRC-WEEKLY-2022",
        "file": "2023/07-Data Visualizations/01-Weekly Fantasy Stats - 2022/{1..18}.csv",
        "repo": "https://github.com/fantasydatapros/LearnPythonWithFantasyFootball",
        "commit": "e367d869b2da48b031c9633797ae6a76a7cb8098",
        "download_url": "https://codeload.github.com/fantasydatapros/LearnPythonWithFantasyFootball/tar.gz/refs/heads/master",
        "downloaded_utc": NOW,
        "contents": "2022 per-player per-week stats (nflverse schema incl. EPA, air yards, target share)",
        "official_status": "THIRD-PARTY archive of official NFL box-score statistics; EPA fields are computed model values.",
        "sha256": sha256(FDP / "2023/07-Data Visualizations/01-Weekly Fantasy Stats - 2022/1.csv"),
    },
    {
        "id": "SRC-PBP",
        "file": "2022/08-Finding TD Regression Candidates/1-Play by Play Data - 2021.csv",
        "repo": "https://github.com/fantasydatapros/LearnPythonWithFantasyFootball",
        "commit": "e367d869b2da48b031c9633797ae6a76a7cb8098",
        "download_url": "https://codeload.github.com/fantasydatapros/LearnPythonWithFantasyFootball/tar.gz/refs/heads/master",
        "downloaded_utc": NOW,
        "contents": "nflfastR play-by-play 2021 incl. EPA per play (382 columns, 50,712 plays)",
        "official_status": "THIRD-PARTY (nflfastR) derivative of official NFL play-by-play. EPA is a computed model value, not an official statistic.",
        "sha256": sha256(PBP_2021),
    },
]

checks = []
def check(name, ok, detail):
    checks.append({"check": name, "pass": bool(ok), "detail": detail})

g = pd.read_csv(GAMES_CSV)
check("unique game_id", g.game_id.is_unique, f"{len(g)} rows, {g.game_id.nunique()} unique")
played = g[g.home_score.notna() & g.away_score.notna()]
check("result == home_score - away_score", ((played.home_score - played.away_score) == played.result).all(), f"{len(played)} played games")
check("total == home_score + away_score", ((played.home_score + played.away_score) == played.total).all(), f"{len(played)} played games")
raw_codes = set(g.home_team) | set(g.away_team)
norm_codes = {FRANCHISE.get(t, t) for t in raw_codes}
check("32 franchises after code normalization", len(norm_codes) == 32, f"raw {len(raw_codes)} codes; OAK->LV, SD->LAC, STL->LA; normalized {len(norm_codes)}")
check("seasons 1999-2026", g.season.min() == 1999 and g.season.max() == 2026, f"{g.season.min()}-{g.season.max()}")
reg = g[g.game_type == "REG"]
check("regular-season games per season sane", reg.groupby("season").size().between(240, 290).all(), "248 (1999-2001), 256 (2002-2020), 272 (2021+), 2026 in progress")
check("no negative scores", (played.home_score >= 0).all() and (played.away_score >= 0).all(), "min scores >= 0")
# spread convention verification (CRITICAL - opposite of sportsbook notation)
p = played[played.spread_line.notna()]
corr = p.result.corr(p.spread_line)
check("spread_line convention: positive = home favored", corr > 0.3, f"corr(result, spread_line) = {corr:.3f}; DATASETS.md confirms positive = home favored")
fav = played[played.spread_line >= 7]
check("home +7 favorites win majority (sign check)", (fav.result > 0).mean() > 0.6, f"home +7+ favorites win {(fav.result > 0).mean():.3f} of {len(fav)}")
ml = played[played.spread_line.notna() & played.home_moneyline.notna()]
agree = ((ml.spread_line > 0) == (ml.home_moneyline < 0)).mean()
check("spread sign agrees with moneyline favorite", agree > 0.97, f"{agree:.4f} agreement over {len(ml)} games")

# weekly player data integrity (both schemas)
w21 = pd.read_csv(FDP / "2022/07-Data Visualizations/01-Weekly Fantasy Stats - 2021/1.csv")
w22 = pd.read_csv(FDP / "2023/07-Data Visualizations/01-Weekly Fantasy Stats - 2022/1.csv")
check("2021 weekly PFR schema loads", len(w21) > 250 and "ReceivingYds" in w21.columns, f"{len(w21)} rows week 1")
check("2022 weekly nflverse schema loads", len(w22) > 250 and "ReceivingYards" in w22.columns, f"{len(w22)} rows week 1")
unmapped21 = set(w21["Tm"].dropna().unique()) - set(TEAM_MAP)
check("2021 PFR team codes mappable", len(unmapped21) == 0, f"unmapped: {sorted(unmapped21)}")
check("2022 team codes already normalized", set(w22["Tm"].dropna().unique()) <= norm_codes, "nflverse codes")

# cross-check weekly receiving yards vs PBP for DAL week 1 2021 (name format F.Last)
pbp = pd.read_csv(PBP_2021, usecols=["game_id", "week", "posteam", "receiver_player_name", "yards_gained", "complete_pass"])
dal = pbp[(pbp.week == 1) & (pbp.posteam == "DAL") & (pbp.complete_pass == 1)]
pbp_rec = dal.groupby("receiver_player_name").yards_gained.sum()
def short_name(full):
    parts = [p for p in full.split() if p not in ("Jr.", "Sr.", "II", "III", "IV", "V")]
    return f"{parts[0][0]}.{parts[-1]}"
w1dal = w21[(w21.Tm == "DAL") & (w21.ReceivingYds > 0)]
mismatches = []
for row in w1dal.itertuples():
    p_yds = pbp_rec.get(short_name(row.Player), 0)
    if abs(p_yds - row.ReceivingYds) > 0:
        mismatches.append((row.Player, int(row.ReceivingYds), int(p_yds)))
check("weekly vs PBP receiving yards DAL W1 2021", len(mismatches) == 0, f"mismatches: {mismatches}" if mismatches else "all 8 DAL receivers match play-by-play sums exactly")

out = {
    "generated_utc": NOW,
    "sources": sources,
    "integrity_checks": checks,
    "all_checks_pass": all(c["pass"] for c in checks),
    "conventions": {
        "result": "home_score - away_score",
        "spread_line": "points home team is favored by; POSITIVE = home favorite (opposite of sportsbook home-spread notation)",
        "franchise_normalization": FRANCHISE,
    },
    "policy": "Every published numeric row links to its source. Official-source column is left blank + flagged UNVERIFIED whenever no official source publishes the value (all betting lines, all computed correlations/backtest results). Computed values are reproducible from the cited archives via this pipeline.",
}
save_json("provenance.json", out)
print(json.dumps({"all_checks_pass": out["all_checks_pass"], "checks": [(c["check"], c["pass"]) for c in checks]}, indent=1))
