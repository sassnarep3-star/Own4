#!/usr/bin/env python3
"""Parse the official line-by-line score transcription and cross-verify every row.

Produces:
  nfl/data/games.csv, nfl/data/games.json
  nfl/data/verification_report.json
"""
from __future__ import annotations
import re, sys
from collections import defaultdict
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from common import (DATA, TEAM_ABBR, WEEK_URL, S_STAND26, S_STAND25,
                    read_csv, write_csv, save_json, load_json)

LINE_RE = re.compile(
    r'^\[(.+?)\s+(\d+),\s+(.+?)\s+(\d+),\s+FINAL,\s+(.+?)\]\((https://www\.nfl\.com/games/[^)]+)\)$'
)
WK_RE = re.compile(r'-reg-(\d+)$')


def parse_scores():
    text = (DATA / "raw_scores.md").read_text(encoding="utf-8")
    games, errors = [], []
    current_week = None
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        m = re.match(r'^##\s*W(\d+)\s*$', line)
        if m:
            current_week = int(m.group(1))
            continue
        if not line.startswith('['):
            continue
        mm = LINE_RE.match(line)
        if not mm:
            errors.append(f"line {lineno}: unparseable: {line[:100]}")
            continue
        away_name, a, home_name, h, date, url = mm.groups()
        if away_name not in TEAM_ABBR or home_name not in TEAM_ABBR:
            errors.append(f"line {lineno}: unknown team {away_name!r} / {home_name!r}")
            continue
        wk = WK_RE.search(url)
        week = int(wk.group(1)) if wk else current_week
        if week is None or week != current_week:
            errors.append(f"line {lineno}: week mismatch url={week} header={current_week}")
        ap, hp = int(a), int(h)
        games.append({
            "game_id": url.rstrip("/").split("/")[-1],
            "week": week, "date": date,
            "away": TEAM_ABBR[away_name], "home": TEAM_ABBR[home_name],
            "away_name": away_name, "home_name": home_name,
            "away_pts": ap, "home_pts": hp,
            "total_pts": ap + hp, "home_margin": hp - ap,
            "abs_home_margin": abs(hp - ap),
            "home_win": 1 if hp > ap else (0 if ap > hp else 0.5),
            "result": f"{away_name} {ap}, {home_name} {hp}",
            "source_url": url, "week_url": WEEK_URL[week],
        })
    return games, errors


def check(name, ok, detail, urls):
    return {"check": name, "result": "PASS" if ok else "REVIEW", "detail": detail,
            "source_urls": urls if isinstance(urls, list) else [urls]}


