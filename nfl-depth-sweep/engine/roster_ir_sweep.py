#!/usr/bin/env python3
"""
roster_ir_sweep.py — D4: 32-team roster/IR sweep vs the official reserve list.

Cross-checks the official NFL league reserve list (November 2026, fetched 2026-11-17
from nfl.com/transactions/league/reserve-list/2026/11, transcribed verbatim to
data/raw/_league_reserve_list_2026-11.md) against the per-club depth charts
parsed in D3 (data/parsed/*.json).

Per club, for every Reserve/Injured entry:
- locate the player on that club's depth chart (exact normalized name match);
- if the player is listed at rank1 of any position → STALE-DEPTH FLAG (a starter
  placed on IR who still occupies rank1 on the club's own depth chart);
- replacement depth: the next-rank player at the same position;
- entries with no chart listing are recorded as "not_on_chart".

Names are matched on a normalized form (case-insensitive, suffixes Jr./Sr./II/III
stripped) to avoid false negatives from suffix variance.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
PARSED = DATA / "parsed"
OUT = DATA / "roster_ir_sweep.json"

TEAM_NAME_TO_CODE = {
    "rams": "LAR", "chargers": "LAC", "saints": "NO", "patriots": "NE",
    "browns": "CLE", "colts": "IND", "titans": "TEN", "cowboys": "DAL",
    "packers": "GB", "dolphins": "MIA", "49ers": "SF", "cardinals": "ARI",
    "vikings": "MIN", "bills": "BUF", "falcons": "ATL", "broncos": "DEN",
    "lions": "DET",
}


def norm_name(name: str) -> str:
    n = name.lower()
    n = re.sub(r"\b(jr|sr|ii|iii|iv)\b\.?", "", n)
    n = re.sub(r"[.\s]+", " ", n).strip()
    return n


def parse_reserve_list() -> list:
    text = (RAW / "_league_reserve_list_2026-11.md").read_text(encoding="utf-8")
    entries = []
    for ln in text.splitlines():
        if not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) < 6 or cells[0] in ("From", "---") or set(cells[0]) <= set("-: "):
            continue
        team_name = cells[0]
        code = TEAM_NAME_TO_CODE.get(team_name.lower())
        if code is None:
            raise SystemExit(f"unknown team name in reserve list: {team_name!r}")
        entries.append({"club": code, "date": cells[2], "player": cells[3], "transaction": cells[5]})
    return entries


def chart_lookup(parsed: dict) -> list:
    """Flatten parsed depth into [{section, position, rank, primary, alt}] for matching."""
    flat = []
    for row in parsed.get("rows", []):
        for e in row["depth"]:
            if e["primary"]:
                flat.append({
                    "section": row["section"], "position": row["position"],
                    "rank": e["rank"], "primary": e["primary"], "alt": e.get("alt"),
                })
    return flat


def main() -> int:
    reserve = parse_reserve_list()
    parsed_files = {p.stem: json.loads(p.read_text()) for p in PARSED.glob("*.json")}

    # full 32-team sweep: every club gets a row, even with zero November entries
    all_codes = [t["code"] for t in json.loads((DATA / "teams.json").read_text())["teams"]]
    clubs = []
    total_flags = 0
    for code in all_codes:
        club_entries = [e for e in reserve if e["club"] == code]
        parsed = parsed_files.get(code, {})
        flat = chart_lookup(parsed)
        by_norm = {}
        for item in flat:
            by_norm.setdefault(norm_name(item["primary"]), []).append(item)
            if item.get("alt"):
                by_norm.setdefault(norm_name(item["alt"]), []).append(item)

        starters_on_ir, chart_listings, replacements, not_on_chart = [], [], [], []
        for entry in club_entries:
            matches = by_norm.get(norm_name(entry["player"]), [])
            if not matches:
                not_on_chart.append({"player": entry["player"], "date": entry["date"]})
                continue
            for m in matches:
                chart_listings.append({
                    "player": entry["player"], "section": m["section"],
                    "position": m["position"], "rank": m["rank"],
                })
                if m["rank"] == 1:
                    # starter on IR still holding rank1 on the club's own chart
                    starters_on_ir.append({
                        "player": entry["player"], "position": m["position"],
                        "section": m["section"], "date_on_ir": entry["date"],
                        "evidence": f"{entry['player']} placed Reserve/Injured {entry['date']} yet listed "
                                    f"rank1 {m['position']} on {code} depth chart (captured 2026-11-17)",
                    })
                    total_flags += 1
                # replacement depth: next-rank player at the same position
                position_rows = [r for r in parsed.get("rows", [])
                                 if r["position"] == m["position"] and r["section"] == m["section"]]
                if position_rows:
                    depth = position_rows[0]["depth"]
                    next_rank = [e for e in depth if e["rank"] == m["rank"] + 1 and e["primary"]]
                    if next_rank:
                        replacements.append({
                            "for_player": entry["player"], "position": m["position"],
                            "replacement_rank": next_rank[0]["rank"],
                            "replacement": next_rank[0]["primary"],
                        })

        clubs.append({
            "club": code,
            "reserve_entries": [{"date": e["date"], "player": e["player"], "transaction": e["transaction"]} for e in club_entries],
            "reserve_count": len(club_entries),
            "starters_on_ir": starters_on_ir,
            "stale_depth_flags": starters_on_ir,
            "chart_listings": chart_listings,
            "replacement_depth": replacements,
            "not_on_chart": not_on_chart,
        })

    sweep = {
        "sweep": "32-team roster/IR sweep vs official reserve list",
        "generated_utc": "2026-11-17",
        "reserve_source": {
            "url": "https://www.nfl.com/transactions/league/reserve-list/2026/11",
            "transcript": "data/raw/_league_reserve_list_2026-11.md",
            "scope": "November 2026 Reserve/Injured transactions",
        },
        "depth_source": "nfl-depth-sweep data/parsed/*.json (D3)",
        "summary": {
            "clubs_with_reserve_entries": len(clubs),
            "reserve_entries_total": len(reserve),
            "stale_depth_flags_total": total_flags,
        },
        "clubs": clubs,
    }
    OUT.write_text(json.dumps(sweep, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"roster_ir_sweep written: {len(clubs)} clubs, {len(reserve)} reserve entries, "
          f"{total_flags} stale-depth flags -> {OUT}")
    for c in clubs:
        if c["starters_on_ir"]:
            for f in c["starters_on_ir"]:
                print(f"  FLAG {c['club']}: {f['player']} ({f['position']} rank1) on IR {f['date_on_ir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
