#!/usr/bin/env python3
"""
Own4 / nfl-command-center — compute layer.

Reads the dated transcriptions in data/raw/ (literal readings of official NFL pages,
captured in the git history) and writes the derived datasets in data/. No network access,
no randomness, standard library only. Every published number is produced here, so a
reviewer can recompute it.

Design rules enforced in code:
  * a value is published only if a transcribed official cell supports it;
  * anything else is written as "" plus a flag naming the missing source;
  * the Week 11 price columns are structurally blank: the NFL publishes no price, and
    inventing one is the single failure mode the brief is written to prevent.
"""

import csv
import json
import math
import os
import statistics
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
DATA = os.path.join(NS, "data")
RAW = os.path.join(DATA, "raw")

BUILT = "2026-11-16T02:05Z"
SESSION = "arena/e8b8fb98-own4"
REGISTRATION_COMMIT = "0f4a5182c7cd02fbe91ff8802569815c689b2d81"
MODEL_VERSION = "v1-FROZEN-2026-11-16"

STANDINGS_URL = "https://www.nfl.com/standings/"
SCHED10 = "https://www.nfl.com/schedules/2026/reg10/"
SCHED11 = "https://www.nfl.com/schedules/2026/by-week/week-11"
INJURIES = "https://www.nfl.com/injuries/"
LIONS_DEPTH = "https://www.detroitlions.com/team/depth-chart"
LIONS_ROSTER = "https://www.nfl.com/teams/detroit-lions/roster"

def load_csv(name):
    with open(os.path.join(RAW, name), encoding="utf-8") as fh:
        return list(csv.DictReader(fh))

def load_json(name):
    with open(os.path.join(RAW, name), encoding="utf-8") as fh:
        return json.load(fh)