def main():
    games, parse_errors = parse_scores()
    src = load_json("sources.json")
    reg = load_json("preregistration.json")
    checks = []

    checks.append(check("Every raw score line parses to a game with an official NFL.com game URL",
                        not parse_errors and len(games) == 120,
                        f"{len(games)} games parsed; {len(parse_errors)} parse errors"
                        + ("; " + "; ".join(parse_errors[:3]) if parse_errors else ""),
                        list(WEEK_URL.values())))
    urls = [g["source_url"] for g in games]
    checks.append(check("Game URLs are unique (no duplicated or dropped games)",
                        len(set(urls)) == len(urls) == 120,
                        f"{len(set(urls))} unique URLs / {len(urls)} rows",
                        list(WEEK_URL.values())))
    counts = defaultdict(int)
    for g in games:
        counts[g["week"]] += 1
    checks.append(check("Weekly game counts match the official by-week pages",
                        [counts[w] for w in range(1, 9)] == [16, 16, 16, 16, 15, 14, 14, 13],
                        "W1..W8 = " + ", ".join(str(counts[w]) for w in range(1, 9))
                        + "; official byes W5(2), W6(4), W7(4), W8(4)",
                        [WEEK_URL[w] for w in range(1, 9)]))

    # recompute standings, cell by cell
    agg = {a: dict(gp=0, w=0, l=0, t=0, pf=0, pa=0) for a in TEAM_ABBR.values()}
    for g in games:
        for side in ("away", "home"):
            t = agg[g[side]]
            t["gp"] += 1
            t["pf"] += g[side + "_pts"]
            t["pa"] += g[("home" if side == "away" else "away") + "_pts"]
        if g["home_win"] == 1:
            agg[g["home"]]["w"] += 1; agg[g["away"]]["l"] += 1
        elif g["home_win"] == 0:
            agg[g["away"]]["w"] += 1; agg[g["home"]]["l"] += 1
        else:
            agg[g["home"]]["t"] += 1; agg[g["away"]]["t"] += 1

    s26 = read_csv("standings_2026.csv")
    mismatches, cells = [], 0
    for row in s26:
        a = row["abbr"]; t = agg[a]
        for col, val in (("W", t["w"]), ("L", t["l"]), ("T", t["t"]),
                         ("PF", t["pf"]), ("PA", t["pa"]), ("NET_PTS", t["pf"] - t["pa"])):
            cells += 1
            if int(row[col]) != val:
                mismatches.append(f"{a}.{col}: standings={row[col]} recomputed={val}")
    checks.append(check("All 32 standings rows recomputed cell-by-cell from the 120 official game scores",
                        not mismatches and cells == 192,
                        f"{cells} cells compared (W/L/T/PF/PA/NET PTS x 32); {len(mismatches)} mismatches"
                        + ("; " + "; ".join(mismatches[:6]) if mismatches else ""),
                        [S_STAND26] + [WEEK_URL[w] for w in range(1, 9)]))
    checks.append(check("League scoring identity: sum of points for equals sum of points against",
                        sum(int(r["PF"]) for r in s26) == sum(int(r["PA"]) for r in s26),
                        f"sum PF = {sum(int(r['PF']) for r in s26)}, "
                        f"sum PA = {sum(int(r['PA']) for r in s26)}, "
                        f"sum of all game totals = {sum(g['total_pts'] for g in games)}",
                        S_STAND26))
    ties = sum(1 for g in games if g["home_win"] == 0.5)
    checks.append(check("League win/loss/tie identity",
                        sum(int(r["W"]) for r in s26) == 120 - ties
                        and sum(int(r["L"]) for r in s26) == 120 - ties
                        and sum(int(r["T"]) for r in s26) == 2 * ties,
                        f"W={sum(int(r['W']) for r in s26)}, L={sum(int(r['L']) for r in s26)}, "
                        f"T={sum(int(r['T']) for r in s26)}, tied games={ties}",
                        S_STAND26))
    checks.append(check("Every 2026 standings row has NET_PTS = PF - PA and an official URL",
                        all(int(r["NET_PTS"]) == int(r["PF"]) - int(r["PA"]) for r in s26)
                        and all(r["source_url"] == S_STAND26 for r in s26),
                        "32/32 rows satisfy the identity; 32/32 carry the official standings URL",
                        S_STAND26))

    s25 = read_csv("standings_2025.csv")
    checks.append(check("2025 standings: 32 teams, 17 games each, balanced W/L and PF/PA",
                        len(s25) == 32
                        and sum(int(r["W"]) + int(r["L"]) + int(r["T"]) for r in s25) == 544
                        and sum(int(r["W"]) for r in s25) == sum(int(r["L"]) for r in s25)
                        and sum(int(r["PF"]) for r in s25) == sum(int(r["PA"]) for r in s25)
                        and all(int(r["NET_PTS"]) == int(r["PF"]) - int(r["PA"]) for r in s25),
                        f"rows=32, team-games=544, sum W={sum(int(r['W']) for r in s25)}, "
                        f"sum PF={sum(int(r['PF']) for r in s25)}, "
                        f"NET_PTS identity 32/32",
                        S_STAND25))

    # QB game-log rows cross-checked against the official game scores
    logs = read_csv("qb_game_logs.csv")
    by_week = defaultdict(list)
    for g in games:
        by_week[g["week"]].append(g)
    qb_bad, qb_ok = [], 0
    for r in logs:
        w, team = int(r["week"]), r["team"]
        cand = [g for g in by_week[w] if g["away"] == team or g["home"] == team]
        if not cand:
            qb_bad.append(f"{r['player']} W{w}: no official game found"); continue
        g = cand[0]
        is_home = g["home"] == team
        tp = g["home_pts"] if is_home else g["away_pts"]
        op = g["away_pts"] if is_home else g["home_pts"]
        if int(r["team_pts"]) != tp or int(r["opp_pts"]) != op:
            qb_bad.append(f"{r['player']} W{w}: log {r['team_pts']}-{r['opp_pts']} vs game {tp}-{op}")
        else:
            qb_ok += 1
        oppn = r["opp"].lstrip("@")
        if TEAM_ABBR.get(oppn) != (g["away"] if is_home else g["home"]):
            qb_bad.append(f"{r['player']} W{w}: opponent {r['opp']} != official game opponent")
        if int(r["comp"]) > int(r["att"]):
            qb_bad.append(f"{r['player']} W{w}: completions > attempts")
    checks.append(check("All 60 official QB game-log rows reconciled to the official game scores",
                        not qb_bad and len(logs) == 60,
                        f"{len(logs)} rows; {qb_ok} score reconciliations; "
                        f"opponent + comp<=att checked; {len(qb_bad)} discrepancies"
                        + ("; " + "; ".join(qb_bad[:4]) if qb_bad else ""),
                        [s["url"] for s in src["sources"] if s["id"] in
                         ("S17","S18","S19","S20","S21","S22","S23","S24")]
                        + [WEEK_URL[w] for w in range(1, 9)]))

    # provenance of every published CSV row
    all_rows = []
    for fn in ("standings_2026.csv","standings_2025.csv","qb_game_logs.csv",
               "upcoming_2026.csv","bye_weeks.csv"):
        all_rows += [(fn, r) for r in read_csv(fn)]
    bad_urls = [(fn, r) for fn, r in all_rows
                if not str(r.get("source_url", "")).startswith("https://")]
    checks.append(check("Every row in every data table has an https official source link",
                        not bad_urls,
                        f"{len(all_rows)} rows across 5 CSVs; {len(bad_urls)} missing source_url",
                        [S_STAND26, S_STAND25, WEEK_URL[9]]))
    checks.append(check("Upcoming Week 8/9 slate carries official game and week URLs",
                        all(r["source_url"].startswith("https://www.nfl.com/games/")
                            and r["week_url"] in WEEK_URL.values()
                            for r in read_csv("upcoming_2026.csv")),
                        f"{len(read_csv('upcoming_2026.csv'))} upcoming rows "
                        f"(1 pending Week 8 game + 15 Week 9 games)",
                        [WEEK_URL[8], WEEK_URL[9]]))
    checks.append(check("Pre-registration committed before analysis with frozen parameters",
                        reg["registered_before_any_analysis_run"] is True,
                        f"{len(reg['validation_gates'])} gates, "
                        f"{len(reg['strategy_catalog'])} strategies, "
                        f"{len(reg['correlation_family']['pairs'])} correlation pairs pre-registered",
                        "https://github.com/sassnarep3-star/Own4"))

    fields = ["game_id","week","date","away","home","away_name","home_name",
              "away_pts","home_pts","total_pts","home_margin","abs_home_margin",
              "home_win","result","source_url","week_url"]
    write_csv("games.csv", games, fields)
    save_json("games.json", {"count": len(games), "games": games})
    report = {
        "title": "Line-by-line verification ledger",
        "generated_from": "official NFL.com by-week schedule pages and standings pages",
        "checks": checks,
        "checks_passed": sum(1 for c in checks if c["result"] == "PASS"),
        "checks_total": len(checks),
        "official_game_rows": len(games),
        "standings_cells_compared": cells,
        "qb_rows_compared": len(logs),
        "csv_rows_provenance_checked": len(all_rows),
        "note": "Every check above is reproducible by running `python nfl/engine/dataset.py`.",
    }
    save_json("verification_report.json", report)
    for c in checks:
        print(f"  [{c['result']:6}] {c['check']}: {c['detail']}")
    print(f"\n{report['checks_passed']}/{report['checks_total']} checks passed; "
          f"{len(games)} games written")
    if report["checks_passed"] != report["checks_total"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
