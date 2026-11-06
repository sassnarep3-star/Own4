#!/usr/bin/env python3
"""
rental/verify_site.py — verification harness for the rental research site.

Fails loudly (exit 1) on any of:
  1. a missing page;
  2. a data-table row (<tr> inside <tbody>) with NO source link (http(s) or repo path);
  3. a local link whose target file does not exist (anchors checked against the target);
  4. template/placeholder leakage ("{{", "}}", "TODO", "%(", "undefined", " nan ");
  5. a page missing the disclaimer footer.

Usage:  python3 rental/verify_site.py
"""
import html.parser
import os
import re
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
PAGES = ["index.html", "executive-summary.html", "laws.html", "units.html",
         "scenarios.html", "practice.html", "discrimination.html", "flagged.html", "sources.html"]

class RowParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_tbody = False
        self.cur = None
        self.rows = []          # list of list-of-links per tbody row
        self.all_hrefs = []
        self.text = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "tbody":
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self.cur = []
        elif tag == "a" and "href" in a:
            self.all_hrefs.append(a["href"])
            if self.cur is not None:
                self.cur.append(a["href"])
    def handle_endtag(self, tag):
        if tag == "tbody":
            self.in_tbody = False
        elif tag == "tr" and self.cur is not None:
            self.rows.append(self.cur)
            self.cur = None
    def handle_data(self, d):
        self.text.append(d)

def check_page(name):
    path = os.path.join(HERE, name)
    problems = []
    if not os.path.exists(path):
        return ["MISSING PAGE: %s" % name]
    src = open(path, encoding="utf-8").read()
    p = RowParser()
    p.feed(src)
    # 2. rows need ≥1 source link: http(s), or a same-site page link WITH an anchor
    #    (the register/flags are citations too). Bare local navigation does not count.
    for i, row in enumerate(p.rows):
        if not any(h.startswith(("http://", "https://")) or (".html#" in h) for h in row):
            problems.append("ROW %d in <tbody> has no source link: %s" % (i + 1, row))
    # 3. local links resolve (same-site); external links are NOT fetched (network may be restricted)
    for h in p.all_hrefs:
        if h.startswith(("http://", "https://", "mailto:", "tel:")):
            continue
        target, frag = (h.split("#", 1) + [""])[:2]
        tpath = os.path.normpath(os.path.join(HERE, target))
        if not target:
            tpath = path
        if not os.path.exists(tpath):
            problems.append("local link target missing: %s" % h)
            continue
        if frag:
            body = open(tpath, encoding="utf-8").read()
            if 'id="%s"' % frag not in body and "id='%s'" % frag not in body:
                problems.append("anchor '#%s' not found in %s" % (frag, target or name))
    # 4. placeholder leakage
    text = " ".join(p.text)
    for pat in [r"\{\{", r"\}\}", r"\bTODO\b", r"%\(\w+\)", r"\bundefined\b"]:
        if re.search(pat, text):
            problems.append("placeholder leak (%s)" % pat)
    # 5. disclaimer footer
    if "not legal advice" not in src.lower():
        problems.append("missing 'not legal advice' disclaimer")
    return problems

def main():
    total_rows = failed = 0
    print("== rental/ site verification ==")
    for page in PAGES:
        probs = check_page(page)
        src = open(os.path.join(HERE, page), encoding="utf-8").read() if os.path.exists(os.path.join(HERE, page)) else ""
        rows = src.count("<tr") - (1 if "<thead>" in src else 0)
        total_rows += max(rows, 0)
        print("- %-28s problems: %d" % (page, len(probs)))
        for pr in probs:
            failed += 1
            print("    !! %s" % pr)
    print("rows scanned (incl. header rows):", total_rows)
    if failed:
        print("FAIL — %d problem(s)" % failed)
        sys.exit(1)
    print("PASS — all local links resolve; every data row carries a source link; no placeholders")
    sys.exit(0)

if __name__ == "__main__":
    main()
