#!/usr/bin/env python3
"""
Own4 — site verification. Fails loudly, exits non-zero.

Checks, per generated page:
  1. the page exists and is valid-enough HTML (balanced <table>/<tr> counts, no unclosed template markers);
  2. EVERY data-table row (<tr> inside <tbody>) contains at least one source link to an allowed
     official domain or to this repository — a row without a source is a defect, not a style issue;
  3. every local href resolves to a file that exists (anchors are checked against the target page);
  4. every page carries the navigation, the responsible-gambling footer and the helpline number;
  5. no placeholder text leaked into the output (None, nan, {, %(, TODO, undefined);
  6. expected row counts match the underlying data (30 standings, 30 team stats, 85 games, ...);
  7. the rebuild is deterministic (caller may compare git diff).

Run: python3 verification/verify_site.py
"""

import html.parser
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

OFFICIAL_DOMAINS = (
    "nba.com", "official.nba.com", "www.nba.com", "stats.nba.com", "gleague.nba.com",
    "ncpgambling.org", "www.ncpgambling.org", "api.github.com", "github.com",
)

PAGES = [
    ("index.html", 10),
    ("verified/executive-summary.html", 7),
    ("verified/standings.html", 30),
    ("verified/team-stats.html", 30),
    ("verified/games.html", 102),
    ("verified/own-lines.html", 2),
    ("verified/strategies.html", 11),
    ("verified/validation.html", 13),
    ("verified/correlations.html", 14),
    ("verified/backtest.html", 44),
    ("verified/leaderboard.html", 8),
    ("verified/sources.html", 13),
    ("verified/audit.html", 24),
    ("verified/flagged.html", 13),
]

# precise defect patterns: a bare cell value, an unformatted template marker, a JS sentinel.
# ("None of it is official" and "Governance" are legitimate English and must not trip the check.)
PLACEHOLDER_PATTERNS = [
    (re.compile(r">\s*(nan|NaN|None|null|inf)\s*<"), "empty/sentinel cell value"),
    (re.compile(r"\{\{|\}\}"), "unrendered template marker"),
    (re.compile(r"%\("), "unformatted %(name)s marker"),
    (re.compile(r"\bTODO\b"), "TODO marker"),
    (re.compile(r"\bundefined\b"), "undefined sentinel"),
    (re.compile(r"<td[^>]*>\s*(\[&#x27;|\[')"), "python list rendered into a cell"),
]

errors = []
warnings = []


