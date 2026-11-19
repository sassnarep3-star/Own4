#!/usr/bin/env python3
"""
CI helper: fail if a rebuild changed a committed byte, and say exactly which bytes.

`git diff --exit-code` on its own gives a bare exit code in a log nobody can read from a
sandbox. This prints the changed lines and, on failure, emits a GitHub error annotation
carrying the first few of them, so the unstable value is named in the checks UI.

Run in CI after a full rebuild:
    python3 nfl-origination-lab/engine/repro_diff.py
"""

import re
import subprocess
import sys

PATHS = ["nfl-origination-lab/data", "nfl-origination-lab/pages",
         "nfl-origination-lab/index.html"]


def main():
    diff = subprocess.run(["git", "diff", "--", *PATHS], capture_output=True, text=True).stdout
    if not diff.strip():
        print("rebuild is byte-identical across every committed file")
        return 0

    changed = [l for l in diff.splitlines()
               if l[:1] in "+-" and not l.startswith(("+++", "---"))]
    files = [l.split(" b/")[-1] for l in diff.splitlines() if l.startswith("diff --git")]
    print("REPRODUCIBILITY FAILURE in %d file(s): %s" % (len(files), ", ".join(files)))
    for line in changed[:40]:
        print("  " + line[:200])
    summary = " | ".join(re.sub(r"\s+", " ", l)[:80] for l in changed[:6])[:900]
    print("::error title=rebuild-not-reproducible::%s" % (summary or "diff with no value lines"))
    return 1


if __name__ == "__main__":
    sys.exit(main())
