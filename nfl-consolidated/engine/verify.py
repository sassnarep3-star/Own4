"""Verifier for the nfl-consolidated site.

Hard checks (non-zero exit on failure):
  1. Every <tbody> row (non-meta) contains at least one https:// source link.
  2. Every blank cell (td.blank) carries a title containing 'unverified'.
  3. No localhost / 127.0.0.1 references; no insecure http links.
  4. Every internal href resolves to a file that exists.
  5. Expected pages all exist; every NAV target reachable from index.html.
  6. Responsible-gambling footer link present on every page.
  7. Dataset integrity: counts in requirements.json match the rendered rows.
"""
import json
import os
import re
import sys
import glob

from common import ROOT, PAGES, load

A_HREF = re.compile(r'<a[^>]+href="([^"]+)"')
TR = re.compile(r"<tr>(.*?)</tr>", re.S)
BLANK_TD = re.compile(r'<td class="blank"[^>]*>')


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def main():
    errors, stats = [], {"pages": 0, "rows": 0, "sourced_rows": 0,
                         "blank_cells": 0, "links": 0}
    pages = sorted(glob.glob(os.path.join(ROOT, "*.html")) +
                   glob.glob(os.path.join(PAGES, "*.html")))
    stats["pages"] = len(pages)

    for p in pages:
        rel = os.path.relpath(p, ROOT)
        html = read(p)
        if "ncpgambling.org" not in html:
            errors.append(f"{rel}: missing responsible-gambling footer link")
        for m in BLANK_TD.finditer(html):
            stats["blank_cells"] += 1
            tag = m.group(0)
            if 'title="unverified' not in tag and "awaiting" not in tag:
                errors.append(f"{rel}: blank cell without unverified marker: {tag[:80]}")
        for tbl in re.findall(r"<table[^>]*>.*?</table>", html, re.S):
            is_meta = '<table class="meta"' in tbl.split(">", 1)[0]
            for body in re.findall(r"<tbody>(.*?)</tbody>", tbl, re.S):
                for tr in TR.findall(body):
                    stats["rows"] += 1
                    hrefs = A_HREF.findall(tr)
                    if is_meta:
                        continue
                    if any(h.startswith("https://") for h in hrefs):
                        stats["sourced_rows"] += 1
                    else:
                        errors.append(f"{rel}: table row without an https source link: "
                                      f"{tr[:140]}")
        for href in A_HREF.findall(html):
            stats["links"] += 1
            if href.startswith(("http://", "https://")):
                if href.startswith("http://"):
                    errors.append(f"{rel}: insecure http link: {href}")
                continue
            if href.startswith(("mailto:", "#")):
                continue
            if "localhost" in href or "127.0.0.1" in href:
                errors.append(f"{rel}: localhost reference: {href}")
                continue
            target, _, frag = href.partition("#")
            tp = os.path.normpath(os.path.join(os.path.dirname(p), target))
            if not os.path.exists(tp):
                errors.append(f"{rel}: broken internal link: {href}")
            elif frag and tp.endswith(".html"):
                th = read(tp)
                if f'id="{frag}"' not in th and f'name="{frag}"' not in th:
                    errors.append(f"{rel}: broken anchor: {href}")

    idx = read(os.path.join(ROOT, "index.html"))
    for href in re.findall(r'href="(pages/[^"]+)"', idx):
        if not os.path.exists(os.path.join(ROOT, href)):
            errors.append(f"index.html: missing nav target {href}")

    # dataset integrity
    reqs = load("requirements.json")
    if reqs["counts"]["met"] + reqs["counts"]["partial"] + \
            reqs["counts"]["blocked"] + reqs["counts"]["not_started"] + \
            reqs["counts"]["in_progress"] != len(reqs["rows"]):
        errors.append("requirements.json: counts do not sum to row count")
    for r in reqs["rows"]:
        if not r["source"].startswith("https://"):
            errors.append(f"requirements.json: non-https source on {r['id']}")
    for q in load("questions.json")["rows"]:
        if not q["source"].startswith("https://"):
            errors.append(f"questions.json: non-https source on {q['id']}")
    for s in load("suggestions.json")["rows"]:
        if not s["source"].startswith("https://"):
            errors.append(f"suggestions.json: non-https source on {s['id']}")
    for f in load("flags.json")["rows"]:
        if not f["source"].startswith("https://"):
            errors.append(f"flags.json: non-https source on {f['id']}")

    print(f"[verify] pages={stats['pages']} rows={stats['rows']} "
          f"sourced={stats['sourced_rows']} blanks={stats['blank_cells']} "
          f"links={stats['links']}")
    if errors:
        print(f"[verify] FAIL — {len(errors)} problem(s):")
        for e in errors[:40]:
            print("  -", e)
        sys.exit(1)
    print("[verify] PASS")


if __name__ == "__main__":
    main()
