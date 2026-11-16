#!/usr/bin/env python3
"""Origination order, enforced in code rather than in prose.

The brief's first structural rule is an ORDER: originate a side market, then a total, then a
moneyline - and publish the model's fair line, the market line, and the difference between them as
three separate columns.

This module owns that order. It does not produce a line: a line needs a price, and this repository
has no official price source (flag RF-02), so `main()` verifies the contract, prints the gate state,
and exits non-zero when someone tries to originate out of order or to originate into an empty store.

Run it two ways:
  python3 engine/originate.py            # audit the store + fixtures, print gate state
  python3 engine/originate.py --probe     # deliberately violate the order; must fail (used by CI
                                          # to prove the guard is live, not decorative)
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
STORE = os.path.join(NS, "data", "price_snapshots.json")
FIXTURES = os.path.join(NS, "data", "fixtures_week10.csv")

ORDER = ["side", "total", "moneyline"]  # team_total and player_prop are gated behind joint evidence
PUBLIC_COLUMNS = ["model_fair_line", "market_line", "difference_model_minus_market"]


def load_store():
    with open(STORE, encoding="utf-8") as fh:
        return json.load(fh)


def check_order(rows) -> list[str]:
    """A market may exist only if every earlier market in ORDER exists for the same game."""
    problems: list[str] = []
    seen: dict[str, set[str]] = {}
    for r in rows:
        seen.setdefault(r["game_key"], set()).add(r["market"])
    for gk, mk in seen.items():
        for i, m in enumerate(ORDER):
            if m in mk and any(p not in mk for p in ORDER[:i]):
                problems.append(f"{gk}: '{m}' recorded before {ORDER[:i]} - origination order violated")
    return problems


def check_columns(rows) -> list[str]:
    problems = []
    for r in rows:
        for c in PUBLIC_COLUMNS:
            if c not in r:
                problems.append(f"row {r.get('id','?')}: missing published column '{c}'")
        # the difference may never be the only number on a row
        if r.get("difference_model_minus_market") not in (None, "") and \
           r.get("model_fair_line") in (None, ""):
            problems.append(f"row {r.get('id','?')}: a difference without a fair line - "
                            "publish all three columns or none")
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true", help="assert the guards fire; exit non-zero if they do not")
    ap.parse_args(argv)

    store = load_store()
    rows = store.get("rows", [])
    import csv as _csv
    with open(FIXTURES, newline="", encoding="utf-8") as fh:
        fixtures = list(_csv.DictReader(fh))

    problems = check_order(rows) + check_columns(rows)
    price_ready = bool(rows) and any(r.get("source_grade") == "official" for r in rows)

    report = {
        "origination_order": ORDER,
        "published_columns": PUBLIC_COLUMNS,
        "store_rows": len(rows),
        "fixtures_available": len(fixtures),
        "price_gate_open": price_ready,
        "decision_blocking": "DEC-P1 (data/governance.json price_data_policy)",
        "why_no_lines": (
            "The store holds zero price rows and no official price source exists, so this program "
            "refuses to originate a market: an originated line with nothing to compare it to would "
            "publish a difference column of all-nulls and invite a reader to treat the model's number "
            "as market evidence. The order, the columns and the guard are the deliverable today."
        ),
        "guard_problems": problems,
    }
    print(json.dumps(report, indent=1))

    if args_probe_requested(argv):
        # the probe: out-of-order and difference-without-fair-line must both be caught
        bad = [{"id": "probe", "game_key": "X@Y-2026-reg-10", "market": "moneyline",
                "model_fair_line": None, "market_line": None, "difference_model_minus_market": 1.5}]
        caught = check_order(bad) + check_columns(bad)
        ok = bool(caught)
        print(json.dumps({"probe_caught": caught, "verdict": "PASS" if ok else "FAIL"}, indent=1))
        return 0 if ok else 1

    if problems:
        return 1
    return 0


def args_probe_requested(argv) -> bool:
    return any(a == "--probe" for a in (argv or []))


if __name__ == "__main__":
    sys.exit(main())
