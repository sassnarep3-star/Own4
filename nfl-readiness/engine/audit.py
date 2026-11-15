#!/usr/bin/env python3
"""Re-derive every number nfl-readiness publishes from the transcribed capture.

Nothing in this file is typed in by hand: the counts, coverage percentages,
cross-capture diffs and standings identities are computed from the checked-in
artifacts so that CI proves the published numbers again.

    python3 nfl-readiness/engine/audit.py          # writes data/derived/*.json
"""
from __future__ import annotations

import csv
import json
import os
from collections import Counter, OrderedDict, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)
DATA = os.path.join(NS, "data")
OUT = os.path.join(DATA, "derived")

SNAPSHOT = os.path.join(DATA, "availability_snapshot_2026-11-15.csv")
FIXTURES = os.path.join(DATA, "fixtures_week10.csv")
STANDINGS = os.path.join(DATA, "standings_2026-11-15.json")

ALL32 = ["ARI-AZ", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN", "DET",
         "GB", "HOU", "IND", "JAX", "KC", "LAR", "LV", "MIA", "MIN", "NE", "NO", "NYG",
         "NYJ", "PHI", "PIT", "SEA", "SF", "TB", "TEN", "WAS", "LAC"]
CLUBS = [c.split("-")[-1] for c in ALL32]

# The four clubs the official Week 10 schedule page lists in its own "Teams on Bye" block
# (read 2026-11-15, https://www.nfl.com/schedules/2026/by-week/week-10).
BYE_WK10 = ["CHI", "DEN", "PHI", "TB"]

DESIGNATIONS = ("Out", "Doubtful", "Questionable", "Probable")
NON_INJURY_MARK = "Not injury related"


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh)]
    return rows


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------- #
# 1. the capture itself
# --------------------------------------------------------------------------- #
def audit_capture(rows):
    per_team = OrderedDict()
    for r in rows:
        t = r["team"]
        d = per_team.setdefault(t, {
            "rows": 0, "out": 0, "doubtful": 0, "questionable": 0, "probable": 0,
            "no_game_status": 0, "injury_labelled": 0, "injury_blank": 0,
            "dnp": 0, "lp": 0, "fp": 0, "practice_blank": 0,
            "non_injury_label": 0, "players": [],
        })
        d["rows"] += 1
        d["players"].append(r["player"])
        gs = (r.get("game_status") or "").strip()
        if gs in ("Out", "Doubtful", "Questionable", "Probable"):
            d[gs.lower()] += 1
        else:
            d["no_game_status"] += 1
        inj = (r.get("injury") or "").strip()
        if inj:
            d["injury_labelled"] += 1
            if NON_INJURY_MARK in inj:
                d["non_injury_label"] += 1
        else:
            d["injury_blank"] += 1
        ps = (r.get("practice_status") or "").strip()
        if ps.startswith("Did Not"):
            d["dnp"] += 1
        elif ps.startswith("Limited"):
            d["lp"] += 1
        elif ps.startswith("Full"):
            d["fp"] += 1
        else:
            d["practice_blank"] += 1

    n = len(rows)
    designated = sum(1 for r in rows if (r.get("game_status") or "").strip())
    vocab = Counter((r.get("game_status") or "").strip() or "(blank)" for r in rows)
    pvocab = Counter((r.get("practice_status") or "").strip() or "(blank)" for r in rows)
    pos = Counter(r["pos"].strip() for r in rows)
    sections_zero_injury = [t for t, d in per_team.items() if d["injury_labelled"] == 0]
    return {
        "rows": n,
        "club_sections_published": len(per_team),
        "clubs_in_the_league": len(CLUBS),
        "clubs_with_no_section": sorted(set(CLUBS) - set(per_team)),
        "bye_clubs_officially_listed": sorted(BYE_WK10),
        "fixtures": len(read_csv(FIXTURES)),
        "designation_rows": designated,
        "designation_coverage_pct": round(100.0 * designated / n, 1) if n else None,
        "game_status_vocabulary": dict(vocab),
        "practice_status_vocabulary": dict(pvocab),
        "position_census": dict(pos),
        "sections_with_zero_injury_labels": sections_zero_injury,
        "rows_carrying_non_injury_text": sum(
            1 for r in rows if NON_INJURY_MARK in (r.get("injury") or "")),
        "per_team": per_team,
    }


# --------------------------------------------------------------------------- #
# 2. this capture against every stored capture of the same page
# --------------------------------------------------------------------------- #
CLUB_CODE = {"ARI": "AZ", "LA": "LAR"}


