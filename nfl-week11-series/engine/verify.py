#!/usr/bin/env python3
"""nfl-week11-series publication gate. Exit 0 = publish; non-zero = fix first."""
import csv, hashlib, json, os, re, subprocess, sys

NS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(NS, "evidence")
DATA = os.path.join(NS, "data")

APPROVED_HOSTS = ("www.nfl.com", "nfl.com", "www.packers.com", "packers.com",
                  "www.houstontexans.com", "houstontexans.com",
                  "static.clubs.nfl.com", "github.com")

PAGES = ["index.html", "series.html", "week10.html", "reserve.html", "depth.html",
         "starters.html", "questions.html", "suggestions.html", "flagged.html",
         "sources.html", "executive-summary.html", "verify.html"]

# Drift pins (REQ-61): evidence counts must equal these or the build is lying.
PINS = {
    "week10_rows.csv": 347,
    "week11_rows.csv": 253,
    "week11_sections.csv": 26,
    "reserve_list_2026-11.csv": 25,
    "reserve_list_2026-10.csv": 25,
    "trades_2026-11.csv": 12,
    "other_2026-11.csv": 5,
    "starter_evidence.csv": 5,
    "depth_observations.csv": 10,
}

CAP_A_PATH = os.path.join(os.path.dirname(NS), "nfl-readiness-register/snapshots/2026-11-18/injury_report-2026-11-18T234917Z.html")
CAP_A_SHA = "e1bbea1bf036c949825106a9a9e51de307da86680583d201a091682d7d012e7b"
CAP_B_PATH = os.path.join(os.path.dirname(NS), "nfl-daily-desk/captures/2026-11-19/injury-report-week11.md")
CAP_B_SHA = "d2ec7ac360f4f56064554d5af0a6352091a3f8ef81d4001539fddbf865c23676"

fails = []

def ok(rule, detail=""):
    print("[ok] %s %s" % (rule, detail))

def fail(rule, detail):
    print("[FAIL] %s %s" % (rule, detail))
    fails.append((rule, detail))

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()

