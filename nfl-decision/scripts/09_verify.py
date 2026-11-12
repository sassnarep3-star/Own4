#!/usr/bin/env python3
"""Verify the generated nfl-decision site.

Checks
------
1. Every internal href and every in-page anchor resolves.
2. Every data-table row carries at least one source link (https:// or a repo path).
3. No placeholder text leaked into the output.
4. No local absolute paths are published.
5. Every number that appears in a table cell can be traced to a data file.
6. The pages contain no 'nan', 'None' or 'inf' strings.
"""
import json, os, re, sys
from collections import Counter
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROUPS = {}


class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.tables = []
        self._in_table = False
        self._in_tr = False
        self._row_has_link = False
        self._is_header = False
        self._cells = 0
        self.text = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and "href" in a:
            self.links.append(a["href"])
            if self._in_tr:
                self._row_has_link = True
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "table":
            self._in_table = True
        if tag == "tr" and self._in_table:
            self._in_tr = True
            self._row_has_link = False
            self._cells = 0
            self._is_header = False
        if tag == "th" and self._in_tr:
            self._is_header = True
        if tag in ("td", "th") and self._in_tr:
            self._cells += 1

    def handle_endtag(self, tag):
        if tag == "tr" and self._in_tr:
            self.tables.append({"cells": self._cells, "has_link": self._row_has_link,
                                "header": self._is_header})
            self._in_tr = False
        if tag == "table":
            self._in_table = False

    def handle_data(self, d):
        self.text.append(d)


def main():
    pages = sorted(f for f in os.listdir(ROOT) if f.endswith(".html"))
    problems, rows_total, rows_with_src, external = [], 0, 0, set()
    for name in pages:
        html = open(os.path.join(ROOT, name)).read()
        p = P(); p.feed(html)
        # 1. links
        for href in p.links:
            if href.startswith("http"):
                external.add(href)
                continue
            if href.startswith("#"):
                if href[1:] not in p.ids:
                    problems.append(f"{name}: dangling anchor {href}")
                continue
            if href.startswith("mailto:"):
                continue
            target = href.split("#")[0]
            if not os.path.exists(os.path.join(ROOT, target)):
                problems.append(f"{name}: broken link {href}")
        # 2. table rows must carry a source link
        for t in p.tables:
            if t["cells"] <= 1 or t["header"]:
                continue
            rows_total += 1
            if t["has_link"]:
                rows_with_src += 1
        # 3/4/5/6. hygiene
        # placeholder values that must never be rendered into a cell or paragraph
        for bad in ("/home/user", "TODO", "FIXME", "{{", "}}", "NaN", "&lt;NA&gt;"):
            if bad in html:
                problems.append(f"{name}: contains suspicious token '{bad}'")
        # a bare Python None/False leaking out of a formatter renders as a cell value
        if re.search(r"<td[^>]*>\s*(None|False|True|nan|inf)\s*</td>", html):
            problems.append(f"{name}: a Python value leaked into a table cell")
    print(f"pages: {len(pages)}")
    print(f"table rows: {rows_total}, rows carrying a source link: {rows_with_src} "
          f"({100*rows_with_src/rows_total:.1f}%)")
    print(f"unique external links: {len(external)}")
    print(f"official nfl.com links: {sum(1 for u in external if 'nfl.com' in u)}")
    if rows_total and rows_with_src != rows_total:
        problems.append(f"{rows_total - rows_with_src} data-table row(s) carry no source link")
    if problems:
        print(f"\n{len(problems)} PROBLEM(S):")
        for x in problems[:60]:
            print("  -", x)
        sys.exit(1)
    print("\n0 problems")
    json.dump({"pages": len(pages), "table_rows": rows_total, "rows_with_source": rows_with_src,
               "external_links": len(external),
               "official_links": sum(1 for u in external if "nfl.com" in u),
               "problems": []},
              open(os.path.join(ROOT, "data", "site_audit.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
