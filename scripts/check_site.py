#!/usr/bin/env python3
"""Site checks: every local link/asset exists; external links are https on allow-listed official hosts;
every table body row carries at least one https link (official source)."""
import os, re, sys, urllib.parse
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OK_HOSTS = {"www.nba.com", "github.com", "docs.github.com", "sassnarep3-star.github.io"}
errs = []; n_links = n_rows = 0; pages = []
for dp, dn, fn in os.walk(ROOT):
    dn[:] = [d for d in dn if d not in (".git", "node_modules")]
    if os.path.relpath(dp, ROOT).split(os.sep)[0] != "lab": continue   # only this session's data lab (lab/); the framework site/docs are other sessions' and have their own tests
    pages += [os.path.join(dp, f) for f in fn if f.endswith(".html")]
for p in sorted(pages):
    s = open(p).read(); rel = os.path.relpath(p, ROOT)
    for m in re.finditer(r'(?:href|src)="([^"]+)"', s):
        u = m.group(1); n_links += 1
        if u.startswith(("http://", "https://")):
            h = urllib.parse.urlparse(u)
            if h.scheme != "https" or h.netloc not in OK_HOSTS: errs.append(f"{rel}: external link not allow-listed: {u}")
        elif u.startswith(("#", "mailto:")): pass
        else:
            t = os.path.normpath(os.path.join(os.path.dirname(p), u.split("#")[0].split("?")[0]))
            if not os.path.exists(t): errs.append(f"{rel}: broken local link {u}")
    for tb in re.findall(r"<tbody>(.*?)</tbody>", s, re.S):
        for r in re.findall(r"<tr>(.*?)</tr>", tb, re.S):
            n_rows += 1
            if 'href="https://' not in r: errs.append(f"{rel}: table row without https source link: {re.sub('<[^>]+>', ' ', r)[:80]}")
for need in (".nojekyll", "lab/index.html", "lab/pages/flagged.html", "lab/pages/executive-summary.html", "lab/assets/style.css"):
    if not os.path.exists(os.path.join(ROOT, need)): errs.append("missing " + need)
print(f"{len(pages)} pages, {n_links} links, {n_rows} table rows checked, {len(errs)} problems")
for e in errs[:50]: print(" -", e)
sys.exit(1 if errs else 0)