def main():
    # 1. hash integrity
    if sha(CAP_A_PATH) == CAP_A_SHA:
        ok("hash-a", "capture_a sha256 matches")
    else:
        fail("hash-a", "capture_a bytes changed")
    if sha(CAP_B_PATH) == CAP_B_SHA:
        ok("hash-b", "capture_b sha256 matches")
    else:
        fail("hash-b", "capture_b bytes changed")

    # 2. drift pins on evidence
    for fn, n in PINS.items():
        path = os.path.join(EV, fn)
        rows = [l for l in open(path, encoding="utf-8") if not l.startswith("#") and l.strip()]
        got = len(rows) - 1  # minus header
        if got == n:
            ok("pin", "%s = %d rows" % (fn, got))
        else:
            fail("pin", "%s has %d rows, pin says %d - re-derive and update the pin deliberately" % (fn, got, n))

    # 3. page rules
    total_rows = sourced_rows = 0
    hrefs_checked = 0
    for fname in PAGES:
        t = open(os.path.join(NS, fname), encoding="utf-8").read()
        # local links resolve
        for m in re.finditer(r'href="([^"]+)"', t):
            href = m.group(1)
            if href.startswith("http"):
                host = re.sub(r"^https?://", "", href).split("/")[0]
                if not any(host == h or host.endswith("." + h) for h in APPROVED_HOSTS):
                    fail("host", "%s links off-list host %s" % (fname, host))
                continue
            if href.startswith("#"):
                if href != "#" and ('id="%s"' % href[1:]) not in t and ('name="%s"' % href[1:]) not in t:
                    fail("anchor", "%s: %s missing" % (fname, href))
                continue
            target = href.split("#")[0]
            if target and not os.path.exists(os.path.join(NS, target)):
                fail("link", "%s -> %s missing" % (fname, href))
            hrefs_checked += 1
        # every tbody row has an approved https source link
        body = re.search(r"<tbody>(.*?)</tbody>", t, re.S)
        for tbl in re.findall(r"<tbody>(.*?)</tbody>", t, re.S):
            for tr in re.findall(r"<tr>(.*?)</tr>", tbl, re.S):
                total_rows += 1
                links = re.findall(r'<a href="(https://[^"]+)"', tr)
                if not links:
                    fail("row-source", "%s: row without https source: %.90s" % (fname, tr))
                    continue
                good = False
                for u in links:
                    host = re.sub(r"^https?://", "", u).split("/")[0]
                    if any(host == h or host.endswith("." + h) for h in APPROVED_HOSTS):
                        good = True
                if good:
                    sourced_rows += 1
                else:
                    fail("row-source", "%s: row with only off-list links: %.90s" % (fname, tr))
        # nav present on every page
        if "<nav>" not in t or "flagged.html" not in t:
            fail("nav", "%s missing nav or flagged link" % fname)

    # 4. count integrity: headline numbers printed on pages match data JSONs
    series = json.load(open(os.path.join(DATA, "series.json")))
    recount = json.load(open(os.path.join(DATA, "week10_recount.json")))
    idx = open(os.path.join(NS, "index.html"), encoding="utf-8").read()
    wk = open(os.path.join(NS, "week10.html"), encoding="utf-8").read()
    se = open(os.path.join(NS, "series.html"), encoding="utf-8").read()
    for page_name, t in (("index", idx), ("week10", wk)):
        if str(recount["observed"]["n_rows"]) not in t:
            fail("count", "%s does not print week10 row count %d" % (page_name, recount["observed"]["n_rows"]))
    if str(series["points"][2]["summary"]["n_rows"]) not in idx:
        fail("count", "index does not print week11 row count")
    if "253" not in se or "242" not in se:
        fail("count", "series page missing capture counts")

    # 5. banned performance-claim scan (numeric claims)
    for fname in PAGES:
        t = open(os.path.join(NS, fname), encoding="utf-8").read()
        text = re.sub(r"<[^>]+>", " ", t)
        for m in re.finditer(r"\d[\d,.]*\s*%?\s*(ROI|CLV|win[- ]rate|units won|profit)", text, re.I):
            fail("banned-claim", "%s: numeric performance claim: %.60s" % (fname, m.group(0)))
        for m in re.finditer(r"\b(ROI|CLV|win[- ]rate)\b", text, re.I):
            start = max(0, m.start() - 220)
            sentence_zone = text[start:m.end() + 80].lower()
            if not re.search(r"\b(no|not|never|reject|forbid|blocks|unmet|nothing|policy)\b", sentence_zone):
                fail("banned-claim", "%s: performance term outside a rejection: %.60s" % (fname, m.group(0)))

    # 6. owner-decision columns stay undecided
    for fname in ("questions.html", "suggestions.html"):
        t = open(os.path.join(NS, fname), encoding="utf-8").read()
        if "undecided" not in t and "awaiting owner" not in t:
            fail("owner-blank", "%s lost its undecided marker" % fname)

    # 7. determinism: rebuild must be byte-identical
    before = {}
    for root, _, files in os.walk(NS):
        for f in files:
            if f.endswith((".html", ".css")) and "engine" not in root:
                p = os.path.join(root, f)
                before[os.path.relpath(p, NS)] = sha(p)
    subprocess.run([sys.executable, os.path.join(NS, "engine", "build.py")], check=True, capture_output=True)
    after = {}
    for root, _, files in os.walk(NS):
        for f in files:
            if f.endswith((".html", ".css")) and "engine" not in root:
                p = os.path.join(root, f)
                after[os.path.relpath(p, NS)] = sha(p)
    if before == after:
        ok("determinism", "rebuild byte-identical (%d files)" % len(before))
    else:
        fail("determinism", "rebuild changed output")

    print("----")
    print("rows checked   : %d (sourced %d)" % (total_rows, sourced_rows))
    print("local links    : %d" % hrefs_checked)
    if fails:
        print("VERIFY: %d FAILURES" % len(fails))
        sys.exit(1)
    print("VERIFY: all rules pass (%d pages)" % len(PAGES))

if __name__ == "__main__":
    main()
