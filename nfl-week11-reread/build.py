#!/usr/bin/env python3
"""Week 11 official injury-report re-read: delta-first public site.

Inputs
  private-store/nfl-week11/week11_injury_report_rows.psv   row-level transcription of the 2026-11-19 read (NOT published)
  snapshots/2026-11-18/injury_report-2026-11-18T234917Z.html  stored raw capture of https://www.nfl.com/injuries/ (committed)
Outputs (public, derived only)
  data/delta_week11.json, index.html, pages/delta.html, pages/flagged.html
Run: python3 build.py   then   python3 verify.py
"""
import hashlib
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent
PRIVATE_PSV = REPO / "private-store" / "nfl-week11" / "week11_injury_report_rows.psv"
RAW_1118 = REPO / "nfl-readiness-register" / "snapshots" / "2026-11-18" / "injury_report-2026-11-18T234917Z.html"
RAW_1118_URL = "https://github.com/sassnarep3-star/Own4/blob/main/nfl-readiness-register/snapshots/2026-11-18/injury_report-2026-11-18T234917Z.html"
SOURCE = "https://www.nfl.com/injuries/"
FETCH_DATE = "2026-11-19"

TEAM_NAMES = {
    "IND": "Colts", "HOU": "Texans", "PIT": "Steelers", "PHI": "Eagles", "AZ": "Cardinals",
    "KC": "Chiefs", "BAL": "Ravens", "CAR": "Panthers", "TB": "Buccaneers", "DET": "Lions",
    "MIA": "Dolphins", "BUF": "Bills", "TEN": "Titans", "DAL": "Cowboys", "NO": "Saints",
    "CHI": "Bears", "NYJ": "Jets", "LAC": "Chargers", "JAX": "Jaguars", "NYG": "Giants",
    "LV": "Raiders", "DEN": "Broncos", "MIN": "Vikings", "SF": "49ers", "CIN": "Bengals",
    "WAS": "Commanders", "ATL": "Falcons", "CLE": "Browns", "GB": "Packers", "LAR": "Rams",
    "NE": "Patriots", "SEA": "Seahawks",
}
MISSING_FROM_PAGE = ["ATL", "CLE", "GB", "LAR", "NE", "SEA"]
PRACTICE_OK = {"Full Participation in Practice", "Limited Participation in Practice", "Did Not Participate In Practice"}
GAME_OK = {"", "Questionable", "Doubtful", "Out", "Probable"}

NEWS = {
    "mayfield": "https://www.nfl.com/news/buccaneers-qb-baker-mayfield-injury-week-11",
    "roundup_nov16": "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-monday-nov-16",
    "hutchinson": "https://www.nfl.com/news/lions-aidan-hutchinson-knee-injury-patriots",
    "lamar": "https://www.nfl.com/news/ravens-lamar-jackson-right-thumb-out-6-9-weeks-expects-to-return-this-season",
    "maye": "https://www.nfl.com/news/nfl-network-patriots-qb-drake-maye-could-miss-rest-of-2026-season",
    "nacua": "https://www.nfl.com/news/rams-wr-puka-nacua-likely-to-be-placed-on-injured-reserve-with-turf-toe-sprained-mcl-and-pcl",
    "willis": "https://www.nfl.com/news/dolphins-place-qb-malik-willis-groin-on-injured-reserve-kyle-mccord-in-line-for-first-start",
}

