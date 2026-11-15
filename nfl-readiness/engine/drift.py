#!/usr/bin/env python3
"""Drift alarm: fail loudly when a source changes shape, instead of returning quiet zeros.

The brief's requirement, verbatim in intent: "add a drift alarm on every scraper pinned to expected
row counts and required fields". This is that alarm, written against the transcribed capture so the
check is reproducible in CI without network access. When a scheduled collector lands (SUG-02), it
calls `check()` on whatever it fetched before writing anything, and a non-zero exit is the alert.

Checks, each pinned in data/drift_expectations.json:
  * total rows, club sections, fixture count;
  * per-club row counts (the failure mode that matters: one club's table silently disappearing);
  * required fields present, and non-blank where a blank cannot be legal;
  * vocabulary: an unlisted practice/game-status string means the source changed;
  * designation coverage floor (a lost column shows up as coverage collapsing, not as an error);
  * blanks that were rewritten into a value ('None', 'Healthy') - the classic silent-inflation bug.

It also writes data/derived/hashes.json: sha256 over each artefact the capture manifest lists.
Those are transcription fingerprints (see the manifest's immutability_limitation), not proofs about
the original page bytes, and the difference is stated on the page that publishes them.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
EXP = os.path.join(NS, "data", "drift_expectations.json")
SNAP = os.path.join(NS, "data", "availability_snapshot_2026-11-15.csv")
DER = os.path.join(NS, "data", "derived")
BAD_BLANKS = {"none", "null", "n/a", "healthy", "available", "no", "-"}


def load_rows(path: str):
    with open(path, newline="", encoding="utf-8") as fh:
        rdr = csv.DictReader(fh)
        return rdr.fieldnames or [], list(rdr)


def check(rows, header, exp) -> list[str]:
    e = exp["expected"]
    bad: list[str] = []
    for f in e["required_fields"]:
        if f not in header:
            bad.append(f"SCHEMA: required field '{f}' is absent from the capture header")
    if len(rows) != e["rows_total"]:
        bad.append(f"ROWS: expected {e['rows_total']}, got {len(rows)} "
                   f"(delta {len(rows) - e['rows_total']:+d})")
    teams = []
    per: dict[str, int] = {}
    for r in rows:
        t = r.get("team", "")
        per[t] = per.get(t, 0) + 1
        if not teams or teams[-1] != t:
            teams.append(t)
    if len(teams) != e["club_sections"]:
        bad.append(f"SECTIONS: expected {e['club_sections']} club sections, got {len(teams)}")
    for t, want in e["rows_by_club"].items():
        got = per.get(t, 0)
        if got != want:
            bad.append(f"CLUB {t}: expected {want} rows, got {got}")
    extra = sorted(set(per) - set(e["rows_by_club"]))
    if extra:
        bad.append(f"CLUBS not in the pinned expectation (new, padded, or a bye week ending): {extra}")
    gs_ok = set(e["allowed_game_status"]) | {""}
    pr_ok = set(e["allowed_practice_status"])
    designated = 0
    for i, r in enumerate(rows, 2):
        for f in e["must_be_nonblank"]:
            if not (r.get(f) or "").strip():
                bad.append(f"line {i}: required non-blank field '{f}' is empty")
        for f in e["required_fields"]:
            if f in (r.get("") or {}):
                bad.append(f"line {i}: ragged row (wrong field count)")
        gs = (r.get("game_status") or "").strip()
        if gs not in gs_ok:
            bad.append(f"line {i}: game_status '{gs}' is outside the pinned vocabulary")
        if gs.lower() in BAD_BLANKS:
            bad.append(f"line {i}: game_status '{gs}' is a rewritten blank, not a published value")
        pr = (r.get("practice_status") or "").strip()
        if pr not in pr_ok:
            bad.append(f"line {i}: practice_status '{pr}' is outside the pinned vocabulary")
        if pr.lower() in BAD_BLANKS:
            bad.append(f"line {i}: practice_status '{pr}' is a rewritten blank")
        if gs:
            designated += 1
    if rows:
        cov = round(100 * designated / len(rows), 1)
        floor = e["designation_coverage_pct"]["floor_pct"]
        if cov < floor:
            bad.append(f"COVERAGE: designation coverage {cov}% is below the {floor}% tripwire - "
                       "the capture has probably lost its Game Status column")
    return bad


def main() -> int:
    with open(EXP, encoding="utf-8") as fh:
        exp = json.load(fh)
    header, rows = load_rows(SNAP)
    bad = check(rows, header, exp)

    with open(os.path.join(NS, "data", "capture_manifest.json"), encoding="utf-8") as fh:
        man = json.load(fh)
    hashes = {}
    for rel in man["hashed_files"]:
        p = os.path.join(NS, rel)
        if not os.path.exists(p):
            bad.append(f"MANIFEST: hashed file missing: {rel}")
            continue
        h = hashlib.sha256()
        with open(p, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 16), b""):
                h.update(chunk)
        hashes[rel] = {"sha256": h.hexdigest(), "bytes": os.path.getsize(p)}
    os.makedirs(DER, exist_ok=True)
    with open(os.path.join(DER, "hashes.json"), "w", encoding="utf-8") as fh:
        json.dump({"note": man["immutability_limitation"],
                   "algorithm": "sha256", "files": hashes}, fh, indent=1)
        fh.write("\n")

    out = {"pinned_from": exp["pinned_from"], "rows_checked": len(rows),
           "verdict": "PASS" if not bad else "FAIL", "problems": bad,
           "hashes_written": len(hashes)}
    with open(os.path.join(DER, "drift_report.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
        fh.write("\n")
    print(json.dumps({k: v for k, v in out.items() if k != "problems"}, indent=1))
    for b in bad[:40]:
        print("DRIFT:", b)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
