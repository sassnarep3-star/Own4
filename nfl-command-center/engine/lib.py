"""Shared helpers for the NFL Command Center engine (standard library only)."""
import csv
import json
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
DERIVED = os.path.join(DATA, "derived")
RAW = os.path.join(DATA, "raw")
OFFICIAL = os.path.join(DATA, "official")

SEED = 20261113
ALIAS = {"ARI": "AZ"}  # the third-party archive uses ARI; NFL.com uses AZ
FRANCHISE = {"STL": "LA", "SD": "LAC", "OAK": "LV"}  # relocations, to keep one rating per franchise


# ---------------------------------------------------------------- distributions
def norm_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def norm_ppf(p):
    """Acklam's rational approximation to the standard normal inverse CDF."""
    if not 0.0 < p < 1.0:
        raise ValueError("p out of range")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    plow, phigh = 0.02425, 1.0 - 0.02425
    if p < plow:
        q = math.sqrt(-2.0 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
    if p > phigh:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
           (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0)


def fisher_ci(r, n, conf=0.95):
    """Fisher z confidence interval for a Pearson correlation coefficient."""
    if n < 4 or r is None:
        return None, None
    r = max(min(r, 0.999999), -0.999999)
    z = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3)
    zc = norm_ppf(0.5 + conf / 2.0)
    lo, hi = z - zc * se, z + zc * se
    return math.tanh(lo), math.tanh(hi)


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def t_test_p(r, n):
    """Two-sided p-value for a Pearson correlation via the t approximation."""
    if r is None or n < 4:
        return None
    r = max(min(r, 0.999999), -0.999999)
    t = r * math.sqrt((n - 2) / (1 - r * r))
    df = n - 2
    # two-sided p from the t distribution via the regularised incomplete beta
    x = df / (df + t * t)
    return betainc(df / 2.0, 0.5, x)


def betainc(a, b, x):
    """Regularised incomplete beta function I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    front = math.exp(math.log(x) * a + math.log(1 - x) * b - lbeta) / a
    if x < (a + 1) / (a + b + 2):
        return front * betacf(a, b, x)
    return 1.0 - math.exp(math.log(1 - x) * b + math.log(x) * a - lbeta) / b * betacf(b, a, 1 - x)


def betacf(a, b, x):
    tiny = 1e-30
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 3e-16:
            break
    return h


def bh_fdr(pairs):
    """Benjamini-Hochberg FDR adjustment. pairs = [(key, p)] -> {key: q}."""
    items = [(k, p) for k, p in pairs if p is not None]
    items.sort(key=lambda kv: kv[1])
    m = len(items)
    out = {}
    prev = 1.0
    for i in range(m - 1, -1, -1):
        k, p = items[i]
        q = min(prev, p * m / (i + 1))
        out[k] = q
        prev = q
    return out


def bootstrap_ci(values, stat_fn, n_boot=10000, conf=0.95, seed=SEED):
    if not values:
        return None, None
    rng = random.Random(seed)
    n = len(values)
    stats = []
    for _ in range(n_boot):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        s = stat_fn(sample)
        if s is not None:
            stats.append(s)
    if len(stats) < 100:
        return None, None
    stats.sort()
    lo = stats[int((1 - conf) / 2 * len(stats))]
    hi = stats[int((1 + conf) / 2 * len(stats)) - 1]
    return lo, hi


def permutation_p(values, stat_fn, n_perm=10000, seed=SEED, one_sided="greater"):
    """Permutation test: shuffle the values, recompute the statistic."""
    if len(values) < 3:
        return None
    observed = stat_fn(values)
    if observed is None:
        return None
    rng = random.Random(seed)
    pool = list(values)
    hits = 0
    for _ in range(n_perm):
        rng.shuffle(pool)
        s = stat_fn(pool)
        if s is None:
            continue
        if one_sided == "greater":
            if s >= observed:
                hits += 1
        else:
            if abs(s) >= abs(observed):
                hits += 1
    return (hits + 1) / (n_perm + 1)


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def stdev(xs):
    xs = [x for x in xs if x is not None]
    if len(xs) < 2:
        return None
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


# ------------------------------------------------------------------- data files
def load_games(include_unplayed=False):
    """Load the third-party archive, sort chronologically.

    By default only played games are returned. With include_unplayed the
    scheduled games that have no result yet are appended at the end of the
    chronological order, flagged with played=False."""
    path = os.path.join(RAW, "nfldata_games.csv")
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if not r["result"]:
                if not include_unplayed:
                    continue
            h = FRANCHISE.get(ALIAS.get(r["home_team"], r["home_team"]), ALIAS.get(r["home_team"], r["home_team"]))
            a = FRANCHISE.get(ALIAS.get(r["away_team"], r["away_team"]), ALIAS.get(r["away_team"], r["away_team"]))
            g = {
                "game_id": r["game_id"],
                "season": int(r["season"]),
                "week": int(r["week"]),
                "gameday": r["gameday"],
                "away": a,
                "home": h,
                "played": bool(r["result"]),
                "away_pts": int(r["away_score"]) if r["away_score"] else None,
                "home_pts": int(r["home_score"]) if r["home_score"] else None,
                "margin": int(r["result"]) if r["result"] else None,   # home minus away
                "total": int(r["total"]) if r["total"] else None,
                "overtime": r["overtime"] != "0",
                "location": r["location"],           # Home / Away / Neutral
                "spread_line": float(r["spread_line"]) if r["spread_line"] else None,
                "home_spread_odds": r["home_spread_odds"],
                "away_spread_odds": r["away_spread_odds"],
                "total_line": float(r["total_line"]) if r["total_line"] else None,
                "over_odds": r["over_odds"],
                "under_odds": r["under_odds"],
                "home_moneyline": r["home_moneyline"],
                "away_moneyline": r["away_moneyline"],
                "away_rest": int(r["away_rest"]) if r["away_rest"] else None,
                "home_rest": int(r["home_rest"]) if r["home_rest"] else None,
                "stadium": r["stadium"],
                "roof": r["roof"],
                "surface": r["surface"],
                "away_qb": r["away_qb_name"],
                "home_qb": r["home_qb_name"],
            }
            g["home_line"] = None if g["spread_line"] is None else -g["spread_line"]
            rows.append(g)
    rows.sort(key=lambda g: (g["gameday"], g["season"], g["week"], g["game_id"]))
    return rows


def decimal_odds(odds):
    """American odds to decimal odds. None/blank -> None."""
    if odds in (None, ""):
        return None
    try:
        o = float(odds)
    except (TypeError, ValueError):
        return None
    if o == 0:
        return None
    if o > 0:
        return 1.0 + o / 100.0
    return 1.0 + 100.0 / abs(o)


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def dump_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, sort_keys=False, ensure_ascii=False)
        fh.write("\n")
