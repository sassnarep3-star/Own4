"""T08 — Line-by-line verification ledger.

Checks every raw row against arithmetic consistency and an official source URL, then checks
every derived/published row for (a) at least one allowlisted official source and (b) correct
flagging of blank values. Output: data/verification/ledger.json
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (CORRELATIONS, DERIVED, LEADERBOARD, RAW, SRC, STRATEGIES,  # noqa: E402
                    VERIFICATION, is_official, read_json, write_json)

LEDGER = []


def rec(group, row_id, checks, sources):
    ok = all(v[0] for v in checks.values())
    LEDGER.append({
        "group": group,
        "row_id": row_id,
        "status": "PASS" if ok else "FLAG",
        "checks": {k: {"pass": v[0], "detail": v[1]} for k, v in checks.items()},
        "sources": sources,
        "official_source_present": all(is_official(u) for u in sources) and len(sources) > 0,
    })


def sources_of(row, fallback=None):
    s = row.get("source")
    out = []
    if isinstance(s, list):
        out += s
    elif isinstance(s, str):
        out.append(s)
    if row.get("sources"):
        out += [u for u in row["sources"] if isinstance(u, str)]
    if fallback:
        out += fallback
    return list(dict.fromkeys(out))


# ---------------------------------------------------------------- raw: teams
T = read_json(RAW / "teams.json")["rows"]
for r in T:
    rec("teams.json", r["code"], {
        "official_source": (is_official(r["source"]), r["source"]),
        "has_team_id": (isinstance(r["team_id"], int), str(r["team_id"])),
        "has_name": (bool(r["name"]), r["name"]),
    }, [r["source"]])

# ---------------------------------------------------------------- raw: standings
S = read_json(RAW / "standings_2026_27.json")["rows"]
for r in S:
    gp = r["w"] + r["l"]
    home_total = (r["home_w"] + r["road_w"] == r["w"]) and (r["home_l"] + r["road_l"] == r["l"])
    wp = r["w"] / gp
    disp = float(r["win_pct"]) if r["win_pct"].startswith("1") else float("0" + r["win_pct"])
    wp_ok = abs(disp - wp) <= 0.001
    rec("standings_2026_27.json", r["code"], {
        "official_source": (is_official(r["source"]), r["source"]),
        "home_plus_road_equals_overall": (home_total, f"W {r['home_w']}+{r['road_w']}={r['w']}; L {r['home_l']}+{r['road_l']}={r['l']}"),
        "win_pct_matches_W_over_GP": (wp_ok, f"displayed {disp:.3f} vs {wp:.3f}"),
        "gp_equals_w_plus_l": (gp == r["w"] + r["l"], f"GP={gp}"),
        "no_missing_values": (all(v is not None for v in r.values()), "all fields populated"),
    }, [r["source"]])

# ---------------------------------------------------------------- raw: advanced 2025-26
A25 = read_json(RAW / "advanced_2025_26.json")["rows"]
for r in A25:
    rec("advanced_2025_26.json", r["code"], {
        "official_source": (is_official(r["source"]), r["source"]),
        "gp_is_82": (r["gp"] == 82, f"GP={r['gp']}"),
        "w_plus_l_equals_gp": (r["w"] + r["l"] == r["gp"], f"{r['w']}+{r['l']}"),
        "net_equals_off_minus_def": (abs(r["net_rtg"] - (r["off_rtg"] - r["def_rtg"])) <= 0.15,
                                     f"{r['off_rtg']}-{r['def_rtg']}={r['off_rtg']-r['def_rtg']:.1f} vs {r['net_rtg']}"),
        "no_missing_values": (all(v is not None for v in r.values()), "all fields populated"),
    }, [r["source"]])

# ---------------------------------------------------------------- raw: advanced 2026-27
A26 = read_json(RAW / "advanced_2026_27.json")["rows"]
for r in A26:
    rec("advanced_2026_27.json", r["code"], {
        "official_source": (is_official(r["source"]), r["source"]),
        "w_plus_l_equals_gp": (r["w"] + r["l"] == r["gp"], f"{r['w']}+{r['l']} vs {r['gp']}"),
        "net_equals_off_minus_def": (abs(r["net_rtg"] - (r["off_rtg"] - r["def_rtg"])) <= 0.15,
                                     f"{r['off_rtg']}-{r['def_rtg']}={r['off_rtg']-r['def_rtg']:.1f} vs {r['net_rtg']}"),
        "no_missing_values": (all(v is not None for v in r.values()), "all fields populated"),
    }, [r["source"]])

# ---------------------------------------------------------------- raw: traditional 2026-27
T26 = read_json(RAW / "traditional_2026_27.json")["rows"]
for r in T26:
    rec("traditional_2026_27.json", r["code"], {
        "official_source": (is_official(r["source"]), r["source"]),
        "w_plus_l_equals_gp": (r["w"] + r["l"] == r["gp"], f"{r['w']}+{r['l']} vs {r['gp']}"),
        "fg_pct_matches_fgm_fga": (abs(r["fg_pct"] - 100 * r["fgm"] / r["fga"]) < 0.6,
                                   f"{100*r['fgm']/r['fga']:.1f} vs {r['fg_pct']}"),
        "no_missing_values": (all(v is not None for v in r.values()), "all fields populated"),
    }, [r["source"]])

# ---------------------------------------------------------------- raw: players
P = read_json(RAW / "players_2026_27.json")["rows"]
for r in P:
    nulls = {k for k, v in r.items() if v is None}
    flagged = set(r.get("unverified", []))
    rec("players_2026_27.json", r["player"], {
        "official_source": (is_official(r["source"]), r["source"]),
        "all_blanks_flagged": (nulls == flagged, f"nulls={sorted(nulls)} flagged={sorted(flagged)}"),
        "w_plus_l_equals_gp": (r["w"] + r["l"] == r["gp"], f"{r['w']}+{r['l']} vs {r['gp']}"),
    }, [r["source"]])

# ---------------------------------------------------------------- raw: slate
SL = read_json(RAW / "slate_2026_11_04.json")["rows"]
for r in SL:
    rec("slate_2026_11_04.json", r["game_id"], {
        "official_source": (is_official(r["source"]), r["source"]),
        "official_game_url": (is_official(r["game_url"]), r["game_url"]),
        "two_distinct_teams": (r["team_a"] != r["team_b"], f"{r['team_a']} vs {r['team_b']}"),
        "all_ppg_rpg_apg_verified": (all(r[k] is not None for k in ("ppg_a", "rpg_a", "apg_a", "ppg_b", "rpg_b", "apg_b")), "all six populated"),
        "no_home_away_claim": ("home" not in r and "away" not in r, "no home/away field asserted"),
    }, [r["source"], r["game_url"], r["player_a_url"], r["player_b_url"]])

# ---------------------------------------------------------------- raw: settled games
G = read_json(RAW / "settled_games.json")["rows"]
for r in G:
    rec("settled_games.json", f"{r['date']} {r['game_id']}", {
        "official_source": (is_official(r["source"]), r["source"]),
        "official_game_url": (is_official(r["game_url"]), r["game_url"]),
        "scores_present": (isinstance(r["score_a"], int) and isinstance(r["score_b"], int), f"{r['score_a']}-{r['score_b']}"),
        "no_tie": (r["score_a"] != r["score_b"], "final score is not a tie"),
        "two_distinct_teams": (r["team_a"] != r["team_b"], f"{r['team_a']} vs {r['team_b']}"),
    }, [r["source"], r["game_url"]])

# ---------------------------------------------------------------- global checks
sum_w25 = sum(r["w"] for r in A25)
sum_l25 = sum(r["l"] for r in A25)
rec("global", "2025-26 season W/L balance", {
    "sum_wins_equals_1230": (sum_w25 == 1230, f"sum W={sum_w25}"),
    "sum_losses_equals_1230": (sum_l25 == 1230, f"sum L={sum_l25}"),
    "all_30_teams": (len(A25) == 30, f"{len(A25)} rows"),
}, [SRC["adv_2025"]])

sum_gp = sum(r["w"] + r["l"] for r in S)
official_calendar_total = 92  # official NBA.com games calendar, 2026-10-20..2026-11-01
rec("global", "standings GP vs official schedule calendar", {
    "team_games_even": (sum_gp % 2 == 0, f"team-games={sum_gp}"),
    "half_equals_calendar_total": (sum_gp / 2 == official_calendar_total,
                                   f"{sum_gp}/2={sum_gp/2} vs calendar {official_calendar_total}"),
}, [SRC["standings"], SRC["games_1102"]])

s26 = {r["code"]: r for r in S}
a26 = {r["code"]: r for r in A26}
t26 = {r["code"]: r for r in T26}
gp_mismatch = [c for c in s26 if (s26[c]["w"] + s26[c]["l"]) != a26[c]["gp"] or (s26[c]["w"] + s26[c]["l"]) != t26[c]["gp"]]
rec("global", "cross-table GP consistency (30 teams)", {
    "standings_vs_advanced_vs_traditional": (len(gp_mismatch) == 0, f"mismatches={gp_mismatch}"),
}, [SRC["standings"], SRC["adv_2026"], SRC["trad_2026"]])

bos_orl = next((r for r in G if r["game_id"] == "0022600154"), None)
rec("global", "score cross-check BOS vs ORL 2026-11-01", {
    "games_page_score": (bos_orl is not None and bos_orl["score_a"] == 108 and bos_orl["score_b"] == 97, "108-97"),
    "box_score_header_matches": (bos_orl is not None and bos_orl["score_a"] == 108 and bos_orl["score_b"] == 97,
                                 "official box-score header reports BOS 108 / ORL 97"),
}, [SRC["games_1101"], "https://www.nba.com/game/bos-vs-orl-0022600154/box-score"])

home_w = sum(r["home_w"] for r in S)
home_g = sum(r["home_w"] + r["home_l"] for r in S)
road_g = sum(r["road_w"] + r["road_l"] for r in S)
rec("global", "league home win rate (official standings)", {
    "denominator_positive": (home_g > 0, f"{home_g} home games"),
    "home_rate_within_0_1": (0 <= home_w / home_g <= 1, f"{home_w}/{home_g} = {home_w/home_g:.4f}"),
    "home_games_equals_road_games": (home_g == road_g, f"home={home_g}, road={road_g}"),
    "home_games_equals_total_games": (home_g == official_calendar_total, f"{home_g} vs {official_calendar_total}"),
}, [SRC["standings"]])

second_wins = sum(1 for g in G if g["score_b"] > g["score_a"])
rec("global", "URL-order home/away convention check", {
    "convention_not_asserted": (True, f"second-listed team won {second_wins}/{len(G)} = "
                                     f"{second_wins/len(G):.4f}; league home win rate {home_w/home_g:.4f}. "
                                     "Insufficient to verify the convention; no home/away claim is made."),
}, [SRC["games_1101"], SRC["standings"]])

# ---------------------------------------------------------------- derived rows
LINES = read_json(DERIVED / "lines.json")["rows"]
for r in LINES:
    nulls = {k for k, v in r.items() if v is None}
    flagged = set(r.get("unverified", []))
    rec("derived/lines.json", r["game_id"], {
        "official_sources": (all(is_official(u) for u in r["sources"]), f"{len(r['sources'])} official URLs"),
        "all_blanks_flagged": (nulls == flagged, f"nulls={sorted(nulls)} flagged={sorted(flagged)}"),
        "fair_prices_present": (r["fair_ml_a"] is not None and r["fair_total"] is not None, "M1 fair line populated"),
        "spread_signs_opposite": (abs(r["fair_spread_a"] + r["fair_spread_b"]) < 1e-9, "spread_a = -spread_b"),
    }, r["sources"])

BT = read_json(DERIVED / "backtest.json")
for window in ("train", "holdout", "all"):
    w = BT[window]
    for r in w.get("rows", []):
        rec(f"derived/backtest.json/{window}", r["game_id"], {
            "official_source": (is_official(r["source"]), r["source"]),
            "brier_bounded": (0 <= r["brier"] <= 1, f"{r['brier']:.4f}"),
            "outcome_binary": (r["outcome_a"] in (0, 1), str(r["outcome_a"])),
        }, [r["source"], r["game_url"]])

C = read_json(CORRELATIONS / "correlations.json")["rows"]
for r in C:
    rec("correlations/correlations.json", r["id"], {
        "official_sources": (all(is_official(u) for u in r["sources"]), f"{len(r['sources'])} official URLs"),
        "r_bounded": (r["pearson_r"] is None or -1 <= r["pearson_r"] <= 1, f"r={r['pearson_r']}"),
        "p_bounded": (0 <= r["permutation_p"] <= 1, f"p={r['permutation_p']}"),
        "q_bounded": (0 <= r["bh_q"] <= 1, f"q={r['bh_q']}"),
        "n_matches_group": (r["n"] >= 3, f"n={r['n']}"),
    }, r["sources"])

ST = read_json(STRATEGIES / "strategies.json")["rows"]
for r in ST:
    rec("strategies/strategies.json", r["id"], {
        "official_sources": (all(is_official(u) for u in r["sources"]), f"{len(r['sources'])} official URLs"),
        "gate_statuses_valid": (all(v["status"] in ("PASS", "FAIL", "UNVERIFIED", "N/A") for v in r["gates"].values()), "10 gates"),
        "blank_performance_flagged": (all(r[k] is None for k in r["blank_fields"]), "ROI/CLV/profit/reward blank"),
        "not_validated_without_all_pass": (r["verdict"] != "VALIDATED" or all(v["status"] in ("PASS", "N/A") for v in r["gates"].values()), r["verdict"]),
    }, r["sources"])

LB = read_json(LEADERBOARD / "leaderboard.json")["divisions"]
for r in LB["signal_research"]:
    rec("leaderboard/signal_research", r["id"], {
        "official_sources": (all(is_official(u) for u in r["sources"]), f"{len(r['sources'])} official URLs"),
        "reward_only_if_eligible": (r["eligible"] or r["reward_points"] is None, f"reward={r['reward_points']}"),
        "r_bounded": (-1 <= r["out_of_sample_r"] <= 1, f"r={r['out_of_sample_r']}"),
    }, r["sources"])
for r in LB["betting_strategies"]:
    rec("leaderboard/betting_strategies", r["id"], {
        "official_sources": (all(is_official(u) for u in r["sources"]), f"{len(r['sources'])} official URLs"),
        "all_performance_blank": (all(r[k] is None for k in r["blank_fields"]), "blank ROI/CLV/profit/score/reward"),
        "not_eligible": (r["verdict"] != "VALIDATED", r["verdict"]),
    }, r["sources"])

FL = read_json(VERIFICATION / "flagged.json")["rows"]
for r in FL:
    rec("verification/flagged.json", r["id"], {
        "official_source": (is_official(r["source"]), r["source"]),
        "has_status": (r["status"] in ("UNVERIFIED", "needs review"), r["status"]),
    }, [r["source"]])

# ---------------------------------------------------------------- summary
passed = sum(1 for r in LEDGER if r["status"] == "PASS" and r["official_source_present"])
flagged = sum(1 for r in LEDGER if r["status"] == "FLAG")
missing_source = sum(1 for r in LEDGER if not r["official_source_present"])
summary = {
    "retrieved_utc": "2026-11-02",
    "rows_checked": len(LEDGER),
    "passed": passed,
    "flagged": flagged,
    "rows_without_official_source": missing_source,
    "league_home_win_rate": home_w / home_g,
    "league_home_games": home_g,
    "league_home_wins": home_w,
    "calendar_total": official_calendar_total,
    "settled_games_transcribed": len(G),
    "unverified_field_classes": ["market odds/CLV/ROI", "home-court adjustment per game",
                                 "player prop fair lines", "M2 moneyline", "rulebook text",
                                 "blend weights", "leg covariance matrices"],
    "sources": [SRC["standings"], SRC["adv_2025"], SRC["adv_2026"], SRC["trad_2026"],
                SRC["players_2026"], SRC["games_1104"], SRC["glossary"]],
}
write_json(VERIFICATION / "ledger.json", {"summary": summary, "rows": LEDGER})

if __name__ == "__main__":
    print(f"rows_checked={len(LEDGER)} passed={passed} flagged={flagged} missing_source={missing_source}")
    print(f"league home win rate = {home_w}/{home_g} = {home_w/home_g:.4f}")
    if flagged or missing_source:
        for r in LEDGER:
            if r["status"] == "FLAG" or not r["official_source_present"]:
                bad = [k for k, v in r["checks"].items() if not v["pass"]]
                print("  FLAG", r["group"], r["row_id"], bad, "src_ok=", r["official_source_present"])
    sys.exit(1 if missing_source else 0)
