#!/usr/bin/env python3
"""Shared primitives for the Own4 NFL research pipeline (standard library only)."""
from __future__ import annotations
import csv, html, json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NFL = ROOT / "nfl"
DATA = NFL / "data"
PAGES = NFL / "pages"
ASSETS = NFL / "assets"

OFFICIAL_HOSTS = {
    "www.nfl.com", "nfl.com", "operations.nfl.com", "media.nfl.com",
    "static.www.nfl.com", "www.ncpgambling.org", "docs.scipy.org",
    "www.statsmodels.org", "scikit-learn.org", "www.itl.nist.gov",
    "www.goldennugget.com", "massgaming.com", "api.github.com",
    "github.com", "docs.github.com",
}

TEAM_ABBR = {
    "Patriots":"NE","Seahawks":"SEA","49ers":"SF","Rams":"LA","Bears":"CHI",
    "Panthers":"CAR","Buccaneers":"TB","Bengals":"CIN","Saints":"NO","Lions":"DET",
    "Bills":"BUF","Texans":"HOU","Ravens":"BAL","Colts":"IND","Browns":"CLE",
    "Jaguars":"JAX","Falcons":"ATL","Steelers":"PIT","Jets":"NYJ","Titans":"TEN",
    "Cardinals":"AZ","Chargers":"LAC","Dolphins":"MIA","Raiders":"LV","Packers":"GB",
    "Vikings":"MIN","Commanders":"WAS","Eagles":"PHI","Cowboys":"DAL","Giants":"NYG",
    "Broncos":"DEN","Chiefs":"KC",
}
TEAM_NAME = {v: k for k, v in TEAM_ABBR.items()}

WEEK_URL = {w: f"https://www.nfl.com/schedules/2026/by-week/week-{w}" for w in range(1, 10)}
S_STAND26 = "https://www.nfl.com/standings/league/2026/REG"
S_STAND25 = "https://www.nfl.com/standings/league/2025/REG"
S_SCHEDULE_RELEASE = "https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced"
S_RULEBOOK = "https://operations.nfl.com/rules-officiating/2026-nfl-rulebook"
S_IMPORTANT_DATES = "https://www.nfl.com/news/2026-27-national-football-league-important-dates"
S_BETTING = "https://www.nfl.com/news/nfl-draftkings-fanduel-fanatics-sports-betting-partners"
S_PASSING = "https://www.nfl.com/stats/player-stats/category/passing/2026/REG/all/passingyards/desc"
S_DK = "https://www.goldennugget.com/lake-charles/casino/draftkings-sportsbook-bar-grill/draftkings-sportsbook-house-rules/"
S_DK_PDF = "https://www.goldennugget.com/contentassets/9800d7ef44d6474dad6cd3e69d29dd99/draftkings-gnlc-retail-house-rules-v15.pdf"
S_MGC_PDF = "https://massgaming.com/wp-content/uploads/DraftKings-House-Rules-5.14.24.pdf"
S_PEARSON = "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html"
S_MULTITEST = "https://www.statsmodels.org/dev/generated/statsmodels.stats.multitest.multipletests.html"
S_CALIBRATION = "https://scikit-learn.org/stable/modules/calibration.html"
S_NIST = "https://www.itl.nist.gov/div898/handbook/eda/section3/eda35c.htm"
S_NCPG = "https://www.ncpgambling.org/help-treatment/"
S_PAGES_API = "https://api.github.com/repos/sassnarep3-star/Own4/pages"
S_REPO = "https://github.com/sassnarep3-star/Own4"

HELPLINE = "1-800-MY-RESET"


def esc(x) -> str:
    return html.escape("" if x is None else str(x), quote=True)


def load_json(name):
    with open(DATA / name, encoding="utf-8") as f:
        return json.load(f)


def save_json(name, obj):
    with open(DATA / name, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=False, ensure_ascii=False)
        f.write("\n")


