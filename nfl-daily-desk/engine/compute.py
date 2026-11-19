#!/usr/bin/env python3
"""Results extension, correlations with n, shadow-record reconciliation, control baselines.

Every number here is either (a) transcribed from an official NFL page read by this session on
2026-11-19 (see captures/), (b) inherited from a repository corpus whose rows each carry an
official game-centre URL, or (c) computed from (a)+(b) by the frozen recipe in this file.
Nothing is estimated from a model of the market, and no market price exists anywhere in the
inputs - the price and residual columns are published blank with a reason.
"""
import hashlib
import json
import math
import os
import random
import re
import subprocess
import sys
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)
DAY = "2026-11-19"
SEED = 20261119
N_PERM = 20000
INHERITED = ROOT + "/nfl-live-board/data/corpus_rows_only.json"
MODEL_A = ROOT + "/nfl-readiness/data/shadow_week11.json"
MODEL_B = ROOT + "/nfl-live-board/data/origination_week11.json"
PREREG_A = ROOT + "/nfl-readiness/prereg/SHADOW_BASELINE_v1.md"


def jload(p):
    return json.load(open(p, encoding="utf-8"))


def md_table_rows(path, ncols, skip_first_cell_pred=None):
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line.startswith("|") or line.startswith("| ---") or set(line) <= set("|-: "):
            continue
        c = [x.strip() for x in line.strip("|").split("|")]
        if len(c) != ncols:
            continue
        if c[0] in ("Player", "From", "Day", "Club", "Headline"):
            continue
        out.append(c)
    return out


# ------------------------------------------------------------------ standings (official read)
def standings():
    rows = []
    for c in md_table_rows(os.path.join(NS, "captures", DAY, "standings-league-2026-reg.md"), 9):
        rows.append({"club": c[0], "W": int(c[1]), "L": int(c[2]), "T": int(c[3]),
                     "PCT": float(c[4]), "PF": int(c[5]), "PA": int(c[6]), "NET": int(c[7]),
                     "source_url": "https://www.nfl.com/standings/league/2026/REG"})
    checks = []
    for r in rows:
        net = r["PF"] - r["PA"]
        pct = round((r["W"] + 0.5 * r["T"]) / max(1, r["W"] + r["L"] + r["T"]), 3)
        checks.append({"club": r["club"], "net_identity": net == r["NET"],
                       "pct_identity": abs(pct - r["PCT"]) < 1e-9,
                       "computed_net": net, "published_pct": r["PCT"], "computed_pct": pct,
                       "source_url": r["source_url"]})
    played = sum(r["W"] + r["L"] + r["T"] for r in rows)
    return rows, checks, played // 2, played % 2


# ------------------------------------------------------------------ week 10 finals (official read)
def week10_finals():
    rows = []
    for c in md_table_rows(os.path.join(NS, "captures", DAY, "week10-finals.md"), 8):
        day, away, home, ap, hp, state, winner, url = c
        rows.append({"week": 10, "day_label": day, "date": date_from_label(day),
                     "fixture_from_url": re.sub(r"https://www.nfl.com/games/|-2026-reg-10", "", url),
                     "away": away, "home": home, "away_pts": int(ap), "home_pts": int(hp),
                     "state": state, "winner": winner, "source_url": url,
                     "neutral_site": "International" in day,
                     "score_identity": "home win" if int(hp) > int(ap) else
                                       ("away win" if int(ap) > int(hp) else "tie")})
        # winner marker consistency: the page marks the winner; cross-check with the scoreline
        rows[-1]["winner_matches_score"] = (rows[-1]["winner"] == (home if int(hp) > int(ap)
                                                                    else away if int(ap) > int(hp) else None))
    return rows


def date_from_label(lbl):
    if "November 12" in lbl:
        return "2026-11-12"
    if "November 13" in lbl:
        return "2026-11-13"
    if "November 14" in lbl:
        return "2026-11-14"
    if "November 15" in lbl:
        return "2026-11-15"
    if "November 16" in lbl:
        return "2026-11-16"
    return ""


