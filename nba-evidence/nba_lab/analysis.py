"""Reproducible retrospective pilot; writes only nba-evidence/data/research.json."""
from __future__ import annotations
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, median
from math import sqrt
from .engine import (RollingStrength, fit_logistic, logistic_predict, half_line,
                     fair_decimal, brier, log_loss, mae, pearson, residualize_minutes,
                     binary_correlation, date_cluster_bootstrap, release_gates,
                     same_game_probabilities, reliability_bins)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def load_csv(name):
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_inputs():
    games = load_csv("games.csv")
    for g in games:
        for key in ("score1", "score2"):
            g[key] = int(g[key])
        g["margin"] = g["score1"] - g["score2"]
        g["total"] = g["score1"] + g["score2"]
    games.sort(key=lambda g: (g["date"], g["game_id"]))
    players = load_csv("players.csv")
    for p in players:
        for key in ("points", "rebounds", "assists"):
            p[key] = int(p[key])
        minutes, seconds = map(int, p["minutes"].split(":"))
        p["minutes_decimal"] = minutes + seconds / 60
        p["pra"] = p["points"] + p["rebounds"] + p["assists"]
    players.sort(key=lambda p: (p["date"], p["game_id"], p["player_id"]))
    return games, players


def grouped(rows):
    result = defaultdict(list)
    for row in rows:
        result[row["date"]].append(row)
    return dict(sorted(result.items()))


def expanding_training_residuals(train: list[dict], prior_games: int) -> list[dict]:
    """Out-of-fold training residuals using strictly earlier dates only.

    The first date has no pre-sample official prior and is excluded rather than
    backfilling it with a mean computed from its own or later outcomes.
    """
    residuals = []
    earlier = []
    for date, rows in grouped(train).items():
        if earlier:
            prior = mean(score for g in earlier for score in (g["score1"], g["score2"]))
            state = RollingStrength(prior, prior_games)
            for _, previous_rows in grouped(earlier).items():
                for g in previous_rows:
                    state.update(g["team1"], g["score1"], g["team2"], g["score2"])
            # Predict the complete current date before exposing any current result.
            pending = [(g, state.predict(g["team1"], g["team2"])) for g in rows]
            for g, p in pending:
                residuals.append({
                    "date": date, "game_id": g["game_id"],
                    "margin": g["margin"] - p["margin"],
                    "total": g["total"] - p["total"],
                    "predicted_margin": p["margin"], "predicted_total": p["total"],
                    "prior_dates": sorted({x["date"] for x in earlier}),
                    "source_url": g["source_url"],
                })
        earlier.extend(rows)
    return residuals


def rank_diagnostics(rows: list[dict], score_key: str) -> list[dict]:
    """Rank matched outcomes within divisions; equal scores share a rank."""
    rows = sorted(rows, key=lambda row: (row["division"], row[score_key], row["id"]))
    for row in rows:
        row["diagnostic_rank"] = 1 + sum(
            other[score_key] < row[score_key]
            for other in rows if other["division"] == row["division"])
    return rows