def read_csv(name):
    with open(DATA / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(name, rows, fields):
    with open(DATA / name, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def fnum(x, d=3):
    if x is None or x == "":
        return ""
    if isinstance(x, str):
        return x
    return f"{x:.{d}f}"


def blank():
    return '<span class="blank">blank — unverified</span>'


def links(urls, label="Official ↗"):
    """One or more official source anchors. Every table row must contain at least one."""
    if isinstance(urls, (str, type(None))):
        urls = [urls] if urls else []
    urls = [u for u in urls if u]
    if not urls:
        return blank()
    seen = []
    for u in urls:
        if u not in seen:
            seen.append(u)
    out = []
    for u in seen:
        short = u.replace("https://", "").split("/")[0]
        out.append(f'<a href="{esc(u)}" target="_blank" rel="noopener" title="{esc(u)}">{esc(short)} ↗</a>')
    return " ".join(out)


def badge(text, cls="ok"):
    return f'<span class="badge {cls}">{esc(text)}</span>'


def value_type(t):
    return {"VERIFIED": badge("VERIFIED", "ok"),
            "COMPUTED": badge("COMPUTED", "info"),
            "POLICY": badge("PROJECT POLICY", "warn"),
            "UNVERIFIED": badge("UNVERIFIED", "bad")}.get(t, esc(t))


# ---------------------------------------------------------------------------
# statistics (stdlib implementations; methods cited to official docs)
# ---------------------------------------------------------------------------
def pearson(xs, ys):
    n = len(xs)
    if n < 3 or n != len(ys):
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def _betacf(a, b, x):
    """Continued fraction for the incomplete beta function (Numerical Recipes)."""
    MAXIT, EPS, FPMIN = 300, 3e-14, 1e-300
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
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < EPS:
            break
    return h


def _betai(a, b, x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                  + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def corr_p(r, n):
    """Two-sided p for Pearson r under H0: rho = 0 (Student t, n-2 df)."""
    if r is None or n < 3:
        return None
    if abs(r) >= 1:
        return 0.0
    df = n - 2
    t = abs(r) * math.sqrt(df / (1 - r * r))
    return max(0.0, min(1.0, _betai(df / 2.0, 0.5, df / (df + t * t))))


def fisher_ci(r, n, z=1.959963984540054):
    if r is None or n < 4 or abs(r) >= 1:
        return (None, None)
    zz = math.atanh(r)
    se = 1.0 / math.sqrt(n - 3)
    return (math.tanh(zz - z * se), math.tanh(zz + z * se))


def bh_fdr(pvals):
    """Benjamini/Hochberg adjusted p-values (fdr_bh), original input order."""
    m = len(pvals)
    idx = sorted(range(m), key=lambda i: (pvals[i] is None, pvals[i] if pvals[i] is not None else 1))
    q = [None] * m
    prev = 1.0
    for rank in range(m - 1, -1, -1):
        i = idx[rank]
        p = pvals[i] if pvals[i] is not None else 1.0
        prev = min(prev, p * m / (rank + 1))
        q[i] = min(1.0, max(0.0, prev))
    return q


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (None, None)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))


def binomial_two_sided(k, n, p=0.5):
    """Exact two-sided binomial p-value, computed in log space (safe for large n)."""
    if n == 0:
        return None
    if p <= 0 or p >= 1:
        return 1.0 if k != round(n * p) else 1.0
    lg = math.lgamma
    lp, lq = math.log(p), math.log1p(-p)
    logpmf = [lg(n + 1) - lg(i + 1) - lg(n - i + 1) + i * lp + (n - i) * lq
              for i in range(n + 1)]
    obs = logpmf[k]
    return min(1.0, sum(math.exp(v) for v in logpmf if v <= obs + 1e-9))


def normal_cdf(x, mu=0.0, sigma=1.0):
    return 0.5 * (1 + math.erf((x - mu) / (sigma * math.sqrt(2))))


def phi_2x2(a, b, c, d):
    """Phi coefficient for a 2x2 table [[a,b],[c,d]] plus a normal-approx p."""
    n = a + b + c + d
    r1, r2 = a + b, c + d
    c1, c2 = a + c, b + d
    den = math.sqrt(r1 * r2 * c1 * c2)
    if den == 0:
        return None, None
    phi = (a * d - b * c) / den
    z = phi * math.sqrt(n)
    p = math.erfc(abs(z) / math.sqrt(2))
    return phi, min(1.0, max(0.0, p))


def american_odds(p):
    """Fair (no-vig) American moneyline from a probability."""
    if p is None or p <= 0 or p >= 1:
        return ""
    return f"-{100 * p / (1 - p):.0f}" if p >= 0.5 else f"+{100 * (1 - p) / p:.0f}"


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def median(xs):
    ys = sorted(xs)
    n = len(ys)
    if n == 0:
        return 0.0
    return ys[n // 2] if n % 2 else (ys[n // 2 - 1] + ys[n // 2]) / 2
