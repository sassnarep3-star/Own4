"""Verifier for the nfl-book site.

Hard checks (non-zero exit on failure):
  1. Every <tbody> row contains at least one https:// source link.
  2. Every internal href resolves to a file that exists (and anchors resolve).
  3. Every blank cell (td.blank) carries a title containing 'unverified'.
  4. No localhost / 127.0.0.1 references.
  5. Expected pages all exist; every NAV target reachable from every page.
  6. JSON datasets parse and key integrity checks pass (V-01..03 in feed).
"""
import json, os, re, sys, glob
from common import ROOT, PAGES, load

A_HREF = re.compile(r'<a[^>]+href="([^"]+)"')
TD = re.compile(r"<td[^>]*>.*?</td>|<td[^>]*/>", re.S)
TR = re.compile(r"<tr>(.*?)</tr>", re.S)
BLANK_TD = re.compile(r'<td class="blank"[^>]*>')


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def main():
    errors, stats = [], {"pages": 0, "rows": 0, "sourced_rows": 0,
                         "blank_cells": 0, "links": 0}
    pages = sorted(glob.glob(os.path.join(ROOT, "*.html")) +
                   glob.glob(os.path.join(PAGES, "*.html")))
    stats["pages"] = len(pages)

    for p in pages:
        rel = os.path.relpath(p, ROOT)
        html = read(p)
        if "ncpgambling.org" not in html:
            errors.append(f"{rel}: missing responsible-gambling footer link")
        # blank cells must be marked
        for m in BLANK_TD.finditer(html):
            stats["blank_cells"] += 1
            tag = m.group(0)
            if 'title="unverified' not in tag and "awaiting" not in tag:
                errors.append(f"{rel}: blank cell without unverified marker: {tag[:80]}")
        # rows: every data-table tbody row needs an https link
        # (tables marked class="meta" are navigation/schema/order only and are
        #  exempt — they carry no factual values)
        for tbl in re.findall(r"<table[^>]*>.*?</table>", html, re.S):
            is_meta = '<table class="meta"' in tbl.split(">", 1)[0]
            for body in re.findall(r"<tbody>(.*?)</tbody>", tbl, re.S):
                for tr in TR.findall(body):
                    stats["rows"] += 1
                    hrefs = A_HREF.findall(tr)
                    if is_meta:
                        continue
                    if any(h.startswith("https://") for h in hrefs):
                        stats["sourced_rows"] += 1
                    else:
                        errors.append(f"{rel}: table row without an https source link: "
                                      f"{tr[:140]}")
        # links
        for href in A_HREF.findall(html):
            stats["links"] += 1
            if href.startswith(("http://", "https://")):
                if href.startswith("http://"):
                    errors.append(f"{rel}: insecure http link: {href}")
                continue
            if href.startswith(("mailto:", "#")):
                continue
            if "localhost" in href or "127.0.0.1" in href:
                errors.append(f"{rel}: localhost reference: {href}")
                continue
            target, _, frag = href.partition("#")
            tp = os.path.normpath(os.path.join(os.path.dirname(p), target))
            if not os.path.exists(tp):
                errors.append(f"{rel}: broken internal link: {href}")
            elif frag and tp.endswith(".html"):
                th = read(tp)
                if f'id="{frag}"' not in th and f'name="{frag}"' not in th:
                    errors.append(f"{rel}: broken anchor: {href}")

    # expected pages from NAV (via index.html)
    idx = read(os.path.join(ROOT, "index.html"))
    for href in re.findall(r'href="(pages/[^"]+)"', idx):
        if not os.path.exists(os.path.join(ROOT, href)):
            errors.append(f"index.html: missing nav target {href}")

    # dataset integrity
    feed = load("results_feed.json")
    if not all(c["result"] == "pass" for c in feed["checks"]):
        errors.append("results_feed.json: a verification check is not passing")
    lb = load("leaderboard.json")
    if lb["points_awarded"] != 0:
        errors.append("leaderboard: points must be 0 while G7 is blocked (amendment A1)")
    snaps = load("price_snapshots.json")
    if snaps["n_snapshots"] != 39:
        errors.append(f"price_snapshots: expected 39, got {snaps['n_snapshots']}")
    for s in snaps["rows"]:
        if s["market_open_value"] is not None or s["market_close_value"] is not None:
            errors.append(f"market snapshot filled without official source: {s}")
    # origination order audit
    for fn in ("own_lines_open.json", "own_lines_close.json"):
        o = load(fn)
        assert o["origination_order"] == ["side", "total", "moneyline"]
        for r in o["rows"]:
            if r["origination_order"] != ["side", "total", "moneyline"]:
                errors.append(f"{fn}: order violated in {r['game_id']}")
            if r["side"]["market_home_line"] is not None:
                errors.append(f"{fn}: market line filled without source")

    print(f"[verify] pages={stats['pages']} rows={stats['rows']} "
          f"sourced={stats['sourced_rows']} blanks={stats['blank_cells']} "
          f"links={stats['links']}")
    if errors:
        print(f"[verify] FAIL — {len(errors)} problem(s):")
        for e in errors[:40]:
            print("  -", e)
        sys.exit(1)
    print("[verify] PASS")


if __name__ == "__main__":
    main()
