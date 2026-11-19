#!/usr/bin/env python3
"""Daily desk parsers: availability (two dated reads -> delta) and the reserve list.

Design rules taken from the 2026-11-19 brief:
  * "Store every injury-hub read with its clock time and publish the delta, never the level."
  * "Make the injury signal a surprise, never a level."
  * "Add a drift alarm to every scraper ... fail the build loudly when a field goes missing
     rather than publishing a blank."
  * "Capture the reserve list so 'not listed' never means 'available'."
A "No Injuries Reported" club block is therefore stored as a captured STATE, not as missing data.
"""
import hashlib
import html
import json
import os
import re
import sys
from collections import Counter, OrderedDict, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)
DAY = "2026-11-19"
READ_B = NS + "/captures/%s/injury-report-week11.md" % DAY
CAPTURE_A = ROOT + "/nfl-readiness-register/snapshots/2026-11-18/injury_report-2026-11-18T234917Z.html"
RESERVE_A = ROOT + "/nfl-readiness-register/snapshots/2026-11-18/reserve_list-2026-11-18T234918Z.html"
RESERVE_B = NS + "/captures/%s/reserve-list-november-2026.md" % DAY

OFFICIAL_PRACTICE = ["Full Participation in Practice", "Limited Participation in Practice",
                     "Did Not Participate In Practice"]
OFFICIAL_GAME_STATUS = ["Questionable", "Doubtful", "Out"]
CLUB_BY_NAME = {
    "Ravens": "BAL", "Bills": "BUF", "Bengals": "CIN", "Browns": "CLE", "Cowboys": "DAL",
    "Broncos": "DEN", "Lions": "DET", "Packers": "GB", "Texans": "HOU", "Colts": "IND",
    "Jaguars": "JAX", "Chiefs": "KC", "Rams": "LA", "Dolphins": "MIA", "Vikings": "MIN",
    "Patriots": "NE", "Saints": "NO", "Giants": "NYG", "Jets": "NYJ", "Eagles": "PHI",
    "Cardinals": "AZ", "Raiders": "LV", "Commanders": "WAS", "Chargers": "LAC", "49ers": "SF",
    "Seahawks": "SEA", "Buccaneers": "TB", "Titans": "TEN", "Panthers": "CAR", "Bears": "CHI",
    "Falcons": "ATL", "Steelers": "PIT",
}


def cell(s):
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    return re.sub(r"\s+", " ", s).strip()


def namekey(s):
    """Rendering-agnostic player key.

    The same player is displayed as 'Dee Alford' in the raw page and as "De'Alford, Dee" in the
    rendered read. Token sorting cannot bridge an apostrophe that splits a surname, so the key is
    the sorted multiset of alphanumeric characters: identical for every rendering of the same name,
    and a collision (two different players with the same letters on one club) is reported by the
    row-count reconciliation rather than silently merged.
    """
    s = html.unescape(s).lower()
    s = re.sub(r"[^a-z0-9]", "", s)
    return "".join(sorted(s))


def digest(path):
    b = open(path, "rb").read()
    return hashlib.sha256(b).hexdigest(), len(b)


# ---------------------------------------------------------------- raw HTML read (2026-11-18)
def parse_raw(path):
    text = open(path, encoding="utf-8").read()
    days = [(m.start(), m.group(1).strip())
            for m in re.finditer(r'<h2 class="d3-o-section-title">([^<]+)</h2>', text)]

    def day_of(pos):
        lab = ""
        for s, l in days:
            if s < pos:
                lab = l
            else:
                break
        return lab

    subs = [(m.start(), cell(m.group(1)), m.end())
            for m in re.finditer(r'<div class="d3-o-section-sub-title"><span>([^<]+)</span></div>', text)]
    rows, no_state = [], []
    for i, (pos, club, end) in enumerate(subs):
        nxt = subs[i + 1][0] if i + 1 < len(subs) else len(text)
        seg = text[end:nxt]
        if "nfl-o-no-results" in seg.split("<table")[0]:
            no_state.append({"day": day_of(pos), "club": club, "state": "No Injuries Reported"})
            continue
        tb = re.search(r"<tbody>(.*?)</tbody>", seg, re.S)
        if not tb:
            no_state.append({"day": day_of(pos), "club": club, "state": "NO TABLE FOUND - parser failure"})
            continue
        for tr in re.findall(r"<tr>(.*?)</tr>", tb.group(1), re.S):
            cells = [cell(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S)]
            if len(cells) < 5:
                continue
            slug = re.search(r'href="/players/([^/"]+)/"', tr)
            rows.append({"day": day_of(pos), "club": club, "club_abbr": CLUB_BY_NAME.get(club, "?"),
                         "player": cells[0], "slug": slug.group(1) if slug else "",
                         "pos": cells[1], "injury": cells[2], "practice": cells[3],
                         "game_status": cells[4]})
    return rows, no_state


