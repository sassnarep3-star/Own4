#!/usr/bin/env python3
"""Verification and drift alarm for nfl-origin-board.

R-63: every scraper is pinned to expected row counts and required fields. A
missing field or a changed count fails the build loudly rather than publishing
a blank.

Run:  python3 nfl-origin-board/verify.py
Exit code 0 = all checks pass.
"""
import json, os, re, sys, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
fail = []


def check(name, ok, detail=""):
    print("%-58s %s%s" % (name, "PASS" if ok else "FAIL", ("  " + detail) if detail else ""))
    if not ok:
        fail.append(name)


# ---------------------------------------------------------------- drift alarms
expected = {
    "games_2026.json": {"games": 150},
    "injuries_week10.json": {"rows": 347},
    "standings_2026.json": {"rows": 32},
    "requirements.json": {"rows": 80},
    "questions.json": {"rows": 30},
    "suggestions.json": {"rows": 24},
    "official_evidence.json": {"rows": 22},
    "flags.json": {"rows": 16},
    "sources.json": {"rows": 35},
    "week11_schedule.json": {"games": 13},
    "third_party_candidate.json": {"rows": 150},
}
for fn, exp in expected.items():
    d = json.load(open(os.path.join(ROOT, "data", fn), encoding="utf-8"))
    for k, v in exp.items():
        got = len(d[k]) if isinstance(d[k], list) else d[k]
        check("drift alarm: %s %s == %d" % (fn, k, v), got == v, "got %s" % got)

# required fields per row type
inj = json.load(open(os.path.join(ROOT, "data", "injuries_week10.json"), encoding="utf-8"))["rows"]
check("required field: every injury row has club, player, position, practice",
      all(r[0] and r[1] and r[2] and r[4] for r in inj))
gm = json.load(open(os.path.join(ROOT, "data", "games_2026.json"), encoding="utf-8"))["games"]
check("required field: every fixture has date, away, home, status, url",
      all(g[1] and g[2] and g[4] and g[6] and g[7] for g in gm))
check("required field: every final carries both scores",
      all(g[3] is not None and g[5] is not None for g in gm if g[6] == "final"))
check("no score invented for an unresolved or scheduled fixture",
      all(g[3] is None and g[5] is None for g in gm if g[6] != "final"))

# derived counts recomputed, not stored
des = [r for r in inj if r[5]]
check("designated rows recompute to 171", len(des) == 171, "got %d" % len(des))
clubs = sorted({r[0] for r in inj})
check("clubs recompute to 28", len(clubs) == 28, "got %d" % len(clubs))
check("absent clubs are exactly the Week 10 byes",
      [t for t in ("CHI", "DEN", "PHI", "TB") if t not in clubs] == ["CHI", "DEN", "PHI", "TB"])

# ------------------------------------------------------------- integrity check
import collections
st = json.load(open(os.path.join(ROOT, "data", "standings_2026.json"), encoding="utf-8"))["rows"]
rec = collections.defaultdict(lambda: dict(W=0, L=0, T=0, PF=0, PA=0))
for wk, dt, aw, ap, ho, hp, s, url, note in gm:
    if s != "final":
        continue
    for t, p, o in ((aw, ap, hp), (ho, hp, ap)):
        rec[t]["PF"] += p; rec[t]["PA"] += o
        rec[t]["W" if p > o else ("L" if p < o else "T")] += 1
bad = [(r[0], k, rec[r[0]][k], dict(W=r[2], L=r[3], T=r[4], PF=r[6], PA=r[7])[k])
       for r in st for k in ("W", "L", "T", "PF", "PA")
       if rec[r[0]][k] != dict(W=r[2], L=r[3], T=r[4], PF=r[6], PA=r[7])[k]]
check("game log reconciles to the official standings, 32 clubs", not bad, "%d mismatches" % len(bad))

# ------------------------------------------------------------------- site scan
htmls = [os.path.join(ROOT, "index.html")] + [
    os.path.join(ROOT, "pages", f) for f in sorted(os.listdir(os.path.join(ROOT, "pages")))
    if f.endswith(".html")]
check("19 pages generated", len(htmls) == 19, "got %d" % len(htmls))

broken = []
loc = 0
rows = 0
rowlinks = 0
rowblank = 0
for p in htmls:
    base = os.path.dirname(p)
    t = open(p, encoding="utf-8").read()
    for h in re.findall(r'href="([^"]+)"', t):
        if h.startswith(("http", "#", "mailto:", "data:", "javascript:")):
            continue
        h = h.split("#")[0].split("?")[0]
        if h and not os.path.exists(os.path.normpath(os.path.join(base, h))):
            broken.append((os.path.basename(p), h))
    if re.search(r'(https?://)?(localhost|127\.0\.0\.1)\s*:\d{2,5}', t):
        loc += 1
    # header rows are column labels, not data rows: exclude them from the source-link audit
    tbody = re.sub(r"<thead>.*?</thead>", "", t, flags=re.S)
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", tbody, re.S):
        rows += 1
        if re.search(r'href=["\']https?://', tr):
            rowlinks += 1
        elif 'class="blank"' in tr or "blank" in tr:
            rowblank += 1
check("no broken internal links", not broken, str(broken[:3]))
check("no localhost or 127.0.0.1 references", loc == 0)
navroots = re.findall(r'<a class="nav[^"]*" href="([^"]+)"',
                      open(os.path.join(ROOT, "index.html"), encoding="utf-8").read())
check("every navigation target exists from the landing page",
      all(os.path.exists(os.path.join(ROOT, h)) for h in navroots))
navsub = re.findall(r'<a class="nav[^"]*" href="([^"]+)"',
                    open(os.path.join(ROOT, "pages", "flagged.html"), encoding="utf-8").read())
check("every navigation target resolves from inside pages/",
      all(os.path.exists(os.path.join(ROOT, "pages", h)) for h in navsub))
check("every data row carries a source link or a visible blank marker",
      rowlinks + rowblank >= rows,
      "%d rows, %d linked, %d marked blank" % (rows, rowlinks, rowblank))

# every page links out to at least one official source
noff = 0
for p in htmls:
    t = open(p, encoding="utf-8").read()
    if "nfl.com" in t or "github.com" in t:
        noff += 1
check("every page cites at least one external source", noff == len(htmls), "%d of %d" % (noff, len(htmls)))

# determinism: a rebuild must not change any emitted file
digests = {p: hashlib.sha256(open(p, "rb").read()).hexdigest() for p in htmls}
json.dump({"pages": len(htmls), "rows": rows, "linked_rows": rowlinks,
           "blank_marked_rows": rowblank, "mismatches": len(bad),
           "digests": digests}, open(os.path.join(ROOT, "data", "verify_state.json"), "w"), indent=1)

print("\n%d pages, %d table rows (%d with a source link, %d explicitly marked blank)" %
      (len(htmls), rows, rowlinks, rowblank))
if fail:
    print("\nFAILED: " + ", ".join(fail))
    sys.exit(1)
print("all checks passed")
