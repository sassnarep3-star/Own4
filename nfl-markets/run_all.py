#!/usr/bin/env python3
"""nfl-markets — end-to-end deterministic pipeline (stdlib only).

Reproduces every data file in data/ from data/raw/ + the peer captures:
  1. load raw archives (provenance: data/raw/provenance.json)
  2. walk-forward model (calibration frozen on 1999-2010)
  3. verified results feed (+ 32/32 standings reconciliation, QC)
  4. price-snapshot store (origination order side->total->ML; fair/open/close/diffs)
  5. strategies -> leaderboard (signal separated from staking)
  6. promotion gates MG-1..MG-8 + demotion-gate counterfactual simulation
  7. injury & replacement-depth tracker (official report + flagged third-party depth)
  8. correlations (official-inputs group; third-party group flagged)
  9. manifest with SHA-256 of every output
Run:  python3 run_all.py
"""
import hashlib, json, os, sys, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import config as C, loader, model, results_feed as F, snapshots as S, strategies as ST, gates as G, injuries as INJ, correlations as K

OUT = C.OUT

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()[:16]

def main():
    manifest = {"generated_from": "nfl-markets/data/raw", "files": {}}
    games = loader.compile_league()
    m, cal = model.run_model(games)

    # results feed + QC
    feed, rec = F.build()
    C.w(os.path.join(OUT, "results_feed.csv"), feed, list(feed[0].keys()))
    manifest["files"]["data/results_feed.csv"] = sha(os.path.join(OUT, "results_feed.csv"))
    snap = S.build(m, games)
    C.w(os.path.join(OUT, "price_snapshots.csv"), snap, list(snap[0].keys()))
    manifest["files"]["data/price_snapshots.csv"] = sha(os.path.join(OUT, "price_snapshots.csv"))

    # strategies + leaderboard
    side = ST.select_side_bets(snap)
    total = ST.select_total_bets(snap)
    ml = ST.select_ml_bets(snap)
    par = ST.build_parlays(side, total)
    lb = ST.leaderboard(side, total, ml, par, feed)
    feed_index = {r["game_id"]: r for r in feed}

    hold = {}
    for strat, sels in (("STRAT-SIDE-3", side), ("STRAT-TOTAL-3", total)):
        h = [s for s in sels if s["season"] == 2026 and s["played"]]
        beats = [ST.beat_close(s, feed_index) for s in h]
        beats = [b for b in beats if b is not None]
        hold[strat] = {"pass": (sum(beats) / len(beats) > 0.5) if beats else None,
                       "detail": f"2026 W1-10 beat-close {sum(beats)}/{len(beats)} = {sum(beats)/len(beats):.1%}" if beats else "n/a"}
    mism = 0 if rec["mismatches_vs_official_capture"].get("status") == "OK" else 99
    for r in lb:
        r["gates"] = G.evaluate_gates(r, holdout_rows=hold.get(r["id"]), reconc_mismatches=mism)

    def ordered(sels):
        ss = sorted([s for s in sels if s["played"]], key=lambda s: (s["season"], s["week"], s["game_id"]))
        units, beat, edge, week_ends, cur_week = [], [], [], [], None
        for s in ss:
            w, _ = ST.settle_selection(s, feed_index)
            if w is None or w == 0.5:
                continue
            units.append(0.9090909 if w == 1.0 else -1.0)
            b = ST.beat_close(s, feed_index)
            beat.append(b if b is not None else 0)
            edge.append(s["edge_vs_close_signed"])
            if cur_week is not None and (s["season"], s["week"]) != cur_week:
                week_ends.append(len(units))
            cur_week = (s["season"], s["week"])
        week_ends.append(len(units))
        return units, beat, edge, week_ends

    demo = {}
    for strat, sels in (("STRAT-SIDE-3", side), ("STRAT-TOTAL-3", total)):
        u, b, e, we = ordered(sels)
        res = G.evaluate_demotion(u, b, e, force_live=True, eval_at=we)
        demo[strat] = {"counterfactual_force_live": True, "n_settled": len(u),
                       "n_trigger_events": len(res["events"]), "events_first_10": res["events"][:10],
                       "final_state_live": res["final_state_live"]}
    C.j(os.path.join(OUT, "leaderboard.json"), lb)
    C.j(os.path.join(OUT, "gates_evaluation.json"),
        {"promotion_gates": G.PROMOTION_GATES, "holdout_2026": hold,
         "demotion": {"rules": G.DEMOTION_RULES, "config": G.DEMOTION_CONFIG, "simulations": demo}})
    manifest["files"]["data/leaderboard.json"] = sha(os.path.join(OUT, "leaderboard.json"))
    manifest["files"]["data/gates_evaluation.json"] = sha(os.path.join(OUT, "gates_evaluation.json"))

    # selections CSV (audit trail of every graded selection)
    sel_rows = []
    for s in side:
        sel_rows.append({"strategy": "STRAT-SIDE-3", **{k: s.get(k) for k in
            ("game_id", "season", "week", "gameday", "market", "side", "fair", "line_entry", "line_close",
             "edge_vs_close_signed", "entry_policy", "entry_status", "played", "official_source_url")}})
    for s in total:
        sel_rows.append({"strategy": "STRAT-TOTAL-3", **{k: s.get(k) for k in
            ("game_id", "season", "week", "gameday", "market", "side", "fair", "line_entry", "line_close",
             "edge_vs_close_signed", "entry_policy", "entry_status", "played", "official_source_url")}})
    for s in ml:
        sel_rows.append({"strategy": "STRAT-ML-5", **{k: s.get(k) for k in
            ("game_id", "season", "week", "gameday", "market", "side", "fair", "edge_vs_close_signed",
             "played", "official_source_url")}, "line_entry": "", "line_close": "",
             "entry_policy": "signal-only", "entry_status": ""})
    C.w(os.path.join(OUT, "selections.csv"), sel_rows, list(sel_rows[0].keys()))
    manifest["files"]["data/selections.csv"] = sha(os.path.join(OUT, "selections.csv"))

    # injuries / replacement depth
    rows, summary, meta = INJ.compute()
    C.j(os.path.join(OUT, "replacement_depth.json"), {"meta": meta, "rows": rows, "team_summary": summary})
    manifest["files"]["data/replacement_depth.json"] = sha(os.path.join(OUT, "replacement_depth.json"))

    # correlations
    corr = K.compute(feed, snap)
    C.j(os.path.join(OUT, "correlations.json"), corr)
    manifest["files"]["data/correlations.json"] = sha(os.path.join(OUT, "correlations.json"))

    # calibration + model QC
    C.j(os.path.join(OUT, "model_calibration.json"), cal)
    manifest["files"]["data/model_calibration.json"] = sha(os.path.join(OUT, "model_calibration.json"))

    # originated upcoming markets (current origination output)
    upcoming = [r for r in snap if r["close_verification_status"] == "PENDING-CLOSE"]
    C.w(os.path.join(OUT, "originated_upcoming.csv"), upcoming, list(snap[0].keys()))
    manifest["files"]["data/originated_upcoming.csv"] = sha(os.path.join(OUT, "originated_upcoming.csv"))

    # standings reconciliation QC
    C.j(os.path.join(OUT, "results_feed_qc.json"), {
        "n_rows": len(feed), "standings_reconciliation_2026": rec,
        "coverage": {"first_season": min(r["season"] for r in feed), "last_season": max(r["season"] for r in feed),
                     "games_2026_played": sum(1 for r in feed if r["season"] == 2026)},
        "snapshot_store": {"n_rows": len(snap),
                           "close_statuses": dict(collections.Counter(r["close_verification_status"] for r in snap)),
                           "open_statuses": dict(collections.Counter(r["open_verification_status"] for r in snap))},
        "model": cal})
    manifest["files"]["data/results_feed_qc.json"] = sha(os.path.join(OUT, "results_feed_qc.json"))

    # quick summary print
    print(f"feed rows: {len(feed)} | snapshots: {len(snap)} | selections: {len(sel_rows)}")
    print(f"standings reconciliation: {rec['mismatches_vs_official_capture'].get('status')}")
    print(f"upcoming originated markets: {len(upcoming)}")
    for r in lb:
        print(f"  {r['id']}: signal n={r['signal'].get('n_selections')} beat_close={r['signal'].get('beat_close_rate')} "
              f"roi={(r['staking'] or {}).get('roi_flat')} gates_pass={sum(1 for g in r.get('gates',[]) if g['pass'] is True)}"
              f"/{sum(1 for g in r.get('gates',[]) if g['pass'] is not None)}")
    C.j(os.path.join(OUT, "manifest.json"), manifest)
    print("manifest written:", len(manifest["files"]), "files")

if __name__ == "__main__":
    main()
