"""S7 — provenance: hash every input and every output, and record which official page each came from.

Run this LAST, after every other builder, so the hashes describe what is actually on disk.
"""
import glob
import os

from common import ROOT, DATA, REGISTERED_UTC, sha256_file, write_json

INPUTS = [
    ("raw/week%d.txt" % w, "https://www.nfl.com/schedules/2026/by-week/week-%d" % w)
    for w in range(1, 11)
] + [
    ("raw/week11.txt", "https://www.nfl.com/schedules/2026/by-week/week-11"),
    ("raw/standings.txt", "https://www.nfl.com/standings/league/2026/REG"),
    ("raw/byes.txt", "https://www.nfl.com/schedules/2026/by-week/week-5 (and the week pages for 6-10)"),
    ("raw/venues11.txt", "13 official Week 11 game-centre pages (Game Info block); one URL per row"),
]


def main():
    inputs = {}
    for rel, src in INPUTS:
        p = os.path.join(ROOT, rel)
        lines = sum(1 for line in open(p, encoding="utf-8")
                    if line.strip() and not line.startswith("#"))
        inputs[rel] = {"sha256": sha256_file(p), "bytes": os.path.getsize(p), "data_lines": lines,
                       "official_source": src}
    outputs = {}
    for p in sorted(glob.glob(os.path.join(DATA, "*.json"))):
        # provenance.json cannot hash itself, and verification.json is the GATE'S OWN OUTPUT: it is
        # written after this file every run, so hashing it would make every build dirty by one run.
        if os.path.basename(p) in ("provenance.json", "verification.json"):
            continue
        outputs["data/" + os.path.basename(p)] = {
            "sha256": sha256_file(p), "bytes": os.path.getsize(p)}
    write_json(os.path.join(DATA, "provenance.json"), {
        "dataset": "nfl_sources_provenance",
        "title": "Every input and output, hashed, with the official page behind each input",
        "built_utc": REGISTERED_UTC,
        "registration_commit": "a4f26f5",
        "excluded_from_outputs": ["verification.json (the gate's own record, written after this file)"],
        "how_to_recheck": ("python3 nfl-sources/engine/verify.py  -> check C3 recomputes every input hash. "
                           "A transcription edited by hand after this file was written fails the build."),
        "inputs": inputs, "outputs": outputs,
    })
    print("inputs hashed:", len(inputs), "outputs hashed:", len(outputs))


if __name__ == "__main__":
    main()
