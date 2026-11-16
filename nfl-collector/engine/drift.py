"""The drift alarm: validate every committed capture against the pinned expectations,
reconcile field-by-field against peer captures, and FAIL LOUDLY (exit 1) on any
violation. This is the brief's 'fail the build loudly when a field goes missing'
requirement, wired as a hard gate.

Also emits data/derived/drift_report.json for the site (all numbers are computed here,
never typed into pages).
"""
import csv
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HERE, load, save

REPO = os.path.dirname(HERE)  # repository root


def check_injury(cap, pins, problems):
    e = cap["counts"]
    src_week = cap["source"].get("week")
    anchor = src_week == pins["week"]
    def fail(msg):
        problems.append({"capture": cap["capture_id"], "problem": msg})
    for f in pins["required_fields"]:
        if cap["rows"] and f not in cap["rows"][0]:
            fail(f"required field missing from capture schema: {f}")
    missing = [f for f in pins["must_be_nonblank"]
               if any(not r.get(f) for r in cap["rows"])]
    if missing:
        fail(f"required field(s) blank in some rows: {missing}")
    vocab = {r["game_status"] for r in cap["rows"] if r["game_status"]}
    bad = vocab - set(pins["allowed_game_status"])
    if bad:
        fail(f"game-status vocabulary drift: {sorted(bad)}")
    pvocab = {r["practice_status"] for r in cap["rows"] if r["practice_status"]}
    badp = pvocab - set(pins["allowed_practice_status"])
    if badp:
        fail(f"practice-status vocabulary drift: {sorted(badp)}")
    designated = sum(1 for r in cap["rows"] if r["game_status"])
    cover = 100.0 * designated / len(cap["rows"]) if cap["rows"] else 0
    if cover < pins["designation_coverage_floor_pct"]:
        fail(f"designation coverage {cover:.1f}% below floor {pins['designation_coverage_floor_pct']}% "
             f"(a lost designation column, not a league change)")
    if anchor:
        if e["rows_total"] != pins["rows_total"]:
            fail(f"pinned row count {pins['rows_total']} != captured {e['rows_total']}")
        if e["club_sections"] != pins["club_sections"]:
            fail(f"pinned club sections {pins['club_sections']} != captured {e['club_sections']}")
        if e["game_sections"] != pins["game_sections"]:
            fail(f"pinned game sections {pins['game_sections']} != captured {e['game_sections']}")
        mine = Counter(r["team"] for r in cap["rows"])
        diff = {k: (pins["rows_by_club"].get(k), mine.get(k, 0))
                for k in set(pins["rows_by_club"]) | set(mine)
                if pins["rows_by_club"].get(k) != mine.get(k, 0)}
        if diff:
            fail(f"per-club row counts drift vs pin: {diff}")
        if designated != pins["injury_labelled_rows"]:
            fail(f"pinned injury-labelled rows {pins['injury_labelled_rows']} != captured {designated}")
    return {"capture": cap["capture_id"], "anchored_to_week_pin": anchor,
            "rows_total": e["rows_total"], "club_sections": e["club_sections"],
            "game_sections": e["game_sections"], "designated_rows": designated,
            "designation_coverage_pct": round(cover, 1)}


def check_transactions(cap, pins, problems):
    missing = [f for f in pins["required_fields"]
               if any(not r.get(f) and not (f == "position" and pins["position_blank_allowed"])
                      for r in cap["rows"])]
    if missing:
        problems.append({"capture": cap["capture_id"], "problem": f"required field(s) blank: {missing}"})
    if "expected_rows_2026_11" in pins and cap.get("kind") == "league_transactions_reserve_list_month":
        if cap["counts"]["rows_total"] != pins["expected_rows_2026_11"]:
            problems.append({"capture": cap["capture_id"],
                             "problem": f"pinned November reserve rows {pins['expected_rows_2026_11']} "
                                        f"!= captured {cap['counts']['rows_total']}"})
        bad = {r["transaction"] for r in cap["rows"]} - {pins["expected_transaction_value"]}
        if bad:
            problems.append({"capture": cap["capture_id"],
                             "problem": f"unexpected transaction value(s): {sorted(bad)}"})


def check_depth(cap, pins, problems):
    src = cap["source"]
    if not src.get("page_status_line_as_printed", "").startswith("Unofficial"):
        problems.append({"capture": cap["capture_id"],
                         "problem": "the club's own 'Unofficial' status line was not captured verbatim"})


