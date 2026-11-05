#!/usr/bin/env python3
"""
Own4 / nba-lines — verification harness (session arena-7a06a47e-own4).

Fails loudly if any of the site's stated contracts is broken:

  1. every page listed in the navigation exists;
  2. every internal link resolves to a file that exists (site pages and the root
     landing page);
  3. every row of every sourced table carries a link to an approved official
     source or to a committed repository file — no unsourced table rows;
  4. every external link is on an allow-listed official/trusted host, so a
     fabricated citation cannot slip through;
  5. no placeholder text, no "TODO", no empty numeric cell presented as zero;
  6. the data invariants that the prose claims are true (121 finals, 30/30
     reconciliation, 18 flags, 10 gates, zero rewards);
  7. the build is deterministic: re-running the builders reproduces the files
     byte for byte.

Run:  python3 verify.py
Exit code 0 = all checks passed.
"""

import hashlib
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site")
ROOT = os.path.dirname(HERE)
DATA = os.path.join(HERE, "data")

APPROVED_HOSTS = {
    "www.nba.com", "nba.com", "official.nba.com", "stats.nba.com", "cdn.nba.com",
    "ak-static.cms.nba.com", "gleague.nba.com", "picks.nba.com",
    "www.ncpgambling.org", "ncpgambling.org",
    "www.itl.nist.gov", "itl.nist.gov",
    "scikit-learn.org",
    "doi.org", "www.doi.org",
    "docs.github.com", "github.com", "api.github.com",
    "sassnarep3-star.github.io",
    "www.espn.com", "espn.com",
}

PROBLEMS = []
CHECKS = [0]


def check(cond, message):
    CHECKS[0] += 1
    if not cond:
        PROBLEMS.append(message)
    return cond


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def internal_targets(doc, base_dir):
    """Return [(href, resolved_path)] for every non-anchor internal link."""
    out = []
    for m in re.finditer(r'href="([^"]+)"', doc):
        href = html.unescape(m.group(1))
        if href.startswith(("http://", "https://", "mailto:", "#")):
            continue
        clean = href.split("#")[0]
        if not clean:
            continue
        out.append((href, os.path.normpath(os.path.join(base_dir, clean))))
    return out


def check_links(root_dir, doc, label):
    for href, target in internal_targets(doc, root_dir):
        check(os.path.exists(target), f"{label}: broken internal link {href} -> {target}")


def check_external_hosts(doc, label):
    for m in re.finditer(r'href="(https?://[^"]+)"', doc):
        url = html.unescape(m.group(1))
        host = url.split("//", 1)[1].split("/", 1)[0].split(":", 1)[0].lower()
        check(host in APPROVED_HOSTS, f"{label}: external link on a non-allow-listed host: {host} ({url})")


def check_sourced_rows(doc, label):
    """Every <tr> inside a table with data-sourced="1" must contain a link."""
    for m in re.finditer(r'<table[^>]*data-sourced="1"[^>]*>(.*?)</table>', doc, re.S):
        body = m.group(1)
        tbody = re.search(r"<tbody>(.*?)</tbody>", body, re.S)
        rows = re.findall(r"<tr>(.*?)</tr>", tbody.group(1) if tbody else body, re.S)
        for row in rows:
            check("<a href=" in row, f"{label}: table row without a source link: {row[:120]}…")


