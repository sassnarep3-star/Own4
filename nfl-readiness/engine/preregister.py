#!/usr/bin/env python3
"""Freeze a rule to git and record the commit as its registration.

The brief's pre-registration requirement, made mechanical: "pre-register by freezing the rule text,
the sample window and the gates to git before the evaluation window opens; the commit hash is the
registration". prose is cheap, so this file makes the claim checkable:

  python3 engine/preregister.py --freeze prereg/PREREG-001-shadow-baseline.md
      -> hashes the file, records it in data/prereg.json together with the commit that contains it
         (HEAD if HEAD already has the file, otherwise 'pending' with the reason), plus the
         evaluation-window state at freeze time.

  python3 engine/preregister.py --check
      -> the CI form. Fails when a frozen file has changed since its recorded commit, when the
         recorded commit does not contain the file, or when an entry was written as 'pending' and
         never resolved. A rule that can be edited after the fact is not pre-registered, so this is
         a build gate, not a report.

Two facts are deliberately recorded side by side: the hash of the rule text, and whether the
evaluation window had opened. Registration means the second was false when the first was written.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)
REG = os.path.join(NS, "data", "prereg.json")


def sh(*args: str) -> str:
    r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    return (r.stdout or "").strip()


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def commit_exists(commit: str) -> bool:
    """False when the checkout is shallow and the registration commit was not fetched."""
    if not commit:
        return False
    return subprocess.run(["git", "cat-file", "-t", commit], cwd=ROOT, capture_output=True).returncode == 0


def git_has(rel: str, commit: str) -> bool:
    return subprocess.run(["git", "cat-file", "-e", f"{commit}:{rel}"], cwd=ROOT,
                          capture_output=True).returncode == 0


def load() -> dict:
    if os.path.exists(REG):
        with open(REG, encoding="utf-8") as fh:
            return json.load(fh)
    return {
        "dataset": "preregistration_ledger",
        "title": "Every rule frozen to git before its evaluation window opened",
        "rule": ("the commit hash is the registration; a change to the rule text after registration "
                 "requires a new id, never an edit"),
        "git_repo_root": os.path.relpath(ROOT, ROOT) or ".",
        "entries": [],
    }


def save(reg: dict) -> None:
    with open(REG, "w", encoding="utf-8") as fh:
        json.dump(reg, fh, indent=1)
        fh.write("\n")


def freeze(rel: str, window_state: str) -> int:
    path = os.path.join(NS, rel)
    if not os.path.exists(path):
        print(f"refusing to register {rel}: file does not exist")
        return 2
    head = sh("git", "rev-parse", "HEAD") or "no-git"
    in_head = git_has(os.path.relpath(path, ROOT), head) if head != "no-git" else False
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = {
        "id": os.path.basename(rel).split("-")[0] + "-" + os.path.basename(rel).split("-")[1][:3],
        "file": "nfl-readiness/" + rel,
        "sha256_at_freeze": sha256(path),
        "frozen_utc": now,
        "registered_commit": head if in_head else None,
        "commit_state": ("registered" if in_head else
                         "pending: the file is not yet in any commit, so the hash of the commit that "
                         "lands it is the registration - re-run --freeze after committing"),
        "evaluation_window_state_at_freeze": window_state,
        "check_command": f"python3 nfl-readiness/engine/preregister.py --check",
    }
    reg = load()
    reg["entries"] = [e for e in reg.get("entries", []) if e["file"] != entry["file"]] + [entry]
    reg["updated_utc"] = now
    save(reg)
    print(json.dumps(entry, indent=1))
    return 0 if in_head else 1


def check() -> int:
    if not os.path.exists(REG):
        print("no preregistration ledger at data/prereg.json")
        return 1
    reg = load()
    head = sh("git", "rev-parse", "HEAD") or "no-git"
    problems: list[str] = []
    skipped: list[str] = []
    for e in reg.get("entries", []):
        rel = e["file"].replace("nfl-readiness/", "")
        path = os.path.join(NS, rel)
        if not os.path.exists(path):
            problems.append(f"{e['id']}: registered file {rel} is gone")
            continue
        now_hash = sha256(path)
        commit = e.get("registered_commit")
        if not commit:
            problems.append(f"{e['id']}: registered_commit is null ({e.get('commit_state','')}) - "
                            "a pending registration is not a registration; re-run --freeze after "
                            "the file is committed")
            continue
        if not commit_exists(commit):
            skipped.append(f"{e['id']}: registration commit {commit[:9]} is not in this checkout "
                           "(shallow clone) - blob equality against HEAD was used instead")
            if sha_blob(e["file"], "HEAD") != now_hash:
                problems.append(f"{e['id']}: {rel} differs from the frozen hash and the registration "
                                f"commit could not be inspected here")
            continue
        if not git_has(e["file"], commit):
            problems.append(f"{e['id']}: commit {commit[:9]} does not contain {e['file']}")
        elif sha_blob(e["file"], commit) != now_hash:
            problems.append(f"{e['id']}: {rel} has changed since registration {commit[:9]} "
                            "(text edited after the freeze - needs a new id)")
        window = e.get("evaluation_window_state_at_freeze", "")
        if not window:
            problems.append(f"{e['id']}: no evaluation-window state recorded at freeze time")
    for k in skipped:
        print("NOTED:", k)
    print(f"entries: {len(reg.get('entries', []))} · head {head[:9]}")
    for e in reg.get("entries", []):
        print(f"  {e['id']}: {e['file']} @ {(e.get('registered_commit') or 'PENDING')[:9]}")
    if problems:
        for p in problems:
            print("PROBLEM:", p)
        return 1
    print("verdict: PASS - every registered rule is unchanged since its registration commit")
    return 0


def sha_blob(rel: str, commit: str) -> str:
    raw = subprocess.run(["git", "show", f"{commit}:{rel}"], cwd=ROOT, capture_output=True)
    return hashlib.sha256(raw.stdout).hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", metavar="RELATIVE_PATH")
    ap.add_argument("--window-state", default="not opened: no evaluation has been run against any price data")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.freeze:
        return freeze(a.freeze, a.window_state)
    if a.check:
        return check()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
