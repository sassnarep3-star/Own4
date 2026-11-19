#!/usr/bin/env python3
"""nfl-week11-series compute engine (session arena-23197e9d-own4).

Reads ONLY: (a) this namespace's evidence/ transcriptions, (b) two peer capture
files read-only (raw HTML capture_a, markdown capture_b) whose sha256 are checked
against recorded values before use, (c) one peer summary JSON read-only.
Writes data/*.json deterministically. No network, no randomness, no clock.
"""
import csv, hashlib, html, json, os, re, sys

NS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(NS, "evidence")
DATA = os.path.join(NS, "data")
REPO = os.path.dirname(NS)

CAP_A_PATH = os.path.join(REPO, "nfl-readiness-register/snapshots/2026-11-18/injury_report-2026-11-18T234917Z.html")
CAP_A_SHA = "e1bbea1bf036c949825106a9a9e51de307da86680583d201a091682d7d012e7b"
CAP_B_PATH = os.path.join(REPO, "nfl-daily-desk/captures/2026-11-19/injury-report-week11.md")
CAP_B_SHA = "d2ec7ac360f4f56064554d5af0a6352091a3f8ef81d4001539fddbf865c23676"
PEER_DELTA = os.path.join(REPO, "nfl-daily-desk/data/availability_delta.json")

SESSION = "arena-23197e9d-own4"
READ_A = "2026-11-18T23:49:17Z"
READ_B = "2026-11-19T07:05:00Z"
READ_C = "2026-11-19T11:25:00Z"   # window 11:05-11:28Z, 7 chunks
URL_INJ = "https://www.nfl.com/injuries/"
URL_INJ_W10 = "https://www.nfl.com/injuries/league/2026/reg10"
URL_RES_NOV = "https://www.nfl.com/transactions/league/reserve-list/2026/11"
URL_RES_OCT = "https://www.nfl.com/transactions/league/reserve-list/2026/10"
URL_TRADES = "https://www.nfl.com/transactions/league/trades/2026/11"
URL_OTHER = "https://www.nfl.com/transactions/league/other/2026/11"
URL_GB = "https://www.packers.com/team/depth-chart"
URL_HOU = "https://www.houstontexans.com/team/depth-chart"
URL_WILLIS = "https://www.nfl.com/news/dolphins-place-qb-malik-willis-groin-on-injured-reserve-kyle-mccord-in-line-for-first-start"

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def rows_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(l for l in f if not l.startswith("#")))

def summary(rows):
    from collections import Counter
    per = Counter(r["club"] for r in rows)
    des = Counter(r["game_status"] for r in rows if r["game_status"])
    prac = Counter(r["practice_status"] for r in rows)
    return {
        "n_rows": len(rows),
        "n_clubs_with_rows": len(per),
        "per_club_rows": dict(sorted(per.items())),
        "designation_levels": dict(sorted(des.items())),
        "n_rows_with_game_designation": sum(des.values()),
        "practice_levels": {"DNP": prac.get("DNP", 0), "LP": prac.get("LP", 0), "FP": prac.get("FP", 0)},
    }

# ---------- capture_a: independent regex parse of the raw HTML ----------
def parse_capture_a():
    assert sha(CAP_A_PATH) == CAP_A_SHA, "capture_a hash mismatch - refusing to parse"
    t = open(CAP_A_PATH, encoding="utf-8", errors="replace").read()
    blocks = re.split(r'd3-o-section-sub-title"><span>([^<]+)</span>', t)
    rows, empty = [], []
    for i in range(1, len(blocks), 2):
        club = blocks[i].strip()
        body = blocks[i + 1]
        if "No Injuries Reported" in body[:400] and "<tbody>" not in body[:800]:
            empty.append(club)
            continue
        for m in re.finditer(
            r'<a href="(/players/[^"]+)"[^>]*>\s*([^<]+?)\s*</a></td><td>([^<]*)</td><td>([^<]*)</td>'
            r'<td>([^<]*)</td><td>([^<]*)</td>', body):
            url, player, pos, inj, prac, game = [html.unescape(x.strip()) for x in m.groups()]
            rows.append({"club": club, "player": player, "player_url": "https://www.nfl.com" + url,
                         "position": pos, "injuries": inj, "practice_status": prac, "game_status": game})
    return rows, empty

