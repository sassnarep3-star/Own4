#!/usr/bin/env python3
"""nfl-depth-sweep verify — fails non-zero if any published claim disagrees with the data.

Gates
  G1 data shape        32 rows in each route file; abbr sets identical to teams_base
  G2 sources           every row carries an https source_url on an official page read
  G3 route semantics   route L all 404; route C all present; 31 tables + 1 image
  G4 aggregates        every headline number on index/findings recomputes from the JSON
  G5 blanks            HOU (image) slot fields are null and rendered blank, never guessed
  G6 links             every internal href resolves; no localhost; every sweep row sourced
  G7 flags             DS-01..DS-13 present, each with a source link
  G8 determinism       rebuild is byte-identical
"""
import json
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
FAILS = []


def fail(msg):
    FAILS.append(msg)
    print(f"FAIL  {msg}")


def ok(msg):
    print(f"ok    {msg}")


def load(name):
    with open(ROOT / "data" / name, encoding="utf-8") as fh:
        return json.load(fh)


def main():
    teams = load("teams_base.json")
    rl = load("route_l.json")
    rc = load("route_c.json")

    # G1 data shape
    t_abbr = [r["abbr"] for r in teams["rows"]]
    l_abbr = [r["abbr"] for r in rl["rows"]]
    c_abbr = [r["abbr"] for r in rc["rows"]]
    if len(t_abbr) != 32 or len(set(t_abbr)) != 32:
        fail("teams_base must hold 32 unique clubs")
    if sorted(t_abbr) != sorted(l_abbr) or sorted(t_abbr) != sorted(c_abbr):
        fail("abbr sets differ between teams_base, route_l and route_c")
    else:
        ok("G1  32 unique clubs, abbr sets identical across all three data files")

    # G2 sources
    for r in rl["rows"]:
        if not (r.get("source_url", "").startswith("https://") and r.get("source_url") == r["url"]):
            fail(f"route_l {r['abbr']} missing/odd source_url")
    for r in rc["rows"]:
        if not (r.get("source_url", "").startswith("https://") and r["source_url"] == r["route_c_url"]):
            fail(f"route_c {r['abbr']} missing/odd source_url")
        if r["route_c_result"] == "present" and not r["heading"]:
            fail(f"route_c {r['abbr']} present but heading blank")
    if not FAILS:
        ok("G2  every row carries its own https source link")

    # G3 route semantics
    if not all(r["result"] == "404" for r in rl["rows"]) or len(rl["rows"]) != 32:
        fail("route L must be 32 rows, all 404")
    if not all(p["result"] == "404" for p in rl.get("extra_probes", [])):
        fail("extra league-wide probe must be recorded as 404")
    if not all(r["route_c_result"] == "present" for r in rc["rows"]):
        fail("route C must be 32/32 present")
    tables = sum(1 for r in rc["rows"] if r["structure"] == "html-table")
    images = sum(1 for r in rc["rows"] if r["structure"].startswith("image"))
    if (tables, images) != (31, 1):
        fail(f"expected 31 html-table + 1 image, got {tables}+{images}")
    if images and [r["abbr"] for r in rc["rows"] if r["structure"].startswith("image")] != ["HOU"]:
        fail("the only image-only club must be HOU")
    if not FAILS:
        ok("G3  route L 32×404 (+league-wide); route C 32 present = 31 tables + HOU image")

    # G4 aggregates recomputed from data and required on the pages
    idx = (ROOT / "index.html").read_text(encoding="utf-8")
    fnd = (ROOT / "pages" / "findings.html").read_text(encoding="utf-8")
    swp = (ROOT / "pages" / "sweep.html").read_text(encoding="utf-8")
    dated = [r for r in rc["rows"] if r["as_of"]]
    shared = [r for r in rc["rows"] if (r["shared_rank1_n"] or 0) > 0]
    empty = [r for r in rc["rows"] if (r["empty_rank1_n"] or 0) > 0]
    shared_slots = sum(r["shared_rank1_n"] or 0 for r in rc["rows"])
    empty_slots = sum(r["empty_rank1_n"] or 0 for r in rc["rows"])
    slots = sum((r["off_n"] or 0) + (r["def_n"] or 0) + (r["st_n"] or 0) for r in rc["rows"])
    unofficial = sum(1 for r in rc["rows"] if r["unofficial"] == "yes")
    from datetime import date
    built = date.fromisoformat(rc["built_utc"])
    checks = [
        ("32/32 league 404 card", "32/32" in idx),
        ("32/32 club present card", idx.count("32/32") >= 2),
        ("31 tables card", ">31</div>" in idx or ">31<" in idx),
        ("shared slots on index", f">{shared_slots}</div>" in idx),
        ("empty slots on index", f">{empty_slots}</div>" in idx),
        ("dated count on index", f">{len(dated)}/32<" in idx),
        ("unofficial count on index", f">{unofficial}</div>" in idx),
        ("total slots on findings", f"<b>{slots}</b>" in fnd),
        ("shared slots on findings", f"only {len(dated)} of 32" in fnd or f"{len(dated)} of 32" in fnd),
        ("shared table rows on findings", all(f"<td>{r['shared_rank1_n']}</td>" in fnd for r in shared)),
        ("empty table rows on findings", all(f"<td>{r['empty_rank1_n']}</td>" in fnd for r in empty)),
    ]
    # chart ages rendered in sweep must equal computed ages
    for r in dated:
        age = (built - date.fromisoformat(r["as_of"])).days
        checks.append((f"age {r['abbr']}={age}d in sweep", f"({age}d before build)" in swp))
    bad = [n for n, c in checks if not c]
    for n in bad:
        fail(f"G4 aggregate not found or wrong: {n}")
    if not bad:
        ok(f"G4  {len(checks)} aggregate checks recomputed from JSON and matched on the pages")

    # G5 blanks for the image-only club
    hou = next(r for r in rc["rows"] if r["abbr"] == "HOU")
    if any(hou[k] is not None for k in ("off_n", "def_n", "st_n", "shared_rank1_n", "empty_rank1_n")):
        fail("HOU image-only row must keep numeric fields null (blank, never guessed)")
    hou_row = next(line for line in swp.split("</tr>") if "<b>HOU</b>" in line)
    if "—" not in hou_row:
        fail("HOU row in sweep must render blanks (—), not numbers")
    else:
        ok("G5  HOU image-only fields are null in data and rendered blank on the page")

    # G6 links
    pages = [ROOT / "index.html"] + sorted((ROOT / "pages").glob("*.html"))
    n_links = 0
    for p in pages:
        text = p.read_text(encoding="utf-8")
        if "localhost" in text or "127.0.0.1" in text:
            fail(f"{p.name} references localhost")
        for href in re.findall(r'href="([^"]+)"', text):
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            n_links += 1
            target = (p.parent / href.split("#")[0]).resolve()
            if not target.exists():
                fail(f"broken internal link in {p.name}: {href}")
    # every sweep row must carry a source anchor (ignore the trailing fragment after the last row)
    data_rows = [c for c in swp.split("</tr>") if "<td>" in c]
    unsourced = [i for i, row in enumerate(data_rows) if "<a class=\"src\"" not in row and "<a class='src'" not in row]
    if len(data_rows) < 32:
        fail(f"sweep table has only {len(data_rows)} data rows")
    if unsourced:
        fail(f"sweep rows without a source link: {unsourced[:5]}")
    if not FAILS:
        ok(f"G6  {n_links} internal links resolve; all {len(data_rows)} sweep rows carry a source link")

    # G7 flags
    flg = (ROOT / "pages" / "flagged.html").read_text(encoding="utf-8")
    ids = re.findall(r"<b>(DS-\d+)</b>", flg)
    expected = [f"DS-{i:02d}" for i in range(1, 14)]
    if sorted(set(ids)) != expected:
        fail(f"flagged page ids {sorted(set(ids))} != {expected}")
    unsourced_flags = [row for row in flg.split("</tr>") if "<b>DS-" in row and "href=" not in row]
    if unsourced_flags:
        fail("a flag row has no source link")
    if not FAILS:
        ok("G7  DS-01..DS-13 published, each with a source link")

    # G8 determinism: rebuild into a temp copy and compare bytes
    with tempfile.TemporaryDirectory() as td:
        tdp = pathlib.Path(td)
        subprocess.run(["cp", "-r", str(ROOT), str(tdp / "ns")], check=True)
        subprocess.run([sys.executable, str(tdp / "ns" / "engine" / "build.py")],
                       check=True, capture_output=True)
        diffs = []
        for p in pages:
            rel = p.relative_to(ROOT)
            if (tdp / "ns" / rel).read_bytes() != p.read_bytes():
                diffs.append(str(rel))
        if diffs:
            fail(f"rebuild not byte-identical: {diffs}")
        else:
            ok("G8  rebuild is byte-identical (deterministic)")

    print()
    if FAILS:
        print(f"VERIFY FAIL — {len(FAILS)} problem(s)")
        sys.exit(1)
    print("VERIFY PASS — all gates green")


if __name__ == "__main__":
    main()
