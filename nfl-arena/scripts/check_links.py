#!/usr/bin/env python3
"""check_links.py — validates the nfl-arena site:
  1. every local href/src resolves to a file in the repo,
  2. every table body row carries at least one https source link,
  3. no TODO/placeholder text is published.
Run from the repo root: python3 nfl-arena/scripts/check_links.py
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARENA = os.path.join(ROOT, "nfl-arena")

errors, checked_links, checked_rows = [], 0, 0

for dirpath, _dirs, files in os.walk(ARENA):
    for fn in sorted(files):
        if not fn.endswith(".html"):
            continue
        path = os.path.join(dirpath, fn)
        text = open(path, encoding="utf-8").read()
        rel = os.path.relpath(path, ROOT)
        if "TODO" in text or "PLACEHOLDER" in text:
            errors.append(f"{rel}: contains TODO/PLACEHOLDER")
        for m in re.finditer(r'(?:href|src)="([^"]+)"', text):
            target = m.group(1)
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target_path = target.split("#")[0]
            if not target_path:
                continue
            resolved = os.path.normpath(os.path.join(dirpath, target_path))
            checked_links += 1
            if not os.path.exists(resolved):
                errors.append(f"{rel}: broken local link -> {target}")
        # every tbody row needs an https source link
        body = re.search(r"<tbody>(.*?)</tbody>", text, re.S)
        if body:
            for row in re.finditer(r"<tr>(.*?)</tr>", body.group(1), re.S):
                checked_rows += 1
                if 'href="https://' not in row.group(1):
                    errors.append(f"{rel}: table row without https source link: {row.group(1)[:120]}")

pages = sum(1 for dp, _, fs in os.walk(ARENA) for f in fs if f.endswith(".html"))
print(f"pages: {pages}")
print(f"local links checked: {checked_links}")
print(f"table rows checked: {checked_rows} (each must carry an https source link)")
if errors:
    print(f"ERRORS: {len(errors)}")
    for e in errors[:40]:
        print(" -", e)
    sys.exit(1)
print("PASS - all local links resolve, all rows source-linked")
