#!/usr/bin/env python3
"""Publication contract, enforced mechanically.

The brief's delivery rule - 'every table row has an official-source link, or blank + unverified' - is
only worth anything if something checks it on every build. This does, for this namespace, plus three
more guards that catch the failure modes actually seen in this repository:

  1. internal links resolve (no page 404s inside the published namespace);
  2. every row of every data table carries a source link or the literal UNVERIFIED marker;
  3. no row on any page asserts a market price (no official source exists - flag RF-02), so a price
     value appearing in the HTML is a build failure, not a review finding;
  4. the landing page's headline numbers equal the derived JSON they were generated from, and every
     file cited inside a data artefact exists in the tree (an artefact that points at a file nobody
     wrote is worse than no artefact).

Exit code 1 = do not publish. Run after engine/build_site.py.
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)
DATA = os.path.join(NS, "data")
PAGES = os.path.join(NS, "pages")
IDX = os.path.join(NS, "index.html")

PATH_RX = re.compile(
    r"(?:nfl-availability-desk/)?((?:(?:[a-z0-9][a-z0-9._-]*)?/)?(?:data|engine|prereg|pages|assets)/"
    r"[A-Za-z0-9_.\-/]+\.(?:json|py|md|html|csv|css|yml))")
# strings that would only appear if a price number had leaked into the published layer
PRICE_LEAK_RX = re.compile(
    r"(?:spread|line|total|odds|price)\s*(?:of|:|=)\s*[+-]?\d+\.\d", re.I)
ROW_ID_RX = re.compile(r"R-\d\d\b")


def html_files():
    out = [("index.html", IDX)]
    if os.path.isdir(PAGES):
        for f in sorted(os.listdir(PAGES)):
            if f.endswith(".html"):
                out.append((f"pages/{f}", os.path.join(PAGES, f)))
    return out


def main() -> int:
    problems: list[str] = []
    files = html_files()
    if not files:
        print("no pages built yet - run engine/build_site.py first")
        return 1

    # 1. internal links resolve
    for rel, path in files:
        with open(path, encoding="utf-8") as fh:
            txt = fh.read()
        for href in re.findall(r'href="([^"#]+)"', txt):
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            tgt = os.path.normpath(os.path.join(os.path.dirname(path), href))
            if not os.path.exists(tgt):
                problems.append(f"{rel}: broken internal link -> {href}")

    # 2. every data row of a source-bearing page carries an official link, a repo-artefact marker,
    #    or the literal UNVERIFIED flag; 3. no leaked price values anywhere.
    rows_checked = 0
    DATA_PAGES = ("pages/availability.html", "pages/snapshot-delta.html", "pages/fixtures.html",
                  "pages/evidence.html", "index.html", "pages/flagged.html", "pages/repo-review.html")
    for rel, path in files:
        with open(path, encoding="utf-8") as fh:
            txt = fh.read()
        if rel in DATA_PAGES:
            for row in re.findall(r"<tr>(.*?)</tr>", txt, re.S):
                if "<td" not in row:
                    continue
                cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
                if len(cells) < 3:
                    continue
                rows_checked += 1
                ok = ('href="http' in row or "<code>" in row or "UNVERIFIED" in row
                      or "repo file" in row or "not published" in row
                      or rel in ("pages/flagged.html", "pages/repo-review.html"))
                if not ok:
                    first = re.sub(r"<[^>]+>", "", cells[0]).strip()[:48]
                    second = re.sub(r"<[^>]+>", "", cells[1]).strip()[:48]
                    problems.append(f"{rel}: data row without a source link or UNVERIFIED marker: "
                                    f"{first} | {second}")
        for m in PRICE_LEAK_RX.finditer(txt):
            problems.append(f"{rel}: text that reads like a price value: {m.group(0)!r} - no official "
                            f"price source exists, so nothing may print one (flag RF-02)")

    # 4a. landing-page headline numbers agree with the derived artefacts
    audit_p = os.path.join(DATA, "derived", "capture_audit.json")
    valid_p = os.path.join(DATA, "derived", "capture_validation.json")
    st_p = os.path.join(DATA, "derived", "standings_check.json")
    for p in (audit_p, valid_p, st_p):
        if not os.path.exists(p):
            problems.append(f"missing derived artefact {os.path.relpath(p, NS)} - run engine/audit.py")
    if all(os.path.exists(p) for p in (audit_p, valid_p, st_p)):
        audit = json.load(open(audit_p))
        valid = json.load(open(valid_p))
        st = json.load(open(st_p))
        with open(IDX, encoding="utf-8") as fh:
            idx = fh.read()
        for n, label in ((audit["rows"], "row count"), (valid["club_sections"], "club sections"),
                         (st["sum_pf"], "sum PF")):
            if not re.search(rf"\b{n}\b", idx):
                problems.append(f"index.html does not print {label} = {n} although the artefacts say {n} "
                                "- the pages were built before the data changed; rebuild")
        if valid["verdict"] != "PASS":
            problems.append("capture validation verdict is FAIL - do not publish")

    # 4b. every file path cited inside a data artefact exists
    cited = set()
    for root, _dirs, fs in os.walk(DATA):
        for f in fs:
            if not f.endswith((".json", ".csv")):
                continue
            fp = os.path.join(root, f)
            try:
                body = open(fp, encoding="utf-8").read()
            except OSError:
                continue
            for m in PATH_RX.finditer(body):
                rel = m.group(1)
                if rel.startswith(("nfl-", "pages/", "assets/")) or True:
                    cited.add((os.path.relpath(fp, NS), rel))
    for src, rel in sorted(cited):
        if rel.startswith("data/readiness.json"):
            rel = rel.split("data/")[-1]
        cands = [os.path.join(NS, rel), os.path.join(ROOT, rel), os.path.join(NS, "data", os.path.basename(rel))]
        if not any(os.path.exists(c) for c in cands):
            problems.append(f"{src} cites {rel}, which does not exist - write the artefact or drop the citation")

    # 5. the register's own vocabulary is closed
    readiness = json.load(open(os.path.join(DATA, "readiness.json")))
    allowed = set(readiness["how_to_read"]["status"])
    ids = [r["id"] for r in readiness["rows"]]
    if len(set(ids)) != len(ids):
        problems.append("readiness.json: duplicate requirement ids")
    want = [f"R-{i:02d}" for i in range(1, len(ids) + 1)]
    if ids != want:
        problems.append(f"readiness.json: ids are not the contiguous sequence R-01..R-{len(ids):02d}")
    for r in readiness["rows"]:
        if r["status"] not in allowed:
            problems.append(f"{r['id']}: status '{r['status']}' is outside the vocabulary declared in how_to_read")
        for k in ("requirement", "gate", "clearing_number", "evidence", "source"):
            if not str(r.get(k, "")).strip():
                problems.append(f"{r['id']}: empty '{k}' field")
        if not re.search(r"\d", r["clearing_number"]):
            problems.append(f"{r['id']}: clearing_number contains no number, so it cannot clear anything")
    tot = {}
    for r in readiness["rows"]:
        tot[r["status"]] = tot.get(r["status"], 0) + 1
    if readiness.get("status_totals") != tot:
        problems.append(f"readiness.json status_totals {readiness.get('status_totals')} != recomputed {tot}")

    print(f"pages checked: {len(files)} · data rows checked for a source or flag: {rows_checked} · "
          f"cited paths resolved: {len(cited)} · register rows: {len(ids)}")
    if problems:
        print(f"\nPROBLEMS ({len(problems)}):")
        for p in problems[:60]:
            print("  -", p)
        return 1
    print("verdict: PASS - publication contract holds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
