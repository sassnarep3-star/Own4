#!/usr/bin/env python3
"""
build_register.py — D3 register builder for the 32-club depth-chart sweep.

Computes nfl-depth-sweep/data/depth_register.json from the checked-in parsed
artefacts (data/parsed/*.json), which themselves derive verbatim from
data/raw/*.md. Nothing here is inferred: every cell comes from the raw
transcripts, and every flag is asserted against the raw text it cites.

Register shape (per brief + claim D3): one row per (club, position) with
position / rank1 / rank2 / rank3, plus per-club date + source + status.

Rank 4+ entries (e.g. GB RB 4th string, NE LT 3rd string, DEN S 3rd string)
are preserved in data/parsed/*.json and reported as a deep_depth count here;
the register cells are rank1–rank3 as specified.

Snapshot dates: taken from each page's own dated statement when present
(GB "Unofficial, Nov. 10, 2026", CHI "As of 10/31/2026", TEN "as of 11/10/26",
LV "as of November 10, 2026", SF "Updated as of 11/10/26"); otherwise the
capture date (2026-11-17) is used and marked chart_date_unstated.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
PARSED = DATA / "parsed"
RAW = DATA / "raw"
OUT = DATA / "depth_register.json"

CAPTURE_DATE = "2026-11-17"

# --- per-club curated flags (each evidence string is asserted against the raw
#     transcript; if the string is not found the build fails loudly) ----------
FLAGS = {
    "LAC": [
        {
            "flag": "stale_depth",
            "detail": "Derwin James Jr. listed S rank1 while page's own Latest Transactions "
                      "places him on Injured Reserve",
            "evidence": "Place Derwin James Jr. on Injured Reserve",
        }
    ],
    "HOU": [
        {
            "flag": "image_only",
            "detail": "depth chart published as image; no machine-readable text surface",
            "evidence": "no machine-readable text table",
        }
    ],
    "BAL": [
        {
            "flag": "snapshot_note",
            "detail": "2026-11-17 snapshot: QB row lists Jacoby Brissett (1); Lamar Jackson "
                      "(the brief's stale-depth case) does not appear in this capture",
            "evidence": "Jacoby Brissett",
        }
    ],
    "NE": [
        {
            "flag": "writer_opinion",
            "detail": "chart is published by Patriots.com writers and explicitly disclaimed as "
                      "not reflecting the organization",
            "evidence": "reflects the opinions of the Patriots.com writers",
        }
    ],
    "IND": [
        {
            "flag": "weekly_snapshot",
            "detail": "Colts publish a new unofficial depth chart each week",
            "evidence": "Colts publish a NEW unofficial depth chart each week",
        }
    ],
}

# --- snapshot-date statements observed on the pages ---------------------------
DATE_PATTERNS = [
    (re.compile(r"Unofficial,\s*(\w+\.?\s*\d{1,2},\s*20\d{2})", re.IGNORECASE), "%b %d, %Y"),
    (re.compile(r"As of\s+(\d{1,2}/\d{1,2}/20\d{2})", re.IGNORECASE), "%m/%d/%Y"),
    (re.compile(r"as of\s+(\d{1,2}/\d{1,2}/\d{2})", re.IGNORECASE), "%m/%d/%y"),
    (re.compile(r"as of\s+(November\s+\d{1,2},\s*20\d{2})", re.IGNORECASE), "%B %d, %Y"),
    (re.compile(r"Updated as of\s+(\d{1,2}/\d{1,2}/\d{2})", re.IGNORECASE), "%m/%d/%y"),
]


def norm_date(text: str) -> str:
    from datetime import datetime

    for pattern, fmt in DATE_PATTERNS:
        m = pattern.search(text)
        if m:
            raw = m.group(1)
            # normalize "Nov." / "Sept." style month abbreviations (trailing dot)
            raw = re.sub(r"\b(Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.", r"\1", raw)
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
    return None


def build_club(club: str, parsed: dict, teams: dict) -> dict:
    raw_path = RAW / f"{club}.md"
    raw_text = raw_path.read_text(encoding="utf-8")
    domain = teams[club]["domain"]
    status = teams[club]["status"]

    snapshot = norm_date(raw_text)
    snapshot_note = None
    if snapshot:
        snapshot_note = "page-stated chart date"
    else:
        snapshot = CAPTURE_DATE
        snapshot_note = "chart date not stated on page; capture date used"

    # assert curated flag evidence exists in the raw transcript
    flags = []
    for fl in FLAGS.get(club, []):
        if fl["evidence"] not in raw_text:
            raise SystemExit(f"FLAG EVIDENCE MISSING for {club}: {fl['evidence']!r}")
        flags.append({"flag": fl["flag"], "detail": fl["detail"]})

    if status == "flagged_image_only":
        return {
            "club": club,
            "domain": domain,
            "source_url": parsed.get("source_url"),
            "fetched_utc": CAPTURE_DATE,
            "snapshot_date": snapshot,
            "snapshot_date_note": snapshot_note,
            "status": "flagged_image_only",
            "transcript": f"data/raw/{club}.md",
            "parsed": None,
            "positions": [],
            "deep_depth_entries": 0,
            "flags": flags,
        }

    positions = []
    deep_count = 0
    for row in parsed["rows"]:
        if row["section"] not in ("offense", "defense"):
            continue  # special teams rows are not position depth rows
        cell_ranks = []
        by_rank = {e["rank"]: e for e in row["depth"]}
        for rank in (1, 2, 3):
            e = by_rank.get(rank)
            if e is None or e["primary"] is None:
                cell_ranks.append(None)
            else:
                cell = {"name": e["primary"]}
                if e.get("jersey"):
                    cell["jersey"] = e["jersey"]
                if e.get("alt"):
                    cell["alt"] = e["alt"]
                cell_ranks.append(cell)
        positions.append({"position": row["position"], "rank1": cell_ranks[0], "rank2": cell_ranks[1], "rank3": cell_ranks[2]})
        deep_count += sum(1 for e in row["depth"] if e["rank"] > 3 and e["primary"])

    return {
        "club": club,
        "domain": domain,
        "source_url": parsed.get("source_url"),
        "fetched_utc": parsed.get("fetched_utc") or CAPTURE_DATE,
        "snapshot_date": snapshot,
        "snapshot_date_note": snapshot_note,
        "status": "verified_text",
        "transcript": f"data/raw/{club}.md",
        "parsed": f"data/parsed/{club}.json",
        "positions": positions,
        "deep_depth_entries": deep_count,
        "flags": flags,
    }


def main() -> int:
    teams = {t["code"]: t for t in json.loads((DATA / "teams.json").read_text())["teams"]}
    clubs = []
    for path in sorted(PARSED.glob("*.json")):
        club = path.stem
        if club not in teams:
            print(f"skipping non-club parsed artefact: {path.name}", file=sys.stderr)
            continue
        parsed = json.loads(path.read_text())
        clubs.append(build_club(club, parsed, teams))

    register = {
        "register": "nfl-depth-sweep official depth-chart register",
        "generated_utc": CAPTURE_DATE,
        "source_policy": "Official NFL club websites, /team/depth-chart route verified club by club (2026-11-17 sweep). "
                         "Every cell transcribed verbatim from a transcript fetched in this session; "
                         "no depth order inferred. Unconfirmable cells are null + flagged.",
        "columns": ["club", "position", "rank1", "rank2", "rank3", "snapshot_date", "source_url", "status"],
        "clubs": clubs,
    }
    OUT.write_text(json.dumps(register, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    n_text = sum(1 for c in clubs if c["status"] == "verified_text")
    n_flag = sum(1 for c in clubs if c["status"] == "flagged_image_only")
    n_pos = sum(len(c["positions"]) for c in clubs)
    print(f"register written: {len(clubs)} clubs ({n_text} verified_text, {n_flag} flagged_image_only), {n_pos} position rows")
    print(f"-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
