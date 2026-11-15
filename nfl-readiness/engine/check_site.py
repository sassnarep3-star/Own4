"""Gate for nfl-readiness/ pages. Stdlib only. Exits non-zero on any error.
Checks: internal links resolve; external links use https on an allow-listed host; every table body
row carries at least one source link; column counts match headers; no player name from the private
injury file appears in public HTML (headline names from public nfl.com news are allowed).
"""
import csv, html, pathlib, re, sys
from html.parser import HTMLParser
ROOT = pathlib.Path(__file__).resolve().parents[1]
PRIV = ROOT.parent / "private-store" / "injury_week10_2026-11-15.csv"
ALLOW_HOSTS = {"www.nfl.com", "github.com", "static.www.nfl.com"}
HEADLINE_NAMES = {"Drake Maye", "Geno Smith", "Aidan Hutchinson", "Daiyan Henley", "TreVeyon Henderson", "Puka Nacua",
                  "Drew Lock", "Lamar Jackson", "Malik Willis", "Kenneth Walker", "Kyle McCord", "J.J. McCarthy", "Baker Mayfield",
                  "Justin Herbert", "Sam Darnold", "Garrett Wilson", "Josh Jacobs", "Carson Beck", "Deshaun Watson", "Brian Robinson", "Amani Hooker"}
errors, warns = [], []

class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []; self.tables = []; self.cur = None; self.rowstack = []; self.in_thead = False
        self.text = []; self._row = None; self._cell = None
    def handle_starttag(self, tag, a):
        d = dict(a)
        if tag == "a" and "href" in d: self.links.append(d["href"])
        if tag == "table": self.tables.append({"head": 0, "rows": []}); self.cur = self.tables[-1]
        if tag == "thead": self.in_thead = True
        if tag == "tbody": self.in_thead = False
        if tag == "tr" and self.cur is not None: self._row = {"cells": 0, "links": 0, "thead": self.in_thead}
        if tag in ("td", "th") and self._row is not None:
            self._row["cells"] += 1; self._cell = True
    def handle_endtag(self, tag):
        if tag == "tr" and self._row is not None and self.cur is not None:
            (self.cur["head"] if self._row["thead"] else None) if False else None
            if self._row["thead"]: self.cur["head"] = self._row["cells"]
            else: self.cur["rows"].append(self._row)
            self._row = None
        if tag == "td" or tag == "th": self._cell = None
        if tag == "table": self.cur = None
    def handle_data(self, data):
        self.text.append(data)

pages = [ROOT / "index.html"] + sorted((ROOT / "pages").glob("*.html"))
priv_names = set()
if PRIV.exists():
    priv_names = {r["player"] for r in csv.DictReader(open(PRIV, encoding="utf-8")) if r["player"]}
stats = {"pages": 0, "table_rows": 0, "rows_with_official_link": 0, "rows_repo_record_only": 0, "rows_without_link": 0, "external_links": 0, "internal_links": 0}
for page in pages:
    stats["pages"] += 1
    raw = page.read_text(encoding="utf-8")
    p = P(); p.feed(raw)
    rel = page.relative_to(ROOT)
    if "<title>" not in raw or "<h1>" not in raw: errors.append(f"{rel}: missing title or h1")
    for href in p.links:
        if href.startswith("#") or href.startswith("mailto:"): continue
        if href.startswith("http"):
            stats["external_links"] += 1
            host = re.sub(r"^https://([^/]+).*", r"\1", href) if href.startswith("https://") else ""
            if not href.startswith("https://") or host not in ALLOW_HOSTS:
                errors.append(f"{rel}: external link not allow-listed or not https: {href}")
            continue
        stats["internal_links"] += 1
        target = (page.parent / href.split("#")[0]).resolve()
        if not target.exists(): errors.append(f"{rel}: broken internal link {href}")
    for t in p.tables:
        for r in t["rows"]:
            stats["table_rows"] += 1
            if t["head"] and r["cells"] != t["head"]: errors.append(f"{rel}: row has {r['cells']} cells, header has {t['head']}")
    # per-row source link check, done on raw html rows
    for row_html in re.findall(r"<tr>(.*?)</tr>", raw, flags=re.S):
        if "<td>" not in row_html: continue
        hrefs = re.findall(r'href="([^"]+)"', row_html)
        ext = [h for h in hrefs if h.startswith("http")]
        if not ext: stats["rows_without_link"] += 1; errors.append(f"{rel}: table row without any source link: {re.sub('<[^>]+>', ' ', row_html)[:120]}")
        elif any("nfl.com" in h for h in ext): stats["rows_with_official_link"] += 1
        else: stats["rows_repo_record_only"] += 1
    text = html.unescape(" ".join(p.text))
    for name in sorted(priv_names):
        if name in text and name not in HEADLINE_NAMES:
            errors.append(f"{rel}: private player name published: {name}")
# nav completeness
idx = (ROOT / "index.html").read_text(encoding="utf-8")
for pg in ["pages/injuries.html", "pages/schedule-results.html", "pages/shadow-baseline.html", "pages/governance.html", "pages/suggestions.html", "pages/questions.html", "pages/executive-summary.html", "pages/flagged.html", "pages/sources.html"]:
    if pg not in idx: errors.append(f"index.html: nav missing {pg}")
print(stats)
print("private names checked:", len(priv_names))
for w in warns: print("WARN", w)
for e in errors[:60]: print("ERROR", e)
print("errors:", len(errors))
sys.exit(1 if errors else 0)