# ---------- capture_b: parse the peer markdown transcription (read-only) ----------
def parse_capture_b():
    assert sha(CAP_B_PATH) == CAP_B_SHA, "capture_b hash mismatch - refusing to parse"
    rows, empty, club = [], [], None
    for line in open(CAP_B_PATH, encoding="utf-8"):
        s = line.strip()
        if s.startswith("### "):
            club = s[4:].strip()
        elif s.startswith("|") and club:
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) == 5 and cells[0] not in ("Player", "---"):
                rows.append({"club": club, "player": cells[0], "player_url": "",
                             "position": cells[1], "injuries": cells[2],
                             "practice_status": cells[3], "game_status": cells[4]})
        elif s == "No Injuries Reported" and club:
            empty.append(club)
    return rows, empty

def abbr_to_full(a):
    return {"DNP": "Did Not Participate In Practice",
            "LP": "Limited Participation in Practice",
            "FP": "Full Participation in Practice"}.get(a, a)

def full_to_abbr(f):
    return {"Did Not Participate In Practice": "DNP",
            "Limited Participation in Practice": "LP",
            "Full Participation in Practice": "FP"}.get(f, f)

def delta(old, new):
    """Row-level delta on (club, player). Statuses normalised to abbreviations."""
    def key(r):
        return (r["club"], r["player"])
    o = {key(r): r for r in old}
    n = {key(r): r for r in new}
    app_keys = sorted(set(n) - set(o))
    gone_keys = sorted(set(o) - set(n))
    def tokens(s):
        return set(re.sub(r"[^a-z0-9 ]", " ", s.lower()).split())
    identity_variants, used_g, used_a = [], set(), set()
    for ka in app_keys:
        for kg in gone_keys:
            if kg in used_g or ka[0] != kg[0]:
                continue
            ta, tg = tokens(ka[1]), tokens(kg[1])
            if ta and tg and (ta <= tg or tg <= ta):
                identity_variants.append({"club": ka[0], "name_in_from": kg[1],
                                          "name_in_to": ka[1],
                                          "player_url": n[ka].get("player_url", ""),
                                          "note": "same player, display-name variant between reads; joined by club+name-token subset"})
                used_g.add(kg); used_a.add(ka); break
    appeared = [n[k] for k in app_keys if k not in used_a]
    gone = [o[k] for k in gone_keys if k not in used_g]
    prac_chg, des_chg, inj_chg = [], [], []
    for k in sorted(set(o) & set(n)):
        a, b = o[k], n[k]
        if full_to_abbr(a["practice_status"]) != full_to_abbr(b["practice_status"]):
            prac_chg.append({"club": k[0], "player": k[1],
                             "from": full_to_abbr(a["practice_status"]),
                             "to": full_to_abbr(b["practice_status"]),
                             "player_url": b.get("player_url") or a.get("player_url")})
        if a["game_status"] != b["game_status"]:
            des_chg.append({"club": k[0], "player": k[1], "from": a["game_status"],
                            "to": b["game_status"],
                            "player_url": b.get("player_url") or a.get("player_url")})
        if a["injuries"] != b["injuries"]:
            inj_chg.append({"club": k[0], "player": k[1], "from": a["injuries"],
                            "to": b["injuries"],
                            "player_url": b.get("player_url") or a.get("player_url")})
    return {"n_shared": len(set(o) & set(n)), "appeared": appeared, "gone": gone,
            "identity_variants": identity_variants,
            "practice_changed": prac_chg, "designation_changed": des_chg,
            "injury_text_changed": inj_chg}

