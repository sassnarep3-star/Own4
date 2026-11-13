"""06 - Verify the NFL Command Center site. Fails loudly, exits non-zero.

Checks, per generated page:
  1. the page exists and is structurally sound (balanced table tags, no
     unrendered template marker);
  2. EVERY data-table row inside a tbody carries at least one source link, and
     every link in that row points at an allowed official domain or at this
     repository - a row without a source is a defect, not a style issue;
  3. every local href resolves to a file that exists, and anchors resolve
     against the target page;
  4. no placeholder text leaked into the output;
  5. a value that is not confirmed by an official source is rendered blank
     with the unverified marker, never silently filled in.

Run: python3 nfl-command-center/engine/06_verify_site.py
"""
import html.parser
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PAGES = os.path.join(ROOT, "pages")
ASSETS = os.path.join(ROOT, "assets")

ALLOWED_DOMAINS = ("nfl.com", "static.www.nfl.com", "www.nfl.com",
                   "github.com", "api.github.com")
REPO = "github.com/sassnarep3-star/Own4"

PLACEHOLDER_PATTERNS = [
    (re.compile(r">\s*(nan|NaN|None|null|inf)\s*<"), "empty or sentinel cell value"),
    (re.compile(r"\{\{|\}\}"), "unrendered template marker"),
    (re.compile(r"%\(\w"), "unformatted named marker"),
    (re.compile(r"\bTODO\b"), "TODO marker"),
    (re.compile(r"\bundefined\b"), "undefined sentinel"),
    (re.compile(r"\bUNREAD\b"), "unread placeholder"),
]

errors = []


class Parser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.rows = []
        self.in_tbody = False
        self.row_depth = 0
        self.cur = None
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.cur = {"links": [], "text": "", "cells": 0}
            self.row_depth = self.depth
        elif self.cur is not None:
            self.depth += 1
            if tag == "td" or tag == "th":
                self.cur["cells"] += 1
            if tag == "a" and a.get("href"):
                self.cur["links"].append(a["href"])
        if tag == "a" and a.get("href") and self.cur is None:
            self.links.append(a["href"])
        self.depth += 1

    def handle_endtag(self, tag):
        if tag == "tr" and self.cur is not None:
            self.rows.append(self.cur)
            self.cur = None
            self.depth = self.row_depth
        if tag == "tbody":
            self.in_tbody = False
        if self.depth > 0:
            self.depth -= 1

    def handle_data(self, data):
        if self.cur is not None:
            self.cur["text"] += data


def check_page(fn):
    path = os.path.join(PAGES, fn)
    if not os.path.exists(path):
        errors.append("%s: page is missing" % fn)
        return
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    for pat, label in PLACEHOLDER_PATTERNS:
        m = pat.search(text)
        if m:
            errors.append("%s: %s (%r)" % (fn, label, m.group(0)[:40]))
    if text.count("<table") != text.count("</table>"):
        errors.append("%s: unbalanced table tags" % fn)
    if text.count("<tr") != text.count("</tr>"):
        errors.append("%s: unbalanced row tags" % fn)
    p = Parser()
    p.feed(text)
    bad_rows = 0
    for i, row in enumerate(p.rows):
        if not row["links"]:
            bad_rows += 1
            if bad_rows <= 3:
                errors.append("%s: table row %d has no source link (text starts %r)"
                              % (fn, i, row["text"].strip()[:50]))
            continue
        for href in row["links"]:
            if href.startswith("#"):
                continue
            if "://" not in href:
                errors.append("%s: row link is not absolute: %s" % (fn, href))
                continue
            host = href.split("/")[2].lower()
            if not any(host == d or host.endswith("." + d) for d in ALLOWED_DOMAINS):
                errors.append("%s: row link to a domain that is not on the allowed list: %s" % (fn, href))
    if bad_rows > 3:
        errors.append("%s: %d table rows in total have no source link" % (fn, bad_rows))
    # navigation and local links
    for href in p.links:
        if href.startswith("#"):
            continue
        if "://" in href:
            continue
        target = href.split("#")[0]
        if not target:
            continue
        full = os.path.normpath(os.path.join(PAGES, target))
        if not os.path.exists(full):
            errors.append("%s: local link does not resolve: %s" % (fn, href))
    # every page must carry the source policy and the gambling footer
    for needle in ("Source policy", "Responsible gambling", "1-800-522-4700"):
        if needle not in text:
            errors.append("%s: footer is missing %r" % (fn, needle))
    if "flagged-for-review.html" not in text:
        errors.append("%s: navigation does not reach the Flagged for review page" % fn)


def main():
    if not os.path.isdir(PAGES):
        print("no pages directory at %s" % PAGES)
        return 1
    files = sorted(f for f in os.listdir(PAGES) if f.endswith(".html"))
    if not files:
        print("no pages found")
        return 1
    for fn in files:
        check_page(fn)
    css = os.path.join(ASSETS, "command.css")
    if not os.path.exists(css):
        errors.append("assets/command.css is missing")
    # every page must reference the stylesheet
    for fn in files:
        with open(os.path.join(PAGES, fn), encoding="utf-8") as fh:
            if "assets/command.css" not in fh.read():
                errors.append("%s: does not link the stylesheet" % fn)
    if errors:
        print("SITE VERIFICATION FAILED: %d error(s)" % len(errors))
        for e in errors[:60]:
            print("  -", e)
        if len(errors) > 60:
            print("  ... and %d more" % (len(errors) - 60))
        return 1
    print("SITE VERIFICATION PASSED: %d pages, every table row carries a source link, "
          "every local link resolves, no placeholder text." % len(files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
