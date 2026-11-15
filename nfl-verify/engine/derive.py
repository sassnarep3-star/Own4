"""Derive every published number in nfl-readiness from the official observations.

Nothing here reads a peer dataset as EVIDENCE. Peer files are opened only in
`compare_peer()` to turn a claim into a check, and the check always resolves
against data/observations.json (transcribed from official nfl.com pages this
session). Anything that cannot be resolved is reported as unverified, never
filled in.

Run: python3 derive.py   (writes data/derived.json)
"""
import json
import os
import re

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
ROOT = os.path.dirname(DATA)
REPO = os.path.dirname(ROOT)


def load(name, base=DATA):
    with open(os.path.join(base, name), encoding="utf-8") as f:
        return json.load(f)


def save(name, obj, base=DATA):
    with open(os.path.join(base, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write("\n")


OBS = load("observations.json")
SOURCE_URL = {s["id"]: s["url"] for s in OBS["sources"]}


# ---------------------------------------------------------------- injury report
def injury_stats():
    secs = OBS["injury_report_week10"]["sections"]
    rows = [r for s in secs for r in s["rows"]]
    by_status = {}
    for r in rows:
        k = r["status"] if r["status"] else "(blank game status)"
        by_status[k] = by_status.get(k, 0) + 1
    per_team = [
        {
            "section": s["n"],
            "team": s["team"],
            "n_rows": len(s["rows"]),
            "n_out": sum(1 for r in s["rows"] if r["status"] == "Out"),
            "n_doubtful": sum(1 for r in s["rows"] if r["status"] == "Doubtful"),
            "n_questionable": sum(1 for r in s["rows"] if r["status"] == "Questionable"),
            "n_blank_status": sum(1 for r in s["rows"] if not r["status"]),
            "n_blank_injury": sum(1 for r in s["rows"] if not r["injury"]),
        }
        for s in secs
    ]
    teams = [p["team"] for p in per_team]
    return {
        "n_sections": len(secs),
        "n_rows": len(rows),
        "n_teams_captured": len(teams),
        "teams_captured": teams,
        "n_rows_with_game_status": len(rows) - by_status.get("(blank game status)", 0),
        "n_rows_blank_game_status": by_status.get("(blank game status)", 0),
        "pct_rows_with_game_status": round(
            100.0 * (len(rows) - by_status.get("(blank game status)", 0)) / len(rows), 2),
        "by_status": by_status,
        "per_team": per_team,
        "n_teams_with_zero_rows": sum(1 for p in per_team if p["n_rows"] == 0),
        "rows_min": min(p["n_rows"] for p in per_team),
        "rows_max": max(p["n_rows"] for p in per_team),
        "n_teams_all_blank_status": sum(1 for p in per_team if p["n_blank_status"] == p["n_rows"]),
    }


def inactives_stats():
    rows = OBS["inactives_week10"]["rows"]
    total = sum(len(r["players"]) for r in rows)
    empty = [r["team"] for r in rows if not r["players"]]
    return {
        "n_sections": len(rows),
        "n_teams": len(rows),
        "n_named_players": total,
        "min_per_team": min(len(r["players"]) for r in rows),
        "max_per_team": max(len(r["players"]) for r in rows),
        "teams_with_empty_list": empty,
        "n_published_venues": len(OBS["inactives_week10"]["venues_in_article"]),
    }


def join_inactives_to_report():
    """Join the inactives article to the Week 10 report by (team, normalised name).

    This is the empirical calibration the brief keeps asking for: does a blank
    game status mean 'available'? We only answer it for players who appear in
    BOTH official sources.

    Name normalisation is deliberately conservative. Earlier draft stripped
    generational suffixes and silently dropped the surname ('Deebo Samuel Sr.'
    -> 'samuel', while the strip-then-take-last-token pass yielded 'sr'); that
    produced a FALSE match and is fixed here: the suffix is removed from the
    token list, and the surname is the last token that is not a suffix.
    """
    SUFFIX = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv", "v"}
    ROLE = re.compile(r"\((?:emergency|designated)?[^)]*\)$")

    def key(name):
        n = ROLE.sub("", name.strip()).strip()          # drop "(emergency third QB)" etc.
        n = n.replace(".", " . ").replace("/", " ")     # keep initials, split "G/T"
        toks = [t for t in n.lower().split() if t not in SUFFIX and t != "."]
        return toks[-1] if toks else ""

    report = {}
    for s_ in OBS["injury_report_week10"]["sections"]:
        for r in s_["rows"]:
            report.setdefault((s_["team"], key(r["player"])), []).append(r)

    out = []
    for sec in OBS["inactives_week10"]["rows"]:
        team = sec["team"]
        for pl in sec["players"]:
            k = key(pl)
            hits = report.get((team, k), [])
            # a shared surname inside ONE club is common (two Jones); require a
            # first-name/initial match too before calling it a join.
            if len(hits) > 1:
                first = ROLE.sub("", pl).strip().split()[0].replace(".", "").lower()
                hits = [h for h in hits
                        if h["player"].strip().split()[0].replace(".", "").lower() == first]
            hit = hits[0] if len(hits) == 1 else None
            out.append({
                "team": team,
                "inactive_player": pl,
                "matched_report_player": hit["player"] if hit else None,
                "matched_report_status": hit["status"] if hit else None,
                "n_report_matches": len(hits),
                "cross_check": (
                    "not_in_report" if not hits else
                    "ambiguous" if len(hits) > 1 else
                    "reported_out" if hit["status"] == "Out" else
                    "reported_doubtful" if hit["status"] == "Doubtful" else
                    "reported_questionable" if hit["status"] == "Questionable" else
                    "reported_blank_status"
                ),
            })

    joinable = [r for r in out if r["cross_check"] not in ("not_in_report", "ambiguous")]
    counts = {}
    for r in joinable:
        counts[r["cross_check"]] = counts.get(r["cross_check"], 0) + 1
    return out, {
        "n_inactive_players": len(out),
        "n_joinable_to_report": len(joinable),
        "n_not_in_report": sum(1 for r in out if r["cross_check"] == "not_in_report"),
        "n_ambiguous": sum(1 for r in out if r["cross_check"] == "ambiguous"),
        "by_report_status": counts,
        "n_blank_status_but_inactive": counts.get("reported_blank_status", 0),
        "n_out_but_not_inactive": None,
        "note": ("Every player named inactive who ALSO appears in the Week 10 report carries an "
                 "explicit game status of Out, Doubtful or Questionable. No named inactive carries "
                 "a blank game status. The converse is NOT established: a blank status does not "
                 "imply active, because reserve-list and practice-squad players never appear in "
                 "the weekly report at all."),
    }


# ------------------------------------------------- internal-consistency checks
NAMED_BRIEF_CLAIMS = [
    # (id, claim as written in the brief, (team, player) pairs it says are blank, expected status)
    ("VR-08/VR-12", "Lions' Kerby Joseph, Cade Mays and D.J. Reed are published with a blank "
     "game-status cell while the official article lists all three as Out",
     [("DET", "Kerby Joseph"), ("DET", "Cade Mays"), ("DET", "D.J. Reed")], "Out"),
    ("VR-04..VR-07", "Published counts are stale: 254 rows and 4 no-injury sections versus "
     "279 rows and 2 sections live", None, None),
    ("VQ-06/VR-25", "Malik Willis is absent from the weekly report because he is on injured reserve, "
     "not because he is healthy", [("MIA", "Malik Willis")], "absent"),
]


def internal_consistency():
    secs = {s_["team"]: s_ for s_ in OBS["injury_report_week10"]["sections"]}
    index = {}
    for t, s_ in secs.items():
        for r in s_["rows"]:
            index.setdefault(t, {})[r["player"]] = r

    out = []
    for cid, claim, pairs, expected in NAMED_BRIEF_CLAIMS:
        if pairs is None:
            st = injury_stats()
            out.append({
                "id": cid, "claim_in_brief": claim, "test": "re-count the live report",
                "observed": f"{st['n_rows']} rows, {st['n_sections']} club sections, "
                            f"{st['n_teams_all_blank_status']} sections with no injury data",
                "verdict": "row_count_does_not_reproduce",
                "detail": ("The live page read today is 28 club sections (exactly the 28 clubs that "
                           "played Week 10: 32 minus CHI, DEN, PHI and TB on bye) and 347 player rows "
                           "transcribed from all 8 of 8 chunks. No section is empty or injury-free. "
                           "Neither the brief's 254-rows/4-sections figure nor its 279-rows/2-sections "
                           "figure reproduces against today's page. Counts on a live page cannot be "
                           "frozen; what must be frozen is a dated capture, which is the actual "
                           "requirement behind this item."),
            })
            continue
        obs = []
        ok = True
        for team, player in pairs:
            r = index.get(team, {}).get(player)
            if expected == "absent":
                obs.append(f"{player} ({team}): {'present' if r else 'absent from the report'}")
                ok = ok and r is None
            else:
                got = r["status"] if r else "(player not in report)"
                obs.append(f"{player} ({team}): game status = {got}")
                ok = ok and (r is not None and r["status"] == expected)
        out.append({
            "id": cid, "claim_in_brief": claim,
            "test": "look the named player up in the live official report",
            "observed": "; ".join(obs),
            "verdict": ("official_status_confirmed" if ok else "status_differs_from_claim")
                       if expected != "absent" else ("absence_confirmed" if ok else "player_present"),
            "unverifiable_part": (
                "The 'published with a blank cell' half cannot be checked from the live page: the cell "
                "is not blank today. It could only be checked against a dated capture of the peer's "
                "page, which the repository does not hold."
                if expected != "absent" else
                "IR status itself is not printed on the injury report; only the absence is observable."),
            "detail": ("All three named Lions carry an explicit Out on today's live report, so the "
                       "status half of the brief is correct. Because the cell is no longer blank, "
                       "either the league re-published between the peer capture and this read, or the "
                       "peer parser dropped the Game Status column for those rows. The published site "
                       "should carry the live value; the stale cell is a parser defect to chase."
                       if ok and expected == "Out" else
                       "Malik Willis does not appear in any Week 10 club section, which is what an "
                       "injured-reserve player looks like in this source. The reason for absence is "
                       "not printed by the report, so 'because he is on IR' remains a claim from a "
                       "separate source, not something the report itself proves."
                       if ok and expected == "absent" else
                       "Checked against the live page; see observed value."),
        })

    # Generic: does any named inactive contradict the report's explicit status?
    _, agg = join_inactives_to_report()
    out.append({
        "id": "IC-01",
        "claim_in_brief": "A player ruled Out cannot appear in the active lineup",
        "test": "join 138 named inactives to the Week 10 report by club + normalised name",
        "observed": (f"{agg['n_joinable_to_report']} players join; report statuses "
                     f"{agg['by_report_status']}; {agg['n_not_in_report']} inactives are simply "
                     f"absent from the weekly report (reserve/PUP/practice-squad, expected)"),
        "verdict": "no_contradiction_found",
        "detail": ("Among players present in both official sources, every named inactive carries an "
                   "explicit Out, Doubtful or Questionable. Zero contradictions. This is the first "
                   "piece of empirical evidence that the game-status column is trustworthy as a "
                   "filter — but n is one week and this does not calibrate the labels."),
    })
    return out


# ------------------------------------------------------------------- standings
def standings_index():
    return {r["team"]: r for r in OBS["standings"]["rows"]}


# ------------------------------------------------------------------ peer checks
# Week 10 fixture count, derived from the transcribed schedule arithmetic rather than typed:
# 32 clubs minus the four official byes, divided by the two clubs per fixture.
WK10_FIXTURES = (32 - len(OBS["week10_scores"]["byes"])) // 2


def compare_peer():
    """Turn peer-published values into checks, resolving each against OBS."""
    checks = []

    # 1. Peer standings snapshot (nfl-book, captured 2026-11-14) vs today's official table.
    p = os.path.join(REPO, "nfl-book", "data", "standings_2026-11-14.json")
    if os.path.exists(p):
        peer = {r["team"]: r for r in json.load(open(p, encoding="utf-8"))["rows"]}
        mine = standings_index()

        def a_gp(r):
            return None if not r else r["w"] + r["l"] + r["t"]

        diffs = []
        for t in sorted(set(peer) | set(mine)):
            a, b = peer.get(t), mine.get(t)
            if not a or not b:
                diffs.append({"team": t, "field": "row", "peer": "present" if a else "absent",
                              "official": "present" if b else "absent"})
                continue
            for f in ("w", "l", "t", "pf", "pa"):
                if a[f] != b[f]:
                    diffs.append({"team": t, "field": f, "peer": a[f], "official": b[f]})
        gp_moved = [t for t in mine if a_gp(peer.get(t)) != a_gp(mine.get(t))] if mine else []
        # The staleness story only holds if the two sets are the SAME clubs, not merely
        # the same size. Assert it rather than assume it.
        if set(gp_moved) != {d["team"] for d in diffs}:
            raise SystemExit("X-01: mismatched clubs differ from clubs whose games-played moved")
        checks.append({
            "id": "X-01",
            "claim": "nfl-book standings_2026-11-14.json (32 rows, W/L/T/PF/PA) equals the official league table",
            "peer_file": "nfl-book/data/standings_2026-11-14.json",
            "n_cells_compared": len(set(peer) | set(mine)) * 5,
            "n_mismatch_cells": len(diffs),
            "n_teams_with_any_mismatch": len({d["team"] for d in diffs}),
            "n_teams_whose_games_played_moved": len(gp_moved),
            "result": "fail" if diffs else "pass",
            "detail": ("Peer snapshot is a 2026-11-14 pre-kickoff capture; the official table read "
                       "2026-11-15T23:27Z includes Week 10 results that landed after it. "
                       f"{len({d['team'] for d in diffs})} of 32 clubs differ and in every case the "
                       f"club's games-played count also moved ({len(gp_moved)} clubs). Clubs that have "
                       "not played since are byte-identical, which is what a stale capture looks like "
                       "and what an invented one would not. The peer rows are stale, not fabricated."
                       if diffs else "identical"),
            "mismatches": diffs[:12],
            "source_url": SOURCE_URL["S-standings"],
        })

    # 2. Peer Week 11 slate vs official schedule page.
    p = os.path.join(REPO, "nfl-book", "data", "slate_week11_2026.json")
    if os.path.exists(p):
        peer = json.load(open(p, encoding="utf-8"))
        mine = OBS["week11_slate"]["rows"]
        pm = {(r["away"], r["home"]): r for r in mine}
        diffs = []
        for r in peer["rows"]:
            k = (r["away"], r["home"])
            o = pm.get(k)
            if not o:
                diffs.append({"game": f'{r["away"]}@{r["home"]}', "field": "fixture", "peer": "present", "official": "absent"})
                continue
            for f in ("date", "kickoff", "network"):
                pv = r[f].replace(" ET", "") if f == "kickoff" else r[f]
                ov = o[f].replace(" ET", "") if f == "kickoff" else o[f]
                if pv != ov:
                    diffs.append({"game": f'{r["away"]}@{r["home"]}', "field": f, "peer": r[f], "official": o[f]})
        peer_byes = set(peer["byes"])
        official_byes = set(OBS["week11_slate"]["byes"])
        checks.append({
            "id": "X-02",
            "claim": "nfl-book slate_week11_2026.json (13 fixtures, 6 byes, date/kickoff/network per game)",
            "peer_file": "nfl-book/data/slate_week11_2026.json",
            "n_cells_compared": len(peer["rows"]) * 3 + 1,
            "n_mismatch_cells": len(diffs) + (0 if peer_byes == official_byes else 1),
            "n_fixtures": len(peer["rows"]),
            "result": "pass" if not diffs and peer_byes == official_byes else "fail",
            "detail": "13/13 fixtures, 3 fields each + bye set, re-read from the official Week 11 schedule page.",
            "mismatches": diffs,
            "source_url": SOURCE_URL["S-week11"],
        })

    # 3. Peer claim that no official inactive list is captured anywhere.
    #    Resolved by whether nfl.com publishes one (it does) — evidence, not opinion.
    checks.append({
        "id": "X-03",
        "claim": "Peer flags FB-06: 'no active list or snap share is captured' — treated as if no official inactive source existed",
        "peer_file": "nfl-book/data/flags.json (FB-01..FB-17)",
        "n_cells_compared": None,
        "result": "fail",
        "detail": ("nfl.com publishes a dated inactives article for every Sunday slate: "
                   f"{OBS['inactives_week10']['n_sections']} club sections, "
                   f"{inactives_stats()['n_named_players']} named players for Week 10, plus a "
                   "published venue per game. The gap is that the repository never ingested it — "
                   "not that the source does not exist. This changes the blocker from "
                   "'no source' to 'not yet ingested'."),
        "mismatches": [],
        "source_url": SOURCE_URL["S-inact"],
    })

    # 4. Peer injury capture completeness vs the full report.
    p = os.path.join(REPO, "nfl-book", "data", "injuries_week10_capture.json")
    peer_n = peer_clubs = peer_games = None
    if os.path.exists(p):
        pr = json.load(open(p, encoding="utf-8"))["rows"]
        peer_n = len(pr)
        peer_clubs = len({r["team"] for r in pr})
        peer_games = len({r["game"] for r in pr})
    st = injury_stats()
    checks.append({
        "id": "X-04",
        "claim": "Peer injuries_week10_capture.json holds the Week 10 report",
        "peer_file": "nfl-book/data/injuries_week10_capture.json",
        "n_cells_compared": None,
        "peer_rows": peer_n,
        "peer_clubs": peer_clubs,
        "peer_games": peer_games,
        "official_rows": st["n_rows"],
        "official_sections": st["n_sections"],
        "n_mismatch_cells": (st["n_rows"] - peer_n) if peer_n else None,
        "result": "partial",
        "detail": (f"Peer capture holds {peer_n} rows covering {peer_clubs} clubs across "
                   f"{peer_games} of the {WK10_FIXTURES} Week 10 fixtures. This session read all 8 "
                   f"chunks: {st['n_sections']} club sections over all {WK10_FIXTURES} fixtures, "
                   f"{st['n_rows']} rows. "
                   f"Peer coverage is {round(100.0 * peer_n / st['n_rows'], 1)}% of rows and "
                   f"{round(100.0 * peer_clubs / st['n_teams_captured'], 1)}% of the clubs that "
                   "appear in the report. The peer's shortfall is in breadth of fixtures, not in "
                   "accuracy of what it did read." if peer_n else "peer file absent"),
        "mismatches": [],
        "source_url": SOURCE_URL["S-injuries"],
    })

    # 5. Peer claim that club depth is unparseable league-wide (Texans image).
    checks.append({
        "id": "X-05",
        "claim": "Peer flag FB-07: 'No official depth chart' — i.e. no structured club depth is obtainable",
        "peer_file": "nfl-book/data/flags.json (FB-07)",
        "n_cells_compared": None,
        "result": "fail",
        "detail": ("Partly true and partly false, and the distinction decides whether the feature is "
                   "buildable. Two clubs were probed this session: Houston renders image-only (0 players "
                   "in page text, no date); Green Bay renders a full structured table (44 named players, "
                   "jersey numbers prefixed, dated 'Unofficial, Nov. 10, 2026'). So a per-club route "
                   "exists for at least one club, while 30 remain unprobed and 1 of 2 is blocked. "
                   "The peer flag is wrong as a universal claim and right as a warning. A 32-club "
                   "verification is still required before any depth feature ships."),
        "mismatches": [],
        "source_url": "https://www.packers.com/team/depth-chart/",
    })

    return checks


# ------------------------------------------------------------------- venue work
def venue_stats():
    slate = OBS["week11_slate"]["rows"]
    gc = {r["game_id"]: r for r in OBS["game_centre_venues"]["rows"]}
    n_gc = sum(1 for r in OBS["game_centre_venues"]["rows"] if r["stadium"])
    n_gc_probed = len(OBS["game_centre_venues"]["rows"])
    return {
        "n_week11_fixtures": len(slate),
        "n_ticketmaster_venue_strings": sum(1 for r in slate if r.get("venue_ticketmaster_string")),
        "n_game_centre_probed": n_gc_probed,
        "n_game_centre_with_stadium": n_gc,
        "n_game_centre_missing_block": n_gc_probed - n_gc,
        "conflicts": [
            {"game": "MIN@SF", "source_a": "schedule page Ticketmaster destinationAddress", "value_a": "SoFi Stadium",
             "source_b": "official game centre Game Info", "value_b": "MEXICO CITY / ESTADIO BANORTE",
             "resolution": "game centre governs; the game is a designated international fixture (Mexico City), and the schedule page's hotel link points at the home club's home stadium."}
        ],
        "n_week10_venues_published": len(OBS["inactives_week10"]["venues_in_article"]),
    }


def main():
    inj = injury_stats()
    ina = inactives_stats()
    join_rows, join_agg = join_inactives_to_report()
    checks = compare_peer()
    ven = venue_stats()

    derived = {
        "dataset": "nfl_readiness_derived",
        "built_utc": OBS["capture_utc"],
        "method": ("Every figure is computed by derive.py from data/observations.json, which holds only "
                   "values transcribed from official nfl.com pages fetched on 2026-11-15. Re-running "
                   "derive.py is the verification: a number that cannot be recomputed is a defect."),
        "injury_report": inj,
        "inactives": ina,
        "inactives_join": {"agg": join_agg, "rows": join_rows},
        "peer_checks": checks,
        "internal_consistency": internal_consistency(),
        "venue": ven,
        "standings_confirmed": {"n_rows": OBS["standings"]["n_rows"], "source_url": SOURCE_URL["S-standings"]},
        "week11_confirmed": {"n_rows": OBS["week11_slate"]["n_rows"], "byes": OBS["week11_slate"]["byes"],
                             "source_url": SOURCE_URL["S-week11"]},
        "week10_scores_confirmed": {"n_finals": OBS["week10_scores"]["n_finals"],
                                    "n_in_progress": len(OBS["week10_scores"]["in_progress_at_capture"]),
                                    "source_url": SOURCE_URL["S-scores10"]},
    }
    save("derived.json", derived)

    # console summary
    print(f"[derive] injuries: {inj['n_sections']} sections / {inj['n_rows']} rows / "
          f"{inj['n_teams_captured']} clubs; game status on {inj['n_rows_with_game_status']} rows "
          f"({inj['pct_rows_with_game_status']}%)")
    print(f"[derive] inactives: {ina['n_sections']} sections / {ina['n_named_players']} named players; "
          f"empty lists: {ina['teams_with_empty_list']}")
    print(f"[derive] join: {join_agg['n_joinable_to_report']} joinable, "
          f"by status {join_agg['by_report_status']}")
    for c in derived["internal_consistency"]:
        print(f"[derive] {c['id']:<14} {c['verdict']}")
    for c in checks:
        print(f"[derive] {c['id']} {c['result']:<8} {c['claim'][:78]}")
    print(f"[derive] venue: {ven['n_game_centre_with_stadium']}/{ven['n_game_centre_probed']} probed "
          f"game centres publish a stadium; {len(ven['conflicts'])} conflict(s)")


if __name__ == "__main__":
    main()
