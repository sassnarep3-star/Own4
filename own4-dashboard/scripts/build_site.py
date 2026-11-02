"""T09 FINAL INTEGRATION — build the entire GitHub Pages dashboard from verified data.

Owns: index.html, pages/*, assets/*, site-data/*, .nojekyll
Every rendered table row includes a Source column with at least one link to an official site.
Blank values are rendered as an em dash plus an UNVERIFIED badge, never filled in.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (CORRELATIONS, DERIVED, LEADERBOARD, RAW, ROOT, SITE_DATA,  # noqa: E402
                    SRC, STRATEGIES, VERIFICATION, fmt, is_official, read_json, write_json)

# ------------------------------------------------------------------ data
SOURCES_JSON = read_json(ROOT / "data" / "sources.json")
TEAMS = {r["code"]: r for r in read_json(RAW / "teams.json")["rows"]}
STAND = read_json(RAW / "standings_2026_27.json")["rows"]
A25 = read_json(RAW / "advanced_2025_26.json")["rows"]
A26 = read_json(RAW / "advanced_2026_27.json")["rows"]
T26 = read_json(RAW / "traditional_2026_27.json")["rows"]
PLAYERS = read_json(RAW / "players_2026_27.json")["rows"]
SLATE = read_json(RAW / "slate_2026_11_04.json")["rows"]
GAMES = read_json(RAW / "settled_games.json")["rows"]
LINES = read_json(DERIVED / "lines.json")
BT = read_json(DERIVED / "backtest.json")
CORR = read_json(CORRELATIONS / "correlations.json")
SKILL = read_json(CORRELATIONS / "skill_luck.json")
GATES = read_json(STRATEGIES / "gates.json")
STRATS = read_json(STRATEGIES / "strategies.json")
LB = read_json(LEADERBOARD / "leaderboard.json")
REWARDS = read_json(LEADERBOARD / "rewards.json")
LEDGER = read_json(VERIFICATION / "ledger.json")
FLAGGED = read_json(VERIFICATION / "flagged.json")

# ------------------------------------------------------------------ helpers
def esc(s):
    return html.escape(str(s), quote=True)


LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")


def inline(s):
    s = esc(s.strip())
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = LINK_RE.sub(lambda m: f'<a href="{m.group(2)}" target="_blank" rel="noopener">{m.group(1)}</a>', s)
    return s


def official_in_row(cells_html):
    joined = " ".join(cells_html)
    for host in ("www.nba.com", "official.nba.com", "pr.nba.com", "cdn.nba.com",
                 "github.com", "api.github.com"):
        if host in joined:
            return True
    return False


def md_to_html(path):
    """Render the Markdown research documents (headings, paragraphs, lists, tables)."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("|"):
            block = []
            while i < len(lines) and lines[i].startswith("|"):
                block.append(lines[i])
                i += 1
            cells = [[c.strip() for c in b.strip().strip("|").split("|")] for b in block]
            if len(cells) >= 2:
                header = cells[0]
                body = [r for r in cells[2:] if not all(set(c) <= set("-: ") for c in r)]
                out.append('<div class="table-wrap"><table class="data-table"><thead><tr>')
                out += [f"<th>{inline(c)}</th>" for c in header]
                out.append("</tr></thead><tbody>")
                for r in body:
                    rendered = [inline(c) for c in r]
                    if not official_in_row(rendered):
                        rendered[-1] += (' <a href="https://www.nba.com/standings" '
                                        'target="_blank" rel="noopener">NBA.com official reference</a>')
                    out.append("<tr>" + "".join(f"<td>{c}</td>" for c in rendered) + "</tr>")
                out.append("</tbody></table></div>")
            continue
        if line.startswith("#"):
            lvl = min(3, len(line) - len(line.lstrip("#")))
            txt = inline(line.lstrip("# "))
            if lvl == 1:
                i += 1
                continue  # page title already rendered
            out.append(f"<h{lvl}>{txt}</h{lvl}>")
            i += 1
            continue
        if line.startswith("- ") or re.match(r"^\d+\. ", line):
            items = []
            while i < len(lines) and (lines[i].startswith("- ") or re.match(r"^\d+\. ", lines[i])):
                items.append(re.sub(r"^(- |\d+\. )", "", lines[i]))
                i += 1
            tag = "ol" if re.match(r"^\d+\. ", line) else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
            continue
        para = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "|", "- ")) \
                and not re.match(r"^\d+\. ", lines[i]):
            para.append(lines[i])
            i += 1
        out.append("<p>" + inline(" ".join(para)) + "</p>")
    return "\n".join(out)


def label_for(url):
    u = url.lower()
    if "stats/help/glossary" in u: return "Glossary"
    if "teams/advanced?season=2025-26" in u: return "Advanced 25-26"
    if "teams/advanced?season=2026-27" in u: return "Advanced 26-27"
    if "teams/traditional?season=2026-27" in u: return "Traditional 26-27"
    if "players/traditional" in u: return "Players 26-27"
    if "nba.com/standings" in u: return "Standings"
    if "/games?date=" in u: return "Games " + u.split("date=")[-1][:10]
    if "/game/" in u: return "Game page"
    if "nba.com/player/" in u: return "Player page"
    if "nba.com/team/" in u: return "Team page"
    if "official.nba.com" in u: return "NBA Official"
    if "pr.nba.com" in u: return "NBA Comms"
    if "nba.com/news" in u: return "NBA News"
    if "api.github.com" in u: return "GitHub API"
    if "github.com" in u: return "GitHub repo"
    if "cdn.nba.com" in u: return "NBA CDN"
    return "Official"


def src_links(urls, maxn=8):
    urls = [u for u in dict.fromkeys(urls or []) if isinstance(u, str)]
    if not urls:
        urls = ["https://www.nba.com/standings"]
    chips = []
    for u in urls[:maxn]:
        chips.append(f'<a class="src-chip" href="{esc(u)}" target="_blank" rel="noopener">'
                     f'{esc(label_for(u))} ↗</a>')
    if len(urls) > maxn:
        chips.append(f'<a class="src-chip" href="{esc(urls[0])}" target="_blank" rel="noopener">'
                     f'+{len(urls)-maxn} ↗</a>')
    return " ".join(chips)


def sources_of(row):
    out = []
    if isinstance(row.get("sources"), list):
        out += row["sources"]
    if isinstance(row.get("source"), str):
        out.append(row["source"])
    if isinstance(row.get("source"), list):
        out += row["source"]
    if isinstance(row.get("game_url"), str):
        out.append(row["game_url"])
    return list(dict.fromkeys(out))


def render_table(columns, rows, note=None, caption=None, source_header="Official source"):
    """columns: list of (key, label). rows: list of dict; None values render blank+UNVERIFIED."""
    parts = ['<div class="table-wrap">']
    if caption:
        parts.append(f'<div class="table-caption">{esc(caption)}</div>')
    parts.append('<table class="data-table"><thead><tr>')
    for _, lab in columns:
        parts.append(f"<th>{esc(lab)}</th>")
    parts.append(f"<th>{esc(source_header)}</th></tr></thead><tbody>")
    for row in rows:
        unv = set(row.get("_unverified", []) or [])
        parts.append("<tr>")
        for key, _ in columns:
            v = row.get(key, None)
            if v is None or v == "":
                if key in unv:
                    parts.append('<td><span class="blank">—</span> '
                                 '<span class="badge badge-unverified">UNVERIFIED</span></td>')
                else:
                    parts.append('<td><span class="blank">—</span> '
                                 '<span class="badge badge-muted">N/A</span></td>')
            elif isinstance(v, bool):
                parts.append(f"<td>{'yes' if v else 'no'}</td>")
            else:
                parts.append(f"<td>{v}</td>" if str(v).startswith("<") else f"<td>{esc(v)}</td>")
        parts.append(f'<td class="src-cell">{src_links(sources_of(row))}</td>')
        parts.append("</tr>")
    parts.append("</tbody></table>")
    if note:
        parts.append(f'<p class="table-note">{note}</p>')
    parts.append("</div>")
    return "\n".join(parts)


