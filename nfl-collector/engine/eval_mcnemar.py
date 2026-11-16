"""Evaluate PREREG-002: exact McNemar, model side (S1) vs better-record baseline,
on 2026 regular-season weeks >= 11 ONLY.

Refusal conditions (all loud, exit non-zero):
  (a) any game with week < 11 would enter the sample;
  (b) any file frozen in data/prereg.json (rule file, peer engine files, this evaluator)
      has changed since registration;
  (c) the calibration re-run on weeks 3..10 does not reproduce the published nfl-book
      metrics (the evaluator's reimplementation has diverged from the frozen engine).

Until at least 10 discordant pairs exist the evaluator reports PENDING and no claim.
"""
import math
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HERE, REPO, load, save

PREREG_ID = "PREREG-002"


def _refuse(msg):
    print(f"eval_mcnemar: REFUSED — {msg}")
    sys.exit(1)


def _prereg_check():
    import preregister as P
    reg = load("data/prereg.json")
    entry = reg["registered"].get(PREREG_ID)
    if not entry:
        _refuse("PREREG-002 is not registered")
    cur = P._sha(entry["file"])
    if cur != entry["file_sha256"]:
        _refuse("rule file edited after registration (refusal condition (b))")
    for p, h in entry["frozen_peer_files"].items():
        if P._sha(p) != h:
            _refuse(f"frozen peer engine file changed: {p} (refusal condition (b))")
    if P._sha(P.EVALUATOR) != entry["frozen_evaluator_sha256"]:
        _refuse("evaluator edited after registration (refusal condition (b))")
    return entry


def _load_peer_engine():
    sys.path.insert(0, os.path.join(REPO, "nfl-book", "engine"))
    import backtest as B  # noqa: PLC0415 — frozen peer engine, hash-checked above
    return B


def _better_record_pick(B, games_cache, f):
    """Arm B, exactly as nfl-book _posthoc_record_baseline implements it: records from
    games with week < f['week']; larger wins-minus-losses differential; tie -> HOME."""
    r = {t: [0, 0] for t in set()}
    rec = {}
    w = f["week"]
    if w not in rec:
        from collections import defaultdict
        rr = defaultdict(lambda: [0, 0])
        for g in games_cache:
            if g["week"] >= w:
                continue
            if g["home_pts"] > g["away_pts"]:
                rr[g["home"]][0] += 1
                rr[g["away"]][1] += 1
            elif g["away_pts"] > g["home_pts"]:
                rr[g["away"]][0] += 1
                rr[g["home"]][1] += 1
        rec[w] = rr
    r = rec[w]
    wh, ww = r[f["home"]]
    ah, aw = r[f["away"]]
    return (wh - ww) > (ah - aw) if (wh - ww) != (ah - aw) else True


def _grade(B, games, weeks, enforce_window=True):
    """Return per-game (model_correct, baseline_correct) rows for the given weeks.
    The week<11 refusal applies ONLY to the evaluation sample; the calibration leg
    (refusal condition (c)) legitimately re-runs the published weeks 3..10."""
    global_games = games
    B._GAMES_CACHE = global_games
    fcs = B.run_forecasts(global_games, weeks)
    rows = []
    for f in fcs:
        if f["actual_margin"] == 0:
            continue  # push: excluded from both arms per the frozen rule
        if enforce_window and f["week"] < 11:
            _refuse(f"game {f['game_id']} with week < 11 entered the sample (refusal condition (a))")
        home_won = f["actual_margin"] > 0
        m_ok = home_won if f["p_home"] >= 0.5 else (not home_won)
        b_pick_home = _better_record_pick(B, global_games, f)
        b_ok = b_pick_home == home_won
        rows.append({"game_id": f["game_id"], "week": f["week"],
                     "model_correct": bool(m_ok), "baseline_correct": bool(b_ok)})
    return rows


def _wilson(x, n):
    z = 1.96
    if n == 0:
        return None, None
    p = x / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return round((c - r) / d, 4), round((c + r) / d, 4)


def _exact_mcnemar_p(b, c):
    n = b + c
    if n == 0:
        return None
    tail = sum(math.comb(n, i) for i in range(b, n + 1))
    return tail / (2 ** n)


