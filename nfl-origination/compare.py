"""Semantic reproducibility check: compare two builds of the site and its data.

    python3 nfl-origination/compare.py SNAPSHOT_DIR LIVE_DIR

`verify.py` proves the published site is internally consistent. This proves the *pipeline* is a
pure function of its inputs, which is a different claim, and one that cannot be checked by byte
comparison across environments: floating-point results legitimately differ in the last digit
between Python versions and C libraries, and `statistics` changed its summation in Python 3.12.

So the rule here is: every non-numeric byte must match exactly, and every number must match to a
relative tolerance of 1e-9. A real regression -- a changed parameter, a dropped leg, a gate that
flips -- moves a number by far more than that, or changes a word, and both are caught.
"""
import json
import pathlib
import re
import sys

TOL = 1e-9
NUM = re.compile(r"-?\d+\.\d+(?:[eE][+-]?\d+)?")


def close(a, b):
    if a == b:
        return True
    return abs(a - b) <= TOL * max(1.0, abs(a), abs(b))


def cmp_json(a, b, path, problems):
    if type(a) is not type(b) and not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
        problems.append("%s: type %s != %s" % (path, type(a).__name__, type(b).__name__))
        return
    if isinstance(a, dict):
        if set(a) != set(b):
            problems.append("%s: keys differ (+%s / -%s)"
                            % (path, sorted(set(b) - set(a)), sorted(set(a) - set(b))))
            return
        for k in a:
            cmp_json(a[k], b[k], "%s.%s" % (path, k), problems)
    elif isinstance(a, list):
        if len(a) != len(b):
            problems.append("%s: length %d != %d" % (path, len(a), len(b)))
            return
        for i, (x, y) in enumerate(zip(a, b)):
            cmp_json(x, y, "%s[%d]" % (path, i), problems)
    elif isinstance(a, str):
        if a != b:
            problems.append("%s: %r != %r" % (path, a[:80], b[:80]))
    else:
        if not close(a, b):
            problems.append("%s: %r != %r" % (path, a, b))


def normalise_html(s):
    def repl(m):
        try:
            v = float(m.group(0))
        except ValueError:
            return m.group(0)
        return "%.10g" % v
    return NUM.sub(repl, s)


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    left, right = pathlib.Path(argv[1]), pathlib.Path(argv[2])
    problems, checked = [], 0

    for sub in ("data", "pages"):
        base = left / sub
        if not base.exists():
            print("missing snapshot: %s" % base)
            return 2
        for f in sorted(base.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(left)
            other = right / rel
            checked += 1
            if not other.exists():
                problems.append("%s: missing from the rebuild" % rel)
                continue
            if f.suffix == ".json":
                try:
                    cmp_json(json.loads(f.read_text()), json.loads(other.read_text()),
                             str(rel), problems)
                except json.JSONDecodeError as exc:
                    problems.append("%s: not valid JSON (%s)" % (rel, exc))
            elif f.suffix == ".html":
                a, b = normalise_html(f.read_text()), normalise_html(other.read_text())
                if a != b:
                    for i, (x, y) in enumerate(zip(a.split("\n"), b.split("\n")), 1):
                        if x != y:
                            problems.append("%s line %d differs" % (rel, i))
                            break
            else:
                if f.read_bytes() != other.read_bytes():
                    problems.append("%s: bytes differ" % rel)

    # every file the rebuild adds must have existed in the snapshot
    for sub in ("data", "pages"):
        for f in sorted((right / sub).rglob("*")):
            if f.is_file() and not (left / f.relative_to(right)).exists():
                problems.append("%s: unexpected new file" % f.relative_to(right))

    print("compared %d files" % checked)
    if problems:
        print("\nDIFFERENCES (%d):" % len(problems))
        for p in problems[:40]:
            print("  " + p)
        return 1
    print("rebuild is reproducible: identical text, every number within %.0e relative" % TOL)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
