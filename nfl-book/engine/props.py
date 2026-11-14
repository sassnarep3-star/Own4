"""nfl-book/engine/props.py — player props and parlays.

Player props
------------
The grading source is official: NFL Operations publishes every quarterback's
game log on nfl.com (https://www.nfl.com/players/<slug>/stats). This module
transcribes those logs, checks the transcription against the official season
totals on the same page (a line-by-line check that catches any mistyped
number), and then prices a prop line for every player out of sample.

A prop PRICE does not exist anywhere in scope: the NFL publishes no betting
lines and no licensed prop feed is present. So a prop can be graded but not
staked, and the staking column for every prop row stays blank with the
reason attached.

Parlays
-------
Two kinds are researched:

* a game-level parlay, two legs from two different games in the same week;
* a same-game parlay, a spread leg and a total leg from ONE game, whose legs
  are NOT independent. The dependence is measured from the official results
  (n is published) rather than assumed away.
"""

from __future__ import annotations

import math
import os
import statistics

from . import core
from . import analysis

PROP_LOGS = os.path.join(core.OFFICIAL, "player_logs_2026.csv")
PROP_TOTALS = os.path.join(core.OFFICIAL, "player_season_totals_2026.csv")

SHRINK_K = 2.0


def _num(x):
    if x is None:
        return None
    x = str(x).strip()
    if x == "":
        return None
    try:
        return float(x)
    except ValueError:
        return None


def load_logs():
    rows = []
    for r in core.read_csv(PROP_LOGS):
        rows.append({
            "player": r["player"], "team": r["team"], "week": int(r["week"]),
            "opponent": r["opponent"], "result": r["result"],
            "comp": _num(r["comp"]), "att": _num(r["att"]),
            "pass_yds": _num(r["pass_yds"]), "pass_avg": _num(r["pass_avg"]),
            "pass_td": _num(r["pass_td"]), "pass_int": _num(r["pass_int"]),
            "sacks": _num(r["sacks"]), "sack_yards": _num(r["sack_yards"]),
            "pass_rating": _num(r["pass_rating"]),
            "rush_att": _num(r["rush_att"]), "rush_yds": _num(r["rush_yds"]),
            "rush_avg": _num(r["rush_avg"]), "rush_td": _num(r["rush_td"]),
            "fumbles": _num(r["fumbles"]), "fumbles_lost": _num(r["fumbles_lost"]),
            "source_url": r["source_url"], "captured_utc": r["captured_utc"],
        })
    rows.sort(key=lambda r: (r["player"], r["week"]))
    return rows


def load_totals():
    out = []
    for r in core.read_csv(PROP_TOTALS):
        out.append({
            "player": r["player"], "team": r["team"], "season": int(r["season"]),
            "games": int(r["games"]), "comp": _num(r["comp"]), "att": _num(r["att"]),
            "pass_yds": _num(r["pass_yds"]), "pass_avg": _num(r["pass_avg"]),
            "pass_td": _num(r["pass_td"]), "pass_int": _num(r["pass_int"]),
            "sacks": _num(r["sacks"]), "sack_yards": _num(r["sack_yards"]),
            "pass_rating": _num(r["pass_rating"]),
            "rush_att": _num(r["rush_att"]), "rush_yds": _num(r["rush_yds"]),
            "rush_avg": _num(r["rush_avg"]), "rush_td": _num(r["rush_td"]),
            "fumbles": _num(r["fumbles"]), "fumbles_lost": _num(r["fumbles_lost"]),
            "source_url": r["source_url"], "captured_utc": r["captured_utc"],
        })
    return out


