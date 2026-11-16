#!/usr/bin/env python3
"""Inventory every decision register in the repository.

Run MANUALLY (or as the informational CI step, after the determinism gate) and commit the
output.  It deliberately never runs as part of the page build: it walks the whole tree, and a
tree walk inside the renderer is how a sibling namespace merging turns this namespace's CI red
through no fault of this namespace's code (the standing warning in COORDINATION.md).  The build
reads the committed snapshot instead, and the snapshot states the commit it describes.

  python3 nfl-decision-console/engine/inventory.py [--write]

Standard library only; deterministic for a fixed tree.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)

REGISTERS = {
    "suggestions": re.compile(r"suggestions\.(json|csv|py)$"),
    "questions": re.compile(r"questions\.(json|csv|py)$"),
    "flags": re.compile(r"flags\.(json|csv|py)$"),
    "requirements": re.compile(r"(requirements|readiness)\.(json|csv|py)$"),
}


VERDICT_FIELDS = ("verdict", "decision", "resolution", "chosen", "choice", "owner_decision")
STATUS_FIELDS = ("status", "state")
TEXT_FIELDS = ("title", "question", "item", "requirement", "name", "summary", "text", "finding", "id")


def row_list(d):
    if isinstance(d, list):
        return d
    if isinstance(d, dict):
        for k in ("rows", "items", "entries", "records"):
            if isinstance(d.get(k), list):
                return d[k]
    return None


def row_text(r):
    """One short comparable string per row, for cross-namespace clustering."""
    if not isinstance(r, dict):
        return str(r)[:300]
    for f in TEXT_FIELDS:
        v = r.get(f)
        if isinstance(v, str) and v.strip():
            return v.strip()[:300]
    return ""


def rows_of(path):
    """Read a register without assuming a schema.

    Returns (n_rows, n_with_verdict_field_filled, n_with_status, [row texts]).  `verdict` counts
    ONLY a decision-shaped field; a register's own engine status ('done', 'needs review') is not a
    reviewer verdict and is counted separately so the two are never conflated on the page.
    """
    if path.endswith(".json"):
        try:
            d = json.load(open(path, encoding="utf-8"))
        except Exception:
            return None, None, None, [], {}, {}
        rows = row_list(d)
        if rows is None and isinstance(d, dict):
            rows = [v for v in d.values() if isinstance(v, list)]
        rows = rows or []
        n = len(rows)

        def filled(row, f):
            v = row.get(f) if isinstance(row, dict) else None
            return isinstance(v, str) and v.strip() and v.strip().lower() not in ("null", "none", "tbd")

        dicts = [r for r in rows if isinstance(r, dict)]
        per_field = {f: sum(1 for r in dicts if filled(r, f)) for f in VERDICT_FIELDS}
        verd = sum(1 for r in dicts if any(filled(r, f) for f in VERDICT_FIELDS))
        stat = sum(1 for r in rows if isinstance(r, dict) and any(
            isinstance(r.get(f), str) and r.get(f, "").strip() for f in STATUS_FIELDS))
        return n, verd, stat, [t for t in (row_text(r) for r in rows) if t], per_field
    if path.endswith(".csv"):
        lines = [l for l in open(path, encoding="utf-8", errors="replace").read().splitlines() if l.strip()]
        head = lines[0].lower().split(",") if lines else []
        idx = [i for i, h in enumerate(head) if any(f in h for f in VERDICT_FIELDS)]
        body = lines[1:]
        verd = 0
        if idx:
            for l in body:
                parts = l.split(",")
                if any(i < len(parts) and parts[i].strip() for i in idx):
                    verd += 1
        texts = []
        if head:
            key = next((i for i, h in enumerate(head) if h.strip() in TEXT_FIELDS[:4]), 1)
            for l in body:
                parts = l.split(",")
                if key < len(parts) and parts[key].strip():
                    texts.append(parts[key].strip()[:300])
        return max(0, len(lines) - 1), verd, verd, texts, {}
    if path.endswith(".py"):
        txt = open(path, encoding="utf-8", errors="replace").read()
        n = len(re.findall(r"^\s{2,8}\{\s*$", txt, re.M))
        texts = [m.group(1).strip()[:300] for m in
                 re.finditer(r'"(?:title|question|item|requirement)"\s*:\s*"([^"]{4,300})"', txt)]
        return (n or len(texts) or None), 0, 0, texts, {}
    return None, None, None, [], {}


def main(write):
    namespaces = sorted(d for d in os.listdir(ROOT)
                        if d.startswith("nfl") and os.path.isdir(os.path.join(ROOT, d)))
    regs, seen = [], set()
    for ns in namespaces + ["verification"]:
        base = os.path.join(ROOT, ns)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [x for x in dirnames if x not in ("node_modules", ".git")]
            for fn in sorted(filenames):
                p = os.path.join(dirpath, fn)
                rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
                if rel in seen or "/pages/" in "/" + rel:
                    continue
                for kind, rx in REGISTERS.items():
                    if rx.search(fn):
                        seen.add(rel)
                        n, verd, stat, texts, fields = rows_of(p)
                        regs.append({"path": rel, "namespace": ns, "kind": kind, "rows": n,
                                     "rows_with_verdict": verd, "rows_with_status": stat,
                                     "verdict_field_counts": fields, "row_texts": texts})
                        break
    totals = {}
    for r in regs:
        t = totals.setdefault(r["kind"], {"files": 0, "rows": 0, "with_verdict": 0,
                                          "with_status": 0, "namespaces": set()})
        t["files"] += 1
        t["rows"] += (r["rows"] or 0)
        t["with_verdict"] += (r["rows_with_verdict"] or 0)
        t["with_status"] += (r["rows_with_status"] or 0)
        t["namespaces"].add(r["namespace"])
        for f, c in (r.get("verdict_field_counts") or {}).items():
            t.setdefault("field_counts", {})
            t["field_counts"][f] = t["field_counts"].get(f, 0) + c
    try:
        head_sha = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"],
                                  capture_output=True, text=True).stdout.strip()
    except Exception:
        head_sha = ""
    out = {
        "dataset": "decision_console_inventory",
        "title": "Every suggestion / question / flag / requirement register in the repository, as at one commit",
        "captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "captured_at_commit": head_sha,
        "rule": "counts and row texts are read from the committed registers by engine/inventory.py. "
                "The page build reads THIS file and never re-walks the tree, so a sibling namespace "
                "merging cannot change a published number here (see the standing warning in "
                "COORDINATION.md). Re-run with --write to refresh, and say so in the commit message.",
        "namespace_count": len(namespaces),
        "namespaces": namespaces,
        "counts": {k: {"files": v["files"], "rows": v["rows"], "rows_with_verdict": v["with_verdict"],
                        "rows_with_status": v["with_status"], "namespaces": len(v["namespaces"])}
                   for k, v in sorted(totals.items())},
        "registers": sorted(regs, key=lambda r: (r["kind"], r["namespace"], r["path"])),
    }
    blob = json.dumps(out, indent=1, sort_keys=True) + "\n"
    dest = os.path.join(NS, "data", "namespace_inventory.json")
    if write:
        open(dest, "w", encoding="utf-8").write(blob)
        print("wrote %s (%d bytes, sha256 %s)" % (os.path.relpath(dest, ROOT), len(blob),
                                                  hashlib.sha256(blob.encode()).hexdigest()[:12]))
    else:
        print(json.dumps(out["counts"], indent=1))
        print("registers:", len(regs), "namespaces:", len(namespaces))
    return 0


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv))