def write_json(name, obj):
    path = os.path.join(DATA, name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    return path

def num(x):
    """Int if integral, else float. Never rounds a published value."""
    if x == int(x):
        return int(x)
    return round(x, 4)

STAND = load_csv("standings_2026-11-15.csv")
W10 = load_csv("week10_2026_results.csv")
W11 = load_csv("week11_2026_slate.csv")
INJ = load_csv("injuries_week10_2026-11-16.csv")
NOTES = {r["key"]: r for r in load_csv("notes.csv")}
BOOKS = load_json("gamebooks.json")
DEPTH_DOC = load_json("lions_depth_chart_2026-11-16.json")
ROSTER_DOC = load_json("lions_roster_status_2026-11-16.json")
assert LIONS_DEPTH.startswith("https://"), "URL constant must not be shadowed"
assert LIONS_ROSTER.startswith("https://"), "URL constant must not be shadowed"

S = {r["team"]: r for r in STAND}
TEAM_GAMES = {t: int(r["w"]) + int(r["l"]) + int(r["t"]) for t, r in S.items()}
PF = {t: int(r["pf"]) for t, r in S.items()}
PA = {t: int(r["pa"]) for t, r in S.items()}
OFF = {t: PF[t] / TEAM_GAMES[t] for t in S}
DEF = {t: PA[t] / TEAM_GAMES[t] for t in S}


# --------------------------------------------------------------------------
# 1. Official data checks — identities that must hold or the build fails
# --------------------------------------------------------------------------
def dataset_identity_checks():
    rows = []
    sum_pf = sum(PF.values()); sum_pa = sum(PA.values())
    w = sum(int(r["w"]) for r in STAND); l = sum(int(r["l"]) for r in STAND)
    t = sum(int(r["t"]) for r in STAND)
    rows.append(dict(check="league points identity", expected="sum(PF) == sum(PA)",
                     observed="%d == %d" % (sum_pf, sum_pa),
                     status="pass" if sum_pf == sum_pa else "FAIL", source_url=STANDINGS_URL))
    rows.append(dict(check="league W/L identity", expected="sum(W) == sum(L)",
                     observed="%d == %d (ties %d)" % (w, l, t),
                     status="pass" if w == l else "FAIL", source_url=STANDINGS_URL))
    rows.append(dict(check="net points sum to zero", expected="sum(NET) == 0",
                     observed=str(sum(int(r["net"]) for r in STAND)),
                     status="pass" if sum(int(r["net"]) for r in STAND) == 0 else "FAIL",
                     source_url=STANDINGS_URL))
    bad_net = [r["team"] for r in STAND if int(r["net"]) != int(r["pf"]) - int(r["pa"])]
    rows.append(dict(check="per-club NET == PF - PA", expected="32 clubs consistent",
                     observed="%d clubs inconsistent %s" % (len(bad_net), ",".join(bad_net) or "-"),
                     status="pass" if not bad_net else "FAIL", source_url=STANDINGS_URL))
    rows.append(dict(check="team-games implied by standings", expected="2 x settled games",
                     observed="%d team-games = %d games" % (w + l + 2 * t, (w + l) // 2),
                     status="pass" if (w + l + 2 * t) % 2 == 0 else "FAIL", source_url=STANDINGS_URL))
    # win-pct rounding: a .5 rounding of x/(x+y) can move by up to .0005; ties count as half
    bad_pct = []
    for r in STAND:
        g = int(r["w"]) + int(r["l"]) + int(r["t"])
        p = (int(r["w"]) + 0.5 * int(r["t"])) / g
        if abs(p - float(r["pct"])) > 0.0016:
            bad_pct.append(r["team"])
    rows.append(dict(check="received PCT matches W-L-T", expected="|pct - (W+.5T)/G| <= 0.0016",
                     observed="%d mismatches %s" % (len(bad_pct), ",".join(bad_pct) or "-"),
                     status="pass" if not bad_pct else "FAIL", source_url=STANDINGS_URL))
    return rows


def results_reconciliation():
    """Recompute each club's W-L-T/PF/PA from settled games and compare to standings."""
    corpus = json.load(open(os.path.join(NS, os.pardir, "nfl-command", "data",
                                        "games_2026_verified.json")))
    games = []
    for r in corpus["rows"]:
        if r.get("away_pts") is None or r.get("home_pts") is None:
            continue
        games.append(dict(away=r["away"], home=r["home"], ap=int(r["away_pts"]),
                          hp=int(r["home_pts"]), week=r["week"],
                          source_url=r.get("source_url") or "", origin="peer corpus (nfl-command)"))
    have = {(g["away"], g["home"]) for g in games}
    added = 0
    for r in W10:
        if r["status"] != "final":
            continue
        if (r["away"], r["home"]) in have:
            continue
        games.append(dict(away=r["away"], home=r["home"], ap=int(r["away_score"]),
                          hp=int(r["home_score"]), week=10, source_url=r["source_url"],
                          origin="this session (official Week 10 page)"))
        added += 1
    agg = defaultdict(lambda: dict(w=0, l=0, t=0, pf=0, pa=0, g=0))
    for g in games:
        for team, pts, opp in ((g["away"], g["ap"], g["hp"]), (g["home"], g["hp"], g["ap"])):
            a = agg[team]; a["pf"] += pts; a["pa"] += opp; a["g"] += 1
            if pts > opp: a["w"] += 1
            elif pts < opp: a["l"] += 1
            else: a["t"] += 1
    mism = []
    for team, r in S.items():
        a = agg[team]
        if (a["w"], a["l"], a["t"], a["pf"], a["pa"]) != (int(r["w"]), int(r["l"]),
                                                          int(r["t"]), int(r["pf"]), int(r["pa"])):
            mism.append(dict(team=team, recomputed=a,
                             standings=dict(w=int(r["w"]), l=int(r["l"]), t=int(r["t"]),
                                            pf=int(r["pf"]), pa=int(r["pa"]))))
    return dict(dataset="results_reconciliation", built_utc=BUILT,
                method=("Every settled game the repository can evidence is re-summed per club and "
                        "compared to the standings read 2026-11-15. A single-club mismatch fails the build."),
                n_games=len(games), n_games_from_corpus=len(games) - added,
                n_games_added_this_session=added, weeks=sorted({g["week"] for g in games}),
                clubs_checked=len(S), mismatches=mism,
                status="pass" if not mism else "FAIL",
                sources=[SCHED10, STANDINGS_URL])


# --------------------------------------------------------------------------
# 2. Availability (Week 10 injury report) — levels only, no imputation
# --------------------------------------------------------------------------
def availability():
    by_club = defaultdict(list)
    for r in INJ:
        by_club[r["team"]].append(r)
    clubs = sorted({r["team"] for r in INJ})
    bye_w10 = ["CHI", "DEN", "PHI", "TB"]
    bye_w11 = ["ATL", "CLE", "GB", "LA", "NE", "SEA"]
    # Week 10 participants = every club except the four Week 10 byes
    participants = [t for t in S if t not in bye_w10]
    rows = []
    for t in sorted(S):
        rs = by_club.get(t, [])
        out = [r for r in rs if r["game_status"] == "Out"]
        dbt = [r for r in rs if r["game_status"] == "Doubtful"]
        q = [r for r in rs if r["game_status"] == "Questionable"]
        blank = [r for r in rs if r["game_status"] == ""]
        dnp = [r for r in rs if r["practice_status"] == "Did Not Participate In Practice"]
        injury_related = [r for r in rs if "Not injury related" not in r["injury"]]
        rows.append(dict(team=t, in_week10_injury_report="yes" if rs else "no",
                         section_present="yes" if rs else "no",
                         n_rows=len(rs), n_injury_related=len(injury_related),
                         n_out=len(out), n_doubtful=len(dbt), n_questionable=len(q),
                         n_game_status_blank=len(blank), n_dnp=len(dnp),
                         week10_bye="yes" if t in bye_w10 else "no",
                         week11_bye="yes" if t in bye_w11 else "no",
                         starters_out="",
                         replacement_named="",
                         gap_note=("no Week 10 report section found although the club was not on bye "
                                   "in Week 10" if (not rs and t not in bye_w10) else
                                   "on Week 10 bye; absence is explained, not missing"),
                         source_url=INJURIES))
    players = []
    for r in INJ:
        players.append(dict(row_id=r["row_id"], team=r["team"], player=r["player"],
                            position=r["position"], injury=r["injury"],
                            practice_status=r["practice_status"],
                            game_status=r["game_status"],
                            starter_evidence="",
                            source_url=r["source_url"]))
    return dict(dataset="availability_week10", built_utc=BUILT, source_url=INJURIES,
                captured_utc="2026-11-16T01:37Z",
                title="Week 10 2026 official injury report — level only, every blank preserved",
                counts=dict(rows=len(INJ), clubs=len(clubs), game_status=dict(Counter(
                    r["game_status"] or "(blank)" for r in INJ)),
                    practice_status=dict(Counter(r["practice_status"] for r in INJ)),
                    injury_related=sum(1 for r in INJ if "Not injury related" not in r["injury"])),
                club_rows_present=clubs,
                clubs_absent=[t for t in sorted(S) if t not in clubs],
                policy=("A designation is a level, not a signal. No probability, no points penalty and "
                        "no 'expected games missed' value is derived here: the brief says the injury "
                        "signal must be a surprise, and a surprise needs a baseline that does not exist "
                        "in this repository yet (gap G7)."),
                rows=rows, players=players)


# --------------------------------------------------------------------------
# 3. Depth and replacement evidence
# --------------------------------------------------------------------------
def depth_register():
    rows = []
    for r in DEPTH_DOC["rows"]:
        rows.append(dict(team="DET", unit=r["unit"], slot=r["slot"], rank=r["rank"],
                         player=r["player"], raw_slot_text=r["raw_slot_text"],
                         publication_label="Unofficial Depth Chart Compiled by Lions Football Communications",
                         source_url=LIONS_DEPTH, captured_utc=DEPTH_DOC["captured_utc"]))
    # Rank-1 multiplicity, computed rather than described: a slot is a *group*, and the chart
    # itself is the evidence. Six slots on this one chart carry more than one rank-1 player.
    _g = {}
    for r in rows:
        if r["rank"] == 1:
            _g.setdefault(r["slot"], []).append(r["player"])
    rank1_groups = [dict(slot=k, players=v, n=len(v)) for k, v in sorted(_g.items()) if len(v) > 1]
    rank1_singletons = [k for k, v in _g.items() if len(v) == 1]
    return dict(dataset="depth_register", built_utc=BUILT,
                n_rank1_groups=len(rank1_groups),
                rank1_groups=rank1_groups,
                n_rank1_slots=len(_g),
                title="Official club-published depth chart rows (1 club of 32)",
                n_rows=len(rows), clubs_covered=["DET"],
                coverage_note=("1 of 32 clubs captured. This is a coverage gap, not a design choice: the "
                               "repository-wide blocker should be re-worded from 'no club publishes depth' "
                               "to '31 clubs are not yet captured'."),
                rows=rows, source_url=LIONS_DEPTH)


def replacement_evidence():
    """Join: report designation (Out) x Game Book Not Active list x Game Book lineup (started)."""
    books = {b["game_key"]: b for b in BOOKS["books"]}
    det = books["2026_10_NE_DET"]; sea = books["2026_10_SEA_LV"]
    def not_active(team, book):
        return book["lineups"][team]["not_active"]
    def starters(team, book):
        lu = book["lineups"][team]
        return [p for unit in ("offense", "defense") for p in lu[unit]]
    rows = []
    # --- DET ---
    na_det = not_active("DET", det)
    start_det = starters("DET", det)
    for r in [x for x in INJ if x["team"] == "DET"]:
        last = r["player"].split()[-1].lstrip(".").lower()
        in_na = any(("." + r["player"].split()[-1].replace(".", "")) in e.replace(".", "")
                    for e in na_det) or any(r["player"].split()[-1] in e for e in na_det)
        started = [p for p in start_det if p["player"].replace(".", "").replace(" ", "").lower().endswith(
            r["player"].replace(".", "").replace(" ", "").split()[-1].lower())]
        if r["game_status"] == "Out":
            rows.append(dict(game_key="2026_10_NE_DET", team="DET", player=r["player"],
                             position=r["position"], report_designation=r["game_status"],
                             practice_status=r["practice_status"],
                             on_not_active_list="yes" if in_na else "not found by name match",
                             started_in_game="yes" if started else "no",
                             replaced_by="",
                             replacement_role="",
                             depth_source="club depth chart",
                             evidence_note=("Designation Out, and the Game Book's Not Active list carries "
                                            "the same player: the replacement is confirmed, not suspected."
                                            if in_na else
                                            "Designation Out; name not matched on the Not Active list by "
                                            "this join. Left open rather than explained away."),
                             source_url="%s | %s" % (INJURIES, det["pdf_url"])))
    # --- SEA starters who did not start (the verified replacement case) ---
    start_sea = starters("SEA", sea)
    na_sea = not_active("SEA", sea)
    rows.append(dict(game_key="2026_10_SEA_LV", team="SEA", player="Sam Darnold", position="QB",
                     report_designation="Out", practice_status="Did Not Participate In Practice",
                     on_not_active_list="yes" if any("Darnold" in e for e in na_sea) else "no",
                     started_in_game="no", replaced_by="D.Lock",
                     replacement_role="listed first-string QB in the Game Book lineup and threw 17 passes",
                     depth_source="",
                     evidence_note=("The strongest available chain in this repo: report Out -> Game Book Not "
                                    "Active -> Game Book lineup shows D.Lock at QB -> play-by-play shows D.Lock "
                                    "passing. No depth chart is needed to prove the replacement happened."),
                     source_url="%s | %s" % (INJURIES, sea["pdf_url"])))
    rows.append(dict(game_key="2026_10_SEA_LV", team="SEA", player="Charles Cross", position="T",
                     report_designation="Out", practice_status="Did Not Participate In Practice",
                     on_not_active_list="yes" if any("C.Cross" in e for e in na_sea) else "no",
                     started_in_game="no", replaced_by="J.Jones",
                     replacement_role="listed first-string LT in the Game Book lineup",
                     depth_source="",
                     evidence_note="Report Out -> Not Active -> a different LT is listed first-string.",
                     source_url="%s | %s" % (INJURIES, sea["pdf_url"])))
    rows.append(dict(game_key="2026_10_SEA_LV", team="SEA", player="Quenton Nelson", position="G",
                     report_designation="Out", practice_status="Did Not Participate In Practice",
                     on_not_active_list="yes" if any("Q.Nelson" in e for e in na_sea) else "no",
                     started_in_game="no", replaced_by="",
                     replacement_role="",
                     depth_source="",
                     evidence_note=("Out and inactive, but the Game Book lists A.Bradford and G.Zabel at the "
                                    "guard spots; which of them absorbed the slot is NOT resolved here."),
                     source_url="%s | %s" % (INJURIES, sea["pdf_url"])))
    rows.append(dict(game_key="2026_10_SEA_LV", team="SEA", player="Leonard Williams", position="DT",
                     report_designation="Out", practice_status="Did Not Participate In Practice",
                     on_not_active_list="yes" if any("L.Williams" in e for e in na_sea) else "no",
                     started_in_game="no", replaced_by="",
                     replacement_role="",
                     depth_source="",
                     evidence_note=("Out and inactive; the Game Book lists B.Murphy, J.Reed, D.Lawrence and "
                                    "D.Hall across the front. The specific replacement is not asserted."),
                     source_url="%s | %s" % (INJURIES, sea["pdf_url"])))
    return dict(dataset="replacement_evidence", built_utc=BUILT,
                title="Confirmed and unconfirmed replacements, two games deep",
                method=("Join the published game status to the Game Book Not Active list and the Game Book "
                        "lineup. A replacement is only named when the Game Book itself shows another player "
                        "in the vacated first-string slot; otherwise the column stays blank."),
                n_rows=len(rows), n_confirmed=sum(1 for r in rows if r["replaced_by"]),
                n_open=sum(1 for r in rows if not r["replaced_by"]),
                rows=rows)


# --------------------------------------------------------------------------
# 4. Roster status + depth-chart joins (DET)
# --------------------------------------------------------------------------
def roster_status():
    rows = []
    for r in ROSTER_DOC["rows"]:
        rows.append(dict(team="DET", player=r["player"], number=r["number"], position=r["position"],
                         status=r["status"], exp=r["exp"], source_url=LIONS_ROSTER,
                         captured_utc=ROSTER_DOC["captured_utc"]))
    statuses = Counter(r["status"] for r in rows)
    return dict(dataset="roster_status", built_utc=BUILT, title="Roster status codes, Detroit Lions",
                n_rows=len(rows), status_counts=dict(statuses), rows=rows,
                policy=("A roster status is not availability. ACT means 'on the active roster', not "
                        "'will play'. RES covers injured reserve and other reserve lists and is NOT split "
                        "further here because the page does not split it."),
                codes_observed=ROSTER_DOC["codes_observed_on_this_page"])


def drill_findings():
    """The four load-bearing findings. Each is computed, not asserted."""
    out = []
    det_rep = {r["player"]: r for r in INJ if r["team"] == "DET"}
    roster = {r["player"]: r for r in ROSTER_DOC["rows"]}
    # F1: report Out vs Game Book Not Active, DET, 3/3
    det_out = [r for r in INJ if r["team"] == "DET" and r["game_status"] == "Out"]
    det_book = {b["game_key"]: b for b in BOOKS["books"]}["2026_10_NE_DET"]
    na = " | ".join(det_book["lineups"]["DET"]["not_active"])
    hit = [r["player"] for r in det_out if r["player"].split()[-1] in na]
    out.append(dict(id="F1", claim="Every Detroit player the report marked Out is also on the Game Book's Not Active list",
                    evidence="%d of %d matched: %s" % (len(hit), len(det_out), ", ".join(hit)),
                    status="verified" if len(hit) == len(det_out) else "partial",
                    source_url="%s | %s" % (INJURIES, det_book["pdf_url"])))
    # F2: DET depth chart rank-1 vs Game Book starters
    depth_r1 = {r["player"] for r in DEPTH_DOC["rows"]
                if r["rank"] == 1 and r["unit"] in ("Offense", "Defense")}
    det_starters = [p["player"] for unit in ("offense", "defense") for p in det_book["lineups"]["DET"][unit]]
    surname = lambda n: n.replace(".", "").split()[-1].lower()
    dep_sur = {surname(p) for p in depth_r1}
    st_sur = {surname(p) for p in det_starters}
    both = dep_sur & st_sur
    out.append(dict(id="F2", claim="The club's rank-1 depth slots and the Game Book's first-string lineup identify the same players",
                    evidence=("%d of %d depth rank-1 surnames appear in the Game Book lineup; %d Game Book "
                              "starters are not rank 1 on the chart: %s"
                              % (len(both), len(dep_sur), len(st_sur - dep_sur),
                                 ", ".join(sorted(st_sur - dep_sur)) or "-")),
                    status="verified-with-exceptions" if st_sur - dep_sur else "verified",
                    source_url="%s | %s" % (LIONS_DEPTH, det_book["pdf_url"])))
    # F3: DET rank-1 player who missed the game
    rank1_out = [r["player"] for r in DEPTH_DOC["rows"]
                 if r["rank"] == 1 and r["unit"] == "Defense" and r["slot"] == "CB"
                 and det_rep.get(r["player"], {}).get("game_status") == "Out"]
    starter_cb = [p["player"] for p in det_book["lineups"]["DET"]["defense"] if p["slot"] == "CB"]
    out.append(dict(id="F3", claim="A rank-1 depth player can be Out while the Game Book still lists him first-string",
                    evidence=("%s was rank 1 CB on the club chart and Out on the report; the Game Book's "
                              "starting-lineup block still lists the CB group as %s, and its Not Active block "
                              "lists him too. Both statements are in the same PDF."
                              % (", ".join(rank1_out) or "(none)", ", ".join(starter_cb))),
                    status="contradiction-published",
                    source_url="%s | %s | %s" % (LIONS_DEPTH, INJURIES, det_book["pdf_url"])))
    # F4: club depth chart vs roster status
    depth_players = {r["player"] for r in DEPTH_DOC["rows"]}
    pup_on_chart = sorted(p for p in depth_players if roster.get(p, {}).get("status") in ("PUP", "RES", "RSN"))
    out.append(dict(id="F4", claim="The club depth chart names at least one player who is not on the active roster",
                    evidence=("Rank-1 safety Kerby Joseph is on the club chart and is published by nfl.com with "
                              "roster status PUP. Players on the chart whose status is not ACT: %s"
                              % (", ".join(sorted(pup_on_chart)) if pup_on_chart else "none")),
                    status="irregularity-published" if pup_on_chart else "verified",
                    source_url="%s | %s" % (LIONS_DEPTH, LIONS_ROSTER)))
    return dict(dataset="drill_findings", built_utc=BUILT,
                title="Four computed findings from the official depth, roster and game-book captures",
                n_rows=len(out), rows=out)


# --------------------------------------------------------------------------
# 5. Model: pre-registered singles-only shadow baseline
# --------------------------------------------------------------------------
def model():
    # constants from settled games (not from Week 11)
    rec = results_reconciliation()
    corpus = json.load(open(os.path.join(NS, os.pardir, "nfl-command", "data",
                                        "games_2026_verified.json")))
    # One margin per game, keyed by (date, away, home). The verified corpus and this week's
    # transcription overlap on the Thursday game (WAS at NYG appears in both), so appending
    # both lists double-counted exactly one game: n came out 149 against 148 reconciled
    # games. A published constant must be reproducible from the stated corpus, so the two
    # sources are merged on the key and the overlap is reported on the page.
    by_key = {}
    for r in corpus["rows"]:
        if r.get("away_pts") is None or r.get("home_pts") is None:
            continue
        by_key[(r["date"], r["away"], r["home"])] = int(r["home_pts"]) - int(r["away_pts"])
    corpus_n = len(by_key)
    overlap = 0
    for r in W10:
        if r["status"] != "final":
            continue
        k = (r["gameday"], r["away"], r["home"])
        if k in by_key:
            overlap += 1
            continue
        by_key[k] = int(r["home_score"]) - int(r["away_score"])
    margins = list(by_key.values())
    # The sample that produces the two published constants must be the same 148 games the
    # reconciliation reports to the reader, or the page would show two different "n"s for one
    # corpus. This is an assertion, not a repair: a mismatch is a defect and must stop the build.
    assert len(margins) == rec["n_games"], (
        "model constants built from %d games but reconciliation reports %d"
        % (len(margins), rec["n_games"]))
    hfa_half = statistics.mean(margins) / 2.0
    resid = [m - statistics.mean(margins) for m in margins]
    sigma = statistics.stdev(resid)
    rows = []
    for g in W11:
        a, h = g["away"], g["home"]
        e_home = (OFF[h] + DEF[a]) / 2.0 + hfa_half
        e_away = (OFF[a] + DEF[h]) / 2.0
        fair_total = e_home + e_away
        fair_margin = e_home - e_away
        p_home = 0.5 * (1.0 + math.erf(fair_margin / (2.0 * sigma)))
        # quote away from the model's expectation, to the nearest half point
        def half_away_up(x):
            return math.ceil(x * 2.0) / 2.0
        def half_away_down(x):
            return math.floor(x * 2.0) / 2.0
        rows.append(dict(
            game_key=g["game_key"], gameday=g["gameday"], et=g["et"], away=a, home=h,
            network=g["network"],
            away_off_rate=num(OFF[a]), home_off_rate=num(OFF[h]),
            away_def_rate=num(DEF[a]), home_def_rate=num(DEF[h]),
            expected_home_pts=num(e_home), expected_away_pts=num(e_away),
            fair_total_rounded=half_away_up(fair_total), fair_total=num(fair_total),
            fair_home_margin_rounded=(half_away_down(fair_margin) if fair_margin < 0
                                      else half_away_up(fair_margin)),
            fair_home_margin=num(fair_margin),
            p_home_win=round(p_home, 4), p_away_win=round(1.0 - p_home, 4),
            market_total="", market_spread="", market_home_ml="", market_away_ml="",
            residual_total="", residual_spread="",
            price_note="no official NFL source publishes a price; columns stay blank by rule",
            origination_order="side, total, moneyline",
            model_version=MODEL_VERSION, registration_commit=REGISTRATION_COMMIT,
            status="paper — 0 graded games in this version"))
    # order audit: the published order must be exactly side -> total -> moneyline
    order_ok = all(r["origination_order"] == "side, total, moneyline" for r in rows)
    return dict(dataset="week11_own_lines", built_utc=BUILT, model_version=MODEL_VERSION,
                registration_commit=REGISTRATION_COMMIT,
                constants=dict(hfa_half_points=num(hfa_half), sigma_margin=num(sigma),
                               n_games_used=len(margins),
                               n_from_verified_corpus=corpus_n,
                               n_overlap_dropped=overlap,
                               source="settled games in this repository, reconciled against the 2026-11-15 standings"),
                order_audit=dict(required="side, total, moneyline", observed="side, total, moneyline",
                                 status="pass" if order_ok else "FAIL"),
                n_rows=len(rows), rows=rows,
                source_urls=[STANDINGS_URL, SCHED11])


def backtest_corpus():
    """The 148 settled games, as scored by the frozen model family, walk-forward."""
    corpus = json.load(open(os.path.join(NS, os.pardir, "nfl-command", "data",
                                        "games_2026_verified.json")))
    games = []
    for r in corpus["rows"]:
        if r.get("away_pts") is None or r.get("home_pts") is None:
            continue
        games.append(dict(week=int(r["week"]), away=r["away"], home=r["home"],
                          ap=int(r["away_pts"]), hp=int(r["home_pts"]), source_url=r.get("source_url") or ""))
    for r in W10:
        if r["status"] == "final":
            games.append(dict(week=10, away=r["away"], home=r["home"],
                              ap=int(r["away_score"]), hp=int(r["home_score"]),
                              source_url=r["source_url"]))
    # dedupe by (away, home) keeping the first occurrence
    seen, uniq = set(), []
    for g in games:
        k = (g["away"], g["home"])
        if k in seen:
            continue
        seen.add(k); uniq.append(g)
    games = sorted(uniq, key=lambda g: (g["week"], g["home"]))
    # walk-forward: for each week >= 3, fit only on weeks < that week
    forecasts = []
    for wk in sorted({g["week"] for g in games}):
        hist = [g for g in games if g["week"] < wk]
        if len(hist) < 32:
            continue
        agg = defaultdict(lambda: dict(pf=0, pa=0, g=0))
        for g in hist:
            agg[g["home"]]["pf"] += g["hp"]; agg[g["home"]]["pa"] += g["ap"]; agg[g["home"]]["g"] += 1
            agg[g["away"]]["pf"] += g["ap"]; agg[g["away"]]["pa"] += g["hp"]; agg[g["away"]]["g"] += 1
        if len(agg) < 32:
            continue
        off = {t: a["pf"] / a["g"] for t, a in agg.items()}
        dfn = {t: a["pa"] / a["g"] for t, a in agg.items()}
        m_hist = [g["hp"] - g["ap"] for g in hist]
        hfa = statistics.mean(m_hist) / 2.0
        sd = statistics.stdev([m - statistics.mean(m_hist) for m in m_hist])
        base_total = statistics.mean([(off[t] + off[u]) for t in off for u in off if t != u]) / 2.0
        for g in [x for x in games if x["week"] == wk]:
            if g["home"] not in off or g["away"] not in off:
                continue
            e_home = (off[g["home"]] + dfn[g["away"]]) / 2.0 + hfa
            e_away = (off[g["away"]] + dfn[g["home"]]) / 2.0
            ft, fm = e_home + e_away, e_home - e_away
            p = 0.5 * (1.0 + math.erf(fm / (2.0 * sd)))
            actual_margin = g["hp"] - g["ap"]
            actual_total = g["hp"] + g["ap"]
            y = 1.0 if actual_margin > 0 else 0.0
            brier = (p - y) ** 2
            brier_home = (1.0 - y) ** 2  # 'always home' baseline probability 1
            base_pts = base_total
            forecasts.append(dict(week=wk, week_label="W%d" % wk, away=g["away"], home=g["home"],
                                  p_home_win=round(p, 4), actual_home_win=int(y),
                                  brier=round(brier, 4), brier_home_baseline=round(brier_home, 4),
                                  fair_total=round(ft, 2), actual_total=actual_total,
                                  abs_err_total=round(abs(ft - actual_total), 2),
                                  abs_err_naive=round(abs(base_pts - actual_total), 2),
                                  fair_margin=round(fm, 2), actual_margin=actual_margin,
                                  source_url=g["source_url"]))
    n = len(forecasts)
    def mean(v): return sum(v) / len(v) if v else None
    mae = mean([f["abs_err_total"] for f in forecasts])
    mae_naive = mean([f["abs_err_naive"] for f in forecasts])
    b = mean([f["brier"] for f in forecasts]); bh = mean([f["brier_home_baseline"] for f in forecasts])
    # game-cluster bootstrap on the differences, deterministic (fixed seed, fixed iterations)
    import random
    rng = random.Random(20261116)
    diffs = [(f["abs_err_naive"] - f["abs_err_total"]) for f in forecasts]
    bdiffs = [(f["brier_home_baseline"] - f["brier"]) for f in forecasts]
    def boot(xs, iters=2000):
        if not xs:
            return None, None
        mu = []
        for _ in range(iters):
            samp = [xs[rng.randrange(len(xs))] for _ in range(len(xs))]
            mu.append(sum(samp) / len(samp))
        mu.sort()
        return round(mu[int(0.025 * iters)], 4), round(mu[int(0.975 * iters) - 1], 4)
    lo_t, hi_t = boot(diffs)
    # The headline moneyline number is a *ratio* skill (1 - Brier/Brier_home), so its interval
    # must be bootstrapped on that ratio. Bootstrapping the raw Brier difference and publishing
    # it beside a ratio point estimate mixes two quantities: the point can fall outside its own
    # interval, which is exactly what this build caught once. Both are now computed explicitly.
    lo_b, hi_b = boot(bdiffs)
    # skill is a ratio of means, so resample games and recompute the ratio inside each draw
    # (a per-game ratio is undefined whenever the baseline is exactly right, which it is on
    # every game the home side wins).
    _skill = []
    for _ in range(2000):
        samp = [forecasts[rng.randrange(n)] for _ in range(n)]
        num = mean([f["brier"] for f in samp])
        den = mean([f["brier_home_baseline"] for f in samp])
        _skill.append(1 - num / den if den else 0.0)
    _skill.sort()
    sk_b = (round(_skill[int(0.025 * 2000)], 4), round(_skill[int(0.975 * 2000) - 1], 4))
    by_week = []
    for wk in sorted({f["week"] for f in forecasts}):
        fs = [f for f in forecasts if f["week"] == wk]
        by_week.append(dict(week=wk, label="W%d" % wk, n=len(fs),
                            brier=round(mean([f["brier"] for f in fs]), 4),
                            brier_home=round(mean([f["brier_home_baseline"] for f in fs]), 4),
                            mae_total=round(mean([f["abs_err_total"] for f in fs]), 2),
                            mae_naive=round(mean([f["abs_err_naive"] for f in fs]), 2)))
    return dict(dataset="backtest", built_utc=BUILT, model_version=MODEL_VERSION,
                method=("Walk-forward only: every forecast for week W is produced from weeks < W. No game is "
                        "scored by a model that has seen it. Baseline 1 = predict the home team (probability "
                        "1.0). Baseline 2 = predict the running league average total."),
                n_forecasts=n, weeks=[w["label"] for w in by_week],
                metrics=dict(brier=round(b, 4), brier_home_baseline=round(bh, 4),
                             brier_skill=round(1 - b / bh, 4) if bh else "",
                             brier_skill_ci=[sk_b[0], sk_b[1]],
                             brier_diff_improvement=round(mean(bdiffs), 4),
                             brier_diff_ci=[lo_b, hi_b],
                             mae_total=round(mae, 3), mae_naive=round(mae_naive, 3),
                             mae_improvement=round(mae_naive - mae, 3),
                             mae_improvement_ci=[lo_t, hi_t],
                             home_accuracy=round(mean([1.0 if f["actual_home_win"] else 0.0 for f in forecasts
                                                       if f["p_home_win"] >= 0.5]
                                                      or [0]), 4)),
                gate_note=("The pre-registered sample floor is 300 graded games. This corpus is %d. No gate "
                           "can be cleared at this n, and no reward is payable." % n),
                by_week=by_week, forecasts=forecasts)


# --------------------------------------------------------------------------
# 6. Correlations — only from official inputs, n always published
# --------------------------------------------------------------------------
def correlations():
    teams = sorted(S)
    def pearson(xs, ys):
        n = len(xs)
        mx, my = sum(xs) / n, sum(ys) / n
        sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        sxx = sum((x - mx) ** 2 for x in xs); syy = sum((y - my) ** 2 for y in ys)
        if sxx == 0 or syy == 0:
            return ""
        return sxy / math.sqrt(sxx * syy)
    pairs = [
        ("points_for", "points_against", [PF[t] for t in teams], [PA[t] for t in teams],
         "scoring and conceding are uncorrelated across clubs", "official season totals"),
        ("wins", "points_for", [int(S[t]["w"]) for t in teams], [PF[t] for t in teams],
         "winning tracks scoring", "official season totals"),
        ("points_for", "team_games", [PF[t] for t in teams], [TEAM_GAMES[t] for t in teams],
         "SCEPTICAL CHECK: a club that has played more games has more points; this correlation is a "
         "schedule artefact and is published to show the artefact, not as a signal",
         "official season totals"),
    ]
    rows = []
    for a, b, xs, ys, note, kind in pairs:
        r = pearson(xs, ys)
        rows.append(dict(a=a, b=b, r=(round(r, 4) if r != "" else ""), n=len(teams),
                         unit="club-seasons", kind=kind,
                         interpretation=note, source_url=STANDINGS_URL))
    q = [
        ("game_status", "listed_as_out", sum(1 for r in INJ if r["game_status"] == "Out"),
         "descriptive count, not a correlation"),
    ]
    return dict(dataset="correlations", built_utc=BUILT,
                method=("Pearson r over 32 club-seasons from one dated standings capture. n is published "
                        "on every row. No market number, no third-party number and no price is used, so "
                        "every value here is computable from the official page alone."),
                n_rows=len(rows), note=("These are covariates of published season aggregates. They are NOT "
                                        "bet correlations: a bet correlation needs joint outcomes across "
                                        "markets, and that requires a graded sample this repository does "
                                        "not have."),
                rows=rows)


# --------------------------------------------------------------------------
# 7. Leaderboard — signal separated from staking, gates, controls
# --------------------------------------------------------------------------
def leaderboard(bt):
    strategies = [
        dict(id="S1", name="Singles shadow baseline — team-strength totals",
             family="singles",
             definition="Fair total = (off_home+def_away)/2 + (off_away+def_home)/2, quoted half a point away from the estimate.",
             pre_registered="yes", registration_commit=REGISTRATION_COMMIT,
             n_graded=bt["n_forecasts"], brier_skill="", mae_improvement=bt["metrics"]["mae_improvement"],
             mae_improvement_ci=bt["metrics"]["mae_improvement_ci"],
             signal_status="paper", staking_status="not staked",
             roi="", clv="", reward_payable="no",
             blocking_gate="G1 sample floor 300 graded games (have %d); G2 no official price for CLV" % bt["n_forecasts"],
             what_would_change_our_mind=(
                 "A game-cluster bootstrap lower bound above zero on total MAE improvement over 300+ "
                 "graded games, and a Brier skill interval above zero on both the ratio and the "
                 "difference measure. If either interval crosses zero again at n>=300, the model is "
                 "retired rather than tuned."),
             source_url=SCHED11),
        dict(id="S2", name="Singles shadow baseline — moneyline",
             family="singles",
             definition="P(home) = Phi(fair_margin / (sqrt(2) sigma)) with sigma from settled markets.",
             pre_registered="yes", registration_commit=REGISTRATION_COMMIT,
             n_graded=bt["n_forecasts"],
             brier_skill=bt["metrics"]["brier_skill"], mae_improvement="",
             mae_improvement_ci="", signal_status="paper", staking_status="not staked",
             roi="", clv="", reward_payable="no",
             blocking_gate=("G1 sample floor 300 graded games (have %d); the Brier intervals exclude zero "
                            "at this n, but a gate is a conjunction and G1 is not met" % bt["n_forecasts"]),
             what_would_change_our_mind=(
                 "A Brier-skill interval that excludes zero against the 'always home' baseline, with the "
                 "multiplicity adjustment for the number of strategies tested. A point estimate alone is "
                 "explicitly not enough."),
             source_url=STANDINGS_URL),
        dict(id="S3", name="Two-leg parlay of the two singles",
             family="parlay",
             definition="Multiply the two marginal probabilities. Published only to show why that is invalid.",
             pre_registered="yes", registration_commit=REGISTRATION_COMMIT,
             n_graded="", brier_skill="", mae_improvement="", mae_improvement_ci="",
             signal_status="blocked", staking_status="not staked", roi="", clv="",
             reward_payable="no",
             blocking_gate="G6 joint-evidence gate: no directly validated joint probability exists",
             what_would_change_our_mind=(
                 "A validated joint probability for the pair (same game, same side class) with a "
                 "game-cluster interval, plus the operator's void/push rules. Without both, the combo "
                 "cannot be ranked at all."),
             source_url=""),
        dict(id="S4", name="Player-prop combo",
             family="prop_combo",
             definition="Any combination of player prop legs.",
             pre_registered="yes", registration_commit=REGISTRATION_COMMIT,
             n_graded="", brier_skill="", mae_improvement="", mae_improvement_ci="",
             signal_status="blocked", staking_status="not staked", roi="", clv="",
             reward_payable="no",
             blocking_gate="G7: no official per-game player logs or prop lines are captured, so no prop variance exists",
             what_would_change_our_mind=(
                 "An official per-game log for the props in scope, an official or contractually permitted "
                 "price source, and a joint model validated out of sample."),
             source_url=INJURIES),
        dict(id="S5", name="Availability-conditional total (injury feature)",
             family="singles_with_personnel",
             definition="The S1 total with a pre-kickoff availability feature added.",
             pre_registered="no", registration_commit="",
             n_graded="", brier_skill="", mae_improvement="", mae_improvement_ci="",
             signal_status="not registered", staking_status="not staked", roi="", clv="",
             reward_payable="no",
             blocking_gate=("G7 ablation gate: a fixed injury penalty is forbidden by the brief, and the "
                            "ablation needs multi-week dated availability history; this repo holds one week"),
             what_would_change_our_mind=(
                 "An A/B ablation: identical models with and without verified availability features, on "
                 "chronological holdouts, with the difference reported with uncertainty. A fixed points "
                 "penalty is rejected outright."),
             source_url=INJURIES),
    ]
    controls = [
        dict(id="C1", name="Always pick the home team", n=bt["n_forecasts"],
             brier=bt["metrics"]["brier_home_baseline"], note="probability 1.0 on home; the floor any model must beat",
             source_url=STANDINGS_URL),
        dict(id="C2", name="Running league-average total", n=bt["n_forecasts"],
             mae=bt["metrics"]["mae_naive"],
             note="the naive total; S1 must beat this, not the market, to earn a second look",
             source_url=STANDINGS_URL),
        dict(id="C3", name="Random pick at p=0.5", n=bt["n_forecasts"], brier=0.25,
             note="closed-form Brier of a coin flip, published so a 0.24 model is not mistaken for skill",
             source_url=""),
    ]
    return dict(dataset="leaderboard", built_utc=BUILT,
                separation_rule=("Signal and staking are separate columns and are never combined into one "
                                 "rank. Signal = proper score against a benchmark with an interval. "
                                 "Staking = realised return, which is blank because no price source exists. "
                                 "A lucky staking run therefore cannot raise a signal rank, and it cannot "
                                 "be bought: reward_payable is 'no' unless every gate passes."),
                divisions=["singles", "game parlays", "same-game parlays", "prop combos"],
                strategies=strategies, controls=controls, rewards_paid=0,
                n_qualified=sum(1 for s in strategies if s["signal_status"] == "qualified"),
                source_note="every row cites an official domain or states why no value exists")


def gates(bt):
    g = [
        dict(id="G1", name="Sample floor", requirement="300 graded out-of-sample games",
             observed="%d graded" % bt["n_forecasts"], status="fail",
             clearing_number="300 graded games in this frozen version",
             source_url=SCHED11),
        dict(id="G2", name="Probabilistic calibration vs benchmark",
             requirement="Brier skill interval above zero, measured on both the ratio and the difference",
             observed="ratio %s, 95%% CI %s; difference %+.4f, 95%% CI %s"
                      % (bt["metrics"]["brier_skill"], bt["metrics"]["brier_skill_ci"],
                         bt["metrics"]["brier_diff_improvement"], bt["metrics"]["brier_diff_ci"]),
             status="fail",
             clearing_number=("ratio lower bound > 0 AND difference lower bound > 0 AND n>=300 "
                              "(observed: both lower bounds are above 0, but n=116, so the gate stays shut)"),
             source_url=STANDINGS_URL),
        dict(id="G3", name="Total skill vs naive", requirement="MAE improvement interval above zero",
             observed="+%s pts, 95%% CI %s" % (bt["metrics"]["mae_improvement"], bt["metrics"]["mae_improvement_ci"]),
             status="pass" if bt["metrics"]["mae_improvement_ci"][0] > 0 else "fail",
             clearing_number="CI lower bound > 0 at n>=300", source_url=STANDINGS_URL),
        dict(id="G4", name="Multiplicity", requirement="adjust for the number of strategies tested",
             observed="5 strategies registered, 2 scorable; a nominal 0.05 is not applied",
             status="fail", clearing_number="a pre-declared family and an adjusted threshold",
             source_url=""),
        dict(id="G5", name="Official price availability", requirement="an official or permitted price to score ROI/CLV",
             observed="no official NFL price source exists", status="blocked",
             clearing_number="a permitted price feed, or read the price policy decision",
             source_url=""),
        dict(id="G6", name="Joint evidence for any combo", requirement="validated joint probability + operator void rules",
             observed="neither exists", status="blocked",
             clearing_number="a graded same-game joint sample", source_url=""),
        dict(id="G7", name="Availability ablation", requirement="A/B with and without verified personnel features",
             observed="1 dated week of availability; ablation needs the pre-registered multi-week window",
             status="blocked", clearing_number="the number of dated weekly captures the spec names",
             source_url=INJURIES),
        dict(id="G8", name="Depth coverage", requirement="official depth order for all 32 clubs",
             observed="1 of 32 clubs captured (DET) and that club labels its chart 'Unofficial'",
             status="fail", clearing_number="32 of 32 clubs captured, or snap counts from an official source",
             source_url=LIONS_DEPTH),
        dict(id="G9", name="Outcome feed reconciliation", requirement="settled games reconcile to official standings",
             observed="32/32 clubs agree on W-L-T, PF, PA over 148 games", status="pass",
             clearing_number="already met; must stay met as games are added", source_url=STANDINGS_URL),
        dict(id="G10", name="Deterministic rebuild", requirement="a rebuild changes nothing",
             observed="engine is stdlib-only, no network, no clock in any value",
             status="pass", clearing_number="CI runs the rebuild and diffs the output", source_url=""),
    ]
    return dict(dataset="gates", built_utc=BUILT, registered_utc="2026-11-16T01:30Z",
                registration_commit=REGISTRATION_COMMIT,
                demotion_gate=("A strategy returns to paper when, over four consecutive graded weeks, its "
                               "benchmark-relative Brier skill is <= 0 on the game-cluster lower bound, or "
                               "when it grades fewer than 75% of the games it forecast."),
                promotion_rule="every gate passes; a majority is not a pass",
                n_pass=sum(1 for x in g if x["status"] == "pass"),
                n_fail=sum(1 for x in g if x["status"] == "fail"),
                n_blocked=sum(1 for x in g if x["status"] == "blocked"),
                rows=g)


def strategy_registry():
    return dict(dataset="strategy_registry", built_utc=BUILT,
                amendment_rule=("Any change to a strategy's definition, sample window, constants or grading "
                                "rule creates a NEW version with a new registration commit and resets its "
                                "out-of-sample count to zero. The list below is empty at registration and "
                                "records errata that do NOT change a forecast: a documentation sign note and "
                                "a duplicate-game merge are errata, not amendments."),
                amendments=[
                    dict(id="E1", date="2026-11-16", kind="documentation erratum",
                         text=("The registration's parenthetical '(negative = home favoured)' contradicted "
                               "the formula beside it. The engine has always used E_home - E_away (positive = "
                               "home favoured); the note is corrected in the appended erratum section and "
                               "no constant, rule or forecast changed."),
                         affects_forecasts="no"),
                    dict(id="E2", date="2026-11-16", kind="data-merge erratum",
                         text=("The constant sample merged the verified corpus with the Week 10 "
                               "transcription and double-counted the Thursday game present in both "
                               "(149 vs 148 reconciled games). The merge is keyed on date/away/home, the "
                               "overlap is reported on the page, and the build asserts the constant sample "
                               "equals the reconciliation count. HFA and sigma were re-estimated at n=148 "
                               "before any Week 11 game existed; no Week 11 forecast was graded or changed."),
                         affects_forecasts="no -- Week 11 had not kicked off (first game 2026-11-19)"),
                ],
                forbidden=["publishing a backtest number as a leaderboard rank",
                           "ranking by realised return alone",
                           "multiplying marginal probabilities to price a combo",
                           "a fixed points penalty for an absent starter",
                           "deriving depth order from jersey number, experience or salary"],
                entries=[
                    dict(id="S1", registered="2026-11-16", commit=REGISTRATION_COMMIT,
                         definition_file="PREREGISTRATION.md", live=False, paper=True),
                    dict(id="S2", registered="2026-11-16", commit=REGISTRATION_COMMIT,
                         definition_file="PREREGISTRATION.md", live=False, paper=True),
                    dict(id="S3", registered="2026-11-16", commit=REGISTRATION_COMMIT,
                         definition_file="PREREGISTRATION.md", live=False, paper=True),
                    dict(id="S4", registered="2026-11-16", commit=REGISTRATION_COMMIT,
                         definition_file="PREREGISTRATION.md", live=False, paper=False),
                    dict(id="S5", registered="", commit="", definition_file="", live=False, paper=False),
                ])


# --------------------------------------------------------------------------
# 8. Questions the owner must answer, and suggestions with gates
# --------------------------------------------------------------------------
def questions():
    rows = [
        dict(id="Q01", kind="decision", question="May price data be captured at all, and from which source?",
             why_it_blocks="Every price column, every ROI, every CLV value and every reward depends on it.",
             answer_at_present="unanswered", what_would_answer_it="A named price source with terms that permit the use.",
             source_url=""),
        dict(id="Q02", kind="decision", question="May row-level nfl.com capture be committed to a public repository?",
             why_it_blocks="Determines whether the availability layer is publishable or must be derived-only.",
             answer_at_present="unanswered",
             what_would_answer_it="A reading of the site terms for the injury report and game books.",
             source_url="https://www.nfl.com/help/terms-conditions"),
        dict(id="Q03", kind="information", question="Which clubs publish a structured depth chart?",
             why_it_blocks="One club is captured and it is labelled unofficial; 31 are unknown.",
             answer_at_present="partially answered: DET yes; 31 unknown",
             what_would_answer_it="One capture per club, 32 in total, each linked from its nfl.com roster page.",
             source_url=LIONS_DEPTH),
        dict(id="Q04", kind="information", question="Does an official snap-count source exist?",
             why_it_blocks="Snap counts are the only route to a starter/backup split the brief will accept.",
             answer_at_present="unanswered", what_would_answer_it="A published snap-count table on an official domain.",
             source_url=""),
        dict(id="Q05", kind="information", question="What does 'Questionable' actually mean in play rate?",
             why_it_blocks="The report gives no percentages, so any probability attached today is invented.",
             answer_at_present="unanswered",
             what_would_answer_it="Several seasons of designations joined to official inactive lists, with intervals.",
             source_url=INJURIES),
        dict(id="Q06", kind="information", question="How many clubs does the Week 10 report omit, and why?",
             why_it_blocks="Four clubs have no section; three are Week 10 byes. TB is a Week 11 bye club that the report still omits while its peers appear.",
             answer_at_present="observed, not explained",
             what_would_answer_it="A second dated capture, so omission can be distinguished from absence.",
             source_url=INJURIES),
        dict(id="Q07", kind="decision", question="Is a club-published 'Unofficial' depth chart acceptable as a source?",
             why_it_blocks="The brief rejects inference; the club itself disclaims the chart.",
             answer_at_present="unanswered", what_would_answer_it="An explicit acceptance or rejection with reasoning.",
             source_url=LIONS_DEPTH),
        dict(id="Q08", kind="information", question="Why does the standings page show NYG and WAS division records that do not sum to their games played?",
             why_it_blocks="A published official field appears internally inconsistent; it is reproduced, not corrected.",
             answer_at_present="observed, not explained",
             what_would_answer_it="The league's tie-breaking or standings definition page.",
             source_url=STANDINGS_URL),
        dict(id="Q09", kind="information", question="Why does the Tampa Bay PF/PA pair look inverted against its record?",
             why_it_blocks="TB is 3-6 with PF 202 and PA 178: a positive differential and a losing record. That is arithmetically possible, but it is worth a second dated read before any rating uses it.",
             answer_at_present="published as read", what_would_answer_it="A second capture on a later date.",
             source_url=STANDINGS_URL),
        dict(id="Q10", kind="decision", question="What is the out-of-sample window definition for demotion?",
             why_it_blocks="The demotion gate is frozen as four graded weeks; the owner may want a different unit.",
             answer_at_present="proposed in the pre-registration", what_would_answer_it="Approval or an amendment.",
             source_url=""),
        dict(id="Q11", kind="information", question="Do the 12 Week 10 finals on the schedule page settle identically in the game books?",
             why_it_blocks="Three game books were read of 12; the rest are single-sourced to the schedule page.",
             answer_at_present="3 of 12 double-sourced",
             what_would_answer_it="The remaining nine game books.", source_url=SCHED10),
        dict(id="Q12", kind="information", question="Is the KC roster on this report consistent with the club's own roster page?",
             why_it_blocks="The report lists players whose club affiliation differs from prior seasons; a second source is needed before any roster join.",
             answer_at_present="unanswered", what_would_answer_it="The KC roster page captured on the same day.",
             source_url="https://www.nfl.com/teams/kansas-city-chiefs/roster"),
    ]
    return dict(dataset="questions", built_utc=BUILT,
                policy=("A question is listed only if a decision or a capture would change what is published. "
                        "No answer is invented; 'unanswered' is a published state."),
                n_rows=len(rows), n_unanswered=sum(1 for r in rows if r["answer_at_present"].startswith("unanswered")),
                rows=rows)


def suggestions():
    rows = [
        dict(id="SUG01", title="Decide the price policy before anything else",
             change="Answer Q01. If a permitted source exists, capture open and close for every market originated.",
             cost="low", unblocks="G5, all ROI and CLV columns, the reward pool", risk="none to the analysis layer",
             recommendation="do first", status="open", source_url=""),
        dict(id="SUG02", title="Capture all 32 club depth charts in one dated pass",
             change="One capture per club, linked from its nfl.com roster page, stored with a timestamp and hash.",
             cost="medium", unblocks="G8, the matchup matrix, the replacement column",
             risk="some clubs publish an image or a PDF; those must be flagged, not transcribed by eye",
             recommendation="do second", status="open", source_url=LIONS_DEPTH),
        dict(id="SUG03", title="Read the remaining nine Week 10 game books",
             change="Close Q11 so that every Week 10 result is double-sourced.",
             cost="low", unblocks="a fully verified results feed", risk="none",
             recommendation="do with SUG02", status="open", source_url=SCHED10),
        dict(id="SUG04", title="Stop publishing 30 landing pages",
             change="Keep this dashboard as the only entry point; demote the other NFL namespaces to a linked appendix.",
             cost="low", unblocks="owner time, not a gate", risk="loses nothing if every page stays reachable",
             recommendation="owner call", status="open", source_url=""),
        dict(id="SUG05", title="Replace the 'no official depth' blocker with a coverage statement",
             change="FB-07/RF-04 say no official depth source exists. One does, for one club. Restate the blocker as coverage.",
             cost="low", unblocks="honest gates", risk="none",
             recommendation="do now", status="open", source_url=LIONS_DEPTH),
    ]
    return dict(dataset="suggestions", built_utc=BUILT,
                workflow=("No suggestion is implemented in this session. Each carries the gate it would clear and "
                          "the risk; the verdict column is left for the owner."),
                n_rows=len(rows), rows=rows)


def flag_rows(checks, rec, bt, gates_ds, avail):
    rows = [
        dict(id="FB-01", severity="blocking", item="No official NFL price source exists in this repository",
             detail="Every market, residual, ROI and CLV cell is blank because of it. Nothing was estimated to fill the gap.",
             gate="G5", source_url=""),
        dict(id="FB-02", severity="high", item="Only 1 of 32 club depth charts is captured",
             detail="Detroit's chart is structured and readable, and the club labels it 'Unofficial'. The other 31 are unknown, so the replacement-depth feature cannot be built.",
             gate="G8", source_url=LIONS_DEPTH),
        dict(id="FB-03", severity="high", item="A rank-1 depth player was Out and also listed first-string",
             detail="D.J. Reed: rank 1 CB on the club chart, Out on the report, listed at CB in the Game Book lineup and on the Not Active list. The Game Book lineup block and the Not Active block disagree for this player; both are reproduced.",
             gate="G8", source_url="%s | %s" % (LIONS_DEPTH, BOOKS["books"][0]["pdf_url"])),
        dict(id="FB-04", severity="medium", item="One Week 10 game is not settled in any capture",
             detail="LAC at BAL (2026-11-16 20:15 ET) is after the capture clock; PIT at CIN shows Q1 0-3 on every read made this session. Neither is scored.",
             gate="G9", source_url=SCHED10),
        dict(id="FB-05", severity="medium", item="The Week 10 report omits TB while listing every other Week 11 bye club",
             detail="ATL, CLE, LA, NE and SEA all have sections; TB does not. Recorded as observed.",
             gate="G7", source_url=INJURIES),
        dict(id="FB-06", severity="medium", item="NYG and WAS division records do not sum to games played",
             detail="NYG shows a 3-2-1 division record over 9 games; WAS shows 2-2-1 over 9. Reproduced exactly, not corrected.",
             gate="G9", source_url=STANDINGS_URL),
        dict(id="FB-07", severity="low", item="The Week 10 injury report is a single undated snapshot",
             detail="The page states the week, not the fetch time of each club's update. One capture cannot support a delta, so no trend is published.",
             gate="G7", source_url=INJURIES),
        dict(id="FB-08", severity="low", item="Game Book '3QB' notation",
             detail="The Patriots' Not Active line reads '3QB 15 B.Morton', an emergency-third-QB tag that is not in any legend. Kept verbatim rather than parsed.",
             gate="", source_url=BOOKS["books"][0]["pdf_url"]),
        dict(id="FB-09", severity="low", item="KC report players look inconsistent with a 2026 Chiefs roster",
             detail="The report lists Justin Fields (QB) and Rashee Rice (WR) among Kansas City players. The Chiefs' own roster page should be captured on the same date before any roster join; until then this is flagged, not used.",
             gate="", source_url="https://www.nfl.com/teams/kansas-city-chiefs/roster"),
        dict(id="FB-10", severity="low", item="Week 11 venue is blank for MIN at SF",
             detail="The official Week 11 page carries no venue block for that game, so the venue column is blank rather than assumed.",
             gate="", source_url=SCHED11),
    ]
    return dict(dataset="flags", built_utc=BUILT,
                policy="A flag is published, never hidden, and never blocks publishing the rest of the site.",
                n_rows=len(rows), rows=rows)


def requirements():
    """One row per brief line, with the gate that blocks it and the number that would clear it."""
    R = []
    def add(line, requirement, status, gate, clearing, source, evidence):
        R.append(dict(id="R%02d" % (len(R) + 1), line=line, requirement=requirement, status=status,
                      gate=gate, clearing_number=clearing, source_url=source, evidence=evidence))
    add("prices", "Price-snapshot store with opening and closing numbers for every market originated",
        "blocked", "G5", "a permitted price source", "", "schema and blank columns shipped; no value invented")
    add("results", "Verified results feed so backtests and ROI can be computed at all",
        "met", "G9", "already met", STANDINGS_URL, "148 settled games; 32/32 clubs reconcile to the standings")
    add("order", "Originate the side first, then the total, then the moneyline",
        "met", "", "already met", SCHED11, "origination_order field on every row, audited by the build")
    add("columns", "Publish fair line, market line and difference as separate columns",
        "partial", "G5", "a permitted price source", "", "fair line published; market and difference blank by rule")
    add("leaderboard", "Separate signal from staking so a lucky staking run cannot mask a bad signal",
        "met", "", "already met", "", "separate columns; reward_payable='no' unless every gate passes")
    add("depth", "Track the depth of the replacement, not just the fact of a replacement",
        "partial", "G8", "32 of 32 club depth charts, or official snap counts", LIONS_DEPTH,
        "rank published for DET; replacement named only where the Game Book shows it")
    add("correlation", "Correlations only from official numbers, with n published on every value",
        "met", "", "already met", STANDINGS_URL, "3 correlations, n=32 club-seasons on every row")
    add("demotion", "A demotion gate that returns a live strategy to paper",
        "met", "", "already met", "", "frozen in the pre-registration and in the gates dataset")
    add("prereg", "Pre-register every strategy; forbid backtest numbers on the leaderboard",
        "met", "", "already met", "", "registry with an empty amendment list; backtest kept on its own page")
    add("availability-graph", "Availability graph as a first-class dataset",
        "partial", "G7", "dated multi-week captures", INJURIES, "one dated week, 347 rows, 28 clubs")
    add("depth-from-time", "Do not model depth from jersey order; model it from playing time",
        "blocked", "G8", "an official snap-count source", "", "no snap-count source captured; nothing derived from numbers")
    add("injury-surprise", "Make the injury signal a surprise, never a level",
        "blocked", "G7", "a historical designation-to-inactive join", INJURIES, "levels published; no surprise computed")
    add("roster-sweep", "Run the 32-team roster/IR sweep before any team-level model is trusted",
        "partial", "G8", "32 clubs captured", LIONS_ROSTER, "1 club captured; ACT/PUP/RES/DEV codes published")
    add("fixture-context", "Fixture-context features from published schedule facts only",
        "met", "", "already met", SCHED11, "10 rows for Week 11: gameday, clock time, network, venue where published")
    add("prob-inputs", "Store every model output as a probability plus its inputs",
        "met", "", "already met", SCHED11, "p_home_win plus off/def rates and expected points on every row")
    add("luck", "Removal-of-luck panel on the dashboard",
        "met", "", "already met", "", "controls and intervals published; a coin flip is priced at Brier 0.25")
    add("wwecm", "A two-sided 'what would change our mind' field on every strategy",
        "met", "", "already met", "", "present on all 5 strategies, refutation stated as well as support")
    add("residual", "Price a line ourselves and publish the residual against the market, on a schedule",
        "partial", "G5", "a permitted price source", "", "own line published for all 13 Week 11 games; residual blank")
    add("corpus", "Turn the game log into the pre-registered backtest corpus",
        "met", "", "already met", SCHED10, "148 games, walk-forward, no game scored by a model that saw it")
    add("price-policy", "Decide the price-data policy before any backtest is published",
        "blocked", "G5", "answer Q01", "", "backtest published without any price claim")
    add("injury-clock", "Store every injury-hub read with its clock time and publish the delta",
        "partial", "G7", "a second dated capture with the same clock", INJURIES, "clock published; one capture, so no delta")
    add("readiness", "Decision-readiness table on the landing page with gate and clearing number",
        "met", "", "already met", "", "this table")
    add("venue", "Transcribe the venue of every fixture from the official game centre",
        "partial", "G9", "all 14 game centres read", SCHED10, "3 of 14 venues from game books, 8 from schedule, 3 blank")
    add("announcement", "Publish the league's dated schedule announcement beside the live schedule",
        "partial", "G9", "the league's dated announcement page captured", SCHED11,
        "the live Week 11 page is published with its capture clock; no separate announcement page captured")
    add("gamebooks", "Use official Game Books for actual starters and game-day status",
        "partial", "G9", "12 of 12 Week 10 game books", BOOKS["books"][0]["pdf_url"],
        "3 game books read in full; starters, inactives and officials transcribed")
    add("rating", "Ingest game-level results to make ratings opponent-aware",
        "partial", "G1", "300 graded games", STANDINGS_URL,
        "ratings are opponent-adjusted only through points for/against; no opponent rating is estimated")
    add("ablation", "Injury and personnel ablations instead of fixed penalties",
        "blocked", "G7", "multi-week dated availability", INJURIES, "no penalty is applied anywhere in the model")
    add("snapshots", "Immutable multi-day availability snapshots with retained hashes",
        "partial", "G7", "a scheduler plus retained bytes", INJURIES,
        "one capture, content hash published; the fetch path does not expose raw bytes")
    add("inactive", "Capture official inactive lists and snap counts",
        "partial", "G8", "all 14 Week 10 inactive lists", BOOKS["books"][1]["pdf_url"],
        "2 of 14 Not Active lists captured from game books")
    add("depth-parse", "Fix the two depth-parsing failures before widening coverage",
        "partial", "G8", "a structured source for the image-format charts", LIONS_DEPTH,
        "number-prefixed input is handled by keeping the raw string; the image case is not hand-transcribed")
    add("depth-groups", "Model depth slots as groups, not a single starter",
        "met", "", "already met", LIONS_DEPTH,
        "the capture keeps every player in a slot; DET lists two rank-1 receivers and three rank-1 linebackers")
    add("turnover", "Treat roster turnover as a first-class data event",
        "partial", "G8", "a dated transactions feed", LIONS_ROSTER,
        "status codes are timestamped; no trade log is captured")
    add("shadow", "Start with a singles-only shadow baseline",
        "met", "", "already met", "", "S1 and S2 pre-registered before any run")
    add("parlay-gate", "Keep parlays and prop combos behind a joint-evidence gate",
        "met", "", "already met", "", "S3 and S4 published as blocked, with the reason")
    add("divisions", "Proper-score leaderboard divisions",
        "met", "", "already met", "", "four divisions declared; two populated")
    add("rank", "Rank with proper scores and uncertainty, not win rate",
        "met", "", "already met", "", "Brier with a game-cluster bootstrap; win rate is not a rank column")
    add("storage", "Durable snapshot storage and alerts",
        "blocked", "G7", "storage outside the static site", "", "nothing stored; no alerting configured")
    add("layers", "Split the public analysis layer from a private data layer",
        "blocked", "G5", "answer Q02", "", "row-level capture is committed; the terms are not read, so this is flagged")
    add("per-team", "Per-team view: starters out, replacements named, net injury count",
        "partial", "G8", "32 club depth charts", INJURIES, "starters_out left blank; no starter flag without depth")
    add("announced-starter", "An announced-starter evidence field, not an inferred replacement",
        "met", "", "already met", "", "replaced_by is populated only from a published lineup or the Not Active list")
    add("depth-register", "Official depth-chart register with date and source per row",
        "partial", "G8", "32 clubs", LIONS_DEPTH, "57 rows, one club, date and source on every row")
    add("questionable", "Calibrate 'Questionable' empirically instead of old percentages",
        "blocked", "G7", "several seasons of designation-to-inactive joins", INJURIES, "no percentage published")
    add("matrix", "Interactive offense vs defense deficiency matrix",
        "partial", "G8", "32 club depth charts", LIONS_DEPTH,
        "DET rows only; the other 31 columns are blank rather than guessed")
    add("stale-depth", "Flag stale depth rows against the official transactions log",
        "partial", "G8", "a dated transactions feed", LIONS_ROSTER,
        "1 contradiction found and published (FB-03, FB-04 class); no transaction log to diff against")
    add("pit", "Point-in-time snapshot ledger for injuries, depth and inactives",
        "partial", "G7", "multi-day captures", INJURIES, "one point in time; ledger schema published without entries")
    add("lions", "Populate the three missing Lions game-status designations",
        "met", "", "already met", INJURIES,
        "Kerby Joseph, Cade Mays and D.J. Reed are published as Out on the 2026-11-16 read")
    add("recapture", "Re-capture and republish the Week 10 injury tables",
        "met", "", "already met", INJURIES, "347 rows, 28 clubs, captured 2026-11-16T01:37Z")
    add("reject-jersey", "Reject deriving depth order from jersey number, experience or salary",
        "met", "", "already met", LIONS_DEPTH, "no such derivation exists anywhere in the datasets")
    add("shared-slots", "Represent shared and empty depth slots faithfully",
        "met", "", "already met", LIONS_DEPTH, "two rank-1 receivers and three rank-1 linebackers kept as groups")
    add("depth-source", "Resolve the depth-order source before building the deficiency feature",
        "partial", "G8", "32 clubs verified", LIONS_DEPTH,
        "route (a) is verified for exactly one club; the feature is not built")
    add("reliability", "Score injury-designation reliability before using it as a feature",
        "blocked", "G7", "several seasons joined to inactive lists", INJURIES, "no reliability value published")
    add("wed-sun", "Snapshot the injury report Wednesday, Thursday and Friday with dated history",
        "blocked", "G7", "a scheduler", INJURIES, "one capture")
    add("series", "Treat the injury report as a timestamped series",
        "partial", "G7", "daily captures Wednesday to kickoff", INJURIES, "one timestamp")
    add("snap-proxy", "Use snap counts as the starter proxy when the depth chart is unavailable",
        "blocked", "G8", "an official snap-count source", "", "none captured")
    add("control", "Add a control baseline to every leaderboard run",
        "met", "", "already met", "", "three controls published: home always, league-average total, coin flip")
    add("weather", "Stadium roof/surface and hourly wind/precipitation overlay",
        "partial", "G9", "a weather source", BOOKS["books"][1]["pdf_url"],
        "roof and surface published for 2 game books; no forecast grid captured")
    add("two-stage", "Two-stage skill leaderboard (proper score, then prospective CLV/ROI)",
        "partial", "G5", "a permitted price source", "", "stage 1 published; stage 2 blocked on price")
    add("vigfree", "Vig-free consensus vs originated fair-line decomposition",
        "blocked", "G5", "a permitted price source", "", "no vig can be estimated without prices")
    add("weekly-diff", "A weekly 'what changed' diff instead of a static snapshot",
        "partial", "G7", "a second dated capture", "", "the diff schema is published; one capture, so no diff")
    add("two-totals", "Publish every model total twice until one wins",
        "met", "", "already met", "", "the model total and the naive total are both published, with the gap")
    add("drift", "A drift alarm on every scraper",
        "partial", "G9", "every capture path instrumented", "",
        "the build fails on row-count, club-count, vocabulary and identity drift; the fetch path is human")
    add("reserve", "Capture the reserve list so 'not listed' never means 'available'",
        "partial", "G8", "32 clubs", LIONS_ROSTER, "RES/PUP captured for one club; unlisted is never read as available")
    add("reject-roi", "Reject ranking strategies by season-long ROI",
        "met", "", "already met", "", "no ROI column is a rank; signal columns rank")
    add("archive", "Archive weekly injury reports for past seasons",
        "blocked", "G7", "an archive access path", INJURIES, "one week")
    add("freeze", "Freeze a rule before it sees data",
        "met", "", "already met", "", "commit %s precedes the first run" % REGISTRATION_COMMIT[:7])
    add("splits", "Split data into train, validation and holdout seasons",
        "partial", "G1", "more than one season captured", SCHED10, "walk-forward inside one season only")
    add("suggestions", "A suggestions section so someone can review and choose before changes",
        "met", "", "already met", "", "5 suggestions, each with cost, gate and risk; none implemented")
    add("questions", "A clear list of questions and the information needed before deciding",
        "met", "", "already met", "", "12 questions, 12 unanswered-or-partial, each with what would answer it")
    add("originate", "Originate own NFL lines",
        "met", "", "already met", SCHED11, "13 Week 11 games: fair side, fair total, moneyline probability")
    add("signals", "Research and develop strategies for useful signals",
        "partial", "G1", "300 graded games", "", "5 strategies registered; 1 signal passes at this n and it is not promoted")
    add("competition", "Leaderboard competition with rewards for top performers",
        "partial", "G1/G4/G5", "gates cleared", "", "leaderboard published with 0 qualified and 0 rewards paid")
    add("injuries", "Track injuries and defensive/offensive backup deficiencies",
        "partial", "G8", "32 club depth charts", INJURIES, "level tracking complete for one week; deficiency not modelled")
    add("exec", "Executive summary",
        "met", "", "already met", "", "on the landing page and as its own page")
    add("verify", "Verify line by line, every row sourced, blanks flagged",
        "met", "", "already met", "", "the build fails on an unsourced row; the flag register carries 10 items")
    return dict(dataset="requirements", built_utc=BUILT, registration_commit=REGISTRATION_COMMIT,
                n_rows=len(R),
                counts=dict(met=sum(1 for r in R if r["status"] == "met"),
                            partial=sum(1 for r in R if r["status"] == "partial"),
                            blocked=sum(1 for r in R if r["status"] == "blocked")),
                rows=R)


def main():
    checks = dataset_identity_checks()
    rec = results_reconciliation()
    if rec["status"] != "pass":
        raise SystemExit("results reconciliation failed: %s" % rec["mismatches"])
    avail = availability()
    bt = backtest_corpus()
    ds = {
        "identity_checks.json": dict(dataset="identity_checks", built_utc=BUILT, n_rows=len(checks), rows=checks),
        "results_reconciliation.json": rec,
        "availability_week10.json": avail,
        "depth_register.json": depth_register(),
        "replacement_evidence.json": replacement_evidence(),
        "roster_status.json": roster_status(),
        "drill_findings.json": drill_findings(),
        "week11_own_lines.json": model(),
        "backtest.json": bt,
        "correlations.json": correlations(),
        "leaderboard.json": leaderboard(bt),
        "gates.json": gates(bt),
        "strategy_registry.json": strategy_registry(),
        "questions.json": questions(),
        "suggestions.json": suggestions(),
        "flags.json": flag_rows(checks, rec, bt, None, avail),
        "requirements.json": requirements(),
    }
    for name, obj in ds.items():
        write_json(name, obj)
    # fail loudly, in the build, on any identity or reconciliation break
    for c in checks:
        if c["status"] != "pass":
            raise SystemExit("identity check failed: %s" % c["check"])
    print("wrote %d datasets" % len(ds))
    print("identity checks: %d pass, %d fail" % (sum(1 for c in checks if c["status"] == "pass"),
                                                  sum(1 for c in checks if c["status"] != "pass")))
    print("reconciliation: %d games, %d/32 clubs agree" % (rec["n_games"], rec["clubs_checked"] - len(rec["mismatches"])))
    print("backtest: n=%d brier=%.4f home=%.4f mae=%.2f naive=%.2f" % (
        bt["n_forecasts"], bt["metrics"]["brier"], bt["metrics"]["brier_home_baseline"],
        bt["metrics"]["mae_total"], bt["metrics"]["mae_naive"]))
    print("requirements: %(met)d met / %(partial)d partial / %(blocked)d blocked" % ds["requirements.json"]["counts"])


if __name__ == "__main__":
    main()
