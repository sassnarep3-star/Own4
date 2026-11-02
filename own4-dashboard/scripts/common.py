"""Shared helpers for the Own4 NBA research pipeline.

Only the Python standard library is used. Every computation in this repository is deterministic
(reproducible RNG seeds) so a reviewer can re-run the exact numbers shown on the site.
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
DERIVED = ROOT / "data" / "derived"
STRATEGIES = ROOT / "data" / "strategies"
CORRELATIONS = ROOT / "data" / "correlations"
LEADERBOARD = ROOT / "data" / "leaderboard"
VERIFICATION = ROOT / "data" / "verification"
SITE_DATA = ROOT / "site-data"

for _d in (DERIVED, STRATEGIES, CORRELATIONS, LEADERBOARD, VERIFICATION, SITE_DATA):
    _d.mkdir(parents=True, exist_ok=True)


def read_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False, sort_keys=False)
        fh.write("\n")


SRC = read_json(ROOT / "data" / "sources.json")["sources"]
ALLOWLIST = set(read_json(ROOT / "data" / "sources.json")["official_host_allowlist"])
TEAMS = {r["code"]: r for r in read_json(RAW / "teams.json")["rows"]}


def is_official(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return False
    return any(host == h or host.endswith("." + h) for h in ALLOWLIST)


# --------------------------------------------------------------------------------------
# Statistics
# --------------------------------------------------------------------------------------
def mean(xs):
    return sum(xs) / len(xs)


def pearson(xs, ys):
    n = len(xs)
    if n != len(ys) or n < 3:
        return None
    mx, my = mean(xs), mean(ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    out = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            out[order[k]] = avg
        i = j + 1
    return out


def spearman(xs, ys):
    return pearson(ranks(xs), ranks(ys))


def permutation_p(xs, ys, iterations=20000, seed=20261102):
    """Two-sided permutation p-value for Pearson r, fixed seed for reproducibility."""
    if len(xs) != len(ys) or len(xs) < 3:
        return None
    obs = pearson(xs, ys)
    if obs is None:
        return None
    rng = random.Random(seed)
    ys_mut = list(ys)
    extreme = 0
    for _ in range(iterations):
        rng.shuffle(ys_mut)
        r = pearson(xs, ys_mut)
        if r is not None and abs(r) >= abs(obs) - 1e-12:
            extreme += 1
    return (extreme + 1) / (iterations + 1)


def bootstrap_ci(xs, ys, iterations=5000, seed=20261102, alpha=0.05):
    """Percentile bootstrap CI for Pearson r."""
    if len(xs) != len(ys) or len(xs) < 4:
        return (None, None)
    rng = random.Random(seed)
    n = len(xs)
    vals = []
    for _ in range(iterations):
        idx = [rng.randrange(n) for _ in range(n)]
        r = pearson([xs[i] for i in idx], [ys[i] for i in idx])
        if r is not None:
            vals.append(r)
    if not vals:
        return (None, None)
    vals.sort()
    lo = vals[int((alpha / 2) * len(vals))]
    hi = vals[min(len(vals) - 1, int((1 - alpha / 2) * len(vals)))]
    return (lo, hi)


def binom_two_sided(k, n, p=0.5):
    """Exact two-sided binomial p-value (sum of probabilities <= observed)."""
    if n == 0:
        return None
    obs = math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))
    total = 0.0
    for i in range(n + 1):
        pi = math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i))
        if pi <= obs + 1e-15:
            total += pi
    return min(1.0, total)


def wilson_ci(k, n, z=1.96):
    if n == 0:
        return (None, None)
    ph = k / n
    den = 1 + z * z / n
    ctr = (ph + z * z / (2 * n)) / den
    half = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return (max(0.0, ctr - half), min(1.0, ctr + half))


def sigmoid(z):
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


def fit_logistic_slope(ratings, win_pcts):
    """Fit p = sigmoid(k * rating) by minimising SSE over a deterministic k grid + refinement.

    All inputs are official season values; no external constants are introduced.
    """
    best_k, best_sse = 0.0, float("inf")
    k = 0.0
    while k <= 1.0:
        sse = sum((win_pcts[i] - sigmoid(k * ratings[i])) ** 2 for i in range(len(ratings)))
        if sse < best_sse:
            best_sse, best_k = sse, k
        k += 0.0005
    step = 0.0005
    while step > 1e-7:
        for cand in (best_k - step, best_k + step):
            sse = sum((win_pcts[i] - sigmoid(cand * ratings[i])) ** 2 for i in range(len(ratings)))
            if sse < best_sse:
                best_sse, best_k = sse, cand
        step /= 2
    return best_k, best_sse


def american_odds(p):
    """Fair (zero-margin) American odds for implied probability p."""
    if p is None or p <= 0 or p >= 1:
        return None
    if p >= 0.5:
        return -round(100 * p / (1 - p))
    return round(100 * (1 - p) / p)


def fmt(v, nd=3):
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, int):
        return str(v)
    return f"{v:.{nd}f}"
