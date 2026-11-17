#!/usr/bin/env python3
"""
verify.py — D7 verifier for the nfl-depth-sweep namespace.

Checks (exit 1 on any failure):
1. ROW-SOURCE GATE: every club in depth_register.json carries an http(s) source URL;
   every position row is traceable to a checked-in transcript + parsed artefact.
2. BROKEN-LINK: source URLs are well-formed http(s); internal site links resolve to
   files on disk; referenced transcript/parsed files exist.
3. NO-LOCALHOST: generated site HTML contains no localhost/127.0.0.1 references.
4. DETERMINISM: re-running the engines reproduces byte-identical artefacts.
5. CONSISTENCY: teams.json has 32 clubs; the register has 32 clubs; every parsed file
   exists; flag evidence strings are present in the raw transcripts.

Run: python3 nfl-depth-sweep/engine/verify.py
"""

import json
import re
import subprocess
import sys
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = ROOT / "site"
ENGINE = ROOT / "engine"

failures = []


def check(ok: bool, label: str):
    if ok:
        print(f"  PASS  {label}")
    else:
        print(f"  FAIL  {label}")
        failures.append(label)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    teams = json.loads((DATA / "teams.json").read_text())["teams"]
    reg = json.loads((DATA / "depth_register.json").read_text())["clubs"]
    ir = json.loads((DATA / "roster_ir_sweep.json").read_text())

    print("1. ROW-SOURCE GATE")
    for c in reg:
        url = c.get("source_url") or ""
        check(bool(re.match(r"^https?://", url)), f"{c['club']}: source URL is http(s) — {url}")
        if c["status"] == "verified_text":
            check((DATA / "raw" / f"{c['club']}.md").exists(), f"{c['club']}: transcript exists")
            check((DATA / "parsed" / f"{c['club']}.json").exists(), f"{c['club']}: parsed artefact exists")
            check(len(c["positions"]) > 0, f"{c['club']}: register has position rows")
        else:
            check(c["status"] == "flagged_image_only", f"{c['club']}: flagged status is image-only")

    print("2. BROKEN-LINK")
    bad_urls = []
    for c in reg:
        url = c.get("source_url") or ""
        if not re.match(r"^https?://[^\s]+$", url):
            bad_urls.append(f"{c['club']}: {url!r}")
    check(not bad_urls, f"all source URLs well-formed ({len(bad_urls)} bad)")

    internal = []
    for html_file in SITE.rglob("*.html"):
        text = html_file.read_text(encoding="utf-8")
        for href in re.findall(r'href="([^"#]+)"', text):
            if href.startswith(("http", "mailto:")):
                continue
            target = (html_file.parent / href).resolve()
            if not target.exists():
                internal.append(f"{html_file.relative_to(ROOT)} -> {href}")
    check(not internal, f"all internal site links resolve ({len(internal)} broken)")

    missing_files = []
    for c in reg:
        if c.get("transcript") and not (ROOT / c["transcript"]).exists():
            missing_files.append(c["transcript"])
        if c.get("parsed") and not (ROOT / c["parsed"]).exists():
            missing_files.append(c["parsed"])
    check(not missing_files, f"referenced transcript/parsed files exist ({len(missing_files)} missing)")

    print("3. NO-LOCALHOST")
    bad = []
    for html_file in SITE.rglob("*.html"):
        text = html_file.read_text(encoding="utf-8")
        if re.search(r"(localhost|127\.0\.0\.1)", text):
            bad.append(str(html_file.relative_to(ROOT)))
    check(not bad, f"no localhost/127.0.0.1 in site HTML ({len(bad)} offending)")

    print("4. DETERMINISM")
    before = {}
    for p in sorted(DATA.rglob("*.json")):
        before[str(p.relative_to(DATA))] = sha(p)
    subprocess.run([sys.executable, str(ENGINE / "parse_depth.py")], check=True, capture_output=True)
    subprocess.run([sys.executable, str(ENGINE / "build_register.py")], check=True, capture_output=True)
    subprocess.run([sys.executable, str(ENGINE / "roster_ir_sweep.py")], check=True, capture_output=True)
    subprocess.run([sys.executable, str(ENGINE / "build_site.py")], check=True, capture_output=True)
    after = {}
    for p in sorted(DATA.rglob("*.json")):
        after[str(p.relative_to(DATA))] = sha(p)
    same = all(before.get(k) == v for k, v in after.items())
    check(same, "re-running engines reproduces byte-identical data artefacts")

    print("5. CONSISTENCY")
    check(len(teams) == 32, f"teams.json has 32 clubs ({len(teams)})")
    check(len(reg) == 32, f"register has 32 clubs ({len(reg)})")
    check(len(ir["clubs"]) == 32, f"roster/IR sweep has 32 clubs ({len(ir['clubs'])})")
    codes_teams = {t["code"] for t in teams}
    codes_reg = {c["club"] for c in reg}
    codes_ir = {c["club"] for c in ir["clubs"]}
    check(codes_teams == codes_reg == codes_ir, "team codes consistent across artefacts")

    # flag evidence must be present in the raw transcripts
    flag_evidence = {
        "LAC": "Place Derwin James Jr. on Injured Reserve",
        "HOU": "no machine-readable text table",
        "BAL": "Jacoby Brissett",
        "NE": "reflects the opinions of the Patriots.com writers",
        "IND": "Colts publish a NEW unofficial depth chart each week",
    }
    for club, ev in flag_evidence.items():
        raw = (DATA / "raw" / f"{club}.md").read_text(encoding="utf-8")
        check(ev in raw, f"{club}: flag evidence present in raw transcript")

    print()
    if failures:
        print(f"VERIFICATION FAILED — {len(failures)} problem(s)")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("VERIFICATION PASSED — all gates green")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
