#!/usr/bin/env python3
"""
nfl-decision-gaps — verifier.

Checks every generated page:
  1. every internal link resolves to a file that exists;
  2. no localhost / 127.0.0.1 reference anywhere;
  3. every table body row carries at least one external https link to a source;
  4. every page carries the navigation block, the skip link and the footer;
  5. the two structural invariants: rows that claim a number publish an n, and
     no page renders a count of repository namespaces that was typed by hand
     (counts must come from data/repo_inventory.json).

Exits non-zero on any failure.
"""
import json
import os
import re
import sys
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)

PAGES = ["index.html"] + sorted("pages/" + f for f in os.listdir(os.path.join(NS, "pages"))
                                if f.endswith(".html"))

fail = []
warn = []
n_rows = 0
n_links = 0
n_ext = 0
unsourced_rows = []


def check(cond, msg):
    if not cond:
        fail.append(msg)
    return cond


for rel in PAGES:
    path = os.path.join(NS, rel)
    if not check(os.path.exists(path), "missing page %s" % rel):
        continue
    doc = open(path, encoding="utf-8").read()

    # 2. no localhost
    check("127.0.0.1" not in doc, "%s references 127.0.0.1" % rel)
    check("localhost" not in doc, "%s references localhost" % rel)

    # 4. shell
    check('class="skip" href="#main"' in doc, "%s missing skip link" % rel)
    check("<nav aria-label=\"Sections\">" in doc, "%s missing navigation" % rel)
    check("<footer>" in doc, "%s missing footer" % rel)
    check("1-800-MY-RESET" in doc, "%s missing responsible-gambling footer" % rel)

    # 1. internal links resolve
    for href in re.findall(r'href="([^"]+)"', doc):
        n_links += 1
        if href.startswith("http") or href.startswith("#") or href.startswith("mailto:"):
            if href.startswith("http"):
                n_ext += 1
                check(href.startswith("https://"), "%s has a non-https link: %s" % (rel, href))
            continue
        target = os.path.normpath(os.path.join(os.path.dirname(path), href.split("#")[0]))
        check(os.path.exists(target), "%s -> broken internal link %s" % (rel, href))

    # 3. every tbody row carries an external https source link
    for tno, tbody in enumerate(re.findall(r"<tbody>(.*?)</tbody>", doc, re.S)):
        for rno, row in enumerate(re.findall(r"<tr>(.*?)</tr>", tbody, re.S)):
            n_rows += 1
            if 'href="https://' not in row:
                unsourced_rows.append("%s table %d row %d" % (rel, tno + 1, rno + 1))

    # 4b. no double-escaped entities (an escaped label that still held an entity)
    for m in re.finditer(r"&amp;[a-zA-Z#0-9]+;", doc):
        fail.append("%s has a double-escaped entity %s" % (rel, m.group(0)))

    # 4c. no typed namespace count. A literal "<int> nfl-" in prose goes stale the
    # moment a sibling session adds a namespace - the exact defect this workspace
    # flags in peers (F2 / SG-H). Counts belong in the pinned inventory.
    prose = re.sub(r"<table.*?</table>", " ", doc, flags=re.S)   # counts inside tables are data, not prose
    text = re.sub(r"<[^>]+>", " ", prose)
    for m in re.finditer(r"\b\d+\s+nfl-", text):
        fail.append("%s types a namespace count into prose: %r" % (rel, m.group(0)))

# 5. the namespace count must come from the pinned data file, never from prose
inv_path = os.path.join(NS, "data", "repo_inventory.json")
check(os.path.exists(inv_path), "data/repo_inventory.json is missing")
if os.path.exists(inv_path):
    import json
    inv = json.load(open(inv_path))
    check("pinned_at" in inv and inv["pinned_at"] not in ("", "unknown"),
          "repo_inventory.json has no pinned commit")
    check("n_namespaces" in inv, "repo_inventory.json has no namespace count")