FLAGS = [
    {"id": "FL-01", "severity": "high", "club": "ATL, CLE, GB, LAR, NE, SEA",
     "issue": "Six clubs have no section in either read: the 2026-11-18 stored capture and the 2026-11-19 page text. Neither shows a 'No Injuries Reported' block for them. The page does not say whether they are on bye or omitted. Not inferred.",
     "action": "Confirm each club's Week 11 status on the official NFL schedule before any team-level use.",
     "source": SOURCE},
    {"id": "FL-02", "severity": "high", "club": "LAC",
     "issue": "Delta: the 2026-11-18 23:49 UTC capture shows 'Chargers - No Injuries Reported'. The 2026-11-19 read shows 11 Chargers rows. The page does not say when the section changed, so the timing of the change is unknown.",
     "action": "Reviewer to confirm the change time from the official report history; the delta is published, the level is not.",
     "source": RAW_1118_URL},
    {"id": "FL-03", "severity": "high", "club": "TB",
     "issue": "Baker Mayfield is listed 'Did Not Participate In Practice' with a blank Injuries cell. An official NFL.com headline on the same site says he is dealing with a lower-leg injury. The cell is left blank; the headline is not used to fill it.",
     "action": "Reviewer to compare the report row with the linked article.",
     "source": NEWS["mayfield"]},
    {"id": "FL-04", "severity": "high", "club": "MIN",
     "issue": "Jordan Addison is listed 'Did Not Participate In Practice' with a blank Injuries cell. An official NFL.com headline says he needs thumb surgery and could go to IR.",
     "action": "Reviewer to compare the report row with the linked article.",
     "source": NEWS["roundup_nov16"]},
    {"id": "FL-05", "severity": "high", "club": "DET",
     "issue": "An official NFL.com headline reports Aidan Hutchinson feared to have suffered a significant knee injury. He has no row on the Lions section.",
     "action": "Reviewer to check whether he is on another list before reading absence as health.",
     "source": NEWS["hutchinson"]},
    {"id": "FL-06", "severity": "high", "club": "BAL",
     "issue": "An official NFL.com headline says Lamar Jackson is expected out 6-9 weeks. He has no row on the Ravens section. The page carries no reserve list, so the reason for absence is not shown.",
     "action": "Confirm reserve status from an official transactions or reserve-list source.",
     "source": NEWS["lamar"]},
    {"id": "FL-07", "severity": "medium", "club": "NE",
     "issue": "Patriots are absent from both reads, and an official NFL.com headline says Drake Maye could miss the rest of the 2026 season.",
     "action": "Resolve together with FL-01.",
     "source": NEWS["maye"]},
    {"id": "FL-08", "severity": "medium", "club": "LAR",
     "issue": "Rams are absent from both reads, and an official NFL.com headline says Puka Nacua is likely to be placed on injured reserve.",
     "action": "Resolve together with FL-01.",
     "source": NEWS["nacua"]},
    {"id": "FL-09", "severity": "medium", "club": "MIA",
     "issue": "Malik Willis is not on the Dolphins section. An official NFL.com headline says he was placed on injured reserve. The page shows no reserve list, so 'not listed' is not read as 'available'.",
     "action": "None for this read; keep reserve status separate from report absence.",
     "source": NEWS["willis"]},
    {"id": "FL-10", "severity": "medium", "club": "DET",
     "issue": "Kerby Joseph, Cade Mays and D.J. Reed show a blank Game Status. The repository's earlier flag (VR-08, VR-12) says an official article lists all three as Out. That article was not re-read here, so the conflict is unresolved.",
     "action": "Open the referenced article and record its date next to the row.",
     "source": SOURCE},
    {"id": "FL-11", "severity": "high", "club": "all",
     "issue": "Method limit. The sandbox cannot reach nfl.com directly (curl exit 35), so no raw HTML hash exists for the 2026-11-19 read. Its rows were transcribed from the fetch-tool text of the page's 7 chunks and kept in a private store. Cross-check: 242 of the 253 rows match the stored 2026-11-18 raw capture exactly; the 11 that differ are the LAC block in FL-02. A reviewer must spot-check against the live page.",
     "action": "Spot-check the live page against the private store (access held by the owner).",
     "source": SOURCE},
    {"id": "FL-12", "severity": "low", "club": "all",
     "issue": "The fetch tool returns no clock time, only the read date. The clock-time rule cannot be met for the 2026-11-19 read. The 2026-11-18 capture has a clock time (23:49:17 UTC).",
     "action": "Record the fetch clock time in the next capture.",
     "source": SOURCE},
    {"id": "FL-13", "severity": "medium", "club": "repository",
     "issue": "Board conflict. An earlier COORDINATION.md entry (S-02) describes the injury page as 'Week 10 still shown'. The stored 2026-11-18 raw capture in this repository is titled Week 11. The raw capture is used here; the earlier note is not.",
     "action": "Correct the board note in the next integration pass.",
     "source": RAW_1118_URL},
]


