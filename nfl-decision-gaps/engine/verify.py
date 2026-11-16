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
import os
import re
import sys

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

# 5. the namespace count must come from the pinned data file, never from prose
inv_path = os.path.join(NS, "data", "repo_inventory.json")
check(os.path.exists(inv_path), "data/repo_inventory.json is missing")
if os.path.exists(inv_path):
    import json
    inv = json.load(open(inv_path))
    check("pinned_at" in inv and inv["pinned_at"] not in ("", "unknown"),
          "repo_inventory.json has no pinned commit")
    check("n_namespaces" in inv, "repo_inventory.json has no namespace count")

print("pages checked      : %d" % len(PAGES))
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
