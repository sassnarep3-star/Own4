#!/usr/bin/env python3
"""Repository census: what exists, what is duplicated, and where registers disagree.

Why this file exists: the NFL work is spread over 40 sibling namespaces written by
different sessions. Before any number is published, the reader needs to know (a) how
many copies of the same register exist, (b) which numbers they disagree on, and (c)
how much of it rests on an official source rather than a third-party archive. All of
that is computable from the tree, so none of it is typed by hand here.

Every count is derived from files. Where a disagreement is found, both values and both
files are recorded so the owner can adjudicate; this script does not pick a winner.

Run: python3 nfl-desk/engine/census.py
"""
import csv
import json
import os
import re
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)
OUT = os.path.join(NS, "data", "census.json")
REPO = "https://github.com/sassnarep3-star/Own4/blob/main/"


def rel(p):
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def url(p):
    return REPO + rel(p)


def walk(pattern_dir, suffix):
    hits = []
    for base, dirs, files in os.walk(pattern_dir):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "__pycache__")]
        for f in files:
            if f.endswith(suffix):
                hits.append(os.path.join(base, f))
    return hits


def json_rows(path):
    try:
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception:
        return None
    if isinstance(d, list):
        return len(d)
    if isinstance(d, dict):
        for k in ("rows", "items", "entries", "registers", "flags", "records"):
            if isinstance(d.get(k), list):
                return len(d[k])
        return None
    return None


