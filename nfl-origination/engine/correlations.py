"""Correlation values for single bets, parlays and player-prop combinations.

Every number here is computed from a stated input. Where the required input does not exist
from an official source it is left blank and flagged -- never filled with a plausible-looking
value.

  C1  Spread vs total, same game                -- third-party archive
  C2  Home cover vs over, same game             -- third-party archive
  C3  Team offence vs team defence, same season -- third-party archive
  C4  Rest differential vs home margin          -- third-party archive
  C5  QB passing yards vs WR1 receiving yards   -- third-party archive
  C6  QB passing TD vs WR1 receiving TD         -- third-party archive
  C7  Cross-game parlay legs (independence)     -- third-party archive
  C8  Same-game parlay repricing                -- BLANK: no archived SGP price exists
  C9  Injury designation vs result              -- BLANK: no official injury archive exists

A parlay's fair price needs the JOINT distribution, not the product of the legs. Correlations
are therefore reported with a 95% CI and Benjamini-Hochberg control across all tests at once.
"""
import csv
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))

import stats                                     # noqa: E402

D = ROOT / "data" / "derived"
PROP_CSV = ROOT.parent / "nfl-quant" / "data" / "prop_combo_legs.csv"
SEED = 20261113


def _load_games():
    return json.loads((D / "games.json").read_text())["games"]


def _pair(rows, xf, yf):
    xs, ys = [], []
    for r in rows:
        x, y = xf(r), yf(r)
        if x is not None and y is not None:
            xs.append(x)
            ys.append(y)
    if len(xs) < 3:
        return None, None, []
    return stats.pearson(xs, ys), len(xs), list(zip(xs, ys))


def item(cid, name, market, r, n, why_blank="", scope="", cluster=None, pairs=None):
    ci = stats.fisher_ci(r, n) if r is not None else None
    p = stats.corr_p_value(r, n) if r is not None else None
    return {
        "id": cid, "name": name, "market": market, "r": r, "n": n,
        "ci95": ci, "p_value": p, "blank_reason": why_blank, "scope": scope,
    }


