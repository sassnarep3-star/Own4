"""Transcribe the committed session transcripts into dated capture files.

Input : data/captures/<date>/transcript_*.md   (page-fetched, hand-audited against the live page)
Output: data/captures/<date>/*.json            (structured captures + hashes, never hand-edited)
        data/captures/ledger.json              (append-only ledger with a sha256 hash chain)

The transcripts are the evidence; this script is mechanical. Every count it produces is
re-checked against data/drift_expectations.json (pinned BEFORE this capture was taken) by
engine/drift.py, and cross-checked field-by-field against the two peer captures already in
this repository (availability-desk 2026-11-15, nfl-book 2026-11-16).
"""
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (HERE, PRACTICE_VOCAB, GAME_STATUS_VOCAB, canonical_sha256,
                    load, save, sha256_file, sha256_text)

CAP_DATE = "2026-11-16"
CAP_DIR = os.path.join(HERE, "data", "captures", CAP_DATE)

URL_REPORT = "https://www.nfl.com/injuries/league/2026/reg10"
URL_TRANSACTIONS = "https://www.nfl.com/transactions/"
URL_TRANSACTIONS_TRADES = "https://www.nfl.com/transactions/league/trades/2026/11"
URL_TRANSACTIONS_RESERVE = "https://www.nfl.com/transactions/league/reserve-list/2026/11"
URL_DEPTH_GB = "https://www.packers.com/team/depth-chart"

ROW_RE = re.compile(r"^\|(.+)\|\s*$")


def _cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _parse_injury_part(path, state):
    """Parse one transcript part; mutate `state` (rows, sections, fixtures)."""
    fixture = None
    club = None
    club_code = None
    slot_day = None
    slot_kick = None
    slot_net = None
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if line.startswith("#") and line[1:2] == " ":
                continue  # provenance comment header
            if line.startswith("## "):
                body = line[3:].strip()
                if body.startswith("NEWS"):
                    state["in_news"] = True
                    continue
                # "THURSDAY, NOVEMBER 12TH — 8:15 PM EST — Prime Video"
                bits = [b.strip() for b in body.split("—")]
                state["in_news"] = False
                slot_day = bits[0] if bits else ""
                slot_kick = bits[1] if len(bits) > 1 else ""
                slot_net = bits[2] if len(bits) > 2 else ""
                club = None
                continue
            if line.startswith("### "):
                name = line[4:].strip()
                is_continuation = "(continued)" in name
                name = name.replace(" (continued)", "").strip()
                codes = name.split(" at ")
                if len(codes) == 2:
                    fixture = (codes[0].strip(), codes[1].strip())
                    if is_continuation and state["fixtures"] and \
                            state["fixtures"][-1]["as_printed"] == name:
                        pass  # continuation header of the section already recorded
                    else:
                        state["fixtures"].append({
                            "as_printed": name, "first_listed": codes[0].strip(),
                            "second_listed": codes[1].strip(), "day": slot_day,
                            "kickoff": slot_kick, "network": slot_net,
                        })
                state["in_news"] = False
                continue
            if line.startswith("#### "):
                head = line[5:].strip()
                is_cont = "continued" in head
                head = head.replace("— continued", "").strip()
                m = re.search(r"\(([A-Z]{2,3})\)\s*$", head)
                club_code = m.group(1) if m else None
                club = head[: m.start()].strip() if m else head
                if not (is_cont and state["clubs"] and state["clubs"][-1] == club_code):
                    state["clubs"].append(club_code)
                state["in_news"] = False
                continue
            if not line.startswith("|"):
                continue
            cells = _cells(line)
            if state.get("in_news"):
                if len(cells) >= 2 and cells[0] and cells[1].startswith("http"):
                    state["news"].append({"headline": cells[0], "url": cells[1]})
                continue
            if fixture is None or club_code is None:
                continue
            if len(cells) < 6:
                continue
            player, pos, injury, practice, game_status, slug = cells[0], cells[1], cells[2], cells[3], cells[4], cells[5]
            if player == "Player":
                continue
            opp = fixture[1] if club_code == fixture[0] else (fixture[0] if club_code == fixture[1] else "")
            state["rows"].append({
                "team": club_code, "opp": opp, "player": player, "pos": pos,
                "injury": injury, "practice_status": practice,
                "game_status": game_status, "player_slug": slug,
                "club_as_printed": club, "day": slot_day, "kickoff": slot_kick,
                "network": slot_net, "fixture_as_printed": f"{fixture[0]} at {fixture[1]}",
            })


