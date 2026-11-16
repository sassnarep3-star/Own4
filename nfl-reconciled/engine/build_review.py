#!/usr/bin/env python3
"""Roll every workspace's flagged items into one review index.

A reviewer currently has to open 18 separate "Flagged for review" pages to see 241 open items. This
engine reads them all, keeps each row's own source link, groups by theme, and writes one index. It
does not judge, merge or close anything: the owner reviews each row on the page that raised it.

Deterministic, stdlib only, no network.
"""

import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "data", "derived")
BUILT = "2026-11-16"

THEMES = [
    ("Prices & market lines", r"\b(price|odds|moneyline|closing line|clv|vig|market price)\b"),
    ("Depth, starters & replacements", r"\b(depth chart|depth|starter|backup|replacement|snap count|string)\b"),
    ("Availability & injuries", r"\b(injur|inactive|availability|reserve list|designation|questionable)\b"),
    ("Data rights & storage", r"\b(terms|licen|copyright|redistribut|row-level|private store|public page)\b"),
    ("Gates, pre-registration & leaderboard", r"\b(gate|pre-?regist|leaderboard|reward|backtest|demot|brier)\b"),
    ("Stale or drifting values", r"\b(stale|drift|out of date|superseded|stale count|no longer)\b"),
    ("Fixtures, schedule & venues", r"\b(fixture|schedule|kickoff|venue|stadium|roof|bye|week \d+)\b"),
    ("Model, ratings & probabilities", r"\b(model|rating|spread|total|probability|brier|calibration|home.field|hfa)\b"),
    ("Standings & records", r"\b(standings|record|w-l|points for|points against|conference)\b"),
    ("Site, navigation & repository hygiene", r"\b(namespace|navigation|nav|root|coordination|readme|link|page|dashboard|canonical|header)\b"),
    ("Capture, hashing & provenance", r"\b(capture|hash|timestamp|provenance|source count|transcri|read time|snapshot)\b"),
]

URL = re.compile(r"https?://[^\s\"'<>)\]]+")


def classify(text):
    for name, pat in THEMES:
        if re.search(pat, text, re.I):
            return name
    return "Unclassified — review on its own page"


def collect():
    rows = []
    seen_files = []
    for path in sorted(glob.glob(os.path.join(ROOT, "nfl*", "**", "*flag*.json"), recursive=True)):
        try:
            d = json.load(open(path, encoding="utf-8"))
        except Exception:
            continue
        rs = d.get("rows") or d.get("flags") or d.get("items") or (d if isinstance(d, list) else [])
        if not isinstance(rs, list):
            continue
        rs = [r for r in rs if isinstance(r, dict)]
        if not rs:
            continue
        wf = os.path.relpath(path, ROOT).replace(os.sep, "/")
        seen_files.append({"path": wf, "n": len(rs)})
        for r in rs:
            blob = " ".join(str(v) for v in r.values())
            urls = URL.findall(blob)
            for key in ("source_url", "source", "url"):
                v = r.get(key)
                if isinstance(v, str):
                    urls += URL.findall(v)
            title = (r.get("title") or r.get("item") or r.get("finding") or r.get("detail") or "")
            title = re.sub(r"\s+", " ", str(title)).strip()
            detail = (r.get("detail") or r.get("finding") or r.get("measured") or "")
            detail = re.sub(r"\s+", " ", str(detail)).strip()
            rows.append({
                "workspace": wf.split("/")[0],
                "file": wf,
                "id": r.get("id"),
                "severity": r.get("severity") or r.get("kind") or "",
                "theme": classify(title + " " + detail),
                "title": title[:400],
                "detail": detail[:600],
                "sources": sorted(set(urls))[:4],
                "page": ("%s/pages/flagged.html" % wf.split("/")[0])
                        if os.path.exists(os.path.join(ROOT, wf.split("/")[0], "pages", "flagged.html"))
                        else ("%s/flagged.html" % wf.split("/")[0]),
            })
    return rows, seen_files


def main():
    rows, files = collect()
    by_theme = {}
    for r in rows:
        by_theme.setdefault(r["theme"], []).append(r)
    by_ws = {}
    for r in rows:
        by_ws.setdefault(r["workspace"], 0)
        by_ws[r["workspace"]] += 1
    obj = {
        "dataset": "review_index",
        "title": "Every open flagged item across every NFL workspace, in one place",
        "built_utc": BUILT,
        "session": "arena/3858e722-own4",
        "rule": ("Collected by reading each workspace's own flags artefact. Nothing is closed, merged "
                 "or re-judged here: each row links back to the page that raised it and to the source "
                 "that page cited. An item with no theme match is grouped as unclassified rather than "
                 "forced into one."),
        "totals": {
            "items": len(rows),
            "files": len(files),
            "workspaces": len(by_ws),
            "with_source_link": sum(1 for r in rows if r["sources"]),
        },
        "by_theme": [{"theme": k, "n": len(v)} for k, v in
                     sorted(by_theme.items(), key=lambda kv: (-len(kv[1]), kv[0]))],
        "by_workspace": [{"workspace": k, "n": v} for k, v in
                         sorted(by_ws.items(), key=lambda kv: (-kv[1], kv[0]))],
        "files": files,
        "rows": rows,
    }
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "review_index.json"), "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1)
        fh.write("\n")
    print("review index: %d items from %d files across %d workspaces (%d carry a source link)"
          % (len(rows), len(files), len(by_ws), obj["totals"]["with_source_link"]))
    for t in obj["by_theme"]:
        print("  %-48s %3d" % (t["theme"], t["n"]))


if __name__ == "__main__":
    main()