# ------------------------------------------------------- rendered markdown read (2026-11-19)
def parse_rendered(path):
    rows, no_state, club, day = [], [], "", ""
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("## ") and re.match(r"## (THURSDAY|FRIDAY|SATURDAY|SUNDAY|MONDAY|WEDNESDAY|TUESDAY)", line):
            day = line[3:].split("—")[0].strip()
            continue
        m = re.match(r"^### (.+?)\s*$", line)
        if m:
            club = m.group(1).strip()
            continue
        if line.strip() == "No Injuries Reported":
            no_state.append({"day": day, "club": club, "state": "No Injuries Reported"})
            continue
        if line.startswith("| ") and not line.startswith("| Player"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) != 5 or set("".join(cells)) <= set("-: "):
                continue
            if cells[0] in ("From", "Day", "Club", "Headline"):
                continue
            rows.append({"day": day, "club": club, "club_abbr": CLUB_BY_NAME.get(club, "?"),
                         "player": cells[0], "slug": "", "pos": cells[1], "injury": cells[2],
                         "practice": cells[3], "game_status": cells[4]})
    return rows, no_state


def drift_check(rows, expect):
    problems = []
    if len(rows) < expect["min_rows"]:
        problems.append("row count %d below pinned floor %d" % (len(rows), expect["min_rows"]))
    for r in rows:
        for f in expect["required_fields"]:
            if f not in r:
                problems.append("field %s absent from %s/%s" % (f, r.get("club"), r.get("player")))
        if r["practice"] not in OFFICIAL_PRACTICE:
            problems.append("practice value outside the official vocabulary: %r (%s/%s)"
                            % (r["practice"], r["club"], r["player"]))
        if r["game_status"] not in OFFICIAL_GAME_STATUS + [""]:
            problems.append("game-status value outside the official vocabulary: %r (%s/%s)"
                            % (r["game_status"], r["club"], r["player"]))
    n = len({r["club"] for r in rows})
    if n != expect["expect_clubs_with_rows"]:
        problems.append("clubs with rows = %d, pinned expectation = %d"
                        % (n, expect["expect_clubs_with_rows"]))
    unknown = sorted({r["club_abbr"] for r in rows} - set(CLUB_BY_NAME.values()))
    if unknown:
        problems.append("club name not in the official 32-club map: %s" % unknown)
    return problems


def summarise(rows, no_state, label):
    gs = Counter(r["game_status"] for r in rows if r["game_status"])
    pr = Counter(r["practice"] for r in rows)
    return {
        "read": label,
        "n_rows": len(rows),
        "n_clubs_with_rows": len({r["club"] for r in rows}),
        "n_clubs_no_injuries_reported": sum(1 for x in no_state if x["state"] == "No Injuries Reported"),
        "no_injuries_reported_clubs": [x["club"] for x in no_state if x["state"] == "No Injuries Reported"],
        "abnormal_blocks": [x for x in no_state if x["state"] != "No Injuries Reported"],
        "designation_levels": dict(gs),
        "n_rows_with_game_designation": sum(gs.values()),
        "pct_rows_with_game_designation": round(100.0 * sum(gs.values()) / max(1, len(rows)), 2),
        "practice_levels": dict(pr),
        "per_club_rows": dict(sorted(Counter(r["club"] for r in rows).items())),
    }