def build_injury_capture():
    state = {"rows": [], "clubs": [], "fixtures": [], "news": [], "in_news": False}
    parts = []
    for part in ("part1", "part2", "part3"):
        p = os.path.join(CAP_DIR, f"transcript_week10_reg10_{part}.md")
        parts.append(p)
        _parse_injury_part(p, state)
    rows = state["rows"]
    # vocabulary + blank checks (audit evidence; drift.py re-checks independently)
    for r in rows:
        if r["practice_status"] and r["practice_status"] not in PRACTICE_VOCAB:
            raise SystemExit(f"transcribe: practice vocabulary violation: {r['practice_status']!r} ({r['player']})")
        if r["game_status"] and r["game_status"] not in GAME_STATUS_VOCAB:
            raise SystemExit(f"transcribe: game-status vocabulary violation: {r['game_status']!r} ({r['player']})")
        if not (r["team"] and r["player"] and r["pos"] and r["practice_status"] and r["player_slug"]):
            raise SystemExit(f"transcribe: required field blank in {r}")
    designations = {}
    for r in rows:
        if r["game_status"]:
            designations[r["game_status"]] = designations.get(r["game_status"], 0) + 1
    practices = {}
    for r in rows:
        practices[r["practice_status"]] = practices.get(r["practice_status"], 0) + 1
    raw_hashes = {os.path.basename(p): sha256_file(p) for p in parts}
    capture = {
        "dataset": "nfl_collector_capture",
        "capture_id": f"LEAGUE-INJURY-W10-REG10-{CAP_DATE}",
        "kind": "league_injury_report",
        "source": {
            "publisher": "NFL Enterprise (nfl.com)",
            "key": "league_injury_report_week_pinned",
            "url": URL_REPORT,
            "also_live_at": "https://www.nfl.com/injuries/",
            "page_title_as_published": "Official NFL Injury Report for Players - Week 10 of the 2026 Season | NFL.com",
            "week": 10, "season": 2026,
            "table_columns_as_published": ["Player", "Position", "Injuries", "Practice Status", "Game Status"],
        },
        "clock": {
            "read_window_start_utc": "2026-11-16T02:35:00Z",
            "read_window_end_utc": "2026-11-16T03:05:00Z",
            "window_evidence": "start = the session's first fetch_page call on the source URL; end = the last "
                               "of the 8 chunk fetches (chunks 1..8 read in order, single pass). The fetch "
                               "tool exposes no per-call clock, so the window is bounded by the claim commit "
                               "and the manifest write, and is recorded as a window, not per-read times.",
            "game_context": "read after all Week 10 Thursday/Sunday games, before the Monday Nov 16 LAC@BAL kickoff",
        },
        "method": {
            "capture_class": "session_fetch_markdown_transcript",
            "how": "all 8 chunks of the page read in one pass with the page-fetch tool; every printed table "
                   "row transcribed in page order; blanks preserved as blanks; club attribution as printed "
                   "by the page; chunk-boundary rows reconstructed from the two printed halves of the row",
            "chunk_count": 8,
            "transcript_sha256": raw_hashes,
            "limitation": "the sha256 hashes above seal the committed transcript, not the page's raw HTML "
                          "bytes; byte-level HTTP capture with header clocks begins with the CI collector",
        },
        "rows": rows,
        "counts": {
            "rows_total": len(rows),
            "club_sections": len([c for c in state["clubs"] if c]),
            "game_sections": len(state["fixtures"]),
            "game_status_counts": designations,
            "practice_status_counts": practices,
        },
        "news_context": state["news"],
    }
    save(f"data/captures/{CAP_DATE}/league_injury_report_week10.json", capture)
    return capture


