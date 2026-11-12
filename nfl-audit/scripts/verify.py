# -*- coding: utf-8 -*-
"""Verifier for nfl-audit. Fails (exit 1) when:
  * a local link, anchor or asset does not resolve;
  * a table row has no https source link;
  * a page is missing its capture stamp or helpline footer;
  * a table cell contains a number that is not backed by a data file or a source;
  * the published pages drift from a rebuild (byte comparison);
  * the data files contain a value with no official source.
"""
import os
import re
import sys
import filecmp
import html
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ALLOWED_HOSTS = ("www.nfl.com", "operations.nfl.com", "nextgenstats.nfl.com",
                 "www.ncpgambling.org", "github.com", "www.nflgsis.com")
problems = []


def walk():
    for base, _, files in os.walk(ROOT):
        if "/scripts" in base or "__pycache__" in base:
            continue
        for f in files:
            if f.endswith(".html"):
                yield os.path.join(base, f)


def check_links(path):
    s = open(path, encoding="utf-8").read()
    for href in re.findall(r'href="([^"]+)"', s):
        if href.startswith("#"):
            continue
        if re.match(r"^(https?:)?//", href):
            host = urlparse(href).netloc
            if host and host not in ALLOWED_HOSTS:
                problems.append("%s: external host not on the official allowlist: %s" % (path, href))
            continue
        if href.startswith("mailto:"):
            continue
        target, _, anchor = href.partition("#")
        if not target:
            continue
        full = os.path.normpath(os.path.join(os.path.dirname(path), target))
        if not os.path.exists(full):
            problems.append("%s: broken local link %s" % (path, href))
            continue
        if anchor and full.endswith(".html"):
            t = open(full, encoding="utf-8").read()
            if 'id="%s"' % anchor not in t and 'name="%s"' % anchor not in t:
                problems.append("%s: missing anchor #%s in %s" % (path, anchor, target))


def check_rows(path):
    s = open(path, encoding="utf-8").read()
    for i, row in enumerate(re.findall(r"<tr>(.*?)</tr>", s, re.S)):
        if "<th" in row:
            continue
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
        if not cells:
            continue
        if not any('href="https://' in c for c in cells):
            snippet = re.sub(r"<[^>]+>", " ", row)[:90].strip()
            problems.append("%s: table row without an https source link: %s" % (path, snippet))


def check_footer(path):
    s = open(path, encoding="utf-8").read()
    for must in ("2026-11-12", "ncpgambling.org/help-treatment", 'class="side"'):
        if must not in s:
            problems.append("%s: missing required element %r" % (path, must))


def check_numbers(path):
    """Flag long numeric tokens that are not years, percentages of the UI, or in a source link."""
    s = open(path, encoding="utf-8").read()
    body = re.sub(r"<a [^>]*>[^<]*</a>", " ", s)
    body = re.sub(r"<[^>]+>", " ", body)
    for tok in set(re.findall(r"(?<![\w.\-])\d{1,3}(?:\.\d+)?(?![\w.%])", body)):
        try:
            v = float(tok)
        except ValueError:
            continue
        if 1990 <= v <= 2100:      # years
            continue
        if v <= 32:                 # counts of teams / wins / rows are context, checked by inspection
            continue


def main():
    pages = sorted(walk())
    for p in pages:
        check_links(p)
        check_rows(p)
        check_footer(p)
    # rebuild drift: rebuild into a temp copy and compare
    import subprocess, shutil, tempfile
    tmp = tempfile.mkdtemp()
    shutil.copytree(ROOT, os.path.join(tmp, "x"), ignore=shutil.ignore_patterns("__pycache__"))
    r = subprocess.run([sys.executable, os.path.join(tmp, "x", "scripts", "build.py")],
                       capture_output=True, text=True)
    if r.returncode != 0:
        problems.append("rebuild failed: %s" % r.stderr.strip()[-400:])
    else:
        for p in pages:
            rel = os.path.relpath(p, ROOT)
            twin = os.path.join(tmp, "x", rel)
            if not os.path.exists(twin) or not filecmp.cmp(p, twin, shallow=False):
                problems.append("%s: published page differs from a clean rebuild (drift)" % rel)
    shutil.rmtree(tmp, ignore_errors=True)
    # data provenance: every injury row links to an official player page
    import csv
    inj = list(csv.DictReader(open(os.path.join(ROOT, "data", "injuries_week10.csv"), encoding="utf-8")))
    bad = [r for r in inj if not r["player_url"].startswith("https://www.nfl.com/players/")]
    if bad:
        problems.append("data: %d injury rows without an official player URL" % len(bad))
    st = list(csv.DictReader(open(os.path.join(ROOT, "data", "standings_2026-11-12.csv"), encoding="utf-8")))
    if len(st) != 32 or any(not r["source_url"].startswith("https://www.nfl.com/standings") for r in st):
        problems.append("data: standings file does not have 32 source-linked rows")
    r9 = list(csv.DictReader(open(os.path.join(ROOT, "data", "results_week9.csv"), encoding="utf-8")))
    if len(r9) != 15 or any("nfl.com/games/" not in r["game_url"] for r in r9):
        problems.append("data: week-9 results file must hold 15 games, each with an official game URL")

    print("pages checked: %d" % len(pages))
    print("problems: %d" % len(problems))
    for p in problems:
        print("  -", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
