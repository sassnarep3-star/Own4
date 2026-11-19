#!/usr/bin/env python3
"""Null test for the deck's walk-forward: permute game margins across the schedule so team
identity carries no information, then rerun the frozen pipeline.

If the pipeline is honest, the observed BSS must sit far in the right tail of this null
distribution. This is the "removal of luck" evidence: the signal is not an artefact of the
protocol, the ridge grid or the sigma rule.

Reads: ../nfl-live-board/data/corpus_2026.json ; writes: data/null.json
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model_eval import (fit_margin, predict_margin, team_index, phi, sd, CORPUS, DATA,
                        SCORE_WEEKS, lcg)

REPS = int(sys.argv[1]) if len(sys.argv) > 1 else 200
LAM = 10.0          # the value the frozen pipeline selected on weeks 4-7

corpus = json.load(open(CORPUS, encoding="utf-8"))["corpus"]
idx, teams = team_index(corpus)


def run(games):
    pre = []
    for w in SCORE_WEEKS:
        tr = [g for g in games if g["week"] < w]
        te = [g for g in games if g["week"] == w]
        th, _ = fit_margin(tr, idx, LAM)
        res = [float(g["home_pts"] - g["away_pts"]) - predict_margin(th, idx, g) for g in tr]
        sig = max(sd(res), 1e-6)
        hr = sum(1 for g in tr if g["home_pts"] > g["away_pts"]) / len(tr)
        for g in te:
            if g["home_pts"] == g["away_pts"]:
                continue
            y = 1.0 if g["home_pts"] > g["away_pts"] else 0.0
            pre.append((phi(predict_margin(th, idx, g) / sig), hr, y))
    n = len(pre)
    bs = sum((p - y) ** 2 for p, _, y in pre) / n
    bb = sum((b - y) ** 2 for _, b, y in pre) / n
    return 1.0 - bs / bb


observed = run(corpus)
margins = [(g["home_pts"] - g["away_pts"]) for g in corpus]
rnd = lcg(777)
null = []
for _ in range(REPS):
    perm = margins[:]
    for i in range(len(perm) - 1, 0, -1):          # Fisher-Yates, deterministic
        j = int(rnd() * (i + 1)) % (i + 1)
        perm[i], perm[j] = perm[j], perm[i]
    g2 = []
    for g, m in zip(corpus, perm):
        gg = dict(g)
        base = (g["home_pts"] + g["away_pts"])
        hh = (base + m) / 2.0
        gg["home_pts"] = int(round(hh))
        gg["away_pts"] = int(round(base - hh))
        g2.append(gg)
    null.append(run(g2))

null.sort()
ge = sum(1 for v in null if v >= observed) / len(null)
out = {
    "dataset": "nfl_command_deck_null", "built_utc": "2026-11-19",
    "what": "walk-forward BSS of CD-1 recomputed on %d margin-permuted schedules" % REPS,
    "why": "separates protocol artefact from team information: under the null the schedule is real "
           "but team identity carries no outcome information",
    "observed_bss": round(observed, 4),
    "null_reps": REPS,
    "null_mean": round(sum(null) / len(null), 4),
    "null_q05": round(null[int(0.05 * len(null))], 4),
    "null_q50": round(null[int(0.50 * len(null))], 4),
    "null_q95": round(null[int(0.95 * len(null)) - 1], 4),
    "null_max": round(null[-1], 4),
    "p_permutation": round(ge, 4),
    "permutation_floor": round(1.0 / (REPS + 1), 4),
    "interpretation": "observed BSS exceeds every one of the %d null schedules" % REPS
    if ge == 0 else "observed BSS is not beyond the null at this rep count",
}
json.dump(out, open(os.path.join(DATA, "null.json"), "w", encoding="utf-8"), indent=1, sort_keys=True)
print(json.dumps(out, indent=1))
