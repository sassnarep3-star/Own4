"""Pure-stdlib statistics helpers used by nfl-marketboard.

Every routine is deterministic. No external dependencies.
"""
from __future__ import annotations
import math


# ---------------------------------------------------------------- normal ----
def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


# ------------------------------------------------------- special functions ---
def _betacf(a: float, b: float, x: float) -> float:
    MAXIT, EPS, FPMIN = 200, 3.0e-12, 1.0e-300
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


def betai(a: float, b: float, x: float) -> float:
    """Regularised incomplete beta function I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
             + a * math.log(x) + b * math.log1p(-x))
    bt = math.exp(lbeta)
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def t_sf(t: float, df: float) -> float:
    """One-sided survival P(T > t) for Student-t with df degrees of freedom."""
    if df <= 0:
        return float('nan')
    x = df / (df + t * t)
    p = 0.5 * betai(df / 2.0, 0.5, x)
    return p if t > 0 else 1.0 - p


def t_two_sided_p(t: float, df: float) -> float:
    if df <= 0:
        return float('nan')
    return 2.0 * t_sf(abs(t), df)


# -------------------------------------------------------------- binomial ----
def binom_pmf(k: int, n: int, p: float) -> float:
    if k < 0 or k > n:
        return 0.0
    return math.comb(n, k) * (p ** k) * ((1.0 - p) ** (n - k))


def binom_right_tail(k: int, n: int, p: float) -> float:
    """P(X >= k) for X ~ Binomial(n, p)."""
    if n <= 0:
        return float('nan')
    return sum(binom_pmf(i, n, p) for i in range(k, n + 1))


# ---------------------------------------------------------------- Pearson ---
def pearson(xs: list, ys: list) -> dict:
    """Pearson r with two-sided p-value and a 95% Fisher-z confidence interval.

    Returns r, n, p_value, ci_low, ci_high.  Returns r=None when n < 3 or when
    either series has zero variance (a correlation is then undefined, not zero).
    """
    n = len(xs)
    out = {'n': n, 'r': None, 'p_value': None, 'ci_low': None, 'ci_high': None,
           'note': ''}
    if len(ys) != n:
        raise ValueError('length mismatch')
    if n < 3:
        out['note'] = 'n < 3: correlation not computed'
        return out
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        out['note'] = 'zero variance in one series: correlation undefined'
        return out
    r = sxy / math.sqrt(sxx * syy)
    r = max(-0.999999999999, min(0.999999999999, r))
    df = n - 2
    t = r * math.sqrt(df / (1.0 - r * r))
    p = t_two_sided_p(t, df)
    z = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3) if n > 3 else float('inf')
    lo = math.tanh(z - 1.959963984540054 * se)
    hi = math.tanh(z + 1.959963984540054 * se)
    out.update({'r': r, 'p_value': p, 'ci_low': lo, 'ci_high': hi,
                't_stat': t, 'df': df})
    return out


def phi_coefficient(a: int, b: int, c: int, d: int) -> dict:
    """Phi (= Pearson r) for a 2x2 table [[a,b],[c,d]]; identical to Pearson
    computed on the four indicator series, so `n` is the total count."""
    n = a + b + c + d
    num = a * d - b * c
    den = math.sqrt(float(a + b) * (c + d) * (a + c) * (b + d))
    if den == 0 or n < 3:
        return {'n': n, 'r': None, 'p_value': None, 'ci_low': None,
                'ci_high': None, 'note': 'undefined (empty margin or n<3)'}
    r = num / den
    # Pearson chi-square without continuity correction equals n * phi^2
    chi2 = n * r * r
    p = math.exp(-0.5 * chi2) if n > 0 else float('nan')  # df=1 closed form
    z = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3) if n > 3 else float('inf')
    return {'n': n, 'r': r, 'p_value': p,
            'ci_low': math.tanh(z - 1.959963984540054 * se),
            'ci_high': math.tanh(z + 1.959963984540054 * se),
            'chi2': chi2, 'df': 1}


# --------------------------------------------------------------- betting ----
def american_to_decimal(o: float) -> float:
    """American odds -> decimal payout multiplier (stake included)."""
    if o is None:
        return float('nan')
    if o > 0:
        return 1.0 + o / 100.0
    return 1.0 + 100.0 / abs(o)


def american_to_implied(o: float) -> float:
    """Raw implied probability from American odds (includes the book's margin)."""
    if o is None:
        return float('nan')
    if o > 0:
        return 100.0 / (o + 100.0)
    return abs(o) / (abs(o) + 100.0)


def prob_to_american(p: float) -> float:
    """Fair-probability -> American odds (no margin)."""
    if p is None or p <= 0 or p >= 1:
        return float('nan')
    if p >= 0.5:
        return -100.0 * p / (1.0 - p)
    return 100.0 * (1.0 - p) / p


def devig(home_ml: float, away_ml: float) -> tuple:
    """Two-way vig removal by normalising the raw implied probabilities."""
    ph = american_to_implied(home_ml)
    pa = american_to_implied(away_ml)
    s = ph + pa
    if s <= 0:
        return float('nan'), float('nan')
    return ph / s, pa / s


# ------------------------------------------------------------ description ---
def mean(xs: list) -> float:
    return sum(xs) / len(xs) if xs else float('nan')


def sd(xs: list) -> float:
    n = len(xs)
    if n < 2:
        return float('nan')
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def permutation_p(observed: float, null_draws: list) -> float:
    """One-sided permutation p-value: fraction of null draws >= observed."""
    if not null_draws:
        return float('nan')
    ge = sum(1 for d in null_draws if d >= observed)
    return (ge + 1) / (len(null_draws) + 1)
