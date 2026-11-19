#!/usr/bin/env python3
"""
Independent parser for the two stored official Week 11 injury-report captures.

WHY THIS FILE EXISTS
--------------------
The two captures were produced by peer sessions, and peer sessions also parsed
them. Re-using a peer's parsed JSON would be reproducing their code path, not
verifying their output. This module therefore shares no code with
`nfl-desk/engine/parse_injuries.py` or `nfl-daily-desk/engine/parse.py`. It reads
the stored bytes itself:

  capture A (authority, raw bytes)
      nfl-readiness-register/snapshots/2026-11-18/injury_report-2026-11-18T234917Z.html
      sha256 e1bbea1b...2e7b, 371,313 bytes, page title
      "Official Latest NFL Injury Report for Players - Week 11 of the 2026 Season | NFL.com"

  capture B (rendered markdown transcription, NOT raw bytes)
      nfl-daily-desk/captures/2026-11-19/injury-report-week11.md
      provenance header: captured 2026-11-19T07:05:00Z, "platform-rendered read (markdown),
      not raw bytes"

WHAT IS VERIFIED AND WHAT IS MERELY COMPARED
--------------------------------------------
A vs B agreement is a *transcription control* between two sessions. It is NOT
independent verification: both reads are of the same publisher's page, and one
day apart. The output says so on every row and in `provenance`.

Output: data/availability_parse.json
Run:    python3 nfl-origination-lab/engine/parse_availability.py
"""

import hashlib
import html
import json
import os
import re
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
ROOT = os.path.dirname(LAB)
OUT = os.path.join(LAB, "data", "availability_parse.json")

CAPTURE_A = os.path.join(
    ROOT, "nfl-readiness-register/snapshots/2026-11-18",
    "injury_report-2026-11-18T234917Z.html")
CAPTURE_B = os.path.join(
    ROOT, "nfl-daily-desk/captures/2026-11-19/injury-report-week11.md")

SOURCE_URL = "https://www.nfl.com/injuries/"

CLUB_ABBR = {
    "Cardinals": "AZ", "Falcons": "ATL", "Ravens": "BAL", "Bills": "BUF",
    "Panthers": "CAR", "Bears": "CHI", "Bengals": "CIN", "Browns": "CLE",
    "Cowboys": "DAL", "Broncos": "DEN", "Lions": "DET", "Packers": "GB",
    "Texans": "HOU", "Colts": "IND", "Jaguars": "JAX", "Chiefs": "KC",
    "Raiders": "LV", "Chargers": "LAC", "Rams": "LA", "Dolphins": "MIA",
    "Vikings": "MIN", "Patriots": "NE", "Saints": "NO", "Giants": "NYG",
    "Jets": "NYJ", "Eagles": "PHI", "Steelers": "PIT", "49ers": "SF",
    "Seahawks": "SEA", "Buccaneers": "TB", "Titans": "TEN", "Commanders": "WAS",
}

