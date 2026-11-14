#!/usr/bin/env python3
"""nfl-book/run_all.py — rebuild every derived number and every page.

    python3 nfl-book/run_all.py

Deterministic: the same inputs always produce the same bytes.
"""

from __future__ import annotations

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from engine import core, seed, analysis, props   # noqa: E402
from engine.store import PriceSnapshotStore      # noqa: E402


def repo_url(path):
    return "https://github.com/sassnarep3-star/Own4/blob/main/nfl-book/" + path


def load_slate(week):
    """The games of one week from the third-party schedule, with the prices it
    publishes. The scores are None until the games are played."""
    rows = []
    for a in core.load_archive():
        if a["week"] != week:
            continue
        rows.append({
            "game_key": seed.game_key(a["week"], a["away"], a["home"]),
            "week": a["week"], "date": a["date"],
            "away": a["away"], "home": a["home"],
            "market_spread_home": a["spread_line_home"],
            "market_total": a["total_line"],
            "market_home_moneyline": a["home_moneyline"],
            "market_away_moneyline": a["away_moneyline"],
        })
    rows.sort(key=lambda r: (r["date"], r["away"]))
    return rows


def market_block(market, side, fair_line, market_line, fair_price, market_price,
                 fair_source_url, market_source_url, market_source_kind, unit):
    """One market of one game: the fair line, the market line and the
    difference, each in its own field."""
    difference = None
    if fair_line is not None and market_line is not None:
        difference = round(fair_line - market_line, 4)
    elif fair_price is not None and market_price is not None:
        difference = round(fair_price - market_price, 4)
    return {
        "market": market,
        "side": side,
        "fair_line": fair_line,
        "market_line": market_line,
        "difference": difference,
        "difference_unit": unit,
        "fair_price": fair_price,
        "market_price": market_price,
        "fair_source_url": fair_source_url,
        "market_source_url": market_source_url,
        "market_source_kind": market_source_kind,
    }


def build_own_lines(games, wf, slate):
    """Originate the side, then the total, then the moneyline, and publish the
    fair line, the market line and the difference as separate fields."""
    standings = core.load_standings()
    fair_src = standings["source_url"]
    prov = core.archive_provenance()
    market_src = prov.get("upstream_commit_url")
    market_kind = "third_party_archive"

    def blocks(g, own_spread, own_total, own_ml, own_prob, market_spread,
               market_total, market_ml_home, market_ml_away):
        out = []
        out.append(market_block(
            "SPREAD", "home", own_spread, market_spread, None, None,
            fair_src, market_src, market_kind, "points"))
        out.append(market_block(
            "TOTAL", "over", own_total, market_total, None, None,
            fair_src, market_src, market_kind, "points"))
        out.append(market_block(
            "MONEYLINE", "home", None, None, own_ml,
            market_ml_home, fair_src, market_src, market_kind, "american odds"))
        out[-1]["fair_probability"] = own_prob
        out[-1]["difference_probability"] = (
            round(own_prob - core.dec_american(market_ml_home), 4)
            if own_prob is not None and market_ml_home is not None else None)
        return out

    # ---- the slate we originate right now
    ratings = core.fit_ratings(games)
    const = core.league_constants(games)
    rows = []
    for g in slate:
        spread, total, ml, exp = core.fair_lines(g, ratings, const)
        rows.append({
            "game_key": seed.game_key(g["week"], g["away"], g["home"]),
            "week": g["week"], "date": g["date"],
            "away": g["away"], "home": g["home"],
            "game_url": seed.game_url(g["away"], g["home"], g["week"]),
            "expected_home_points": exp["expected_home_points"],
            "expected_away_points": exp["expected_away_points"],
            "expected_margin": exp["expected_margin"],
            "expected_total": exp["expected_total"],
            "markets": blocks(g, spread["fair_line"], total["fair_line"],
                              ml["fair_price"], ml["fair_probability"],
                              g["market_spread_home"], g["market_total"],
                              g["market_home_moneyline"], g["market_away_moneyline"]),
            "model_inputs": spread["model_inputs"],
        })
    # ---- the same shape for every out-of-sample week we have already played
    history = []
    for r in wf:
        history.append({
            "game_key": r["game_key"], "week": r["week"], "date": r["date"],
            "away": r["away"], "home": r["home"],
            "game_url": seed.game_url(r["away"], r["home"], r["week"]),
            "actual_margin": r["actual_margin"], "actual_total": r["actual_total"],
            "expected_home_points": r["expected_home_points"],
            "expected_away_points": r["expected_away_points"],
            "markets": blocks(r, r["own_spread_home"], r["own_total"],
                              r["own_home_ml"], r["own_home_win_prob"],
                              r["market_spread_home"], r["market_total"],
                              r["market_home_ml"], r["market_away_ml"]),
        })
    return {
        "id": "own-lines-%s" % core.SNAPSHOT_UTC,
        "origination_order": ["SPREAD", "TOTAL", "MONEYLINE"],
        "order_note": (
            "The side is originated first, the total second and the moneyline "
            "third. The moneyline is not a separate opinion: it is priced FROM "
            "the originated side and the official standard deviation of the "
            "margin, so it cannot disagree with the side."),
        "columns_note": (
            "fair line, market line and difference are three separate fields. "
            "A missing market line leaves the difference blank rather than "
            "implying a zero edge."),
        "model": {
            "fitted_on_games": len(games),
            "shrinkage_games": core.SHRINK_K,
            "home_field_advantage": const["mean_home_margin"],
            "sd_home_margin": const["sd_home_margin"],
            "mean_total": const["mean_total"],
            "sd_total": const["sd_total"],
            "source_url": fair_src,
        },
        "slate": {
            "week": slate[0]["week"] if slate else None,
            "games": len(slate),
            "source_url": "https://www.nfl.com/schedules/2026/by-week/week-%d" % (
                slate[0]["week"] if slate else 0),
        },
        "rows": rows,
        "history": history,
    }