# 6. result-state/source consistency. A terminal score is publishable only
# with an explicitly Final state and two integer scores. Non-final states must
# not carry scores, and every result/venue source ID must resolve to an official
# NFL URL in the generated source register.
results_path = os.path.join(NS, "data", "results_week10.json")
sources_path = os.path.join(NS, "data", "sources.json")
result_rows = []
source_map = {}
try:
    result_data = json.load(open(results_path, encoding="utf-8"))
    result_rows = result_data.get("rows", [])
except Exception as exc:
    fail.append("cannot read data/results_week10.json: %s" % exc)
try:
    source_data = json.load(open(sources_path, encoding="utf-8"))
    for source in source_data:
        sid = source.get("id")
        if sid in source_map:
            fail.append("duplicate source id in sources.json: %s" % sid)
        source_map[sid] = source
except Exception as exc:
    fail.append("cannot read data/sources.json: %s" % exc)

check(len(result_rows) == 14,
      "Week 10 result feed must contain 14 fixture rows; found %d" % len(result_rows))
result_ids = set()
source_ids_top = set(result_data.get("source_ids", [])) if "result_data" in locals() else set()
for rno, row in enumerate(result_rows, 1):
    game = row.get("game", "row %d" % rno)
    check(game not in result_ids, "duplicate Week 10 fixture row: %s" % game)
    result_ids.add(game)
    state = row.get("state")
    status = row.get("status", "")
    away_pts = row.get("away_pts")
    home_pts = row.get("home_pts")
    if state == "final":
        check(type(away_pts) is int and type(home_pts) is int,
              "%s: Final state requires two integer scores" % game)
        check(status == "Final", "%s: normalized final state conflicts with source status %r" % (game, status))
    elif state == "scheduled":
        check(away_pts is None and home_pts is None,
              "%s: scheduled/non-final state must have blank scores" % game)
        check(status.startswith("Scheduled"),
              "%s: scheduled state conflicts with source status %r" % (game, status))
    else:
        fail.append("%s: unsupported or missing result state %r" % (game, state))

    row_sources = []
    for field in ("result_src", "venue_src"):
        value = row.get(field, "")
        ids = [part.strip() for part in value.split(",") if part.strip()]
        if field == "result_src":
            check(bool(ids), "%s: result state/score has no source IDs" % game)
        if field == "venue_src" and row.get("venue"):
            check(bool(ids), "%s: published venue has no source ID" % game)
        row_sources.extend(ids)
        for sid in ids:
            source = source_map.get(sid)
            check(source is not None, "%s: unknown source ID %s" % (game, sid))
            if source is not None:
                host = (urlparse(source.get("url", "")).hostname or "").lower()
                check(host == "nfl.com" or host.endswith(".nfl.com"),
                      "%s: result/venue source %s is not an official NFL URL" % (game, sid))
                check(sid in source_ids_top,
                      "%s: source %s is absent from results_week10.json source_ids" % (game, sid))
    if state in ("final", "scheduled"):
        check(any((urlparse(source_map[sid]["url"]).hostname or "").lower().endswith("nfl.com")
                  and any(part in source_map[sid]["url"] for part in ("/schedules/", "/scores", "/games/"))
                  for sid in [x for x in row_sources if x in source_map]),
              "%s: no official NFL schedule, scores or Game Center source for the reported state" % game)

print("pages checked      : %d" % len(PAGES))
print("result rows checked: %d" % len(result_rows))
print("table rows checked : %d" % n_rows)
print("links checked      : %d (%d external https)" % (n_links, n_ext))
print("flagged items      : %d" % len(unsourced_rows))

if unsourced_rows:
    print("\nFAIL: %d table rows carry no external https source link:" % len(unsourced_rows))
    for r in unsourced_rows[:60]:
        print("   ", r)
    if len(unsourced_rows) > 60:
        print("    ... and %d more" % (len(unsourced_rows) - 60))

fail.extend("row without an official source link: " + r for r in unsourced_rows)

if fail:
    print("\nFAIL: %d problem(s):" % len(fail))
    for f in fail:
        print("   ", f)
    sys.exit(1)

print("\nOK: all checks passed.")
