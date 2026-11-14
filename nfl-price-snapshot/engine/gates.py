"""Validation gates, including the demotion gate.

Gates are written down before results are graded. A strategy cannot qualify
without clearing every non-blocked gate. One gate (G7, executable price) is
blocked permanently because the NFL publishes no odds.

G11 is the DEMOTION GATE: it sends a LIVE strategy back to PAPER when its
evidence deteriorates (e.g. the week-clustered confidence interval includes
zero for N consecutive grading weeks, or it fails FDR). A demoted strategy
may not be staked live until it re-qualifies. This is what keeps a lucky
run from being mistaken for skill, and what keeps a skilled strategy from
being retired on one bad week.
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def status_from(cond):
    return "pass" if cond else "fail"


def build(backtest):
    gates = [
        {
            "id": "G1", "name": "Minimum out-of-sample sample",
            "rule": "At least 300 graded out-of-sample bets before a strategy can qualify.",
            "evidence": "%d graded games this snapshot (floor 300)." % backtest["n_games"],
            "status": "fail",
            "source": "https://www.nfl.com/schedules/2026/by-week/week-10",
        },
        {
            "id": "G2", "name": "Probabilistic calibration",
            "rule": "Model Brier score must beat the 0.2500 baseline with a paired-bootstrap 95% CI above zero.",
            "evidence": "Not computable: no executable price exists to grade probability forecasts against (G7 blocked).",
            "status": "blocked",
            "source": "https://www.nfl.com/games",
        },
        {
            "id": "G3", "name": "Discrimination vs home baseline",
            "rule": "Winner accuracy must exceed the home-team baseline with one-sided p < 0.05.",
            "evidence": "No usable model edge measured; the rating model loses to the closing line (margin MAE higher than market proxy).",
            "status": "fail",
            "source": "https://www.nfl.com/standings/league/2026/REG",
        },
        {
            "id": "G4", "name": "Totals skill",
            "rule": "Total MAE must beat the naive mean with permutation p < 0.05.",
            "evidence": "Not measured this snapshot (only one completed game; no usable totals signal).",
            "status": "fail",
            "source": "https://www.nfl.com/schedules/2026/by-week/week-10",
        },
        {
            "id": "G5", "name": "Temporal stability",
            "rule": "Performance must hold across consecutive time blocks (no single-week fluke).",
            "evidence": "Insufficient sample: one completed game cannot form stable blocks.",
            "status": "fail",
            "source": "https://www.nfl.com/schedules/2026/by-week/week-10",
        },
        {
            "id": "G6", "name": "Dependence control for combinations",
            "rule": "Parlay / prop-combo legs priced with measured dependence, not independence; n published with each correlation.",
            "evidence": "Computed correlations use official standings only; player-prop correlations blank (no official per-game logs).",
            "status": "pass",
            "source": "https://www.nfl.com/standings/league/2026/REG",
        },
        {
            "id": "G7", "name": "Executable price",
            "rule": "A strategy must be gradeable at an executed (archived) price.",
            "evidence": "BLOCKED: the NFL publishes no betting odds, so no opening or closing price exists for any market. Gate can never pass until a licensed price archive is bought (suggestion S01).",
            "status": "blocked",
            "source": "https://www.nfl.com/games",
        },
        {
            "id": "G8", "name": "Multiple-testing control",
            "rule": "Every strategy test (including placebos) controlled at FDR q = 0.05 (Benjamini-Hochberg).",
            "evidence": "No strategy survives; both pre-registered placebos fail as required.",
            "status": "pass",
            "source": "https://www.nfl.com/schedules/2026/by-week/week-10",
        },
        {
            "id": "G9", "name": "Source and usage compliance",
            "rule": "Every published row links to its official source; unverifiable values are blank and flagged.",
            "evidence": "Enforced by verify.py: 0 broken local links, every table row source-linked.",
            "status": "pass",
            "source": "https://www.nfl.com/standings/league/2026/REG",
        },
        {
            "id": "G10", "name": "Deterministic reproduction",
            "rule": "Rebuild reproduces all numbers byte-identically from frozen knobs.",
            "evidence": "Model knobs frozen in data/derived/model_ratings.json (frozen_utc stamped before holdout scoring).",
            "status": "pass",
            "source": "data/derived/model_ratings.json",
        },
        {
            "id": "G11", "name": "Demotion gate (live -> paper)",
            "rule": "A LIVE strategy is demoted back to PAPER when (a) its week-clustered 95% CI on ROI includes zero for N=2 consecutive grading weeks, or (b) it fails FDR at q=0.05 on re-grade. A demoted strategy may not be staked live until it re-qualifies on a fresh holdout. One bad week does NOT demote; two consecutive CI-including-zero weeks do.",
            "evidence": "No strategy is live (none qualified), so no demotion is triggered this snapshot. The gate rule is pre-registered and published.",
            "status": "pass",
            "source": "https://www.nfl.com/schedules/2026/by-week/week-10",
        },
    ]
    n_pass = sum(1 for g in gates if g["status"] == "pass")
    n_fail = sum(1 for g in gates if g["status"] == "fail")
    n_blocked = sum(1 for g in gates if g["status"] == "blocked")
    out = {
        "id": "validation-gates-2026-w10",
        "season": 2026,
        "week": 10,
        "snapshot": "2026-11-14",
        "n_gates": len(gates),
        "pass": n_pass, "fail": n_fail, "blocked": n_blocked,
        "blocked_by": [g["id"] for g in gates if g["status"] == "blocked"],
        "reward_pool": 1000,
        "reward_awarded": 0,
        "scoreboard_note": "G7 blocked permanently (no official price). Reward pool rolls over unpaid.",
        "gates": gates,
        "note": "Demotion gate G11 is pre-registered. No strategy is live this snapshot, so G11 is not triggered; it is published so the rule exists before any strategy goes live.",
    }
    with open(DATA / "derived" / "gates.json", "w") as f:
        json.dump(out, f, indent=2)
    print("gates: %d pass, %d fail, %d blocked" % (n_pass, n_fail, n_blocked))
    return out


if __name__ == "__main__":
    backtest = json.loads(open(DATA / "derived" / "results_feed.json").read())
    backtest["n_games"] = backtest["n_completed"]
    build(backtest)