def build_transactions_capture():
    path = os.path.join(CAP_DIR, "transcript_transactions_2026-11.md")
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            if not raw.startswith("|"):
                continue
            cells = [c.strip() for c in raw.strip().strip("|").split("|")]
            if len(cells) < 7 or cells[0] in ("From", ""):
                continue
            frm, to, date, name, pos, txn, slug = cells[:7]
            rows.append({"from": frm, "to": to, "date_as_printed": date, "player": name,
                         "position": pos, "transaction": txn, "player_slug": slug})
    capture = {
        "dataset": "nfl_collector_capture",
        "capture_id": f"LEAGUE-TRANSACTIONS-TRADES-2026-11-{CAP_DATE}",
        "kind": "league_transactions_trades_month",
        "source": {
            "publisher": "NFL Enterprise (nfl.com)",
            "key": "league_transactions_month",
            "url": URL_TRANSACTIONS_TRADES,
            "hub_url": URL_TRANSACTIONS,
            "page_title_as_published": "2026 NFL League Transactions - Trades Waivers, Signings & more.",
            "table_columns_as_published": ["From", "To", "Date", "Name", "Position", "Transaction"],
        },
        "clock": {
            "read_window_start_utc": "2026-11-16T02:35:00Z",
            "read_window_end_utc": "2026-11-16T03:05:00Z",
            "window_evidence": "same single-pass read window as the injury capture (page fetched once, "
                               "no pagination); bounded window, not per-read clocks",
        },
        "method": {
            "capture_class": "session_fetch_markdown_transcript",
            "how": "the trades category view for 2026-11 read in full (single page, no pagination); the "
                   "Position column is blank on every row as printed and is preserved blank",
            "chunk_count": 1,
            "transcript_sha256": {"transcript_transactions_2026-11.md": sha256_file(path)},
        },
        "rows": rows,
        "counts": {"rows_total": len(rows)},
    }
    save(f"data/captures/{CAP_DATE}/league_transactions_trades_2026-11.json", capture)
    return capture


def build_depth_capture():
    path = os.path.join(CAP_DIR, "transcript_club_depth_GB.md")
    rows = []
    unit = None
    status_line = None
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if line.startswith("## "):
                body = line[3:].strip()
                unit = body if body.isupper() else unit
                continue
            if line.startswith("Unofficial"):
                status_line = line.strip()
                continue
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 4 or cells[0] == "Position":
                continue
            pos, slots = cells[0], cells[1:4]
            for slot_index, cell in enumerate(slots, start=1):
                empty = (cell == "")
                m = re.match(r"^(\d{1,2})\s+(.+)$", cell) if cell else None
                rows.append({
                    "club": "GB", "unit": unit, "position": pos, "slot": slot_index,
                    "raw_cell": cell, "jersey_number": m.group(1) if m else "",
                    "player": m.group(2).strip() if m else "",
                    "empty_slot": empty,
                })
    capture = {
        "dataset": "nfl_collector_capture",
        "capture_id": f"CLUB-DEPTH-GB-{CAP_DATE}",
        "kind": "club_depth_chart",
        "source": {
            "publisher": "Green Bay Packers (packers.com — official club site)",
            "key": "club_depth_gb",
            "url": URL_DEPTH_GB,
            "page_title_as_published": "Packers Depth Chart | Green Bay Packers – packers.com",
            "page_status_line_as_printed": status_line,
            "club_self_label": "UNOFFICIAL, dated Nov. 10, 2026 by the club itself — the collector never "
                               "upgrades 'on an official club site' to 'an official depth designation'",
            "table_columns_as_published": ["Position", "Player", "Player", "Player"],
        },
        "clock": {
            "read_window_start_utc": "2026-11-16T02:35:00Z",
            "read_window_end_utc": "2026-11-16T03:05:00Z",
            "window_evidence": "same single-pass read window as the other captures (page fetched once)",
        },
        "method": {
            "capture_class": "session_fetch_markdown_transcript",
            "how": "single page, no pagination; every cell stored verbatim in raw_cell; jersey numbers "
                   "stripped into jersey_number by the pinned rule (leading digits before the first space) "
                   "and the name into player; empty slots stored as empty slots, never renumbered; the "
                   "offense row that carries a player only in slot 3 is stored exactly so",
            "chunk_count": 1,
            "transcript_sha256": {"transcript_club_depth_GB.md": sha256_file(path)},
        },
        "rows": rows,
        "counts": {
            "rows_total": len(rows),
            "filled_player_cells": sum(1 for r in rows if not r["empty_slot"]),
            "empty_slots": sum(1 for r in rows if r["empty_slot"]),
            "units": sorted({r["unit"] for r in rows if r["unit"]}),
        },
    }
    save(f"data/captures/{CAP_DATE}/club_depth_gb.json", capture)
    return capture