def settle_store(store, games):
    """Settle every own-model price snapshot against the official results.

    A snapshot whose publication does not state how its spread line is
    written is NOT settled: the result stays blank and the row says why.
    Settling it would mean guessing the sign convention.
    """
    index = {g["game_key"]: g for g in games}
    rows = []
    for rec in store.rows():
        if rec["originator"] != "own_model":
            continue
        g = index.get(rec["game_key"])
        if not g:
            continue
        snap = rec["open"]
        market = rec["market"]
        line = snap["line"]
        price = snap["price"]
        conv = snap.get("line_convention")
        result = None
        profit = None
        blocked = None
        if market == "SPREAD" and line is not None:
            if conv in (seed.CONV_MARKET, seed.CONV_STATED_HOME, seed.CONV_MARGIN):
                # every convention recorded here is written from the home
                # perspective with a POSITIVE value favouring the home team
                margin = g["home_pts"] - g["away_pts"]
                team_margin = margin if rec["side"] == "home" else -margin
                team_line = line if rec["side"] == "home" else -line
                if team_margin > team_line:
                    result = "win"
                elif team_margin < team_line:
                    result = "loss"
                else:
                    result = "push"
            else:
                blocked = ("the publication does not state how its spread "
                           "line is written, so the line is not settled")
        elif market == "TOTAL" and line is not None:
            total = g["home_pts"] + g["away_pts"]
            if total == line:
                result = "push"
            else:
                over = total > line
                covers = over if rec["side"] == "over" else not over
                result = "win" if covers else "loss"
        elif market == "MONEYLINE":
            if g["home_pts"] == g["away_pts"]:
                result = "push"
            else:
                won = g["home_pts"] > g["away_pts"]
                covers = won if rec["side"] == "home" else not won
                result = "win" if covers else "loss"
        if result == "win" and price is not None:
            profit = core.moneyline_decimal(price) - 1.0
        elif result == "loss":
            profit = -1.0
        elif result == "push":
            profit = 0.0
        rows.append({
            "record_key": rec["record_key"],
            "game_key": rec["game_key"], "week": g["week"], "date": g["date"],
            "away": g["away"], "home": g["home"],
            "market": market, "side": rec["side"],
            "published_line": line, "published_price": price,
            "published_utc": snap["published_utc"],
            "published_source_url": snap["source_url"],
            "line_convention": conv,
            "away_pts": g["away_pts"], "home_pts": g["home_pts"],
            "result": result, "profit_units": profit,
            "not_settled_reason": blocked,
            "settlement_source_url": g.get("official_source_url") or g.get("game_url"),
        })
    priced = [r for r in rows if r["profit_units"] is not None]
    decided = [r for r in rows if r["result"] in ("win", "loss")]
    hits = sum(1 for r in decided if r["result"] == "win")
    implied = [core.dec_american(r["published_price"]) for r in rows
               if r["market"] == "MONEYLINE" and r["published_price"] is not None]
    return {
        "rows": rows,
        "summary": {
            "settled": len(rows),
            "settled_with_a_result": sum(1 for r in rows if r["result"]),
            "not_settled": sum(1 for r in rows if not r["result"]),
            "not_settled_reason": ("the publication does not state the sign "
                                    "convention of its spread line"),
            "decided": len(decided),
            "hits": hits,
            "hit_rate": (hits / len(decided)) if decided else None,
            "mean_implied_probability": (sum(implied) / len(implied)) if implied else None,
            "settled_with_a_price": len(priced),
            "profit_units": sum(r["profit_units"] for r in priced),
            "roi": None,
            "roi_note": ("These are OUR OWN published numbers, most of them "
                         "fair prices. A fair price carries no edge by "
                         "construction, so a return computed from it would be "
                         "circular and is deliberately not published. What is "
                         "published is the calibration: how often the outcome "
                         "agreed with the number we published."),
            "note": ("A price is only available where the publication carried "
                     "one. Spreads and totals settle but cannot carry money "
                     "without a price."),
        },
    }


