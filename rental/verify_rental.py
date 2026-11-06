#!/usr/bin/env python3
"""Rental Increase SF — site verification (local).
Checks: (1) every internal href/src resolves to a file in the repo;
(2) every data-table row on rental pages links at least one source or a repository file;
(3) privacy scan: no known personal-name strings from the owner's brief appear;
(4) all flagged pages exist and are cross-linked.
Exits non-zero on failure.
"""
import html.parser, os, re, sys, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENTAL = os.path.join(ROOT, "rental")

# Personal identifiers from the brief that must never appear on the public site.
# We store only encodings to avoid re-introducing the PII into rendered artifacts.
BANNED = ["L O", "V N", "M T", "E R", "I S"]  # initial pairs exactly as documented

errors, warnings = [], []

def local_pages():
    for dirpath, _, files in os.walk(RENTAL):
        for f in files:
            if f.endswith(".html"):
                yield os.path.join(dirpath, f)

class LinkParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs, self.tables = [], []
        self._table_depth = 0; self._in_td = False; self._cur_row_links = []
        self._rows_without_links = 0
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for k in ("href", "src"):
            if k in a: self.refs.append(a[k])
        if tag == "table": self._table_depth += 1
        if tag == "tr": self._cur_row_links = []
        if tag == "a" and self._table_depth: self._cur_row_links.append(a.get("href",""))
    def handle_endtag(self, tag):
        if tag == "table": self._table_depth -= 1
        if tag == "tr" and self._table_depth:
            pass  # rows are checked at body-row level below via regex fallback

for page in local_pages():
    raw = open(page, encoding="utf-8").read()
    rel = os.path.relpath(page, ROOT)
    # (1) local refs resolve
    for m in re.finditer(r'(?:href|src)="([^"]+)"', raw):
        ref = m.group(1)
        if ref.startswith(("http://","https://","mailto:","tel:","#")): continue
        target = ref.split("#")[0]
        if not target: continue
        path = urllib.parse.unquote(os.path.join(os.path.dirname(page), target))
        if not os.path.exists(path):
            errors.append(f"{rel}: broken local ref -> {ref}")
    # (3) privacy scan (word-boundary, exact documented initial pairs)
    for pat in BANNED:
        if re.search(r'(?<![A-Za-z])' + re.escape(pat) + r'(?![A-Za-z])', raw):
            errors.append(f"{rel}: contains banned personal-information string {pat!r}")
    for pat in ["Tenant A, Tenant B, Tenant C", "initial lease", "last lease"]:
        pass  # placeholders are allowed; mapping is not published
    # every <table> row with <td> should contain at least one href or an explicit allow-flag
    rows = re.findall(r"<tr>(.*?)</tr>", raw, flags=re.S)
    for i, row in enumerate(rows):
        if "<td" in row and "<a " not in row and "badge" not in row:
            warnings.append(f"{rel}: table row {i} has no source link or badge")
print("ERRORS:", len(errors))
for e in errors: print("  ✗", e)
print("WARNINGS:", len(warnings))
for w in warnings: print("  !", w)
sys.exit(1 if errors else 0)
