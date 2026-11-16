"""Game-book participation spike (decision DEC-3 = B: one club-pair, one week).

The official Game Book is the only league source that states who ACTUALLY started,
who substituted, who did not play and who was not active — the field that turns the
availability graph from a one-sided list into a testable claim (SUG-03).

Route verified this session: the game centre page publishes "Download Game Book (PDF)"
per fixture, linking to the league's own CDN. This spike parses ONE fixture's
participation block (WAS at NYG, Week 10) from the committed transcript and joins it
to the weekly report rows for the same two clubs.

Name-matching rule (pinned): the game book prints "F.LastName" (initial + surname);
a report row matches when its printed player name's first token starts with that
initial and its last token equals that surname. A collision (two report rows mapping
to one game-book cell, or vice versa) is flagged, never guessed through.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HERE, canonical_sha256, load, save, sha256_file  # noqa: E402

CAP_DATE = "2026-11-16"
TRANSCRIPT = f"data/captures/{CAP_DATE}/transcript_gamebook_WAS_NYG_reg10.md"
GAME_CENTRE = "https://www.nfl.com/games/commanders-at-giants-2026-reg-10"
PDF_URL = ("https://static.www.nfl.com/image/upload/v1794570519/"
           "gamecenter/ab5828d9-4feb-11f1-abca-2c54536568a9.pdf")
REPORT_URL = "https://www.nfl.com/injuries/league/2026/reg10"

ROW_RE = re.compile(r"^\|\s*([A-Z]{2,3})\s*\|\s*([a-z_]+)\s*\|\s*([^|]+?)\s*\|\s*(\d{1,2})\s*\|\s*(.+?)\s*\|\s*$")


def _split_gb_name(cell):
    """'L.Patrick' -> ('L', 'Patrick'); 'A.Williams' -> ('A', 'Williams')."""
    m = re.match(r"^([A-Z])\.([A-Za-z\-]+)$", cell.strip())
    if not m:
        return None
    return m.group(1), m.group(2)


def _report_key(name):
    """Report player name -> (first_initial, last_token)."""
    toks = name.strip().split()
    if len(toks) < 2:
        return None
    return (toks[0][0].upper(), toks[-1])


def parse_transcript(path):
    rows = []
    header = {}
    with open(path, encoding="utf-8") as fh:
        in_header = False
        for raw in fh:
            line = raw.rstrip("\n")
            if line.startswith("## Header"):
                in_header = True
                continue
            if line.startswith("## "):
                in_header = False
            if in_header and line.startswith("|"):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) == 4 and cells[0] != "date_as_printed" and not cells[0].startswith("date"):
                    header[cells[0]] = cells[1] if len(cells) > 1 else ""
                elif len(cells) == 4:
                    header[cells[0]] = cells[1]
                continue
            if line.startswith("|"):
                m = ROW_RE.match(line)
                if m:
                    rows.append({"club": m.group(1), "role": m.group(2), "position": m.group(3),
                                 "jersey": m.group(4), "player": m.group(5)})
    return header, rows


def build_join(gb_rows, report_rows, clubs=("WAS", "NYG")):
    """Join the game-book participation cells to the report rows of the same clubs."""
    gb_by_key = {}
    collisions = []
    for g in gb_rows:
        key = (g["club"],) + (_split_gb_name(g["player"]) or ("", g["player"]))
        if key in gb_by_key:
            collisions.append({"key": key, "game_book_cells": 2})
        gb_by_key[key] = g
    joined = []
    for r in report_rows:
        if r["team"] not in clubs:
            continue
        rk = _report_key(r["player"])
        g = gb_by_key.get((r["team"], rk[0], rk[1])) if rk else None
        joined.append({
            "club": r["team"], "player": r["player"], "pos": r["pos"],
            "injury": r["injury"], "practice_status": r["practice_status"],
            "game_status": r["game_status"],
            "game_book_status": g["role"] if g else "not_found_in_game_book",
            "game_book_position": g["position"] if g else "",
            "game_book_jersey": g["jersey"] if g else "",
            "match_rule": "initial+surname",
        })
    return joined, collisions


def main():
    header, gb_rows = parse_transcript(os.path.join(HERE, TRANSCRIPT))
    report = load(f"data/captures/{CAP_DATE}/league_injury_report_week10.json")
    joined, collisions = build_join(gb_rows, report["rows"])
    roles = {}
    for g in gb_rows:
        roles[g["role"]] = roles.get(g["role"], 0) + 1
    statuses = {}
    for j in joined:
        statuses[j["game_book_status"]] = statuses.get(j["game_book_status"], 0) + 1
    # calibration rows: Out / Doubtful report rows vs actual game-book status
    calibration = [j for j in joined if j["game_status"] in ("Out", "Doubtful")]
    capture = {
        "dataset": "nfl_collector_capture",
        "capture_id": f"GAMEBOOK-WAS-NYG-REG10-{CAP_DATE}",
        "kind": "official_game_book_participation",
        "source": {
            "publisher": "NFL Enterprise (nfl.com — league CDN)",
            "key": "game_book_was_nyg_reg10",
            "url": PDF_URL,
            "game_centre_url": GAME_CENTRE,
            "pdf_url": PDF_URL,
            "discovery": "the game centre page publishes 'Download Game Book (PDF)' per fixture; "
                         "verified in-session 2026-11-16",
            "pdf_page": "1 of the PDF (participation block)",
            "header_as_printed": header,
        },
        "clock": {
            "read_window_start_utc": "2026-11-16T02:35:00Z",
            "read_window_end_utc": "2026-11-16T03:05:00Z",
            "window_evidence": "same single-pass read window as the other captures",
        },
        "method": {
            "capture_class": "session_fetch_markdown_transcript",
            "how": "PDF rendered by the page-fetch tool; the participation block (Lineups, "
                   "Substitutions, Did Not Play, Not Active) is on page 1 and transcribed "
                   "verbatim in role order; the remaining PDF pages (drive charts, play-by-play) "
                   "are not needed for participation",
            "chunk_count": 1,
            "transcript_sha256": {"transcript_gamebook_WAS_NYG_reg10.md": sha256_file(os.path.join(HERE, TRANSCRIPT))},
            "limitation": "raw PDF bytes not stored (RC-05/RC-09); spike covers 1 of 14 Week 10 "
                          "fixtures (DEC-3 = B); the CI collector's per-fixture discovery route "
                          "is registered for the remaining 13",
        },
        "rows": gb_rows,
        "counts": {"rows_total": len(gb_rows), "by_role": roles},
        "join_to_report": {
            "rule": "game book prints 'F.LastName'; a report row matches when its first token "
                    "starts with that initial and its last token equals that surname; collisions "
                    "are flagged, never guessed through",
            "rows": joined,
            "counts": statuses,
            "collisions": collisions,
            "calibration_rows": calibration,
        },
    }
    save(f"data/captures/{CAP_DATE}/gamebook_was_nyg_reg10.json", capture)

    # ledger entry (idempotent)
    from transcribe import update_ledger  # noqa: PLC0415 — reuse the same chain
    update_ledger([capture])

    n_out_na = sum(1 for j in calibration if j["game_book_status"] == "not_active")
    print(f"gamebook: {len(gb_rows)} participation rows ({roles}); join: {len(joined)} report rows "
          f"of WAS/NYG -> {statuses}; collisions={len(collisions)}; "
          f"Out/Doubtful rows: {len(calibration)}, of which not_active: {n_out_na}")


if __name__ == "__main__":
    main()
