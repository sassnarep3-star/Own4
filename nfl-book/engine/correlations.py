"""Correlation register — computed ONLY from officially sourced numbers.

Inputs: data/results_feed.json (scores, dates, home/away; every row carries an
official nfl.com URL). No market, price, prop or third-party number enters any
computed correlation. Correlations that would require non-official inputs are
published as blank rows with the reason (never estimated).
Every computed row publishes n, r, a two-sided p-value and Fisher-z 95% CI.
"""
import math
from collections import defaultdict
from common import load, save


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None, None, None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx == 0 or syy == 0:
        return None, None, None
    r = sxy / math.sqrt(sxx * syy)
    r = max(-0.999999, min(0.999999, r))
    # two-sided p via t distribution approximation (df = n-2), use normal approx
    # for large n and erfc-based normal otherwise — adequate for reporting here.
    if n > 3:
        t = r * math.sqrt((n - 2) / (1 - r * r))
        p = math.erfc(abs(t) / math.sqrt(2))  # normal approximation, disclosed
    else:
        p = None
    z = 0.5 * math.log((1 + r) / (1 - r))
    se = 1 / math.sqrt(n - 3) if n > 3 else None
    if se:
        lo = math.tanh(z - 1.96 * se)
        hi = math.tanh(z + 1.96 * se)
    else:
        lo = hi = None
    return round(r, 4), (round(p, 4) if p is not None else None), \
        ([round(lo, 4), round(hi, 4)] if lo is not None else None)