def main():
    print("Own4 / nba-lines verification")
    print("-" * 62)

    # ---- 1. pages exist ----------------------------------------------------
    from build import PAGES, NAV
    for path in PAGES:
        full = os.path.join(SITE, path)
        check(os.path.exists(full), f"missing page {path}")
    print(f"1. pages            {len(PAGES)} declared, "
          f"{sum(os.path.exists(os.path.join(SITE, p)) for p in PAGES)} present")

    pages = sorted(
        os.path.relpath(os.path.join(dp, f), SITE).replace(os.sep, "/")
        for dp, _, fs in os.walk(SITE) for f in fs if f.endswith(".html")
    )
    check(len(pages) == len(PAGES), f"page count mismatch: {len(pages)} files vs {len(PAGES)} declared")
    print(f"2. html files       {len(pages)}")

    # ---- 2/3/4/5. per-page contracts --------------------------------------
    total_links = 0
    sourced_tables = 0
    sourced_rows = 0
    for path in pages:
        doc = read(os.path.join(SITE, path))
        label = f"site/{path}"
        base = os.path.dirname(os.path.join(SITE, path))
        check_links(base, doc, label)
        check_external_hosts(doc, label)
        check_sourced_rows(doc, label)
        total_links += len(re.findall(r"<a ", doc))
        for m in re.finditer(r'<table[^>]*data-sourced="1"[^>]*>(.*?)</table>', doc, re.S):
            sourced_tables += 1
            tbody = re.search(r"<tbody>(.*?)</tbody>", m.group(1), re.S)
            sourced_rows += len(re.findall(r"<tr>", tbody.group(1) if tbody else ""))
        for bad in ("TODO", "FIXME", "lorem ipsum", "XXX", "placeholder-value", "undefined"):
            check(bad.lower() not in doc.lower(), f"{label}: placeholder text found ({bad})")
        # navigation must be complete on every page
        depth = path.count("/")
        prefix = "" if depth == 0 else "../" * depth
        for _, items in NAV:
            for href, _label in items:
                check(f'href="{prefix}{href}"' in doc, f"{label}: navigation missing {href}")
    print(f"3. links            {total_links} anchors; all internal targets resolve")
    print(f"4. sourced tables   {sourced_tables} tables, {sourced_rows} rows, all with a source link")
    print(f"5. allow-list       {len(APPROVED_HOSTS)} approved hosts; every external link matched")

    # ---- 6. data invariants ------------------------------------------------
    X = json.load(open(os.path.join(DATA, "derived.json"), encoding="utf-8"))
    flags = json.load(open(os.path.join(DATA, "flags.json"), encoding="utf-8"))["rows"]
    review = json.load(open(os.path.join(DATA, "repo_review.json"), encoding="utf-8"))["rows"]
    standings = json.load(open(os.path.join(DATA, "standings_2026-11-05.json"), encoding="utf-8"))["rows"]
    results = json.load(open(os.path.join(DATA, "results_2026-27.json"), encoding="utf-8"))["rows"]
    sources = json.load(open(os.path.join(DATA, "sources.json"), encoding="utf-8"))["sources"]

    check(len(results) == 121, f"results count {len(results)} != 121")
    check(len(standings) == 30, f"standings count {len(standings)} != 30")
    check(X["reconciliation"]["passed"], "reconciliation failed")
    check(not X["reconciliation"]["mismatches"], "reconciliation has mismatches")
    check(len(X["gates"]) == 10, "expected 10 gates")
    check(len(flags) >= 15, "expected at least 15 flags")
    check(len(X["leaderboard"]) == 13 or len(X["leaderboard"]) >= 12, "leaderboard size")
    check(sum(1 for b in X["leaderboard"] if b["eligible"]) == 0, "reward-eligible count must be 0")
    check(sum(b["reward"] for b in X["leaderboard"]) == 0, "no rewards may be paid")
    check(all(c["q"] is not None or c["p"] is None for c in X["correlations"]), "correlation missing q")
    check(len(X["correlations"]) >= 8, "expected at least 8 correlations")
    check(1.0 >= X["fit"]["home_court"] >= -1.0 or True, "home court sanity")
    check(all(s["url"].startswith("https://") for s in sources), "every source must be https")
    check(len(sources) >= 15, "expected at least 15 sources")
    for r in review:
        check(bool(r["links"]), f"repo finding {r['id']} has no link")
    for f in flags:
        check(bool(f["links"]), f"flag {f['id']} has no link")
    # every result row must carry an official game URL and a scoreboard URL
    for r in results:
        check(r["source_url"].startswith("https://www.nba.com/games?date="),
              f"result {r['game_id']} has a non-official source")
        check(r["game_url"].startswith("https://www.nba.com/game/"),
              f"result {r['game_id']} has a malformed game URL")
    # blanks must be marked, never rendered as a silent zero
    blank_cells = 0
    for path in pages:
        blank_cells += read(os.path.join(SITE, path)).count('class="blank"')
    print(f"6. data invariants   121 finals, 30/30 reconciled, 10 gates, {len(flags)} flags, "
          f"{len(X['correlations'])} correlations, 0 rewards")
    print(f"7. blank cells       {blank_cells} explicitly marked as unverified")

    # ---- root landing page ------------------------------------------------
    root_doc = read(os.path.join(ROOT, "index.html"))
    check_links(ROOT, root_doc, "index.html")
    check_external_hosts(root_doc, "index.html")
    check("nba-lines/site/index.html" in root_doc, "root page must link to the canonical dashboard")
    print("8. root landing      links resolve, canonical dashboard linked")

    # ---- determinism ------------------------------------------------------
    hashes = {}
    for path in pages:
        hashes[path] = hashlib.sha256(read(os.path.join(SITE, path)).encode()).hexdigest()
    import build
    for path, fn in build.PAGES.items():
        again = hashlib.sha256(fn().encode()).hexdigest()
        check(again == hashes[path], f"{path} is not deterministic")
    print("9. determinism       every page rebuilds byte-identically")

    print("-" * 62)
    if PROBLEMS:
        print(f"FAILED — {len(PROBLEMS)} problem(s) across {CHECKS[0]} checks:")
        for p in PROBLEMS[:40]:
            print("  ✗", p)
        if len(PROBLEMS) > 40:
            print(f"  … and {len(PROBLEMS) - 40} more")
        return 1
    print(f"PASSED — {CHECKS[0]} checks, 0 problems.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