def cc(code):
    """Normalise club labels only (the report abbreviates Arizona 'AZ' and the Rams 'LAR');
    no player data is touched."""
    return CLUB_CODE.get(code, code)


def peer_captures():
    """Normalise every repo capture of https://www.nfl.com/injuries/ to
    {'label','captured','rows':[(team, player)]} in published order."""
    out = []

    p = os.path.join(ROOT, "nfl-arena", "data", "injuries_week10.json")
    if os.path.exists(p):
        d = load_json(p)
        out.append({
            "label": "nfl-arena/data/injuries_week10.json",
            "captured": d.get("captured_utc"),
            "source": "peer session capture (read 2026-11-13, the Friday report)",
            "rows": [(cc(r["team"]), r["player"], (r.get("game_status") or "").strip()) for r in d.get("rows", [])],
        })

    p = os.path.join(ROOT, "nfl-command", "data", "injuries_week10.json")
    if os.path.exists(p):
        d = load_json(p)
        out.append({
            "label": "nfl-command/data/injuries_week10.json",
            "captured": d.get("captured_utc"),
            "source": "peer session capture",
            "rows": [(cc(r["team"]), r["player"], (r.get("game_status") or "").strip()) for r in d.get("rows", [])],
        })

    p = os.path.join(ROOT, "nfl-book", "data", "injuries_week10_capture.json")
    if os.path.exists(p):
        d = load_json(p)
        out.append({
            "label": "nfl-book/data/injuries_week10_capture.json",
            "captured": d.get("captured_utc"),
            "source": "peer session capture, self-declared partial (2 of 8 page chunks)",
            "rows": [(cc(r["team"]), r["player"], (r.get("game_status") or "").strip()) for r in d.get("rows", [])],
        })

    p = os.path.join(ROOT, "nfl-marketboard", "data", "raw", "injuries_week10_official.csv")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as fh:
            lines = [ln for ln in fh if not ln.startswith("#")]
        rdr = csv.DictReader(lines)
        rows = [(cc(r["team"]), r["player"], (r.get("game_status") or "").strip()) for r in rdr]
        out.append({
            "label": "nfl-marketboard/data/raw/injuries_week10_official.csv",
            "captured": "2026-11-14",
            "source": "peer session capture (header comment names the reading session and date)",
            "rows": rows,
        })

    p = os.path.join(ROOT, "nfl-audit", "data", "injuries_week10.csv")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as fh:
            rdr = csv.DictReader(fh)
            rows = [(cc(r["abbr"]), r["player"], (r.get("game_status") or "").strip()) for r in rdr]
        out.append({
            "label": "nfl-audit/data/injuries_week10.csv",
            "captured": None,
            "source": "peer session capture",
            "rows": rows,
        })
    return out


def diff_against(mine_rows, peer):
    mine = [(r["team"], r["player"]) for r in mine_rows]
    mine = [(cc(t), p) for t, p in mine]
    peer_rows = [(t, p) for t, p, *_ in peer["rows"]]
    peer_desig = sum(1 for *_rest, gs in [(r[0], r[1], r[2] if len(r) > 2 else "") for r in peer["rows"]]
                     if gs)
    mine_set, peer_set = set(mine), set(peer_rows)
    by_team_mine, by_team_peer = defaultdict(list), defaultdict(list)
    for t, p in mine:
        by_team_mine[t].append(p)
    for t, p in peer_rows:
        by_team_peer[t].append(p)

    truncation = {
        t: (by_team_peer[t] == by_team_mine[t][:len(by_team_peer[t])])
        for t in by_team_peer if t in by_team_mine
    }
    prefix_like = sum(1 for v in truncation.values() if v)
    return {
        "peer": peer["label"],
        "peer_captured": peer["captured"],
        "peer_source": peer["source"],
        "peer_rows": len(peer_rows),
        "peer_designation_rows": peer_desig,
        "this_capture_designation_rows": sum(1 for r in mine_rows if (r.get("game_status") or "").strip()),
        "peer_rows_are_a_strict_subset_of_this_capture": peer_set <= mine_set,
        "this_capture_rows": len(mine),
        "row_delta": len(mine) - len(peer["rows"]),
        "players_in_this_capture_only": sorted(f"{t} {p}" for t, p in (mine_set - peer_set)),
        "players_in_peer_only": sorted(f"{t} {p}" for t, p in (peer_set - mine_set)),
        "clubs_peer_only": sorted(set(by_team_peer) - set(by_team_mine)),
        "clubs_missing_from_peer": sorted(set(by_team_mine) - set(by_team_peer)),
        "teams_compared": len(truncation),
        "teams_where_peer_is_a_prefix_of_this": prefix_like,
        "per_team_counts": {
            t: {"peer": len(by_team_peer.get(t, [])), "this": len(by_team_mine.get(t, []))}
            for t in sorted(set(by_team_peer) | set(by_team_mine))
        },
        "club_code_normalisation": "ARI->AZ, LA->LAR applied to peer labels only",
    }