def main():
    feed = load("results_feed.json")
    rows = feed["rows"]
    rows = sorted(rows, key=lambda g: (g["week"], g["date"], g["game_id"]))

    computed = []

    # CR-01 home margin vs game total
    xs = [g["home_pts"] - g["away_pts"] for g in rows]
    ys = [g["home_pts"] + g["away_pts"] for g in rows]
    r, p, ci = pearson(xs, ys)
    computed.append({
        "id": "CR-01", "name": "Home margin vs game total",
        "inputs": "official final scores", "n": len(rows), "r": r, "p": p, "ci95": ci,
        "source_url": feed["sources"]["standings"],
        "note": "computed from results_feed.json (official nfl.com per-row sources)"})

    # CR-02 team scoring persistence: points in a team's game vs points in its next game
    by_team = defaultdict(list)
    for g in rows:
        by_team[g["away"]].append((g["week"], g["away_pts"], g["date"]))
        by_team[g["home"]].append((g["week"], g["home_pts"], g["date"]))
    xs, ys = [], []
    for t, games in by_team.items():
        games = sorted(games, key=lambda x: (x[0], x[2]))
        for i in range(len(games) - 1):
            xs.append(games[i][1])
            ys.append(games[i + 1][1])
    r, p, ci = pearson(xs, ys)
    computed.append({
        "id": "CR-02", "name": "Team points scored, consecutive games",
        "inputs": "official final scores", "n": len(xs), "r": r, "p": p, "ci95": ci,
        "source_url": feed["sources"]["scores_week1"],
        "note": "each ordered pair of consecutive games by one team"})

    # CR-03 within-week consecutive-game dependence (home-win indicator)
    by_week = defaultdict(list)
    for g in rows:
        by_week[g["week"]].append(g)
    xs, ys = [], []
    for w, gs in sorted(by_week.items()):
        gs = sorted(gs, key=lambda g: (g["date"], g["game_id"]))
        for i in range(len(gs) - 1):
            a, b = gs[i], gs[i + 1]
            if a["home_pts"] == a["away_pts"] or b["home_pts"] == b["away_pts"]:
                continue  # ties excluded (2026 has one tie through W10)
            xs.append(1 if a["home_pts"] > a["away_pts"] else 0)
            ys.append(1 if b["home_pts"] > b["away_pts"] else 0)
    r, p, ci = pearson(xs, ys)
    computed.append({
        "id": "CR-03", "name": "Same-week consecutive games: home-win vs next home-win",
        "inputs": "official final scores", "n": len(xs), "r": r, "p": p, "ci95": ci,
        "source_url": feed["sources"]["scores_week9"],
        "note": "tests whether one game's outcome predicts the next game's in the "
                "same week (relevant to parlay-leg independence)"})

    # CR-04 rest-day differential vs home margin (needs dates from the feed)
    date_idx = {}
    for g in rows:
        date_idx[(g["week"], g["away"], g["home"])] = g["date"]
    last_seen = {}
    xs, ys = [], []
    for g in rows:
        import datetime as dt
        d = dt.date.fromisoformat(g["date"])
        rh = (d - last_seen[g["home"]]).days if g["home"] in last_seen else None
        ra = (d - last_seen[g["away"]]).days if g["away"] in last_seen else None
        if rh is not None and ra is not None:
            xs.append(rh - ra)
            ys.append(g["home_pts"] - g["away_pts"])
        last_seen[g["home"]] = d
        last_seen[g["away"]] = d
    r, p, ci = pearson(xs, ys)
    computed.append({
        "id": "CR-04", "name": "Rest-day differential (home minus away) vs home margin",
        "inputs": "official final scores + official schedule dates in the feed",
        "n": len(xs), "r": r, "p": p, "ci95": ci,
        "source_url": feed["sources"]["scores_week10"],
        "note": "week-1 games excluded (no prior game); dates for weeks 2-8 are "
                "peer-transcribed from official week pages and were not all "
                "re-read this session (flag FB-03)"})

    # CR-05 season aggregate: points allowed vs wins (team level)
    agg = defaultdict(lambda: {"pf": 0, "pa": 0, "w": 0, "g": 0})
    for g in rows:
        a, h = g["away"], g["home"]
        agg[a]["pf"] += g["away_pts"]; agg[a]["pa"] += g["home_pts"]
        agg[h]["pf"] += g["home_pts"]; agg[h]["pa"] += g["away_pts"]
        agg[a]["g"] += 1; agg[h]["g"] += 1
        if g["home_pts"] > g["away_pts"]:
            agg[h]["w"] += 1
        elif g["away_pts"] > g["home_pts"]:
            agg[a]["w"] += 1
        else:
            agg[h]["w"] += 0.5; agg[a]["w"] += 0.5
    xs = [agg[t]["pa"] for t in agg]
    ys = [agg[t]["w"] for t in agg]
    r, p, ci = pearson(xs, ys)
    computed.append({
        "id": "CR-05", "name": "Points allowed vs wins (team level, 2026 through W10 TNF)",
        "inputs": "official final scores", "n": len(xs), "r": r, "p": p, "ci95": ci,
        "source_url": feed["sources"]["standings"],
        "note": "n = 32 teams"})

    blanks = [
        {"id": "CR-06", "name": "Same-game parlay leg cover correlation",
         "reason": "requires official point spreads per game; the NFL publishes no "
                   "lines (FB-01). Left blank, not estimated.",
         "source_url": "https://www.nfl.com/"},
        {"id": "CR-07", "name": "Player prop co-occurrence (QB passing + WR receiving)",
         "reason": "requires official player-prop lines; none exist in any official "
                   "source read by this project (FB-05). Left blank.",
         "source_url": "https://www.nfl.com/"},
        {"id": "CR-08", "name": "Open-to-close line movement correlation",
         "reason": "requires market open/close prices; no official price source "
                   "(FB-01). The price-snapshot store records OUR lines only.",
         "source_url": "https://www.nfl.com/"},
        {"id": "CR-09", "name": "Injury-report status vs game outcome",
         "reason": "requires archived official injury reports per week; only the "
                   "current Week 10 report is retrievable (FB-06). Left blank.",
         "source_url": "https://www.nfl.com/injuries/"},
    ]

    out = {
        "dataset": "nfl_book_correlations",
        "title": "Correlations computed only from officially sourced numbers",
        "built_utc": "2026-11-14",
        "method": "Pearson r on official final scores/dates; p = two-sided normal "
                  "approximation of the t test (disclosed); CI = Fisher z. "
                  "No market, price or third-party number is used anywhere.",
        "n_computed": len(computed), "n_blank": len(blanks),
        "computed": computed, "blank": blanks,
    }
    save("correlations.json", out)
    print("[correlations] " + ", ".join(
        f"{c['id']} n={c['n']} r={c['r']}" for c in computed))
    return out


if __name__ == "__main__":
    main()
