#!/usr/bin/env python3
"""CI gate: re-verify the archive against the official transcription.

Exits non-zero if any official spot-check game mismatches the archive or any
integrity check fails. Read-only.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dataset as D  # noqa: E402


def main() -> int:
    games = D.normalise_archive(D.load_archive())
    standings = D.load_json(os.path.join(D.OFFICIAL, "standings_2026.json"))

    v = D.verify_against_official(games)
    ic = D.integrity_checks(games, standings)

    print("official score spot-check : %s / %s matched, %s mismatched, %s missing"
          % (v["matched"], v["games_compared"], v["mismatched"], v["missing_in_archive"]))
    print("weeks checked             : %s" % v["weeks_checked"])
    print("weeks not usable          : %s" % v["weeks_attempted_not_usable"])

    for r in ic:
        print("%-6s %-8s %s" % (r["id"], "PASS" if r["passed"] else "FAIL", r["check"]))
        print("       %s" % r["detail"])

    failed = [r["id"] for r in ic if not r["passed"]]
    ok = (v["mismatched"] == 0 and v["missing_in_archive"] == 0
          and v["matched"] == v["games_compared"] and not failed)
    if not ok:
        print("\nFAILED: %s" % (failed or "official spot-check"))
        return 1
    print("\nOK: %d/%d official games match and all %d integrity checks pass."
          % (v["matched"], v["games_compared"], len(ic)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
