#!/usr/bin/env python3
"""
Own4 · nfl-live-board · correlations

Every number in data/correlations.json is computed here from the reconciled 149-game corpus
(data/corpus_2026.json). Each row publishes n beside the value. Rows that would need a price,
a player prop or a depth source are present with a BLANK value and the reason, so that a
missing correlation cannot be mistaken for a correlation of zero.

What the values mean:
  * r is the Pearson correlation of the pair named in the row;
  * the 95% interval comes from Fisher's z transform, which is the textbook interval for a
    sample correlation and is stated as such - it assumes independent pairs, and games inside
    a week are not perfectly independent, so the interval is a floor on the true width;
  * the p-value is a two-sided permutation test (10,000 shuffles) with a fixed seed, so it can
    be reproduced on any machine. A permutation test needs no normality assumption;
  * n is the number of complete pairs actually used, printed in the same row.

Run: python3 nfl-live-board/engine/correlations.py
"""
import json
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
SEED = 20261117
PERM = 10000


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def fisher_ci(r, n):
    if r is None or n is None or n < 4 or abs(r) >= 1:
        return [None, None]
    z = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3)
    lo, hi = z - 1.959963984540054 * se, z + 1.959963984540054 * se
    return [round(math.tanh(lo), 4), round(math.tanh(hi), 4)]


def perm_p(xs, ys, rng, observed):
    if observed is None:
        return None
    n = len(xs)
    label = ys[:]
    hits = 0
    for _ in range(PERM):
        rng.shuffle(label)
        r = pearson(xs, label)
        if r is not None and abs(r) >= abs(observed):
            hits += 1
    return round((hits + 1) / float(PERM + 1), 4)


def row(cid, a, b, xs, ys, source, kind="computed", definition="", blank_reason="", sig=""):
    n = len(xs)
    r = pearson(xs, ys) if n >= 3 else None
    rng = random.Random(SEED + int(cid[1:]))
    return {
        "id": cid, "pair": "%s ~ %s" % (a, b), "definition": definition or "%s versus %s" % (a, b),
        "kind": kind, "n": n,
        "r": None if r is None else round(r, 4),
        "ci95_fisher": fisher_ci(r, n),
        "p_permutation": perm_p(xs, ys, rng, r) if r is not None else None,
        "source": source, "blank_reason": blank_reason,
        "note": sig,
    }


