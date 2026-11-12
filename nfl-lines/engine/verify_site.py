#!/usr/bin/env python3
"""Site verification: link integrity, source coverage and blank-cell accounting.

Run after build_site.py. Exits non-zero if a link is broken or a data row has no
source link at all.
"""
from __future__ import annotations

import os
import re
import sys
from collections import Counter

import dataset as D

ROOT = D.ROOT
HREF = re.compile(r'href=["\']([^"\']+)["\']', re.I)
TR = re.compile(r"<tr\b", re.I)
TBODY = re.compile(r"<tbody>(.*?)</tbody>", re.S)

OFFICIAL_HOSTS = ("www.nfl.com", "operations.nfl.com", "static.www.nfl.com")


def pages():
    out = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        if ".git" in dirpath:
            continue
        for f in filenames:
            if f.endswith(".html"):
                out.append(os.path.relpath(os.path.join(dirpath, f), ROOT))
    return sorted(out)


def check():
    problems = []
    files = pages()
    total_rows = 0
    rows_with_any_link = 0
    rows_with_official_link = 0
    blank_cells = 0
    local_checked = 0

    for f in files:
        body = open(os.path.join(ROOT, f), "r", encoding="utf-8").read()
        # local link integrity
        for href in HREF.findall(body):
            h = href.strip()
            if not h or h.startswith(("http://", "https://", "mailto:", "#", "javascript:", "data:")):
                continue
            target = h.split("?")[0].split("#")[0]
            if not target or h.startswith("#"):
                continue
            local_checked += 1
            resolved = os.path.normpath(os.path.join(os.path.dirname(f), target))
            if not os.path.exists(os.path.join(ROOT, resolved)):
                problems.append("broken local link in %s: %s" % (f, h))
        # row-level source coverage (data rows only)
        for tb in TBODY.findall(body):
            for row in re.findall(r"<tr[^>]*>(.*?)</tr>", tb, re.S):
                total_rows += 1
                links = HREF.findall(row)
                if links:
                    rows_with_any_link += 1
                if any(any(hh in u for hh in OFFICIAL_HOSTS) for u in links):
                    rows_with_official_link += 1
                blank_cells += row.count("class=\"blank\"") + row.count("class='blank'")
                if not links:
                    problems.append("row without any link in %s: %s"
                                    % (f, re.sub(r"<[^>]+>", " ", row)[:90].strip()))

    return {
        "pages": len(files),
        "local_links_checked": local_checked,
        "data_rows": total_rows,
        "rows_with_any_link": rows_with_any_link,
        "rows_with_official_link": rows_with_official_link,
        "blank_cells_published": blank_cells,
        "problems": problems,
    }


def main():
    r = check()
    print("pages                    :", r["pages"])
    print("local links checked      :", r["local_links_checked"])
    print("data rows                :", r["data_rows"])
    print("rows with any link       :", r["rows_with_any_link"])
    print("rows with an official link:", r["rows_with_official_link"])
    print("blank (unverified) cells :", r["blank_cells_published"])
    if r["problems"]:
        print("\nPROBLEMS (%d):" % len(r["problems"]))
        for p in r["problems"][:40]:
            print("  -", p)
        sys.exit(1)
    print("\nOK - no broken links and every data row carries a link.")


if __name__ == "__main__":
    main()
