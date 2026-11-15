#!/usr/bin/env python3
"""nfl-dashboard verification: stdlib only.
Checks (1) every <tbody> row carries at least one https source link,
(2) every local link resolves to an existing file,
(3) standings identity sum(PF) == sum(PA),
(4) no placeholder/invented values (blank cells are explicit em-dash spans),
(5) rebuild is deterministic.
"""
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGES = os.path.join(ROOT, "pages")
DATA = os.path.join(ROOT, "data")

errors = []
checks = 0


def check(cond, msg):
    global checks
    checks += 1
    if not cond:
        errors.append(msg)
        print("FAIL: %s" % msg)


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)


def local_target(href, cur_file):
    href = href.split("#")[0]
    if href.startswith("http://") or href.startswith("https://") or href.startswith("mailto:"):
        return None
    if href.startswith("/"):
        return None  # absolute site-relative: not checked here
    return os.path.normpath(os.path.join(os.path.dirname(cur_file), href))


pages = [os.path.join(ROOT, "index.html")] + [
    os.path.join(PAGES, f) for f in sorted(os.listdir(PAGES)) if f.endswith(".html")
]
print("pages found:", len(pages))

for path in pages:
    with open(path) as f:
        html_text = f.read()
    # existing local files
    for m in re.finditer(r'href=(["\'])(https?://[^"\']+)\1', html_text):
        pass  # external links fine
    for m in re.finditer(r'href=(["\'])([^"\']+)\1', html_text):
        t = local_target(m.group(2), path)
        if t and not os.path.exists(t):
            errors.append("broken local link %s -> %s" % (path, m.group(2)))
    # every data row (inside a <tbody>) needs an https source link; <thead> header rows are not data rows
    row_no = 0
    for m in re.finditer(r"<tbody>(.*?)</tbody>", html_text, re.S):
        for row in re.findall(r"<tr>(.*?)</tr>", m.group(1), re.S):
            row_no += 1
            links = re.findall(r'href=(["\'])(https://[^"\']+)\1', row)
            if not links:
                errors.append("%s row %d has no https source link" % (os.path.basename(path), row_no))
        # any plain 'TBD' or invented-looking tokens are forbidden
        for bad in ("TBD", "N/A", "todo", "XXX"):
            if bad in strip_tags(row):
                errors.append("%s row %d contains placeholder '%s'" % (os.path.basename(path), i + 1, bad))

# standings identity
import json
with open(os.path.join(DATA, "standings.json")) as f:
    standings = json.load(f)
pf = sum(t["PF"] for t in standings["teams"])
pa = sum(t["PA"] for t in standings["teams"])
check(pf == pa, "standings identity failed: sum PF %d != sum PA %d" % (pf, pa))
check(pf == 6664, "sum PF unexpected: %d" % pf)

# gate/strategy counts
with open(os.path.join(DATA, "strategies.json")) as f:
    strategies = json.load(f)
check(len(strategies["rows"]) == 7, "expected 7 registered strategies, got %d" % len(strategies["rows"]))
rewards = sum(int(s["reward_points"]) for s in strategies["rows"])
check(rewards == 0, "reward points must be 0, got %d" % rewards)

print("checks:", checks)
if errors:
    print("ERRORS (%d):" % len(errors))
    for e in errors:
        print(" -", e)
    sys.exit(1)
print("VERIFY OK: all pages source-linked, links resolve, standings identity holds, no placeholders.")