def main():
    corpus = json.load(open(os.path.join(DATA, "corpus_rows_only.json")))["rows"]
    rows = []

    # C01 - margin vs total, the classic totals/side dependence
    xs, ys = [], []
    for g in corpus:
        m = g["home_pts"] - g["away_pts"]
        t = g["home_pts"] + g["away_pts"]
        xs.append(float(m)); ys.append(float(t))
    rows.append(row("C01", "game margin", "game total", xs, ys,
                    "https://www.nfl.com/standings/league/2026/REG",
                    definition="(home - away) points versus (home + away) points, one pair per game",
                    sig="the size of the relationship that makes a same-game parlay of side and total "
                        "dependent. It is measured here so it never has to be assumed."))

    # C02 - total vs the pre-game rating total (model total): only for walk-forward rows
    wf = json.load(open(os.path.join(DATA, "origination_week11.json")))["walk_forward_rows"]
    xs = [w["fair_total"] for w in wf]; ys = [w["actual_total"] for w in wf]
    rows.append(row("C02", "model fair total", "actual total", xs, ys,
                    "https://www.nfl.com/scores/2026/week-10",
                    definition="the pre-kickoff model total versus the total actually scored, walk-forward weeks only",
                    sig="a high value is necessary but not sufficient for a useful totals model; "
                        "it is not a market test."))

    # C03 - fair margin vs actual margin
    xs = [w["fair_margin_home"] for w in wf]; ys = [w["actual_margin_home"] for w in wf]
    rows.append(row("C03", "model fair margin", "actual margin", xs, ys,
                    "https://www.nfl.com/scores/2026/week-10",
                    definition="the pre-kickoff model margin (home perspective) versus the actual margin",
                    sig="this is the side model's own skill, measured on outcomes it never saw."))

    # C04 - rest differential vs margin (fixture context, schedule facts only)
    import datetime
    last = {}
    xs, ys = [], []
    for g in sorted(corpus, key=lambda x: (x["date"], x["game_id"])):
        try:
            d = datetime.date.fromisoformat(g["date"])
        except ValueError:
            continue
        rest_h = (d - last[g["home"]]).days if g["home"] in last else None
        rest_a = (d - last[g["away"]]).days if g["away"] in last else None
        last[g["home"]] = d
        last[g["away"]] = d
        if rest_h is None or rest_a is None:
            continue
        xs.append(float(rest_h - rest_a))
        ys.append(float(g["home_pts"] - g["away_pts"]))
    rows.append(row("C04", "rest differential (home - away, days)", "home margin", xs, ys,
                    "https://www.nfl.com/schedules/2026/by-week/week-11",
                    definition="rest days computed from the official dates of consecutive fixtures "
                               "(a schedule fact, not an estimate), versus the game margin",
                    sig="rest is derived from published dates only. The first appearance of each "
                        "club is dropped because its prior game is outside the corpus."))

    # C05 - neutral-site vs margin: too few neutral games to correlate honestly
    neut = [g for g in corpus if g.get("neutral_verified")]
    rows.append({
        "id": "C05", "pair": "neutral site ~ home margin", "kind": "insufficient n",
        "definition": "whether playing at a neutral site changes the home margin",
        "n": len(neut), "r": None, "ci95_fisher": [None, None], "p_permutation": None,
        "source": "https://www.nfl.com/scores/2026/week-10",
        "blank_reason": "only %d corpus games are venue-verified as neutral from the official pages "
                        "this session read (the Week-9 Madrid and Week-10 Munich fixtures). The "
                        "inherited feed flags more, but a peer flag is not a verification, so those "
                        "are carried separately in the corpus and are not used here. A correlation "
                        "on n=%d is undefined, so the row is blank." % (len(neut), len(neut)),
        "note": "",
    })

    # C06/C07 - price-based correlations: structurally blank
    for cid, pair, why in (
        ("C06", "closing line move ~ result", "needs a closing price on both sides; no official "
         "price source exists (F-01)"),
        ("C07", "market total ~ model total", "needs a market total; no official price source "
         "exists (F-01)"),
    ):
        rows.append({
            "id": cid, "pair": pair, "kind": "blocked", "definition": pair, "n": None,
            "r": None, "ci95_fisher": [None, None], "p_permutation": None,
            "source": "https://www.nfl.com/", "blank_reason": why, "note": "",
        })

    # C08 - injury designation vs result: structurally blank
    rows.append({
        "id": "C08", "pair": "injury designation ~ result", "kind": "blocked",
        "definition": "whether a Questionable or Doubtful designation predicts the game result",
        "n": None, "r": None, "ci95_fisher": [None, None], "p_permutation": None,
        "source": "https://www.nfl.com/injuries/league/2026/reg10",
        "blank_reason": "one dated availability snapshot this season; a correlation needs many "
                        "weeks of designations joined to results (F-04)", "note": "",
    })

    out = {
        "dataset": "nfl_live_board_correlations",
        "title": "Correlations computed from officially sourced numbers, with n published",
        "built_utc": "2026-11-17",
        "method": ("Pearson r; 95%% interval by Fisher z (stated as a floor on width because games "
                   "inside a week are not fully independent); two-sided permutation p with %d "
                   "shuffles and seed %d." % (PERM, SEED)),
        "policy": "a blank r always carries its reason in the same row; no value is estimated",
        "n_computed": sum(1 for r in rows if r["r"] is not None),
        "n_blank": sum(1 for r in rows if r["r"] is None),
        "rows": rows,
    }
    json.dump(out, open(os.path.join(DATA, "correlations.json"), "w"), indent=1)
    print("correlations: %d computed, %d blank" % (out["n_computed"], out["n_blank"]))
    for r in rows:
        print("  %-4s n=%-5s r=%-8s ci95=%-20s p=%s  %s" %
              (r["id"], r["n"], r["r"], r["ci95_fisher"], r["p_permutation"], r["pair"][:52]))


if __name__ == "__main__":
    main()
