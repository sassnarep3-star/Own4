#!/usr/bin/env python3
"""Compare a recomputed data tree against the committed one.

Why this exists: `math.erf` is supplied by the platform C library, and CPython
builds on different runners can disagree in the last bits. That is enough to
flip a `>= theta` comparison for one bet out of ~7,000 when the CI runs on a
different Python/glibc than the machine that produced the committed files.

The rule here is therefore:
  * structure, keys, strings, integers and booleans must match EXACTLY;
  * floats must match to a relative tolerance of 1e-6 (far tighter than any
    figure published on the site, all of which are rounded to <= 4 decimals).

Anything else is a failure. This still catches a changed threshold, a changed
bet count, a reclassified tier or a different winner.

    python3 nfl-hub/compare.py <recomputed_dir> <committed_dir>
"""
from __future__ import annotations

import json
import os
import sys

RTOL = 1e-6
ATOL = 1e-9
FAILS = []


def compare(path, a, b, where=""):
    if type(a) is not type(b):
        # int/float mixing is fine when the values agree
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            pass
        else:
            FAILS.append(f"{path}{where}: type {type(a).__name__} vs {type(b).__name__}")
            return
    if isinstance(a, dict):
        if set(a) != set(b):
            FAILS.append(f"{path}{where}: keys differ ({sorted(set(a) ^ set(b))[:4]})")
            return
        for k in a:
            compare(path, a[k], b[k], f"{where}.{k}")
    elif isinstance(a, list):
        if len(a) != len(b):
            FAILS.append(f"{path}{where}: length {len(a)} vs {len(b)}")
            return
        for i, (x, y) in enumerate(zip(a, b)):
            compare(path, x, y, f"{where}[{i}]")
    elif isinstance(a, float) or isinstance(b, float):
        x, y = float(a), float(b)
        if abs(x - y) > ATOL + RTOL * max(abs(x), abs(y)):
            FAILS.append(f"{path}{where}: {x!r} vs {y!r}")
    else:
        if a != b:
            FAILS.append(f"{path}{where}: {a!r} vs {b!r}")


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    fresh, committed = sys.argv[1], sys.argv[2]
    checked = 0
    for root, _, files in os.walk(fresh):
        for f in sorted(files):
            if not f.endswith(".json"):
                continue
            rel = os.path.relpath(os.path.join(root, f), fresh)
            fp = os.path.join(committed, rel)
            if not os.path.exists(fp):
                FAILS.append(f"{rel}: missing from committed tree")
                continue
            try:
                a = json.load(open(os.path.join(fresh, rel)))
                b = json.load(open(fp))
            except Exception as exc:  # noqa: BLE001
                FAILS.append(f"{rel}: parse error {exc}")
                continue
            compare(rel, a, b)
            checked += 1
    if FAILS:
        print(f"FAIL: {len(FAILS)} differences across {checked} JSON files")
        for x in FAILS[:25]:
            print("  -", x)
        return 1
    print(f"PASS: {checked} JSON files are identical to structure and equal within {RTOL:g} relative tolerance")
    return 0


if __name__ == "__main__":
    sys.exit(main())
