#!/usr/bin/env python3
"""Publication gate for the NFL Line Genesis hub.

Fails (exit 1) when any of these is false:
  1. every data table row carries at least one source link;
  2. every internal href/src resolves to a real file, and every #anchor exists;
  3. every page carries the navigation and the responsible-gambling footer;
  4. no page links a URL recorded as 404, except the pages documenting that 404;
  5. a rebuild is byte-identical to the committed HTML;
  6. every JSON data file parses and the required keys exist.

    python3 nfl-hub/verify.py
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from urllib.parse import urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
FAILS = []
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, ok, detail))
    if not ok:
        FAILS.append(f"{name}: {detail}")


class Scan(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tbody = 0
        self.row = None
        self.rows = []
        self.links = []
        self.ids = set()
        self.has_nav = False
        self.has_help = False
        self.text = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "tbody":
            self.tbody += 1
        if tag == "tr" and self.tbody:
            self.row = []
        if tag in ("a", "link", "script", "img", "source"):
            u = a.get("href") or a.get("src")
            if u:
                self.links.append(u)
                if tag == "a" and self.row is not None:
                    self.row.append(u)
            if tag == "a" and "ncpgambling" in (u or ""):
                self.has_help = True
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "nav":
            self.has_nav = True
        if tag in ("a", "link"):
            pass

    def handle_endtag(self, tag):
        if tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None
        if tag == "tbody":
            self.tbody = max(0, self.tbody - 1)

    def handle_data(self, data):
        self.text.append(data)


def pages():
    out = [os.path.join(HERE, "index.html")]
    for f in sorted(os.listdir(os.path.join(HERE, "pages"))):
        if f.endswith(".html"):
            out.append(os.path.join(HERE, "pages", f))
    return out


def anchors_of(path):
    s = Scan()
    with open(path, encoding="utf-8") as f:
        s.feed(f.read())
    return s.ids


def main():
    src = {s["id"]: s for s in json.load(open(os.path.join(HERE, "data", "sources.json")))["sources"]}
    dead = {s["url"] for s in src.values() if s["http_status"] == "404"}
    documenting = {"pages/sources.html", "pages/flagged.html", "pages/audit.html"}
    all_pages = pages()
    check("page count is 15", len(all_pages) == 15, f"{len(all_pages)} pages")

    anchor_cache = {}
    total_rows = 0
    total_links = 0
    for path in all_pages:
        rel = os.path.relpath(path, HERE).replace(os.sep, "/")
        s = Scan()
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        s.feed(raw)
        total_rows += len(s.rows)
        total_links += len(s.links)
        unsourced = [i for i, r in enumerate(s.rows) if not r]
        check(f"{rel}: every table row has a source link", not unsourced,
              f"{len(unsourced)} unsourced rows (first at index {unsourced[:3]})")
        check(f"{rel}: has navigation", s.has_nav, "no <nav>")
        check(f"{rel}: has helpline footer", s.has_help, "NCPG link missing")
        check(f"{rel}: no TODO/placeholder text", "TODO" not in raw and "Lorem ipsum" not in raw)
        if rel not in documenting:
            bad = [u for u in s.links if u in dead]
            check(f"{rel}: no 404 citations", not bad, f"{bad[:2]}")

        # internal links + anchors
        for u in s.links:
            parts = urlsplit(u)
            if parts.scheme in ("http", "https", "mailto"):
                continue
            target = parts.path
            frag = parts.fragment
            base = os.path.dirname(path)
            if not target:
                tpath = path
            else:
                tpath = os.path.normpath(os.path.join(base, target))
            if not os.path.exists(tpath):
                check(f"{rel}: link target exists", False, u)
                continue
            if frag:
                if tpath not in anchor_cache:
                    anchor_cache[tpath] = anchors_of(tpath)
                if frag not in anchor_cache[tpath]:
                    check(f"{rel}: anchor exists", False, u)
        check(f"{rel}: has a description meta", 'name="description"' in raw)

    check("table rows are numerous enough to be a real dashboard", total_rows > 200, f"{total_rows} rows")

    # JSON integrity
    required = {
        "official/standings_2026.json": ["teams", "source_url"],
        "official/schedule_week10_2026.json": ["games", "byes", "source"],
        "model/week10_lines.json": ["rows", "lookahead_tests", "method"],
        "model/model_card.json": ["holdout", "sigma"],
        "strategies/results.json": ["results", "chosen_thresholds", "splits"],
        "correlations.json": ["rows"],
        "injuries.json": ["explicit_game_status", "qb_depth_changes", "depth_chart"],
        "suggestions.json": ["suggestions", "decision_gates"], "questions.json": ["rows"],
        "flags.json": ["flags"], "sources.json": ["sources"], "audit.json": ["workspaces"],
    }
    for name, keys in required.items():
        p = os.path.join(HERE, "data", name)
        try:
            d = json.load(open(p))
            check(f"data/{name} parses", True)
            for k in keys:
                check(f"data/{name} has '{k}'", k in d, "missing key")
        except Exception as exc:  # noqa: BLE001
            check(f"data/{name} parses", False, str(exc))

    # reproducibility
    with tempfile.TemporaryDirectory() as tmp:
        before = {}
        for p in all_pages:
            before[os.path.relpath(p, HERE)] = open(p, "rb").read()
        subprocess.run([sys.executable, os.path.join(HERE, "build.py")], check=True,
                       stdout=subprocess.DEVNULL)
        for p in all_pages:
            rel = os.path.relpath(p, HERE)
            after = open(p, "rb").read()
            check(f"{rel}: rebuild is byte-identical", before[rel] == after, "content drifted")

    # required disclosure phrases
    idx = open(os.path.join(HERE, "index.html"), encoding="utf-8").read()
    check("dashboard states no validated edge", "do not bet these lines" in idx.lower())
    check("dashboard links the questions register", "pages/questions.html" in idx)

    passed = not FAILS
    print(f"pages={len(all_pages)} rows={total_rows} links={total_links} checks={len(CHECKS)}")
    for name, ok, detail in CHECKS:
        if not ok:
            print(f"FAIL  {name}  {detail}")
    print("RESULT:", "PASS" if passed else f"{len(FAILS)} FAILURES")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