def parse_private():
    rows, games, noinj = [], [], []
    for raw in PRIVATE_PSV.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("|")
        if parts[0] == "GAME":
            _, day, time, net, away, home = parts
            games.append({"day": day, "time": time, "network": net, "away": away, "home": home})
        elif parts[0] == "NOINJ":
            noinj.append(parts[1])
        else:
            if len(parts) != 6:
                raise SystemExit(f"bad column count ({len(parts)}): {line}")
            team, player, pos, injury, practice, game = parts
            rows.append({"team": team, "player": player, "position": pos, "injury": injury,
                         "practice_status": practice, "game_status": game})
    return rows, games, noinj


def parse_raw_1118():
    """Machine-parse the stored raw capture: club tables plus 'No Injuries Reported' blocks.
    Club attribution = the last club nickname in the text between the previous marker and this one."""
    s = RAW_1118.read_text(encoding="utf-8", errors="replace")
    nick = {v: k for k, v in TEAM_NAMES.items()}
    pattern = re.compile(r"<table\b|No Injuries Reported")
    out = {}
    prev = 0
    for m in pattern.finditer(s):
        seg = re.sub(r"<[^>]+>", " ", s[prev:m.start()])
        names = [w for w in re.findall(r"[A-Za-z0-9]+", seg) if w in nick]
        if m.group(0) == "<table":
            end = s.find("</table>", m.start())
            tb = s[m.start():end]
            recs = []
            for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", tb, re.S):
                cells = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
                if len(cells) != 5:
                    continue
                vals = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in cells]
                recs.append(vals)
            if names and recs:
                out.setdefault(nick[names[-1]], []).extend(recs)
            prev = end
        else:
            if names:
                out.setdefault(nick[names[-1]], "NOINJ")
            prev = m.end()
    return out


def delta(rows_now, raw_then):
    now = {}
    for r in rows_now:
        now.setdefault(r["team"], []).append(
            (r["player"], r["position"], r["injury"], r["practice_status"], r["game_status"]))
    per_club = []
    for code in TEAM_NAMES:
        then = raw_then.get(code)
        cur = now.get(code, [])
        if then is None:
            status = "absent in 11-18 capture"
            then_rows = []
            then_noinj = False
        elif then == "NOINJ":
            status = "No Injuries Reported (11-18)"
            then_rows = []
            then_noinj = True
        else:
            status = "rows (11-18)"
            then_rows = [tuple(x) for x in then]
            then_noinj = False
        s_then, s_now = set(then_rows), set(cur)
        added = len(s_now - s_then)
        removed = len(s_then - s_now)
        if not then_rows and not then_noinj and not cur:
            state = "absent in both reads"
        elif added == 0 and removed == 0 and then_rows == [] and cur == []:
            state = "no change"
        elif added == 0 and removed == 0 and len(then_rows) == len(cur):
            state = "no change"
        else:
            state = "changed"
        if code in MISSING_FROM_PAGE and not then_rows and not cur:
            state = "absent in both reads"
        per_club.append({"club": code, "name": TEAM_NAMES[code], "state_1118": status,
                         "rows_1118": len(then_rows), "rows_1119": len(cur),
                         "added": added, "removed": removed, "state": state})
    return per_club


def build_outputs():
    rows, games, noinj = parse_private()
    raw_then = parse_raw_1118()
    per_club = delta(rows, raw_then)
    n_compared = sum(1 for c in per_club if c["state"] in ("no change", "changed"))
    n_same = sum(1 for c in per_club if c["state"] == "no change")
    n_changed = sum(1 for c in per_club if c["state"] == "changed")
    n_absent = sum(1 for c in per_club if c["state"] == "absent in both reads")
    rows_same = sum(c["rows_1119"] for c in per_club if c["state"] == "no change")
    digest = hashlib.sha256(PRIVATE_PSV.read_bytes()).hexdigest()
    raw_digest = hashlib.sha256(RAW_1118.read_bytes()).hexdigest()
    data = {
        "source": SOURCE,
        "capture_then": {"utc": "2026-11-18T23:49:17Z", "raw_file_sha256": raw_digest, "raw_file": RAW_1118_URL},
        "capture_now": {"date": FETCH_DATE, "clock_time": None, "method": "fetch_page tool (7 chunks)",
                        "private_transcription_sha256": digest},
        "clubs_total": len(TEAM_NAMES),
        "clubs_compared": n_compared,
        "clubs_no_change": n_same,
        "clubs_changed": n_changed,
        "clubs_absent_both_reads": n_absent,
        "rows_unchanged_count": rows_same,
        "per_club_delta": per_club,
        "games": games,
        "flags": FLAGS,
    }
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "delta_week11.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return data, len(rows)