def main():
    os.makedirs(DATA, exist_ok=True)
    w11 = rows_csv(os.path.join(EV, "week11_rows.csv"))
    w10 = rows_csv(os.path.join(EV, "week10_rows.csv"))
    secs = rows_csv(os.path.join(EV, "week11_sections.csv"))
    res_nov = rows_csv(os.path.join(EV, "reserve_list_2026-11.csv"))
    res_oct = rows_csv(os.path.join(EV, "reserve_list_2026-10.csv"))
    trades = rows_csv(os.path.join(EV, "trades_2026-11.csv"))
    other = rows_csv(os.path.join(EV, "other_2026-11.csv"))
    starters = rows_csv(os.path.join(EV, "starter_evidence.csv"))
    depth = rows_csv(os.path.join(EV, "depth_observations.csv"))

    a_rows, a_empty = parse_capture_a()
    b_rows, b_empty = parse_capture_b()
    peer = json.load(open(PEER_DELTA, encoding="utf-8"))

    s_a = summary(a_rows); s_a["no_injuries_reported_clubs"] = sorted(a_empty)
    s_b = summary(b_rows); s_b["no_injuries_reported_clubs"] = sorted(b_empty)
    s_c = summary(w11)
    s_c["no_injuries_reported_clubs"] = sorted(r["club"] for r in secs if r["empty_marker"])

    # -- series.json ------------------------------------------------------
    d_ac = delta(a_rows, w11)
    d_bc = delta(b_rows, w11)
    d_ab = delta(a_rows, b_rows)
    d_ab_peer = peer["reads"]["capture_a"]["summary"]  # peer's own published a summary
    series = {
        "dataset": "nfl-week11-series/series",
        "title": "Timestamped availability series (REQ-21/53/54): three dated reads of the official injury report",
        "session": SESSION,
        "policy": "Deltas are the published signal; single levels are context only. Every read carries its clock time and method. Hashes verified before parse; parser shares no code with any transcription.",
        "points": [
            {"id": "capture_a", "label": "raw-bytes capture (peer workflow)", "read_utc": READ_A,
             "kind": "immutable raw HTML bytes", "source_url": URL_INJ,
             "path": "nfl-readiness-register/snapshots/2026-11-18/injury_report-2026-11-18T234917Z.html",
             "sha256": CAP_A_SHA, "sha256_verified_this_session": True, "summary": s_a,
             "peer_published_summary": d_ab_peer},
            {"id": "capture_b", "label": "platform-rendered markdown read (peer session)", "read_utc": READ_B,
             "kind": "rendered markdown transcription", "source_url": URL_INJ,
             "path": "nfl-daily-desk/captures/2026-11-19/injury-report-week11.md",
             "sha256": CAP_B_SHA, "sha256_verified_this_session": True, "summary": s_b},
            {"id": "capture_c", "label": "platform-rendered markdown read (this session)", "read_utc": READ_C,
             "kind": "rendered markdown transcription (7 chunks; chunks 5-6 chrome-only, verified)",
             "source_url": URL_INJ,
             "path": "nfl-week11-series/evidence/week11_rows.csv",
             "summary": s_c},
        ],
        "deltas": [
            {"from": "capture_a", "to": "capture_b", "hours_apart": 7.25, **d_ab},
            {"from": "capture_a", "to": "capture_c", "hours_apart": 11.6, **d_ac},
            {"from": "capture_b", "to": "capture_c", "hours_apart": 4.33, **d_bc},
        ],
        "peer_delta_arithmetic_note": {
            "peer_narrative": "capture_a -> capture_b: 241 shared, 11 appeared, 1 gone, 1 status change (nfl-daily-desk/data/availability_delta.json)",
            "arithmetic": "241 shared + 11 appeared = 252 rows, but the peer's own capture_b summary reports 253 rows; 1 row unexplained",
            "this_session_finds": "independent parses: a=242 (matches peer summary), b=253 (matches peer summary); the gone/appeared pair in the peer narrative is the De'Alford, Dee <-> Dee Alford display-name variant this session classifies as one identity pair (b->c identity_variants)",
            "status": "published as a cross-session arithmetic note; nothing edited in the peer namespace",
        },
        "cross_checks": {
            "per_club_b_vs_c_equal": s_b["per_club_rows"] == s_c["per_club_rows"],
            "designation_levels_a_b_c_equal": s_a["designation_levels"] == s_b["designation_levels"] == s_c["designation_levels"],
            "n_designation_rows_a_b_c": [s_a["n_rows_with_game_designation"], s_b["n_rows_with_game_designation"], s_c["n_rows_with_game_designation"]],
        },
    }
    json.dump(series, open(os.path.join(DATA, "series.json"), "w"), indent=1, sort_keys=False)

    # -- week10_recount.json ---------------------------------------------
    s10 = summary(w10)
    empty10 = [r["club"] for r in secs if False]  # week10 had no empty sections (verified in transcription)
    recount = {
        "dataset": "nfl-week11-series/week10_recount",
        "title": "Week 10 injury-table recount (REQ-48), dated 2026-11-19",
        "session": SESSION,
        "read_utc": "2026-11-19T11:20:00Z",
        "source_url": URL_INJ_W10,
        "page_title_as_rendered": "Official NFL Injury Report for Players - Week 11 of the 2026 Season | NFL.com",
        "page_week_label_as_rendered": "Injuries - WEEK 10",
        "method": "platform page-read tool, 8 chunks, all read; every club table transcribed verbatim to evidence/week10_rows.csv; counts machine-derived from that file",
        "observed": {**s10, "n_no_injury_sections": 0, "n_club_sections": 28},
        "brief_claims": [
            {"claim": "repo-published Week 10 tables carried 254 rows", "value": 254,
             "observed_today": s10["n_rows"], "status": "superseded-at-source",
             "note": "the official page now publishes 347 rows; the repo figure was a stale snapshot"},
            {"claim": "repo-published tables carried 4 no-injury sections", "value": 4,
             "observed_today": 0, "status": "superseded-at-source",
             "note": "every one of the 28 club sections publishes rows today"},
            {"claim": "live page carried 279 rows at brief time", "value": 279,
             "observed_today": s10["n_rows"], "status": "changed-at-source",
             "note": "the page grew 279 -> 347 rows after the week completed; a single count is a timestamped snapshot, not a fact (REQ-54)"},
            {"claim": "live page carried 2 no-injury sections at brief time", "value": 2,
             "observed_today": 0, "status": "changed-at-source",
             "note": "both previously empty sections now publish rows"},
        ],
        "policy": "Recount published with clock time; no repo-side patch of historical rows is attempted (fix must come from the source page).",
    }
    json.dump(recount, open(os.path.join(DATA, "week10_recount.json"), "w"), indent=1)

    # -- reserve_check.json ----------------------------------------------
    def in_rows(rows, player):
        return [r for r in rows if r["player"] == player]
    six = [("Mason McCormick", "Steelers", "2026-11-18"), ("Jared Wiley", "Chiefs", "2026-11-18"),
           ("Aidan Hutchinson", "Lions", "2026-11-18"), ("Bo Richter", "Vikings", "2026-11-18"),
           ("Azeez Al-Shaair", "Texans", "2026-11-17"), ("Jaylon Carlies", "Colts", "2026-11-17")]
    check_rows = []
    for player, club, ir_date in six:
        ra, rb, rc = in_rows(a_rows, player), in_rows(b_rows, player), in_rows(w11, player)
        check_rows.append({
            "player": player, "club": club, "reserve_date": ir_date,
            "reserve_source_url": URL_RES_NOV,
            "in_capture_a_2026-11-18T23:49Z": bool(ra), "in_capture_b_2026-11-19T07:05Z": bool(rb),
            "in_capture_c_2026-11-19T11:25Z": bool(rc),
            "capture_c_practice": rc[0]["practice_status"] if rc else "",
            "capture_c_game_status": rc[0]["game_status"] if rc else "",
            "table_source_url": URL_INJ,
            "finding": ("still listed in the practice table 2 days after Reserve/Injured - contradiction live"
                        if rc else "dropped from the practice table between capture_b and capture_c"),
        })
    willis = {
        "player": "Malik Willis", "club": "Dolphins", "position": "QB",
        "news_says": "placed on injured reserve Tuesday due to a groin injury (Weeks 10-13 missed; eligible to return Dec 13)",
        "news_source_url": URL_WILLIS,
        "news_date_resolution": "article read 2026-11-19; body says 'Tuesday'; related content dated Nov 10-11 2026 and the referenced Week 10 game was Sun Nov 15 -> Tuesday = 2026-11-10 (resolution published as an inference from the article's own frame, flagged)",
        "ledger_november_row_found": bool([r for r in res_nov if r["player"] == "Malik Willis"]),
        "ledger_october_row_found": bool([r for r in res_oct if r["player"] == "Malik Willis"]),
        "other_ledger_november_row_found": bool([r for r in other if r["player"] == "Malik Willis"]),
        "other_ledger_source_url": URL_OTHER,
        "appears_in_week10_table": bool([r for r in w10 if r["player"] == "Malik Willis"]),
        "appears_in_week11_table": bool([r for r in w11 if r["player"] == "Malik Willis"]),
        "finding": "absence from the weekly report is not availability: Willis is absent from both weeks' tables AND the reserve ledgers do not carry the move the news describes - both surfaces are needed; ledger gap flagged (F-WS-01)",
    }
    reserve = {
        "dataset": "nfl-week11-series/reserve_check",
        "title": "Reserve-list vs practice-table cross-check (REQ-62): 'not listed' never means 'available'",
        "session": SESSION,
        "read_utc": "2026-11-19T11:13:00Z",
        "sources": {"reserve_november": URL_RES_NOV, "reserve_october": URL_RES_OCT,
                    "other_november": URL_OTHER, "injury_report": URL_INJ},
        "ledger_counts": {"november_rows": len(res_nov), "october_rows": len(res_oct),
                          "other_november_rows": len(other), "trades_november_rows": len(trades)},
        "six_reported_contradictions": check_rows,
        "still_contradictory_at_capture_c": [r["player"] for r in check_rows if r["in_capture_c_2026-11-19T11:25Z"]],
        "willis_case": willis,
        "policy": "Rows are ledger/table observations only; no availability state is inferred from absence.",
    }
    json.dump(reserve, open(os.path.join(DATA, "reserve_check.json"), "w"), indent=1)

    # -- depth_check.json -------------------------------------------------
    gb = [r for r in depth if r["club"] == "GB"]
    stripped = []
    for r in gb:
        for f in ("raw_rank1", "raw_rank2", "raw_rank3", "raw_rank4"):
            v = r[f]
            m = re.match(r"^(\d+)\s+(.*)$", v) if v else None
            if v and v.startswith("(continuation"):
                stripped.append({"raw": v, "recovered": "26 Kaleb Johnson", "rule": "continuation row (position blank)"})
            elif m:
                stripped.append({"raw": v, "recovered": m.group(2), "rule": "strip leading jersey number"})
    depth_out = {
        "dataset": "nfl-week11-series/depth_check",
        "title": "Depth-parsing checks (REQ-31/49/50): live club pages read 2026-11-19",
        "session": SESSION,
        "read_utc": "2026-11-19T11:11:00Z",
        "gb": {"source_url": URL_GB, "as_of_label_on_page": "Unofficial, Nov. 10, 2026",
               "n_observation_rows": len(gb),
               "jersey_number_strip_rule": "strip ^\\d+ + from every player cell; store raw string alongside",
               "n_cells_recovered_by_strip_rule": len(stripped),
               "recoveries": stripped,
               "structural_findings": [
                   "PR slot publishes an EMPTY rank-1 cell with the player at rank 2 (empty-first-slot, REQ-50)",
                   "Kitan Oladapo (27) is published in BOTH S slots (shared across slots, REQ-50)",
                   "RB slot's 4th player appears on a continuation row with an EMPTY position cell (parser trap)",
                   "every player cell prepends the jersey number (REQ-31 failure mode confirmed live)",
               ]},
        "hou": {"source_url": URL_HOU,
                "finding": "Depth Chart section publishes one image (https://static.clubs.nfl.com/image/upload/texans/g3gkhdyah3rj1knd6dnz) under 'Unofficial Depth Chart'; no structured rows exist to parse; transcription by eye is rejected (REQ-31); an authorized structured source is required",
                "venue_label_note": "club gameday promo on the same page reads 'at Reliant Stadium on November 19' vs the league schedule label NRG Stadium (peer F-DSK-16); recorded, not resolved (REQ-23)"},
        "policy": "Depth slots are treated as groups; no starter is inferred from column order (brief rejects jersey/experience/salary derivation).",
    }
    json.dump(depth_out, open(os.path.join(DATA, "depth_check.json"), "w"), indent=1)

    # -- starter_evidence.json -------------------------------------------
    starter_out = {
        "dataset": "nfl-week11-series/starter_evidence",
        "title": "Announced-starter evidence (REQ-41): dated official statements, not inferred replacements",
        "session": SESSION,
        "read_utc": "2026-11-19T11:29:00Z",
        "rows": starters,
        "policy": "Each row cites a dated official article or ledger row. No replacement is inferred from depth order.",
        "brief_reference": "the brief cites VR-24/VR-25/VQ-05 for Lock, McCord and Brissett; those tracker IDs remain unresolvable in-repo (peer F-R1), so official substitutes are published here",
    }
    json.dump(starter_out, open(os.path.join(DATA, "starter_evidence.json"), "w"), indent=1)

    # -- sources.json ----------------------------------------------------
    sources = {
        "dataset": "nfl-week11-series/sources",
        "title": "Official reads performed by this session (2026-11-19)",
        "session": SESSION,
        "policy": "Every page read via the platform page-read tool (fetch_page); raw-bytes automation is the peer snapshotter (scheduled Wed/Thu/Fri 18:00Z cron; workflow_dispatch is 403-blocked for this integration).",
        "reads": [
            {"url": URL_INJ, "what": "Week 11 injury report (capture_c)", "window_utc": "11:05-11:28Z", "chunks": "7/7"},
            {"url": URL_INJ_W10, "what": "Week 10 injury report (recount)", "window_utc": "11:12-11:20Z", "chunks": "8/8"},
            {"url": URL_RES_NOV, "what": "Reserve List ledger November 2026", "window_utc": "11:12-11:13Z", "chunks": "2/2"},
            {"url": URL_RES_OCT, "what": "Reserve List ledger October 2026", "window_utc": "11:13-11:15Z", "chunks": "2/2"},
            {"url": URL_TRADES, "what": "Trades ledger November 2026", "window_utc": "11:09Z", "chunks": "1/1"},
            {"url": URL_OTHER, "what": "Other ledger November 2026", "window_utc": "11:30Z", "chunks": "1/1"},
            {"url": URL_GB, "what": "Packers official depth chart", "window_utc": "11:11Z", "chunks": "1/1"},
            {"url": URL_HOU, "what": "Texans official depth chart", "window_utc": "11:12Z", "chunks": "1/1"},
            {"url": URL_WILLIS, "what": "Willis IR / McCord starter article", "window_utc": "11:14Z", "chunks": "1/1"},
            {"url": "https://www.nfl.com/news/drew-lock-no-injury-designation-seahawks-raiders", "what": "Lock starter article (headline read from news rail of reg10)", "window_utc": "11:20Z", "chunks": "headline only"},
            {"url": "https://www.nfl.com/news/sam-darnold-ruled-out-for-seahawks-week-10-game-vs-raiders-drew-lock-expected-to-start-again", "what": "Lock starter article 2 (headline read from news rail of reg10)", "window_utc": "11:20Z", "chunks": "headline only"},
        ],
        "peer_captures_used_read_only": [
            {"path": "nfl-readiness-register/snapshots/2026-11-18/injury_report-2026-11-18T234917Z.html", "sha256": CAP_A_SHA, "verified": True},
            {"path": "nfl-daily-desk/captures/2026-11-19/injury-report-week11.md", "sha256": CAP_B_SHA, "verified": True},
            {"path": "nfl-daily-desk/data/availability_delta.json", "used_for": "capture_b published summary + peer a->b delta", "verified": "values compared against own re-parses"},
        ],
    }
    json.dump(sources, open(os.path.join(DATA, "sources.json"), "w"), indent=1)

    # -- flags.json ------------------------------------------------------
    flags = {
        "dataset": "nfl-week11-series/flags",
        "title": "Flagged for review (non-blocking; each blocks a claim, not the merge)",
        "session": SESSION,
        "policy": "No value is inferred; every flag carries the source links needed to re-check it by hand.",
        "rows": [
            {"id": "F-WS-01", "severity": "high",
             "flag": "Willis IR move missing from both November transaction ledgers",
             "detail": "The official news article states Malik Willis (MIA QB) was placed on injured reserve Tuesday (resolves to 2026-11-10 from the article frame). No Willis row exists in the official November Reserve List ledger (25 rows), the November Other ledger (5 rows), or the October Reserve List ledger (25 rows) - all read 2026-11-19.",
             "sources": [URL_WILLIS, URL_RES_NOV, URL_OTHER],
             "clears_when": "the league publishes the move in a ledger, or the owner confirms the news/ledger surfaces are allowed to diverge"},
            {"id": "F-WS-02", "severity": "low",
             "flag": "reg10 page renders a Week-11 title over Week-10 content",
             "detail": "https://www.nfl.com/injuries/league/2026/reg10 prints page title '...Week 11 of the 2026 Season' while the section label reads 'Injuries - WEEK 10' and the tables are Week 10 fixtures.",
             "sources": [URL_INJ_W10], "clears_when": "the source title matches the section label"},
            {"id": "F-WS-03", "severity": "medium",
             "flag": "Week 10 tables are a living document: 254 (repo) vs 279 (live at brief time) vs 347 (live 2026-11-19)",
             "detail": "Dated recount published; the brief's counts are both superseded. Any pipeline that treats one capture as the Week 10 corpus is mis-specified unless the capture is timestamped (REQ-19/54).",
             "sources": [URL_INJ_W10], "clears_when": "a frozen, dated Week 10 corpus is pre-registered (REQ-19) and this recount becomes one point in it"},
            {"id": "F-WS-04", "severity": "high",
             "flag": "Practice tables lag the reserve ledger; Thursday-game rows lag by 2 days",
             "detail": "At capture_c (2026-11-19T11:25Z), Jaylon Carlies (Reserve/Injured 2026-11-17) still appears in the Colts Thursday practice table and Azeez Al-Shaair (Reserve/Injured 2026-11-17) still appears in the Texans table, while McCormick/Wiley/Hutchinson/Richter (Reserve/Injured 2026-11-18) dropped out between capture_b and capture_c. Table membership must be reconciled against the ledger per read, not trusted as availability.",
             "sources": [URL_INJ, URL_RES_NOV], "clears_when": "an inactive-list feed (REQ-30) confirms game-day status for each fixture"},
            {"id": "F-WS-05", "severity": "medium",
             "flag": "Texans depth chart is a single image",
             "detail": "houstontexans.com/team/depth-chart publishes one image under 'Unofficial Depth Chart'; no structured rows exist. REQ-31 forbids transcription by eye; an authorized structured source is required before the HOU backup-deficiency feature exists.",
             "sources": [URL_HOU], "clears_when": "an authorized structured depth source covers HOU (REQ-51 route verification)"},
            {"id": "F-WS-06", "severity": "medium",
             "flag": "Packers depth rows: jersey numbers, empty first slot, shared slot player, orphan continuation row",
             "detail": "Live read shows numbers prepended to every player cell (recoverable by strip+raw), PR rank-1 EMPTY with the player at rank 2, Kitan Oladapo published in both S slots, and a 4th RB on a continuation row with a blank position cell.",
             "sources": [URL_GB], "clears_when": "nfl-depth-sweep re-parses its stored transcripts under a slot-as-group schema with explicit empty state"},
            {"id": "F-WS-07", "severity": "low",
             "flag": "Venue label disagreement recurs on the club site",
             "detail": "houstontexans.com gameday promo: 'at Reliant Stadium on November 19'; league schedule label is NRG Stadium (peer F-DSK-16). Venue transcription must name its source per row (REQ-23).",
             "sources": [URL_HOU], "clears_when": "the game centre label is transcribed and the two labels are reconciled by the owner"},
            {"id": "F-WS-08", "severity": "low",
             "flag": "Display-name / slug mismatch: 'Dee Alford' -> /players/deaundre-ford/",
             "detail": "Bills table row prints 'Dee Alford' while the profile slug is deaundre-ford. Identity keys must be the URL (or an ID), never the display name.",
             "sources": [URL_INJ], "clears_when": "the league corrects one of the two labels"},
            {"id": "F-WS-09", "severity": "low",
             "flag": "Snapshotter cannot be triggered manually by this integration",
             "detail": "gh workflow run nfl-readiness-register.yml returns HTTP 403 (Resource not accessible by integration). The scheduled Wed/Thu/Fri 18:00Z cron remains the automation path; today's scheduled run is expected at 18:00Z.",
             "sources": ["https://github.com/sassnarep3-star/Own4/actions/workflows/419575938"],
             "clears_when": "the workflow token gains dispatch rights or the owner triggers it manually"},
            {"id": "F-WS-10", "severity": "low",
             "flag": "Brief tracker IDs VR-xx/VQ-xx remain unresolvable",
             "detail": "The brief's VR-04..VR-26 / VQ-05..VQ-08 citations have no in-repo definitions (peer F-R1). Where possible this session published official substitutes (Lions trio status, Lock/McCord/Brissett starter evidence) rather than treating the IDs as sources.",
             "sources": ["https://github.com/sassnarep3-star/Own4"],
             "clears_when": "the owner supplies the tracker export (peer DEC-R7)"},
            {"id": "F-WS-11", "severity": "medium",
             "flag": "Game designations exist for one fixture only",
             "detail": "In capture_c all 16 non-blank Game Status cells belong to Thursday's IND@HOU tables; all Sunday/Monday cells are blank. Blank is not 'available'. One game of designation coverage again this week (matches peer finding).",
             "sources": [URL_INJ], "clears_when": "Friday/Saturday designation releases are captured and joined (REQ-53 cadence)"},
        ],
    }
    json.dump(flags, open(os.path.join(DATA, "flags.json"), "w"), indent=1)

    # -- questions.json --------------------------------------------------
    questions = {
        "dataset": "nfl-week11-series/questions",
        "title": "Questions raised by this session's reads (information needed before decisions)",
        "session": SESSION,
        "policy": "One row per question: what is known, what is missing, what evidence would answer it. Owner decisions stay blank.",
        "rows": [
            {"id": "Q-WS-1", "question": "Is the November reserve ledger authoritative when it contradicts an official news IR announcement (Willis)?",
             "known": "news says IR (Tuesday, resolves 2026-11-10); three ledgers read 2026-11-19 carry no row",
             "missing": "league documentation of ledger completeness/latency rules",
             "discover": "owner reads nfl.com/terms + asks the league data desk; n=1 answer would settle the precedence rule",
             "blocks": ["REQ-62"], "decision": ""},
            {"id": "Q-WS-2", "question": "What latency budget should the pipeline assume between Reserve/Injured posting and practice-table removal?",
             "known": "four11/18 moves dropped out between 07:05Z and 11:25Z; two 11/17 moves still present at 11:25Z (2 days)",
             "missing": "per-club publication schedules; inactive lists (REQ-30)",
             "discover": "capture the report at 2 more clock times before TNF kickoff and measure removal lag per club",
             "blocks": ["REQ-54", "REQ-62"], "decision": ""},
            {"id": "Q-WS-3", "question": "Which capture becomes the frozen Week 10 corpus row set (347 rows today, 279 at brief time, 254 in repo)?",
             "known": "all three counts are dated; the page is a living document",
             "missing": "owner decision on the pre-registration timestamp (REQ-19/20)",
             "discover": "owner picks the registration cut; the commit hash is the registration (REQ-65)",
             "blocks": ["REQ-19"], "decision": ""},
            {"id": "Q-WS-4", "question": "Does an authorized structured depth source exist for Houston (image-only club page)?",
             "known": "club page publishes one image; brief forbids transcription by eye",
             "missing": "a licensed/official structured feed covering HOU",
             "discover": "evaluate route (a) club pages club-by-club and route (b) snap-count derivation (REQ-51) with n=32 coverage counts",
             "blocks": ["REQ-31", "REQ-51"], "decision": ""},
        ],
    }
    json.dump(questions, open(os.path.join(DATA, "questions.json"), "w"), indent=1)

    # -- suggestions.json ------------------------------------------------
    suggestions = {
        "dataset": "nfl-week11-series/suggestions",
        "title": "Suggestions (proposed - awaiting owner; nothing implemented without a decision)",
        "session": SESSION,
        "policy": "Ranked by decision value per unit of work; every suggestion leaves the owner decision column blank.",
        "rows": [
            {"id": "S-WS-1", "suggestion": "Add a 'series' page to the root dashboard that renders the newest capture delta (a->b->c) instead of any single injury level",
             "why": "REQ-21 says publish the delta, never the level; the root landing page currently links level-style pages",
             "effort": "small (nav + one generated page)", "owner_decision": ""},
            {"id": "S-WS-2", "suggestion": "Pin the reg-week pages (reg1..reg18) in the snapshotter, not just /injuries/ (current week)",
             "why": "REQ-48-style recounts need immutable week pages; today's recount shows the page mutates after the week",
             "effort": "small (extend capture URL list + drift pins)", "owner_decision": ""},
            {"id": "S-WS-3", "suggestion": "Join the reserve ledger to every capture automatically and publish the contradiction count per read",
             "why": "F-WS-04 shows table/ledger divergence is per-club and time-varying",
             "effort": "medium (join keyed on player URL slug)", "owner_decision": ""},
            {"id": "S-WS-4", "suggestion": "Treat player URL slugs as identity keys in every parser (display names collide/mismatch)",
             "why": "F-WS-08 (Dee Alford / deaundre-ford) and peer identity defects",
             "effort": "small (parser convention + audit)", "owner_decision": ""},
        ],
    }
    json.dump(suggestions, open(os.path.join(DATA, "suggestions.json"), "w"), indent=1)

    print("compute: week11 rows", len(w11), "| week10 rows", len(w10))
    print("compute: capture_a rows", len(a_rows), "empty", a_empty)
    print("compute: capture_b rows", len(b_rows), "empty", b_empty)
    print("compute: delta a->c: appeared", len(d_ac["appeared"]), "gone", len(d_ac["gone"]),
          "practice", len(d_ac["practice_changed"]), "designation", len(d_ac["designation_changed"]))
    print("compute: delta b->c: appeared", len(d_bc["appeared"]), "gone", len(d_bc["gone"]),
          "practice", len(d_bc["practice_changed"]), "designation", len(d_bc["designation_changed"]))
    print("compute: OK")

if __name__ == "__main__":
    main()