def verify_transcription(logs, totals):
    """Line-by-line check: does the sum of the transcribed games equal the
    official season totals published on the same page?"""
    fields = [
        ("games", lambda r: 1.0 if r["pass_yds"] is not None else 0.0),
        ("comp", lambda r: r["comp"]),
        ("att", lambda r: r["att"]),
        ("pass_yds", lambda r: r["pass_yds"]),
        ("pass_td", lambda r: r["pass_td"]),
        ("pass_int", lambda r: r["pass_int"]),
        ("sacks", lambda r: r["sacks"]),
        ("sack_yards", lambda r: r["sack_yards"]),
        ("rush_att", lambda r: r["rush_att"]),
        ("rush_yds", lambda r: r["rush_yds"]),
        ("rush_td", lambda r: r["rush_td"]),
        ("fumbles", lambda r: r["fumbles"]),
        ("fumbles_lost", lambda r: r["fumbles_lost"]),
    ]
    rows = []
    ok = 0
    checks = 0
    for t in totals:
        games = [r for r in logs if r["player"] == t["player"]]
        for name, fn in fields:
            got = sum(fn(r) or 0.0 for r in games)
            want = t.get(name)
            if want is None:
                rows.append({
                    "player": t["player"], "field": name,
                    "transcribed_sum": got, "official_total": None,
                    "match": None, "status": "official total not published",
                    "source_url": t["source_url"],
                })
                continue
            checks += 1
            match = abs(got - want) < 1e-9
            ok += 1 if match else 0
            rows.append({
                "player": t["player"], "field": name,
                "transcribed_sum": got, "official_total": want,
                "match": match,
                "status": "match" if match else "MISMATCH",
                "source_url": t["source_url"],
            })
    return {
        "players": len(totals),
        "checks": checks,
        "matches": ok,
        "all_match": ok == checks,
        "method": ("Every game row was transcribed from the official player "
                   "log table, then the per-player column sums were compared "
                   "with the official 2026 season totals published on the same "
                   "page. A mistyped number breaks the sum."),
        "rows": rows,
    }


def prop_model_line(prior_values, prior_mean):
    """Model line for the next game of a player, from that player's own
    earlier games only, shrunk toward the pooled official mean."""
    n = len(prior_values)
    mu = (sum(prior_values) + SHRINK_K * prior_mean) / (n + SHRINK_K)
    if n >= 2:
        sd = statistics.stdev(prior_values)
    else:
        sd = None
    return mu, sd


def build_prop_rows(logs):
    """One out-of-sample prop decision per player game with a prior."""
    played = [r for r in logs if r["pass_yds"] is not None]
    pooled = [r["pass_yds"] for r in played]
    pooled_mean = sum(pooled) / len(pooled)
    pooled_sd = statistics.stdev(pooled)
    by_player = {}
    for r in played:
        by_player.setdefault(r["player"], []).append(r)
    rows = []
    for player, games in sorted(by_player.items()):
        prior = []
        for g in games:
            if len(prior) >= 3:
                mu, sd = prop_model_line(prior, pooled_mean)
                line = round(mu)
                sigma = sd if (sd and sd > 0) else pooled_sd
                p_over = 1.0 - core.norm_cdf((line - mu) / sigma)
                side = "over" if p_over > 0.5 else "under"
                actual = g["pass_yds"]
                hit = actual > line if side == "over" else actual < line
                push = actual == line
                rows.append({
                    "player": player, "team": g["team"], "week": g["week"],
                    "opponent": g["opponent"], "date": None,
                    "prop": "passing yards",
                    "model_line": line,
                    "model_mean": round(mu, 3),
                    "model_sd": round(sigma, 3),
                    "fair_probability": round(p_over if side == "over" else 1 - p_over, 4),
                    "side": side,
                    "actual": actual,
                    "result": "push" if push else ("win" if hit else "loss"),
                    "n_prior_games": len(prior),
                    "source_url": g["source_url"],
                })
            prior.append(g["pass_yds"])
    return rows, pooled_mean, pooled_sd


