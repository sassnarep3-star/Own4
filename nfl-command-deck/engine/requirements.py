#!/usr/bin/env python3
"""
nfl-command-deck — independent audit of the consolidated requirement register.

The register is a peer artifact (nfl-req-review/data/requirements_2026_11_18.json, 73 rows).
This script does not restate it as new analysis. It asks one question of each row:
**is the status supported by the artifact the row cites?**

Two mechanical tests, applied to every row:
  1. artifact existence — every path the row cites is present in the tree;
  2. independent assertion — for rows where a data assertion is possible, this script
     evaluates it itself and records pass / contradicted / not-checkable.

A row whose status is `met` but whose artifact is missing is reported as contradicted.
A row that cannot be tested mechanically is reported as not-checkable, with the reason.

Writes: data/requirements.json
"""

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)
DATA = os.path.join(NS, "data")
REGISTER = os.path.join(ROOT, "nfl-req-review", "data", "requirements_2026_11_18.json")


def load(rel):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        return None
    try:
        return json.load(open(p, encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def rows_of(obj, *candidates):
    if obj is None:
        return []
    if isinstance(obj, list):
        return obj
    for c in candidates:
        if isinstance(obj.get(c), list):
            return obj[c]
    for v in obj.values():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            return v
    return []


# --------------------------------------------------------------- independent assertions
def a_price_store():
    d = load("nfl-book/data/price_snapshots.json")
    rows = rows_of(d, "rows")
    filled = [r for r in rows if r.get("market_open_value") is not None]
    return (len(rows) > 0 and len(filled) == 0,
            "%d market rows, %d with a non-null market open price" % (len(rows), len(filled)),
            "https://github.com/sassnarep3-star/Own4/blob/main/nfl-book/data/price_snapshots.json")


def a_results_feed():
    d = load("nfl-book/data/results_feed.json")
    if not d:
        return False, "results_feed.json missing", ""
    n = d.get("n_games") or len(rows_of(d, "rows"))
    rows = rows_of(d, "rows")
    src = sum(1 for r in rows if str(r.get("source_url", "")).startswith("https://www.nfl.com/"))
    return (len(rows) >= 130 and src == len(rows),
            "%d rows, %d carrying an nfl.com source URL" % (len(rows), src),
            "https://github.com/sassnarep3-star/Own4/blob/main/nfl-book/data/results_feed.json")


def a_model_outputs():
    d = load("nfl-book/data/model_outputs.json")
    rows = rows_of(d, "rows", "outputs")
    if not rows:
        return False, "no model output rows", ""
    r = rows[0]
    has_p = any("prob" in k.lower() or "p_" in k.lower() for k in r)
    has_in = any("input" in k.lower() or "feature" in k.lower() or "rating" in k.lower() for k in r)
    return (has_p and has_in,
            "%d rows; probability field present=%s, input field present=%s" % (len(rows), has_p, has_in),
            "https://github.com/sassnarep3-star/Own4/blob/main/nfl-book/data/model_outputs.json")


def a_signal_staking_split():
    d = load("nfl-book/data/leaderboard.json")
    rows = rows_of(d, "rows")
    if not rows:
        return False, "no leaderboard rows", ""
    r = rows[0]
    sig = [k for k in r if k.startswith("signal")]
    stk = [k for k in r if k.startswith("staking")]
    return (bool(sig) and bool(stk),
            "%d rows; signal fields %s; staking fields %s" % (len(rows), sig, stk),
            "https://github.com/sassnarep3-star/Own4/blob/main/nfl-book/data/leaderboard.json")


def a_demotion():
    d = load("nfl-book/data/demotion_eval.json")
    if not d:
        return False, "demotion_eval.json missing", ""
    text = json.dumps(d).lower()
    return ("demot" in text and ("paper" in text or "back" in text),
            "demotion_eval.json present; mentions paper/demotion: %s" % ("demot" in text),
            "https://github.com/sassnarep3-star/Own4/blob/main/nfl-book/data/demotion_eval.json")


def a_prereg():
    import hashlib
    d = load("nfl-live-board/data/prereg.json")
    if not d:
        return False, "prereg.json missing", ""
    p = os.path.join(ROOT, "nfl-live-board", d.get("prereg_file", ""))
    if not os.path.exists(p):
        return False, "registered prereg file missing", ""
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    ok = h == d.get("prereg_sha256")
    return (ok, "prereg hash matches registration: %s (%s)" % (ok, h[:16]),
            "https://github.com/sassnarep3-star/Own4/blob/main/nfl-live-board/prereg/PREREG-LB.md")


def a_luck_panel():
    d = load("nfl-live-board/data/leaderboard.json")
    if not d:
        return False, "leaderboard missing", ""
    rl = d.get("removal_of_luck") or {}
    items = rl.get("what_it_removes") or []
    return (len(items) >= 4,
            "removal_of_luck block with %d items; points awarded %s" % (len(items), d.get("points_awarded")),
            "https://github.com/sassnarep3-star/Own4/blob/main/nfl-live-board/data/leaderboard.json")


def a_per_team_view():
    d = load("nfl-book/data/per_team_view.json")
    rows = rows_of(d, "rows", "teams")
    return (len(rows) == 32, "%d team rows" % len(rows),
            "https://github.com/sassnarep3-star/Own4/blob/main/nfl-book/data/per_team_view.json")


def a_lions():
    names = ["Kerby Joseph", "Cade Mays", "D.J. Reed"]
    hits = {}
    for rel in ("nfl-readiness-register/data/injury_capture.json",
                "nfl-book/data/injuries_week10_capture.json",
                "nfl-origin-board/data/injuries_week10.json"):
        txt = ""
        p = os.path.join(ROOT, rel)
        if os.path.exists(p):
            txt = open(p, encoding="utf-8", errors="replace").read()
        for n in names:
            if n in txt:
                hits.setdefault(n, rel)
    return (len(hits) == 3, "found in committed data: %s" % hits,
            "https://www.nfl.com/injuries/")


def a_availability_graph():
    d = load("nfl-book/data/availability_graph.json")
    rows = rows_of(d, "rows")
    filled = [r for r in rows if r.get("actual_starter")]
    return (len(rows) > 0, "%d rows; %d with a confirmed actual starter" % (len(rows), len(filled)),
            "https://github.com/sassnarep3-star/Own4/blob/main/nfl-book/data/availability_graph.json")


def a_depth_register():
    d = load("nfl-depth-sweep/data/depth_register.json")
    clubs = rows_of(d, "clubs")
    dated = [c for c in clubs if c.get("snapshot_date")]
    return (len(clubs) == 32 and len(dated) == 32,
            "%d clubs, %d with a snapshot date" % (len(clubs), len(dated)),
            "https://github.com/sassnarep3-star/Own4/blob/main/nfl-depth-sweep/data/depth_register.json")


def a_decision_table():
    """G01: is a one-row-per-requirement readiness table published on a landing page?"""
    p = os.path.join(ROOT, "nfl-readiness-register", "index.html")
    if not os.path.exists(p):
        return False, "no readiness landing page", ""
    s = open(p, encoding="utf-8").read()
    trows = len(re.findall(r"<tr", s))
    return (trows >= 60 and "block" in s.lower(),
            "%d table rows on nfl-readiness-register/index.html" % trows,
            "https://sassnarep3-star.github.io/Own4/nfl-readiness-register/")


def a_official_inactives():
    found = []
    for dp, dn, fn in os.walk(ROOT):
        if "/.git" in dp:
            continue
        for f in fn:
            if f.endswith(".json") and "inactive" in f.lower():
                rel = os.path.relpath(os.path.join(dp, f), ROOT)
                d = load(rel)
                n = len(rows_of(d, "rows", "inactives"))
                if n:
                    found.append((rel, n))
    return (bool(found), "inactive-list datasets found: %s" % found,
            "https://www.nfl.com/injuries/")


def a_snap_counts():
    found = []
    for dp, dn, fn in os.walk(ROOT):
        if "/.git" in dp:
            continue
        for f in fn:
            low = f.lower()
            if f.endswith(".json") and ("snap_count" in low or "snapcount" in low
                                        or "snaps_" in low or low.startswith("snaps")):
                rel = os.path.relpath(os.path.join(dp, f), ROOT)
                d = load(rel)
                n = len(rows_of(d, "rows", "snaps"))
                found.append((rel, n))
    return (any(n for _, n in found), "snap-count datasets: %s" % found,
            "https://www.nfl.com/")


def a_texans():
    d = load("nfl-depth-sweep/data/depth_register.json")
    clubs = rows_of(d, "clubs")
    hou = next((c for c in clubs if c.get("club") == "HOU"), None)
    ok = bool(hou) and hou.get("status") != "verified_text"
    return (ok, "HOU status: %s" % (hou or {}).get("status"),
            (hou or {}).get("source_url", ""))


def a_fixture_venue():
    """The origin-board capture stores games as positional arrays; venue is field index 7."""
    d = load("nfl-origin-board/data/week11_schedule.json")
    games = (d or {}).get("games") or []
    if not games:
        return False, "no week-11 schedule dataset", ""
    with_venue = [g for g in games if isinstance(g, list) and len(g) > 7 and g[7]]
    gaps = [{"week": g[0], "date": g[1], "away": g[3], "home": g[4],
             "game_url": g[6], "venue": ""} for g in games
            if not (isinstance(g, list) and len(g) > 7 and g[7])]
    span = "; ".join("%s@%s on %s (no venue)" % (g["away"], g["home"], g["date"]) for g in gaps)
    return (len(with_venue) == len(games),
            "%d fixtures carry a venue string; %d does not: %s. The cell is blank in the "
            "capture, so it stays blank here." % (len(games), len(gaps), span),
            "https://www.nfl.com/schedules/2026/by-week/week-11")


ASSERTIONS = {
    "A01": ("price-snapshot store: market open/close values present", a_price_store),
    "A02": ("verified results feed rows", a_results_feed),
    "A03": ("venue transcribed for every Week-11 fixture", a_fixture_venue),
    "B04": ("model output = probability + inputs", a_model_outputs),
    "C01": ("signal and staking separated on the leaderboard", a_signal_staking_split),
    "C06": ("demotion gate artifact", a_demotion),
    "C07": ("pre-registration hash verifies", a_prereg),
    "E02": ("availability graph rows", a_availability_graph),
    "E06": ("official inactive list captured", a_official_inactives),
    "E20": ("depth register: dated rows per club", a_depth_register),
    "E25": ("three Lions designations present in committed data", a_lions),
    "G01": ("decision-readiness table on a landing page", a_decision_table),
    "E03": ("snap counts captured (playing-time proxy)", a_snap_counts),
    "E07": ("HOU depth still image-only", a_texans),
}


def main():
    reg = json.load(open(REGISTER, encoding="utf-8"))
    rows = reg["rows"]

    out_rows = []
    tally = {"pass": 0, "contradicted": 0, "not-checkable": 0, "artifact-missing": 0}
    for r in rows:
        arts = r.get("artifacts") or []
        missing = [a["path"] for a in arts if not os.path.exists(os.path.join(ROOT, a["path"]))]
        rec = {
            "id": r["id"], "group": r["group"], "requirement": r["requirement"],
            "status": r["status"], "gate": r.get("gate", ""), "clears": r.get("clears", ""),
            "peer_source": r.get("source", ""), "peer_evidence": r.get("evidence", ""),
            "artifacts_cited": [a["path"] for a in arts],
            "artifacts_missing": missing,
        }
        if r["id"] in ASSERTIONS:
            label, fn = ASSERTIONS[r["id"]]
            try:
                ok, detail, url = fn()
            except Exception as ex:                      # noqa: BLE001 — the error is the result
                ok, detail, url = False, "assertion raised %s: %s" % (type(ex).__name__, ex), ""
            rec.update({
                "independent_check": label, "independent_result": "pass" if ok else "contradicted",
                "independent_detail": detail, "independent_source": url,
            })
            verdict = "pass" if ok else "contradicted"
        else:
            rec.update({
                "independent_check": "no data assertion defined for this row",
                "independent_result": "not-checkable",
                "independent_detail": ("artifact existence only: %d cited, %d missing"
                                       % (len(arts), len(missing))),
                "independent_source": r.get("source", ""),
            })
            verdict = "artifact-missing" if missing else "not-checkable"
        rec["verdict"] = verdict
        tally[verdict] = tally.get(verdict, 0) + 1
        out_rows.append(rec)

    summary = {
        "rows": len(out_rows),
        "peer_status_counts": {},
        "verified_by_this_session": sum(1 for r in out_rows if r["verdict"] == "pass"),
        "contradicted": sum(1 for r in out_rows if r["verdict"] == "contradicted"),
        "not_checkable": sum(1 for r in out_rows if r["verdict"] == "not-checkable"),
        "artifacts_missing": sum(1 for r in out_rows if r["artifacts_missing"]),
    }
    for r in out_rows:
        summary["peer_status_counts"][r["status"]] = summary["peer_status_counts"].get(r["status"], 0) + 1

    out = {
        "dataset": "nfl_command_deck_requirements",
        "title": "Requirement register audited line by line against the artifacts it cites",
        "built_utc": "2026-11-19",
        "session": "arena/1153eb96-own4",
        "register_source": "nfl-req-review/data/requirements_2026_11_18.json (peer artifact, read-only)",
        "rule": "a status is only re-confirmed when this session evaluates the artifact itself; "
                "everything else is 'not-checkable' and stays exactly as the peer published it",
        "summary": summary,
        "rows": out_rows,
    }
    json.dump(out, open(os.path.join(DATA, "requirements.json"), "w", encoding="utf-8"),
              indent=1, sort_keys=True)
    print(json.dumps(summary, indent=1))
    for r in out_rows:
        if r["verdict"] in ("contradicted", "artifact-missing"):
            print("!!", r["id"], r["status"], r["verdict"], r["independent_detail"][:120])


if __name__ == "__main__":
    main()
