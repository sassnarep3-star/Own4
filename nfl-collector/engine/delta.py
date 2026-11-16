"""Build the dated read-series deltas for the Week 10 availability report and the
cross-source conflict flags.

The brief: 'Treat the injury report as a timestamped series, not a weekly snapshot' and
'Store every injury-hub read with its clock time and publish the delta, never the level'.

The series below contains every dated read of the Week 10 report that exists in this
repository (two by peer namespaces, read with their own fetch paths; one by this session).
Deltas are computed BETWEEN consecutive reads; a read never replaces a previous one.
Conflict flags join the transactions capture (trades) to the report rows.
"""
import csv
import json
import os
import sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HERE, load, save

REPO = os.path.dirname(HERE)
ALIAS = {"ARI": "AZ"}  # published in drift_expectations.json; reconciliation only


def _norm(rows, fields):
    out = OrderedDict()
    for r in rows:
        team = ALIAS.get(r.get("team", ""), r.get("team", ""))
        out[(team, r.get("player", ""))] = {f: r.get(fields.get(f, f), "") for f in fields}
    return out


def _delta(a, b, a_label, b_label):
    """Deltas between two reads; publishes transitions, never levels."""
    rows = []
    for key in sorted(set(a) | set(b)):
        ra, rb = a.get(key), b.get(key)
        team, player = key
        if ra is None:
            rows.append({"team": team, "player": player, "change": "row_added",
                         "from_read": a_label, "to_read": b_label,
                         "to_practice_status": rb["practice_status"],
                         "to_game_status": rb["game_status"], "to_injury": rb["injury"]})
            continue
        if rb is None:
            rows.append({"team": team, "player": player, "change": "row_removed",
                         "from_read": a_label, "to_read": b_label,
                         "from_practice_status": ra["practice_status"],
                         "from_game_status": ra["game_status"], "from_injury": ra["injury"]})
            continue
        for f, label in (("practice_status", "practice_status"),
                         ("game_status", "game_status"), ("injury", "injury")):
            if ra[f] != rb[f]:
                rows.append({"team": team, "player": player, "change": f"{label}_change",
                             "from_read": a_label, "to_read": b_label,
                             f"from_{label}": ra[f], f"to_{label}": rb[f]})
    return rows


def build_series():
    """Every dated read of the Week 10 report present in the repository, oldest first."""
    with open(os.path.join(REPO, "nfl-availability-desk/data/availability_snapshot_2026-11-15.csv"),
              newline="", encoding="utf-8") as fh:
        r1_rows = list(csv.DictReader(fh))
    with open(os.path.join(REPO, "nfl-book/data/injuries_week10_capture.json"), encoding="utf-8") as fh:
        r2_rows = json.load(fh)["rows"]
    mine = load("data/captures/2026-11-16/league_injury_report_week10.json")
    r3_rows = mine["rows"]
    # each peer names the same fields differently (documented in drift_expectations.json):
    f_csv = {"practice_status": "practice_status", "game_status": "game_status", "injury": "injury"}
    f_book = {"practice_status": "practice", "game_status": "game_status", "injury": "injury"}
    f_mine = {"practice_status": "practice_status", "game_status": "game_status", "injury": "injury"}
    series = [
        {"read_id": "R1", "captured_by": "nfl-availability-desk (peer namespace)",
         "window_utc": "2026-11-15T23:23:14Z .. 2026-11-15T23:34:00Z",
         "rows": len(r1_rows),
         "context": "read live during the Week 10 Sunday window: three Sunday games in progress, two not kicked off",
         "file": "nfl-availability-desk/data/availability_snapshot_2026-11-15.csv"},
        {"read_id": "R2", "captured_by": "nfl-book (peer namespace)",
         "window_utc": "2026-11-16 (window as recorded by that session; per-call clocks not exposed by its fetch path)",
         "rows": len(r2_rows),
         "context": "all 8 chunks, raw transcript sha256 sealed by that session's capture file",
         "file": "nfl-book/data/injuries_week10_capture.json"},
        {"read_id": "R3", "captured_by": "nfl-collector (this namespace)",
         "window_utc": "2026-11-16T02:35:00Z .. 2026-11-16T03:05:00Z",
         "rows": len(r3_rows),
         "context": "read after all Week 10 Thursday/Sunday games, before the Monday-night kickoff",
         "file": "nfl-collector/data/captures/2026-11-16/league_injury_report_week10.json"},
    ]
    a1 = _norm(r1_rows, f_csv)
    a2 = _norm(r2_rows, f_book)
    a3 = _norm(r3_rows, f_mine)
    deltas = _delta(a1, a2, "R1", "R2") + _delta(a2, a3, "R2", "R3")
    summary = {
        "n_reads": len(series),
        "n_delta_rows": len(deltas),
        "by_kind": {},
        "reads_rows": [s["rows"] for s in series],
    }
    for d in deltas:
        summary["by_kind"][d["change"]] = summary["by_kind"].get(d["change"], 0) + 1
    return {"dataset": "nfl_collector_series_deltas", "built_utc": "2026-11-16",
            "rule": "deltas are computed between consecutive reads; a read never replaces a "
                    "previous one and no read is published as a live level",
            "series": series, "deltas": deltas, "summary": summary}