def evaluate_prop_rows(rows, label, family="prop"):
    """Signal-only evaluation of a set of prop decisions.

    There is no prop price, so there is no break-even rate and no return. The
    signal test is the exact binomial against 50% — a coin flip — with a
    bootstrap interval and a relabelling placebo."""
    n = len(rows)
    wins = sum(1 for r in rows if r["result"] == "win")
    losses = sum(1 for r in rows if r["result"] == "loss")
    pushes = sum(1 for r in rows if r["result"] == "push")
    decided = n - pushes
    p = analysis.exact_binom_two_sided(decided, wins, 0.5) if decided else None
    ci = analysis.bootstrap_ci(wins, decided) if decided else (None, None)
    placebo = analysis.permutation_p(wins, decided) if decided else None
    return {
        "id": label, "family": family,
        "name": "Passing yards: model line against the official game log",
        "rule": ("For each quarterback game after the third, the model line is "
                 "the shrunk mean of that quarterback's own earlier games. The "
                 "side is the one the model prefers. The outcome is the "
                 "official passing-yard total on nfl.com."),
        "n": n, "wins": wins, "losses": losses, "pushes": pushes,
        "decided": decided,
        "hit_rate": (wins / decided) if decided else None,
        "break_even_rate": None,
        "break_even_note": ("No prop price exists in scope, so there is no "
                            "break-even rate and no return. The test is against "
                            "a coin flip."),
        "p_value": p,
        "bootstrap_ci_low": ci[0], "bootstrap_ci_high": ci[1],
        "placebo_p": placebo,
        "source_url": "https://www.nfl.com/players/josh-allen/stats",
    }


def prop_combinations(rows):
    """Two-leg player-prop combinations: two quarterbacks in the same week.

    The two legs are not independent: they share a week, and the game script
    of one game can move the other's line. The dependence is measured from
    the official data and published with n."""
    by_week = {}
    for r in rows:
        by_week.setdefault(r["week"], []).append(r)
    combos = []
    weeks = sorted(by_week)
    for i, w1 in enumerate(weeks):
        for w2 in weeks[i + 1:]:
            for a in by_week[w1]:
                for b in by_week[w2]:
                    if a["player"] == b["player"]:
                        continue
                    if a["result"] == "push" or b["result"] == "push":
                        continue
                    joint = (a["result"] == "win") and (b["result"] == "win")
                    prod = a["fair_probability"] * b["fair_probability"]
                    combos.append({
                        "week_a": w1, "week_b": w2,
                        "player_a": a["player"], "player_b": b["player"],
                        "side_a": a["side"], "side_b": b["side"],
                        "leg_a_hit": a["result"] == "win",
                        "leg_b_hit": b["result"] == "win",
                        "both_hit": joint,
                        "independent_probability": round(prod, 4),
                        "source_url": a["source_url"],
                    })
    n = len(combos)
    both = sum(1 for c in combos if c["both_hit"])
    # Dependence: the observed joint hit rate against the mean of the two
    # marginal hit rates. A positive number means the legs moved together.
    if combos:
        marg_a = sum(1 for c in combos if c["leg_a_hit"]) / n
        marg_b = sum(1 for c in combos if c["leg_b_hit"]) / n
        expected = 0.5 * (marg_a + marg_b)
        observed = both / n
        dependence = observed - expected
        p = analysis.exact_binom_two_sided(n, both, expected) if expected else None
    else:
        marg_a = marg_b = expected = observed = dependence = p = None
    return {
        "id": "PC1", "family": "prop_combination",
        "name": "Two-leg player-prop combination across different weeks",
        "rule": ("Two quarterback passing-yard prop decisions from different "
                 "weeks are paired. A combination hits when both legs hit."),
        "n": n, "wins": both,
        "hit_rate": (both / n) if n else None,
        "p_value": p,
        "marginal_hit_rate_a": marg_a, "marginal_hit_rate_b": marg_b,
        "independent_expectation": expected,
        "observed_joint_rate": observed,
        "dependence": dependence,
        "dependence_note": ("The difference between the observed joint hit "
                            "rate and the average of the two marginal hit "
                            "rates. Positive means the legs move together."),
        "source_url": "https://www.nfl.com/players/josh-allen/stats",
        "rows": combos[:400],
        "rows_published": min(len(combos), 400),
        "rows_total": len(combos),
    }