def csv_rows(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = [l for l in fh if l.strip() and not l.lstrip().startswith("#")]
        return max(0, len(lines) - 1)
    except Exception:
        return None


def namespaces():
    return sorted(
        d for d in os.listdir(ROOT)
        if d.startswith("nfl") and os.path.isdir(os.path.join(ROOT, d)) and d != "nfl-desk"
    )


def has_official_citation(path):
    try:
        txt = open(path, encoding="utf-8", errors="replace").read()
    except Exception:
        return False
    return bool(re.search(r"nfl\.com|operations\.nfl\.com", txt))


def main():
    ns = namespaces()
    inventory = []
    for d in ns:
        base = os.path.join(ROOT, d)
        htmls = [p for p in walk(base, ".html") if "node_modules" not in p]
        jsons = [p for p in walk(base, ".json") if "node_modules" not in p]
        csvs = [p for p in walk(base, ".csv") if "node_modules" not in p]
        verifiers = sorted(rel(p) for p in (walk(base, ".py") if os.path.isdir(base) else [])
                           if re.search(r"(verify|check)", os.path.basename(p)))
        readme = os.path.join(base, "README.md")
        inventory.append({
            "namespace": d,
            "pages_html": len(htmls),
            "data_json": len(jsons),
            "data_csv": len(csvs),
            "verifiers": verifiers,
            "readme": rel(readme) if os.path.exists(readme) else "",
            "landing": rel(os.path.join(base, "index.html")) if os.path.exists(os.path.join(base, "index.html")) else "",
        })

    # --- duplication: the same register written many times ---------------------
    dup = {
        "executive_summaries": sorted(rel(p) for p in walk(ROOT, "EXECUTIVE_SUMMARY.md")
                                      if rel(p).split("/")[0].startswith("nfl")),
        "suggestions_pages": sorted(rel(p) for p in walk(ROOT, ".html")
                                    if os.path.basename(p) == "suggestions.html"
                                    and rel(p).split("/")[0].startswith("nfl")),
        "flagged_pages": sorted(rel(p) for p in walk(ROOT, ".html")
                                if os.path.basename(p) == "flagged.html"
                                and rel(p).split("/")[0].startswith("nfl")),
        "questions_pages": sorted(rel(p) for p in walk(ROOT, ".html")
                                  if os.path.basename(p) == "questions.html"
                                  and rel(p).split("/")[0].startswith("nfl")),
        "sources_pages": sorted(rel(p) for p in walk(ROOT, ".html")
                                if os.path.basename(p) == "sources.html"
                                and rel(p).split("/")[0].startswith("nfl")),
    }

    # --- requirement registers -------------------------------------------------
    regs = {}
    candidates = {
        "readiness_register": "nfl-readiness-register/data/requirements.json",
        "req_review_r2": "nfl-req-review/data/requirements_2026_11_18.json",
        "consolidated": "nfl-consolidated/data/requirements.json",
        "command": "nfl-command/data/requirements.json",
    }
    for key, p in candidates.items():
        full = os.path.join(ROOT, p)
        if not os.path.exists(full):
            continue
        rows = json.load(open(full, encoding="utf-8")).get("rows", [])
        regs[key] = {
            "path": p, "url": url(full), "rows": len(rows),
            "status_counts": dict(sorted(Counter(r.get("status") for r in rows).items())),
            "ids": [r.get("id") for r in rows],
        }

    # --- the three registers describe the same 73 lines with different answers ---
    # They use different id schemes (REQ-xx vs A01/B01/...), so rows are matched on
    # normalised requirement text and compared only where the text matches exactly.
    def load_rows(path, text_key, status_key):
        full = os.path.join(ROOT, path)
        if not os.path.exists(full):
            return {}
        out = {}
        for r in json.load(open(full, encoding="utf-8")).get("rows", []):
            t = re.sub(r"[^a-z0-9]+", " ", str(r.get(text_key, "")).lower()).strip()
            if t:
                out.setdefault(t, []).append(
                    {"id": r.get("id"), "status": r.get(status_key),
                     "url": url(full), "path": path})
        return out

    REG = {
        "readiness_register": load_rows("nfl-readiness-register/data/requirements.json", "verbatim", "status"),
        "round2_review": load_rows("nfl-req-review/data/requirements_2026_11_18.json", "requirement", "status"),
        "consolidated": load_rows("nfl-consolidated/data/requirements.json", "requirement", "status"),
    }
    # harmonise vocabularies onto one scale so a difference means a difference, not a synonym
    SYN = {"met": "implemented", "implemented": "implemented",
           "partial": "partial", "blocked": "blocked", "not_started": "open",
           "open": "open", "in_progress": "open", "process": "process",
           "rejected": "rejected", "resolved-at-source": "resolved-at-source"}
    disagreements = []
    names = list(REG)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = REG[names[i]], REG[names[j]]
            for text in sorted(set(a) & set(b)):
                sa = SYN.get(a[text][0]["status"], a[text][0]["status"])
                sb = SYN.get(b[text][0]["status"], b[text][0]["status"])
                if sa != sb:
                    disagreements.append({
                        "text": text[:110],
                        f"{names[i]}_id": a[text][0]["id"],
                        f"{names[i]}_status": a[text][0]["status"],
                        f"{names[j]}_id": b[text][0]["id"],
                        f"{names[j]}_status": b[text][0]["status"],
                        "files": [a[text][0]["path"], b[text][0]["path"]],
                    })
    matched = {
        n: len(REG[n]) for n in REG
    }
    text_matches = {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            text_matches["%s_vs_%s" % (names[i], names[j])] = len(set(REG[names[i]]) & set(REG[names[j]]))

    # --- the corpus question: how many settled games exist ---------------------
    feeds = [
        ("nfl-core/data/results_feed_2026.csv", "csv", "week"),
        ("nfl-ledger/data/results_feed.csv", "csv", "week"),
        ("nfl-marketboard/data/raw/results_2026_official.csv", "csv", None),
        ("nfl-markets/data/results_feed.csv", "filtered", "season"),
    ]
    corpus = []
    for p, kind, col in feeds:
        full = os.path.join(ROOT, p)
        if not os.path.exists(full):
            continue
        n = csv_rows(full)
        item = {"path": p, "url": url(full), "rows": n}
        if kind == "filtered" and col:
            try:
                rows = list(csv.DictReader(open(full, encoding="utf-8", errors="replace")))
                item["rows_2026"] = sum(1 for r in rows if r.get("season") == "2026")
                item["rows_all_seasons"] = len(rows)
                item["columns_present"] = sorted(rows[0].keys())[:14]
                item["has_official_url_column"] = any("official" in c for c in rows[0].keys())
            except Exception as exc:
                item["error"] = str(exc)[:120]
        if p.endswith("results_feed_2026.csv"):
            try:
                rows = list(csv.DictReader(open(full, encoding="utf-8", errors="replace")))
                item["status_counts"] = dict(sorted(Counter(r["status"] for r in rows).items()))
                item["finals"] = sum(1 for r in rows if r["status"] == "FINAL")
                item["scheduled"] = sum(1 for r in rows if r["status"] == "SCHEDULED")
                item["rows_with_scores"] = sum(1 for r in rows if r["away_score"] and r["home_score"])
            except Exception as exc:
                item["error"] = str(exc)[:120]
        corpus.append(item)

    # cross-check the settled-game count against the official standings
    st_path = os.path.join(NS, "data", "standings_2026-11-19.json")
    standings_math = None
    if os.path.exists(st_path):
        st = json.load(open(st_path, encoding="utf-8"))
        team_games = sum(r["W"] + r["L"] + r["T"] for r in st["rows"])
        games_with_remainder = round(team_games / 2)
        standings_math = {
            "teams": len(st["rows"]),
            "team_games_played": team_games,
            "implied_league_games_complete": games_with_remainder,
            "odd_remainder": team_games % 2,
            "source_url": st["source_url"],
            "standings_file": "nfl-desk/data/standings_2026-11-19.json",
            "caution": ("An odd team-game total means at least one game is counted for only one "
                        "club (a postponed/cancelled game). The implied count is an upper bound: "
                        "it assumes every counted game was a normal two-club game."),
        }

    # --- thin artifacts: files with very few rows ------------------------------
    thin = []
    for d in ns:
        for p in walk(os.path.join(ROOT, d), ".json"):
            n = json_rows(p)
            if n is not None and 0 < n <= 6:
                thin.append({"path": rel(p), "url": url(p), "rows": n})
    thin.sort(key=lambda x: (x["rows"], x["path"]))
    thin = [t for t in thin if "/data/" in t["path"]][:40]

    # --- third-party dependence: files that cite nflverse or similar -----------
    third = []
    for d in ns:
        for root, dirs, files in os.walk(os.path.join(ROOT, d)):
            dirs[:] = [x for x in dirs if x not in (".git", "node_modules", "raw")]
            for f in files:
                if f.endswith((".json", ".csv", ".md")):
                    p = os.path.join(root, f)
                    try:
                        txt = open(p, encoding="utf-8", errors="replace").read(4000)
                    except Exception:
                        continue
                    if re.search(r"nflverse|nfldata|pro-football-reference|oddsapi|the-odds-api", txt, re.I):
                        third.append(rel(p))
    third = sorted(set(third))[:30]

    # Deliberately NOT recording `git count-objects` or a tracked-file count here: both
    # depend on the clone (shallow vs full, pack layout), so they would make this committed
    # data file differ between a laptop and CI and break the byte-identical rebuild gate.
    # --- the originated-line file: what "the 136-game log" actually is -----------
    ol_path = os.path.join(ROOT, "nfl-lines/data/derived/own_lines_week10.json")
    own_lines = None
    if os.path.exists(ol_path):
        rows = json.load(open(ol_path, encoding="utf-8"))
        market_cols = [c for c in rows[0] if c.startswith("market_")]
        own_cols = [c for c in rows[0] if c.startswith("own_")]
        own_lines = {
            "path": "nfl-lines/data/derived/own_lines_week10.json",
            "url": url(ol_path),
            "rows": len(rows),
            "weeks": sorted({r.get("week") for r in rows}),
            "games_with_market_spread": sum(1 for r in rows if r.get("market_spread_line") is not None),
            "games_with_market_total": sum(1 for r in rows if r.get("market_total_line") is not None),
            "games_with_own_spread": sum(1 for r in rows if r.get("own_spread_line") is not None),
            "games_without_market": sum(1 for r in rows if r.get("market_spread_line") is None),
            "market_columns": market_cols,
            "own_columns": own_cols,
            "note": ("This is the only file in the repository with exactly 136 rows, which is where the "
                     "brief's '136-game log' most plausibly comes from. It is a full-season schedule with "
                     "a fair line for every fixture and a market value only where a third-party archive "
                     "had one."),
        }

    with_verifier = [n["namespace"] for n in inventory if n["verifiers"]]

    out = {
        "dataset": "nfl_desk_census",
        "title": "Repository census — namespaces, registers, duplication, corpus arithmetic",
        "built_utc": "2026-11-19",
        "method": ("engine/census.py walks the tree; every count below is measured, not typed. "
                   "Disagreements are recorded with both files and both values."),
        "namespaces_count": len(ns),
        "namespaces_with_verifier": len(with_verifier),
        "namespaces_without_verifier": sorted(n["namespace"] for n in inventory if not n["verifiers"]),
        "namespaces": inventory,
        "duplication": {k: {"count": len(v), "paths": v[:60]} for k, v in dup.items()},
        "requirement_registers": regs,
        "register_disagreements": disagreements,
        "register_text_matched_rows": text_matches,
        "register_disagreement_count": len(disagreements),
        "corpus_feeds": corpus,
        "originated_lines": own_lines,
        "standings_cross_check": standings_math,
        "thin_artifacts": thin,
        "third_party_citation_files": third,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print("namespaces", len(ns))
    print("register disagreements", len(disagreements), text_matches)
    print("duplication", {k: len(v) for k, v in dup.items()})
    print("corpus", [(c["path"], c.get("rows")) for c in corpus])
    print("standings check", standings_math)
    print("-> %s" % OUT)


if __name__ == "__main__":
    main()
