#!/usr/bin/env python3
"""Site audit for nfl-lab/:
1. every <tbody> row contains at least one https link to an allow-listed official host
2. no broken internal links (relative targets must exist)
3. all external links https + allow-listed
4. required pages present; flagged.html exists with items; no non-empty market cells
Exit 1 on any problem.
"""
import os, re, sys, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LAB = os.path.join(ROOT, "nfl-lab")

OK_HOSTS = {
    "www.nfl.com", "nfl.com", "static.www.nfl.com", "operations.nfl.com",
    "www.operations.nfl.com", "stats.nfl.com", "nextgenstats.nfl.com",
    "scikit-learn.org", "www.scikit-learn.org",
    "itl.nist.gov", "www.itl.nist.gov", "www.nist.gov",
    "www.ncpgambling.org", "ncpgambling.org",
}

REQUIRED = ["index.html", "executive-summary.html", "data.html", "signals.html",
            "correlations.html", "own-lines.html", "strategies.html", "leaderboard.html",
            "validation.html", "flagged.html", "sources.html", "assets/style.css"]

errs = []
n_links = n_rows = n_extern = 0

for need in REQUIRED:
    if not os.path.exists(os.path.join(LAB, need)):
        errs.append("missing required page: " + need)

pages = [os.path.join(LAB, f) for f in sorted(os.listdir(LAB)) if f.endswith(".html")]
for p in pages:
    s = open(p).read()
    rel = os.path.relpath(p, ROOT)
    # links
    for m in re.finditer(r'(?:href|src)="([^"]+)"', s):
        u = m.group(1)
        n_links += 1
        if u.startswith(("http://", "https://")):
            n_extern += 1
            h = urllib.parse.urlparse(u)
            if h.scheme != "https":
                errs.append(f"{rel}: non-https link {u}")
            elif h.netloc not in OK_HOSTS:
                errs.append(f"{rel}: host not allow-listed: {u}")
        elif u.startswith(("#", "mailto:")):
            pass
        else:
            tgt = os.path.normpath(os.path.join(os.path.dirname(p), u.split("#")[0].split("?")[0]))
            if not os.path.exists(tgt):
                errs.append(f"{rel}: broken internal link {u}")
    # table rows need official source link
    for tb in re.findall(r"<tbody>(.*?)</tbody>", s, re.S):
        for r in re.findall(r"<tr>(.*?)</tr>", tb, re.S):
            n_rows += 1
            if 'href="https://' not in r:
                errs.append(f"{rel}: table row without https source link: "
                            + re.sub("<[^>]+>", " ", r)[:90].strip())
            else:
                for hm in re.finditer(r'href="(https://[^"]+)"', r):
                    h = urllib.parse.urlparse(hm.group(1))
                    if h.netloc not in OK_HOSTS:
                        errs.append(f"{rel}: row source host not allow-listed: {hm.group(1)}")

# market columns must be blank on own-lines (G7 policy)
ol = open(os.path.join(LAB, "own-lines.html")).read()
for row in re.findall(r"<tbody>(.*?)</tbody>", ol, re.S):
    for r in re.findall(r"<tr>(.*?)</tr>", row, re.S):
        tds = re.findall(r"<td>(.*?)</td>", r, re.S)
        if len(tds) >= 13:
            if tds[9].strip() or tds[10].strip() or tds[11].strip():
                errs.append("own-lines: market cells not blank: " + re.sub("<[^>]+>", " ", r)[:80])

# flagged page non-empty
fl = open(os.path.join(LAB, "flagged.html")).read()
n_flags = len(re.findall(r"<tr>.*?FL-\d+", fl, re.S))
if n_flags < 10:
    errs.append(f"flagged.html has only {n_flags} items (expected >= 10)")

print(f"{len(pages)} pages, {n_links} links ({n_extern} external), {n_rows} table rows audited, "
      f"{n_flags} flagged items, {len(errs)} problems")
for e in errs[:40]:
    print(" -", e)
sys.exit(1 if errs else 0)
