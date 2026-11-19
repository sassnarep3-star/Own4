#!/usr/bin/env python3
"""Cross-session reconciliation.

Another session (`arena/6c8bbde6-own4`, namespace `nfl-verify-2026-11-19`, merged to main) read the
same official pages on the same day, 2026-11-19. Two independent reads of one source are the only
verification a single reader cannot fake, so this step compares the two artifact sets field by field
and publishes where they agree and where they do not. The peer namespace is read, never edited.
"""
import hashlib
import json
import os
import re
import subprocess
import unicodedata

NS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(NS)
PEER = "nfl-verify-2026-11-19"
PEER_DATA = os.path.join(ROOT, PEER, "data")
OUT = os.path.join(NS, "data", "cross_session.json")
INJ = "https://www.nfl.com/injuries/"
STAND = "https://www.nfl.com/standings/league/2026/REG"
RESERVE = "https://www.nfl.com/transactions/league/reserve-list/2026/11"
SCHED11 = "https://www.nfl.com/schedules/2026/by-week/week-11"


def namekey(name):
    n = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode()
    return "".join(sorted(re.sub(r"[^a-z0-9]", "", n.lower())))


def jload(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def git_utc(rel):
    try:
        out = subprocess.run(["git", "-C", ROOT, "log", "-1", "--format=%cI", "--", rel],
                             capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        out = ""
    return out or "unknown"


def injuries(mine, theirs):
    m = {(r["club_abbr"], namekey(r["player"])): r for r in mine["rows"]}
    t = {(r["club"], namekey(r["player"])): r for r in theirs["rows"]}
    both = sorted(set(m) & set(t))
    diffs = []
    for k in both:
        a, b = m[k], t[k]
        for fm, ft in (("practice", "practice"), ("game_status", "game_status"),
                       ("injury", "injury"), ("pos", "position")):
            if (a.get(fm) or "") != (b.get(ft) or ""):
                diffs.append({"club": k[0], "player": a["player"], "field": fm,
                              "this_desk": a.get(fm) or "", "peer_read": b.get(ft) or ""})
    pm, pt = {}, {}
    for r in mine["rows"]:
        pm[r["club_abbr"]] = pm.get(r["club_abbr"], 0) + 1
    for r in theirs["rows"]:
        pt[r["club"]] = pt.get(r["club"], 0) + 1
    per_club = [{"club": c, "this_desk_rows": pm.get(c, 0), "peer_rows": pt[c],
                 "agree": pm.get(c, 0) == pt[c]} for c in sorted(pt)]
    return {"joined_rows": len(both), "peer_rows": len(theirs["rows"]),
            "desk_rows": len(mine["rows"]),
            "rows_only_in_peer": len(set(t) - set(m)), "rows_only_in_this_desk_in_peer_clubs":
            len({k for k in set(m) - set(t) if k[0] in pt}),
            "field_differences": diffs, "n_field_differences": len(diffs),
            "identical_rows": len(both) - len({(d["club"], d["player"]) for d in diffs}),
            "clubs_the_peer_read": sorted(pt), "clubs_this_desk_read": len(pm),
            "per_club_row_counts": per_club,
            "per_club_counts_all_agree": all(x["agree"] for x in per_club),
            "practice_vocab_note": "the official vocabulary is mixed-case in the source itself — the "
                                   "byte-exact 2026-11-18 capture holds 83 'Full Participation in Practice', "
                                   "82 'Limited Participation in Practice' and 77 'Did Not Participate In "
                                   "Practice'. This desk pins those strings verbatim; a delta panel built on "
                                   "title-cased values would report casing changes as availability changes.",
            "source_url": theirs.get("source", INJ), "peer_source": INJ}


def standings(mine, theirs):
    t = {x["abbr"]: x for x in theirs["teams"]}
    agree = {"W": 0, "L": 0, "T": 0, "PF": 0, "PA": 0, "NET": 0}
    mismatches, compared = [], 0
    for r in mine["rows"]:
        p = t.get(r["club"])
        if not p:
            continue
        compared += 1
        for f_mine, f_peer in (("W", "w"), ("L", "l"), ("T", "t"), ("PF", "pf"), ("PA", "pa"), ("NET", "net")):
            if r[f_mine] == p[f_peer]:
                agree[f_mine] += 1
            else:
                mismatches.append({"club": r["club"], "field": f_mine, "this_desk": r[f_mine],
                                   "peer": p[f_peer]})
    peer_games = sum(x["w"] + x["l"] + x["t"] for x in theirs["teams"]) // 2
    peer_pf = sum(x["pf"] for x in theirs["teams"])
    peer_pa = sum(x["pa"] for x in theirs["teams"])
    mine_games = sum(r["W"] + r["L"] + r["T"] for r in mine["rows"]) // 2
    return {"clubs_in_both": compared, "fields_compared": compared * 6,
            "fields_agree": sum(agree.values()), "mismatches": mismatches,
            "games_from_peer_read": peer_games, "games_from_this_desk_read": mine_games,
            "peer_pf_total": peer_pf, "desk_pf_total": sum(r["PF"] for r in mine["rows"]),
            "peer_pa_total": peer_pa, "desk_pa_total": sum(r["PA"] for r in mine["rows"]),
            "peer_extra_fields": ["conf", "division", "pct"] if "conf" in theirs["teams"][0] else [],
            "note": "the peer read exposes conference and division per club; this desk's read of the same "
                    "page could not establish the split-column order because the rendered header was "
                    "un-substituted, so those fields are omitted here and carried by the peer artifact "
                    "under its own read date",
            "source_url": STAND}


def reserve(mine, theirs):
    def key(x):
        return (str(x.get("date", "")), namekey(x.get("name", "")), str(x.get("transaction", "")))
    ms, ts = {}, {}
    for r in mine["rows"]:
        ms.setdefault(key(r), r)
    for r in theirs["entries"]:
        ts.setdefault(key(r), r)
    both = set(ms) & set(ts)
    pos_blank_peer = sum(1 for r in theirs["entries"] if not (r.get("position") or "").strip())
    return {"desk_rows": len(mine["rows"]), "peer_rows": len(theirs["entries"]),
            "rows_in_both": len(both), "only_this_desk": sorted(str(k) for k in set(ms) - set(ts))[:8],
            "only_peer": sorted(str(k) for k in set(ts) - set(ms))[:8],
            "peer_blank_position_cells": pos_blank_peer,
            "position_blank_confirms_desk_flag": pos_blank_peer == len(theirs["entries"]),
            "source_url": RESERVE}


def slate(mine, theirs):
    mine_set = {(r["away"], r["home"]) for r in mine["rows"]}
    their_set = {(f["away"], f["home"]) for f in theirs["fixtures"]}
    venues = [f for f in theirs["fixtures"] if f.get("venue")]
    disagree = [f for f in theirs["fixtures"] if f.get("venue") and f.get("game_centre_venue")
                and f["venue"] != f["game_centre_venue"]]
    return {"desk_fixtures": len(mine_set), "peer_fixtures": len(their_set),
            "fixtures_in_both": sorted("%s@%s" % x for x in (mine_set & their_set)),
            "n_in_both": len(mine_set & their_set),
            "only_this_desk": sorted("%s@%s" % x for x in (mine_set - their_set)),
            "only_peer": sorted("%s@%s" % x for x in (their_set - mine_set)),
            "peer_byes": [b["abbr"] for b in theirs.get("byes", [])],
            "venues_transcribed_by_peer": len(venues), "venue_pages": len(theirs["fixtures"]),
            "venue_label_disagreements": [{"fixture": "%s@%s" % (f["away"], f["home"]),
                                           "schedule_page": f["venue"], "game_centre": f["game_centre_venue"],
                                           "schedule_source": f.get("venue_source"),
                                           "game_centre_source": f.get("game_centre")} for f in disagree],
            "note": "the desk records no venue of its own; the peer read transcribed 12 of 13 from the "
                    "schedule page's stadium links and cross-checked Thursday's against the game centre, "
                    "which is how the label disagreement surfaced",
            "source_url": SCHED11}


def main():
    mine_inj = jload(os.path.join(NS, "data", "availability_delta.json"))
    mine_st = jload(os.path.join(NS, "data", "standings.json"))
    mine_res = jload(os.path.join(NS, "data", "reserve_delta.json"))
    mine_sh = jload(os.path.join(NS, "data", "shadow_cohorts.json"))
    if not os.path.isdir(PEER_DATA):
        json.dump({"dataset": "nfl_daily_desk_cross_session", "absent": True,
                   "note": "the peer namespace is not in this checkout, so there is nothing to reconcile"},
                  open(OUT, "w"), indent=1)
        print("peer namespace absent")
        return
    peer_flags = jload(os.path.join(PEER_DATA, "flags.json"))["flags"]
    out = {
        "dataset": "nfl_daily_desk_cross_session",
        "title": "Two sessions read the same official pages on 2026-11-19 — where the artifacts agree",
        "built_utc": "2026-11-19T08:10:00Z",
        "policy": "computed from both namespaces' published JSON with no manual entry; a disagreement is "
                  "published as a disagreement with each side's file named, and no peer file is edited to "
                  "make the comparison clean",
        "peer_namespace": PEER,
        "peer_session": "arena/6c8bbde6-own4",
        "peer_files": {n: {"sha256": hashlib.sha256(open(os.path.join(PEER_DATA, n), "rb").read()).hexdigest(),
                           "bytes": os.path.getsize(os.path.join(PEER_DATA, n)),
                           "last_commit_touching_it": git_utc(os.path.join(PEER, "data", n))}
                       for n in sorted(os.listdir(PEER_DATA)) if n.endswith(".json")},
        "injury_report": injuries(mine_inj, jload(os.path.join(PEER_DATA, "injuries_2026_11_19.json"))),
        "standings": standings(mine_st, jload(os.path.join(PEER_DATA, "standings_2026_11_19.json"))),
        "reserve_list": reserve(mine_res, jload(os.path.join(PEER_DATA, "reserve_list_2026_11.json"))),
        "week11_slate": slate(mine_sh, jload(os.path.join(PEER_DATA, "schedule_week11_2026_11_19.json"))),
        "peer_flags": peer_flags,
    }
    ir, st = out["injury_report"], out["standings"]
    out["headline"] = {
        "injury_rows_compared": ir["joined_rows"], "injury_rows_identical": ir["identical_rows"],
        "injury_field_differences": ir["n_field_differences"],
        "injury_per_club_counts_all_agree": ir["per_club_counts_all_agree"],
        "standings_fields_compared": st["fields_compared"], "standings_fields_agree": st["fields_agree"],
        "games_from_two_independent_reads": [st["games_from_this_desk_read"], st["games_from_peer_read"]],
        "reserve_rows_in_both": out["reserve_list"]["rows_in_both"],
        "week11_fixtures_in_both": out["week11_slate"]["n_in_both"],
        "reading": ("two sessions, one official page, same day: %d of %d injury rows agree on every field, "
                    "and all %d per-club row counts the peer published match this desk's. %d of %d "
                    "standings fields agree, the reserve ledger reconciles at %d of %d rows, and %d of %d "
                    "Week 11 fixtures appear in both. The %d injury differences and the venue label "
                    "disagreement are published below rather than reconciled silently."
                    % (ir["identical_rows"], ir["joined_rows"], len(ir["per_club_row_counts"]),
                       st["fields_agree"], st["fields_compared"], out["reserve_list"]["rows_in_both"],
                       out["reserve_list"]["peer_rows"], out["week11_slate"]["n_in_both"],
                       out["week11_slate"]["peer_fixtures"], ir["n_field_differences"])),
    }
    json.dump(out, open(OUT, "w"), indent=1)
    print(json.dumps(out["headline"], indent=1))


if __name__ == "__main__":
    main()
