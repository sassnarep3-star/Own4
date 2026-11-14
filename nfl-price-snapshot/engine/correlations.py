"""Correlations computed ONLY from officially sourced numbers.

Every input comes from the official nfl.com standings (PF, PA, W, L, net
points) read on 2026-11-14. n is published with each value. Player-prop and
same-game-parlay correlations are BLANK because the NFL publishes no official
per-game player logs (nfl.com/stats/ is client-rendered; no official download
feed was established).

Method: Pearson r, 95% CI via Fisher z, two-sided p-value. No multiple-testing
correction is claimed here; each value stands alone with its n.
"""
import json
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None, n
    mx = sum(xs) / n; my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx == 0 or syy == 0:
        return 0.0, n
    r = sxy / math.sqrt(sxx * syy)
    return r, n


def ci_and_p(r, n):
    if r is None or n < 4:
        return None, None, None
    z = 0.5 * math.log((1.0 + r) / (1.0 - r)) if abs(r) < 1 else (1e9 if r > 0 else -1e9)
    se = 1.0 / math.sqrt(n - 3)
    lo_z, hi_z = z - 1.96 * se, z + 1.96 * se
    lo = (math.exp(2 * lo_z) - 1) / (math.exp(2 * lo_z) + 1)
    hi = (math.exp(2 * hi_z) - 1) / (math.exp(2 * hi_z) + 1)
    # two-sided p via t = r*sqrt((n-2)/(1-r^2)), df = n-2 (normal approx)
    if abs(r) >= 1:
        p = 0.0
    else:
        t = r * math.sqrt((n - 2) / max(1e-12, 1.0 - r * r))
        df = n - 2
        # student t two-sided tail (normal approximation adequate for reporting)
        p = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(t) / math.sqrt(2.0 * (df / (df + t * t))))))
    return round(lo, 4), round(hi, 4), round(p, 6)


def build():
    st = json.loads(open(DATA / "official" / "standings_2026-11-14.json").read())
    teams = {}
    for r in st["rows"]:
        teams[r[0]] = {
            "abbr": r[0], "w": r[2], "l": r[3], "t": r[4],
            "pf": r[6], "pa": r[7], "net": r[8],
            "games": r[2] + r[3] + r[4],
        }
    abbrs = sorted(teams)
    n = len(abbrs)

    def col(key):
        if key == "pf_g":
            return [teams[a]["pf"] / max(1, teams[a]["games"]) for a in abbrs]
        if key == "pa_g":
            return [teams[a]["pa"] / max(1, teams[a]["games"]) for a in abbrs]
        return [teams[a][key] for a in abbrs]

    tests = [
        ("C1", "Wins vs Points For", "w", "pf"),
        ("C2", "Wins vs Points Against", "w", "pa"),
        ("C3", "Point differential vs Wins", "net", "w"),
        ("C4", "Points For vs Points Against", "pf", "pa"),
        ("C5", "Points For per game vs Wins", "pf_g", "w"),
    ]
    items = []
    for tid, name, a, b in tests:
        xa = col(a)
        xb = col(b)
        r, nn = pearson(xa, xb)
        lo, hi, p = ci_and_p(r, nn)
        items.append({
            "id": tid, "name": name,
            "var_a": a, "var_b": b,
            "source": "official standings PF/PA/W/L (nfl.com/standings/league/2026/REG)",
            "r": None if r is None else round(r, 4),
            "n": nn,
            "ci95": [lo, hi] if lo is not None else None,
            "p_value": p,
            "note": "All inputs from official standings; n published with each value.",
        })

    # Blocked: player-prop / same-game correlations (no official per-game logs)
    blocked = [
        {"id": "C6", "name": "QB passing yards vs WR1 receiving yards (same game)",
         "blank_reason": "No official per-game player log exists; nfl.com/stats/ is client-rendered and no official download feed was established. Left blank (flagged).",
         "r": None, "n": None, "ci95": None, "p_value": None,
         "source": "https://www.nfl.com/stats/"},
        {"id": "C7", "name": "Same-game-parlay repriced dependence (market price)",
         "blank_reason": "No archived same-game-parlay price exists; the NFL publishes no odds. Left blank (flagged).",
         "r": None, "n": None, "ci95": None, "p_value": None,
         "source": "https://www.nfl.com/games"},
    ]

    out = {
        "id": "correlations-2026-w10",
        "season": 2026,
        "week": 10,
        "snapshot": "2026-11-14",
        "source_url": "https://www.nfl.com/standings/league/2026/REG",
        "n_teams": n,
        "tests_computed": len(items),
        "tests_blocked": len(blocked),
        "items": items + blocked,
        "note": "Computed correlations use only officially sourced numbers (standings) and publish n. Blocked items name the missing input rather than inventing a value.",
    }
    with open(DATA / "derived" / "correlations.json", "w") as f:
        json.dump(out, f, indent=2)
    print("correlations: %d computed, %d blocked" % (len(items), len(blocked)))
    return out


if __name__ == "__main__":
    build()