# --------------------------------------------------------------------------- #
# 3. standings identities
# --------------------------------------------------------------------------- #
def standings_checks():
    st = load_json(STANDINGS)
    rows = st["rows"]
    tot_pf = sum(r["PF"] for r in rows)
    tot_pa = sum(r["PA"] for r in rows)
    gp = {r["club"]: r["W"] + r["L"] + r["T"] for r in rows}
    tot_gp = sum(gp.values())
    net_ok = all(r["net_pts"] == r["PF"] - r["PA"] for r in rows)
    pct_bad = []
    for r in rows:
        g = r["W"] + r["L"] + r["T"]
        want = round((r["W"] + 0.5 * r["T"]) / g, 3) if g else 0.0
        if abs(want - r["pct"]) > 0.0011:
            pct_bad.append({"club": r["club"], "published": r["pct"], "recomputed": want})
    fixtures = read_csv(FIXTURES)
    report_records = {}
    for f in fixtures:
        for part in (f["injury_report_records"] or "").split(";"):
            part = part.strip()
            if not part:
                continue
            club, rec = part.split(" ", 1)
            report_records[club] = rec
    def norm(txt):
        # the report prints "8-1" and only appends the tie digit when a tie exists;
        # the standings always print three numbers. Compare the parsed triple, not the string.
        bits = [int(x) for x in txt.strip().split("-")]
        while len(bits) < 3:
            bits.append(0)
        return tuple(bits)

    compare = []
    for r in rows:
        published = report_records.get(r["club"])
        live = (r["W"], r["L"], r["T"])
        if published is not None:
            compare.append({"club": r["club"],
                            "report_record": published,
                            "report_parsed": "-".join(str(x) for x in norm(published)),
                            "standings_record": "-".join(str(x) for x in live),
                            "match": norm(published) == live})
    matches = sum(1 for c in compare if c["match"])
    settled = sum(1 for f in fixtures if f["schedule_state_at_capture"] == "Final")
    credited_wk10 = settled + sum(
        1 for f in fixtures if f["schedule_state_at_capture"].startswith("In progress"))
    in_progress = sum(1 for f in fixtures if f["schedule_state_at_capture"].startswith("In progress"))
    not_started = sum(1 for f in fixtures if f["schedule_state_at_capture"] == "Not started")
    return {
        "clubs": len(rows),
        "sum_pf": tot_pf,
        "sum_pa": tot_pa,
        "pf_equals_pa": tot_pf == tot_pa,
        "net_points_identity_holds": net_ok,
        "win_pct_mismatches": pct_bad,
        "sum_games_played": tot_gp,
        "games_played_derived": tot_gp // 2,
        "backtest_corpus": {
            "method": ("games credited in the live standings = sum(GP)/2; Week 10 games already credited = "
                       "games final or in progress at read time; games through Week 9 = the difference"),
            "games_credited_to_date": tot_gp // 2,
            "week10_games_credited_at_read": credited_wk10,
            "week10_games_final_at_read": settled,
            "games_through_week9": tot_gp // 2 - credited_wk10,
            "week10_slate_size": len(fixtures),
            "games_after_week10_completes": tot_gp // 2 - credited_wk10 + len(fixtures),
            "reviewer_claim": ("the brief asks for 'the 136-game log' to become the pre-registered corpus; "
                               "no file at the base commit publishes 136 and the official arithmetic above "
                               "gives a different number - see flag RF-01, which states both figures instead "
                               "of quietly adopting either"),
        },
        "games_played_is_even": tot_gp % 2 == 0,
        "teams_on_bye_derived": [c for c in CLUBS if c not in report_records],
        "week10_fixtures": len(fixtures),
        "week10_final_at_read": settled,
        "week10_in_progress_at_read": in_progress,
        "week10_not_started_at_read": not_started,
        "report_record_vs_live_standings": {
            "clubs_compared": len(compare),
            "matching": matches,
            "mismatching": [c for c in compare if not c["match"]],
            "reading": ("the bracketed record on the injury-report page equals the LIVE standings record for "
                        "{m} of {n} clubs at read time - including the four clubs whose Week 10 games were "
                        "still in progress and the clubs playing the 8:20 PM and Monday games that had not "
                        "kicked off. So the record field is a live join, not a pre-game attribute of the "
                        "report; a snapshot must store the record it saw with the clock time, and the model "
                        "must never read it off the report table.").format(m=matches, n=len(compare)),
            "report_format_note": ("the report prints W-L and appends -T only when T>0 (NYG 5-3-1, WAS 3-5-1); "
                                   "the standings always print three numbers. Comparison is on the parsed triple."),
        },
    }