def _calibrate(B, games):
    """Refusal condition (c): the evaluator must reproduce the published nfl-book
    backtest metrics on weeks 3..10 before it may evaluate weeks >= 11."""
    pub = load("../nfl-book/data/backtest.json")
    s1 = pub["metrics"]["S1"]
    rows = _grade(B, games, list(range(3, 11)), enforce_window=False)
    n = len(rows)
    mw = sum(1 for r in rows if r["model_correct"])
    bw = sum(1 for r in rows if r["baseline_correct"])
    # the published metrics are rounded to 4 decimals; compare like-for-like
    ok = (n == s1["n_decided"]) \
        and (round(mw / n, 4) == s1["accuracy"]) \
        and (round(bw / n, 4) == s1["extra"]["posthoc_better_record_accuracy"])
    return {"published_n": s1["n_decided"], "recomputed_n": n,
            "published_model_accuracy": s1["accuracy"], "recomputed_model_accuracy": round(mw / n, 4),
            "published_baseline_accuracy": s1["extra"]["posthoc_better_record_accuracy"],
            "recomputed_baseline_accuracy": round(bw / n, 4),
            "result": "REPRODUCED" if ok else "DIVERGED"}


def main():
    entry = _prereg_check()
    B = _load_peer_engine()
    feed = load("../nfl-book/data/results_feed.json")
    games = feed["rows"]
    calib = _calibrate(B, games)
    if calib["result"] != "REPRODUCED":
        _refuse(f"calibration diverged from the published backtest: {calib} (refusal condition (c))")
    weeks_present = sorted({g["week"] for g in games})
    eval_weeks = [w for w in range(11, max(weeks_present) + 1)]
    out = {
        "dataset": "nfl_collector_prereg002_mcnemar_eval",
        "prereg_id": PREREG_ID,
        "evaluated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "registration": {"file_sha256": entry["file_sha256"], "registered_utc": entry["registered_utc"]},
        "calibration_weeks_3_10": calib,
        "weeks_available": weeks_present,
        "status": "PENDING",
        "sample_window": "2026 regular season, weeks >= 11 only (PREREG-002 §2)",
        "gate": {"qualifying": "p < 0.05 and b+c >= 30",
                 "provisional": "p < 0.05 and 10 <= b+c < 30",
                 "not_evaluable": "b+c < 10"},
        "history": [],
    }
    if eval_weeks:
        rows = _grade(B, games, eval_weeks)
        b = sum(1 for r in rows if r["model_correct"] and not r["baseline_correct"])
        c = sum(1 for r in rows if not r["model_correct"] and r["baseline_correct"])
        mw = sum(1 for r in rows if r["model_correct"])
        bw = sum(1 for r in rows if r["baseline_correct"])
        n = len(rows)
        p = _exact_mcnemar_p(b, c) if (b + c) >= 10 else None
        out.update({
            "n_games": n, "model_correct": mw, "baseline_correct": bw,
            "model_accuracy": round(mw / n, 4) if n else None,
            "model_accuracy_ci95": _wilson(mw, n),
            "baseline_accuracy": round(bw / n, 4) if n else None,
            "baseline_accuracy_ci95": _wilson(bw, n),
            "discordant": {"model_right_baseline_wrong": b, "model_wrong_baseline_right": c,
                           "n_discordant": b + c},
            "exact_mcnemar_p_one_sided": round(p, 6) if p is not None else None,
            "status": ("QUALIFYING" if (p is not None and p < 0.05 and b + c >= 30)
                       else "PROVISIONAL" if (p is not None and p < 0.05)
                       else "EVALUATED_NO_EFFECT" if p is not None
                       else "PENDING_NOT_EVALUABLE"),
        })
        out["history"].append({"evaluated_utc": out["evaluated_utc"],
                               "n_games": n, "b": b, "c": c, "p": out["exact_mcnemar_p_one_sided"]})
    prev_path = os.path.join(HERE, "data", "derived", "mcnemar_eval.json")
    if os.path.exists(prev_path):
        prev = load("data/derived/mcnemar_eval.json")
        # determinism: if the evaluation state has not changed, keep the committed file
        # byte-identical (no new timestamp) — a re-run with the same sample is a no-op
        same_state = (prev.get("status") == out["status"]
                      and prev.get("n_games") == out.get("n_games")
                      and (prev.get("discordant") or {}).get("n_discordant")
                      == (out.get("discordant") or {}).get("n_discordant"))
        if same_state and not out["history"]:
            print("eval_mcnemar: evaluation state unchanged — committed artefact left untouched")
            return
        out["history"] = (prev.get("history") or []) + out["history"]
    save("data/derived/mcnemar_eval.json", out)
    print(f"eval_mcnemar: calibration {calib['result']} (weeks 3..10 reproduce the published "
          f"backtest exactly); evaluation weeks {eval_weeks or 'none available yet'} -> {out['status']}")


if __name__ == "__main__":
    main()