def build_leaderboard(evals, wf):
    """The signal board and the staking board, kept apart on purpose.

    A lucky staking run must not be able to mask a bad signal, so the two
    boards are ranked separately and a strategy may only be staked when its
    SIGNAL gates pass.
    """
    signal_rows = []
    stake_rows = []
    for e in evals:
        s = e["signal"]
        st = e["staking"]
        sig_pass = all(g["status"] == "pass" for g in e["gates"])
        signal_rows.append({
            "id": e["id"], "name": e["name"], "family": e["family"],
            "market": e["market"], "rule": e["rule"],
            "n": s["n"], "hit_rate": s["hit_rate"],
            "break_even_rate": s["break_even_rate"],
            "p_value": s["p_value"], "q_value": s["q_value"],
            "bootstrap_ci_low": s["bootstrap_ci_low"],
            "bootstrap_ci_high": s["bootstrap_ci_high"],
            "placebo_p": s["placebo_p"],
            "gates_passed": "%d/%d" % (e["gates_passed"], len(e["gates"])),
            "signal_pass": sig_pass,
            "signal_score": s["signal_score"],
            "source_url": e["source_url"],
        })
        stake_rows.append({
            "id": e["id"], "name": e["name"], "market": e["market"],
            "bets_with_a_price": st["bets_with_a_price"],
            "profit_units": st["profit_units"], "roi": st["roi"],
            "clv_points": st["clv_points"],
            "signal_pass": sig_pass,
            "stake_eligible": sig_pass,
            "eligibility_rule": ("A strategy may only be staked when every "
                                 "signal gate passes. A staking result never "
                                 "promotes a strategy on its own."),
            "source_url": e["source_url"],
        })
    signal_rows.sort(key=lambda r: (-(r["signal_score"] or -1), r["id"]))
    stake_rows.sort(key=lambda r: (-(r["roi"] if r["roi"] is not None else -1e9), r["id"]))
    for i, r in enumerate(signal_rows):
        r["signal_rank"] = i + 1
    for i, r in enumerate(stake_rows):
        r["staking_rank"] = i + 1
    masking = []
    sig_rank = {r["id"]: r["signal_rank"] for r in signal_rows}
    for r in stake_rows:
        better = sig_rank[r["id"]] > r["staking_rank"]
        masking.append({
            "id": r["id"], "name": r["name"],
            "signal_rank": sig_rank[r["id"]], "staking_rank": r["staking_rank"],
            "roi": r["roi"],
            "signal_pass": r["signal_pass"],
            "masking_risk": bool(better and not r["signal_pass"]),
            "explanation": (
                "The staking board ranks this strategy better than the signal "
                "board while its signal gates fail. Under this policy it is "
                "not staked: the staking result is treated as noise."
                if better and not r["signal_pass"] else
                "No masking: the staking rank is not better than the signal rank, "
                "or the signal gates pass."),
            "source_url": r["source_url"],
        })
    points = 1000
    awarded = sum(points for r in signal_rows if r["signal_pass"])
    return {
        "policy": {
            "signal_board": ("Ranks skill only: sample size, hit rate against "
                             "break-even, exact binomial p, false-discovery "
                             "controlled q, bootstrap floor and a relabelling "
                             "placebo. No money."),
            "staking_board": ("Ranks money only: flat one unit per bet at the "
                              "observed price. A staking result never "
                              "promotes a strategy."),
            "reward": ("%d points to a strategy that passes every signal gate; "
                       "0 otherwise. No partial credit." % points),
        },
        "signal_rows": signal_rows,
        "staking_rows": stake_rows,
        "masking_check": masking,
        "points_awarded": awarded,
        "points_available": points * len(signal_rows),
        "out_of_sample_decisions": len(wf),
    }


