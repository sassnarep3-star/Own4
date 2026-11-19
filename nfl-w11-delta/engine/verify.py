#!/usr/bin/env python3
"""Verifier for the Week 11 injury-delta workspace (stdlib only). Exit 1 on any FAIL.

Checks are independent of engine/delta.py where possible:
  1. raw capture sha256 equals the manifest entry; manifest entry is unique
  2. transcription file sha256 equals the hash recorded in delta.json (no silent edits)
  3. row counts re-derived here (regex on the transcription; re-parse of raw HTML) equal delta.json counts
  4. drift alarm: positions / practice / game-status vocabularies are closed sets; an unknown value fails
  5. delta arithmetic: read = raw + added - removed; overlap = unchanged + changed
  6. every published table row links to an official NFL URL; no localhost references
  7. delta page lists exactly added + removed + changed rows (no level leak); local links resolve
  8. the site is deterministic: a rebuild is byte-identical
"""
import hashlib
import html.parser
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
REPO = os.path.dirname(NS)
sys.path.insert(0, HERE)

FAILS = []
PASSES = []


def check(ok, msg):
    (PASSES if ok else FAILS).append(msg)
    print(("PASS " if ok else "FAIL ") + msg)


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


POSITIONS_OK = None  # closed set discovered from the transcription and frozen below
PRACTICE_OK = {"Full Participation in Practice", "Limited Participation in Practice", "Did Not Participate In Practice"}
GAME_OK = {"", "Out", "Questionable", "Doubtful"}
POSITIONS_OK = {"QB", "RB", "WR", "TE", "T", "G", "C", "OL", "DL", "DE", "DT", "LB", "CB", "S", "K", "P", "LS", "FB"}
OFFICIAL_PREFIX = "https://www.nfl.com/"


def read_rows(path):
    rows, club, clubs, no_rows = [], None, [], []
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("#### "):
            club = line[5:].strip()
            clubs.append(club)
            continue
        if line.startswith("- ") and ": No Injuries Reported" in line:
            no_rows.append(line[2:].split(":")[0].strip())
            continue
        if line.startswith("| ") and club and not line.startswith("| Player") and not line.startswith("| ---"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) != 5:
                raise SystemExit("FAIL malformed row (%d cells): %s" % (len(cells), line))
            rows.append({"team_nickname": club, "player": cells[0], "position": cells[1], "injury": cells[2],
                         "practice": cells[3], "game": cells[4]})
    return rows, clubs, no_rows


class Rows(html.parser.HTMLParser):
    """Counts <tr> body rows and collects their hrefs for a given HTML file."""
    def __init__(self):
        super().__init__()
        self.in_tbody = False
        self.rows = []
        self.cur = None
        self.hrefs = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.cur = {"cells": 0, "hrefs": []}
        if tag == "td" and self.cur is not None:
            self.cur["cells"] += 1
        if tag == "a":
            href = a.get("href") or ""
            self.links.append(href)
            if self.cur is not None:
                self.cur["hrefs"].append(href)

    def handle_endtag(self, tag):
        if tag == "tbody":
            self.in_tbody = False
        if tag == "tr" and self.cur is not None:
            self.rows.append(self.cur)
            self.cur = None


