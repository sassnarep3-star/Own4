#!/usr/bin/env python3
"""
Own4 · nfl-live-board · substance.py — the determinism gate, done honestly.

A byte-for-byte `git diff` is the wrong gate for data that contains floating point. The engines
call `math.erf` and a seeded RNG; a different C library (glibc version, CPU) can move the last
bit of an erf, and inside a permutation loop that can flip one comparison and shift a p-value in
the fourth decimal. This repository's own canonical gate documents exactly that problem, so it
asserts invariants instead of bytes. This does the same, and is stricter about everything that
is not a float.

For every committed JSON artefact it compares the committed value with the freshly rebuilt one:

    floats  - must agree within 1e-9 relative tolerance; a float that differs but is inside
              tolerance is recorded as tolerated drift and printed, never silently accepted;
    ints / strings / bools / nulls - must be exactly equal;
    list lengths and dict key sets - must be exactly equal.

Exit 1 on any substantive difference. Run after engine/run_all.sh has rebuilt data/.

    python3 nfl-live-board/engine/substance.py
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
DATA = os.path.join(ROOT, "data")
REL = "nfl-live-board/data/"
TOL = 1e-9

substantive, tolerated = [], []


def walk(path, a, b):
    """Compare committed (a) with rebuilt (b)."""
    if isinstance(a, float) or isinstance(b, float):
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            substantive.append((path, a, b))
            return
        if a == b:
            return
        scale = max(1.0, abs(a), abs(b))
        if abs(a - b) <= TOL * scale:
            tolerated.append((path, a, b))
        else:
            substantive.append((path, a, b))
        return
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            substantive.append((path + "/keys", sorted(set(a) ^ set(b)), "symmetric difference"))
            return
        for k in a:
            walk(path + "/" + str(k), a[k], b[k])
        return
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            substantive.append((path + "/len", len(a), len(b)))
            return
        for i, (x, y) in enumerate(zip(a, b)):
            walk(path + "/%d" % i, x, y)
        return
    if a != b or type(a) is not type(b):
        substantive.append((path, a, b))


def main():
    files = sorted(f for f in os.listdir(DATA) if f.endswith(".json"))
    for f in files:
        try:
            committed = subprocess.run(["git", "show", "HEAD:" + REL + f],
                                       cwd=REPO, capture_output=True, text=True, check=True).stdout
        except subprocess.CalledProcessError:
            substantive.append((f, "tracked in HEAD", "not found (uncommitted artefact)"))
            continue
        a = json.loads(committed)
        with open(os.path.join(DATA, f)) as fh:
            b = json.load(fh)
        walk(f, a, b)

    print("artefacts compared: %d" % len(files))
    if tolerated:
        print("tolerated float drift (last-bit libm differences, inside %g relative): %d" % (TOL, len(tolerated)))
        for p, x, y in tolerated[:8]:
            print("   %s  committed=%r rebuilt=%r" % (p, x, y))
    if substantive:
        print("\nSUBSTANTIVE DIFFERENCES: %d" % len(substantive))
        for p, x, y in substantive[:25]:
            print("   %s  committed=%r rebuilt=%r" % (p, x, y))
        return 1
    print("no substantive difference: every non-float value is identical, every float is inside tolerance")
    return 0


if __name__ == "__main__":
    sys.exit(main())
