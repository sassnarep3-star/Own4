#!/usr/bin/env python3
"""
Own4 — publication invariants.

Why this file exists: a byte-for-byte diff of the rebuilt site is a good check but not a
portable one. The statistical layer calls math.erf (libm) and a seeded Mersenne Twister;
across two environments with the same Python but different C libraries, a comparison deep
inside the permutation loop can land on the other side of a tie and move a published
p-value in the last digit. That is an environment artefact, not a data problem.

So the CI gate is split in two:
  * the transcription (`verification/data/`) must rebuild BYTE-IDENTICALLY — it is pure
    literals, no arithmetic, no randomness;
  * the analysis and the pages must rebuild to the same substantive result — checked here
    against the values that the published claims depend on, with explicit tolerances.

Run: python3 verification/assert_publication.py
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out")

fails = []


def close(label, got, want, tol):
    if got is None or abs(got - want) > tol:
        fails.append("%s: got %r, expected %r +/- %r" % (label, got, want, tol))


def eq(label, got, want):
    if got != want:
        fails.append("%s: got %r, expected %r" % (label, got, want))


def main():
    an = json.load(open(os.path.join(OUT, "analysis.json")))
    rec = json.load(open(os.path.join(OUT, "reconciliation.json")))

    # --- audit ---
    eq("reconciliation failures", rec["summary"]["fail"], 0)
    eq("reconciliation notes", rec["summary"]["note"], 3)
    eq("sample games", rec["summary"]["sample_games"], 85)
    eq("official games at snapshot", rec["summary"]["official_games"], 121)
    close("coverage %", rec["summary"]["coverage_pct"], 70.2, 0.1)
    eq("uncaptured games", rec["summary"]["missing_games"], 36)

    # --- analysis ---
    eq("graded games", an["metrics"]["graded"], 35)
    close("winner accuracy", an["metrics"]["winner_accuracy"], 0.571428, 1e-5)
    close("home baseline", an["metrics"]["home_baseline_accuracy"], 0.600000, 1e-5)
    close("MAE total", an["metrics"]["mae_total"], 15.1231, 0.02)
    close("MAE baseline", an["metrics"]["mae_total_baseline"], 15.8591, 0.02)
    if not (0.01 < an["metrics"]["permutation_p_totals"] < 0.05):
        fails.append("permutation p moved out of the nominal band: %r" % an["metrics"]["permutation_p_totals"])
    eq("gates", [g["status"] for g in an["gates"]].count("PASS"), 4)
    eq("gates", [g["status"] for g in an["gates"]].count("FAIL"), 5)
    eq("gates", [g["status"] for g in an["gates"]].count("BLOCKED"), 1)
    eq("strategies qualified", sum(1 for s in an["strategies"] if s["status"] == "NO QUALIFICATION"), 8)
    eq("rewards awarded", an["rewards"]["awarded"], 0)
    eq("team correlations", len(an["team_correlations"]), 10)
    eq("correlations surviving FDR", sum(1 for c in an["team_correlations"] if c["bh_reject"]), 5)
    eq("originated lines", len(an["own_lines"]), 2)
    eq("prop reference rows", len(an["props"]), 4)
    for line in an["own_lines"]:
        if line["price"] is not None:
            fails.append("a price was published without an official source")

    # --- pages ---
    pages = {
        "index.html": 10, "verified/standings.html": 30, "verified/team-stats.html": 30,
        "verified/games.html": 102, "verified/own-lines.html": 2, "verified/strategies.html": 11,
        "verified/validation.html": 13, "verified/backtest.html": 44, "verified/leaderboard.html": 8,
        "verified/correlations.html": 14, "verified/sources.html": 12, "verified/audit.html": 23,
        "verified/flagged.html": 13, "verified/executive-summary.html": 7,
    }
    for rel, rows in pages.items():
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            fails.append("missing page: " + rel)
            continue
        raw = open(path, encoding="utf-8").read()
        got = len(re.findall(r"<tr>", raw))
        # header rows live in <thead>, so the data-row count is checked by verify_site.py;
        # here we only require the page to contain at least its data rows
        if got < rows:
            fails.append("%s: only %d <tr> elements, expected at least %d" % (rel, got, rows))
        if re.search(r">\s*(nan|NaN|None)\s*<", raw):
            fails.append(rel + ": sentinel value in a table cell")

    if fails:
        print("FAILED publication invariants (%d):" % len(fails))
        for f in fails:
            print("  -", f)
        return 1
    print("publication invariants hold: 85 games / 121 official, 35 graded, 4-5-1 gates, "
          "0 qualified, 0 rewards, 5 FDR survivors, 14 pages.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
