"""Small statistics helpers.

Standard library only. Everything is deterministic: every random draw uses an explicit seed,
so a re-run reproduces every published number, and CI can assert on it.
"""
import math
import random


def mean(xs):
    return sum(xs) / float(len(xs)) if xs else None


def stdev(xs):
    if len(xs) < 2:
        return None
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def pearson(xs, ys):
    n = len(xs)
    if n < 3 or n != len(ys):
        return None
    mx, my = mean(xs), mean(ys)
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def phi_from_binary(xs, ys):
    """Phi coefficient for two 0/1 vectors; equals Pearson on binary data."""
    return pearson([float(x) for x in xs], [float(y) for y in ys])


def _betacf(a, b, x):
    """Continued fraction for the incomplete beta function (Lentz's method)."""
    MAXIT, EPS, FPMIN = 200, 3e-16, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < EPS:
            break
    return h


def betai(a, b, x):
    """Regularised incomplete beta function I_x(a, b)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(lbeta + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def t_sf(t, df):
    """Upper tail probability of Student's t."""
    if df <= 0:
        return None
    x = df / (df + t * t)
    p = 0.5 * betai(df / 2.0, 0.5, x)
    return p if t > 0 else 1.0 - p


def corr_p_value(r, n):
    """Two-sided p-value for a Pearson correlation under H0: rho = 0."""
    if r is None or n < 3:
        return None
    if abs(r) >= 1.0:
        return 0.0
    t = r * math.sqrt((n - 2) / max(1e-15, (1 - r * r)))
    return t_sf(abs(t), n - 2) * 2.0


def norm_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def fisher_ci(r, n, z=1.959963985):
    """95% CI for a correlation via Fisher z."""
    if r is None or n < 4:
        return None
    r = max(-0.999999, min(0.999999, r))
    zr = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3.0)
    lo, hi = zr - z * se, zr + z * se
    return [math.tanh(lo), math.tanh(hi)]


def benjamini_hochberg(pvals, q=0.05):
    """BH step-up. Returns (rejected_flags, thresholds) in the input order."""
    m = len(pvals)
    if m == 0:
        return [], []
    order = sorted(range(m), key=lambda i: pvals[i])
    thresh = [0.0] * m
    k_max = 0
    for rank, idx in enumerate(order, start=1):
        t = q * rank / m
        thresh[idx] = t
        if pvals[idx] <= t:
            k_max = rank
    rejected = [False] * m
    if k_max:
        cutoff = q * k_max / m
        for idx in order:
            if pvals[idx] <= cutoff:
                rejected[idx] = True
    return rejected, thresh


def bootstrap_ci(values, stat=mean, reps=2000, seed=20261113, alpha=0.05, cluster=None):
    """Percentile bootstrap. `cluster` groups rows so correlated rows resample together."""
    if not values:
        return None
    rng = random.Random(seed)
    out = []
    if cluster is None:
        n = len(values)
        for _ in range(reps):
            sample = [values[rng.randrange(n)] for _ in range(n)]
            out.append(stat(sample))
    else:
        groups = {}
        for key, v in zip(cluster, values):
            groups.setdefault(key, []).append(v)
        keys = list(groups)
        n = len(keys)
        for _ in range(reps):
            pick = [keys[rng.randrange(n)] for _ in range(n)]
            flat = [v for k in pick for v in groups[k]]
            out.append(stat(flat))
    out.sort()
    lo = out[int(alpha / 2.0 * reps)]
    hi = out[min(reps - 1, int((1 - alpha / 2.0) * reps))]
    return [lo, hi]


def permutation_p(observed, null_draws, greater_is_better=True):
    """Two-sided-ish empirical p: share of null draws at least as extreme as observed."""
    if not null_draws:
        return None
    if greater_is_better:
        hits = sum(1 for d in null_draws if d >= observed)
    else:
        hits = sum(1 for d in null_draws if d <= observed)
    return (hits + 1.0) / (len(null_draws) + 1.0)


def profit_units(odds_decimal_minus110=1.909090909):
    """Return on a 1-unit win at the standard -110 price, and -1 on a loss."""
    return odds_decimal_minus110 - 1.0


def american_to_decimal(american):
    a = float(american)
    return 1.0 + (a / 100.0 if a > 0 else 100.0 / abs(a))


def kelly_fraction(p, decimal_odds):
    b = decimal_odds - 1.0
    if b <= 0:
        return 0.0
    f = (p * b - (1 - p)) / b
    return max(0.0, f)
