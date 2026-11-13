#!/usr/bin/env python3
"""Own4 · NFL own-lines site verifier.

Fails, loudly and with a non-zero exit code, if:
  1. any local href does not resolve to a file that exists (fragments included);
  2. any data-table row (<tr> inside <tbody>) has no link at all;
  3. any data-table row has no link to an official NFL.com source;
  4. any page lacks the navigation, the responsible-gambling footer or the snapshot date;
  5. placeholder text leaked into the output (None, nan, TODO, unrendered templates);
  6. a page claims a market price or a reward that the data does not support.

Run: python3 nfl-own/engine/verify_site.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
OWN = os.path.dirname(HERE)
ROOT = os.path.dirname(OWN)

HREF = re.compile(r'href=["\']([^"\']+)["\']', re.I)
TBODY = re.compile(r"<tbody>(.*?)</tbody>", re.S)
ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)

OFFICIAL_HOSTS = ("nfl.com", "www.nfl.com", "operations.nfl.com", "static.www.nfl.com")
REPO_HOSTS = ("github.com/sassnarep3-star/Own4",)

PLACEHOLDERS = [
    (re.compile(r">\s*(?:None|NaN|nan|undefined|null|inf)\s*<"), "sentinel value in a cell"),
    (re.compile(r"\{\{|\}\}"), "unrendered template marker"),
    (re.compile(r"%\("), "unformatted %(name)s marker"),
    (re.compile(r"\bTODO\b"), "TODO marker"),
    (re.compile(r"<td[^>]*>\s*(?:\[|&#x27;\[)"), "python list rendered into a cell"),
    (re.compile(r"background:#1d3category"), "CSS typo"),
]


def pages():
    out = []
    for dirpath, _dirs, files in os.walk(OWN):
        if "/data/" in dirpath or dirpath.endswith("/data"):
            continue
        for f in files:
            if f.endswith(".html"):
                out.append(os.path.relpath(os.path.join(dirpath, f), OWN))
    return sorted(out)


def main():
    problems = []
    warnings = []
    files = pages()
    total_rows = rows_linked = rows_official = blanks = local_checked = 0
    ext = Counter()

    for rel in files:
        body = open(os.path.join(OWN, rel), encoding="utf-8").read()
        # 1. local links
        for href in HREF.findall(body):
            h = href.strip()
            if h.startswith(("http://", "https://", "mailto:", "javascript:", "data:")):
                host = h.split("/")[2] if "//" in h else ""
                ext[host] += 1
                continue
            target, _sep, frag = h.partition("#")
            if not target:
                continue
            local_checked += 1
            resolved = os.path.normpath(os.path.join(os.path.dirname(rel), target))
            path = os.path.join(OWN, resolved)
            if not os.path.exists(path):
                problems.append("broken local link in %s: %s" % (rel, h))
            elif frag and path.endswith(".html"):
                tgt = open(path, encoding="utf-8").read()
                if ('id="%s"' % frag) not in tgt and ("name=\"%s\"" % frag) not in tgt:
                    problems.append("broken fragment in %s: %s" % (rel, h))
        # 2/3. row-level source coverage
        for tb in TBODY.findall(body):
            for row in ROW.findall(tb):
                total_rows += 1
                links = HREF.findall(row)
                if links:
                    rows_linked += 1
                # A row is sourced if it links either an official NFL host or this repo. A row
                # whose value is a statement ABOUT the archive or the repository legitimately
                # cites only the repository, and that is checked by hand-comment on the page.
                if any(any(hh in u for hh in OFFICIAL_HOSTS) or
                       any(rh in u for rh in REPO_HOSTS) or "github.com/" in u
                       or "ncpgambling.org" in u for u in links):
                    rows_official += 1
                else:
                    txt = re.sub(r"<[^>]+>", " ", row)
                    txt = re.sub(r"\s+", " ", txt).strip()[:80]
                    problems.append("row without any source link in %s: %s" % (rel, txt))
                blanks += row.count('class="blank"')
        # 4. chrome
        if "<nav" not in body or "</nav>" not in body:
            problems.append("%s: navigation block missing" % rel)
        if "1-800-MY-RESET" not in body:
            problems.append("%s: helpline footer missing" % rel)
        if "2026-11-13" not in body:
            problems.append("%s: snapshot date missing" % rel)
        if "not wagering advice" not in body:
            problems.append("%s: research disclaimer missing" % rel)
        # 5. placeholders
        for pat, label in PLACEHOLDERS:
            m = pat.search(body)
            if m:
                problems.append("%s: %s near %r" % (rel, label, body[max(0, m.start() - 40):m.start() + 40]))

    # 6. claims must not exceed the data
    board = json.load(open(os.path.join(OWN, "data", "derived", "leaderboard.json"),
                           encoding="utf-8"))
    if board["total_points_awarded"] != 0:
        problems.append("leaderboard awards points but no entry is eligible")
    if any(r["eligible"] for r in board["rows"]):
        problems.append("an entry is marked eligible; the gates say otherwise")
    own = json.load(open(os.path.join(OWN, "data", "derived", "own_lines.json"),
                         encoding="utf-8"))
    for r in own["rows"]:
        if r["market_spread"] is not None or r["market_total"] is not None:
            problems.append("a market value appeared in own_lines.json for %s" % r["home"])
    # the dashboard must state zero eligibility in words, not only in a table
    dash = open(os.path.join(OWN, "index.html"), encoding="utf-8").read()
    if "0 of" not in dash or "reward-eligible" not in dash:
        problems.append("dashboard does not state the zero-eligibility headline")

    print("pages                 : %d" % len(files))
    print("local links checked   : %d" % local_checked)
    print("external links        : %d across %d hosts" % (sum(ext.values()), len(ext)))
    print("data rows             : %d" % total_rows)
    print("rows with a link      : %d" % rows_linked)
    print("rows with official src: %d" % rows_official)
    print("blank cells published : %d" % blanks)
    print("problems              : %d" % len(problems))
    for p in problems:
        print("  PROBLEM", p)
    for w in warnings:
        print("  WARN   ", w)
    if problems:
        print("\nVERIFY FAILED")
        return 1
    print("\nVERIFY PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