CSS = """
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1d2330;background:#f6f7f9;line-height:1.45}
header{background:#013369;color:#fff;padding:18px 24px}
nav a{margin-right:14px;color:#fff;text-decoration:none;font-weight:600}
main{padding:20px 24px;max-width:1200px;margin:auto}
h1{font-size:1.5rem;margin:.2rem 0}h2{font-size:1.2rem;margin-top:1.6rem}
.cards{display:flex;flex-wrap:wrap;gap:12px}
.card{background:#fff;border:1px solid #dde1e7;border-radius:8px;padding:12px 16px;min-width:170px}
.card b{display:block;font-size:1.5rem}
table{border-collapse:collapse;width:100%;background:#fff;font-size:.92rem;margin:8px 0 18px}
th,td{border-bottom:1px solid #e5e8ed;padding:6px 8px;text-align:left;vertical-align:top}
th{background:#eef1f5}
.flag-high{color:#9b1c1c;font-weight:600}.flag-medium{color:#8a5a00;font-weight:600}.flag-low{color:#285e3a}
.note{background:#fff8e1;border:1px solid #f0d98a;padding:10px 14px;border-radius:6px}
.blank{color:#8a94a6}
footer{padding:16px 24px;color:#56606f;font-size:.85rem}
"""


def page(title, body, depth=0):
    prefix = "../" if depth else ""
    nav = (f'<nav><a href="{prefix}index.html">Landing</a>'
           f'<a href="{prefix}pages/delta.html">Club delta</a>'
           f'<a href="{prefix}pages/flagged.html">Flagged for Review</a></nav>')
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body>"
            "<header><h1 style='color:#fff;margin:0 0 8px'>NFL Week 11 injury report: delta re-read (2026)</h1>"
            f"{nav}</header><main>{body}</main>"
            f"<footer>Read date {FETCH_DATE} (UTC). Every row links to an official NFL.com source. Research only, not wagering advice. "
            "Blank = blank on the official page or unverified; never filled in. Row-level player data is held in a private store and is not published here.</footer>"
            "</body></html>")


def flags_table(flags):
    out = ["<table><tr><th>ID</th><th>Severity</th><th>Club</th><th>Issue (as read)</th><th>Action</th><th>Source</th></tr>"]
    for f in flags:
        out.append(f"<tr><td>{f['id']}</td><td class='flag-{f['severity']}'>{f['severity']}</td>"
                   f"<td>{html.escape(f['club'])}</td><td>{html.escape(f['issue'])}</td>"
                   f"<td>{html.escape(f['action'])}</td>"
                   f"<td><a href='{f['source']}'>source</a></td></tr>")
    out.append("</table>")
    return "".join(out)


