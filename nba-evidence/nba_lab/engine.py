"""Small, deterministic standard-library research engine.

All odds are hypothetical fair prices unless an official quote is supplied.
No function in this module places bets or fabricates missing prices.
"""
from __future__ import annotations
from collections import defaultdict
from math import exp, log, sqrt, floor, isfinite
from random import Random
from statistics import mean, stdev


def probability(value: float) -> float:
    if not isfinite(value) or not 0 <= value <= 1:
        raise ValueError("Probability must be finite and in [0,1]")
    return value


def fair_decimal(p: float) -> float:
    p = probability(p)
    if p == 0:
        raise ValueError("Zero-probability event has no finite fair decimal price")
    return 1 / p


def implied_probability(decimal: float) -> float:
    if not isfinite(decimal) or decimal <= 1:
        raise ValueError("Decimal odds must be finite and > 1")
    return 1 / decimal


def remove_vig_two_way(a: float, b: float) -> tuple[float, float]:
    """Proportional normalization; not a claim that this de-vig method is best."""
    x, y = implied_probability(a), implied_probability(b)
    return x / (x + y), y / (x + y)


def ev_per_unit(p: float, decimal: float) -> float:
    return probability(p) * (decimal - 1) - (1 - probability(p))


def half_line(x: float) -> float:
    """Nearest half-integer, excluding integer pushes; ties go upward."""
    if not isfinite(x):
        raise ValueError("Line must be finite")
    return floor(x) + 0.5


def kelly_fraction(p: float, decimal: float, cap: float = 0.01) -> float:
    """Research-only capped Kelly. Missing price never implies a stake."""
    if not isfinite(cap) or not 0 <= cap <= 1:
        raise ValueError("Invalid stake cap")
    b = decimal - 1
    if b <= 0 or not isfinite(b):
        raise ValueError("Invalid decimal price")
    return max(0.0, min(cap, (p * b - (1 - p)) / b))


def settle_single(value: float, line: float, side: str) -> str:
    if side not in {"over", "under"}:
        raise ValueError("Expected over/under")
    if value == line:
        return "push"
    return "win" if (value > line) == (side == "over") else "loss"


def settle_ticket(legs: list[dict]) -> dict:
    """Equal-unit ticket settlement with operator-agnostic explicit assumptions.

    Each leg needs decimal odds and result win/loss/push/void. A push/void
    reduces the decimal payout multiplier to 1. A losing leg loses the ticket.
    An operator's actual rules can differ; this is not a universal sportsbook rule.
    """
    if not legs:
        raise ValueError("Empty ticket")
    multiplier = 1.0
    statuses = []
    for leg in legs:
        status = leg["result"]
        if status not in {"win", "loss", "push", "void"}:
            raise ValueError("Missing/invalid settlement")
        price = fair_decimal(1 / leg["decimal"])
        statuses.append(status)
        if status == "loss":
            return {"result": "loss", "profit": -1.0, "active_legs": sum(s == "win" for s in statuses)}
        if status == "win":
            multiplier *= price
    return {"result": "push" if multiplier == 1 else "win", "profit": multiplier - 1,
            "active_legs": sum(s == "win" for s in statuses)}


def pearson(x: list[float], y: list[float]) -> float | None:
    if len(x) != len(y) or len(x) < 3:
        return None
    mx, my = mean(x), mean(y)
    xx = sum((v - mx) ** 2 for v in x)
    yy = sum((v - my) ** 2 for v in y)
    if xx == 0 or yy == 0:
        return None
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / sqrt(xx * yy)


def residualize_minutes(values: list[float], minutes: list[float]) -> list[float]:
    """Remove fitted linear minutes effect; not a causal playing-time adjustment."""
    m, v = mean(minutes), mean(values)
    denom = sum((x - m) ** 2 for x in minutes)
    slope = sum((x - m) * (y - v) for x, y in zip(minutes, values)) / denom if denom else 0
    return [y - v - slope * (x - m) for x, y in zip(minutes, values)]


def binary_correlation(x: list[int], y: list[int]) -> dict:
    if len(x) != len(y) or not x or any(v not in {0, 1} for v in x + y):
        raise ValueError("Paired binary observations required")
    n = len(x)
    a, b, ab = sum(x) / n, sum(y) / n, sum(i and j for i, j in zip(x, y)) / n
    denominator = a * (1 - a) * b * (1 - b)
    return {"n": n, "p_a": a, "p_b": b, "p_joint": ab,
            "independent_joint": a * b, "joint_lift": ab / (a * b) if a * b else None,
            "phi": (ab - a * b) / sqrt(denominator) if denominator else None}


def brier(probs: list[float], outcomes: list[int]) -> float:
    if len(probs) != len(outcomes) or not probs:
        raise ValueError("Paired nonempty probability/outcome arrays required")
    return mean((probability(p) - y) ** 2 for p, y in zip(probs, outcomes))


def log_loss(probs: list[float], outcomes: list[int]) -> float:
    if len(probs) != len(outcomes) or not probs:
        raise ValueError("Paired nonempty arrays required")
    return mean(-log(max(1e-12, p if y else 1 - p)) for p, y in zip(probs, outcomes))