class Ids(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag in ("a", "link", "script", "img") and (a.get("href") or a.get("src")):
            self.links.append(a.get("href") or a.get("src"))


def main():
    # 1. raw capture + manifest
    man = [json.loads(l) for l in open(os.path.join(REPO, "nfl-readiness-register/snapshots/manifest.jsonl"), encoding="utf-8") if l.strip()]
    ent = [m for m in man if m.get("capture_id") == "injury_report-2026-11-18T234917Z"]
    check(len(ent) == 1, "manifest has exactly one entry for the Week 11 raw capture")
    raw_path = os.path.join(REPO, "nfl-readiness-register/snapshots/2026-11-18/injury_report-2026-11-18T234917Z.html")
    if ent:
        check(sha(raw_path) == ent[0]["sha256"], "raw capture sha256 equals manifest (immutability)")

    d = json.load(open(os.path.join(NS, "data", "delta.json"), encoding="utf-8"))
    read_path = os.path.join(NS, "data", "official_read_2026-11-19_w11.md")

    # 2. transcription hash
    check(sha(read_path) == d["delta_to"]["sha256"], "transcription sha256 equals the hash used by delta.json")

    # 3. independent re-derivation of counts
    rr, rclubs, rno = read_rows(read_path)
    from parse_raw import parse_html
    raw = parse_html(open(raw_path, encoding="utf-8").read())
    raw_rows = raw["rows"]
    raw_tables = raw["table_titles"]
    raw_html = open(raw_path, encoding="utf-8").read()
    raw_no = re.findall(r'<span>([^<]+)</span></div></div><section class="[^"]*nfl-o-no-results', raw_html)
    check(len(raw_rows) == d["counts"]["raw_rows"], "raw row count re-derived (%d) equals delta.json" % len(raw_rows))
    check(len(rr) == d["counts"]["read_rows"], "transcription row count re-derived (%d) equals delta.json" % len(rr))
    check(len(raw_tables) == d["counts"]["raw_tables"], "raw club-table count re-derived (%d)" % len(raw_tables))
    check(len(rclubs) == d["counts"]["read_tables"], "transcription club-table count re-derived (%d)" % len(rclubs))
    check(set(raw_no) == {"Chargers", "Bengals", "Commanders"},
          "raw 'No Injuries Reported' blocks are exactly Chargers, Bengals, Commanders (%s)" % ", ".join(raw_no))
    check("Chargers" not in raw_tables and "Chargers" in rclubs, "Chargers: absent table in raw, populated in read (F1)")

    # 4. drift alarm: closed vocabularies
    pos = {r["position"] for r in rr} | {r["position"] for r in raw_rows}
    prac = {r["practice"] for r in rr} | {r["practice"] for r in raw_rows}
    game = {r["game"] for r in rr} | {r["game"] for r in raw_rows}
    check(pos <= POSITIONS_OK, "position vocabulary is closed (unknown: %s)" % sorted(pos - POSITIONS_OK))
    check(prac <= PRACTICE_OK, "practice-status vocabulary is closed (unknown: %s)" % sorted(prac - PRACTICE_OK))
    check(game <= GAME_OK, "game-status vocabulary is closed (unknown: %s)" % sorted(game - GAME_OK))
    keys_r = [(r["team_nickname"], r["player"]) for r in rr]
    keys_w = [(r["team_nickname"], r["player"]) for r in raw_rows]
    check(len(set(keys_r)) == len(keys_r), "no duplicate (club, player) in the later read")
    check(len(set(keys_w)) == len(keys_w), "no duplicate (club, player) in the raw capture")
    check(all(r["player"] and r["position"] for r in rr), "every later-read row has a player and a position")

    # 5. delta arithmetic
    c = d["counts"]
    kr = set(keys_r)
    kw = set(keys_w)
    check(len(kr) == len(kw) + c["added"] - c["removed"], "later-read rows = raw rows + added - removed")
    check(len(kr & kw) == c["unchanged"] + c["changed"], "overlap = unchanged + changed")
    check(len(d["added"]) == c["added"] and len(d["removed"]) == c["removed"] and len(d["changed"]) == c["changed"],
          "delta.json lists match the counts")
    check(all(r["team_nickname"] in set(rclubs) for r in d["added"]), "every added row belongs to a club in the later read")

    # 6/7. site checks
    site_files = ["index.html", "pages/delta.html", "pages/clubs.html", "pages/sources.html", "pages/flagged.html"]
    for rel in site_files:
        p = os.path.join(NS, rel)
        check(os.path.exists(p), "page exists: %s" % rel)
        txt = open(p, encoding="utf-8").read()
        check("localhost" not in txt and "127.0.0.1" not in txt, "no localhost reference in %s" % rel)
        rp = Rows()
        rp.feed(txt)
        body_rows = [r for r in rp.rows if r["cells"] > 0]
        bad = [r for r in body_rows if not any(h.startswith(OFFICIAL_PREFIX) for h in r["hrefs"])]
        check(not bad, "every table row in %s carries an official nfl.com link (%d rows, %d without)" % (rel, len(body_rows), len(bad)))
        ids = Ids()
        ids.feed(txt)
        for href in ids.links:
            if href.startswith("http") or href.startswith("data:") or href.startswith("mailto:"):
                continue
            if href.split("#")[0] == "":
                continue
            target = os.path.normpath(os.path.join(os.path.dirname(p), href.split("#")[0]))
            if not os.path.exists(target):
                check(False, "local link resolves in %s: %s" % (rel, href))
    dp = open(os.path.join(NS, "pages", "delta.html"), encoding="utf-8").read()
    rp = Rows()
    rp.feed(dp)
    n_delta_rows = len([r for r in rp.rows if r["cells"] > 0])
    check(n_delta_rows == c["added"] + c["removed"] + c["changed"],
          "delta page lists exactly the changed rows (%d); no unchanged level rows" % n_delta_rows)

    # 8. determinism
    before = {rel: sha(os.path.join(NS, rel)) for rel in site_files}
    subprocess.run([sys.executable, os.path.join(HERE, "build.py")], check=True, cwd=REPO, capture_output=True)
    after = {rel: sha(os.path.join(NS, rel)) for rel in site_files}
    check(before == after, "site rebuild is byte-identical (deterministic)")

    print("VERIFY: %s (%d pass, %d fail)" % ("PASS" if not FAILS else "FAIL", len(PASSES), len(FAILS)))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
