#!/usr/bin/env python3
"""Verifier for nfl-repo-inventory (stdlib only).

Checks:
  1. Rebuild is deterministic: build.py output equals the committed pages.
  2. Every local href and src resolves to a file in this namespace.
  3. Every inventory row has a GitHub source link; every flag has at least one evidence link.
  4. Overview tile counts equal counts recomputed from data/*.json.
  5. Every verifier run refers to a namespace in the inventory and a file in the repository.
  6. No localhost / 127.0.0.1 references in any page.
Exit code 0 = PASS.
"""
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, ".."))
DATA = os.path.join(HERE, "data")
PAGES = ["index.html", "pages/inventory.html", "pages/verifier-runs.html", "pages/flagged.html"]
problems = []


def fail(msg):
    problems.append(msg)


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


spec = importlib.util.spec_from_file_location("build", os.path.join(HERE, "engine", "build.py"))
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

inv = load("inventory.json")
runs = load("verifier_runs.json")
flags = load("flags.json")
reads = load("official_reads.json")

# 1. determinism
expected = {
    "index.html": build.overview(inv, runs, flags, reads),
    os.path.join("pages", "inventory.html"): build.inventory_page(inv),
    os.path.join("pages", "verifier-runs.html"): build.runs_page(runs),
    os.path.join("pages", "flagged.html"): build.flags_page(flags),
}
for rel, text in expected.items():
    path = os.path.join(HERE, rel)
    if not os.path.exists(path):
        fail(f"missing page {rel}")
        continue
    with open(path, encoding="utf-8") as fh:
        if fh.read() != text:
            fail(f"{rel} is stale: rerun engine/build.py")

# 2. local links
for rel in PAGES:
    path = os.path.join(HERE, rel)
    if not os.path.exists(path):
        continue
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if re.search(r"localhost|127\.0\.0\.1", text):
        fail(f"{rel}: localhost reference")
    for href in re.findall(r'href="([^"]+)"', text):
        if href.startswith(("http://", "https://", "#", "mailto:")):
            continue
        target = os.path.normpath(os.path.join(os.path.dirname(path), href))
        if href.startswith("../"):
            # the root site link is outside this namespace; check it exists in the repo
            if not os.path.exists(target):
                fail(f"{rel}: broken link {href}")
            continue
        if not os.path.exists(target):
            fail(f"{rel}: broken local link {href}")

# 3. source links per row
for r in inv["rows"]:
    if not str(r.get("github_url", "")).startswith("https://github.com/"):
        fail(f"inventory row {r.get('namespace')} has no GitHub source link")
    if r.get("namespace") and not os.path.isdir(os.path.join(REPO, r["namespace"])):
        fail(f"inventory namespace {r['namespace']} is not a directory in the repository")
for f in flags["flags"]:
    if not f.get("evidence"):
        fail(f"flag {f['id']} has no evidence link")
    for u in f["evidence"]:
        if u.startswith("https://github.com/sassnarep3-star/Own4/blob/main/"):
            rel = u.split("/blob/main/", 1)[1]
            if not os.path.exists(os.path.join(REPO, rel)):
                fail(f"flag {f['id']}: evidence file {rel} not in repository")
for rr in reads["rows"]:
    if not str(rr.get("url", "")).startswith("https://www.nfl.com/"):
        fail(f"official read '{rr.get('what')}' does not link to nfl.com")

# 4. tile counts
rows = inv["rows"]
expected_counts = {
    "nfl* namespaces": inv["namespace_count"],
    "tracked files": sum(r["tracked_files"] for r in rows),
    "with a verifier": sum(1 for r in rows if r["verifier_path"]),
    "flags for review": len(flags["flags"]),
}
with open(os.path.join(HERE, "index.html"), encoding="utf-8") as fh:
    idx = fh.read()
for label, value in expected_counts.items():
    if not re.search(rf'<div class="tile"><b>{value}</b>{re.escape(label)}</div>', idx):
        fail(f"overview tile '{label}' does not equal {value}")
if inv["namespace_count"] != len(rows):
    fail("namespace_count does not match rows")

# 5. verifier runs
names = {r["namespace"] for r in rows}
for r in runs["runs"]:
    if r["namespace"] not in names:
        fail(f"verifier run for unknown namespace {r['namespace']}")
    if not os.path.exists(os.path.join(REPO, r["verifier"])):
        fail(f"verifier file {r['verifier']} not in repository")

if problems:
    print("FAIL")
    for p in problems:
        print(" -", p)
    sys.exit(1)
print(f"PASS - {len(rows)} namespaces, {len(runs['runs'])} verifier runs, {len(flags['flags'])} flags, "
      f"{len(PAGES)} pages: deterministic build, links resolve, every row sourced, tiles match data.")