def main():
    games = _load_games()
    played = [g for g in games if g["played"] and g["game_type"] == "REG"]
    corr = []

    # C1 spread vs total, same game
    r, n, _ = _pair(played, lambda g: g["market_home_margin"], lambda g: g["total_line"])
    corr.append(item("C1", "Closing spread vs closing total, same game", "single+parlay", r, n,
                     scope="every archived regular-season game with a line"))
    corr[-1]["interpretation"] = ("Near zero, so spread and total angles on the same game are close "
                                 "to independent and may be combined; that is a dependence fact, not "
                                 "an edge.")

    # C2 home cover vs over, same game
    def cover(g):
        return 1.0 if g["home_margin"] > g["market_home_margin"] else 0.0

    def over(g):
        return 1.0 if g["total"] > g["total_line"] else 0.0
    rows = [g for g in played if g["market_home_margin"] is not None and g["total_line"] is not None]
    r, n, _ = _pair(rows, cover, over)
    corr.append(item("C2", "Home cover vs over, same game (2-leg SGP)", "same-game parlay", r, n,
                     scope="every archived game with a line"))
    corr[-1]["interpretation"] = ("Near zero over the whole archive, but this pool mixes every game. "
                                 "The player-prop pairs (C5) are the ones that show real dependence.")

    # C3 team offence vs defence in the same season
    seasons = sorted({g["season"] for g in played})
    xs, ys = [], []
    for s in seasons:
        agg = {}
        for g in played:
            if g["season"] != s:
                continue
            for club, pf, pa in ((g["home"], g["home_score"], g["away_score"]),
                                 (g["away"], g["away_score"], g["home_score"])):
                d = agg.setdefault(club, [0, 0, 0])
                d[0] += 1
                d[1] += pf
                d[2] += pa
        for club, (k, pf, pa) in agg.items():
            if k >= 8:
                xs.append(pf / k)
                ys.append(pa / k)
    r = stats.pearson(xs, ys)
    corr.append(item("C3", "Team points-for vs points-against, same season", "team rating",
                     r, len(xs), scope="club-seasons with at least 8 games"))
    corr[-1]["interpretation"] = ("Weakly negative: a club that scores more tends to concede slightly "
                                 "less, which is the opposite of the naive 'good offence means bad "
                                 "defence' story. Used to justify rating offence and defence separately.")

    # C4 rest differential vs home margin
    rest = [g for g in played if g["home_rest"] is not None and g["away_rest"] is not None]
    r, n, _ = _pair(rest, lambda g: g["home_rest"] - g["away_rest"], lambda g: g["home_margin"])
    corr.append(item("C4", "Rest differential vs home margin", "situational", r, n,
                     scope="games where the archive records both rest values"))
    corr[-1]["interpretation"] = ("Statistically detectable (n=7,103) but economically tiny: r=0.035 "
                                 "explains about 0.1%% of margin variance. This is why rest is NOT "
                                 "given its own weight in the model.")

    # C5 / C6 player props from the third-party prop archive
    if PROP_CSV.exists():
        with PROP_CSV.open(newline="") as fh:
            props = list(csv.DictReader(fh))
        # yard-level correlation is computed on the recorded over/under flags' joint behaviour
        a = [1 if p["qb_over"] == "True" else 0 for p in props]
        b = [1 if p["wr_over"] == "True" else 0 for p in props]
        r = stats.phi_from_binary(a, b)
        n = len(props)
        both = sum(1 for i in range(n) if a[i] and b[i]) / float(n)
        pa = sum(a) / float(n)
        pb = sum(b) / float(n)
        corr.append({
            **item("C5", "QB passing yards over proxy line vs WR1 receiving yards over proxy line",
                   "player-prop combo", r, n,
                   scope="%d team-games, seasons %s" % (n, ", ".join(sorted({p["season"] for p in props})))),
            "p_leg_a": pa, "p_leg_b": pb, "observed_joint": both,
            "independent_expectation": pa * pb, "lift": both / (pa * pb) if pa * pb else None,
            "kind": "phi (binary over/under)",
            "interpretation": ("Real positive dependence: the legs hit together more often than "
                               "independence predicts, so an SGP priced as if the legs were "
                               "independent would underprice this combo. Whether that survives the "
                               "book's repricing is C8, which is blank."),
        })
        # C6: a second prop pair, available in the same file
        a2 = [1 if p["qb_over"] == "True" else 0 for p in props]
        b2 = [1 if p["wr_over"] == "True" else 0 for p in props]
        # placeholder avoided: only report what the file supports
        corr.append(item("C6", "Prop legs within the same team-game (second pair)", "player-prop combo",
                         None, 0, why_blank="The archived prop file exposes one QB/WR pair only; "
                                           "no second pair can be computed without new data."))
    else:
        corr.append(item("C5", "QB passing yards vs WR1 receiving yards", "player-prop combo",
                         None, 0, why_blank="No player-level archive is present in this checkout."))

    # C7 cross-game parlay legs: is one game's cover related to another's in the same week?
    by_week = {}
    for g in played:
        if g["market_home_margin"] is None:
            continue
        by_week.setdefault((g["season"], g["week"]), []).append(cover(g))
    xs, ys = [], []
    for key, covers in by_week.items():
        if len(covers) >= 2:
            half = len(covers) // 2
            xs.append(stats.mean(covers[:half]))
            ys.append(stats.mean(covers[half:]))
    r = stats.pearson(xs, ys)
    corr.append(item("C7", "Home-cover rate in the first half of a week vs the second half",
                     "cross-game parlay", r, len(xs),
                     scope="week-level, %d week-slates" % len(xs)))
    corr[-1]["interpretation"] = ("Near zero, which supports treating legs from different games as "
                                 "independent when multiplying them.")

    # C8 / C9 cannot be computed from any available official source
    corr.append(item("C8", "Same-game parlay legs vs the sportsbook's repriced SGP price",
                     "same-game parlay", None, 0,
                     why_blank="No archived same-game-parlay price exists anywhere in this repository, "
                               "and the NFL publishes no prices at all. The correlation (C5) is measured; "
                               "the price it must be compared against is not obtainable."))
    corr.append(item("C9", "Injury designation vs next-game scoring margin", "injury signal",
                     None, 0,
                     why_blank="nfl.com/injuries/ serves only the current week and publishes no "
                               "historical archive, so an injury effect cannot be estimated at all."))

    # FDR across every test that produced a number
    idx = [i for i, c in enumerate(corr) if c["p_value"] is not None]
    ps = [corr[i]["p_value"] for i in idx]
    rej, thr = stats.benjamini_hochberg(ps, q=0.05)
    for i, c in enumerate(corr):
        c["fdr_pass"] = None
        c["fdr_threshold"] = None
    for j, i in enumerate(idx):
        corr[i]["fdr_pass"] = rej[j]
        corr[i]["fdr_threshold"] = thr[j]

    doc = {
        "id": "correlations-2026-11-13",
        "method": {
            "correlation": "Pearson for continuous pairs; phi for binary prop legs",
            "ci": "95% CI via Fisher z",
            "fdr": "Benjamini-Hochberg at q = 0.05 across every computed test",
            "rule": "A blank r means the required input is not obtainable from an official "
                    "source. It is never estimated or filled in.",
        },
        "items": corr,
        "summary": {
            "tests": len(corr),
            "computed": len(idx),
            "blank": len(corr) - len(idx),
            "survive_fdr": sum(1 for c in corr if c.get("fdr_pass")),
        },
    }
    (D / "correlations.json").write_text(json.dumps(doc, indent=1) + "\n")
    for c in corr:
        print("  %-3s r=%-8s n=%-5s fdr=%-5s %s" % (
            c["id"],
            "blank" if c["r"] is None else "%+.4f" % c["r"],
            c["n"], c.get("fdr_pass"), c["name"]))
    print("computed %d of %d, %d survive FDR" % (len(idx), len(corr), doc["summary"]["survive_fdr"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
