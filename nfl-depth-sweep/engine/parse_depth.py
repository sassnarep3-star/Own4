#!/usr/bin/env python3
"""
parse_depth.py — D3 parser for the 32-club depth-chart sweep (session arena/2388d73a-own4).

Reads verbatim raw transcripts from data/raw/*.md and emits structured per-club JSON
to data/parsed/<club>.json.

Handles the two named parsing failures and the observed cross-club variance:

1. Packers jersey-number prepend: GB cells are "N PlayerName" (e.g. "9 Christian Watson").
   The jersey number is captured and stripped from the player name; the raw string is
   preserved in the raw transcript.
2. Texans depth-as-image: HOU has no text table at all. Its file is a flag record; the
   parser emits capture_status="flagged_image_only" and no rows (never infers).

Cross-club variance handled:
- Heading variants: "## Offense" / "#### **OFFENSE**" (case-insensitive, asterisks tolerated).
- Shared rank slots: a cell with two names, e.g. "[Cooper Kupp](url) [Rashid Shaheed](url)"
  or "[Zaven Collins](url) [Baron Browning](url)" → primary + alt (VR-21).
- Sparse/blank cells: empty cell → no player at that rank (never invented).
- Blank position cells: a row like "|  |  |  | 26 Kaleb Johnson |" inherits the position
  of the previous row in the same section (GB RB 4th string).
- Player-link format: "[Name](url)" → Name; multi-link cells → shared slot.
- Plain-text names (no link, no jersey number) → used as-is.
- Table header/separator rows are skipped.

Output rows: one entry per (section, position, rank) with primary/alt/jersey.
Every output cell traces to the raw transcript — the parser only reformats, never infers.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PARSED_DIR = ROOT / "data" / "parsed"

# --- regexes -------------------------------------------------------------------
SECTION_RE = re.compile(r"^#{2,6}\s*\**\s*(OFFENSE|DEFENSE|SPECIAL\s*TEAMS)\**\s*$", re.IGNORECASE)
LINK_RE = re.compile(r"\[(.+?)\]\((.+?)\)")
JERSEY_RE = re.compile(r"^(\d{1,2})\s+(.+)$")
BLANK_RE = re.compile(r"^[\s\-—:|]+$")


def section_key(name: str) -> str:
    n = name.upper().replace(" ", "_")
    if n == "OFFENSE":
        return "offense"
    if n == "DEFENSE":
        return "defense"
    if n == "SPECIAL_TEAMS":
        return "special_teams"
    raise ValueError(f"unknown section {name!r}")


def parse_player_cell(cell: str):
    """Parse one table cell into (primary, alt, jersey) or None if blank."""
    cell = cell.strip()
    if not cell:
        return None

    links = LINK_RE.findall(cell)
    if links:
        names = [ln for ln, _ in links]
        if len(names) == 1:
            return {"primary": names[0], "alt": None, "jersey": None}
        if len(names) == 2:
            # shared rank slot: two players occupy one rank (VR-21)
            return {"primary": names[0], "alt": names[1], "jersey": None}
        raise ValueError(f"cell with {len(names)} links not supported: {cell!r}")

    # no markdown link — plain text (GB jersey-prepend or bare name)
    m = JERSEY_RE.match(cell)
    if m:
        return {"primary": m.group(2).strip(), "alt": None, "jersey": m.group(1)}
    return {"primary": cell, "alt": None, "jersey": None}


def parse_transcript(path: Path):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # --- header metadata -----------------------------------------------------
    meta = {"source_url": None, "fetched_utc": None, "note": None}
    for ln in lines:
        if ln.startswith("# source_url:"):
            # take the first http(s) URL only (header may carry parenthetical notes)
            m = re.search(r"https?://[^\s)]+", ln)
            meta["source_url"] = m.group(0) if m else None
        elif ln.startswith("# fetched_utc:"):
            meta["fetched_utc"] = ln.split(":", 1)[1].strip()

    club = path.stem

    # --- flag files (image-only etc.) have no tables ----------------------
    if "STATUS: UNVERIFIED" in text or "no machine-readable text table" in text:
        return {
            "club": club,
            "capture_status": "flagged_image_only",
            "source_url": meta["source_url"],
            "fetched_utc": meta["fetched_utc"],
            "rows": [],
            "parse_warnings": ["depth chart published as image; no text surface — no rows parsed"],
        }

    # --- section split -------------------------------------------------------
    sections = {}  # section_key -> list of row dicts
    current = None
    warnings = []
    last_position = {}  # section_key -> last seen position (for blank-position rows)

    for ln in lines:
        m = SECTION_RE.match(ln)
        if m:
            current = section_key(m.group(1))
            sections.setdefault(current, [])
            last_position[current] = None
            continue
        if not ln.startswith("|"):
            continue
        if current is None:
            continue

        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        # skip header row (Position / Player...) and separator rows
        if BLANK_RE.match(ln) or cells[0].lower() == "position" or all(
            BLANK_RE.match(c) for c in cells
        ):
            continue

        position = cells[0]
        inherited = False
        if not position:
            # wrapped/continuation row (e.g. GB RB 4th string): inherit the previous
            # row's position in this section, then merge its entries into that row.
            if last_position.get(current):
                position = last_position[current]
                inherited = True
            else:
                warnings.append(f"{current}: blank position with no predecessor — skipped")
                continue
        last_position[current] = position

        # entries keyed by TRUE column index (rank = position in the raw table row,
        # not the enumeration of non-empty cells — wrapped rows have leading blanks)
        entries = {}
        for col_idx, cell in enumerate(cells[1:], start=1):
            entry = parse_player_cell(cell)
            if entry is not None:
                entries[col_idx] = entry

        row = {"section": current, "position": position, "depth": []}
        if inherited:
            # merge into the previous row with the same section+position (keep existing
            # entries at their ranks; blank columns in the continuation carry no data)
            target = None
            for prev in reversed(sections.get(current, [])):
                if prev["position"] == position:
                    target = prev
                    break
            if target is None:
                warnings.append(f"{current}: continuation row for {position!r} with no target — kept as new row")
                sections[current].append(row)
            else:
                existing = {e["rank"] for e in target["depth"]}
                for rank in sorted(entries):
                    entry = entries[rank]
                    if rank in existing:
                        # wrapped rows drop trailing empty columns, so a continuation
                        # entry can collide with an earlier rank. It belongs at the
                        # next free rank (the row wraps, it does not duplicate).
                        new_rank = max(existing) + 1
                        warnings.append(
                            f"{current}: rank {rank} collision while merging {position!r} — "
                            f"placed {entry['primary']!r} at free rank {new_rank}"
                        )
                        rank = new_rank
                    target["depth"].append({"rank": rank, **entry})
                    existing.add(rank)
                continue
        for rank in sorted(entries):
            row["depth"].append({"rank": rank, **entries[rank]})
        sections[current].append(row)

    rows = [row for rows_list in sections.values() for row in rows_list]

    # --- validation ----------------------------------------------------------
    for sec in ("offense", "defense"):
        if sec not in sections:
            warnings.append(f"missing {sec} section in transcript")

    return {
        "club": club,
        "capture_status": "verified_text",
        "source_url": meta["source_url"],
        "fetched_utc": meta["fetched_utc"],
        "sections": sections,
        "rows": rows,
        "parse_warnings": warnings,
    }


def main() -> int:
    PARSED_DIR.mkdir(parents=True, exist_ok=True)
    raw_files = sorted(RAW_DIR.glob("*.md"))
    if not raw_files:
        print("no raw transcripts found", file=sys.stderr)
        return 1
    # league-level files (e.g. the reserve-list transcript) start with "_";
    # they are not per-club transcripts
    raw_files = [p for p in raw_files if not p.stem.startswith("_")]

    summary = []
    for path in raw_files:
        result = parse_transcript(path)
        out = PARSED_DIR / f"{result['club']}.json"
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        n_rows = len(result.get("rows", []))
        summary.append((result["club"], result["capture_status"], n_rows, len(result.get("parse_warnings", []))))

    print(f"{'club':5} {'status':20} {'rows':>5} {'warn':>4}")
    for club, status, n_rows, n_warn in summary:
        print(f"{club:5} {status:20} {n_rows:>5} {n_warn:>4}")
    print(f"\nparsed {len(summary)} transcripts -> {PARSED_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
