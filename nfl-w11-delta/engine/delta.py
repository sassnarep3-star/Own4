#!/usr/bin/env python3
"""Week 11 official injury report: delta between two dated reads.

Inputs
  A) raw HTML capture (immutable, stored by the readiness register):
     nfl-readiness-register/snapshots/2026-11-18/injury_report-2026-11-18T234917Z.html
     sha256 must equal the manifest entry (checked here).
  B) transcribed read of the official page (fetch_page rendering, 2026-11-19):
     nfl-w11-delta/data/official_read_2026-11-19_w11.md

Outputs
  nfl-w11-delta/data/delta.json  (delta only: added / removed / changed rows, per-club counts,
                                  clubs that changed presence, plus provenance)

Rule (brief: "publish the delta, never the level"): the site renders only what is in delta.json.
Stdlib only, deterministic (no clock reads; the read time comes from the transcription header).
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
REPO = os.path.dirname(NS)
sys.path.insert(0, HERE)
from parse_raw import parse_html  # noqa: E402

RAW_REL = "nfl-readiness-register/snapshots/2026-11-18/injury_report-2026-11-18T234917Z.html"
MANIFEST_REL = "nfl-readiness-register/snapshots/manifest.jsonl"
READ_REL = "nfl-w11-delta/data/official_read_2026-11-19_w11.md"
OUT_REL = "nfl-w11-delta/data/delta.json"
RAW_CAPTURE_ID = "injury_report-2026-11-18T234917Z"
OFFICIAL_URL = "https://www.nfl.com/injuries/"

ROW_RE = re.compile(r"^\| (?!Player\b)(?!---)(.+?) \| (.+?) \| (.*?) \| (.*?) \| (.*?) \|\s*$")
CLUB_RE = re.compile(r"^#### (.+?)\s*$")
GAME_RE = re.compile(r"^### (.+?)\s*$")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def read_transcription(path):
    rows, clubs, no_rows = [], [], []
    club = None
    game = None
    current_game_clubs = []
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        m = GAME_RE.match(line)
        if m and not line.startswith("#### "):
            game = m.group(1)
            current_game_clubs = []
            continue
        m = CLUB_RE.match(line)
        if m:
            club = m.group(1)
            clubs.append(club)
            current_game_clubs.append(club)
            continue
        if line.startswith("- ") and ": No Injuries Reported" in line:
            no_rows.append(line[2:].split(":")[0].strip())
            continue
        m = ROW_RE.match(line)
        if m and club is not None:
            name, pos, inj, prac, game_status = (g.strip() for g in m.groups())
            rows.append({"team_nickname": club, "player": name, "position": pos,
                         "injury": inj, "practice": prac, "game": game_status,
                         "game_header": game})
    return {"rows": rows, "clubs_with_table": clubs, "no_injury_teams": no_rows}


def key(r):
    return (r["team_nickname"], r["player"])


def main():
    man = [json.loads(l) for l in open(os.path.join(REPO, MANIFEST_REL), encoding="utf-8") if l.strip()]
    entry = [m for m in man if m.get("capture_id") == RAW_CAPTURE_ID]
    if len(entry) != 1:
        raise SystemExit("manifest entry for %s not found exactly once" % RAW_CAPTURE_ID)
    raw_path = os.path.join(REPO, RAW_REL)
    raw_sha = sha256_file(raw_path)
    if raw_sha != entry[0]["sha256"]:
        raise SystemExit("raw capture sha256 mismatch: file %s manifest %s" % (raw_sha, entry[0]["sha256"]))

    raw = parse_html(open(raw_path, encoding="utf-8").read())
    raw_rows = []
    for r in raw["rows"]:
        raw_rows.append({"team_nickname": r["team_nickname"], "player": r["player"],
                         "position": r["position"], "injury": r["injury"],
                         "practice": r["practice"], "game": r["game"]})
    raw_clubs = raw["table_titles"]

    rd = read_transcription(os.path.join(REPO, READ_REL))
    read_rows = rd["rows"]
    read_clubs = rd["clubs_with_table"]

    # raw: the "No Injuries Reported" blocks are not in table_titles; find them from the HTML
    raw_html = open(raw_path, encoding="utf-8").read()
    raw_no_rows = []
    for m in re.finditer(r'<span>([^<]+)</span></div></div><section class="[^"]*nfl-o-no-results', raw_html):
        raw_no_rows.append(m.group(1).strip())

    # duplicates within a source would break the key; fail loudly
    for name, rows in (("raw", raw_rows), ("read", read_rows)):
        ks = [key(r) for r in rows]
        dups = sorted({k for k in ks if ks.count(k) > 1})
        if dups:
            raise SystemExit("duplicate (club, player) keys in %s: %s" % (name, dups))

    raw_map = {key(r): r for r in raw_rows}
    read_map = {key(r): r for r in read_rows}

    added = [read_map[k] for k in sorted(read_map) if k not in raw_map]
    removed = [raw_map[k] for k in sorted(raw_map) if k not in read_map]
    changed = []
    for k in sorted(set(raw_map) & set(read_map)):
        a, b = raw_map[k], read_map[k]
        diffs = {}
        for f in ("injury", "practice", "game", "position"):
            if a[f] != b[f]:
                diffs[f] = {"from": a[f], "to": b[f]}
        if diffs:
            changed.append({"team_nickname": k[0], "player": k[1], "changes": diffs})

    per_club = {}
    for club in sorted(set(raw_clubs) | set(read_clubs) | set(raw_no_rows) | set(rd["no_injury_teams"])):
        per_club[club] = {
            "raw_rows": sum(1 for r in raw_rows if r["team_nickname"] == club),
            "read_rows": sum(1 for r in read_rows if r["team_nickname"] == club),
            "raw_state": "table" if club in raw_clubs else ("no injuries reported" if club in raw_no_rows else "absent"),
            "read_state": "table" if club in read_clubs else ("no injuries reported" if club in rd["no_injury_teams"] else "absent"),
        }
        per_club[club]["row_delta"] = per_club[club]["read_rows"] - per_club[club]["raw_rows"]

    out = {
        "dataset": "nfl_w11_injury_delta",
        "official_url": OFFICIAL_URL,
        "delta_from": {"capture_id": RAW_CAPTURE_ID, "captured_utc": entry[0]["captured_utc"],
                       "raw_path": RAW_REL, "sha256": raw_sha, "method": "parsed raw HTML (stdlib parser)"},
        "delta_to": {"read_path": READ_REL, "read_utc_note": "2026-11-19, after 06:48:48 UTC (agent clock)",
                     "sha256": sha256_file(os.path.join(REPO, READ_REL)),
                     "method": "fetch_page rendering transcribed by agent (not raw HTML bytes)"},
        "counts": {"raw_rows": len(raw_rows), "read_rows": len(read_rows),
                   "raw_tables": len(raw_clubs), "read_tables": len(read_clubs),
                   "added": len(added), "removed": len(removed), "changed": len(changed),
                   "unchanged": len(set(raw_map) & set(read_map)) - len(changed)},
        "clubs": per_club,
        "added": [{"team_nickname": r["team_nickname"], "player": r["player"], "position": r["position"],
                   "injury": r["injury"], "practice": r["practice"], "game": r["game"]} for r in added],
        "removed": [{"team_nickname": r["team_nickname"], "player": r["player"], "position": r["position"],
                     "injury": r["injury"], "practice": r["practice"], "game": r["game"]} for r in removed],
        "changed": changed,
    }
    with open(os.path.join(REPO, OUT_REL), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False, sort_keys=False)
        f.write("\n")
    print(json.dumps(out["counts"], indent=1))


if __name__ == "__main__":
    main()
