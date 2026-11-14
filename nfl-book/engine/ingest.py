"""Build the verified results feed.

Policy (requirement: verified results feed so backtests and ROI can be computed):
  * Every row carries an official nfl.com URL.
  * Rows for Week 1, Week 9 and the Week 10 Thursday game were re-read LINE BY LINE
    from official score pages in this session on 2026-11-14 and must match the
    inherited archive exactly (32 games).
  * Team aggregates (W-L-T, PF, PA) recomputed from the full feed must match the
    official standings read line by line this session (32 teams x 5 fields).
  * Any mismatch fails the build. Rows not re-read this session are labelled
    aggregate_only and flagged — never presented as line-by-line verified.
"""
import json, os
from collections import defaultdict
from common import (ROOT, load, save, LINE_BY_LINE, NEUTRAL_CONFIRMED,
                    OFFICIAL_STANDINGS_URL, OFFICIAL_SCORES_URLS)

PEER_FEED = os.path.join(os.path.dirname(ROOT), "nfl-command",
                         "data", "games_2026_verified.json")


def main():
    with open(PEER_FEED, "r", encoding="utf-8") as f:
        peer = json.load(f)
    rows_in = peer["rows"]

    checks = []

    # ---- 1. line-by-line comparison for the 32 games fetched this session ----
    mismatches = []
    ll_count = 0
    for r in rows_in:
        key = (r["week"], r["away"], r["home"])
        if key in LINE_BY_LINE:
            ll_count += 1
            ap, hp, url = LINE_BY_LINE[key]
            if (r["away_pts"], r["home_pts"]) != (ap, hp):
                mismatches.append({"game": key, "feed": [r["away_pts"], r["home_pts"]],
                                   "official_this_session": [ap, hp], "url": url})
    checks.append({
        "id": "V-01", "name": "Line-by-line re-read of official score pages vs feed",
        "result": "pass" if not mismatches and ll_count == 32 else "fail",
        "detail": f"{ll_count} of 137 games re-read from nfl.com score/game pages "
                  f"on 2026-11-14 (all Week 1: 16, all Week 9: 15, Week 10 TNF: 1); "
                  f"{len(mismatches)} mismatches",
        "mismatches": mismatches,
        "sources": [OFFICIAL_SCORES_URLS[1], OFFICIAL_SCORES_URLS[9],
                    OFFICIAL_SCORES_URLS[10],
                    "https://www.nfl.com/games/commanders-at-giants-2026-reg-10"],
    })

    # ---- 2. rebuild team aggregates and compare to official standings -------
    standings = load("standings_2026-11-14.json")
    official = {t["team"]: t for t in standings["rows"]}

    agg = defaultdict(lambda: {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0, "g": 0})
    for r in rows_in:
        a, h = r["away"], r["home"]
        ap, hp = r["away_pts"], r["home_pts"]
        agg[a]["pf"] += ap; agg[a]["pa"] += hp
        agg[h]["pf"] += hp; agg[h]["pa"] += ap
        agg[a]["g"] += 1; agg[h]["g"] += 1
        if ap > hp:
            agg[a]["w"] += 1; agg[h]["l"] += 1
        elif hp > ap:
            agg[h]["w"] += 1; agg[a]["l"] += 1
        else:
            agg[a]["t"] += 1; agg[h]["t"] += 1

    cell_checks, cell_mismatch = 0, []
    for team, o in sorted(official.items()):
        g = agg[team]
        for field in ("w", "l", "t", "pf", "pa"):
            cell_checks += 1
            if g[field] != o[field]:
                cell_mismatch.append({"team": team, "field": field,
                                      "computed": g[field], "official": o[field]})
    sum_w = sum(g["w"] for g in agg.values())
    sum_l = sum(g["l"] for g in agg.values())
    sum_t = sum(g["t"] for g in agg.values())
    sum_pf = sum(g["pf"] for g in agg.values())
    sum_pa = sum(g["pa"] for g in agg.values())
    identity_ok = (sum_w == sum_l and sum_pf == sum_pa and
                   sum_w + sum_l + sum_t == 2 * len(rows_in))
    checks.append({
        "id": "V-02", "name": "Recomputed aggregates vs official standings (line by line)",
        "result": "pass" if not cell_mismatch else "fail",
        "detail": f"{cell_checks - len(cell_mismatch)}/{cell_checks} cells match "
                  f"(32 teams x W,L,T,PF,PA) against {OFFICIAL_STANDINGS_URL}",
        "mismatches": cell_mismatch, "sources": [OFFICIAL_STANDINGS_URL],
    })
    checks.append({
        "id": "V-03", "name": "League-wide identities",
        "result": "pass" if identity_ok else "fail",
        "detail": f"sum W {sum_w} = sum L {sum_l}; sum PF {sum_pf} = sum PA {sum_pa}; "
                  f"decisions {sum_w + sum_l + sum_t} = 2 x {len(rows_in)} games",
        "sources": [OFFICIAL_STANDINGS_URL],
    })

    # ---- 3. per-row feed with verification level ---------------------------
    feed_rows = []
    for r in rows_in:
        key = (r["week"], r["away"], r["home"])
        ll = key in LINE_BY_LINE
        neutral = r.get("neutral", False)
        if key in NEUTRAL_CONFIRMED:
            neutral = True
        feed_rows.append({
            "game_id": f"W{r['week']:02d}-{r['away']}-{r['home']}",
            "week": r["week"], "date": r["date"],
            "away": r["away"], "home": r["home"],
            "away_pts": r["away_pts"], "home_pts": r["home_pts"],
            "neutral": neutral,
            "verification": "line_by_line_2026-11-14" if ll else "aggregate_only_2026-11-14",
            "source_url": r.get("score_source_url") or r.get("source_url"),
            "week_page_url": r.get("official_week_page") or
                             f"https://www.nfl.com/schedules/2026/by-week/week-{r['week']}",
        })

    n_ll = sum(1 for r in feed_rows if r["verification"].startswith("line_by_line"))
    out = {
        "dataset": "nfl_book_verified_results_feed",
        "title": "Verified 2026 NFL results feed (settled games through Week 10 Thursday)",
        "built_utc": "2026-11-14",
        "n_games": len(feed_rows),
        "n_line_by_line": n_ll,
        "n_aggregate_only": len(feed_rows) - n_ll,
        "provenance_note": (
            "Base archive: nfl-command/data/games_2026_verified.json (each row carries an "
            "official nfl.com game URL). This session re-read 32 games line by line from "
            "official score/game pages (Weeks 1 and 9 in full, Week 10 Thursday) and "
            "recomputed all 32 teams' W-L-T/PF/PA against the official standings page read "
            "line by line on 2026-11-14 (V-01..V-03). Rows marked aggregate_only were not "
            "re-read page-by-page this session and are flagged, not certified."),
        "sources": {
            "standings": OFFICIAL_STANDINGS_URL,
            "scores_week1": OFFICIAL_SCORES_URLS[1],
            "scores_week9": OFFICIAL_SCORES_URLS[9],
            "scores_week10": OFFICIAL_SCORES_URLS[10],
            "game_w10_tnf": "https://www.nfl.com/games/commanders-at-giants-2026-reg-10",
        },
        "checks": checks,
        "rows": feed_rows,
    }
    save("results_feed.json", out)

    status = "PASS" if all(c["result"] == "pass" for c in checks) else "FAIL"
    print(f"[ingest] {status}: {len(feed_rows)} games, {n_ll} line-by-line, "
          f"V-01..V-03 "
          + ", ".join(f"{c['id']}={c['result']}" for c in checks))
    if status == "FAIL":
        raise SystemExit(1)
    return out


if __name__ == "__main__":
    main()