# ------------------------------------------------------------------ corpus + correlations
def pearson(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    if sxx <= 0 or syy <= 0:
        return None, n
    return sxy / math.sqrt(sxx * syy), n


def fisher_ci(r, n):
    if r is None or n < 4 or abs(r) >= 1:
        return [None, None]
    z = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3)
    lo, hi = z - 1.96 * se, z + 1.96 * se
    back = lambda v: (math.exp(2 * v) - 1) / (math.exp(2 * v) + 1)
    return [round(back(lo), 4), round(back(hi), 4)]


def perm_p(x, y, n, seed=SEED):
    if n < 4:
        return None
    rng = random.Random(seed)
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx <= 0 or syy <= 0:
        return None
    obs = abs(sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(sxx * syy))
    y2 = list(y)
    ge = 0
    for _ in range(N_PERM):
        rng.shuffle(y2)
        sxy = sum((a - mx) * (b - my) for a, b in zip(x, y2))
        r = sxy / math.sqrt(sxx * syy)
        if abs(r) >= obs - 1e-12:
            ge += 1
    return round((ge + 1) / (N_PERM + 1), 6)


def main():
    st_rows, st_checks, league_games, league_parity = standings()
    w10 = week10_finals()
    inherited = jload(INHERITED)["rows"]
    seen = {(r["away"], r["home"], r["date"]) for r in inherited}
    added = [r for r in w10 if (r["away"], r["home"], r["date"]) not in seen]
    inh_by = {(r["away"], r["home"], r["date"]): r for r in inherited}
    dup = [r for r in w10 if (r["away"], r["home"], r["date"]) in seen]
    corpus = [dict(r) for r in inherited] + [
        {"game_id": "W10-%s-%s" % (r["away"], r["home"]), "week": 10, "date": r["date"],
         "away": r["away"], "home": r["home"], "away_pts": r["away_pts"], "home_pts": r["home_pts"],
         "source_url": r["source_url"], "provenance": "verified by session arena-92c458e6-own4 on 2026-11-19",
         "neutral_verified": r["neutral_site"]} for r in added]

    # identity: games played from standings must equal corpus size
    identity = {
        "league_games_from_standings": league_games,
        "corpus_games": len(corpus),
        "inherited_games": len(inherited),
        "added_by_this_read": len(added),
        "already_present_in_inherited_corpus": len(dup),
        "holds": league_games == len(corpus),
        "standings_team_game_total_even": league_parity == 0,
        "note": "sum(W+L+T)/2 over the 32 official standings rows is the league's own count of games "
                "played; the corpus must equal it or a game is missing/double-counted",
        "source_url": "https://www.nfl.com/standings/league/2026/REG",
    }
    # zero-sum: league points for == points against
    pf = sum(r["PF"] for r in st_rows)
    pa = sum(r["PA"] for r in st_rows)
    corpus_pts = sum(r["away_pts"] + r["home_pts"] for r in corpus)
    scoring = {"standings_pf_total": pf, "standings_pa_total": pa,
               "pf_minus_pa": pf - pa, "corpus_total_points": corpus_pts,
               "standings_match_corpus_points": pf == corpus_pts,
               "source_url": "https://www.nfl.com/standings/league/2026/REG"}

    # ---- correlation set, frozen recipe: Pearson r, Fisher-z 95%, 20k permutations, seed
    def pairs(fn):
        xs, ys, rows = [], [], []
        for r in corpus:
            try:
                x, y = fn(r)
            except Exception:
                x = y = None
            if x is not None and y is not None:
                xs.append(x); ys.append(y); rows.append(r["game_id"])
        return xs, ys, rows

    # rest days from published dates only
    by_team = defaultdict(list)
    for r in sorted(corpus, key=lambda r: r["date"]):
        by_team[r["away"]].append(r["date"]); by_team[r["home"]].append(r["date"])

    def rest_diff(r):
        prev = {t: None for t in (r["away"], r["home"])}
        import datetime as dt
        d0 = dt.date.fromisoformat(r["date"])

        def back(team):
            ds = sorted(dt.date.fromisoformat(x) for x in by_team[team] if x < r["date"])
            return (d0 - ds[-1]).days if ds else None
        a, h = back(r["away"]), back(r["home"])
        if a is None or h is None:
            return None
        return h - a

    specs = [
        {"id": "K01", "pair": "game margin ~ game total",
         "definition": "(home - away) points vs (home + away) points, one pair per played game",
         "why": "this is the dependence that makes a same-game parlay of side and total invalid when "
                "marginals are multiplied; it is measured, never assumed",
         "fn": lambda r: (r["home_pts"] - r["away_pts"], r["home_pts"] + r["away_pts"])},
        {"id": "K02", "pair": "away points ~ home points",
         "definition": "one pair per played game",
         "why": "the dependence term for any two-team combination",
         "fn": lambda r: (r["away_pts"], r["home_pts"])},
        {"id": "K03", "pair": "rest differential (home - away, days) ~ home margin",
         "definition": "rest computed only from the published dates of consecutive fixtures in the corpus",
         "why": "fixture context is a schedule fact, so it is the cheapest legitimate feature to test",
         "fn": lambda r: (rest_diff(r), r["home_pts"] - r["away_pts"])},
        {"id": "K04", "pair": "previous-game margin (team) ~ next-game margin (team)",
         "definition": "team-level persistence across that club's consecutive games",
         "why": "how much of a rating signal is real persistence rather than noise",
         "fn": None},
    ]
    # K04 built separately: pair consecutive games per team
    pers_x, pers_y, pers_ids = [], [], []
    import datetime as dt
    for team, dates in by_team.items():
        rows_t = sorted((g for g in corpus if team in (g["away"], g["home"])), key=lambda g: g["date"])
        for i in range(1, len(rows_t)):
            prev, cur = rows_t[i - 1], rows_t[i]
            pm = prev["home_pts"] - prev["away_pts"] if prev["home"] == team else prev["away_pts"] - prev["home_pts"]
            cm = cur["home_pts"] - cur["away_pts"] if cur["home"] == team else cur["away_pts"] - cur["home_pts"]
            pers_x.append(pm); pers_y.append(cm); pers_ids.append(cur["game_id"])

    rows_out, detail = [], {}
    for sp in specs:
        if sp["id"] == "K04":
            xs, ys, ids = pers_x, pers_y, pers_ids
        else:
            xs, ys, ids = pairs(sp["fn"])
        r, n = (pearson(xs, ys) if len(xs) > 2 else (None, len(xs)))
        rr = round(r, 4) if r is not None else None
        entry = {"id": sp["id"], "pair": sp["pair"], "definition": sp["definition"], "why": sp["why"],
                 "n": n, "r": rr, "ci95_fisher_z": fisher_ci(rr, n) if rr is not None else [None, None],
                 "p_permutation": perm_p(xs, ys, n) if rr is not None else None,
                 "n_permutations": N_PERM, "seed": SEED,
                 "method": "Pearson r on officially sourced numbers only; Fisher-z interval is a floor on "
                           "width because games inside a week share a slate; two-sided permutation test",
                 "source_url": "https://www.nfl.com/schedules/2026/by-week/week-10",
                 "provenance": "%d rows inherited from nfl-live-board/data/corpus_rows_only.json (each with "
                               "its own game-centre URL) + %d rows verified by this session on 2026-11-19"
                               % (len(inherited), len(added))}
        rows_out.append(entry)
    # blanks kept honest: things a reader will expect, that cannot be computed from official inputs
    forbid = [
        {"id": "K05", "pair": "practice designation level ~ club margin",
         "why": "the brief requires the availability signal to be a surprise, not a level; a level "
                "correlation would need one dated report per club-week",
         "n": 0, "r": None, "blank_reason":
             "the repository holds dated reports for 2 weeks (2026-11-15 Week 10, 2026-11-18/19 Week 11). "
             "With 2 report-weeks there is no cross-sectional sample of levels, and the value would be "
             "invented. n=0 is published instead.",
         "source_url": "https://www.nfl.com/injuries/"},
        {"id": "K06", "pair": "model residual ~ market residual (CLV)",
         "why": "closing line value is the luck-free market score",
         "n": 0, "r": None, "blank_reason":
             "no official or licensed opening/closing price exists anywhere in this repository or on any "
             "NFL page; a CLV correlation cannot be computed without fabricating prices",
         "source_url": "https://www.nfl.com/"},
        {"id": "K07", "pair": "snap-share of a replaced starter ~ game total adjustment",
         "why": "the depth-of-replacement measure the brief asks for",
         "n": 0, "r": None, "blank_reason":
             "no official snap-count source has been located and licensed; replacement depth is therefore "
             "not modelled - see the suggestion that decides this before any feature is built",
         "source_url": "https://www.nfl.com/"},
    ]
    rows_out += forbid

    # ---- controls, from official numbers only
    home_wins = sum(1 for r in corpus if r["home_pts"] > r["away_pts"])
    away_wins = sum(1 for r in corpus if r["away_pts"] > r["home_pts"])
    ties = len(corpus) - home_wins - away_wins
    wk10_home = sum(1 for r in w10 if r["home_pts"] > r["away_pts"])
    controls = {
        "dataset": "nfl_daily_desk_controls",
        "title": "Control baselines computed from the official 2026 corpus (the luck yardsticks)",
        "built_utc": "2026-11-19T07:25:00Z",
        "corpus_games": len(corpus),
        "rows": [
            {"control": "always home", "n": len(corpus), "hit_rate": round(home_wins / len(corpus), 4),
             "detail": "home %d, away %d, ties %d in the 2026 corpus" % (home_wins, away_wins, ties),
             "source_url": "https://www.nfl.com/schedules/2026/by-week/week-10"},
            {"control": "coin flip", "n": len(corpus), "hit_rate": 0.5,
             "detail": "the null a side pick must beat after the home baseline is taken out",
             "source_url": "https://www.nfl.com/schedules/2026/by-week/week-10"},
            {"control": "favorites only", "n": 0, "hit_rate": None,
             "detail": "blank: a favorite is a market object and no market price is available",
             "source_url": "https://www.nfl.com/"},
            {"control": "week 10 home record (freshness check)", "n": len(w10), "hit_rate": round(wk10_home / len(w10), 4),
             "detail": "%d of %d Week 10 games won at home (Munich counted as published, home column = DET)"
                       % (wk10_home, len(w10)),
             "source_url": "https://www.nfl.com/schedules/2026/by-week/week-10"},
        ],
    }

    # ---- shadow reconciliation: two independently pre-registered records, one fixture set
    def git_last(path):
        try:
            h = subprocess.run(["git", "-C", ROOT, "log", "-1", "--format=%H|%cI", "--", path],
                               capture_output=True, text=True).stdout.strip()
            return h
        except Exception:
            return ""

    a = jload(MODEL_A)
    b = jload(MODEL_B)
    st_by = {r["club"]: r for r in st_rows}
    games_b = b["rows"]
    games_a = [f for f in a.get("forecasts", []) if f.get("home")]
    idx_a = {(f["away"], f["home"]): f for f in games_a}
    idx_b = {(f["away"], f["home"]): f for f in games_b if f.get("home")}
    fixtures = sorted(set(idx_a) | set(idx_b))
    rec = []
    for away, home in fixtures:
        fa, fb = idx_a.get((away, home)), idx_b.get((away, home))
        inputs_ok, input_detail = None, []
        for club in (away, home):
            ra = (fa or {}).get("inputs", {}).get(club)
            st = st_by.get(club)
            if ra and st:
                ok = (int(ra["W"]), int(ra["L"]), int(ra["T"]), int(ra["PF"]), int(ra["PA"])) == \
                     (st["W"], st["L"], st["T"], st["PF"], st["PA"])
                input_detail.append({"club": club, "recorded_inputs": ra,
                                     "official_2026-11-19": {k: st[k] for k in ("W", "L", "T", "PF", "PA")},
                                     "match": ok})
                inputs_ok = ok if inputs_ok is None else (inputs_ok and ok)
            elif ra and not st:
                input_detail.append({"club": club, "match": None,
                                     "blank_reason": "club absent from the standings read"})
        gap = None
        if fa and fb and fa.get("margin_home") is not None and fb.get("stage_1_side_fair_margin_home") is not None:
            gap = round(abs(float(fa["margin_home"]) - float(fb["stage_1_side_fair_margin_home"])), 4)
        rec.append({"away": away, "home": home,
                    "kickoff_label": (fa or {}).get("kickoff") or ("%s, %s" % (fb.get("date"), fb.get("kickoff_et"))),
                    "model_A_margin_home": (fa or {}).get("margin_home"),
                    "model_A_p_home": (fa or {}).get("p_home"),
                    "model_B_fair_spread_home": (fb or {}).get("stage_1_side_fair_spread_home"),
                    "model_B_fair_total": (fb or {}).get("stage_2_total_fair_total"),
                    "model_B_p_home": (fb or {}).get("stage_3_ml_p_home"),
                    "abs_gap_between_frozen_models": gap,
                    "both_records_present": bool(fa and fb),
                    "market_line": None,
                    "market_line_blank_reason": "no official or licensed price source exists; the "
                                                 "residual column stays empty rather than being filled "
                                                 "with an assumed -110",
                    "residual_vs_market": None,
                    "inputs_verified_against_official_standings_2026-11-19": inputs_ok,
                    "input_detail": input_detail,
                    "graded": None,
                    "grade_blank_reason": "no Week 11 kickoff has occurred at this read; every row in "
                                         "this table is a pre-kickoff record and stays ungraded",
                    "source_url": "https://www.nfl.com/games/%s-at-%s-2026-reg-11" % (
                        {"IND": "colts", "MIA": "dolphins", "NO": "saints", "TEN": "titans", "TB": "buccaneers",
                         "AZ": "cardinals", "PIT": "steelers", "NYJ": "jets", "JAX": "jaguars", "LV": "raiders",
                         "MIN": "vikings", "CIN": "bengals", "BAL": "ravens"}.get(away, away.lower()),
                        {"HOU": "texans", "BUF": "bills", "CHI": "bears", "DAL": "cowboys", "DET": "lions",
                         "KC": "chiefs", "PHI": "eagles", "LAC": "chargers", "NYG": "giants", "DEN": "broncos",
                         "SF": "49ers", "WAS": "commanders", "CAR": "panthers"}.get(home, home.lower())),
                    })
    shadow = {
        "dataset": "nfl_daily_desk_shadow_reconciliation",
        "title": "Two independently pre-registered Week 11 shadow records, reconciled line by line",
        "built_utc": "2026-11-19T07:25:00Z",
        "policy": "both frozen records are published side by side with the gap between them; neither is "
                  "chosen, tuned or dropped. Ranking needs graded outcomes, and grading starts after kickoff.",
        "records": {
            "model_A": {"name": a.get("model"), "prereg_file": MODEL_A.replace(ROOT + "/", ""),
                        "prereg_sha256": hashlib.sha256(open(PREREG_A, "rb").read()).hexdigest(),
                        "last_touched": git_last(PREREG_A),
                        "sigma": "assumption flag in the file: sigma is a stated constant (13.5), "
                                 "not a number measured from official data - flagged F-DSK-05",
                        "source_url": "https://www.nfl.com/standings/league/2026/REG"},
            "model_B": {"name": (b.get("model") or {}).get("kind"),
                        "prereg_file": "nfl-live-board/data/origination_week11.json",
                        "built_utc": b.get("built_utc"),
                        "frozen": (b.get("model") or {}).get("frozen"),
                        "n_train_games": (games_b[0].get("n_train_games") if games_b else None),
                        "last_touched": git_last(MODEL_B),
                        "market_columns_policy": b.get("market_columns_policy"),
                        "source_url": "https://www.nfl.com/schedules/2026/by-week/week-11"},
        },
        "n_fixtures_recorded": len(rec),
        "n_fixtures_in_official_slate": 13,
        "coverage": "13 of 13 Week 11 fixtures appear in both records" if len(rec) == 13 else
                    "coverage is incomplete - see rows",
        "rows": rec,
        "grading_queue": {
            "gradeable_now": 0,
            "why": "no Week 11 game has finished at this read; the first kickoff (IND at HOU) is "
                   "2026-11-19 8:15 PM ET (2026-11-20 01:15 UTC)",
            "first_grade_due_utc": "2026-11-20T02:30:00Z",
            "rule": "grade both models with the same frozen recipe (Brier vs the always-home baseline "
                    "from data/controls.json, MAE on the total), one game at a time, and only then rank",
            "source_url": "https://www.nfl.com/schedules/2026/by-week/week-11",
        },
        "demotion_gate": {
            "rule_text": "a live strategy returns to paper when its game-cluster lower bound on "
                         "benchmark-relative skill falls to or below zero over the trailing 4-week window, "
                         "or when a required input feed has been stale for more than 1 report cycle",
            "strategies_live": 0,
            "demotions_today": 0,
            "status": "nothing to demote: no strategy has been promoted, because no graded sample exists",
            "source_url": "https://www.nfl.com/schedules/2026/by-week/week-11",
        },
    }

    ext = {
        "dataset": "nfl_daily_desk_corpus_extension",
        "title": "2026 results corpus: what this session added, and the identities that hold",
        "built_utc": "2026-11-19T07:25:00Z",
        "policy": "a game enters the corpus only with an official game-centre URL and a scoreline read "
                  "from an official page; unplayed fixtures stay out",
        "inherited_from": "nfl-live-board/data/corpus_rows_only.json",
        "inherited_games": len(inherited),
        "added_games": [dict(r, provenance="official week page + game centre read 2026-11-19T07:06Z")
                        for r in added],
        "already_in_corpus": [{"away": r["away"], "home": r["home"], "date": r["date"],
                               "today_read": "%s-%s" % (r["away_pts"], r["home_pts"]),
                               "inherited_row": "%s-%s" % (inh_by[(r["away"], r["home"], r["date"])]["away_pts"],
                                                            inh_by[(r["away"], r["home"], r["date"])]["home_pts"]),
                               "score_agrees": (r["away_pts"], r["home_pts"]) ==
                                               (inh_by[(r["away"], r["home"], r["date"])]["away_pts"],
                                                inh_by[(r["away"], r["home"], r["date"])]["home_pts"]),
                               "source_url": r["source_url"]} for r in dup],
        "corpus_games_after_extension": len(corpus),
        "identity": identity, "scoring": scoring,
        "standings_identity_checks": st_checks,
        "week10_finals": w10,
        "closes_from_previous_build": {
            "item": "LAC at BAL (Week 10 Monday night) was listed as 'unplayed_not_in_corpus' by the "
                    "2026-11-17 build because the official page showed records, not a score",
            "now": "FINAL, LAC 23, BAL 20 - read 2026-11-19 from "
                   "https://www.nfl.com/games/chargers-at-ravens-2026-reg-10 via the week page",
            "effect": "corpus n 149 -> 150 and every Week 10 game is now settled",
            "source_url": "https://www.nfl.com/schedules/2026/by-week/week-10",
        },
    }
    for path, obj in [("corpus_extension", ext), ("correlations", {"dataset": "nfl_daily_desk_correlations",
                                                                   "title": "Correlations from officially "
                                                                           "sourced numbers only, with n on "
                                                                           "every value",
                                                                   "built_utc": "2026-11-19T07:25:00Z",
                                                                   "rows": rows_out}),
                      ("controls", controls), ("shadow_reconciliation", shadow),
                      ("standings", {"dataset": "nfl_daily_desk_standings",
                                     "title": "2026 league standings, rows transcribed from the official "
                                              "league page (read 2026-11-19T07:04Z)",
                                     "columns_not_transcribed": "home/road/div/conf/streak: the rendered "
                                                                "page header is the un-substituted template "
                                                                "text '$year$ NFL $displayname$ Standings', "
                                                                "so column order cannot be established from "
                                                                "that read; values are omitted, not guessed",
                                     "rows": st_rows, "identity_checks": st_checks,
                                     "league_games_played": league_games})]:
        json.dump(obj, open(os.path.join(NS, "data", path + ".json"), "w"), indent=1)
    print("standings rows %d, league games %d (identity holds: %s)" % (len(st_rows), league_games, identity["holds"]))
    print("corpus %d = inherited %d + added %d ; pf==corpus points: %s" %
          (len(corpus), len(inherited), len(added), scoring["standings_match_corpus_points"]))
    for e in rows_out[:4]:
        print(" ", e["id"], "n=%s" % e["n"], "r=%s" % e["r"], "ci=%s" % e["ci95_fisher_z"], "p=%s" % e.get("p_permutation"))
    print("shadow fixtures %d ; both records %d ; gaps %s" %
          (len(rec), sum(1 for r in rec if r["both_records_present"]),
           [r["abs_gap_between_frozen_models"] for r in rec][:6]))
    bad = [c for c in st_checks if not (c["net_identity"] and c["pct_identity"])]
    print("standings identity failures:", bad)


if __name__ == "__main__":
    main()