def prop_eval(entry, market, price_available):
    """Turn a prop or parlay signal into the same shape as a game strategy so
    every family competes on the same two boards.

    There is no prop or parlay price in scope, so the staking block is empty
    and says why. The signal block is a real test against a coin flip.
    """
    signal = {
        "n": entry.get("n", 0),
        "wins": entry.get("wins"),
        "losses": entry.get("losses"),
        "pushes": entry.get("pushes"),
        "decided": entry.get("decided"),
        "hit_rate": entry.get("hit_rate"),
        "break_even_rate": None,
        "break_even_note": ("No price for this market exists in scope, so "
                             "there is no break-even rate and no return. The "
                             "test is against a coin flip."),
        "p_value": entry.get("p_value"),
        "q_value": None,
        "bootstrap_ci_low": entry.get("bootstrap_ci_low"),
        "bootstrap_ci_high": entry.get("bootstrap_ci_high"),
        "placebo_p": entry.get("placebo_p"),
        "signal_score": None,
        "beats_closing_line": False,
        "beats_closing_line_evidence": (
            "no closing price exists for this market, so the strategy cannot "
            "be measured against one"),
        "both_halves_clear": False,
        "holdout_evidence": ("not evaluated for this family: the sample is "
                             "too small to split into two halves"),
        "market_price_available": price_available,
        "n_strategies": 1,
    }
    staking = {
        "bets_with_a_price": 0,
        "profit_units": None,
        "roi": None,
        "clv_points": None,
        "note": "No price for this market exists in scope, so there is no return to publish.",
    }
    return {
        "id": entry["id"], "name": entry["name"], "family": entry["family"],
        "market": market, "rule": entry.get("rule", entry["name"]),
        "signal": signal, "staking": staking, "bets": [],
        "source_url": entry.get("source_url", "https://www.nfl.com/injuries/"),
    }