def run(*, write: bool = True, games_override: list[dict] | None = None,
        players_override: list[dict] | None = None):
    protocol = json.loads((DATA / "protocol.json").read_text())
    if (games_override is None) != (players_override is None):
        raise ValueError("Supply both normalized input tables or neither")
    games, players = (load_inputs() if games_override is None
                      else (games_override, players_override))
    train_dates = sorted({g["date"] for g in games if g["date"] <= protocol["train_through"]})
    train = [g for g in games if g["date"] in train_dates]
    prior_mean = mean(score for g in train for score in (g["score1"], g["score2"]))
    prior_win = mean(g["margin"] > 0 for g in train)
    prior_total = mean(g["total"] for g in train)
    model = RollingStrength(prior_mean, protocol["shrinkage_prior_games"])
    train_features, train_labels, predictions = [], [], []
    for date, rows in grouped(games).items():
        # Predict every game on a date before updating with any game on that date.
        day_predictions = []
        for g in rows:
            p = model.predict(g["team1"], g["team2"])
            row = {**g, "mean1": p["mean1"], "mean2": p["mean2"],
                   "predicted_margin": p["margin"], "predicted_total": p["total"],
                   "prior_games1": p["prior_games1"], "prior_games2": p["prior_games2"],
                   "split": "train" if date in train_dates else
                   "validation" if date in protocol["validation_dates"] else "test"}
            if date in train_dates:
                train_features.append(p["margin"])
                train_labels.append(int(g["margin"] > 0))
            else:
                row["p1"] = logistic_predict(logistic, p["margin"])
                row["baseline_p1"] = prior_win
                row["fair_decimal1"] = fair_decimal(row["p1"])
                row["fair_decimal2"] = fair_decimal(1 - row["p1"])
                row["spread1"] = -half_line(p["margin"])
                row["total_line"] = half_line(p["total"])
                row["team1_won"] = int(g["margin"] > 0)
                row["book_decimal"] = None
                row["estimated_price_edge"] = None
                row["bet_decision"] = "no bet: official price unavailable"
                predictions.append(row)
            day_predictions.append(row)
        if date in train_dates:
            logistic = fit_logistic(train_features, train_labels, protocol["logistic_l2"],
                                    protocol["logistic_iterations"])
        for g in rows:
            model.update(g["team1"], g["score1"], g["team2"], g["score2"])
    # Save all pre-outcome feature states for audit, not just favorable selections.
    feature_rows = []
    audit_model = RollingStrength(prior_mean, protocol["shrinkage_prior_games"])
    for date, rows in grouped(games).items():
        for g in rows:
            p = audit_model.predict(g["team1"], g["team2"])
            feature_rows.append({"date": date, "game_id": g["game_id"], **p,
                                 "source_url": g["source_url"]})
        for g in rows:
            audit_model.update(g["team1"], g["score1"], g["team2"], g["score2"])

    def metrics(rows):
        ps = [r["p1"] for r in rows]
        ys = [r["team1_won"] for r in rows]
        base = [r["baseline_p1"] for r in rows]
        return {"n": len(rows), "dates": len({r["date"] for r in rows}),
                "brier": brier(ps, ys), "baseline_brier": brier(base, ys),
                "log_loss": log_loss(ps, ys), "baseline_log_loss": log_loss(base, ys),
                "margin_mae": mae([r["mean1"] - r["mean2"] for r in rows], [r["margin"] for r in rows]),
                "baseline_margin_mae": mae([0] * len(rows), [r["margin"] for r in rows]),
                "total_mae": mae([r["total_line"] for r in rows], [r["total"] for r in rows]),
                "baseline_total_mae": mae([prior_total] * len(rows), [r["total"] for r in rows]),
                "mean_probability": mean(ps), "observed_rate": mean(ys),
                "directional_accuracy": mean((r["p1"] > .5) == bool(y) for r, y in zip(rows, ys)),
                "reliability": reliability_bins(ps, ys),
                "brier_difference_ci": date_cluster_bootstrap(
                    [{"date": r["date"], "diff": (r["baseline_p1"] - y) ** 2 - (r["p1"] - y) ** 2}
                     for r, y in zip(rows, ys)], "diff", protocol["bootstrap_replicates"], protocol["bootstrap_seed"])}
    validation = [r for r in predictions if r["split"] == "validation"]
    test = [r for r in predictions if r["split"] == "test"]
    # Corrective revision Q-LEAK-2026-11-05: residual fitting is expanding and
    # same-game probabilities never read the target game's final total.
    train_residuals = expanding_training_residuals(train, protocol["shrinkage_prior_games"])
    for r in validation + test:
        favorite1 = r["p1"] >= .5
        r.update(same_game_probabilities(r, train_residuals))
        # Outcomes are attached only after every pre-event probability is frozen.
        r["over_hit"] = int(r["total"] > r["total_line"])
        r["sgp_hit"] = int((r["team1_won"] == int(favorite1)) and r["over_hit"])
    sgp_test = [r for r in test]
    sgp_joint = [r["p_sgp"] for r in sgp_test]
    sgp_independent = [r["p_sgp_independent"] for r in sgp_test]
    sgp_outcomes = [r["sgp_hit"] for r in sgp_test]
    sgp_metrics = {"n": len(sgp_test), "dates": len({r["date"] for r in sgp_test}),
                   "training_pairs": len(train_residuals),
                   "training_dates": len({r["date"] for r in train_residuals}),
                   "joint_estimate_brier": brier(sgp_joint, sgp_outcomes),
                   "independent_brier": brier(sgp_independent, sgp_outcomes),
                   "joint_estimate_log_loss": log_loss(sgp_joint, sgp_outcomes),
                   "independent_log_loss": log_loss(sgp_independent, sgp_outcomes),
                   "over_brier": brier([r["p_over"] for r in sgp_test], [r["over_hit"] for r in sgp_test]),
                   "hits": sum(sgp_outcomes), "observed_rate": mean(sgp_outcomes),
                   "mean_joint_estimate": mean(sgp_joint),
                   "mean_independent_estimate": mean(sgp_independent),
                   "residual_correlation": pearson([r["margin"] for r in train_residuals], [r["total"] for r in train_residuals]),
                   "reliability": reliability_bins(sgp_joint, sgp_outcomes),
                   "brier_difference_ci": date_cluster_bootstrap(
                       [{"date": r["date"],
                         "diff": (r["p_sgp_independent"] - r["sgp_hit"]) ** 2 -
                                 (r["p_sgp"] - r["sgp_hit"]) ** 2} for r in sgp_test],
                       "diff", protocol["bootstrap_replicates"], protocol["bootstrap_seed"]),
                   "status": "Exploratory corrected forecast; no official ticket price or release qualification"}
    # All eligible pairings among the strongest favorite on each test date.
    # Tickets can share a date/team and are not independent observations.
    # Selection uses model probabilities only; no official parlay price exists.
    by_date = grouped(test)
    favorites = [max(rows, key=lambda r: r["p_favorite"]) for rows in by_date.values()]
    cross = []
    for i, a in enumerate(favorites):
        for b in favorites[i + 1:]:
            assert a["date"] != b["date"]
            if {a["team1"], a["team2"]} & {b["team1"], b["team2"]}:
                continue  # Shared-team dependence: exclude rather than assume independence.
            cross.append({"id": f"X{len(cross)+1}", "date": a["date"] + " / " + b["date"],
                          "leg1": a["favorite"], "leg2": b["favorite"],
                          "game_ids": [a["game_id"], b["game_id"]],
                          "p_independent_assumption": a["p_favorite"] * b["p_favorite"],
                          "hit": a["favorite"] == (a["team1"] if a["team1_won"] else a["team2"]) and
                                 b["favorite"] == (b["team1"] if b["team1_won"] else b["team2"]),
                          "official_ticket_decimal": None, "roi": None,
                          "source_urls": [a["source_url"], b["source_url"]]})

    train_players = [p for p in players if p["date"] <= protocol["train_through"]]
    test_players = [p for p in players if p["date"] > protocol["train_through"]]
    thresholds = {k: half_line(median(p[k] for p in train_players)) for k in ("points", "rebounds", "assists", "pra")}
    prop_specs = [("PR", "points", "rebounds"), ("PA", "points", "assists"), ("PRA", "pra", None)]
    props = []
    prop_predictions = []
    for sid, a, b in prop_specs:
        keys = [a] + ([b] if b else [])
        train_x = [int(p[a] > thresholds[a]) for p in train_players]
        test_x = [int(p[a] > thresholds[a]) for p in test_players]
        if b:
            train_y = [int(p[b] > thresholds[b]) for p in train_players]
            test_y = [int(p[b] > thresholds[b]) for p in test_players]
            tr = binary_correlation(train_x, train_y)
            te = binary_correlation(test_x, test_y)
            line = " + ".join(f"{k} > {thresholds[k]:g}" for k in keys)
        else:
            tr = te = None
            line = f"PRA > {thresholds['pra']:g}"

        def prop_hit(player):
            return int(all(player[k] > thresholds[k] for k in keys))

        train_outcomes = [prop_hit(p) for p in train_players]
        test_outcomes = [prop_hit(p) for p in test_players]
        ptrain, ptest = mean(train_outcomes), mean(test_outcomes)
        # Registered 0.5 smoothing produces a usable diagnostic probability;
        # it is not personalized and is not an executable betting forecast.
        forecast_probability = (sum(train_outcomes) + .5) / (len(train_outcomes) + 1)
        forecast = [forecast_probability] * len(test_outcomes)
        baseline = [.5] * len(test_outcomes)
        test_metric = {
            "brier": brier(forecast, test_outcomes),
            "log_loss": log_loss(forecast, test_outcomes),
            "baseline_brier": brier(baseline, test_outcomes),
            "baseline_log_loss": log_loss(baseline, test_outcomes),
            "reliability": reliability_bins(forecast, test_outcomes),
            "brier_difference_ci": None,
            "ci_reason": "Only one test date; dependence-aware interval unavailable",
        }
        props.append({"id": sid, "line": line, "train_n": len(train_players), "test_n": len(test_players),
                      "train_joint_rate": ptrain, "test_joint_rate": ptest,
                      "test_hits": sum(test_outcomes), "forecast_probability": forecast_probability,
                      "train_binary": tr, "test_binary": te, "test_metrics": test_metric,
                      "official_quote": None, "roi": None,
                      "source_urls": sorted({p["source_url"] for p in players})})
        for player, outcome in zip(test_players, test_outcomes):
            prop_predictions.append({
                "prop_id": sid, "date": player["date"], "game_id": player["game_id"],
                "player_id": player["player_id"], "player": player["player"],
                "team": player["team"], "line": line,
                "forecast_probability": forecast_probability,
                "fair_decimal": fair_decimal(forecast_probability), "actual_hit": outcome,
                "book_decimal": None, "roi": None, "source_url": player["source_url"],
            })
    correlations = []
    for name, xkey, ykey in [("Team1 vs team2 score", "score1", "score2"),
                              ("Margin vs total", "margin", "total")]:
        x, y = [g[xkey] for g in games], [g[ykey] for g in games]
        correlations.append({"id": name, "n": len(games), "clusters": len({g['date'] for g in games}),
                             "r": pearson(x, y), "ci": None,
                             "scope": "Descriptive 62-game sample; no causal or market-efficiency claim",
                             "source_urls": sorted({g['source_url'] for g in games})})
    minutes = [p["minutes_decimal"] for p in players]
    for a, b in (("points", "rebounds"), ("points", "assists"), ("rebounds", "assists")):
        x, y = [p[a] for p in players], [p[b] for p in players]
        correlations.append({"id": f"Player {a} / {b}, minutes-residualized", "n": len(players), "clusters": 2,
                             "r": pearson(residualize_minutes(x, minutes), residualize_minutes(y, minutes)),
                             "raw_r": pearson(x, y), "ci": None,
                             "scope": "Pooled cross-player convenience sample, only two games; not within-player SGP dependence",
                             "source_urls": sorted({p["source_url"] for p in players})})
    # Gate statuses apply to release as a betting strategy, not to code execution.
    gate_defs = [
        ("G01", "Official provenance", "Every input value has an official NBA source and passes integrity checks.", "pass"),
        ("G02", "No future information", "All evaluation features precede the date being predicted; parameters frozen after training. Same-game residual folds use strictly earlier dates; observed totals are attached only after probabilities are frozen.", "pass"),
        ("G03", "Sample size", f"At least {protocol['minimum_settled_selections']} settled selections and {protocol['minimum_distinct_dates']} distinct dates.", "fail"),
        ("G04", "Official executable prices", "Timestamped official sportsbook quotes, limits and applicable rules for every selection.", "unverified"),
        ("G05", "Settlement audit", "Operator-specific pushes, voids, participation and overtime rules matched to every ticket.", "unverified"),
        ("G06", "Probability quality", "Locked holdout beats a matched baseline; dependence-aware interval excludes no improvement.", "unverified"),
        ("G07", "Multiple testing", "Complete trial registry and family-wise error control on a sufficiently large independent holdout.", "unverified"),
        ("G08", "Joint dependence", "Stable out-of-sample joint calibration and actual ticket prices; pairwise correlation alone is insufficient.", "unverified"),
        ("G09", "Prospective replication", f"At least {protocol['minimum_prospective_tickets']} frozen pre-event paper tickets across {protocol['minimum_seasons']} seasons.", "fail"),
        ("G10", "Risk and execution", "Positive lower-bound net return after price/limits/voids; predeclared drawdown and exposure limits pass.", "unverified")]
    gates = [{"id": i, "name": n, "requirement": r, "status": s} for i, n, r, s in gate_defs]
    strategies = []
    specs = [
        ("S01", "Strength → moneyline", "Singles", "Shrunk scoring-for/against differential, frozen logistic calibration; require an official price edge ≥3 percentage points.", "Frozen logistic probability versus de-vigged official two-way price; no price, no selection."),
        ("S02", "Strength → spread", "Singles", "Own half-point spread from expected margin; trade only against a verified better official line.", "Margin MAE and price-adjusted cover return versus constant-margin and market baselines."),
        ("S03", "Scoring environment → total", "Singles", "Combine each offense with the opponent's scoring-against history; compare with an official total.", "Total MAE, over/under calibration and net return versus constant total and market."),
        ("S04", "Cross-game favorite pair", "Parlays", "Two favorites from different dates and disjoint teams; independence is a hypothesis, never a default fact.", "Joint Brier and actual ticket return versus singles and the operator's quoted ticket price."),
        ("S05", "Favorite + over", "Same-game parlay", "Shift training margin/total residual pairs to pregame means; estimate joint hits without multiplying marginals.", "Joint Brier versus independence and actual SGP return; residuals are not a full copula."),
        ("S06", "Points + rebounds", "Player prop combos", "Cohort median half-point thresholds; estimate joint events from player-level data, not pooled game correlations.", "Joint calibration and actual SGP price; require repeated player histories and availability snapshots."),
        ("S07", "Points + assists", "Player prop combos", "Separate role/minutes effects from shared opportunity; require player-specific conditional distributions.", "Joint calibration and actual SGP price; no borrowing of cross-player correlation as within-player dependence."),
        ("S08", "PRA threshold", "Player props", "PRA = points + rebounds + assists; model the sum directly rather than adding separate fair lines.", "Count-distribution calibration, tail coverage and verified official price; participation rules must be explicit.")]
    for sid, name, family, signal, test_plan in specs:
        sg = [dict(g) for g in gates]
        if sid in {"S04", "S05", "S06", "S07"}:
            sg[7]["status"] = "fail"
        strategies.append({"id": sid, "name": name, "family": family, "signal": signal,
                           "test_plan": test_plan, "gates": sg, "release": release_gates(sg),
                           "measured_roi": None, "correlation_for_pricing": None,
                           "source_url": "https://www.nba.com/stats/help/glossary"})
    test_metric = metrics(test)
    game_method_source = "https://www.nba.com/games?date=2025-01-08"
    leaderboard = [
        {"id": "M01", "name": "Rolling strength + logistic", "division": "Moneyline / team1 win",
         "n": len(test), "brier": test_metric["brier"], "log_loss": test_metric["log_loss"],
         "qualified": False, "reward_points": 0, "source_url": game_method_source},
        {"id": "B01", "name": "Frozen training team1 base rate", "division": "Moneyline / team1 win",
         "n": len(test), "brier": test_metric["baseline_brier"], "log_loss": test_metric["baseline_log_loss"],
         "qualified": False, "reward_points": 0, "source_url": game_method_source},
        {"id": "J01", "name": "Paired chronological residuals", "division": "Same-game / favorite + over",
         "n": sgp_metrics["n"], "brier": sgp_metrics["joint_estimate_brier"],
         "log_loss": sgp_metrics["joint_estimate_log_loss"], "qualified": False,
         "reward_points": 0, "source_url": game_method_source},
        {"id": "J02", "name": "Product of marginals (assumption)", "division": "Same-game / favorite + over",
         "n": sgp_metrics["n"], "brier": sgp_metrics["independent_brier"],
         "log_loss": sgp_metrics["independent_log_loss"], "qualified": False,
         "reward_points": 0, "source_url": game_method_source},
    ]
    for prop in props:
        division = f"Player cohort / {prop['id']}"
        source_url = test_players[0]["source_url"]
        leaderboard.extend([
            {"id": f"P-{prop['id']}", "name": "Smoothed training cohort rate", "division": division,
             "n": prop["test_n"], "brier": prop["test_metrics"]["brier"],
             "log_loss": prop["test_metrics"]["log_loss"], "qualified": False,
             "reward_points": 0, "source_url": source_url},
            {"id": f"B-{prop['id']}", "name": "Constant 50% baseline", "division": division,
             "n": prop["test_n"], "brier": prop["test_metrics"]["baseline_brier"],
             "log_loss": prop["test_metrics"]["baseline_log_loss"], "qualified": False,
             "reward_points": 0, "source_url": source_url},
        ])
    leaderboard = rank_diagnostics(leaderboard, "brier")
    point_leaderboard = rank_diagnostics([
        {"id": "M-MARGIN", "name": "Rolling strength expected margin", "division": "Margin / team1 minus team2",
         "n": len(test), "mae": test_metric["margin_mae"], "source_url": game_method_source},
        {"id": "B-MARGIN", "name": "Zero-margin baseline (no venue inference)", "division": "Margin / team1 minus team2",
         "n": len(test), "mae": test_metric["baseline_margin_mae"], "source_url": game_method_source},
        {"id": "M-TOTAL", "name": "Originated half-point total", "division": "Total / combined points",
         "n": len(test), "mae": test_metric["total_mae"], "source_url": game_method_source},
        {"id": "B-TOTAL", "name": "Frozen training total mean", "division": "Total / combined points",
         "n": len(test), "mae": test_metric["baseline_total_mae"], "source_url": game_method_source},
    ], "mae")
    source_rows = []
    for kind, rows in (("game", games), ("player", players)):
        for row in rows:
            payload = json.dumps(row, ensure_ascii=False, sort_keys=True).encode()
            source_rows.append({"kind": kind, "id": row["game_id"] + (":" + row["player_id"] if kind == "player" else ""),
                                "source_url": row["source_url"], "checked_on": "2026-11-02",
                                "verification": "Primary NBA page inspected; normalized factual fields transcribed",
                                "normalized_record_sha256": hashlib.sha256(payload).hexdigest()})
    result = {"protocol": protocol, "sample": {"games": len(games), "players": len(players),
              "dates": sorted({g['date'] for g in games}),
              "train_games": len(train), "validation_games": len(validation), "test_games": len(test),
              "player_train_games": len({p['game_id'] for p in train_players}),
              "player_test_games": len({p['game_id'] for p in test_players})},
              "prior": {"team_points": prior_mean, "team1_win_rate": prior_win, "total": prior_total},
              "logistic": logistic, "validation": metrics(validation), "test": metrics(test),
              "predictions": validation + test, "features": feature_rows, "sgp": sgp_metrics,
              "training_residuals": train_residuals,
              "cross_game": cross, "player_thresholds": thresholds, "props": props,
              "prop_predictions": prop_predictions,
              "correlations": correlations, "gates": gates, "strategies": strategies,
              "leaderboard": leaderboard, "point_leaderboard": point_leaderboard,
              "reward_pool_points": protocol["reward_pool_points"],
              "rewards_awarded": 0, "source_rows": source_rows,
              "qualified_strategies": 0, "official_price_rows": 0,
              "revision": {
                  "id": "Q-LEAK-2026-11-05", "date": "2026-11-05",
                  "reason": "Code audit found that the previous same-game estimator used the target final total and did not center favorite simulations on predicted_margin.",
                  "correction": "Shift chronological margin/total residual pairs by predicted_margin and predicted_total; expanding residual folds exclude the first date; outcome-mutation and deterministic-shift regression tests enforce the formulas.",
                  "invalidated_outputs": ["previous p_over", "previous p_sgp", "previous p_sgp_independent", "previous same-game Brier comparison"],
                  "unchanged": ["source extracts", "date splits", "moneyline model settings", "release thresholds", "zero-reward policy"],
                  "holdout_boundary": "The original outputs had been inspected, so corrected same-game results are not a pristine confirmatory holdout."
              },
              "limitations": ["Retrospective pilot, not prospective preregistration.",
                              "Only 62 games over eight dates; no full-season representativeness.",
                              "Only two complete player box scores; no personalized player prop forecasts.",
                              "No verified historical sportsbook odds, limits or ticket settlement records.",
                              "No home/away, injury, lineup, rest, travel or referee adjustment.",
                              "Date-cluster intervals suppressed below 20 dates; luck cannot be eliminated.",
                              "Cohort-level prop thresholds are experimental, not official or personalized lines.",
                              "Previous same-game outputs were invalidated by target-total leakage; corrected outputs remain exploratory and require new prospective replication.",
                              "Model-derived values are calculations from cited inputs, not official NBA betting lines."]}
    if write:
        (DATA / "research.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    return result


if __name__ == "__main__":
    r = run()
    print(json.dumps({"sample": r["sample"], "test": r["test"], "sgp": r["sgp"],
                      "qualified_strategies": r["qualified_strategies"]}, indent=2))
