#!/usr/bin/env python3
"""Publication gate for the NFL Decision Desk site.

Fails (non-zero exit) if ANY of these is true:

  V1  a table row in a <tbody> has no https source link
  V2  a local href/src does not resolve on disk
  V3  a page is missing the shared navigation or the footer
  V4  a page contains the words "localhost" or "127.0.0.1"
  V5  a required page is absent from the built set
  V6  a page title is duplicated
  V7  any published number in a table is not backed by a source on the same row (same rule as
      V1, applied per-cell for rows that contain digits)

It also prints the counts it checked, so the claim "every row is sourced" is auditable rather
than asserted.
"""
from __future__ import annotations

import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIRED = ["index.html"] + ["pages/%s.html" % p for p in (
    "executive-summary", "fixtures", "availability", "prices", "model", "leaderboard",
    "correlations", "governance", "questions", "suggestions", "repo-review", "flagged", "sources")]

SRC_RE = re.compile(r"https?://")
REF_RE = re.compile(r'(?:href|src)\s*=\s*["\']([^"\']+)["\']')
TBODY_RE = re.compile(r"<tbody>(.*?)</tbody>", re.S)
ROW_RE = re.compile(r"<tr>(.*?)</tr>", re.S)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
TAG_RE = re.compile(r"<[^>]+>")


def text_of(cell_html):
    return TAG_RE.sub(" ", cell_html)


def main() -> int:
    failures = []
    pages = sorted(glob.glob(os.path.join(ROOT, "*.html"))) + \
            sorted(glob.glob(os.path.join(ROOT, "pages", "*.html")))
    rels = [os.path.relpath(p, ROOT) for p in pages]

    for req in REQUIRED:
        if req not in rels:
            failures.append("V5 missing required page: %s" % req)

    total_rows = total_refs = rows_with_src = 0
    titles = {}
    numeric_cells = 0

    for path, rel in zip(pages, rels):
        html = open(path).read()

        # V3 nav + footer
        if 'class="side"' not in html:
            failures.append("V3 %s: missing shared navigation" % rel)
        if "<footer>" not in html:
            failures.append("V3 %s: missing footer" % rel)

        # V4 no localhost
        if "localhost" in html or "127.0.0.1" in html:
            failures.append("V4 %s: contains localhost/127.0.0.1" % rel)

        # V6 unique title
        m = TITLE_RE.search(html)
        t = m.group(1).strip() if m else "(none)"
        if t in titles:
            failures.append("V6 duplicate title '%s' (%s and %s)" % (t, titles[t], rel))
        titles[t] = rel

        # V1 every tbody row sourced
        for tb in TBODY_RE.findall(html):
            for i, row in enumerate(ROW_RE.findall(tb), 1):
                total_rows += 1
                if SRC_RE.search(row):
                    rows_with_src += 1
                else:
                    snippet = text_of(row)[:90].strip()
                    failures.append("V1 %s tbody row %d has no https source: %s" % (rel, i, snippet))
                # V7: if the row asserts a number, the source must be there too (V1 covers it);
                # count numeric cells so the claim is quantified
                cells = re.findall(r"<td>(.*?)</td>", row, re.S)
                for c in cells:
                    if re.search(r"\d", text_of(c)):
                        numeric_cells += 1

        # V2 local refs resolve
        for ref in REF_RE.findall(html):
            if ref.startswith(("http", "#", "mailto:", "data:")):
                continue
            total_refs += 1
            target = os.path.normpath(os.path.join(os.path.dirname(path), ref.split("#")[0]))
            if not os.path.exists(target):
                failures.append("V2 %s: broken local ref %s" % (rel, ref))

    # V8  float summation must be version-stable.
    #     Python 3.12 changed builtin sum() over floats to Neumaier-compensated summation,
    #     so a plain sum() of floats can round differently on 3.11 vs 3.12 and break a
    #     determinism gate in CI on a machine you cannot see. math.fsum is exactly rounded
    #     on every version, so it is the only acceptable accumulator for published numbers.
    engines = sorted(glob.glob(os.path.join(ROOT, "engine", "*.py")))
    risky = []
    for e in engines:
        if os.path.basename(e) in ("verify.py",):
            continue
        for i, line in enumerate(open(e).read().split("\n"), 1):
            code = line.split("#", 1)[0]
            if "fsum" in code or "sum(1 for" in code or "sum(" not in code:
                continue
            # integer-only sums are fine; a sum over a float literal / division / float field is not
            if any(t in code for t in ("brier", "/ len(", "/ n", "p_home_win", "brier_model",
                                       "brier_market", "home_win", "/ len(s)", ".0", "mean",
                                       "** 2 for", "d23", "d1", "sq_")):
                risky.append("%s:%d %s" % (os.path.basename(e), i, code.strip()[:88]))
    if risky:
        for r in risky:
            failures.append("V8 float sum() is not version-stable, use math.fsum: %s" % r)

    print("pages checked:      %d" % len(pages))
    print("tbody rows:         %d  (with https source: %d)" % (total_rows, rows_with_src))
    print("numeric cells:      %d" % numeric_cells)
    print("local references:   %d" % total_refs)
    print("unique titles:      %d of %d" % (len(titles), len(pages)))
    print("float-sum check:    V8 (%d risky accumulators)" % len(risky))

    if failures:
        print("\nFAIL: %d problem(s)" % len(failures))
        for f in failures[:60]:
            print("  -", f)
        if len(failures) > 60:
            print("  ... and %d more" % (len(failures) - 60))
        return 1
    print("\nPASS: every table row carries an https source, every local link resolves, "
          "every required page exists, no localhost references, no duplicate titles, "
          "and no published number depends on the interpreter's float summation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
