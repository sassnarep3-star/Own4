"""Shared helpers for the nfl-collector namespace (stdlib only, deterministic).

Conventions held by every engine in this namespace:
  * JSON is written with sorted keys and fixed separators so rebuilds are byte-identical.
  * A value that cannot be confirmed from an official source is written blank, never inferred.
  * Raw NFL HTML is never committed: captures store structured rows, transcript hashes and
    timestamps only (flag RF-18 on the flagged page stays open for the owner).
"""
import hashlib
import json
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # namespace root
REPO = os.path.dirname(HERE)  # repository root


def load(path):
    with open(os.path.join(HERE, path), "r", encoding="utf-8") as fh:
        return json.load(fh)


def save(path, obj):
    full = os.path.join(HERE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True)
        fh.write("\n")
    return full


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_sha256(obj):
    """sha256 of the canonical JSON rendering used by the ledger hash chain."""
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


PRACTICE_VOCAB = {
    "Did Not Participate In Practice",
    "Limited Participation in Practice",
    "Full Participation in Practice",
}
GAME_STATUS_VOCAB = {"Doubtful", "Out", "Questionable", "Probable"}