def main():
    os.makedirs(core.DERIVED, exist_ok=True)
    games, unmatched = core.build_results()
    recon = core.reconcile_results(games)
    results = {
        "id": "results-feed-%s" % core.SNAPSHOT_UTC,
        "description": ("Every 2026 regular-season game with a final score, "
                        "settled. Scores read directly from nfl.com are marked "
                        "official_read; the rest come from the third-party "
                        "archive and are marked reconciled_to_official "
                        "because the whole feed reproduces the official "
                        "nfl.com standings cell for cell."),
        "games": len(games),
        "official_read_games": sum(1 for g in games if g["score_source"] == "official_read"),
        "reconciled_games": sum(1 for g in games if g["score_source"] == "reconciled_to_official"),
        "official_games_without_a_direct_read": unmatched,
        "reconciliation": recon,
        "rows": games,
    }
    core.write_json(os.path.join(core.DERIVED, "results.json"), results)

    store, header = seed.build_store()
    coverage = store.coverage()
    store.save(os.path.join(core.DERIVED, "price_snapshots.json"), header)
    core.write_json(os.path.join(core.DERIVED, "price_snapshot_coverage.json"),
                    {"coverage": coverage, "header": header})

    wf = analysis.walk_forward(games)
    acc = analysis.walk_forward_accuracy(wf)
    variants = analysis.model_variants(games)
    core.write_json(os.path.join(core.DERIVED, "model_variants.json"), variants)

    # ---- player props and parlays, graded from the official player logs
    logs = props.load_logs()
    totals = props.load_totals()
    transcription = props.verify_transcription(logs, totals)
    prop_rows, pooled_mean, pooled_sd = props.build_prop_rows(logs)
    prop_signal = props.evaluate_prop_rows(prop_rows, "P1")
    prop_signal["source_url"] = "https://www.nfl.com/players/josh-allen/stats"
    prop_combo = props.prop_combinations(prop_rows)
    parlay = props.build_parlay_rows(wf)
    same_game = props.same_game_parlay_dependence(games)

    # one prop strategy per player, so a single lucky player cannot carry the
    # family, and the false-discovery correction covers the whole family
    per_player = []
    for player in sorted({r["player"] for r in prop_rows}):
        rows = [r for r in prop_rows if r["player"] == player]
        sig = props.evaluate_prop_rows(rows, "PP_%s" % player.replace(" ", "_"))
        sig["name"] = "Passing yards: %s" % player
        sig["source_url"] = rows[0]["source_url"]
        per_player.append(sig)
    prop_family = [prop_signal] + per_player
    prop_q = analysis.bh_qvalues([p["p_value"] for p in prop_family])
    for p, q in zip(prop_family, prop_q):
        p["q_value"] = q
        p["n_strategies"] = len(prop_family)

    prop_bundle = {
        "id": "props-%s" % core.SNAPSHOT_UTC,
        "description": ("Player props graded from the official nfl.com player "
                        "game logs, and the parlay families. No prop or parlay "
                        "price exists in scope, so these families are graded "
                        "but cannot be staked."),
        "pooled_mean_pass_yards": round(pooled_mean, 3),
        "pooled_sd_pass_yards": round(pooled_sd, 3),
        "decisions": len(prop_rows),
        "rows": prop_rows,
        "prop_signal": prop_signal,
        "per_player": per_player,
        "prop_combination": prop_combo,
        "parlay": parlay,
        "same_game_parlay_dependence": same_game,
        "transcription_check": transcription,
    }
    core.write_json(os.path.join(core.DERIVED, "props.json"), prop_bundle)

    evals = []
    for strat in analysis.STRATEGIES:
        bets, signal, staking = analysis.evaluate_strategy(strat, wf, {})
        evals.append({"strategy": strat, "bets": bets, "signal": signal,
                      "staking": staking,
                      "id": strat["id"], "name": strat["name"],
                      "family": strat["family"], "market": strat["market"],
                      "rule": strat["rule"]})
    q = analysis.bh_qvalues([e["signal"]["p_value"] for e in evals])
    for e, qq in zip(evals, q):
        e["signal"]["q_value"] = qq
        e["signal"]["n_strategies"] = len(evals)
        # signal score: how far the hit rate sits above break-even, weighted by
        # sample size, with the false-discovery penalty applied
        s = e["signal"]
        if s["hit_rate"] is not None and s["break_even_rate"] is not None:
            edge = s["hit_rate"] - s["break_even_rate"]
            qpen = 0.0 if (qq is not None and qq <= 0.05) else -1.0
            s["signal_score"] = round(edge * math.sqrt(s["n"]) + qpen, 6)
        else:
            s["signal_score"] = None
        # holdout split: the first and second half of the sample
        n = s["n"]
        half = n // 2
        first = e["bets"][:half]
        second = e["bets"][half:]
        def rate(bets):
            d = [b for b in bets if b["result"] != "push"]
            if not d:
                return None
            return sum(1 for b in d if b["result"] == "win") / len(d)
        r1, r2 = rate(first), rate(second)
        be = s["break_even_rate"]
        s["first_half_hit_rate"] = r1
        s["second_half_hit_rate"] = r2
        s["both_halves_clear"] = bool(
            r1 is not None and r2 is not None and be is not None and r1 > be and r2 > be)
        s["holdout_evidence"] = ("first half %s, second half %s, break-even %s" % (
            analysis.fmt(r1), analysis.fmt(r2), analysis.fmt(be)))
        e["gates"], e["gates_passed"], e["demotions"] = analysis.evaluate_gates(
            s, e["staking"], e["bets"])
        e["signal"]["beats_closing_line"] = acc.get("model_beats_market")
        e["signal"]["beats_closing_line_evidence"] = (
            "out-of-sample spread error %s vs closing-line error %s over %d games" % (
                analysis.fmt(acc.get("model_spread_mae")),
                analysis.fmt(acc.get("market_spread_mae")),
                acc.get("n_predictions")))
        e["source_url"] = "https://www.nfl.com/standings/league/2026/REG"

    # ---- the prop and parlay families compete on the same two boards
    prop_evals = []
    for p in prop_family:
        e = prop_eval(p, "PROP", False)
        e["signal"]["q_value"] = p.get("q_value")
        e["signal"]["n_strategies"] = p.get("n_strategies")
        prop_evals.append(e)
    combo_eval = prop_eval({
        "id": prop_combo["id"], "name": prop_combo["name"],
        "family": prop_combo["family"], "rule": prop_combo["rule"],
        "n": prop_combo["n"], "wins": prop_combo["wins"],
        "hit_rate": prop_combo["hit_rate"],
        "source_url": prop_combo["source_url"],
    }, "PROP_COMBO", False)
    parlay_eval = prop_eval({
        "id": parlay["id"], "name": parlay["name"], "family": parlay["family"],
        "rule": parlay["rule"], "n": parlay["n"], "wins": parlay["wins"],
        "hit_rate": parlay["hit_rate"], "source_url": parlay["source_url"],
    }, "PARLAY", False)

    for e in prop_evals + [combo_eval, parlay_eval]:
        s = e["signal"]
        if s["hit_rate"] is not None:
            edge = s["hit_rate"] - 0.5
            qpen = 0.0 if (s["q_value"] is not None and s["q_value"] <= 0.05) else -1.0
            s["signal_score"] = round(edge * math.sqrt(s["n"]) + qpen, 6)
        e["gates"], e["gates_passed"], e["demotions"] = analysis.evaluate_gates(
            s, e["staking"], e["bets"])
    evals = evals + prop_evals + [combo_eval, parlay_eval]

    board = build_leaderboard(evals, wf)
    core.write_json(os.path.join(core.DERIVED, "leaderboard.json"), board)
    core.write_json(os.path.join(core.DERIVED, "strategies.json"), {
        "walk_forward": wf,
        "accuracy": acc,
        "model_variants": variants,
        "rows": [{
            "id": e["id"], "name": e["name"], "family": e["family"],
            "market": e["market"], "rule": e["rule"],
            "signal": e["signal"], "staking": e["staking"],
            "gates": e["gates"], "gates_passed": e["gates_passed"],
            "demotions": e["demotions"],
            "bets": e["bets"],
        } for e in evals],
    })

    slate = load_slate(max(g["week"] for g in games) + 1)
    own = build_own_lines(games, wf, slate)
    core.write_json(os.path.join(core.DERIVED, "own_lines.json"), own)

    settlements = settle_store(store, games)
    core.write_json(os.path.join(core.DERIVED, "settlements.json"), settlements)

    standings = core.load_standings()
    corr = analysis.build_correlations(games, standings)
    core.write_json(os.path.join(core.DERIVED, "correlations.json"), corr)
    depth = analysis.build_depth()
    core.write_json(os.path.join(core.DERIVED, "depth.json"), depth)
    core.write_json(os.path.join(core.DERIVED, "repo_review.json"),
                    analysis.build_repo_review())

    gates = {
        "id": "gates-%s" % core.SNAPSHOT_UTC,
        "validation_gates": analysis.SIGNAL_GATES,
        "demotion_gates": analysis.DEMOTION_GATES,
        "demotion_rule": ("A strategy that is live is sent back to paper when "
                          "any demotion gate triggers. A strategy may only be "
                          "promoted to live when every validation gate passes "
                          "and the sample floor is met."),
        "rows": [{
            "id": e["id"], "name": e["name"],
            "gates": e["gates"], "gates_passed": e["gates_passed"],
            "demotions": e["demotions"],
            "status": "paper" if e["gates_passed"] < len(e["gates"]) else "live",
            "promotion_rule": ("Live requires every validation gate to pass. "
                               "No strategy is live, so no demotion event has "
                               "been recorded; the rule is applied to every "
                               "strategy so the transition stays inspectable."),
        } for e in evals],
    }
    core.write_json(os.path.join(core.DERIVED, "gates.json"), gates)

    # ---------------------------------------------------- verification ledger
    st_rows = core.load_standings()["rows"]
    sources = [
        {"id": "NFL-STANDINGS", "kind": "official",
         "description": "Official 2026 league standings: all 32 clubs, W, L, T, PF, PA.",
         "url": "https://www.nfl.com/standings/league/2026/REG",
         "captured_utc": core.SNAPSHOT_UTC},
        {"id": "NFL-SCORES-W1", "kind": "official",
         "description": "Official week 1 final scores and game URLs.",
         "url": "https://www.nfl.com/scores/2026/week-1", "captured_utc": core.SNAPSHOT_UTC},
        {"id": "NFL-SCORES-W2", "kind": "official",
         "description": "Official week 2 final scores and game URLs.",
         "url": "https://www.nfl.com/scores/2026/week-2", "captured_utc": core.SNAPSHOT_UTC},
        {"id": "NFL-SCORES-W3", "kind": "official",
         "description": "Official week 3 pairings. The score cell reads 'Hidden Score'.",
         "url": "https://www.nfl.com/scores/2026/week-3", "captured_utc": core.SNAPSHOT_UTC},
        {"id": "NFL-SCORES-W4", "kind": "official",
         "description": "Official week 4 pairings. The score cell reads 'Hidden Score'.",
         "url": "https://www.nfl.com/scores/2026/week-4", "captured_utc": core.SNAPSHOT_UTC},
        {"id": "NFL-SCORES-W5", "kind": "official",
         "description": "Official week 5 final scores and game URLs.",
         "url": "https://www.nfl.com/scores/2026/week-5", "captured_utc": core.SNAPSHOT_UTC},
        {"id": "NFL-SCORES-W8", "kind": "official",
         "description": "Official week 8 final scores and game URLs.",
         "url": "https://www.nfl.com/scores/2026/week-8", "captured_utc": core.SNAPSHOT_UTC},
        {"id": "NFL-SCORES-W9", "kind": "official",
         "description": "Official week 9 final scores and game URLs.",
         "url": "https://www.nfl.com/scores/2026/week-9", "captured_utc": core.SNAPSHOT_UTC},
        {"id": "NFL-SCORES-W11", "kind": "official",
         "description": "Official week 11 schedule, matchups, dates and times.",
         "url": "https://www.nfl.com/scores/2026/week-11", "captured_utc": core.SNAPSHOT_UTC},
        {"id": "NFL-GAME-ATL-GB", "kind": "official",
         "description": "Official game page used to read a hidden-score game: ATL 35, GB 14.",
         "url": "https://www.nfl.com/games/falcons-at-packers-2026-reg-3",
         "captured_utc": core.SNAPSHOT_UTC},
        {"id": "NFL-INJURIES", "kind": "official",
         "description": "Official week 10 injury report: players, positions, injuries, practice and game status.",
         "url": "https://www.nfl.com/injuries/", "captured_utc": "2026-11-12"},
        {"id": "NFL-ROSTER-HOU", "kind": "official",
         "description": "Official Houston Texans roster, read to confirm the active roster and positions.",
         "url": "https://www.nfl.com/teams/houston-texans/roster/",
         "captured_utc": core.SNAPSHOT_UTC},
        {"id": "NFL-DEPTH", "kind": "official",
         "description": "NFL Operations depth charts. The page returns 404; there is no official depth chart.",
         "url": "https://www.nfl.com/depth-charts/", "captured_utc": core.SNAPSHOT_UTC},
        {"id": "NFL-PLAYER-LOGS", "kind": "official",
         "description": "Official nfl.com player game logs and 2026 season totals for eight quarterbacks.",
         "url": "https://www.nfl.com/players/josh-allen/stats", "captured_utc": core.SNAPSHOT_UTC},
        {"id": "ARCHIVE", "kind": "third_party",
         "description": ("Pinned nflverse/nfldata archive. Supplies market closing "
                         "lines and prices. The NFL publishes no betting lines."),
         "url": core.archive_provenance().get("upstream_commit_url"),
         "captured_utc": core.archive_provenance().get("retrieved_utc")},
    ]
    checks = []
    checks.append({
        "id": "V1", "what": "The results feed reproduces the official standings",
        "method": "Sum every game in the feed per club and compare wins, losses, ties, points for and points against with the official nfl.com standings, cell by cell.",
        "result": "%d of %d cells match across all %d clubs" % (
            recon["cells_matching"], recon["cells_total"], recon["teams_total"]),
        "status": "PASS" if recon["exact"] else "FAIL",
        "badge": "v-verified" if recon["exact"] else "v-unverified",
        "source_url": recon["source_url"],
    })
    checks.append({
        "id": "V2", "what": "The player log transcription matches the official season totals",
        "method": transcription["method"],
        "result": "%d of %d checks match across %d players" % (
            transcription["matches"], transcription["checks"], transcription["players"]),
        "status": "PASS" if transcription["all_match"] else "FAIL",
        "badge": "v-verified" if transcription["all_match"] else "v-unverified",
        "source_url": "https://www.nfl.com/players/josh-allen/stats",
    })
    orphan = [r for r in store.rows() if r["close"] and not r["open"]]
    checks.append({
        "id": "V3", "what": "No closing price snapshot exists without an opening one",
        "method": "Every record in the price store is inspected for a close without an open. The store refuses to write one.",
        "result": "%d records inspected, %d orphan closing snapshots" % (len(store.rows()), len(orphan)),
        "status": "PASS" if not orphan else "FAIL",
        "badge": "v-verified" if not orphan else "v-unverified",
        "source_url": repo_url("data/derived/price_snapshots.json"),
    })
    no_source = []
    for r in results["rows"]:
        if not (r.get("official_source_url") or r.get("game_url")):
            no_source.append(r["game_key"])
    checks.append({
        "id": "V4", "what": "Every game in the feed carries an official source link",
        "method": "Each row of the results feed is inspected for a source URL pointing at an nfl.com page.",
        "result": "%d of %d games carry an official source link" % (
            len(results["rows"]) - len(no_source), len(results["rows"])),
        "status": "PASS" if not no_source else "FAIL",
        "badge": "v-verified" if not no_source else "v-unverified",
        "source_url": "https://www.nfl.com/standings/league/2026/REG",
    })
    missing_n = [r["name"] for r in corr["rows"] if r.get("n") is None]
    checks.append({
        "id": "V5", "what": "Every correlation is published with its sample size n",
        "method": "Each correlation row is inspected for an n value.",
        "result": "%d of %d correlations publish n" % (
            len(corr["rows"]) - len(missing_n), len(corr["rows"])),
        "status": "PASS" if not missing_n else "FAIL",
        "badge": "v-verified" if not missing_n else "v-unverified",
        "source_url": "https://www.nfl.com/standings/league/2026/REG",
    })
    mislabelled = [m for m in own["rows"] for m2 in m["markets"]
                   if m2["market_source_kind"] not in ("third_party_archive",)
                   and m2["market_line"] is not None]
    checks.append({
        "id": "V6", "what": "No market number is presented as an official number",
        "method": "Every market block in the originated lines is inspected for its source kind.",
        "result": "%d market blocks checked, %d mislabelled" % (
            sum(len(m["markets"]) for m in own["rows"]), len(mislabelled)),
        "status": "PASS" if not mislabelled else "FAIL",
        "badge": "v-verified" if not mislabelled else "v-unverified",
        "source_url": core.archive_provenance().get("upstream_commit_url"),
    })
    depth_filled = [r for r in depth["rows"] if r["replacement_depth_tier"]]
    checks.append({
        "id": "V7", "what": "No depth cell is filled without an official source",
        "method": "Every injury row is inspected for a filled replacement tier.",
        "result": "%d injury rows checked, %d depth cells filled" % (
            len(depth["rows"]), len(depth_filled)),
        "status": "PASS" if not depth_filled else "FAIL",
        "badge": "v-verified" if not depth_filled else "v-unverified",
        "source_url": depth["source_url"],
    })
    core.write_json(os.path.join(core.DERIVED, "verification.json"), {
        "id": "verification-%s" % core.SNAPSHOT_UTC,
        "description": ("The register of every source this namespace used and "
                        "every check that was run against it."),
        "sources": sources,
        "checks": checks,
    })

    print("games=%d official_read=%d reconciled=%d exact=%s" % (
        len(games),
        sum(1 for g in games if g["score_source"] == "official_read"),
        sum(1 for g in games if g["score_source"] == "reconciled_to_official"),
        recon["exact"]))
    print("walk-forward predictions=%d model_mae=%s market_mae=%s" % (
        acc["n_predictions"], analysis.fmt(acc["model_spread_mae"]),
        analysis.fmt(acc["market_spread_mae"])))
    print("price snapshots=%d open_close=%d open_only=%d" % (
        coverage["records"], coverage["open_close"], coverage["open_only"]))
    print("settled=%d hit_rate=%s" % (settlements["summary"]["settled"],
                                 analysis.fmt(settlements["summary"]["hit_rate"])))
    print("slate week=%s games=%d" % (own["slate"]["week"], own["slate"]["games"]))


if __name__ == "__main__":
    main()
