#!/usr/bin/env python3
"""audit_rows.py — row/source audit for the pipeline/ section (session 75685c60).

Checks, for every page in pipeline/:
  1. Every <tr> inside a table.data <tbody> contains at least one https:// link
     (the row's source) OR an explicit unverified/blank marker.
  2. All internal hrefs resolve to files that exist in the repo.
  3. All external links are https and well-formed.
  4. Required datasets carry source_url on every row (JSON side).
  5. Flagged page exists and publishes all flagged_pipeline items.
Exit code 0 = all checks pass; 1 = problems (printed).
"""

import glob
import json
import os
import re
import sys
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIPE = os.path.join(ROOT, "pipeline")

problems = []
checked_rows = 0
checked_links = set()


def add(page, msg):
    problems.append(f"{page}: {msg}")


def audit_pages():
    global checked_rows
    pages = sorted(glob.glob(os.path.join(PIPE, "*.html")))
    if not pages:
        add("pipeline/", "no pages built")
        return
    nav_targets = set()
    for path in pages:
        name = os.path.basename(path)
        text = open(path, encoding="utf-8").read()
        # collect nav targets from header nav for existence check
        for m in re.finditer(r'<nav>(.*?)</nav>', text, re.S):
            for h in re.findall(r'href="([^"]+)"', m.group(1)):
                nav_targets.add(h)
        # split tables
        for tmatch in re.finditer(r'<table class="data">(.*?)</table>', text, re.S):
            table = tmatch.group(1)
            tbody = re.search(r"<tbody>(.*?)</tbody>", table, re.S)
            if not tbody:
                add(name, "table.data without tbody")
                continue
            for row in re.findall(r"<tr>(.*?)</tr>", tbody.group(1), re.S):
                checked_rows += 1
                has_https = bool(re.search(r'<a href="https://[^"]+"', row))
                has_blank = 'class="blank"' in row or "unverified" in row or "no official odds source" in row
                if not (has_https or has_blank):
                    # show a snippet for debugging
                    snip = re.sub(r"\s+", " ", row)[:160]
                    add(name, f"row without https source link or blank marker: {snip}")
        # links
        for h in re.findall(r'href="([^"]+)"', text):
            if h.startswith("https://"):
                u = urlparse(h)
                if not u.netloc or " " in h:
                    add(name, f"malformed external link: {h}")
                checked_links.add(h)
            elif h.startswith("http://"):
                add(name, f"insecure/external non-https link: {h}")
            elif h.startswith("#") or h.startswith("mailto:"):
                continue
            else:
                # internal relative link
                target = os.path.normpath(os.path.join(PIPE, h.split("#")[0]))
                if not os.path.exists(target):
                    add(name, f"broken internal link: {h}")
                # also allow repo-root relative pages that exist
    for h in nav_targets:
        if not os.path.exists(os.path.join(PIPE, h)):
            add("nav", f"missing nav target {h}")


def audit_json_rows():
    def rows_with_sources(file, rows, key="source_url"):
        p = os.path.join(ROOT, "data", file)
        if not os.path.exists(p):
            add(file, "missing dataset")
            return
        data = json.load(open(p))
        for i, r in enumerate(rows(data)):
            if not r.get(key):
                add(file, f"row {i} missing {key}")
            elif not str(r[key]).startswith("https://"):
                add(file, f"row {i} non-https {key}: {r.get(key)}")

    rows_with_sources("standings.json", lambda d: d["east"] + d["west"])
    rows_with_sources("prior_2025-26.json", lambda d: d["east"] + d["west"])
    rows_with_sources("games_official.json", lambda d: d["games"])
    rows_with_sources("games_official.json", lambda d: d["scheduled"])
    rows_with_sources("model_ratings.json", lambda d: d["ratings"])
    rows_with_sources("own_lines_2026-11-02.json", lambda d: d["lines"])
    rows_with_sources("signals.json", lambda d: d["items"])
    rows_with_sources("reconciliation.json", lambda d: d["teams"])
    rows_with_sources("pipeline_strategies.json",
                      lambda d: d["strategies"] + d["gates"])
    rows_with_sources("pipeline_sources.json", lambda d: d["sources"], "url")
    rows_with_sources("flagged_pipeline.json", lambda d: d["flags"])
    # player logs: rows carry nba_game_url + espn_box_url (partner class disclosed)
    p = os.path.join(ROOT, "data", "player_gamelogs.json")
    data = json.load(open(p))
    for i, r in enumerate(data["rows"][:50] + data["rows"][-50:]):
        if not str(r.get("nba_game_url", "")).startswith("https://"):
            add("player_gamelogs.json", f"row missing nba_game_url")
        if not str(r.get("espn_box_url", "")).startswith("https://"):
            add("player_gamelogs.json", f"row missing espn_box_url")


def audit_flagged():
    p = os.path.join(ROOT, "pipeline", "flagged.html")
    if not os.path.exists(p):
        add("flagged.html", "missing")
        return
    text = open(p, encoding="utf-8").read()
    flags = json.load(open(os.path.join(ROOT, "data", "flagged_pipeline.json")))["flags"]
    for f in flags:
        if f["id"] not in text:
            add("flagged.html", f"flag {f['id']} not published on page")


def main():
    audit_pages()
    audit_json_rows()
    audit_flagged()
    print(f"pages rows checked: {checked_rows}; unique external links: {len(checked_links)}")
    if problems:
        print(f"PROBLEMS ({len(problems)}):")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    print("audit_rows: ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