def mae(predicted: list[float], actual: list[float]) -> float:
    if len(predicted) != len(actual) or not predicted:
        raise ValueError("Paired nonempty arrays required")
    return mean(abs(p - a) for p, a in zip(predicted, actual))


def wilson(successes: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Descriptive binomial interval; do not use for dependent overlapping tickets."""
    if n <= 0 or not 0 <= successes <= n:
        raise ValueError("Invalid binomial counts")
    p = successes / n
    d = 1 + z * z / n
    center = (p + z * z / (2 * n)) / d
    radius = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0, center - radius), min(1, center + radius)


def holm_adjust(pvalues: list[float]) -> list[float]:
    """Family-wise adjusted p-values; caller supplies the complete search family."""
    m = len(pvalues)
    adjusted = [None] * m
    running = 0.0
    for rank, (i, _) in enumerate(sorted(enumerate(pvalues), key=lambda t: t[1])):
        p = probability(pvalues[i])
        running = max(running, min(1.0, (m - rank) * p))
        adjusted[i] = running
    return adjusted


def date_cluster_bootstrap(rows: list[dict], value_key: str, replicates: int, seed: int,
                           alpha: float = 0.05) -> dict | None:
    """Resample whole dates, retaining all same-day dependence in each draw.

    This does not capture between-day dependence or regime changes. At least
    20 distinct dates are required for even a descriptive percentile interval.
    """
    groups = defaultdict(list)
    for row in rows:
        groups[row["date"]].append(row[value_key])
    if len(groups) < 20:
        return None
    keys = sorted(groups)
    rng = Random(seed)
    estimates = []
    for _ in range(replicates):
        sample = [v for _ in keys for v in groups[rng.choice(keys)]]
        estimates.append(mean(sample))
    estimates.sort()
    def quantile(q):
        pos = (len(estimates) - 1) * q
        lo = int(floor(pos))
        hi = min(lo + 1, len(estimates) - 1)
        return estimates[lo] + (estimates[hi] - estimates[lo]) * (pos - lo)
    return {"low": quantile(alpha / 2), "high": quantile(1 - alpha / 2),
            "clusters": len(keys), "replicates": replicates, "seed": seed,
            "method": "date-cluster percentile bootstrap; short-series limitations remain"}


def fit_logistic(features: list[float], labels: list[int], l2: float, iterations: int) -> dict:
    """Two-parameter regularized logistic fit using deterministic gradient descent."""
    if len(features) != len(labels) or not features or any(y not in {0, 1} for y in labels):
        raise ValueError("Invalid logistic training data")
    center = mean(features)
    scale = stdev(features) if len(features) > 1 and stdev(features) > 0 else 1.0
    x = [(f - center) / scale for f in features]
    intercept = log((sum(labels) + 0.5) / (len(labels) - sum(labels) + 0.5))
    slope = 0.0
    n = len(x)
    for _ in range(iterations):
        errors = [1 / (1 + exp(-(intercept + slope * xi))) - y for xi, y in zip(x, labels)]
        g0 = sum(errors) / n
        g1 = sum(e * xi for e, xi in zip(errors, x)) / n + l2 * slope / n
        intercept -= 0.2 * g0
        slope -= 0.2 * g1
    return {"intercept": intercept, "slope": slope, "center": center, "scale": scale,
            "l2": l2, "iterations": iterations, "n": n}


def logistic_predict(model: dict, feature: float) -> float:
    z = model["intercept"] + model["slope"] * (feature - model["center"]) / model["scale"]
    return 1 / (1 + exp(-max(-35.0, min(35.0, z))))


class RollingStrength:
    """Shrunk scoring-for/against means; update only after a date completes."""
    def __init__(self, prior_mean: float, prior_games: int = 5):
        self.prior_mean = prior_mean
        self.prior_games = prior_games
        self.stats = defaultdict(lambda: [0, 0.0, 0.0])

    def rating(self, team: str) -> tuple[float, float]:
        n, scored, allowed = self.stats[team]
        k = self.prior_games
        return (scored + k * self.prior_mean) / (n + k), (allowed + k * self.prior_mean) / (n + k)

    def predict(self, team1: str, team2: str) -> dict:
        off1, def1 = self.rating(team1)
        off2, def2 = self.rating(team2)
        p1 = (off1 + def2) / 2
        p2 = (off2 + def1) / 2
        return {"mean1": p1, "mean2": p2, "margin": p1 - p2, "total": p1 + p2,
                "prior_games1": self.stats[team1][0], "prior_games2": self.stats[team2][0]}

    def update(self, team1: str, score1: float, team2: str, score2: float) -> None:
        for team, scored, allowed in ((team1, score1, score2), (team2, score2, score1)):
            s = self.stats[team]
            s[0] += 1
            s[1] += scored
            s[2] += allowed


def release_gates(gates: list[dict]) -> dict:
    """Every gate must explicitly pass; unknown is never a pass."""
    allowed = {"pass", "fail", "unverified"}
    if not gates or any(g.get("status") not in allowed for g in gates):
        raise ValueError("Explicit nonempty gate statuses required")
    qualified = all(g["status"] == "pass" for g in gates)
    return {"qualified": qualified, "reward_points": 0,
            "status": "eligible for research ranking" if qualified else "not eligible",
            "blocking_gates": [g["id"] for g in gates if g["status"] != "pass"]}