class P(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.ids = set()
        self.tbody_rows = 0
        self.in_tbody = False
        self.row_links = []
        self.cur_row = None
        self.depth_table = 0
        self.text = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and "href" in a:
            self.links.append(a["href"])
            if self.cur_row is not None:
                self.cur_row.append(a["href"])
        if tag == "script" and a.get("src"):
            self.links.append(a["src"])
        if tag == "link" and a.get("href"):
            self.links.append(a["href"])
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.tbody_rows += 1
            self.cur_row = []
        if tag == "table":
            self.depth_table += 1

    def handle_endtag(self, tag):
        if tag == "tr" and self.cur_row is not None:
            self.row_links.append(self.cur_row)
            self.cur_row = None
        if tag == "tbody":
            self.in_tbody = False
        if tag == "table":
            self.depth_table -= 1

    def handle_data(self, data):
        self.text.append(data)


def allowed(href):
    if href.startswith("#"):
        return True
    m = re.match(r"https?://([^/]+)/", href)
    if not m:
        return False
    host = m.group(1).lower()
    return any(host == d or host.endswith("." + d) for d in OFFICIAL_DOMAINS)


def resolve_local(page_rel, href):
    """Resolve a relative href against the page, returning (path, anchor)."""
    if href.startswith("#"):
        return page_rel, href[1:]
    if re.match(r"^[a-z]+:", href):
        return None, None
    target, _, anchor = href.partition("#")
    target = target.split("?")[0]
    base = os.path.dirname(page_rel)
    full = os.path.normpath(os.path.join(base, target))
    return full, anchor


def check_page(rel, min_rows):
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        errors.append("%s: missing" % rel)
        return
    raw = open(path, encoding="utf-8").read()
    if raw.count("<table") != raw.count("</table>"):
        errors.append("%s: unbalanced <table> tags" % rel)
    if raw.count("<tr") != raw.count("</tr>"):
        errors.append("%s: unbalanced <tr> tags" % rel)

    p = P()
    p.feed(raw)

    if "Own4" not in raw or 'class="side"' not in raw:
        errors.append("%s: navigation block missing" % rel)
    if "1-800-MY-RESET" not in raw or "ncpgambling.org" not in raw:
        errors.append("%s: responsible-gambling footer missing" % rel)
    if "assets/canonical.js" not in raw:
        errors.append("%s: canonical script reference missing" % rel)

    for pattern, label in PLACEHOLDER_PATTERNS:
        m = pattern.search(raw)
        if m:
            errors.append("%s: %s leaked into output (%r)" % (rel, label, m.group(0)))

    # every data row needs a source link
    for i, links in enumerate(p.row_links, start=1):
        if not links:
            errors.append("%s: table row %d has no link at all" % (rel, i))
            continue
        if not any(allowed(h) for h in links):
            errors.append("%s: table row %d has no official/repository source link (%s)"
                          % (rel, i, ", ".join(links[:3])))

    if p.tbody_rows < min_rows:
        errors.append("%s: expected at least %d data rows, found %d" % (rel, min_rows, p.tbody_rows))

    # local links
    for href in p.links:
        if allowed(href):
            continue
        target, anchor = resolve_local(rel, href)
        if target is None:
            errors.append("%s: non-http, non-local href %r" % (rel, href))
            continue
        full = os.path.join(ROOT, target)
        if not os.path.exists(full):
            errors.append("%s: broken local link %r -> %s" % (rel, href, target))
            continue
        if anchor and full.endswith(".html"):
            tp = P()
            tp.feed(open(full, encoding="utf-8").read())
            if anchor not in tp.ids:
                errors.append("%s: anchor %r not found in %s" % (rel, href, target))


def check_data_counts():
    """Row counts must match the data files, not just the minimum."""
    d = os.path.join(HERE, "data")
    an = json.load(open(os.path.join(HERE, "out", "analysis.json")))
    rec = json.load(open(os.path.join(HERE, "out", "reconciliation.json")))
    stand = json.load(open(os.path.join(d, "standings.json")))["rows"]
    tstats = json.load(open(os.path.join(d, "team_stats.json")))["rows"]
    fresh = json.load(open(os.path.join(d, "games_fresh.json")))["rows"]
    old = json.load(open(os.path.join(ROOT, "official", "games.json")))["rows"]
    expect = {
        "verified/standings.html": len(stand),
        "verified/team-stats.html": len(tstats),
        "verified/games.html": len(fresh) + len(old) + len(json.load(open(os.path.join(d, "calendar.json")))["days"]),
        "verified/strategies.html": len(an["strategies"]) + 3,
        "verified/validation.html": len(an["gates"]) + len(an["calibration"]),
        "verified/backtest.html": len(an["graded_games"]) + len(an["blocks"]) + 6,
        "verified/leaderboard.html": len(an["strategies"]),
    }
    for rel, n in expect.items():
        raw = open(os.path.join(ROOT, rel), encoding="utf-8").read()
        p = P()
        p.feed(raw)
        if p.tbody_rows != n:
            errors.append("%s: %d data rows but the data holds %d" % (rel, p.tbody_rows, n))

    if len(stand) != 30 or len(tstats) != 30:
        errors.append("data: expected 30 standings and 30 team-stat rows")
    if rec["summary"]["fail"]:
        errors.append("reconciliation: %d checks failed" % rec["summary"]["fail"])


def main():
    for rel, min_rows in PAGES:
        check_page(rel, min_rows)
    check_data_counts()

    total_rows = 0
    for rel, _ in PAGES:
        p = P()
        p.feed(open(os.path.join(ROOT, rel), encoding="utf-8").read())
        total_rows += len(p.row_links)

    print("pages checked: %d" % len(PAGES))
    print("data rows with source links: %d" % total_rows)
    for w in warnings:
        print("WARN", w)
    if errors:
        print("\nFAILED with %d problem(s):" % len(errors))
        for e in errors:
            print("  -", e)
        return 1
    print("all checks passed: every data row is source-linked, every local link resolves.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