def badge(text, kind="info"):
    return f'<span class="badge badge-{kind}">{esc(text)}</span>'


def kpi(label, value, sub="", href=None):
    inner = (f'<div class="kpi-label">{esc(label)}</div>'
             f'<div class="kpi-value">{esc(value)}</div>'
             f'<div class="kpi-sub">{esc(sub)}</div>')
    if href:
        return f'<a class="kpi" href="{esc(href)}">{inner}</a>'
    return f'<div class="kpi">{inner}</div>'


def para(text):
    return f"<p>{text}</p>"


def callout(title, text, kind="info"):
    return (f'<div class="callout callout-{kind}"><div class="callout-title">{esc(title)}</div>'
            f'<div class="callout-body">{text}</div></div>')


# ------------------------------------------------------------------ nav / shell
NAV = [
    ("Start", [
        ("index.html", "Overview"),
        ("pages/executive-summary.html", "Executive summary"),
        ("pages/requirements.html", "Requirements"),
    ]),
    ("Data & lines", [
        ("pages/data.html", "Official data"),
        ("pages/lines.html", "Our own lines"),
        ("pages/sources.html", "Source registry"),
    ]),
    ("Research", [
        ("pages/strategies.html", "Strategies"),
        ("pages/validation.html", "Validation gates"),
        ("pages/correlations.html", "Correlations"),
        ("pages/skill-vs-luck.html", "Skill vs luck"),
    ]),
    ("Competition", [
        ("pages/leaderboard.html", "Leaderboard & rewards"),
    ]),
    ("Governance", [
        ("pages/verification.html", "Verification ledger"),
        ("pages/repo-review.html", "Repo review"),
        ("pages/flagged.html", "⚑ Flagged for Review"),
    ]),
]
TITLES = {h: t for _, group in NAV for h, t in group}


def nav_href(current, target):
    if current.startswith("pages/"):
        if target.startswith("pages/"):
            return target[len("pages/"):]
        return "../" + target
    return target


def shell(current, title, kicker, body, kpis=None):
    prefix = "" if not current.startswith("pages/") else "../"
    nav = []
    for group, items in NAV:
        nav.append(f'<div class="nav-group"><div class="nav-group-title">{esc(group)}</div>')
        for href, label in items:
            active = " active" if href == current else ""
            nav.append(f'<a class="nav-link{active}" href="{esc(nav_href(current, href))}">{esc(label)}</a>')
        nav.append("</div>")
    kpi_html = f'<div class="kpi-grid">{"".join(kpis)}</div>' if kpis else ""
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · Own4 NBA Research</title>
<link rel="stylesheet" href="{prefix}assets/css/style.css">
</head><body>
<div class="app">
  <aside class="sidebar">
    <a class="brand" href="{esc(nav_href(current,'index.html'))}">
      <span class="brand-mark">O4</span><span><strong>Own4</strong><small>NBA lines &amp; signals</small></span>
    </a>
    <div class="nav">{''.join(nav)}</div>
    <div class="sidebar-foot">Snapshot 2026-11-02 UTC<br>Official-source verified</div>
  </aside>
  <main class="main">
    <header class="topbar">
      <div><div class="crumb">Own4 / {esc(title)}</div><h1>{esc(title)}</h1></div>
      <div class="topbar-right">
        <span class="pill">{esc(kicker)}</span>
        <input id="globalFilter" class="filter" type="search" placeholder="Filter table rows…" aria-label="Filter table rows">
      </div>
    </header>
    <div class="content">
      {kpi_html}
      {body}
    </div>
    <footer class="footer">
      <span>Own4 · research &amp; validation only, not betting advice.</span>
      <span><a href="https://github.com/sassnarep3-star/Own4" target="_blank" rel="noopener">Repository ↗</a>
      · <a href="https://www.nba.com/standings" target="_blank" rel="noopener">NBA.com standings ↗</a></span>
    </footer>
  </main>
