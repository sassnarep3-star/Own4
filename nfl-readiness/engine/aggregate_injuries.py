"""Derives PUBLIC aggregates from the PRIVATE row-level capture (private-store/, gitignored).
Public output contains counts only: no player names, positions or injury text.
Drift alarm: exits non-zero if the counts differ from the expected live-page counts.
"""
import csv, hashlib, json, pathlib, sys, collections
ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "private-store" / "injury_week10_2026-11-15.csv"
rows = list(csv.DictReader(open(SRC, encoding="utf-8")))
sha = hashlib.sha256(SRC.read_bytes()).hexdigest()

by_team = collections.OrderedDict()
block_of = {}
for r in rows:
    by_team.setdefault(r["team"], []).append(r)
    block_of[r["team"]] = r["game_block"]

teams = []
for t, rs in by_team.items():
    inj = [r for r in rs if r["injury"].strip()]
    teams.append({
        "team": t,
        "matchup": block_of[t],
        "listed_rows": len(rs),
        "injury_entries": len(inj),
        "out": sum(r["game_status"] == "Out" for r in rs),
        "doubtful": sum(r["game_status"] == "Doubtful" for r in rs),
        "questionable": sum(r["game_status"] == "Questionable" for r in rs),
        "dnp_practice": sum(r["practice_status"] == "DNP" for r in rs),
        "dnp_with_blank_injury": sum(r["practice_status"] == "DNP" and not r["injury"].strip() for r in rs),
        "starters_out": None,        # blank: no official depth source (see Q-R03)
        "replacements_named": None,  # blank: no official depth/starter source (see Q-R03)
    })

checks = {
    "player_rows": len(rows),
    "teams": len(by_team),
    "game_blocks": len(set(block_of.values())),
    "injury_entries": sum(1 for r in rows if r["injury"].strip()),
    "rows_with_game_status": sum(1 for r in rows if r["game_status"].strip()),
    "game_status_without_injury": sum(1 for r in rows if r["game_status"].strip() and not r["injury"].strip()),
    "injury_without_game_status": sum(1 for r in rows if r["injury"].strip() and not r["game_status"].strip()),
    "dnp_with_blank_injury": sum(1 for r in rows if r["practice_status"] == "DNP" and not r["injury"].strip()),
    "teams_with_zero_injury_entries": sum(1 for t in teams if t["injury_entries"] == 0),
}
expected = {"player_rows": 347, "teams": 28, "game_blocks": 14, "injury_entries": 171,
            "game_status_without_injury": 0, "injury_without_game_status": 0, "teams_with_zero_injury_entries": 0}
drift = {k: (checks[k], v) for k, v in expected.items() if checks[k] != v}
out = {
    "dataset": "nfl_week10_injury_report_public_aggregates",
    "source_url": "https://www.nfl.com/injuries/",
    "captured": "2026-11-15 (bash clock 23:24Z-23:28Z bracketing the fetch); fetch_page text rendering, not raw HTML bytes",
    "private_source_sha256": sha,
    "private_source_note": "row-level file kept in private-store/ (gitignored) until nfl.com terms are cleared (terms s.1.3)",
    "checks": checks,
    "drift_alarm": drift,
    "teams": teams,
}
(ROOT / "nfl-readiness" / "data" / "injury_week10_aggregates.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(checks, indent=1)); print("drift:", drift or "none"); print("sha256", sha)
sys.exit(1 if drift else 0)
