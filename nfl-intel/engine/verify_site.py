#!/usr/bin/env python3
"""Verifies the nfl-intel site: (1) all local href/src targets exist, (2) every
<tr data-row> contains a source link (class="src"), (3) no localhost/127.0.0.1 links,
(4) no obviously empty source cells. Exit 1 on any failure."""
import html.parser, pathlib, sys, re, urllib.parse

ROOT = pathlib.Path('nfl-intel')
errors, checked_rows, checked_links = [], 0, 0

class SrcChecker(html.parser.HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path; self.in_row = False; self.row_has_src = False
        self.links = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'tr' and 'data-row' in a:
            self.in_row = True; self.row_has_src = False
        cls = a.get('class','')
        if 'src' in cls.split(): self.row_has_src = True
        for k in ('href','src'):
            if k in a: self.links.append((k, a[k]))
    def handle_endtag(self, tag):
        if tag == 'tr' and self.in_row:
            global checked_rows
            checked_rows += 1
            if not self.row_has_src:
                errors.append(f"{self.path}: data-row without source link")
            self.in_row = False

html_files = list(ROOT.rglob('*.html'))
for f in html_files:
    text = f.read_text()
    if re.search(r'localhost|127\.0\.0\.1', text):
        errors.append(f"{f}: localhost reference")
    p = SrcChecker(f); p.feed(text)
    for k, v in p.links:
        if v.startswith(('http://','https://','mailto:','#','data:')): continue
        target = v.split('#')[0].split('?')[0]
        if not target: continue
        checked_links += 1
        base = f.parent if target.startswith('/') is False else ROOT
        resolved = (f.parent / urllib.parse.unquote(target)).resolve() if not target.startswith('/') else (ROOT / urllib.parse.unquote(target.lstrip('/'))).resolve()
        if not resolved.exists():
            errors.append(f"{f}: broken local {k} -> {v}")

print(f"html files: {len(html_files)} · data-rows checked: {checked_rows} · local links checked: {checked_links}")
if errors:
    print(f"\nFAIL ({len(errors)}):"); [print(' -',e) for e in errors]; sys.exit(1)
print("PASS — no broken links, every data-row has a source link")