def build_pages(data, row_count):
    per = data["per_club_delta"]
    changed = [c for c in per if c["state"] == "changed"]
    games = data["games"]
    cards = f"""
<div class="cards">
 <div class="card"><b>{data['clubs_total']}</b>NFL clubs checked</div>
 <div class="card"><b>{data['clubs_no_change']}</b>clubs unchanged between reads</div>
 <div class="card"><b>{data['clubs_changed']}</b>club(s) changed</div>
 <div class="card"><b>{data['clubs_absent_both_reads']}</b>clubs absent in both reads</div>
 <div class="card"><b>{data['rows_unchanged_count']}</b>report rows unchanged (no level published)</div>
 <div class="card"><b>{len(FLAGS)}</b>items flagged for review</div>
</div>"""
    landing = f"""
<h2>Headline (delta, not level)</h2>
{cards}
<div class="note"><b>What changed:</b> between the stored official capture of 2026-11-18 23:49:17 UTC and the official
NFL.com read of {FETCH_DATE}, the Los Angeles Chargers went from "No Injuries Reported" to a populated report section (FL-02).
The other {data['clubs_no_change']} clubs showed no row-level change. Six clubs are absent from both reads (FL-01).
<br><b>Caveat:</b> this is a two-read comparison, not a timestamped series. The second read has no clock time
(FL-12), and the second read was transcribed by hand from the fetch-tool text (FL-11).</div>
<h2>Pages</h2>
<table><tr><th>Page</th><th>What it shows</th><th>Source</th></tr>
<tr><td><a href="pages/delta.html">Club delta</a></td><td>Per-club comparison: rows in each read, added, removed, state</td><td><a href="{SOURCE}">nfl.com/injuries</a></td></tr>
<tr><td><a href="pages/flagged.html">Flagged for Review</a></td><td>{len(FLAGS)} irregularities and unverified items, with source links</td><td><a href="{SOURCE}">nfl.com/injuries</a></td></tr>
</table>
<h2>Games listed on the Week 11 page (schedule facts, as displayed)</h2>
<table><tr><th>Day</th><th>Time (as displayed)</th><th>Network (as displayed)</th><th>Away (record)</th><th>Home (record)</th><th>Source</th></tr>
{''.join(f"<tr><td>{g['day']}</td><td>{g['time']}</td><td>{html.escape(g['network'])}</td><td>{html.escape(g['away'])}</td><td>{html.escape(g['home'])}</td><td><a href='{SOURCE}'>nfl.com/injuries</a></td></tr>" for g in games)}
</table>
<h2>Not done in this read</h2>
<ul>
<li>Depth charts, inactive lists and snap counts: not read here.</li>
<li>Injury-designation reliability scoring: needs archived past-season reports; not read here.</li>
<li>Any model, price, or strategy output: none in this read.</li>
</ul>"""

    rows_html = []
    for c in per:
        rows_html.append(
            f"<tr><td>{c['club']} {c['name']}</td><td>{c['state_1118']}</td><td>{c['rows_1118']}</td>"
            f"<td>{c['rows_1119']}</td><td>{c['added']}</td><td>{c['removed']}</td>"
            f"<td><b>{c['state']}</b></td>"
            f"<td><a href='{SOURCE}'>nfl.com/injuries</a> &middot; <a href='{RAW_1118_URL}'>11-18 raw capture</a></td></tr>")
    delta_page = f"""
<h2>Per-club delta: 2026-11-18 23:49 UTC capture vs {FETCH_DATE} read</h2>
<p>Counts only. Row contents are held privately and are not published. "Absent in both reads" means the club has no section in either read (FL-01).</p>
<table><tr><th>Club</th><th>11-18 status</th><th>Rows 11-18</th><th>Rows 11-19</th><th>Added</th><th>Removed</th><th>State</th><th>Source</th></tr>
{''.join(rows_html)}</table>
<p class="note">Method: each read is compared club by club on the full row (player, position, injury, practice status, game status).
The 11-18 side was machine-parsed from the stored raw HTML. The 11-19 side is a hand transcription of the fetch-tool text (FL-11).</p>"""

    flagged = f"""
<h2>Flagged for Review</h2>
<p class="note">Published with links and not blocking. Each needs a reviewer decision. Nothing here was filled in from a headline.
FL-01 and FL-11 affect the whole read.</p>
{flags_table(FLAGS)}"""

    (ROOT / "index.html").write_text(page("NFL Week 11 injury report re-read", landing), encoding="utf-8")
    (ROOT / "pages").mkdir(exist_ok=True)
    (ROOT / "pages" / "delta.html").write_text(page("Club delta - Week 11", delta_page, 1), encoding="utf-8")
    (ROOT / "pages" / "flagged.html").write_text(page("Flagged for Review - Week 11 re-read", flagged, 1), encoding="utf-8")


def main():
    data, row_count = build_outputs()
    build_pages(data, row_count)
    print(f"private_rows={row_count} clubs_compared={data['clubs_compared']} unchanged={data['clubs_no_change']} "
          f"changed={data['clubs_changed']} absent_both={data['clubs_absent_both_reads']} flags={len(FLAGS)}")


if __name__ == "__main__":
    main()