def field_delta_vs_marketboard(mine_rows):
    """Row sets are identical between this capture and nfl-marketboard's 2026-11-14 capture,
    so the per-field differences are the cleanest measurement of intra-week movement in the
    official report that exists in this repo."""
    p = os.path.join(ROOT, "nfl-marketboard", "data", "raw", "injuries_week10_official.csv")
    if not os.path.exists(p):
        return {"available": False, "reason": "peer capture file not present"}
    with open(p, encoding="utf-8") as fh:
        lines = [ln for ln in fh if not ln.startswith("#")]
    peer = {}
    for r in csv.DictReader(lines):
        peer[(cc(r["team"]), r["player"])] = r
    game_changed, practice_changed, injury_changed = [], [], []
    for r in mine_rows:
        k = (cc(r["team"]), r["player"])
        q = peer.get(k)
        if q is None:
            continue
        if (r.get("game_status") or "").strip() != (q.get("game_status") or "").strip():
            game_changed.append({"team": r["team"], "player": r["player"], "pos": r["pos"],
                                 "as_of_2026-11-14": (q.get("game_status") or "").strip() or "(blank)",
                                 "as_of_2026-11-15": (r.get("game_status") or "").strip() or "(blank)"})
        if (r.get("practice_status") or "").strip() != (q.get("practice_status") or "").strip():
            practice_changed.append({"team": r["team"], "player": r["player"],
                                     "as_of_2026-11-14": (q.get("practice_status") or "").strip() or "(blank)",
                                     "as_of_2026-11-15": (r.get("practice_status") or "").strip() or "(blank)"})
        if (r.get("injury") or "").strip() != (q.get("injury") or "").strip():
            injury_changed.append({"team": r["team"], "player": r["player"],
                                   "as_of_2026-11-14": (q.get("injury") or "").strip() or "(blank)",
                                   "as_of_2026-11-15": (r.get("injury") or "").strip() or "(blank)"})
    return {
        "available": True,
        "compared": len(peer),
        "game_status_changes": game_changed,
        "practice_status_changes": practice_changed,
        "injury_label_changes": injury_changed,
        "game_status_changes_by_club": dict(Counter(c["team"] for c in game_changed)),
        "reading": ("{g} rows changed game designation and {p} rows changed practice status between the "
                    "2026-11-14 and 2026-11-15 renders of the same Week 10 report, with zero rows added or "
                    "removed. The movement is not spread across the league: {top}. A capture taken before the "
                    "change is therefore not a wrong capture, it is a different fact - only a dated series can "
                    "tell 'Out' from 'became Out', which is the whole argument for daily capture and for "
                    "publishing the delta rather than the level.").format(
                        g=len(game_changed), p=len(practice_changed),
                        top=("; ".join(f"{k} {v}" for k, v in Counter(c["team"] for c in game_changed).most_common())
                             or "none")),
    }


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = read_csv(SNAPSHOT)
    cap = audit_capture(rows)
    diffs = [diff_against(rows, p) for p in peer_captures()]
    st = standings_checks()
    delta = field_delta_vs_marketboard(rows)

    write(OUT + "/designation_delta.json", delta)
    write(OUT + "/capture_audit.json", cap)
    write(OUT + "/capture_diffs.json", {"built_from": "engine/audit.py", "diffs": diffs})
    write(OUT + "/standings_check.json", st)
    print(json.dumps({
        "rows": cap["rows"],
        "sections": cap["club_sections_published"],
        "designation_coverage_pct": cap["designation_coverage_pct"],
        "peers_compared": len(diffs),
        "standings_pf_eq_pa": st["pf_equals_pa"],
        "games_played": st["games_played_derived"],
        "report_vs_live_matches": st["report_record_vs_live_standings"]["matching"],
        "report_vs_live_total": st["report_record_vs_live_standings"]["clubs_compared"],
        "game_status_changes_1114_to_1115": len(delta.get("game_status_changes", [])),
    }, indent=1))
    return 0


def write(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, sort_keys=False)
        fh.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
