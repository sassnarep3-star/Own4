"""Pre-registration ledger: freeze rule files by sha256; fail CI if a frozen rule is edited.

  --freeze PREREG-002   record the hash of prereg/PREREG-002-*.md plus the frozen peer-engine
                        hashes into data/prereg.json (registration)
  --check               every registered file's current hash must equal the frozen hash;
                        the evaluator's own hash must match too (refusal condition (b))
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HERE, REPO, load, save

FROZEN_PEER_FILES = [
    "nfl-book/engine/model.py",
    "nfl-book/engine/backtest.py",
    "nfl-book/engine/common.py",
]
EVALUATOR = "nfl-collector/engine/eval_mcnemar.py"


def _sha(path):
    full = path if os.path.isabs(path) else os.path.join(REPO, path)
    h = hashlib.sha256()
    with open(full, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def freeze(rule_id):
    matches = [f for f in os.listdir(os.path.join(HERE, "prereg")) if f.startswith(rule_id)]
    if len(matches) != 1:
        raise SystemExit(f"preregister: expected exactly one file for {rule_id}, found {matches}")
    fname = matches[0]
    rel = f"nfl-collector/prereg/{fname}"
    entry = {
        "rule_id": rule_id,
        "file": rel,
        "file_sha256": _sha(rel),
        "registered_utc": "2026-11-16",
        "registered_by": "arena/013190b4-own4",
        "registration_note": "the sha256 of the rule file is the registration; any edit fails "
                             "--check in CI. Peer-engine hashes below are frozen at the same "
                             "moment; the evaluator refuses to run if they change.",
        "frozen_peer_files": {p: _sha(p) for p in FROZEN_PEER_FILES},
        "frozen_evaluator_sha256": _sha(EVALUATOR),
        "data_state_at_registration": {
            "results_feed": "nfl-book/data/results_feed.json",
            "weeks_present": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "week11_games_present": 0,
            "assertion": "no Week 11 result existed in this repository at registration",
        },
    }
    prereg_path = os.path.join(HERE, "data", "prereg.json")
    if os.path.exists(prereg_path):
        reg = json.load(open(prereg_path))
    else:
        reg = {"dataset": "nfl_collector_prereg_ledger", "registered": {}}
    reg["registered"][rule_id] = entry
    save("data/prereg.json", reg)
    print(f"preregister: {rule_id} frozen — file sha256 {entry['file_sha256'][:16]}… "
          f"({len(entry['frozen_peer_files'])} peer files + evaluator hash recorded)")


def check():
    reg = load("data/prereg.json")
    failures = []
    for rule_id, entry in reg["registered"].items():
        cur = _sha(entry["file"])
        if cur != entry["file_sha256"]:
            failures.append(f"{rule_id}: rule file edited after registration "
                            f"({entry['file_sha256'][:12]}… -> {cur[:12]}…)")
        for p, h in entry["frozen_peer_files"].items():
            cur_p = _sha(p)
            if cur_p != h:
                failures.append(f"{rule_id}: frozen peer file changed: {p}")
        if _sha(EVALUATOR) != entry["frozen_evaluator_sha256"]:
            failures.append(f"{rule_id}: evaluator edited after registration: {EVALUATOR}")
    if failures:
        print("preregister: FAIL — a frozen rule or its frozen implementation changed:")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print(f"preregister: PASS — {len(reg['registered'])} registered rule(s) intact")


if __name__ == "__main__":
    ap = sys.argv[1:] if len(sys.argv) > 1 else []
    if ap and ap[0] == "--freeze":
        freeze(ap[1])
    elif ap and ap[0] == "--check":
        check()
    else:
        raise SystemExit("usage: preregister.py --freeze PREREG-002 | --check")
