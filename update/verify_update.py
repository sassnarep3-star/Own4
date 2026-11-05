#!/usr/bin/env python3
"""
Own4 update verifier — line-by-line checks for the settlement and refresh files.

Run: python3 update/verify_update.py
Exits non-zero if any check fails. Every check is printed with PASS/FAIL.
"""
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OFFICIAL_DOMAINS = ("nba.com", "www.nba.com", "official.nba.com", "stats.nba.com", "ncpgambling.org", "www.ncpgambling.org")

checks = []

def check(name, ok, detail=""):
    checks.append((name, bool(ok), detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

def official(url):
    return isinstance(url, str) and any(url.startswith(f"https://{d}/") or url == f"https://{d}" for d in OFFICIAL_DOMAINS)

def load(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return json.load(f)

# --- settlement file ---------------------------------------------------------
s = load("settlement_2026-11-02.json")
rows = s["rows"]
check("settlement: 15/15 slate games settled", len(rows) == 15 and s["games_settled"] == 15, f"rows={len(rows)}")
check("settlement: every row has official source_url", all(official(r.get("source_url")) for r in rows))
check("settlement: every row has game_url on nba.com", all(official(r.get("game_url")) for r in rows))
check("settlement: game_ids unique", len({r["game_id"] for r in rows}) == len(rows))
check("settlement: no unverified rows", all(r.get("unverified") is False for r in rows))

for r in rows:
    tot = r["away_pts"] + r["home_pts"]
    marg = r["home_pts"] - r["away_pts"]
    check(f"settlement {r['game_id']}: total/margin recompute", tot == r["total_pts"] and marg == r["margin_home"],
          f"total={r['total_pts']} margin={r['margin_home']}")
    check(f"settlement {r['game_id']}: spread outcome recompute",
          r["home_cover"] == ((marg + r["own_spread_home"]) > 0), f"spread_home={r['own_spread_home']}")
    check(f"settlement {r['game_id']}: total outcome recompute",
          r["over_own_total"] == (tot > r["own_total"]))
    check(f"settlement {r['game_id']}: brier recompute",
          abs(r["brier"] - (r["p_home_win"] - (1 if marg > 0 else 0)) ** 2) < 1e-5)
    check(f"settlement {r['game_id']}: SU pick consistency",
          r["su_pick"] == ("home" if r["p_home_win"] >= 0.5 else "away"))

# cross-check vs the repo slate (read-only)
with open(os.path.join(ROOT, "data", "own_lines_2026-11-02.csv"), newline="", encoding="utf-8") as f:
    slate = {r["game_id"]: r for r in csv.DictReader(f)}
check("settlement: all slate game_ids present in official results", set(slate) == {r["game_id"] for r in rows})
mismatch = [gid for gid, line in slate.items()
            if next((r for r in rows if r["game_id"] == gid), None)
            and (next(r for r in rows if r["game_id"] == gid)["away"] != line["away"]
                 or next(r for r in rows if r["game_id"] == gid)["home"] != line["home"])]
check("settlement: teams match repo slate for every game", not mismatch, str(mismatch))

# aggregates recompute
n = len(rows)
recomputed = {
    "su_hits": sum(1 for r in rows if r["su_hit"]),
    "home_spread_covers": sum(1 for r in rows if r["home_cover"]),
    "overs_own_total": sum(1 for r in rows if r["over_own_total"]),
    "totals_pick_hits": sum(1 for r in rows if r["total_hit"]),
    "ot_games": sum(1 for r in rows if r["status"] == "Final/OT"),
}
agg = s["aggregates"]
for k, v in recomputed.items():
    check(f"settlement: aggregate {k} recompute", agg[k] == v, f"file={agg[k]} recomputed={v}")
check("settlement: mean_brier recompute", abs(agg["mean_brier"] - sum(r["brier"] for r in rows) / n) < 1e-5)
check("settlement: margin_mae recompute", abs(agg["margin_mae"] - sum(r["margin_abs_error"] for r in rows) / n) < 1e-5)
check("settlement: total_mae recompute", abs(agg["total_mae"] - sum(r["total_abs_error"] for r in rows) / n) < 1e-5)
check("settlement: slate completeness of official list", s["games_missing_official_result"] == [] and s["official_games_not_in_slate"] == [])

# --- refresh file ------------------------------------------------------------
r = load("games_2026-11-03_to_2026-11-05.json")
n4 = r["games_2026-11-04"]
n5 = r["games_2026-11-05"]
check("refresh: 2026-11-03 recorded as no-games with official source",
      r["completed_games_2026-11-03"] == 0 and official(r["no_games_2026-11-03"]["source_url"]))
check("refresh: 2026-11-04 has exactly 14 games (official calendar grid)", len(n4) == 14, f"n={len(n4)}")
check("refresh: 2026-11-05 has 2 scheduled, unplayed games", len(n5) == 2 and all(g["status"] == "scheduled" for g in n5))
check("refresh: 2026-11-05 games have no fabricated scores", all(g["away_pts"] is None and g["home_pts"] is None for g in n5))
for g in n4 + n5:
    check(f"refresh {g['game_id']}: official source_url", official(g.get("source_url")))
    check(f"refresh {g['game_id']}: nba.com game_url", official(g.get("game_url")))
ids4 = [g["game_id"] for g in n4]
check("refresh: 2026-11-04 game ids unique", len(set(ids4)) == len(ids4))
for g in n4:
    check(f"refresh {g['game_id']}: total/margin recompute",
          g["total_pts"] == g["away_pts"] + g["home_pts"] and g["margin_home"] == g["home_pts"] - g["away_pts"])

# cross-check: lab dataset row count must be 92 for the 121 total to hold
with open(os.path.join(ROOT, "data", "games_2026-27.csv"), newline="", encoding="utf-8") as f:
    lab_rows = list(csv.DictReader(f))
check("refresh: lab dataset still has 92 games through 2026-11-01", len(lab_rows) == 92, f"n={len(lab_rows)}")
max_lab = max(row["date"] for row in lab_rows)
check("refresh: lab dataset last date is 2026-11-01", max_lab == "2026-11-01", f"max={max_lab}")
check("refresh: completed-through-2026-11-04 arithmetic",
      r["completed_games_total_through_2026-11-04"] == len(lab_rows) + 15 + len(n4))

# settlement must not contradict the refresh on shared facts
check("refresh/settlement: Nov 2 OT game agrees (Final/OT)",
      next(g for g in rows if g["game_id"] == "0022600165")["status"] == "Final/OT")

# --- HTML page checks ---------------------------------------------------------
html_path = os.path.join(HERE, "index.html")
if os.path.exists(html_path):
    html = open(html_path, encoding="utf-8").read()
    ext = re.findall(r'href="(https?://[^"]+)"', html)
    check("page: every external link is on an official/trusted domain",
          all(official(u) for u in ext), f"{len(ext)} external links")
    internal = re.findall(r'(?:href|src)="(?!https?:|mailto:|#|tel:)([^"]+)"', html)
    missing = [u for u in internal if not os.path.exists(os.path.normpath(os.path.join(HERE, u.split("#")[0])))]
    check("page: no broken internal links", not missing, str(missing))
    rows_html = len(re.findall(r"<tr[ >]", html))
    src_links = len(re.findall(r'<a[^>]+href="https://(?:www\.)?nba\.com/', html))
    check("page: table rows present and source-linked", rows_html > 10 and src_links >= 1,
          f"rows={rows_html} nba_links={src_links}")
else:
    check("page: update/index.html exists", False, "missing")

npass = sum(1 for _, ok, _ in checks if ok)
nfail = len(checks) - npass
print(f"\n{npass} PASS, {nfail} FAIL ({len(checks)} checks)")
sys.exit(1 if nfail else 0)