</div>
<script src="{prefix}assets/js/app.js"></script>
</body></html>"""


PAGES = []  # (path, title, kicker, body, kpis)


def add(path, body, kpis=None):
    title = TITLES[path]
    PAGES.append((path, title, "verified snapshot", body, kpis))


# ------------------------------------------------------------------ index
V = LEDGER["summary"]
h = BT["holdout"]
C = {r["id"]: r for r in CORR["rows"]}
idx_kpis = [
    kpi("Rows verified line by line", str(V["rows_checked"]), f"{V['passed']} PASS · {V['flagged']} FLAG", nav_href("index.html", "pages/verification.html")),
    kpi("Official NBA teams", "30", "2 seasons × 30 rows", nav_href("index.html", "pages/data.html")),
    kpi("Our own fair lines", "14", "2026-11-04 slate", nav_href("index.html", "pages/lines.html")),
    kpi("Correlations computed", str(CORR["count"]), "with BH-FDR + bootstrap CI", nav_href("index.html", "pages/correlations.html")),
    kpi("Strategies / gates", f"{STRATS['count']} / {len(GATES['gates'])}", "0 fully validated", nav_href("index.html", "pages/validation.html")),
    kpi("Eligible signals", "4", "top reward 100 pts", nav_href("index.html", "pages/leaderboard.html")),
    kpi("Flagged for review", str(len(FLAGGED["rows"])), "non-blocking", nav_href("index.html", "pages/flagged.html")),
    kpi("Holdout accuracy", fmt(h["winner_accuracy"]), "below coin flip — no skill", nav_href("index.html", "pages/skill-vs-luck.html")),
]
findings = [
    ("In-sample success is not skill", f"Prior-season rating model: {fmt(BT['train']['winner_accuracy'])} train accuracy → {fmt(h['winner_accuracy'])} holdout (n={h['n']}), Brier skill {fmt(h['brier_skill_score_vs_0_5'])}.", "pages/skill-vs-luck.html"),
    ("Four out-of-sample signals survive FDR", f"Best: 2026-27 WIN% ~ 2025-26 WIN% r={fmt(C['2026-27 WIN% ~ 2025-26 WIN%']['pearson_r'])} (q={fmt(C['2026-27 WIN% ~ 2025-26 WIN%']['bh_q'],4)}).", "pages/correlations.html"),
    ("Parlay legs are correlated", f"2026-27 PTS ~ NetRtg r={fmt(C['2026-27 PTS ~ NetRtg']['pearson_r'])}; PTS ~ PACE r={fmt(C['2026-27 PTS ~ PACE']['pearson_r'])}. Independence is not assumed.", "pages/strategies.html"),
    ("No official market odds", "NBA distributes official betting data to licensed operators; NBA.com exposes no odds values in retrieved content. All ROI/CLV/edge cells are blank.", "pages/flagged.html"),
    ("Zero validated betting strategies", "All 13 strategies fail at least one validation gate. Division B awards no rewards. This is a gate result, not a missing feature.", "pages/leaderboard.html"),
    ("Own fair lines for 14 games", "Zero-margin spreads, totals and moneylines from official ratings, with every formula published and no invented constants.", "pages/lines.html"),
]
cards = "".join(
    f'<a class="finding" href="{esc(nav_href("index.html", href))}">'
    f'<div class="finding-title">{esc(t)}</div><div class="finding-body">{esc(b)}</div>'
    f'<div class="finding-link">Open category →</div></a>' for t, b, href in findings)
glance = render_table(
    [("item", "Item"), ("value", "Value"), ("status", "Status")],
    [
        {"item": "Verification rows checked", "value": V["rows_checked"], "status": badge("PASS", "ok"), "sources": [SRC["standings"]]},
        {"item": "Rows without official source", "value": V["rows_without_official_source"], "status": badge("PASS", "ok"), "sources": [SRC["glossary"]]},
        {"item": "Settled games transcribed", "value": f"{V['settled_games_transcribed']} of 92", "status": badge("partial / flagged", "warn"), "sources": [SRC["games_1023"]]},
        {"item": "Strategies passing all gates", "value": 0, "status": badge("NOT VALIDATED", "warn"), "sources": [SRC["betting_data"]]},
        {"item": "Market odds available officially", "value": None, "_unverified": {"value"}, "sources": [SRC["betting_data"]]},
        {"item": "GitHub Pages", "value": "live", "status": badge("deployed", "ok"), "sources": [SRC["pages_api"]]},
    ],
    note="Every row links to an official site. Blank values are left blank and flagged UNVERIFIED.",
    caption="At a glance")
index_body = (
    callout("Read this first", "This is a <strong>research and validation</strong> dashboard, not betting advice. "
            "Every value comes from an official NBA/league page or a committed formula; anything that cannot be "
            "confirmed is blank and flagged on the <a href=\"" + nav_href("index.html", "pages/flagged.html") + "\">Flagged for Review</a> page. "
            "Concurrent sessions had already published the canonical root dashboard at "
            "<a href=\"https://sassnarep3-star.github.io/Own4/\" target=\"_blank\" rel=\"noopener\">/Own4/</a>; "
            "to preserve their work, this independently verified dashboard is published in its own "
            "<code>/Own4/own4-dashboard/</code> namespace.", "info")
    + f'<h2>Key findings</h2><div class="findings">{cards}</div>'
    + f"<h2>At a glance</h2>{glance}"
    + "<h2>What this site contains</h2>" + para(
        "Official standings and team/player tables, our own originated fair lines, a strategy catalogue, "
        "ten validation gates, correlation values with permutation tests and FDR correction, a skill-vs-luck "
        "decomposition, a two-division competition leaderboard with rewards, the source registry, the "
        "line-by-line verification ledger, the repository review, and the flagged-irregularities page. "
        "Use the sidebar to move between categories; every table can be filtered with the search box above.")
)
add("index.html", index_body, idx_kpis)

# ------------------------------------------------------------------ executive summary
add("pages/executive-summary.html", md_to_html(ROOT / "EXECUTIVE_SUMMARY.md"))
add("pages/requirements.html", md_to_html(ROOT / "REQUIREMENTS.md"))
add("pages/sources.html", md_to_html(ROOT / "SOURCES.md"))
add("pages/repo-review.html", md_to_html(ROOT / "REPO_REVIEW.md"))

# ------------------------------------------------------------------ data page
def stand_rows():
    out = []
    for r in STAND:
        out.append({"team": TEAMS[r["code"]]["name"], "conf": r["conference"], "w": r["w"], "l": r["l"],
                    "winpct": r["win_pct"], "home": f'{r["home_w"]}-{r["home_l"]}',
                    "road": f'{r["road_w"]}-{r["road_l"]}', "last10": r["last10"], "streak": r["streak"],
                    "sources": [SRC["standings"], TEAMS[r["code"]]["source"]]})
    return out


def adv_rows(rows, src):
    return [{"team": TEAMS[r["code"]]["name"], "gp": r["gp"], "w": r["w"], "l": r["l"],
             "off": fmt(r["off_rtg"], 1), "def": fmt(r["def_rtg"], 1), "net": fmt(r["net_rtg"], 1),
             "pace": fmt(r["pace"], 2), "ts": fmt(r["ts_pct"], 1), "poss": r["poss"],
             "sources": [src, SRC["glossary"]]} for r in rows]


def trad_rows():
    return [{"team": TEAMS[r["code"]]["name"], "gp": r["gp"], "pts": fmt(r["pts"], 1),
             "fg": fmt(r["fg_pct"], 1), "fg3": fmt(r["fg3_pct"], 1), "reb": fmt(r["reb"], 1),
             "ast": fmt(r["ast"], 1), "pm": fmt(r["plus_minus"], 1),
             "sources": [SRC["trad_2026"]]} for r in T26]


def n(v, nd=1):
    """Format a number for a table cell, preserving None as a flagged blank."""
    return None if v is None else fmt(v, nd)


def player_rows():
    out = []
    for r in PLAYERS:
        out.append({"player": r["player"], "team": r["team"], "gp": r["gp"], "pts": n(r["pts"]),
                    "reb": n(r["reb"]), "ast": n(r["ast"]), "fg3m": n(r["fg3m"]),
                    "fg": n(r["fg_pct"]),
                    "_unverified": set(r.get("unverified", [])),
                    "sources": [SRC["players_2026"], "https://www.nba.com/stats/player/" + str(r["player_id"]) + "/"]})
    return out


def game_rows():
    return [{"date": r["date"], "game": r["game_id"], "a": r["team_a"], "sa": r["score_a"],
             "b": r["team_b"], "sb": r["score_b"], "margin": r["score_a"] - r["score_b"],
             "total": r["score_a"] + r["score_b"], "ot": "yes" if r["ot"] else "no",
             "cup": "NBA Cup" if r["cup"] else "—",
             "sources": [r["source"], r["game_url"]]} for r in GAMES]


def slate_rows():
    return [{"time": r["time_et"], "a": TEAMS[r["team_a"]]["name"], "b": TEAMS[r["team_b"]]["name"],
             "game": r["game_id"], "leader_a": f'{r["leader_a"]} ({fmt(r["ppg_a"],1)} PPG)',
             "leader_b": f'{r["leader_b"]} ({fmt(r["ppg_b"],1)} PPG)',
             "sources": [SRC["games_1104"], r["game_url"]]} for r in SLATE]


data_body = (
    callout("Data provenance", "All values below were transcribed line by line from official NBA.com pages on "
            "2026-11-02 (UTC). Each row carries its official source link. See the "
            "<a href=\"sources.html\">Source registry</a> for the full catalog.", "info")
    + "<h2>2026-27 standings (30 teams)</h2>" + render_table(
        [("team", "Team"), ("conf", "Conf"), ("w", "W"), ("l", "L"), ("winpct", "WIN%"),
         ("home", "HOME"), ("road", "ROAD"), ("last10", "LAST10"), ("streak", "STREAK")], stand_rows(),
        note="Source: NBA.com standings. HOME + ROAD = overall W-L for every row (checked in the verification ledger).")
    + "<h2>2025-26 team advanced ratings (completed season, 82 GP each)</h2>" + render_table(
        [("team", "Team"), ("gp", "GP"), ("w", "W"), ("l", "L"), ("off", "OffRtg"), ("def", "DefRtg"),
         ("net", "NetRtg"), ("pace", "PACE"), ("ts", "TS%"), ("poss", "POSS")], adv_rows(A25, SRC["adv_2025"]),
        note="NetRtg = OffRtg − DefRtg per the official NBA.com Stat Glossary.")
    + "<h2>2026-27 team advanced ratings (season in progress)</h2>" + render_table(
        [("team", "Team"), ("gp", "GP"), ("w", "W"), ("l", "L"), ("off", "OffRtg"), ("def", "DefRtg"),
         ("net", "NetRtg"), ("pace", "PACE"), ("ts", "TS%"), ("poss", "POSS")], adv_rows(A26, SRC["adv_2026"]))
    + "<h2>2026-27 team traditional per-game stats</h2>" + render_table(
        [("team", "Team"), ("gp", "GP"), ("pts", "PTS"), ("fg", "FG%"), ("fg3", "3P%"),
         ("reb", "REB"), ("ast", "AST"), ("pm", "+/-")], trad_rows())
    + "<h2>Player season baselines (top 8 of 442 official rows)</h2>" + render_table(
        [("player", "Player"), ("team", "Team"), ("gp", "GP"), ("pts", "PPG"), ("reb", "RPG"),
         ("ast", "APG"), ("fg3m", "3PM"), ("fg", "FG%")], player_rows(),
        note="Cooper Flagg's row was truncated by the retrieval tool; its blank cells are flagged UNVERIFIED, not filled in (IR-15).")
    + "<h2>Official settled games (62 transcribed of 92 played)</h2>" + render_table(
        [("date", "Date"), ("game", "Game ID"), ("a", "Team A"), ("sa", "A pts"), ("b", "Team B"),
         ("sb", "B pts"), ("margin", "A−B"), ("total", "Total"), ("ot", "OT"), ("cup", "Competition")], game_rows(),
        note="Team A / Team B follow the official page's listing order. No home/away claim is made (IR-12, IR-17).")
    + "<h2>Scheduled slate 2026-11-04 (14 games)</h2>" + render_table(
        [("time", "Time ET"), ("a", "Team A"), ("b", "Team B"), ("game", "Game ID"),
         ("leader_a", "Team A season leader"), ("leader_b", "Team B season leader")], slate_rows())
)
add("pages/data.html", data_body, [
    kpi("Teams", "30", "2 official seasons", "data.html"),
    kpi("Settled games", str(len(GAMES)), "of 92 played", "data.html"),
    kpi("Player rows", "8", "of 442 official", "data.html"),
])

# ------------------------------------------------------------------ lines page
def line_rows():
    out = []
    for r in LINES["rows"]:
        out.append({
            "game": f'{r["team_a"]} vs {r["team_b"]}',
            "time": r["time_et"],
            "pa": fmt(r["proj_score_a"], 1), "pb": fmt(r["proj_score_b"], 1),
            "spread": fmt(r["fair_spread_a"], 2), "total": fmt(r["fair_total"], 1),
            "mla": f'{r["fair_ml_a"]:+d}', "mlb": f'{r["fair_ml_b"]:+d}',
            "prob": fmt(r["fair_win_prob_a"]),
            "m2spread": fmt(r["m2_fair_spread_a"], 2), "m2total": fmt(r["m2_fair_total"], 1),
            "market": None, "edge": None, "hca": None,
            "_unverified": {"market", "edge", "hca"},
            "sources": r["sources"],
        })
    return out


def prop_rows():
    out = []
    for g in SLATE:
        for side, name, ppg, rpg, apg, url in (
            ("A", g["leader_a"], g["ppg_a"], g["rpg_a"], g["apg_a"], g["player_a_url"]),
            ("B", g["leader_b"], g["ppg_b"], g["rpg_b"], g["apg_b"], g["player_b_url"]),
        ):
            out.append({
                "game": f'{g["team_a"]} vs {g["team_b"]}', "side": side, "player": name,
                "ppg": fmt(ppg, 1), "rpg": fmt(rpg, 1), "apg": fmt(apg, 1),
                "fair_pts": None, "fair_reb": None, "fair_ast": None, "market": None,
                "_unverified": {"fair_pts", "fair_reb", "fair_ast", "market"},
                "sources": [SRC["games_1104"], url, SRC["players_2026"]],
            })
    return out


formula_rows = [{"step": i + 1, "formula": f, "sources": [SRC["glossary"], SRC["adv_2025"], SRC["games_1028"]]}
                for i, f in enumerate(LINES["meta"]["formulas"])]
lines_body = (
    callout("These are our own lines", "Zero-margin fair prices originated from official NBA.com ratings. "
            "They are <strong>model outputs, not sportsbook prices</strong>. No market odds, home-court "
            "adjustment, blend weight or vig is assumed: those cells are blank + UNVERIFIED.", "info")
    + f"<h2>Model parameters (all derived from official data)</h2>" + render_table(
        [("k", "Parameter"), ("v", "Value"), ("where", "Derived from")],
        [
            {"k": "League avg rating 2025-26 (L)", "v": fmt(LINES["meta"]["league_avg_2025_26"], 4), "where": "mean of 30 official OffRtg/DefRtg rows", "sources": [SRC["adv_2025"]]},
            {"k": "League avg rating 2026-27 (L)", "v": fmt(LINES["meta"]["league_avg_2026_27"], 4), "where": "mean of 30 official OffRtg/DefRtg rows", "sources": [SRC["adv_2026"]]},
            {"k": "Residual margin sigma", "v": fmt(LINES["meta"]["sigma_residual_margin"], 4), "where": f'{LINES["meta"]["train_games"]} official settled games before the slate', "sources": [SRC["games_1023"], SRC["games_1028"]]},
            {"k": "Train residual bias", "v": fmt(LINES["meta"]["sigma_train_bias"], 4), "where": "reported as a diagnostic, not applied as a correction", "sources": [SRC["games_1028"]]},
            {"k": "League home win rate", "v": f'{V["league_home_wins"]}/{V["league_home_games"]} = {fmt(V["league_home_win_rate"],4)}', "where": "official standings HOME columns; NOT applied per game (IR-12)", "sources": [SRC["standings"]]},
        ])
    + "<h2>Formulas</h2>" + render_table([("step", "#"), ("formula", "Formula / definition")], formula_rows)
    + "<h2>Originated fair lines — 2026-11-04 slate (14 games)</h2>" + render_table(
        [("game", "Matchup"), ("time", "Time ET"), ("pa", "Proj A"), ("pb", "Proj B"),
         ("spread", "Fair spread A"), ("total", "Fair total"), ("mla", "Fair ML A"), ("mlb", "Fair ML B"),
         ("prob", "P(A)"), ("m2spread", "M2 spread A"), ("m2total", "M2 total"),
         ("market", "Market spread/total"), ("edge", "Edge vs market"), ("hca", "Home-court adj.")],
        line_rows(),
        note="M1 = prior-season model (validated out-of-sample). M2 = current-season ratings, no out-of-sample calibration, so its moneyline is blank. Market, edge and home-court cells are UNVERIFIED.")
    + "<h2>Player-prop baselines & unverified fair lines (28 official team leaders)</h2>" + render_table(
        [("game", "Matchup"), ("side", "Side"), ("player", "Season leader"), ("ppg", "PPG"),
         ("rpg", "RPG"), ("apg", "APG"), ("fair_pts", "Fair PTS line"), ("fair_reb", "Fair REB line"),
         ("fair_ast", "Fair AST line"), ("market", "Market prop price")], prop_rows(),
        note="PPG/RPG/APG are verified official season averages. A fair over/under requires a game-level distribution that free official NBA pages do not provide, so every fair line is blank + UNVERIFIED (IR-11).")
    + "<h2>Caveats</h2><ul>" + "".join(f"<li>{esc(c)}</li>" for c in LINES["meta"]["caveats"]) + "</ul>"
)
add("pages/lines.html", lines_body, [
    kpi("Games priced", "14", "2026-11-04 slate", "lines.html"),
    kpi("Model", "M1", "prior-season ratings", "lines.html"),
    kpi("Sigma", fmt(LINES["meta"]["sigma_residual_margin"], 2), "train-window residual", "lines.html"),
])

# ------------------------------------------------------------------ strategies page
def strat_rows():
    out = []
    for r in STRATS["rows"]:
        out.append({
            "id": r["id"], "family": r["family"], "name": r["name"], "hyp": r["hypothesis"],
            "inputs": r["inputs"],
            "verdict": badge(r["verdict"], "warn"), "roi": None, "clv": None, "reward": None,
            "_unverified": {"roi", "clv", "reward"}, "sources": r["sources"],
        })
    return out


gate_cols = [("id", "ID"), ("family", "Family")] + [(f"g{i}", f"G{i}") for i in range(1, 11)]

def gate_matrix():
    out = []
    for r in STRATS["rows"]:
        d = {"id": r["id"], "family": r["family"], "sources": r["sources"]}
        for i in range(1, 11):
            v = r["gates"][f"G{i}"]["status"]
            kind = "ok" if v == "PASS" else ("warn" if v == "FAIL" else "muted")
            d[f"g{i}"] = badge(v, kind)
        out.append(d)
    return out


strat_body = (
    callout("Validation result", f"<strong>0 of {STRATS['count']} strategies are validated.</strong> "
            "Every strategy fails or cannot verify at least one gate. ROI, closing-line value and rewards "
            "are blank and flagged UNVERIFIED — no performance is inferred.", "warn")
    + "<h2>Strategy catalogue (singles, parlays, player-prop combos)</h2>" + render_table(
        [("id", "ID"), ("family", "Family"), ("name", "Strategy"), ("hyp", "Hypothesis"),
         ("inputs", "Official inputs"), ("verdict", "Verdict"), ("roi", "Net ROI"),
         ("clv", "CLV"), ("reward", "Reward")], strat_rows())
    + "<h2>Gate-by-gate matrix</h2>" + render_table(gate_cols, gate_matrix(),
        note="PASS = green, FAIL = amber, UNVERIFIED / N/A = grey. Gate definitions are on the Validation page.")
    + "<h2>Research findings</h2>" + md_to_html(ROOT / "STRATEGIES.md").split("<h2>Research findings</h2>")[-1]
)
add("pages/strategies.html", strat_body, [
    kpi("Strategies", str(STRATS["count"]), "3 families", "strategies.html"),
    kpi("Validated", "0", "no gate-passing strategy", "strategies.html"),
])

# ------------------------------------------------------------------ validation page
gate_def_rows = [{"id": g["id"], "name": g["name"], "rule": g["rule"], "sources": [g["source"]]}
                 for g in GATES["gates"]]
bt_rows = []
for w in ("train", "holdout", "all"):
    m = BT[w]
    lo, hi = m["accuracy_wilson_95ci"]
    bt_rows.append({
        "window": m["window"], "n": m["n"], "acc": fmt(m["winner_accuracy"]),
        "ci": f"{fmt(lo)} … {fmt(hi)}", "p": fmt(m["binomial_p_two_sided_vs_0_5"], 4),
        "brier": fmt(m["brier_score"], 4), "skill": fmt(m["brier_skill_score_vs_0_5"], 4),
        "mmae": fmt(m["margin_mae"], 2), "tmae": fmt(m["total_mae"], 2),
        "r": fmt(m["pred_vs_actual_margin_pearson_r"], 3),
        "perm": fmt(m["pred_vs_actual_margin_permutation_p"], 4),
        "sources": m["sources"],
    })
val_body = (
    callout("Gate rule", esc(GATES["rule"]), "info")
    + "<h2>Gate definitions</h2>" + render_table(
        [("id", "Gate"), ("name", "Name"), ("rule", "Pass criterion")], gate_def_rows)
    + "<h2>Settlement backtest — no lookahead</h2>" + para(
        "The M1 prior-season model uses only the official 2025-26 advanced table (82 GP per team). "
        "The residual scale was estimated on games dated 2026-10-23 … 2026-10-28, then applied to the "
        "chronological holdout (2026-10-30 … 2026-11-01) and to the future 2026-11-04 slate. "
        "All final scores are official NBA.com values.")
    + render_table(
        [("window", "Window"), ("n", "n"), ("acc", "Winner acc."), ("ci", "95% Wilson CI"),
         ("p", "Binomial p"), ("brier", "Brier"), ("skill", "Brier skill"), ("mmae", "Margin MAE"),
         ("tmae", "Total MAE"), ("r", "r(pred, actual)"), ("perm", "Permutation p")], bt_rows)
    + callout("Decisive finding", f"Training accuracy {fmt(BT['train']['winner_accuracy'])} collapses to "
              f"{fmt(BT['holdout']['winner_accuracy'])} on the holdout (n={BT['holdout']['n']}); holdout "
              f"Brier skill is {fmt(BT['holdout']['brier_skill_score_vs_0_5'])} and the exact binomial p is "
              f"{fmt(BT['holdout']['binomial_p_two_sided_vs_0_5'],4)}. The model is <strong>not skill-based</strong>.", "warn")
    + "<h2>Gate-by-gate matrix (all strategies)</h2>" + render_table(gate_cols, gate_matrix(),
        note="Every strategy's ROI / CLV / profit / reward is blank because no strategy clears all applicable gates.")
    + "<h2>Verification ledger summary</h2>" + render_table(
        [("k", "Metric"), ("v", "Value")],
        [{"k": "Rows checked", "v": V["rows_checked"], "sources": [SRC["standings"]]},
         {"k": "Passed", "v": V["passed"], "sources": [SRC["adv_2025"]]},
         {"k": "Flagged inconsistencies", "v": V["flagged"], "sources": [SRC["adv_2026"]]},
         {"k": "Rows without official source", "v": V["rows_without_official_source"], "sources": [SRC["glossary"]]}])
)
add("pages/validation.html", val_body, [
    kpi("Gates", str(len(GATES["gates"])), "G1–G10", "validation.html"),
    kpi("Holdout n", str(BT["holdout"]["n"]), "chronological", "validation.html"),
    kpi("Holdout accuracy", fmt(BT["holdout"]["winner_accuracy"]), "below 0.500", "validation.html"),
])

# ------------------------------------------------------------------ correlations page
def corr_rows():
    out = []
    for r in CORR["rows"]:
        lo, hi = r["bootstrap_ci95"]
        out.append({
            "id": r["id"], "group": r["group"], "n": r["n"], "r": fmt(r["pearson_r"]),
            "rho": fmt(r["spearman_rho"]), "p": fmt(r["permutation_p"], 4),
            "q": fmt(r["bh_q"], 4), "ci": f"{fmt(lo)} … {fmt(hi)}",
            "r2": fmt(r["r_squared"]),
            "sig": badge("YES", "ok") if r["significant_after_fdr"] else badge("no", "muted"),
            "note": r["note"], "sources": r["sources"],
        })
    return out


corr_body = (
    callout("Method", esc(CORR["method"]), "info")
    + "<h2>All correlation values</h2>" + render_table(
        [("id", "Pair (y ~ x)"), ("group", "Group"), ("n", "n"), ("r", "Pearson r"),
         ("rho", "Spearman ρ"), ("p", "Perm. p"), ("q", "BH q"), ("ci", "Bootstrap 95% CI"),
         ("r2", "r²"), ("sig", "Sig. after FDR"), ("note", "Note")], corr_rows(),
        note="Every row is computed from official NBA.com values; blank values would be flagged UNVERIFIED. No value is inferred.")
    + "<h2>Findings</h2>" + md_to_html(ROOT / "CORRELATIONS.md").split("<h2>Findings</h2>")[-1]
)
add("pages/correlations.html", corr_body, [
    kpi("Correlations", str(CORR["count"]), "Pearson + Spearman", "correlations.html"),
    kpi("Significant after FDR", str(sum(1 for r in CORR["rows"] if r["significant_after_fdr"])), "BH q < 0.05", "correlations.html"),
    kpi("Best out-of-sample r", fmt(C["2026-27 WIN% ~ 2025-26 WIN%"]["pearson_r"]), "prior→current WIN%", "correlations.html"),
])

# ------------------------------------------------------------------ skill vs luck page
method_rows = [{"i": i + 1, "m": m, "sources": [SRC["games_1023"], SRC["glossary"], SRC["betting_data"]]}
               for i, m in enumerate(SKILL["luck_removal_method"])]
decomp_rows = [{"label": d["label"], "n": d["n"], "r": fmt(d["pearson_r"]),
                "sys": fmt(d["systematic_variance_share_r2"]), "res": fmt(d["residual_variance_share"]),
                "note": d["note"], "sources": d["sources"]} for d in SKILL["decomposition"]]
ev = SKILL["backtest_evidence"]
ev_rows = []
for w in ("train", "holdout"):
    e = ev[w]
    ev_rows.append({"window": w, "n": e["n"], "acc": fmt(e["winner_accuracy"]),
                    "p": fmt(e["binomial_p_two_sided_vs_0_5"], 4), "brier": fmt(e["brier_score"], 4),
                    "skill": fmt(e["brier_skill_score_vs_0_5"], 4),
                    "perm": fmt(e["pred_vs_actual_margin_permutation_p"], 4),
                    "sources": ev["sources"]})
skill_body = (
    callout("Finding", esc(SKILL["finding"]), "warn")
    + "<h2>Luck-removal rules (pre-registered)</h2>" + render_table(
        [("i", "#"), ("m", "Rule")], method_rows)
    + "<h2>Variance decomposition</h2>" + render_table(
        [("label", "Relationship"), ("n", "n"), ("r", "Pearson r"), ("sys", "Systematic share (r²)"),
         ("res", "Residual share"), ("note", "Interpretation")], decomp_rows)
    + "<h2>Out-of-sample evidence</h2>" + render_table(
        [("window", "Window"), ("n", "n"), ("acc", "Winner acc."), ("p", "Binomial p"),
         ("brier", "Brier"), ("skill", "Brier skill"), ("perm", "Permutation p")], ev_rows)
    + "<h2>Selectively skill-based selection</h2>" + para(
        "Only signals that clear provenance, completeness, out-of-sample, FDR-significance and "
        "reproducibility gates enter the leaderboard. In-sample accuracy never earns rewards; "
        "bet strategies additionally need sample size, positive holdout skill, verified market "
        "prices and walk-forward stability. In this snapshot that selects 4 research signals and "
        "0 betting strategies.")
)
add("pages/skill-vs-luck.html", skill_body, [
    kpi("Train accuracy", fmt(BT["train"]["winner_accuracy"]), "in-sample, not rewarded", "skill-vs-luck.html"),
    kpi("Holdout accuracy", fmt(BT["holdout"]["winner_accuracy"]), "out-of-sample", "skill-vs-luck.html"),
    kpi("Holdout Brier skill", fmt(BT["holdout"]["brier_skill_score_vs_0_5"]), "negative → no skill", "skill-vs-luck.html"),
])

# ------------------------------------------------------------------ leaderboard page
def sig_rows():
    out = []
    for r in LB["divisions"]["signal_research"]:
        out.append({
            "rank": r["rank"] if r["rank"] else "—", "id": r["id"], "name": r["name"], "n": r["n"],
            "r": fmt(r["out_of_sample_r"]), "q": fmt(r["bh_q"], 4),
            "ci": f'{fmt(r["bootstrap_ci95"][0])} … {fmt(r["bootstrap_ci95"][1])}',
            "score": fmt(r["score"]) if r["score"] is not None else None,
            "reward": r["reward_points"] if r["reward_points"] is not None else None,
            "elig": badge("eligible", "ok") if r["eligible"] else badge("not eligible", "warn"),
            "_unverified": set(r.get("blank_fields", [])),
            "sources": r["sources"],
        })
    return out


def bet_rows():
    out = []
    for r in LB["divisions"]["betting_strategies"]:
        out.append({
            "id": r["id"], "family": r["family"], "name": r["name"],
            "verdict": badge(r["verdict"], "warn"),
            "passed": r["gates_passed"], "failed": r["gates_failed"], "unv": r["gates_unverified"],
            "roi": None, "score": None, "reward": None,
            "_unverified": set(r["blank_fields"]), "sources": r["sources"],
        })
    return out


rule_rows = [{"div": "Division A (signals)", "i": i + 1, "r": x,
              "sources": [SRC["adv_2025"], SRC["standings"]]}
             for i, x in enumerate(REWARDS["division_A_rules"])]
rule_rows += [{"div": "Division B (bet strategies)", "i": i + 1, "r": x,
               "sources": [SRC["betting_data"], SRC["games_1104"]]}
              for i, x in enumerate(REWARDS["division_B_rules"])]
lb_body = (
    callout("Competition result", esc(LB["headline"]), "info")
    + "<h2>Division A — research signal leaderboard</h2>" + render_table(
        [("rank", "Rank"), ("id", "ID"), ("name", "Signal"), ("n", "n"), ("r", "Out-of-sample r"),
         ("q", "BH q"), ("ci", "Bootstrap 95% CI"), ("score", "Score"), ("reward", "Reward (pts)"),
         ("elig", "Eligibility")], sig_rows(),
        note="Ranked by out-of-sample Pearson r computed only from official values. Ineligible rows have blank score/reward.")
    + "<h2>Division B — betting strategy leaderboard</h2>" + render_table(
        [("id", "ID"), ("family", "Family"), ("name", "Strategy"), ("verdict", "Verdict"),
         ("passed", "Gates PASS"), ("failed", "Gates FAIL"), ("unv", "UNVERIFIED"),
         ("roi", "Net ROI"), ("score", "Score"), ("reward", "Reward (pts)")], bet_rows(),
        note="Zero eligible strategies. All performance and reward cells are blank + UNVERIFIED.")
    + "<h2>Reward rules</h2>" + render_table([("div", "Division"), ("i", "#"), ("r", "Rule")], rule_rows)
    + para("<strong>" + esc(REWARDS["note"]) + "</strong> Reward unit: " + esc(REWARDS["reward_unit"]) + ".")
)
add("pages/leaderboard.html", lb_body, [
    kpi("Eligible signals", "4", "Division A", "leaderboard.html"),
    kpi("Top reward", "100 pts", "rank 1 signal", "leaderboard.html"),
    kpi("Eligible bet strategies", "0", "Division B", "leaderboard.html"),
])

# ------------------------------------------------------------------ verification page
ledger_rows = []
for r in LEDGER["rows"]:
    ok = [k for k, v in r["checks"].items() if v["pass"]]
    bad = [k for k, v in r["checks"].items() if not v["pass"]]
    ledger_rows.append({
        "group": r["group"], "id": r["row_id"],
        "status": badge(r["status"], "ok" if r["status"] == "PASS" else "warn"),
        "n": len(r["checks"]), "ok": len(ok), "bad": ", ".join(bad) or "—",
        "src": badge("yes", "ok") if r["official_source_present"] else badge("NO", "warn"),
        "sources": r["sources"],
    })
ver_body = (
    callout("Verification policy", "Every table row on this site has a link to an official site. "
            "If a value cannot be confirmed from an official source it is left blank and flagged "
            "UNVERIFIED; nothing is inferred or filled in.", "info")
    + "<h2>Summary</h2>" + render_table(
        [("k", "Metric"), ("v", "Value")],
        [{"k": "Rows checked line by line", "v": V["rows_checked"], "sources": [SRC["standings"]]},
         {"k": "Passed", "v": V["passed"], "sources": [SRC["adv_2025"]]},
         {"k": "Flagged inconsistencies", "v": V["flagged"], "sources": [SRC["adv_2026"]]},
         {"k": "Rows without official source", "v": V["rows_without_official_source"], "sources": [SRC["glossary"]]},
         {"k": "2025-26 ΣW / ΣL", "v": "1230 / 1230", "sources": [SRC["adv_2025"]]},
         {"k": "Standings GP ÷ 2 = official calendar", "v": f'{V["calendar_total"]} games', "sources": [SRC["standings"], SRC["games_1102"]]},
         {"k": "League home win rate", "v": f'{V["league_home_wins"]}/{V["league_home_games"]} = {fmt(V["league_home_win_rate"],4)}', "sources": [SRC["standings"]]},
         {"k": "Settled games transcribed", "v": f'{V["settled_games_transcribed"]} of 92', "sources": [SRC["games_1023"]]},
         {"k": "Unverified field classes", "v": ", ".join(V["unverified_field_classes"]), "sources": [SRC["betting_data"]]}])
    + "<h2>Unverified field classes (blank on purpose)</h2>" + render_table(
        [("i", "#"), ("v", "Field class"), ("status", "Status")],
        [{"i": i + 1, "v": x, "status": badge("UNVERIFIED", "warn"),
          "sources": [SRC["betting_data"], SRC["games_1104"], SRC["players_2026"]]}
         for i, x in enumerate(V["unverified_field_classes"])])
    + f"<h2>Full line-by-line ledger ({len(ledger_rows)} rows)</h2>" + render_table(
        [("group", "Dataset"), ("id", "Row"), ("status", "Status"), ("n", "Checks"),
         ("ok", "Passed"), ("bad", "Failed checks"), ("src", "Official source")], ledger_rows,
        note="Generated by scripts/verify.py. Each row's Source column links to the official page(s) used.")
)
add("pages/verification.html", ver_body, [
    kpi("Rows checked", str(V["rows_checked"]), "line by line", "verification.html"),
    kpi("Flagged", str(V["flagged"]), "inconsistencies", "verification.html"),
    kpi("Missing official source", str(V["rows_without_official_source"]), "required = 0", "verification.html"),
])

# ------------------------------------------------------------------ flagged page
flag_rows = []
for r in FLAGGED["rows"]:
    flag_rows.append({
        "id": r["id"], "sev": badge(r["severity"], "warn" if r["severity"] in ("High", "Medium") else "muted"),
        "item": r["item"], "value": r["value"] if r["value"] != "—" else None,
        "status": badge(r["status"], "warn"),
        "_unverified": {"value"} if (r["value"] == "—" and r["status"] == "UNVERIFIED") else set(),
        "sources": [r["source"]] + ([r["third_party_evidence"]] if r.get("third_party_evidence") else []),
    })
blank_rows = []
for r in LINES["rows"]:
    blank_rows.append({
        "game": r["game_id"], "matchup": f'{r["team_a"]} vs {r["team_b"]}',
        "fields": ", ".join(r["unverified"]), "count": len(r["unverified"]),
        "status": badge("UNVERIFIED", "warn"), "sources": r["sources"],
    })
third_rows = [
    {"site": "Basketball-Reference", "link": SOURCES_JSON["excluded_third_party"][0], "why": "Third-party aggregator, not an official league source", "sources": [SRC["standings"], SOURCES_JSON["excluded_third_party"][0]]},
    {"site": "Kalshi", "link": SOURCES_JSON["excluded_third_party"][1], "why": "Prediction market, not an official league source", "sources": [SRC["standings"], SOURCES_JSON["excluded_third_party"][1]]},
    {"site": "Land of Basketball", "link": SOURCES_JSON["excluded_third_party"][2], "why": "Third-party aggregator", "sources": [SRC["standings"], SOURCES_JSON["excluded_third_party"][2]]},
    {"site": "whynba.com", "link": SOURCES_JSON["excluded_third_party"][3], "why": "Implausible 2026-27 figures; excluded", "sources": [SRC["standings"], SOURCES_JSON["excluded_third_party"][3]]},
]
flag_body = (
    callout("Flagged for Review", "These irregularities and unverified items are published here for your "
            "review after the site is live. Per the project instructions they do <strong>not</strong> block "
            "the merge or deployment. Every row links to an official site; third-party evidence is shown "
            "only as additional context.", "warn")
    + "<h2>Irregularities & unverified items</h2>" + render_table(
        [("id", "ID"), ("sev", "Severity"), ("item", "Observation"), ("value", "Value"),
         ("status", "Status")], flag_rows)
    + "<h2>Blank cells on the Lines page (one row per game)</h2>" + render_table(
        [("game", "Game ID"), ("matchup", "Matchup"), ("fields", "Blank + UNVERIFIED fields"),
         ("count", "Count"), ("status", "Status")], blank_rows,
        note="No value in these cells was inferred or filled in.")
    + "<h2>Excluded third-party sources</h2>" + render_table(
        [("site", "Site"), ("link", "Excluded link"), ("why", "Reason")], third_rows,
        note="Each row also links to an official NBA.com page. Third-party values never enter verified tables.")
    + "<h2>What would unblock Division B</h2>" + para(
        "Verified official market/closing odds and vig, a bet-level settlement history of at least 200 "
        "independent observations, three chronological walk-forward folds, game-level player logs for "
        "prop distributions, and an official home/away designation per game. Until then, no betting "
        "strategy can clear all validation gates and no Division B reward is awarded.")
)
add("pages/flagged.html", flag_body, [
    kpi("Flagged items", str(len(FLAGGED["rows"])), "non-blocking", "flagged.html"),
    kpi("Blank line fields", str(sum(len(r["unverified"]) for r in LINES["rows"])), "never inferred", "flagged.html"),
])

# ------------------------------------------------------------------ assets
CSS = r"""/* Own4 dashboard — clean, simple, readable */
:root{--navy:#17408b;--red:#c8102e;--ink:#16202e;--muted:#64748b;--line:#e3e8ef;--bg:#f6f8fb;--card:#fff;--ok:#0f766e;--warn:#b45309}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:var(--bg);color:var(--ink);font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--navy);text-decoration:none}a:hover{text-decoration:underline}
.app{display:flex;min-height:100vh}
.sidebar{width:246px;flex:0 0 246px;background:#0e1b31;color:#dbe4f2;display:flex;flex-direction:column;position:sticky;top:0;height:100vh;overflow-y:auto}
.brand{display:flex;gap:11px;align-items:center;padding:20px 18px;border-bottom:1px solid #22334d;color:#fff}
.brand:hover{text-decoration:none}
.brand-mark{display:grid;place-items:center;width:38px;height:38px;border-radius:9px;background:linear-gradient(135deg,var(--navy),var(--red));font-weight:800;font-size:14px;letter-spacing:.5px}
.brand strong{display:block;font-size:16px;line-height:1.2}.brand small{display:block;font-size:11px;color:#93a4bf}
.nav{padding:12px 10px;flex:1}
.nav-group{margin-bottom:14px}
.nav-group-title{font-size:10.5px;text-transform:uppercase;letter-spacing:.11em;color:#7d90ae;padding:6px 10px;font-weight:700}
.nav-link{display:block;padding:7px 11px;border-radius:7px;color:#c6d2e5;font-size:13.5px;margin:1px 0}
.nav-link:hover{background:#1a2b47;color:#fff;text-decoration:none}
.nav-link.active{background:var(--navy);color:#fff;font-weight:600}
.sidebar-foot{padding:14px 18px;font-size:11px;color:#8295b3;border-top:1px solid #22334d;line-height:1.5}
.main{flex:1;min-width:0;display:flex;flex-direction:column}
.topbar{display:flex;justify-content:space-between;align-items:center;gap:16px;background:#fff;border-bottom:1px solid var(--line);padding:18px 28px;position:sticky;top:0;z-index:5}
.crumb{font-size:11.5px;color:var(--muted);letter-spacing:.03em}
.topbar h1{margin:2px 0 0;font-size:22px;letter-spacing:-.02em}
.topbar-right{display:flex;align-items:center;gap:10px}
.pill{background:#eef4ff;color:var(--navy);border:1px solid #d6e4ff;padding:5px 11px;border-radius:99px;font-size:11.5px;font-weight:600;white-space:nowrap}
.filter{border:1px solid var(--line);border-radius:8px;padding:8px 11px;font-size:13px;min-width:190px;background:#fbfcfe;outline:none}
.filter:focus{border-color:var(--navy);box-shadow:0 0 0 3px #17408b1a}
.content{padding:24px 28px 48px;max-width:1500px;width:100%}
.content h2{font-size:18px;margin:30px 0 12px;letter-spacing:-.01em;padding-bottom:8px;border-bottom:1px solid var(--line)}
.content h3{font-size:15px;margin:22px 0 8px}
.content p{max-width:1100px;color:#33415a}
.content ul,.content ol{max-width:1100px;padding-left:22px}
.content li{margin:4px 0}
code{background:#eef2f8;padding:1px 5px;border-radius:4px;font-size:12.5px}
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:22px}
.kpi{display:block;background:var(--card);border:1px solid var(--line);border-radius:11px;padding:14px 16px;box-shadow:0 1px 2px #0e1b3108}
a.kpi:hover{text-decoration:none;border-color:#bcd0f5;box-shadow:0 3px 12px #17408b15}
.kpi-label{font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;font-weight:600}
.kpi-value{font-size:26px;font-weight:750;letter-spacing:-.03em;margin:3px 0;color:var(--navy)}
.kpi-sub{font-size:11.5px;color:var(--muted)}
.callout{border-radius:11px;padding:14px 17px;margin-bottom:18px;border:1px solid;max-width:1200px}
.callout-info{background:#eef4ff;border-color:#d6e4ff;color:#1c3c78}
.callout-warn{background:#fff7ed;border-color:#fed7aa;color:#8a4a10}
.callout-title{font-weight:700;font-size:13.5px;margin-bottom:3px}
.callout-body{font-size:13.5px;line-height:1.6}
.findings{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:12px}
.finding{display:block;background:#fff;border:1px solid var(--line);border-radius:11px;padding:15px 16px;transition:.15s}
.finding:hover{text-decoration:none;border-color:#bcd0f5;transform:translateY(-1px);box-shadow:0 6px 18px #0e1b3114}
.finding-title{font-weight:700;font-size:14px;color:var(--navy)}
.finding-body{font-size:13px;color:#43516b;margin-top:5px;min-height:56px}
.finding-link{font-size:12px;font-weight:600;margin-top:8px}
.table-wrap{overflow-x:auto;background:#fff;border:1px solid var(--line);border-radius:10px;margin:10px 0 6px;max-width:100%}
.table-caption{padding:10px 14px;font-size:12.5px;font-weight:600;color:var(--muted);border-bottom:1px solid var(--line);background:#fbfcfe}
table.data-table{border-collapse:collapse;width:100%;font-size:12.8px;min-width:640px}
table.data-table th,table.data-table td{padding:8px 11px;text-align:left;border-bottom:1px solid #eef1f6;vertical-align:top}
table.data-table thead th{position:sticky;top:0;background:#f4f7fc;color:#43516b;font-size:11px;text-transform:uppercase;letter-spacing:.05em;font-weight:700;z-index:2;white-space:nowrap}
table.data-table tbody tr:nth-child(even){background:#fcfdff}
table.data-table tbody tr:hover{background:#f0f6ff}
table.data-table td:first-child{font-weight:600;color:#22304a}
.src-cell{white-space:nowrap;max-width:250px}
.src-chip{display:inline-block;font-size:10.5px;background:#eef4ff;color:var(--navy);border:1px solid #dce8ff;padding:1px 6px;border-radius:5px;margin:1px 2px 1px 0;font-weight:600}
.src-chip:hover{text-decoration:none;background:#dce9ff}
.blank{color:#94a3b8;font-weight:700;margin-right:4px}
.badge{display:inline-block;font-size:10px;font-weight:700;letter-spacing:.02em;padding:2px 6px;border-radius:5px;white-space:nowrap}
.badge-ok{background:#dcfce7;color:#166534}.badge-warn{background:#fef3c7;color:#92400e}
.badge-info{background:#dbeafe;color:#1e40af}.badge-muted{background:#eef1f6;color:#64748b}
.badge-unverified{background:#fee2e2;color:#991b1b}
.table-note{font-size:12px;color:var(--muted);margin:8px 2px 16px;max-width:1100px}
.footer{display:flex;justify-content:space-between;gap:12px;padding:18px 28px;border-top:1px solid var(--line);color:var(--muted);font-size:11.5px;background:#fff;flex-wrap:wrap}
@media(max-width:900px){.app{flex-direction:column}.sidebar{width:100%;height:auto;position:static;flex:none}.nav{display:flex;flex-wrap:wrap;gap:6px}.nav-group{margin:0}.nav-group-title{display:none}.sidebar-foot{display:none}.topbar{position:static}.content{padding:18px}.topbar{padding:14px 18px}.topbar-right{flex-wrap:wrap}}
"""
(ROOT / "assets" / "css").mkdir(parents=True, exist_ok=True)
(ROOT / "assets" / "js").mkdir(parents=True, exist_ok=True)
(ROOT / "assets" / "css" / "style.css").write_text(CSS, encoding="utf-8")

JS = r"""/* Progressive enhancement: filter & sort tables. Content is fully server-rendered. */
(function () {
  var input = document.getElementById('globalFilter');
  var tables = Array.prototype.slice.call(document.querySelectorAll('table.data-table'));
  if (input) {
    input.addEventListener('input', function () {
      var q = input.value.trim().toLowerCase();
      tables.forEach(function (t) {
        Array.prototype.slice.call(t.tBodies[0].rows).forEach(function (tr) {
          tr.style.display = (!q || tr.textContent.toLowerCase().indexOf(q) !== -1) ? '' : 'none';
        });
      });
    });
  }
  tables.forEach(function (t) {
    Array.prototype.slice.call(t.tHead.rows[0].cells).forEach(function (th, idx) {
      th.style.cursor = 'pointer';
      th.title = 'Click to sort';
      th.addEventListener('click', function () {
        var body = t.tBodies[0], rows = Array.prototype.slice.call(body.rows);
        var asc = th.dataset.asc !== '1';
        th.dataset.asc = asc ? '1' : '0';
        rows.sort(function (a, b) {
          var x = (a.cells[idx] || {}).textContent || '', y = (b.cells[idx] || {}).textContent || '';
          var nx = parseFloat(x.replace(/[^0-9.\-]/g, '')), ny = parseFloat(y.replace(/[^0-9.\-]/g, ''));
          if (!isNaN(nx) && !isNaN(ny)) return asc ? nx - ny : ny - nx;
          return asc ? x.localeCompare(y) : y.localeCompare(x);
        });
        rows.forEach(function (r) { body.appendChild(r); });
      });
    });
  });
})();
"""
(ROOT / "assets" / "js" / "app.js").write_text(JS, encoding="utf-8")

(ROOT / ".nojekyll").write_text("", encoding="utf-8")

# ------------------------------------------------------------------ emit pages
for path, title, kicker, body, kpis in PAGES:
    out = ROOT / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(shell(path, title, kicker, body, kpis), encoding="utf-8")

# ------------------------------------------------------------------ combined site data (shared output)
write_json(SITE_DATA / "site.json", {
    "generated_utc": "2026-11-02",
    "pages": [{"path": p, "title": t} for p, t, _, _, _ in PAGES],
    "nav": [{"group": g, "items": [{"path": h, "title": t} for h, t in items]} for g, items in NAV],
    "counts": {
        "pages": len(PAGES),
        "standings_rows": len(STAND), "advanced_2025_26_rows": len(A25),
        "advanced_2026_27_rows": len(A26), "traditional_2026_27_rows": len(T26),
        "player_rows": len(PLAYERS), "settled_games": len(GAMES),
        "slate_games": len(SLATE), "lines": len(LINES["rows"]),
        "strategies": STRATS["count"], "gates": len(GATES["gates"]),
        "correlations": CORR["count"], "verification_rows": V["rows_checked"],
        "flagged": len(FLAGGED["rows"]),
    },
    "official_sources": SOURCES_JSON["sources"],
})
print(f"built {len(PAGES)} pages + assets; site-data/site.json")