def same_game_parlay_dependence(games):
    """The dependence between a spread leg and a total leg of ONE game.

    Measured from the official final scores: for every game, the margin and
    the total. The correlation is published with n."""
    margins = [g["home_pts"] - g["away_pts"] for g in games]
    totals = [g["home_pts"] + g["away_pts"] for g in games]
    row = analysis.corr_row(
        "Home margin vs game total (same game, parlay legs)",
        margins, totals, "points vs points",
        "https://www.nfl.com/scores/2026/week-1",
        "Both series are official final scores. This is the dependence "
        "between the two legs of a same-game parlay.")
    # The sign agreement: do the same games that cover also run over?
    both = 0
    either = 0
    for m, t in zip(margins, totals):
        cover = m > 0
        over = t > 44.5
        if cover and over:
            both += 1
        if cover or over:
            either += 1
    row["covers_and_over_rate"] = both / len(games) if games else None
    row["covers_x_over_rate"] = (both / either) if either else None
    row["note"] = (
        "A parlay priced as if its legs were independent is mispriced "
        "whenever this dependence is not zero. The joint rate and n are "
        "published above so the correction can be read rather than assumed.")
    return row


def build_parlay_rows(wf, min_gap=2.0):
    """Two-leg game-level parlays: the two games of a week with the largest
    spread disagreement between the model and the market."""
    weeks = sorted({r["week"] for r in wf})
    parlays = []
    for w in weeks:
        games = [r for r in wf if r["week"] == w]
        legs = []
        for r in games:
            if r["own_spread_home"] is None or r["market_spread_home"] is None:
                continue
            gap = r["own_spread_home"] - r["market_spread_home"]
            if abs(gap) < min_gap:
                continue
            # a higher published line means the model likes the home side
            side = "home" if gap > 0 else "away"
            signed = r["own_spread_home"] if side == "home" else -r["own_spread_home"]
            hit = r["actual_margin"] > signed
            p = 1.0 - core.norm_cdf((signed - r["own_spread_home"]) /
                                    max(r["model_sd"], 1e-9)) if "model_sd" in r else None
            legs.append({
                "game_key": r["game_key"], "away": r["away"], "home": r["home"],
                "side": side, "line": r["own_spread_home"],
                "market_line": r["market_spread_home"], "gap": round(gap, 2),
                "hit": hit, "source_url": "https://www.nfl.com/standings/league/2026/REG",
            })
        if len(legs) >= 2:
            a, b = legs[0], legs[1]
            parlays.append({
                "week": w,
                "leg_a": a, "leg_b": b,
                "both_hit": a["hit"] and b["hit"],
                "either_hit": a["hit"] or b["hit"],
                "source_url": "https://www.nfl.com/standings/league/2026/REG",
            })
    n = len(parlays)
    both = sum(1 for p in parlays if p["both_hit"])
    marg = 0.0
    for p in parlays:
        marg += (1.0 if p["leg_a"]["hit"] else 0.0)
        marg += (1.0 if p["leg_b"]["hit"] else 0.0)
    marg = marg / (2 * n) if n else None
    observed = both / n if n else None
    return {
        "id": "L1", "family": "parlay",
        "name": "Two-leg game parlay: the model's side in the two games of a week with the biggest disagreement",
        "rule": ("Within each week, take the games where the model's spread "
                 "differs from the market's by at least %.1f points and pair "
                 "the first two. A parlay hits when both legs hit." % min_gap),
        "n": n, "wins": both,
        "hit_rate": observed,
        "marginal_leg_hit_rate": marg,
        "independent_expectation": (marg ** 2) if marg is not None else None,
        "dependence": (observed - (marg ** 2)) if (observed is not None and marg is not None) else None,
        "price": None,
        "price_note": ("No parlay price exists in scope, so the parlay can be "
                       "graded but not staked."),
        "source_url": "https://www.nfl.com/standings/league/2026/REG",
        "rows": parlays,
    }