def update_ledger(captures):
    """Append the capture records to the ledger with a sha256 hash chain (idempotent:
    a re-run of the same capture with identical rows is a no-op, never a duplicate)."""
    ledger_path = os.path.join(HERE, "data", "captures", "ledger.json")
    if os.path.exists(ledger_path):
        ledger = load("data/captures/ledger.json")
    else:
        ledger = {"dataset": "nfl_collector_capture_ledger", "entries": [], "chain_head": ""}
    prev = ledger["chain_head"]
    existing_ids = [e["capture_id"] for e in ledger["entries"]]
    appended = 0
    for cap in captures:
        entry = {
            "capture_id": cap["capture_id"],
            "kind": cap["kind"],
            "date": CAP_DATE,
            "source_url": cap["source"]["url"],
            "rows_total": cap["counts"]["rows_total"],
            "rows_sha256": canonical_sha256(cap["rows"]),
            "clock_read_window_utc": cap["clock"]["read_window_start_utc"] + " .. " + cap["clock"]["read_window_end_utc"],
            "capture_class": cap["method"]["capture_class"],
            "prev_entry_sha256": prev,
        }
        entry["entry_sha256"] = canonical_sha256(
            {k: v for k, v in entry.items() if k != "entry_sha256"})
        if entry["capture_id"] in existing_ids:
            continue  # idempotent: identical re-transcription never re-enters the chain
        ledger["entries"].append(entry)
        appended += 1
        prev = sha256_text(prev + entry["entry_sha256"])
    if appended == 0:
        return ledger, 0  # determinism: an idempotent re-run never rewrites the file
    ledger["chain_head"] = prev
    ledger["updated_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    save("data/captures/ledger.json", ledger)
    return ledger, appended


def build_reserve_capture():
    path = os.path.join(CAP_DIR, "transcript_reserve_list_2026-11.md")
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            if not raw.startswith("|"):
                continue
            cells = [c.strip() for c in raw.strip().strip("|").split("|")]
            if len(cells) < 7 or cells[0] in ("From", ""):
                continue
            frm, to, date, name, pos, txn, slug = cells[:7]
            rows.append({"from": frm, "to": to, "date_as_printed": date, "player": name,
                         "position": pos, "transaction": txn, "player_slug": slug})
    if not rows:
        raise SystemExit("transcribe: reserve-list transcript produced no rows")
    capture = {
        "dataset": "nfl_collector_capture",
        "capture_id": f"LEAGUE-TRANSACTIONS-RESERVE-2026-11-{CAP_DATE}",
        "kind": "league_transactions_reserve_list_month",
        "source": {
            "publisher": "NFL Enterprise (nfl.com)",
            "key": "league_transactions_reserve_list",
            "url": URL_TRANSACTIONS_RESERVE,
            "hub_url": URL_TRANSACTIONS,
            "page_title_as_published": "2026 NFL reserve-list by month | NFL.com",
            "table_columns_as_published": ["From", "To", "Date", "Name", "Position", "Transaction"],
        },
        "clock": {
            "read_window_start_utc": "2026-11-16T02:35:00Z",
            "read_window_end_utc": "2026-11-16T03:05:00Z",
            "window_evidence": "same single-pass read window as the other captures (2 chunks, in order)",
        },
        "method": {
            "capture_class": "session_fetch_markdown_transcript",
            "how": "the reserve-list category view for 2026-11 read in full (2 chunks); the rendered "
                   "November table begins at 11/07 — earlier November IR placements (e.g. Lamar "
                   "Jackson, placed on IR per the league's own news article dated Nov 5) are not "
                   "visible in the rendered table; recorded as a coverage limitation, never filled "
                   "from another source",
            "chunk_count": 2,
            "transcript_sha256": {"transcript_reserve_list_2026-11.md": sha256_file(path)},
        },
        "rows": rows,
        "counts": {"rows_total": len(rows)},
    }
    save(f"data/captures/{CAP_DATE}/league_reserve_list_2026-11.json", capture)
    return capture


def main():
    caps = [
        build_injury_capture(),
        build_transactions_capture(),
        build_reserve_capture(),
        build_depth_capture(),
    ]
    ledger, appended = update_ledger(caps)
    print(f"transcribe: injury rows={caps[0]['counts']['rows_total']} "
          f"clubs={caps[0]['counts']['club_sections']} games={caps[0]['counts']['game_sections']}")
    print(f"transcribe: transactions rows={caps[1]['counts']['rows_total']} "
          f"reserve rows={caps[2]['counts']['rows_total']} "
          f"depth rows={caps[3]['counts']['rows_total']} (filled {caps[3]['counts']['filled_player_cells']})")
    print(f"transcribe: ledger entries={len(ledger['entries'])} (appended {appended}) "
          f"chain_head={ledger['chain_head'][:12]}…")


if __name__ == "__main__":
    main()