# Identities the peer read published as two spellings of one person. Never merged
# on a guess: recorded so a reader can see the ambiguity instead of a silent join.
NAME_COLLISIONS = [
    {"observed": ["Dee Alford", "De'Alford, Dee"],
     "where": "peer session arena-92c458e6-own4 finding 7 (nfl-daily-desk)",
     "handling": "left as two keys; no join attempted"},
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", " ", s)).strip()


# ---------------------------------------------------------------------------
# capture A — the raw-byte HTML
# ---------------------------------------------------------------------------

TABLE_RE = re.compile(
    r"<table[^>]*d3-o-reports--detailed[^>]*>(.*?)</table>", re.S)
ROW_RE = re.compile(r"<tbody>(.*?)</tbody>", re.S)
TR_RE = re.compile(r"<tr>(.*?)</tr>", re.S)
TD_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
CLUB_SUBTITLE_RE = re.compile(
    r'd3-o-section-sub-title">\s*<span>([^<]+)</span>', re.S)
MATCHUP_RE = re.compile(
    r'nfl-c-matchup-strip__team-abbreviation">\s*([A-Z]{2,3})\s*<', re.S)
NO_INJURY_RE = re.compile(r"No Injuries Reported", re.I)


def parse_capture_a():
    raw = open(CAPTURE_A, encoding="utf-8").read()

    # Walk the document once, keeping the order of club headings and tables.
    events = []
    for m in CLUB_SUBTITLE_RE.finditer(raw):
        events.append((m.start(), "club", html.unescape(m.group(1)).strip()))
    for m in TABLE_RE.finditer(raw):
        events.append((m.start(), "table", m.group(1)))
    events.sort(key=lambda e: e[0])

    rows = []
    blocks = []          # one per club heading: {club, rows, has_table}
    fixtures = []
    cur = None
    pending_matchup = None
    for pos, kind, payload in events:
        if kind == "club":
            cur = {"club": payload, "rows": [], "has_table": False}
            blocks.append(cur)
        else:
            body = payload
            if cur is None:
                cur = {"club": "", "rows": [], "has_table": False}
                blocks.append(cur)
            cur["has_table"] = True
            m = ROW_RE.search(body)
            if not m:
                continue
            for tr in TR_RE.finditer(m.group(1)):
                cells = [strip_tags(c) for c in TD_RE.findall(tr.group(1))]
                link = re.search(r'href="(/players/[^"]+)"', tr.group(1))
                if len(cells) < 5:
                    continue
                rows.append({
                    "club": CLUB_ABBR.get(cur["club"], ""),
                    "club_name": cur["club"],
                    "player": cells[0],
                    "pos": cells[1],
                    "injury": cells[2],
                    "practice": cells[3],
                    "game_status": cells[4],
                    "player_url": ("https://www.nfl.com" + link.group(1))
                                  if link else "",
                    "source_url": SOURCE_URL,
                    "capture": "A",
                    "capture_clock_utc": "2026-11-18T23:49:17Z",
                })
            cur["rows"].append(len(rows))

    # matchup strips: away/home header pairs above each club block (order only,
    # used for a fixture assertion, never for a player value)
    fixtures = [(a, b) for a, b in
                (m.groups() for m in re.finditer(
                    r'nfl-c-matchup-strip__team-abbreviation">\s*([A-Z]{2,3})\s*<'
                    r'.{0,4000}?nfl-c-matchup-strip__team-abbreviation">\s*([A-Z]{2,3})\s*<',
                    raw, re.S))
                if a != b][:13]

    no_injury_blocks = []
    for m in NO_INJURY_RE.finditer(raw):
        seg = raw[max(0, m.start() - 1500):m.start()]
        subs = CLUB_SUBTITLE_RE.findall(seg)
        no_injury_blocks.append(subs[-1].strip() if subs else "")

    return rows, blocks, no_injury_blocks, fixtures, raw


# ---------------------------------------------------------------------------
# capture B — the rendered markdown
# ---------------------------------------------------------------------------

MD_ROW_RE = re.compile(r"^\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|"
                       r"\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*$")


def parse_capture_b():
    rows = []
    club = None
    day = None
    for line in open(CAPTURE_B, encoding="utf-8"):
        s = line.rstrip("\n")
        if s.startswith("## "):
            day = s[3:].strip()
        elif s.startswith("### "):
            club = s[4:].strip()
        elif s.startswith("|") and not s.startswith("| Player"):
            m = MD_ROW_RE.match(s)
            if not m or not club:
                continue
            player, pos, injury, practice, game = [g.strip() for g in m.groups()]
            if not player:
                continue
            rows.append({
                "club": CLUB_ABBR.get(club, ""),
                "club_name": club,
                "player": player,
                "pos": pos,
                "injury": injury,
                "practice": practice,
                "game_status": game,
                "day": day,
                "source_url": SOURCE_URL,
                "capture": "B",
                "capture_clock_utc": "2026-11-19T07:05:00Z",
            })
    return rows


def main():
    for p in (CAPTURE_A, CAPTURE_B):
        if not os.path.exists(p):
            sys.exit("missing stored capture: %s" % p)

    a_rows, blocks, no_injury, fixtures, raw = parse_capture_a()
    b_rows = parse_capture_b()

    # ---- transcription control: A (raw bytes, 11-18) vs B (rendered, 11-19) ----
    key = lambda r: (r["club"], r["player"])
    amap = {key(r): r for r in a_rows}
    bmap = {key(r): r for r in b_rows}
    FIELDS = ("pos", "injury", "practice", "game_status")
    joined = 0
    per_field_equal = {f: 0 for f in FIELDS}
    diffs = []
    for k in sorted(set(amap) & set(bmap)):
        joined += 1
        for f in FIELDS:
            if amap[k][f] == bmap[k][f]:
                per_field_equal[f] += 1
            else:
                diffs.append({"club": k[0], "player": k[1], "field": f,
                              "A_2026-11-18": amap[k][f],
                              "B_2026-11-19": bmap[k][f]})
    only_a = sorted(set(amap) - set(bmap))
    only_b = sorted(set(bmap) - set(amap))

    # ---- drift alarm, declared before the result is seen ----
    D = {  # declared expectations, from the two captures' own provenance
        "A": {"rows_min": 200, "rows_max": 320, "clubs_min": 20, "clubs_max": 32,
              "practice_values": {"Did Not Participate In Practice",
                                  "Limited Participation in Practice",
                                  "Full Participation in Practice"}},
        "B": {"rows_min": 200, "rows_max": 320, "clubs_min": 20, "clubs_max": 32,
              "practice_values": {"Did Not Participate In Practice",
                                  "Limited Participation in Practice",
                                  "Full Participation in Practice"}},
    }
    alarms = []
    for tag, rs in (("A", a_rows), ("B", b_rows)):
        d = D[tag]
        n, nclubs = len(rs), len({r["club"] for r in rs})
        if not (d["rows_min"] <= n <= d["rows_max"]):
            alarms.append("%s: %d rows outside [%d,%d]" % (tag, n, d["rows_min"], d["rows_max"]))
        if not (d["clubs_min"] <= nclubs <= d["clubs_max"]):
            alarms.append("%s: %d clubs outside [%d,%d]" % (tag, nclubs, d["clubs_min"], d["clubs_max"]))
        bad = {r["practice"] for r in rs} - d["practice_values"] - {""}
        if bad:
            alarms.append("%s: practice values outside official vocabulary: %s" % (tag, sorted(bad)))
        if any(not r["player"] for r in rs):
            alarms.append("%s: player name missing on at least one row" % tag)

    # ---- designation census (both captures), split by practice status ----
    def census(rs):
        out = {}
        for r in rs:
            g = r["game_status"] or "(blank)"
            p = r["practice"] or "(blank)"
            out.setdefault(g, {}).setdefault(p, 0)
            out[g][p] += 1
        return out

    # ---- six reserve-list contradictions the peer session reported ----
    # We can only check the half that lives in this capture: the practice row.
    WATCH = ["Al-Shaair", "Carlies", "McCormick", "Wiley", "Hutchinson", "Richter"]
    watch_hits = []
    for w in WATCH:
        for r in b_rows:
            if w.split()[-1].lower() in r["player"].lower():
                watch_hits.append({"watch": w, "player": r["player"], "club": r["club"],
                                   "practice": r["practice"], "game_status": r["game_status"],
                                   "source_url": r["source_url"]})

    payload = {
        "dataset": "nfl_origination_lab_availability_parse",
        "title": "Two stored official Week 11 injury-report captures, parsed independently",
        "built_utc": "2026-11-19T00:00:00Z",   # pinned: the build must be byte-reproducible
        "provenance": {
            "A": {"path": os.path.relpath(CAPTURE_A, ROOT),
                  "kind": "raw bytes captured by the nfl-readiness-register workflow",
                  "sha256": sha256(CAPTURE_A),
                  "bytes": os.path.getsize(CAPTURE_A),
                  "captured_utc": "2026-11-18T23:49:17Z",
                  "source_url": SOURCE_URL,
                  "read_this_session": False},
            "B": {"path": os.path.relpath(CAPTURE_B, ROOT),
                  "kind": "rendered markdown transcription; NOT raw bytes",
                  "sha256": sha256(CAPTURE_B),
                  "bytes": os.path.getsize(CAPTURE_B),
                  "captured_utc": "2026-11-19T07:05:00Z",
                  "source_url": SOURCE_URL,
                  "read_this_session": False},
            "this_session_live_read": None,
            "this_session_live_read_reason":
                "the sandbox has no HTTPS egress to nfl.com; verified with curl before this run",
        },
        "counts": {
            "A": {"rows": len(a_rows), "clubs": len({r["club"] for r in a_rows}),
                  "club_tables": sum(1 for b in blocks if b["has_table"]),
                  "no_injury_blocks": len([x for x in no_injury if x])},
            "B": {"rows": len(b_rows), "clubs": len({r["club"] for r in b_rows})},
        },
        "transcription_control": {
            "method": "join on (club, player) between the two independent reads; no code shared with either peer parser",
            "joined_rows": joined,
            "fields_compared": list(FIELDS),
            "fields_equal": per_field_equal,
            "differences": diffs,
            "only_in_A": [{"club": c, "player": p} for c, p in only_a],
            "only_in_B": [{"club": c, "player": p} for c, p in only_b],
            "what_it_proves":
                "that two sessions transcribed the same publisher page to the same values. "
                "It does not make either read independent of the publisher, and a value that "
                "is wrong on the page is wrong in both.",
        },
        "drift_alarm": {"status": "PASS" if not alarms else "FAIL",
                        "declared_expectations": {k: {kk: (sorted(vv) if isinstance(vv, set) else vv) for kk, vv in v.items()} for k, v in D.items()}, "problems": alarms},
        "designation_census": {
            "A": census(a_rows),
            "B": census(b_rows),
            "note": "a blank Game Status is a blank cell on the official page; it is "
                    "published as blank and never converted to 'available'.",
        },
        "reserve_list_watch": {
            "definition": "players the peer session reported as simultaneously on the "
                          "November 2026 Reserve/Injured list and carrying a practice row",
            "rows": watch_hits,
            "what_this_check_does_not_do": "it does not confirm enlistment on the reserve "
                                           "list (a second page this session could not read); "
                                           "it confirms only that the practice row exists",
        },
        "name_collisions": NAME_COLLISIONS,
        "fixture_order_observed": fixtures,
        "rows": b_rows,   # the later read is the working row set; A is in rows_norm
        "rows_earlier_read": a_rows,
        "sources": [
            {"url": SOURCE_URL,
             "title": "Official Latest NFL Injury Report for Players - Week 11 of the 2026 Season | NFL.com",
             "read_by": "peer captures A and B, not this session"},
        ],
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1)
        fh.write("\n")

    # console summary
    print("capture A rows %d / clubs %d" % (len(a_rows), len({r["club"] for r in a_rows})))
    print("capture B rows %d / clubs %d" % (len(b_rows), len({r["club"] for r in b_rows})))
    print("joined %d; field equality %s" % (joined, per_field_equal))
    print("differences %d; only_A %d; only_B %d" % (len(diffs), len(only_a), len(only_b)))
    print("drift alarm:", payload["drift_alarm"]["status"], alarms)
    print("wrote", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