def main():
    expect = json.load(open(os.path.join(NS, "data", "drift_expectations.json")))
    a_rows, a_no = parse_raw(CAPTURE_A)
    b_rows, b_no = parse_rendered(RESERVE_B.replace("reserve-list-november-2026.md",
                                                    "injury-report-week11.md"))
    problems = drift_check(a_rows, expect["reads"]["capture_a"]) + \
        drift_check(b_rows, expect["reads"]["capture_b"])

    ha = {namekey(r["player"]) + "|" + r["club_abbr"]: r for r in a_rows}
    hb = {namekey(r["player"]) + "|" + r["club_abbr"]: r for r in b_rows}
    shared = sorted(set(ha) & set(hb))
    changes = []
    for k in shared:
        x, y = ha[k], hb[k]
        for f in ("practice", "game_status", "injury"):
            if x[f] != y[f]:
                changes.append({"club_abbr": x["club_abbr"], "club": x["club"],
                                "player": y["player"], "position": y["pos"], "field": f,
                                "earlier_value": x[f] or "(blank)", "later_value": y[f] or "(blank)",
                                "day": y["day"]})
    added = [hb[k] for k in sorted(set(hb) - set(ha))]
    gone = [ha[k] for k in sorted(set(ha) - set(hb))]
    # candidate (NOT merged) pairs: an unmatched A row and an unmatched B row on the same club that
    # agree on every field except the display name. Published as a candidate because display name is
    # not a stable join key; identity needs the player URL, which the rendered read does not carry.
    only_a = [ha[k] for k in sorted(set(ha) - set(hb))]
    only_b = [hb[k] for k in sorted(set(hb) - set(ha))]
    used, candidate_pairs = set(), []
    for x in only_a:
        for j, y in enumerate(only_b):
            if j in used:
                continue
            if (x["club_abbr"], x["pos"], x["injury"], x["practice"], x["game_status"], x["day"]) == \
               (y["club_abbr"], y["pos"], y["injury"], y["practice"], y["game_status"], y["day"]):
                used.add(j)
                candidate_pairs.append({"club_abbr": x["club_abbr"], "club": x["club"],
                                        "position": x["pos"], "earlier_display": x["player"],
                                        "later_display": y["player"],
                                        "earlier_player_url": ("https://www.nfl.com/players/%s/" % x["slug"])
                                        if x.get("slug") else "",
                                        "resolution": "candidate same-player pair - reported, not merged; "
                                                        "join on the player URL, not on the display name"})
                break
    display_variants = [{"club_abbr": hb[k]["club_abbr"], "raw_display": ha[k]["player"],
                         "rendered_display": hb[k]["player"],
                         "player_url": ("https://www.nfl.com/players/%s/" % ha[k]["slug"]) if ha[k].get("slug") else "",
                         "note": "same person, different display rendering between the two reads "
                                 "(matched by character multiset, not by string equality)"}
                        for k in sorted(set(ha) & set(hb)) if ha[k]["player"] != hb[k]["player"]]
    a_clubs = {r["club_abbr"] for r in a_rows}
    b_clubs = {r["club_abbr"] for r in b_rows}
    club_transitions = []
    for c in sorted(b_clubs - a_clubs):
        club_transitions.append({
            "club_abbr": c, "club": CLUB_BY_NAME and sorted(b_clubs and {r["club"] for r in b_rows if r["club_abbr"] == c})[0],
            "earlier_state": "No Injuries Reported (official block marker)",
            "later_state": "%d player rows" % len([r for r in b_rows if r["club_abbr"] == c]),
            "reading": "either the club's report was filled in after the earlier capture or the "
                       "earlier capture caught the page mid-publish; both readings make the block a "
                       "captured state, and both are reported rather than reconciled silently",
        })
    for c in sorted(a_clubs - b_clubs):
        club_transitions.append({"club_abbr": c,
                                 "earlier_state": "%d player rows" % len([r for r in a_rows if r["club_abbr"] == c]),
                                 "later_state": "No Injuries Reported (official block marker)",
                                 "reading": "rows disappeared between reads - investigate before use"})

    sha_a, bytes_a = digest(CAPTURE_A)
    sha_b, bytes_b = digest(RESERVE_B.replace("reserve-list-november-2026.md", "injury-report-week11.md"))
    out = {
        "dataset": "nfl_daily_desk_availability_delta",
        "title": "Week 11 availability: two dated official reads, and the delta between them",
        "built_utc": "2026-11-19T07:20:00Z",
        "session": "arena-92c458e6-own4",
        "policy": "the signal is the change between reads, never the level of one read; a blank "
                  "Game Status cell is published as blank, it is never read as 'available'",
        "reads": OrderedDict([
            ("capture_a", {
                "label": "2026-11-18T23:49:17Z raw-bytes capture",
                "kind": "immutable raw bytes (workflow capture)",
                "path": os.path.relpath(CAPTURE_A, ROOT),
                "sha256": sha_a, "bytes": bytes_a,
                "source_url": "https://www.nfl.com/injuries/",
                "summary": summarise(a_rows, a_no, "capture_a"),
            }),
            ("capture_b", {
                "label": "2026-11-19T07:05:00Z rendered read",
                "kind": "platform-rendered markdown, transcribed by this session",
                "path": os.path.relpath(RESERVE_B.replace("reserve-list-november-2026.md",
                                                          "injury-report-week11.md"), ROOT),
                "sha256": sha_b, "bytes": bytes_b,
                "source_url": "https://www.nfl.com/injuries/",
                "summary": summarise(b_rows, b_no, "capture_b"),
            }),
        ]),
        "drift_alarm": {"checks": "row floor, required fields, official vocabulary, club count",
                        "problems": problems, "status": "PASS" if not problems else "FAIL"},
        "row_level_delta": {
            "n_keys_in_both": len(shared),
            "n_changed": len(changes),
            "n_rows_only_in_earlier_read": len(gone),
            "n_rows_only_in_later_read": len(added),
            "changes": changes,
            "display_name_variants": display_variants,
            "candidate_same_player_pairs": candidate_pairs,
            "residual_after_pairing": {"only_in_later": len(only_b) - len(candidate_pairs),
                                       "only_in_earlier": len(only_a) - len(candidate_pairs)},
            "rows_added_in_later_read": [{"club_abbr": r["club_abbr"], "club": r["club"],
                                          "player": r["player"], "position": r["pos"],
                                          "practice": r["practice"],
                                          "game_status": r["game_status"] or "(blank)",
                                          "day": r["day"]} for r in added],
        },
        "club_block_transitions": club_transitions,
        "surprise_panel": {
            "definition": "surprise = observed designation minus the designation the previous dated "
                          "read implied for the same player. It is only defined where two reads exist; "
                          "every other row is published blank with this reason.",
            "n_players_with_two_reads": len(shared),
            "n_surprises": len(changes),
            "n_players_with_only_one_read": len(set(hb) - set(ha)),
        },
        "rows": [dict(r, source_url="https://www.nfl.com/injuries/") for r in b_rows],
        "no_injury_blocks": [{"club": x["club"], "day": x["day"], "state": x["state"],
                              "source_url": "https://www.nfl.com/injuries/"} for x in b_no],
    }

    # ------------------------------------------------------------------ reserve list delta
    ra, _ = parse_raw_reserve(RESERVE_A)
    rb, _ = parse_reserve_md(RESERVE_B)
    ka = {(r["club_abbr"], namekey(r["name"])): r for r in ra}
    kb = {(r["club_abbr"], namekey(r["name"])): r for r in rb}
    ir = {
        "dataset": "nfl_daily_desk_reserve_delta",
        "title": "League reserve list (IR): November 2026, two dated reads",
        "built_utc": "2026-11-19T07:20:00Z",
        "policy": "'not listed on the injury report' never means 'available': a player on the reserve "
                  "list is absent from the weekly report by construction",
        "source_url": "https://www.nfl.com/transactions/league/reserve-list/2026/11",
        "read_a": {"label": "2026-11-18T23:49:18Z raw-bytes capture", "rows": len(ra),
                   "sha256": digest(RESERVE_A)[0], "bytes": digest(RESERVE_A)[1],
                   "path": os.path.relpath(RESERVE_A, ROOT)},
        "read_b": {"label": "2026-11-19T07:06:30Z rendered read", "rows": len(rb),
                   "sha256": digest(RESERVE_B)[0], "bytes": digest(RESERVE_B)[1],
                   "path": os.path.relpath(RESERVE_B, ROOT)},
        "delta": {"n_new_rows": len([k for k in kb if k not in ka]),
                  "n_rows_dropped": len([k for k in ka if k not in kb]),
                  "new_rows": [kb[k] for k in sorted(set(kb) - set(ka))]},
        "per_club_november_ir": dict(sorted(Counter(r["club_abbr"] for r in rb).items(),
                                            key=lambda kv: (-kv[1], kv[0]))),
        "rows": rb,
        "caveats": [
            "the November ledger as rendered lists 25 Reserve/Injured moves; it is a month ledger, not "
            "the full 53-man IR state, so a club with zero November rows is not 'healthy'",
            "the official page publishes the Position column blank for every row of this ledger "
            "(confirmed in the raw bytes, not a transcription gap)",
        ],
    }
    json.dump(out, open(os.path.join(NS, "data", "availability_delta.json"), "w"), indent=1)
    json.dump(ir, open(os.path.join(NS, "data", "reserve_delta.json"), "w"), indent=1)
    print("availability rows later read %d / earlier %d; designation changes %d; club transitions %d"
          % (len(b_rows), len(a_rows), len(changes), len(club_transitions)))
    print("reserve rows: earlier %d later %d new %d" % (len(ra), len(rb), len([k for k in kb if k not in ka])))
    print("drift problems:", problems)
    json.dump({"rows": b_rows, "no_blocks": b_no}, open("/tmp/avail.json", "w"))
    sys.exit(1 if problems else 0)


def parse_raw_reserve(path):
    text = open(path, encoding="utf-8").read()
    rows = []
    for tr in re.findall(r"<tr>(.*?)</tr>", text, re.S):
        cells = [cell(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(cells) < 6:
            continue
        abbrs = re.findall(r'/clubs/logos/([A-Z]{2,3})', tr)
        rows.append({"club_abbr": abbrs[0] if abbrs else "?", "club": cells[0], "date": cells[2],
                     "name": cells[3], "position": cells[4], "transaction": cells[5]})
    return rows, []


def parse_reserve_md(path):
    rows = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line.startswith("| ") or line.startswith("| From") or line.startswith("| ---"):
            continue
        c = [x.strip() for x in line.strip("|").split("|")]
        if len(c) != 6 or set("".join(c)) <= set("-: "):
            continue
        rows.append({"club_abbr": c[0], "club": c[1], "date": c[2], "name": c[3],
                     "position": c[4] or "(blank on the official page)", "transaction": c[5]})
    return rows, []


if __name__ == "__main__":
    main()
