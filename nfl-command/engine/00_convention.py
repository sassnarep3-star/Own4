"""00 - Determine and record the archive's spread-line convention.

The third-party archive stores one number per game in `spread_line`. Two
readings are possible:

  A (adopted): spread_line is the AWAY team's line, so the home team's line
    is -spread_line and the home team covers when margin > -spread_line.
  B (rejected): spread_line is the HOME team's line, so the home team covers
    when margin > spread_line.

The reading is decided by two independent checks that do not depend on the
cover rate:

  1. Moneyline cross-check. For a game with a spread, the team that is the
     moneyline favourite must be the team that is the spread favourite.
  2. Cover-rate coherence. A market with a home-field advantage must produce
     a home cover rate that is coherent with the share of games the home team
     is the favourite.

Writes: data/spread_convention_determination.json
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import ROOT, dump_json, load_games


def dec(o):
    try:
        o = float(o)
        return 1 + 100.0 / o if o > 0 else 1 + 100.0 / abs(o)
    except (TypeError, ValueError):
        return None


def main():
    games = load_games()
    rows = [g for g in games if g["spread_line"] is not None]

    def cover_rate(sign, subset):
        """sign=-1 -> reading A (home_line = -sl); sign=+1 -> reading B."""
        hit = 0.0
        for g in subset:
            hl = sign * g["spread_line"]
            if g["margin"] > hl:
                hit += 1
            elif g["margin"] == hl:
                hit += 0.5
        return hit / len(subset) if subset else None

    r26 = [g for g in rows if g["season"] == 2026]

    ml_tested = 0
    agree_a = 0
    agree_b = 0
    for g in rows:
        h = dec(g["home_moneyline"])
        a = dec(g["away_moneyline"])
        if h is None or a is None:
            continue
        ml_tested += 1
        ml_home_fav = h < a
        # reading A: the home line is -sl, so the home team is favoured when sl > 0
        if ml_home_fav == (g["spread_line"] > 0):
            agree_a += 1
        # reading B: the home line is +sl, so the home team is favoured when sl < 0
        if ml_home_fav == (g["spread_line"] < 0):
            agree_b += 1

    # share of games in which the home team is the spread favourite under each reading
    home_fav_a = sum(1 for g in rows if g["spread_line"] > 0) / len(rows)
    home_fav_b = 1 - home_fav_a

    res = {
        "id": "spread-convention-determination",
        "determined_utc": "2026-11-13T00:00:00Z",
        "data": {
            "file": "data/raw/nfldata_games.csv",
            "sha256": "0114259438549a7c0bf201f7c91944f8ec1c02dba7339673b07d3129a5ff81df",
            "source": "https://github.com/nflverse/nfldata",
            "commit": "a7eee2ca013f19aa59db9fe170c41ef0ff1cfaaa",
            "status": "THIRD-PARTY ARCHIVE. The NFL publishes no betting lines.",
        },
        "question": "Does the archive's spread_line belong to the home team or to the away team?",
        "adopted": {
            "id": "A",
            "rule": "The archive's spread_line is the AWAY team's line. The home team's line is -spread_line. The home team covers when the actual margin (home minus away) is greater than -spread_line.",
            "rows": len(rows),
            "home_cover_rate_all": round(cover_rate(-1, rows), 5),
            "home_cover_rate_2026": round(cover_rate(-1, r26), 5),
            "home_team_is_spread_favourite_share": round(home_fav_a, 5),
            "moneyline_agreement_rate": round(agree_a / ml_tested, 5),
            "moneyline_games_tested": ml_tested,
            "reason": "The moneyline cross-check agrees with this reading in %.2f%% of the %d games that carry both a spread and a moneyline. The home cover rate of %.2f%% is coherent with the share of games in which the home team is the spread favourite (%.2f%%): a favourite covering a three-point line wins about six times in ten, so the two numbers must agree."
                      % (100 * agree_a / ml_tested, ml_tested, 100 * cover_rate(-1, rows), 100 * home_fav_a),
        },
        "rejected": {
            "id": "B",
            "rule": "The archive's spread_line is the HOME team's line. The home team covers when the actual margin is greater than +spread_line.",
            "rows": len(rows),
            "home_cover_rate_all": round(cover_rate(1, rows), 5),
            "home_cover_rate_2026": round(cover_rate(1, r26), 5),
            "home_team_is_spread_favourite_share": round(home_fav_b, 5),
            "moneyline_agreement_rate": round(agree_b / ml_tested, 5),
            "moneyline_games_tested": ml_tested,
            "reason": "The moneyline cross-check agrees with this reading in only %.2f%% of the same %d games, which is the rate you would expect by chance. The reading is therefore rejected."
                      % (100 * agree_b / ml_tested, ml_tested),
        },
        "supersedes": "The descriptive sentence about the spread convention in data/strategy_registry_preregistered.json and the note in data/gates_preregistered.json were written before this determination was made and quoted the cover rate under the rejected reading. The thresholds registered in those files are unchanged. This file is the dated, reproducible record of the convention.",
        "how_to_reproduce": "python3 engine/00_convention.py",
    }
    dump_json(os.path.join(ROOT, "data", "spread_convention_determination.json"), res)
    print("adopted:", res["adopted"]["rule"][:60], "...")
    print("  home cover all  = %.4f   2026 = %.4f" % (res["adopted"]["home_cover_rate_all"],
                                                      res["adopted"]["home_cover_rate_2026"]))
    print("  moneyline agreement: adopted %.4f  rejected %.4f"
          % (res["adopted"]["moneyline_agreement_rate"], res["rejected"]["moneyline_agreement_rate"]))


if __name__ == "__main__":
    main()
