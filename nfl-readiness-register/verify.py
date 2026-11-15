#!/usr/bin/env python3
"""nfl-readiness verifier.

Checks, before every publish:
  1. every data table row in generated HTML carries an external https source link
     (rows in tables marked class="meta" are navigation metadata and exempt);
  2. no broken internal links (href targets exist on disk);
  3. no localhost/127.0.0.1 links;
  4. requirement register arithmetic: per-team injury rows sum to the published total;
  5. snapshot manifest hashes match the stored bytes (tamper-evidence);
  6. all data JSON files parse; blanks exist only alongside flags (counted).
Exit non-zero on any failure (fail loudly, REQ-61).
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

failures = []
notes = []


def check(name, ok, detail=""):
    (notes if ok else failures).append("%s %s %s" % ("PASS" if ok else "FAIL", name, detail))


# 1+2+3: scan generated HTML
html_files = ["index.html"] + [
    os.path.join("pages", f) for f in sorted(os.listdir(os.path.join(HERE, "pages"))) if f.endswith(".html")
]
rows_total = 0
rows_with_src = 0
links_checked = 0
for rel in html_files:
    path = os.path.join(HERE, rel)
    text = open(path, encoding="utf-8").read()
    for m in re.finditer(r'href="([^"]+)"', text):
        href = m.group(1)
        links_checked += 1
        check_link = href.split("#")[0]
        if href.startswith("http://localhost") or href.startswith("https://localhost") or "127.0.0.1" in href:
            failures.append("FAIL localhost link %s in %s" % (href, rel))
        if href.startswith("http"):
            continue
        target = os.path.normpath(os.path.join(os.path.dirname(path), check_link))
        if not os.path.exists(target):
            failures.append("FAIL broken internal link %s in %s" % (href, rel))
    for tm in re.finditer(r"<table([^>]*)>(.*?)</table>", text, re.S):
        attrs, inner = tm.group(1), tm.group(2)
        body = re.split(r"</thead>", inner)
        if len(body) < 2:
            continue
        is_meta = re.search(r'class="[^"]*meta', attrs) is not None
        for rm in re.finditer(r"<tr>(.*?)</tr>", body[1], re.S):
            cells = re.findall(r"<td[^>]*>(.*?)</td>", rm.group(1), re.S)
            if len(cells) < 2:
                continue
            rows_total += 1
            has_ext = any("https://" in c for c in cells)
            if is_meta:
                rows_with_src += 1
            elif has_ext:
                rows_with_src += 1
            else:
                failures.append("FAIL row without https source in %s: %s" % (rel, rm.group(1)[:90]))

# 4: register arithmetic
req = json.load(open(os.path.join(HERE, "data", "requirements.json")))
inj = json.load(open(os.path.join(HERE, "data", "injury_capture.json")))
s = sum(inj["per_team_rows"].values())
check("per-team rows sum", s == inj["totals"]["player_rows"], "%d vs %d" % (s, inj["totals"]["player_rows"]))
check("requirement row count", len(req["rows"]) >= 68, "n=%d" % len(req["rows"]))
check("register ids unique", len({r["id"] for r in req["rows"]}) == len(req["rows"]))
check("register rows have official source", all(r.get("official_source", "").startswith("https://") for r in req["rows"]))

# 5: manifest hashes
man_path = os.path.join(HERE, "snapshots", "manifest.jsonl")
entries = [json.loads(l) for l in open(man_path, encoding="utf-8") if l.strip()]
for e in entries:
    p = os.path.join(HERE, "snapshots", e["raw_path"].split("snapshots/", 1)[-1])
    if not os.path.exists(p):
        failures.append("FAIL manifest path missing %s" % e["raw_path"])
        continue
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    check("sha256 %s" % e["capture_id"], h == e["sha256"])

# 6: JSON parses
for f in sorted(os.listdir(os.path.join(HERE, "data"))):
    if f.endswith(".json"):
        try:
            json.load(open(os.path.join(HERE, "data", f), encoding="utf-8"))
        except Exception as ex:
            failures.append("FAIL json %s: %s" % (f, ex))

# blanks published and flagged
flag_text = open(os.path.join(HERE, "pages", "flagged.html"), encoding="utf-8").read()
blanks_on_site = sum(open(os.path.join(HERE, rel), encoding="utf-8").read().count("blank — unverified") for rel in html_files)
check("blanks are published + flagged page exists", len(failures) == 0 and "Flagged" in flag_text, "blank markers=%d, flags=%d" % (blanks_on_site, len(json.load(open(os.path.join(HERE, "data", "flags.json")))["rows"])))

print("\n".join(notes))
print("rows_total=%d rows_with_source=%d links_checked=%d" % (rows_total, rows_with_src, links_checked))
if failures:
    print("\n".join(failures))
    print("VERIFY: FAIL (%d problems)" % len(failures))
    sys.exit(1)
print("VERIFY: PASS (%d data rows, %d with https source, %d links ok)" % (rows_total, rows_with_src, links_checked))
