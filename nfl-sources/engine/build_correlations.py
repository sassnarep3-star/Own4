"""S4 — the registered correlation set, computed only from officially sourced numbers.

Every value carries its n, the two-sided p, and a Fisher-z 95% interval. A correlation that would need
a price, a prop line, a snap count or a depth rank is not estimated: it is published blank with the
reason and the clearing number.
"""
import os
from datetime import date

from common import (DATA, REGISTERED_UTC, read_json, write_json, mean, pearson, p_two_sided,
                    fisher_ci, sd)

STANDINGS_URL = "https://www.nfl.com/standings/league/2026/REG"


def rest_days(games):
    """Days between a club's previous game and this one, from the printed dates only."""
    last = {}
    out = {}
    for g in sorted(games, key=lambda x: (x["date_iso"], x["game_id"])):
        d = date.fromisoformat(g["date_iso"])
        for side in ("home", "away"):
            t = g[side]
            if t in last:
                out[(g["game_id"], t)] = (d - last[t]).days
            last[t] = d
    return out


def main():
    res = read_json(os.path.join(DATA, "results.json"))
    games = sorted(res["rows"], key=lambda g: (g["date_iso"], g["game_id"]))
    rest = rest_days(games)

    computed, blank = [], []

    # CR-01 home margin vs game total
    hm = [g["home_pts"] - g["away_pts"] for g in games]
    tot = [g["home_pts"] + g["away_pts"] for g in games]
    r = pearson(hm, tot)
    computed.append({
        "id": "CR-01", "name": "Home margin vs game total",
        "inputs": "official final scores only", "n": len(hm), "r": round(r, 4),
        "p": round(p_two_sided(r, len(hm)), 4), "ci95": [round(x, 4) for x in fisher_ci(r, len(hm))],
        "reading": "Home margin and total are nearly orthogonal on this sample.",
        "source_url": STANDINGS_URL,
        "note": "computed from nfl-sources/data/results.json, whose rows each cite their official week page",
    })

    # CR-02 a club's points scored, consecutive games
    xs, ys = [], []
    by_team = {}
    for g in games:
        by_team.setdefault(g["home"], []).append((g["date_iso"], g["home_pts"]))
        by_team.setdefault(g["away"], []).append((g["date_iso"], g["away_pts"]))
    for t, seq in by_team.items():
        seq.sort()
        for a, b in zip(seq, seq[1:]):
            xs.append(a[1])
            ys.append(b[1])
    r = pearson(xs, ys)
    computed.append({
        "id": "CR-02", "name": "A club's points scored, consecutive games",
        "inputs": "official final scores only",
        "n": len(xs), "r": round(r, 4), "p": round(p_two_sided(r, len(xs)), 4),
        "ci95": [round(x, 4) for x in fisher_ci(r, len(xs))],
        "reading": ("A small positive autocorrelation: last week's scoring barely predicts this week's. "
                    "n counts ordered pairs of games, not games."),
        "source_url": STANDINGS_URL,
    })

    # CR-03 points scored vs points allowed, same game (club level)
    x3, y3 = [], []
    for g in games:
        x3.append(g["home_pts"]); y3.append(g["away_pts"])
        x3.append(g["away_pts"]); y3.append(g["home_pts"])
    r = pearson(x3, y3)
    computed.append({
        "id": "CR-03", "name": "Points scored vs points allowed, same game (club-game level)",
        "inputs": "official final scores only", "n": len(x3), "r": round(r, 4),
        "p": round(p_two_sided(r, len(x3)), 4), "ci95": [round(x, 4) for x in fisher_ci(r, len(x3))],
        "reading": ("A negative value means a game's two scores are not independent draws — the obvious "
                    "reading is pace. This is the number that makes 'just multiply the probabilities' "
                    "wrong for prop combos in the same game."),
        "source_url": STANDINGS_URL,
        "note": "n counts club-games (two per game), because the observation is a club's scoring and conceding",
    })

    # CR-04 rest-day differential vs home margin
    rx, ry, games_sel = [], [], []
    for g in games:
        h = rest.get((g["game_id"], g["home"]))
        a = rest.get((g["game_id"], g["away"]))
        if h is None or a is None:
            continue
        rx.append(h - a)
        ry.append(g["home_pts"] - g["away_pts"])
        games_sel.append(g)
    r = pearson(rx, ry) if len(rx) >= 3 else None
    # robustness, computed here so the published claim is an artefact rather than a remembered run
    nz = [(x, y) for x, y in zip(rx, ry) if x != 0]
    r_nz = pearson([x for x, _ in nz], [y for _, y in nz]) if len(nz) >= 3 else None
    loo = {}
    for w in sorted({g["week"] for g in games}):
        keep = [(x, y, g["week"]) for x, y, g in zip(rx, ry, games_sel) if g["week"] != w]
        if len(keep) >= 3:
            loo[w] = round(pearson([k[0] for k in keep], [k[1] for k in keep]), 4)
    edge = {"home_rest_advantage": [], "equal_rest": [], "away_rest_advantage": []}
    for x, y in zip(rx, ry):
        edge["home_rest_advantage" if x > 0 else "equal_rest" if x == 0 else "away_rest_advantage"].append(y)
    computed.append({
        "id": "CR-04", "name": "Rest-day differential (home minus away) vs home margin",
        "inputs": ("official final scores + the dates printed on the official week pages (no schedule date "
                   "is taken from anywhere else)"),
        "n": len(rx), "r": round(r, 4) if r is not None else None,
        "p": round(p_two_sided(r, len(rx)), 4) if r is not None else None,
        "ci95": [round(x, 4) for x in fisher_ci(r, len(rx))] if r is not None and len(rx) > 4 else None,
        "mean_rest_home": mean([v for v in rx]) if rx else None,
        "robustness": {
            "n_zero_rest_difference": len(rx) - len(nz),
            "nonzero_only_r": round(r_nz, 4) if r_nz is not None else None,
            "n_nonzero": len(nz),
            "leave_one_week_out_r": loo,
            "loo_range": [min(loo.values()), max(loo.values())] if loo else None,
            "mean_home_margin_by_rest_edge": {k: (round(mean(v), 2) if v else None) for k, v in edge.items()},
            "n_by_rest_edge": {k: len(v) for k, v in edge.items()},
        },
        "reading": ("Week-1 games are excluded because neither club has a previous game in the corpus. "
                    "Rest is derived from printed dates, so a rescheduled game would show up here as a "
                    "rest anomaly rather than being smoothed away."),
        "source_url": STANDINGS_URL,
    })

    # CR-05 international-game flag vs home margin
    intl = [g["home_pts"] - g["away_pts"] for g in games if g["international_game"]]
    dom = [g["home_pts"] - g["away_pts"] for g in games if not g["international_game"]]
    diff = mean(intl) - mean(dom) if intl and dom else None
    computed.append({
        "id": "CR-05", "name": "International game (printed section) vs home margin",
        "inputs": "official final scores + the section heading printed on the official week page",
        "n_international": len(intl), "n_domestic": len(dom),
        "mean_home_margin_international": round(mean(intl), 2) if intl else None,
        "mean_home_margin_domestic": round(mean(dom), 2) if dom else None,
        "difference_in_means": round(diff, 2) if diff is not None else None,
        "r": None,
        "reading": ("n = %d international games is far too small to estimate a home-field effect, so no "
                    "correlation is printed: a point-biserial r on this split would be noise dressed as a "
                    "number. The group means are shown with their n and nothing is concluded from them."
                    % len(intl)),
        "source_url": STANDINGS_URL,
    })

    for row in [
        {"id": "CR-06", "name": "Same-game parlay leg cover correlation",
         "reason": ("needs a point spread per game. The NFL publishes no lines, so the official source "
                    "cannot supply it; a sportsbook would be third-party."),
         "clearing_number": "any citable official or licensed price archive covering the games in question"},
        {"id": "CR-07", "name": "Player prop correlation (e.g. QB passing vs WR receiving)",
         "reason": "needs per-player prop lines and targets; neither is on an official nfl.com page read here.",
         "clearing_number": "an official or licensed play-by-play + prop-line archive"},
        {"id": "CR-08", "name": "Availability (starters out) vs margin",
         "reason": ("depends on a verified per-club depth rank or snap counts, which this repository does "
                    "not have for any club (peer namespaces record the same gap)."),
         "clearing_number": "a verified depth rank or snap count for 32 of 32 clubs, archived point-in-time"},
        {"id": "CR-09", "name": "Injury-designation reliability (play rate by designation)",
         "reason": "needs several seasons of designations joined to official inactive lists.",
         "clearing_number": "3+ seasons of archived weekly reports plus inactive lists"},
    ]:
        blank.append(row)

    out = {
        "dataset": "nfl_sources_correlations",
        "title": "Registered correlations, official numbers only, each with n",
        "built_utc": REGISTERED_UTC,
        "rule": ("Computed only from numbers printed on an official nfl.com page that this workspace read. "
                 "Each value carries n, a two-sided p (normal approximation of the t test, disclosed) and a "
                 "Fisher-z 95% interval. No market, price, prop or third-party number is used."),
        "n_computed": len(computed), "n_blank": len(blank),
        "computed": computed, "blank": blank,
    }
    write_json(os.path.join(DATA, "correlations.json"), out)
    for c in computed:
        print("%s n=%s r=%s p=%s ci=%s" % (c["id"], c.get("n", "%s/%s" % (c.get("n_international"), c.get("n_domestic"))),
                                           c["r"], c.get("p"), c.get("ci95")))
    print("blank:", [b["id"] for b in blank])


if __name__ == "__main__":
    main()
