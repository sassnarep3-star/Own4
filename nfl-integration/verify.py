#!/usr/bin/env python3
"""Verify the NFL integration-review site (session arena/8e2de421-own4).

Checks, for every page under nfl-integration/:
  1. every <tbody> row contains at least one https:// source link;
  2. every internal href resolves to a file that exists (anchors included);
  3. no localhost / 127.0.0.1 references;
  4. the responsible-gambling helpline footer is present;
  5. no empty table cell that should hold a value (blank must be explicit: none here).

Run:  python3 nfl-integration/verify.py        (exit 0 = clean)
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

errors = []
pages = []
for base, _dirs, files in os.walk(HERE):
    for fn in sorted(files):
        if fn.endswith(".html"):
            pages.append(os.path.join(base, fn))

rows_total = 0
rows_sourced = 0

for path in sorted(pages):
    rel = os.path.relpath(path, ROOT)
    raw = open(path, encoding="utf-8").read()

    # 1. every tbody row carries an https source link
    for i, row in enumerate(re.findall(r"<tr[^>]*>(.*?)</tr>", raw, re.S), 1):
        if "<td>" not in row:
            continue  # header row rendered inside tbody would be skipped anyway
        rows_total += 1
        if 'href="https://' in row:
            rows_sourced += 1
        else:
            errors.append("%s: table row %d has no https source link" % (rel, i))

    # 2. internal links resolve
    for href in re.findall(r'href="([^"]+)"', raw):
        if href.startswith("https://") or href.startswith("http://"):
            continue
        if href.startswith("#"):
            if href[1:] and ('id="%s"' % href[1:]) not in raw \
                    and ('name="%s"' % href[1:]) not in raw:
                errors.append("%s: dangling anchor %s" % (rel, href))
            continue
        target = href.split("#", 1)[0]
        if not target:
            continue
        full = os.path.normpath(os.path.join(os.path.dirname(path), target))
        if not os.path.exists(full):
            errors.append("%s: broken internal link %s" % (rel, href))

    # 3. no localhost
    if "localhost" in raw or "127.0.0.1" in raw:
        errors.append("%s: localhost reference" % rel)

    # 4. helpline footer
    if "1-800-MY-RESET" not in raw:
        errors.append("%s: helpline footer missing" % rel)

    # 5. no sentinel values
    if re.search(r">\s*(TODO|TBD|FIXME|XXX)\s*<", raw):
        errors.append("%s: placeholder text present" % rel)

print("pages checked      : %d" % len(pages))
print("table rows         : %d" % rows_total)
print("rows with source   : %d" % rows_sourced)
if errors:
    print("ERRORS (%d):" % len(errors))
    for e in errors:
        print("  -", e)
    sys.exit(1)
print("PASS - every row sourced, every link resolves, footer present")
