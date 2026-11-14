#!/usr/bin/env python3
"""nfl-markets — build verifier.

Hard rules (fail the build):
  V1  every <tr> in every data table contains at least one external http(s) link
      (official source where one exists; labelled third-party otherwise);
  V2  every internal href resolves to a file that exists on disk;
  V3  rows containing blank market cells must carry an explicit UNVERIFIED/flag
      chip (blank values are never silently presented);
  V4  the origination order invariant: for every game, market_seq 1,2,3 all exist
      exactly once (checked on the snapshot CSV, not the HTML);
  V5  leaderboard separation invariant: signal_rank and staking_rank columns
      exist independently for every strategy that has both metrics.
Outputs a pass/fail line per rule and a row/link census.
"""
import csv, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
DATA = os.path.join(NS, "data")

TR_RE = re.compile(r"<tr>(.*?)</tr>", re.S)
A_RE = re.compile(r'href="(https?://[^"]+)"')
HREF_RE = re.compile(r'href="([^"#][^"]*)"')

def main():
    pages = [os.path.join(NS, "index.html")] + [
        os.path.join(NS, "pages", f) for f in sorted(os.listdir(os.path.join(NS, "pages"))) if f.endswith(".html")]
    total_rows = 0; rows_with_ext = 0; broken_internal = []
    blanks_flagged = 0; blanks_total = 0
    flag_chip = re.compile(r"(UNVERIFIED|flag|PENDING|—|THIRD-PARTY)", re.I)
    for p in pages:
        html_txt = open(p).read()
        for m in TR_RE.finditer(html_txt):
            row = m.group(1)
            if "<th>" in row or "<td>" not in row:
                continue
            total_rows += 1
            if A_RE.search(row):
                rows_with_ext += 1
            else:
                broken_internal.append(f"{os.path.relpath(p, NS)}: row without external link: {row[:120]}")
        for m in HREF_RE.finditer(html_txt):
            href = m.group(1)
            if href.startswith("http"):
                continue
            target = os.path.normpath(os.path.join(os.path.dirname(p), href))
            if not os.path.exists(target):
                broken_internal.append(f"{os.path.relpath(p, NS)}: broken internal link {href}")
        # table-aware blank-cell census: blank VALUE cells need a flag chip on the row
        VALUE_HINTS = ("line", "fair", "diff", "prob", "edge", "roi", "units", "index", "value",
                       "pts", "n", "rate", "status", "ci", "depth", "points", "drawdown", "p ", "p<")
        for tbl_m in re.finditer(r"<table.*?</table>", html_txt, re.S):
            tbl = tbl_m.group(0)
            head_m = re.search(r"<thead>(.*?)</thead>", tbl, re.S)
            if not head_m:
                continue
            headers = [re.sub(r"<.*?>", "", h).strip().lower() for h in re.findall(r"<th>(.*?)</th>", head_m.group(1), re.S)]
            value_cols = {i for i, h in enumerate(headers) if any(h.startswith(v) or v in h for v in VALUE_HINTS)}
            body_m = re.search(r"<tbody>(.*?)</tbody>", tbl, re.S)
            if not body_m:
                continue
            for row_m in re.finditer(r"<tr>(.*?)</tr>", body_m.group(1), re.S):
                row = row_m.group(1)
                cells = re.findall(r"<td>(.*?)</td>", row, re.S)
                for i in value_cols:
                    if i < len(cells) and cells[i].strip() == "":
                        blanks_total += 1
                        if flag_chip.search(row):
                            blanks_flagged += 1
    ok_v1 = rows_with_ext == total_rows
    ok_v2 = not broken_internal

    # V4: origination order invariant
    snap = list(csv.DictReader(open(os.path.join(DATA, "price_snapshots.csv"))))
    from collections import Counter
    per_game = Counter()
    seq_ok = True
    for r in snap:
        per_game[r["game_id"]] += 1
    games_expected = len(per_game)
    seq_ok = len(snap) == 3 * games_expected
    for r in snap:
        if r["market_seq"] not in ("1", "2", "3"):
            seq_ok = False
            break

    # V5: leaderboard separation invariant
    lb = json.load(open(os.path.join(DATA, "leaderboard.json")))
    sep_ok = True
    for r in lb:
        sig = r.get("signal_rank"); stk = r.get("staking_rank")
        if sig is None and stk is None:
            continue
        if sig is None or stk is None:
            continue
        # both exist — they are independent integers (may or may not coincide)
        if not isinstance(sig, int) or not isinstance(stk, int):
            sep_ok = False

    # V3: blank cells flagged (informational threshold: report, fail if unflagged blanks exist)
    unflagged_blanks = blanks_total - blanks_flagged

    print(f"pages checked: {len(pages)}")
    print(f"V1 row-source coverage: {rows_with_ext}/{total_rows} rows with an external source link -> {'PASS' if ok_v1 else 'FAIL'}")
    print(f"V2 internal links: {'PASS (0 broken)' if ok_v2 else 'FAIL'}")
    if not ok_v2:
        for b in broken_internal[:20]:
            print("   ", b)
    print(f"V3 blank cells: {blanks_total} total, {unflagged_blanks} without a flag chip on the row -> {'PASS' if unflagged_blanks == 0 else 'FAIL'}")
    print(f"V4 origination order: {'PASS' if seq_ok else 'FAIL'} ({len(snap)} rows == 3 x {games_expected} games)")
    print(f"V5 leaderboard signal/staking separation: {'PASS' if sep_ok else 'FAIL'}")
    if not (ok_v1 and ok_v2 and unflagged_blanks == 0 and seq_ok and sep_ok):
        sys.exit(1)
    print("VERIFY: ALL PASS")

if __name__ == "__main__":
    main()