def reconcile_peers(cap, pins, problems):
    results = []

    def _key(rows):
        # Common key space across peer captures: (team, printed player name). The
        # availability-desk peer also records slugs, which the field map below compares
        # as a field; the nfl-book peer records no slug at all, so names are the only
        # shared key. A duplicated (team, player) key would break this - guard loudly.
        seen = {}
        for r in rows:
            k = (r["team"], r["player"])
            if k in seen:
                problems.append({"capture": "reconciliation",
                                 "problem": f"duplicate (team, player) key {k} — reconcile on a finer key"})
            seen[k] = r
        return seen

    want = _key(cap["rows"])
    for peer in pins["cross_capture_reconciliation"]["peers"]:
        ppath = os.path.join(REPO, peer["path"])
        if peer["path"].endswith(".csv"):
            with open(ppath, newline="", encoding="utf-8") as fh:
                prows = list(csv.DictReader(fh))
        else:
            with open(ppath, encoding="utf-8") as fh:
                prows = json.load(fh)["rows"]
        fmap = peer["fields"]
        aliases = pins["cross_capture_reconciliation"].get("club_code_aliases", {})
        aliases = {k: v for k, v in aliases.items() if k != "why"}
        pwant = _key(prows)
        if aliases:
            pwant = {(aliases.get(t, t), p): r for (t, p), r in pwant.items()}
        diffs = []
        for key, mine in want.items():
            theirs = pwant.get(key)
            if theirs is None:
                diffs.append({"key": key, "kind": "absent_in_peer"})
                continue
            for my_f, their_f in fmap.items():
                mine_v = mine.get(my_f, "")
                peer_v = theirs.get(their_f, "")
                if my_f == "team" and my_f in fmap:
                    # club codes: reconcile through the published alias map, not raw equality
                    peer_v = aliases.get(peer_v, peer_v)
                if mine_v != peer_v:
                    diffs.append({"key": key, "kind": "field_diff", "field": my_f,
                                  "mine": mine_v, "peer": peer_v})
        for key in pwant.keys() - want.keys():
            diffs.append({"key": key, "kind": "absent_in_mine"})
        results.append({"peer": peer["path"], "peer_rows": len(prows), "mine_rows": len(cap["rows"]),
                        "keys_compared": len(want), "differences": len(diffs), "detail": diffs[:20]})
        if diffs:
            problems.append({"capture": cap["capture_id"],
                             "problem": f"{len(diffs)} reconciliation differences vs peer {peer['path']} "
                                        f"(published on the captures page, never silently resolved)"})
    return results


def main():
    pins = load("data/drift_expectations.json")
    cap_date = "2026-11-16"
    injury = load(f"data/captures/{cap_date}/league_injury_report_week10.json")
    txn = load(f"data/captures/{cap_date}/league_transactions_trades_2026-11.json")
    resv = load(f"data/captures/{cap_date}/league_reserve_list_2026-11.json")
    depth = load(f"data/captures/{cap_date}/club_depth_gb.json")
    problems = []
    inj_report = check_injury(injury, pins["league_injury_report"], problems)
    check_transactions(txn, pins["league_transactions"], problems)
    check_transactions(resv, pins["league_reserve_list"], problems)
    check_depth(depth, pins["club_depth_gb"], problems)
    recon = reconcile_peers(injury, pins, problems)
    report = {
        "dataset": "nfl_collector_drift_report",
        "built_utc": "2026-11-16",
        "captures_checked": 4,
        "injury_report_check": inj_report,
        "peer_reconciliation": recon,
        "problems": problems,
        "result": "FAIL" if problems else "PASS",
    }
    save("data/derived/drift_report.json", report)
    if problems:
        print("drift: FAIL — the build must fail loudly, per the brief:")
        for p in problems:
            print(f"  - [{p['capture']}] {p['problem']}")
        sys.exit(1)
    print(f"drift: PASS — injury capture {inj_report['rows_total']} rows / "
          f"{inj_report['club_sections']} clubs / {inj_report['designated_rows']} designated "
          f"({inj_report['designation_coverage_pct']}%), all pins hold, "
          f"peer reconciliation clean across {len(recon)} peer captures")


if __name__ == "__main__":
    main()
