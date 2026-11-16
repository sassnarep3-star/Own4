"""Parser self-test: validates the CI collector's HTML extraction mechanics against a
SYNTHETIC fixture whose structure mirrors the three registered source schemas.

The fixture is written by hand from the structure the session capture observed (tables with
the pinned headers, club headings between tables). It is clearly synthetic and is NEVER
published as data. What this proves: the TableParser correctly extracts the pinned schemas
from <table> markup. What it does NOT prove: that the live DOM matches on every run — that
is what the drift alarm is for (a schema change fails loudly).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collect import TableParser, _slug_from_cell  # noqa: E402

FIXTURE = """<!DOCTYPE html><html><body>
<h2>THURSDAY, NOVEMBER 12TH</h2>
<h3>WAS at NYG</h3>
<h4>Commanders (WAS)</h4>
<table><thead><tr><th>Player</th><th>Position</th><th>Injuries</th><th>Practice Status</th><th>Game Status</th></tr></thead>
<tbody>
<tr><td>John Bates</td><td>TE</td><td></td><td>Full Participation in Practice</td><td></td></tr>
<tr><td>Lucas Patrick</td><td>C</td><td>Concussion</td><td>Did Not Participate In Practice</td><td>Out</td></tr>
</tbody></table>
<h4>Giants (NYG)</h4>
<table><thead><tr><th>Player</th><th>Position</th><th>Injuries</th><th>Practice Status</th><th>Game Status</th></tr></thead>
<tbody>
<tr><td>Malik Harrison</td><td>LB</td><td>Groin</td><td>Limited Participation in Practice</td><td>Questionable</td></tr>
</tbody></table>
<h2>Trades</h2>
<table><thead><tr><th>From</th><th>To</th><th>Date</th><th>Name</th><th>Position</th><th>Transaction</th></tr></thead>
<tbody>
<tr><td>ATL</td><td>JAX</td><td>11/10</td><td>Jessie Bates</td><td></td><td>Traded</td></tr>
</tbody></table>
<h2>OFFENSE</h2>
<table><thead><tr><th>Position</th><th>Player</th><th>Player</th><th>Player</th></tr></thead>
<tbody>
<tr><td>WR</td><td>9 Christian Watson</td><td>16 Bo Melton</td><td></td></tr>
<tr><td>RB</td><td></td><td></td><td>26 Kaleb Johnson</td></tr>
</tbody></table>
</body></html>"""


def main():
    p = TableParser()
    p.feed(FIXTURE)
    tables = p.tables
    problems = []

    def want(cond, msg):
        if not cond:
            problems.append(msg)

    want(len(tables) == 4, f"expected 4 tables, got {len(tables)}")
    if len(tables) == 4:
        t_inj1, t_inj2, t_txn = None, None, None
        t_depth = None
        for t in tables:
            head = [h.lower() for h in t["header"][:5]]
            if head[:2] == ["player", "position"] and len(t["rows"]) == 2:
                t_inj1 = t_inj1 or t
            elif head[:2] == ["player", "position"]:
                t_inj2 = t
            elif head[:2] == ["from", "to"]:
                t_txn = t
            elif head[:2] == ["position", "player"]:
                t_depth = t
        want(t_inj1 is not None and len(t_inj1["rows"]) == 2, "injury table 1 rows")
        want(t_inj1 and t_inj1["rows"][1][3] == "Did Not Participate In Practice",
             "injury practice cell")
        want(t_txn is not None and t_txn["rows"][0][2] == "11/10", "transactions row date")
        want(t_depth is not None and len(t_depth["rows"]) == 2, "depth table rows")
        # the depth cells: jersey strip rule
        num, name = _slug_from_cell(t_depth["rows"][0][1])
        want(num == "9" and name == "Christian Watson", f"jersey strip: {num} {name!r}")
        num2, name2 = _slug_from_cell(t_depth["rows"][1][3])
        want(num2 == "26" and name2 == "Kaleb Johnson", f"slot-3 strip: {num2} {name2!r}")
        want(t_depth["rows"][0][3] == "", "empty slot preserved")
        # club attribution context reaches the parser
        want("WAS" in (t_inj1.get("context") or ""), "club heading context captured")

    if problems:
        print("selftest: FAIL")
        for m in problems:
            print("  -", m)
        sys.exit(1)
    print("selftest: PASS — TableParser extracts all three pinned schemas from table markup "
          "(synthetic fixture, never published as data)")


if __name__ == "__main__":
    main()