def build_conflicts():
    """Cross-source conflicts: transactions (trades + reserve list) joined to the report rows."""
    txn = load("data/captures/2026-11-16/league_transactions_trades_2026-11.json")
    res = load("data/captures/2026-11-16/league_reserve_list_2026-11.json")
    inj = load("data/captures/2026-11-16/league_injury_report_week10.json")
    by_slug = {}
    for r in inj["rows"]:
        by_slug.setdefault(r["player_slug"], []).append(r)
    rows = []
    for t in txn["rows"]:
        slug = t["player_slug"]
        hits = by_slug.get(slug, [])
        from_hits = [h for h in hits if h["team"] == t["from"]]
        to_hits = [h for h in hits if h["team"] == t["to"]]
        if from_hits and to_hits:
            verdict = "listed_on_BOTH_clubs_reports"
        elif from_hits:
            verdict = "CONFLICT_traded_player_still_listed_on_former_club_report"
        elif to_hits:
            verdict = "listed_on_new_club_report"
        else:
            verdict = "not_listed_on_either_report"
        rows.append({
            "player": t["player"], "from": t["from"], "to": t["to"],
            "trade_date_as_printed": t["date_as_printed"],
            "on_former_club_report": bool(from_hits),
            "on_new_club_report": bool(to_hits),
            "verdict": verdict,
            "source_transaction": "https://www.nfl.com/transactions/league/trades/2026/11",
            "source_report": "https://www.nfl.com/injuries/league/2026/reg10",
        })
    n_conflicts = sum(1 for r in rows if r["verdict"].startswith("CONFLICT"))
    # --- reserve-list join: 'not listed' must never mean 'available' ---
    reserve_rows = []
    for t in res["rows"]:
        hits = by_slug.get(t["player_slug"], [])
        own_hits = [h for h in hits if h["team"] == t["to"]]
        if own_hits:
            verdict = "on_IR_and_listed_on_club_report"
        else:
            verdict = "on_IR_and_absent_from_report (not listed must not be read as available)"
        reserve_rows.append({
            "player": t["player"], "club": t["to"], "ir_date_as_printed": t["date_as_printed"],
            "on_report": bool(own_hits), "verdict": verdict,
            "source_reserve": "https://www.nfl.com/transactions/league/reserve-list/2026/11",
            "source_report": "https://www.nfl.com/injuries/league/2026/reg10",
        })
    n_absent = sum(1 for r in reserve_rows if not r["on_report"])
    return {"dataset": "nfl_collector_conflicts", "built_utc": "2026-11-16",
            "rule": "a player traded on a printed date who is still listed on his FORMER club's "
                    "weekly report after that date is a cross-source conflict; published as a flag, "
                    "never resolved by editing either source. Separately, every Reserve/Injured "
                    "placement is joined to the report: an IR player absent from the club's report "
                    "is the brief's 'not listed never means available' case.",
            "n_trades_checked": len(rows), "n_conflicts": n_conflicts,
            "rows": rows,
            "reserve_join": {
                "n_reserve_rows_checked": len(reserve_rows),
                "n_ir_absent_from_report": n_absent,
                "rows": reserve_rows,
                "coverage_limitation": "the rendered November reserve table begins at 11/07; IR "
                                       "placements dated 11/05–11/06 are not visible in the rendered "
                                       "view and are therefore not in this join (recorded as printed)"
            },
            "note": "reserve-list transactions are captured from the league's own category page"
            }


def main():
    series = build_series()
    conflicts = build_conflicts()
    save("data/derived/series_deltas.json", series)
    save("data/derived/conflicts.json", conflicts)
    print(f"delta: {series['summary']['n_reads']} dated reads, "
          f"{series['summary']['n_delta_rows']} delta rows "
          f"({series['summary']['by_kind']})")
    print(f"delta: conflicts — {conflicts['n_conflicts']} of {conflicts['n_trades_checked']} "
          f"trades show the player still on the former club's report")


if __name__ == "__main__":
    main()
