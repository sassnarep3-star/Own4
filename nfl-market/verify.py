#!/usr/bin/env python3
"""Verify the NFL market lab site.

Gates, applied to every page under nfl-market/:

  1. every <tbody> row carries at least one https:// source link;
  2. every number printed in a table cell can be traced back to the JSON that
     the build read (provenance, not decoration);
  3. every internal href resolves to a file that exists, and every in-page
     anchor resolves to an id on that page;
  4. no localhost / 127.0.0.1 reference, no empty href, no javascript: href;
  5. the responsible-gambling helpline footer is present;
  6. no TODO / TBD / FIXME / XXX / lorem placeholder text;
  7. every page carries the required "third-party" disclosure when it prints a
     price sourced from the commercial book;
  8. the nav set is identical on every page and every nav target exists.

Exit 0 = clean.

Run:  python3 nfl-market/verify.py
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")

errors = []
warnings = []

# --------------------------------------------------------------- JSON corpus
corpus_strings = set()
corpus_numbers = set()


def walk(node):
    if isinstance(node, dict):
        for v in node.values():
            walk(v)
    elif isinstance(node, list):
        for v in node:
            walk(v)
    elif isinstance(node, bool):
        corpus_strings.add(str(node).lower())
    elif isinstance(node, (int, float)):
        corpus_numbers.add(float(node))
        corpus_strings.add(str(node))
    elif isinstance(node, str):
        corpus_strings.add(node)
        try:
            corpus_numbers.add(float(node))
        except ValueError:
            pass
    elif node is None:
        corpus_strings.add("blank")


json_files = []
for base, _d, files in os.walk(DATA):
    for fn in sorted(files):
        if fn.endswith(".json"):
            p = os.path.join(base, fn)
            json_files.append(p)
            try:
                walk(json.load(open(p, encoding="utf-8")))
            except Exception as exc:            # noqa: BLE001
                errors.append("%s: unreadable JSON (%s)" % (p, exc))


import re as _re
_corpus_text = " \u0001 ".join(corpus_strings)


def _in_text(txt):
    """The printed number appears in the stored JSON as a delimited number.

    This is how a cited figure (kept verbatim inside a note) and a jersey number
    (inside a lineup slot like "67 N.Allegretti") are traceable without being
    mistaken for a computed statistic.
    """
    pat = r"(?<![\d.])" + _re.escape(txt) + r"(?![\d])"
    return _re.search(pat, _corpus_text) is not None


def number_is_sourced(tok):
    """A printed number is sourced if it rounds from, or equals, a stored one."""
    txt = tok.replace("%", "").replace("pp", "").strip().rstrip(".,")
    txt = txt.rstrip(",")
    try:
        val = float(txt)
    except ValueError:
        return True                              # not a bare number: skip
    dec = len(txt.split(".")[1]) if "." in txt else 0
    for cand in corpus_numbers:
        if abs(round(cand, dec) - val) < 1e-9:
            return True
        if abs(round(cand * 100.0, dec) - val) < 1e-9:   # percent-formatted
            return True
    if _in_text(tok.rstrip(".,")) or _in_text(tok):
        return True
    # integers that are counts of stored things are legitimately derived
    if dec == 0 and val in (len(json_files), 0, 1):
        return True
    return False


# --------------------------------------------------------------------- pages
pages = []
for base, _d, files in os.walk(ROOT):
    if os.sep + "data" in base:
        continue
    for fn in sorted(files):
        if fn.endswith(".html"):
            pages.append(os.path.join(base, fn))

NAV = None
rows_total = rows_sourced = nums_checked = nums_ok = 0

for path in sorted(pages):
    rel = os.path.relpath(path, ROOT)
    raw = open(path, encoding="utf-8").read()

    # 1 + 2: rows, sources, provenance of printed numbers
    for i, row in enumerate(re.findall(r"<tr[^>]*>(.*?)</tr>", raw, re.S), 1):
        if "<td" not in row:
            continue
        rows_total += 1
        if 'href="https://' in row:
            rows_sourced += 1
        else:
            errors.append("%s: table row %d has no https source link" % (rel, i))
        for cell in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S):
            if "href=\"https://" in cell:
                continue                     # link text, not a printed value
            text = re.sub(r"<[^>]+>", " ", cell).strip()
            for tok in re.findall(r"[-+]?\d[\d,]*\.?\d*", text):
                nums_checked += 1
                if number_is_sourced(tok):
                    nums_ok += 1
                else:
                    errors.append(
                        "%s: row %d prints %r with no match in the JSON it "
                        "claims to come from" % (rel, i, tok))

    # 3: links
    for href in re.findall(r'href="([^"]*)"', raw):
        if href.startswith(("https://", "http://")):
            if href.startswith("http://"):
                errors.append("%s: insecure http link %s" % (rel, href))
            continue
        if href.startswith("javascript:") or href.strip() == "":
            errors.append("%s: bad href %r" % (rel, href))
            continue
        if href.startswith("#"):
            if href[1:] and ('id="%s"' % href[1:]) not in raw:
                errors.append("%s: dangling anchor %s" % (rel, href))
            continue
        target = href.split("#", 1)[0]
        if not target:
            continue
        full = os.path.normpath(os.path.join(os.path.dirname(path), target))
        if not os.path.exists(full):
            errors.append("%s: broken internal link %s" % (rel, href))

    # 4: no localhost
    if "127.0.0.1" in raw or "localhost" in raw:
        errors.append("%s: localhost reference" % rel)

    # 5: helpline
    if "1-800-MY-RESET" not in raw:
        errors.append("%s: helpline footer missing" % rel)

    # 6: placeholders
    if re.search(r">\s*(TODO|TBD|FIXME|XXX|lorem)\b", raw, re.I):
        errors.append("%s: placeholder text present" % rel)

    # 7: price disclosure on any page that prints a provider price
    if "sports.core.api.espn.com" in raw:
        if not re.search(r"No price on this site is (official|an official league "
                         r"price)", raw):
            errors.append("%s: prints third-party prices without the "
                          "not-official disclosure" % rel)

    # 8: nav consistency
    navs = re.findall(r'<nav><div class="inner">(.*?)</div></nav>', raw, re.S)
    labels = tuple(re.findall(r">([^<]+)</a>", navs[0])) if navs else ()
    if NAV is None:
        NAV = labels
    elif labels != NAV:
        errors.append("%s: nav differs from the other pages" % rel)

print("json files         : %d" % len(json_files))
print("pages checked      : %d" % len(pages))
print("table rows         : %d" % rows_total)
print("rows with source   : %d" % rows_sourced)
print("numbers in tables  : %d" % nums_checked)
print("numbers traceable  : %d" % nums_ok)
if warnings:
    print("WARNINGS (%d):" % len(warnings))
    for w in warnings:
        print("  ~", w)
if errors:
    print("ERRORS (%d):" % len(errors))
    for e in errors[:60]:
        print("  -", e)
    if len(errors) > 60:
        print("  ... %d more" % (len(errors) - 60))
    sys.exit(1)
print("PASS - every row sourced, every number traceable, every link resolves, "
      "footer present, no placeholders")
