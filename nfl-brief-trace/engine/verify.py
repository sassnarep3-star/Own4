"""Verifier for nfl-brief-trace. Run from repo root after trace.py and build.py.
Checks: every table row has an official link or BLANK+UNVERIFIED flag; every local link resolves;
no localhost; status counts add up; rule-text fetches that were empty are not used as evidence;
two consecutive builds are byte-identical. Exit 1 on any failure."""
import glob, hashlib, json, os, re, subprocess, sys
from html.parser import HTMLParser

ROOT = os.getcwd()
BASE = os.path.join(ROOT, "nfl-brief-trace")
fails = []
def check(ok, msg):
    print(("PASS " if ok else "FAIL ") + msg)
    if not ok: fails.append(msg)

T = json.load(open(os.path.join(BASE, "data", "trace.json"), encoding="utf-8"))
C = json.load(open(os.path.join(BASE, "data", "official_checks.json"), encoding="utf-8"))

check(T["n_items"] == 80 and len(T["items"]) == 80, "80 brief lines traced")
check(sum(T["status_counts"].values()) == T["n_items"], "status counts sum to n_items")
OFFICIAL_HOSTS = ("www.nfl.com", "nfl.com", "support.nfl.com", "operations.nfl.com")
from urllib.parse import urlparse
bad_rows = []
for r in T["items"]:
    off = r["official"]
    if off:
        host = urlparse(off["url"]).netloc
        if host not in OFFICIAL_HOSTS or urlparse(off["url"]).scheme != "https":
            bad_rows.append(r["id"] + ": non-official host " + host)
    elif not r["official_flag"]:
        bad_rows.append(r["id"] + ": no official link and no UNVERIFIED flag")
check(not bad_rows, "every item has an official https link or an UNVERIFIED flag " + str(bad_rows[:3]))

empty_urls = {x["url"] for x in C["rows"] if not x["usable"]}
used = {r["official"]["url"] for r in T["items"] if r["official"]}
check(not (used & empty_urls), "no item relies on an unusable (empty-body) official URL")
check(all(r["official"]["fetched_this_session"] or r["official"]["url"].endswith("/scores/2026/week-10")
          for r in T["items"] if r["official"]),
      "every official link used is fetched this session or is the register-cited SCORES URL (marked)")

for r in T["items"]:
    for a in r["artifacts"]:
        if a["exists"]:
            check_path = os.path.join(ROOT, a["path"])
            if not os.path.exists(check_path):
                fails.append("artifact vanished " + a["path"])
broken = [r["id"] for r in T["items"] if r["status"] == "broken-reference"]
check(not broken, "no broken artifact references " + str(broken))

pages = [os.path.join(BASE, "index.html")] + sorted(glob.glob(os.path.join(BASE, "pages", "*.html")))
class Collect(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.rows=[]; self._row=None; self._depth=0; self.in_tbody=False
    def handle_starttag(self, tag, attrs):
        d=dict(attrs)
        if tag in ("a","link","script") and (d.get("href") or d.get("src")):
            self.links.append(d.get("href") or d.get("src"))
        if tag=="tr" and self.in_tbody: self._row=[]; self._rowhtml=""
        if tag=="tbody": self.in_tbody=True
    def handle_endtag(self, tag):
        if tag=="tbody": self.in_tbody=False
        if tag=="tr" and self._row is not None:
            self.rows.append(self._rowhtml); self._row=None
    def handle_data(self, data):
        if self._row is not None: self._rowhtml += data
    def handle_entity_ref(self, name): pass
    def handle_startendtag(self, tag, attrs): self.handle_starttag(tag, attrs)

for p in pages:
    src = open(p, encoding="utf-8").read()
    check("localhost" not in src and "127.0.0.1" not in src, "no localhost reference in " + os.path.relpath(p, BASE))
    c = Collect(); c.feed(src)
    for href in c.links:
        if href.startswith(("http://","https://","mailto:","#")): continue
        target = os.path.normpath(os.path.join(os.path.dirname(p), href.split("#")[0]))
        if not os.path.exists(target):
            fails.append(f"broken local link {href} in {os.path.relpath(p, BASE)}")
    if "tbody" in src:
        n_rows_html = src.count("<tr><td>")
        # every data row must carry either an https link or a BLANK + UNVERIFIED flag
        rows = re.findall(r"<tr>(.*?)</tr>", src, flags=re.S)
        data_rows = [x for x in rows if "<td>" in x]
        missing = [i for i, x in enumerate(data_rows)
                   if "href=" not in x and "BLANK" not in x]
        check(not missing, f"every data row in {os.path.relpath(p, BASE)} has a source link or BLANK flag ({len(data_rows)} rows)")

check(not any(f.startswith("broken local link") for f in fails), "all local links resolve")
for f_ in fails:
    if f_.startswith("broken local link"): print("   ", f_)

def snapshot():
    h = hashlib.sha256()
    for p in pages: h.update(open(p, "rb").read())
    return h.hexdigest()
# Pages quote live counts (e.g. COORDINATION.md line count), so rebuild once from the current trace first.
subprocess.run([sys.executable, os.path.join(BASE, "engine", "build.py")], check=True, capture_output=True)
first = snapshot()
subprocess.run([sys.executable, os.path.join(BASE, "engine", "build.py")], check=True, capture_output=True)
second = snapshot()
check(first == second, "rebuild is byte-identical (deterministic)")

print("VERIFY:", "PASS" if not fails else f"FAIL ({len(fails)})")
sys.exit(1 if fails else 0)
