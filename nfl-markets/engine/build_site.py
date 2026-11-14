#!/usr/bin/env python3
"""nfl-markets — static site builder (stdlib only).

Builds index.html + 12 category subpages from the data files in data/.
HARD RULES (enforced by engine/verify.py after build):
  - every table row carries a source link (official where one exists; a labelled
    third-party source otherwise, with a flag chip);
  - values that cannot be confirmed stay blank and carry an UNVERIFIED/flag chip;
  - every internal link resolves; no page references a missing file.
"""
import csv, datetime as dt, html, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
ROOT = os.path.dirname(NS)
DATA = os.path.join(NS, "data")
PAGES = os.path.join(NS, "pages")
ASSETS = os.path.join(NS, "assets")

def esc(v):
    return html.escape(str(v if v is not None else ""))

def fmt(v, nd=2):
    if v in ("", None):
        return ""
    try:
        f = float(v)
        return f"{f:.{nd}f}" if nd else str(int(f))
    except (TypeError, ValueError):
        return esc(v)

def chip(label, kind):
    kinds = {"ok": "chip ok", "third": "chip third", "flag": "chip flag", "off": "chip off"}
    return f'<span class="{kinds.get(kind, "chip")}">{esc(label)}</span>'

def link(url, text=None):
    t = esc(text or url)
    return f'<a href="{esc(url)}" rel="noopener">{t}</a>'

BASE = ""   # "" when building from namespace root; ".." when building from pages/
def plink(path, text=None):
    """internal link that is correct from BOTH index.html and pages/*.html"""
    if BASE == "..":
        target = path[len("pages/"):] if path.startswith("pages/") else ("../" + path)
    else:
        target = path
    return link(target, text)

def table(headers, rows, cls="data"):
    h = "".join(f"<th>{esc(x)}</th>" for x in headers)
    body = "".join(f"<tr>{''.join(f'<td>{c}</td>' for c in r)}</tr>" for r in rows)
    return f'<div class="tblwrap"><table class="{cls}"><thead><tr>{h}</tr></thead><tbody>{body}</tbody></table></div>'

NAV = [
    ("index.html", "Dashboard"),
    ("pages/results-feed.html", "Results feed"),
    ("pages/price-snapshots.html", "Price snapshots"),
    ("pages/origination.html", "Origination"),
    ("pages/leaderboard.html", "Leaderboard"),
    ("pages/gates.html", "Gates & demotion"),
    ("pages/injuries.html", "Injuries & depth"),
    ("pages/correlations.html", "Correlations"),
    ("pages/suggestions.html", "Suggestions"),
    ("pages/decisions.html", "Decisions & unknowns"),
    ("pages/flagged.html", "⚑ Flagged for review"),
    ("pages/methods.html", "Methods"),
    ("pages/sources.html", "Sources"),
]

def page(path, title, body, subtitle=""):
    rel = "../" if "/" in path else ""
    nav = "".join(f'<a href="{rel}{href}"{" class=active" if href == path.split("pages/")[-1] and path.startswith("pages/") or (not path.startswith("pages/") and href == path) else ""}>{esc(label)}</a>' for href, label in NAV)
    sub = f'<p class="subtitle">{esc(subtitle)}</p>' if subtitle else ""
    doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · NFL Markets · Own4</title>
<link rel="stylesheet" href="{rel}assets/style.css"></head>
<body>
<header class="top"><div class="wrap">
<div class="brand"><a href="{rel}index.html" style="color:inherit;text-decoration:none">NFL&nbsp;Markets</a>
<span class="tagline">origination · price snapshots · verified results · signal vs staking</span></div>
<nav class="mainnav">{nav}</nav>
</div></header>
<main class="wrap"><h1>{esc(title)}</h1>{sub}
{body}
</main>
<footer class="wrap foot">Session <code>arena/65c4a22e-own4</code> · built {dt.datetime.now(dt.timezone.utc):%Y-%m-%dT%H:%MZ} ·
research framework only — not wagering advice · every value without an official source is blank and flagged.</footer>
</body></html>"""
    full = os.path.join(NS, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(doc)
    return full

def jload(name):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)

def cload(name):
    with open(os.path.join(DATA, name), newline="") as f:
        return list(csv.DictReader(f))

SRC = None
def sources():
    global SRC
    if SRC is None:
        import sys
        sys.path.insert(0, os.path.dirname(HERE))  # namespace root, so `engine` is importable
        from engine import config as C
        SRC = C.SOURCES
    return SRC

def src_link(key, text=None):
    s = sources().get(key)
    if not s:
        return esc(text or key)
    return link(s["url"], text or f"{s['label']}: {key}")

# ---------------------------------------------------------------- pages ----

def build_index():
    global BASE
    BASE = ""
    feed = cload("results_feed.csv")
    snap = cload("price_snapshots.csv")
    lb = jload("leaderboard.json")
    qc = jload("results_feed_qc.json")
    inj = jload("replacement_depth.json")
    corr = jload("correlations.json")
    played_2026 = [r for r in feed if r["season"] == "2026"]
    current_week = max(int(r["week"]) for r in played_2026)
    n_snap = len(snap)
    covered = len(inj["meta"]["covered_teams"])
    flags = jload("flags.json")
    sugg = jload("suggestions.json")
    dec = jload("decisions.json")
    kpis = [
        ("Verified results rows", f"{len(feed):,}", "2011-2026 · 32/32 standings reconciliation", "pages/results-feed.html"),
        ("Price-snapshot rows", f"{n_snap:,}", "side → total → moneyline, every originated market", "pages/price-snapshots.html"),
        ("Origination model", "v1", "Elo+EWMA, walk-forward, calibrated 1999-2010", "pages/origination.html"),
        ("Strategies graded", str(len(lb)), "signal separated from staking; rewards = 0", "pages/leaderboard.html"),
        ("Gates passed", "0 strategies", "nothing promoted; all PAPER", "pages/gates.html"),
        ("Replacement depth", f"{covered}/32 teams", "official report + flagged third-party depth", "pages/injuries.html"),
        ("Correlations with n", str(len(corr['official_inputs']) + len(corr['third_party_inputs_flagged'])), "official group + flagged third-party group", "pages/correlations.html"),
        ("Open flags", str(len(flags["flags"])), "published, non-blocking, with sources", "pages/flagged.html"),
    ]
    cards = "".join(f'<a class="card" href="{href}"><div class="kpi">{esc(v)}</div><div class="kpi-l">{esc(k)}</div><div class="kpi-d">{esc(d)}</div></a>'
                    for k, v, d, href in kpis)
    highlight = f"""
<div class="callout warn"><strong>Headline (honest negative result):</strong> every implementable strategy matches or
underperforms the closing market — best beat-close rate 50.31% (permutation p=0.45), all flat-stake ROI negative,
zero rewards, nothing promoted. The leaderboard keeps <em>signal</em> and <em>staking</em> in separate columns so a
lucky staking run cannot mask a bad signal. See {plink("pages/leaderboard.html", "Leaderboard")} and
{plink("pages/gates.html", "Gates")}.</div>
<div class="callout"><strong>What is new in this namespace:</strong>
<ul>
<li>A populated {plink("pages/price-snapshots.html", "price-snapshot store")} — {n_snap:,} rows: origination order
side → total → moneyline; model fair line, market open, market close and both differences as separate columns;
opening numbers blank + flagged where no archive exists (never inferred).</li>
<li>A {plink("pages/results-feed.html", "verified results feed")} — {len(feed):,} played games 2011-2026, official
source link on every row, 32/32 standings reconciliation vs the official capture, live NFL.com spot checks.</li>
<li>{plink("pages/injuries.html", "Replacement-depth tracking")} — the depth (2nd/3rd/4th/none) of each replacement,
not just the fact of one: 10 starter-out rows quantified; 24 teams blank + flagged (no chart source).</li>
<li>{plink("pages/correlations.html", "Correlations with n published")} — official-input group vs flagged
third-party group; cross-game parlay legs cover −1.19pp vs market-implied independence (n=27,129 pairs).</li>
<li>A {plink("pages/suggestions.html", "suggestions review queue")} and a
{plink("pages/decisions.html", "decisions register")} — what we know, what we do not know, and how to discover it —
so nothing is decided on the information we do not have.</li>
</ul></div>
<div class="callout note"><strong>Current week:</strong> 2026 REG {current_week} — week in progress (Thursday final:
WAS 24–21 NYG). Origination for every unplayed market is live on the {plink("pages/origination.html", "Origination page")}.</div>
"""
    body = f'<div class="cards">{cards}</div>{highlight}'
    page("index.html", "NFL markets dashboard", body,
         "Price-snapshot store, verified results feed, signal-vs-staking leaderboard, replacement depth, correlations with n, gates and demotion — all row-sourced, blanks flagged, never inferred.")

def build_results_feed():
    global BASE
    BASE = ".."
    feed = cload("results_feed.csv")
    rows26 = [r for r in feed if r["season"] == "2026"]
    trs = []
    for r in rows26:
        st = r["verification_status"]
        ch = chip("cross-checked vs official standings", "ok") if st == "cross-checked-official" else chip("archive official-origin", "third")
        trs.append([esc(r["gameday"]), f"W{r['week']}", esc(r["away_team"]), f"<strong>{r['away_score']}</strong>",
                    esc(r["home_team"]), f"<strong>{r['home_score']}</strong>",
                    esc(r["winner"]), ("OT" if r["overtime"] != "0" else ""),
                    link(r["official_source_url"], "nfl.com game page"),
                    link(r["official_week_url"], "week"), ch])
    t26 = table(["Date", "Wk", "Away", "Pts", "Home", "Pts", "Winner", "", "Official source (per row)", "Week page", "Verification"], trs)
    body = f"""
<p>One row per played game, 2011-2026 regular seasons ({len(feed):,} rows; the {len(rows26)} rows of the current 2026
season are shown — the full archive is <code>data/results_feed.csv</code>). Every row links to the official
nfl.com game page; 2026 rows are additionally reconciled: recomputing standings from this feed matches the official
standings capture <strong>32/32 with zero mismatches</strong>, and the NFC East records were cross-checked live against
nfl.com on 2026-11-14 (4/4 match).</p>
<div class="callout note">Backtests and ROI settle <strong>only</strong> against this feed. Scores render client-side on
nfl.com pages (not extractable by plain fetch); they are verified by the 32/32 arithmetic reconciliation plus live
record spot checks — see {plink("pages/methods.html", "Methods")}.</div>
<h2>2026 season (through Week 10 Thursday)</h2>{t26}
<h2>Verification summary</h2>
{table(["Check", "Result", "Evidence"],
 [["Standings reconciliation 2026 (feed-recomputed vs official capture)", "32/32 exact, 0 mismatches", link("https://github.com/sassnarep3-star/Own4/blob/main/nfl-markets/data/results_feed_qc.json", "QC JSON (REPO)")],
  ["Live NFC East records vs nfl.com page widget (2026-11-14)", "4/4 match", link("https://www.nfl.com/games/commanders-at-giants-2026-reg-10", "official game page")],
  ["Week-10 Thursday final (WAS 24–21 NYG)", "matches feed and peer verification", link("https://www.nfl.com/games/commanders-at-giants-2026-reg-10", "official game page")]])}
"""
    page("pages/results-feed.html", "Verified results feed", body)

def build_snapshots():
    global BASE
    BASE = ".."
    snap = cload("price_snapshots.csv")
    qc = jload("results_feed_qc.json")
    st = qc["snapshot_store"]
    counts = {
        "open": st["open_statuses"], "close": st["close_statuses"],
    }
    avail_rows = []
    SRC_OPEN = "https://github.com/nflverse/nfldata/blob/master/data/"
    for label, d in (("Opening numbers", counts["open"]), ("Closing numbers", counts["close"])):
        tot = sum(d.values())
        for k, v in sorted(d.items(), key=lambda x: -x[1]):
            meaning = ("no archive exists — blank, never inferred" if "BLANK" in k else
                       ("source does not publish capture time" if "TIMING" in k or "UNPUBLISHED" in k else
                        ("game not played yet" if "PENDING" in k else "read from the named archive file")))
            src = (link("https://github.com/sassnarep3-star/Own4/blob/main/nfl-markets/data/price_snapshots.csv", "store CSV (REPO)") if "BLANK" in k else
                   link(SRC_OPEN + ("initial_lines.csv" if label.startswith("Opening") and "VERIFIED" in k else
                                    "sc_lines.csv" if label.startswith("Opening") else
                                    "closing_lines.csv" if "VERIFIED" in k else "games.csv"), "archive file"))
            avail_rows.append([esc(label), esc(k), f"{v:,}", f"{100*v/tot:.1f}%", meaning, src])
    t_avail = table(["Series", "Status", "Rows", "Share", "Meaning", "Source"], avail_rows)
    week = [r for r in snap if r["close_verification_status"] == "PENDING-CLOSE" and r["gameday"] <= "2026-11-17"]
    trs = []
    for r in sorted(week, key=lambda x: (x["gameday"], x["market_seq"])):
        trs.append([esc(r["gameday"]), f"W{r['week']}", esc(r["market_seq"]), f"<strong>{esc(r['market'])}</strong>",
                    esc(r["away_team"]) + " @ " + esc(r["home_team"]),
                    fmt(r["model_fair_line"]), fmt(r["market_open_line"]) or chip("UNVERIFIED-BLANK", "flag"),
                    fmt(r["market_close_line"], 2) or "—",
                    fmt(r["diff_open_line"]) or "—", fmt(r["diff_close_line"]) or "—",
                    esc(r["open_verification_status"]), esc(r["close_verification_status"]),
                    link(r["official_source_url"], "nfl.com game")])
    t_week = table(["Gameday", "Wk", "Seq", "Market (origination order)", "Matchup", "Model fair",
                    "Market open", "Market close*", "Diff open", "Diff close", "Open status", "Close status", "Source"], trs)
    body = f"""
<p>The price-snapshot store records, for <strong>every market we originate</strong> (order: side → total → moneyline),
the model's fair line, the market's opening number, the market's closing number, and the two differences — each as its
own column. Current size: <strong>{len(snap):,} rows</strong> (4,191 games × 3 markets). Full store:
<code>data/price_snapshots.csv</code> (SHA-256 in <code>data/manifest.json</code>).</p>
<h2>Availability matrix (what exists vs what is blank)</h2>{t_avail}
<div class="callout warn"><strong>*Close for unplayed games</strong> is the latest POSTED line, not a close
(PENDING-CLOSE). Moneyline opening numbers do not exist in any archive — those cells are blank by rule
(4,191 rows) and every ML strategy is signal-only.</div>
<h2>Live origination snapshot — weeks 10-11, 2026 (unplayed markets)</h2>{t_week}
<p class="small">Model fair lines: this repo's walk-forward model (v1), captured at the day-before-kickoff cutoff;
state size per line is recorded (<code>state_games_used</code>). Market open/close: labelled third-party archives —
see {plink("pages/sources.html", "Sources")} for the convention tests behind every conversion.</p>
"""
    page("pages/price-snapshots.html", "Price-snapshot store", body)

def build_origination():
    global BASE
    BASE = ".."
    snap = cload("price_snapshots.csv")
    cal = jload("model_calibration.json")
    rows = [r for r in snap if r["close_verification_status"] == "PENDING-CLOSE"]
    REPO_MODEL = "https://github.com/sassnarep3-star/Own4/blob/main/nfl-markets/engine/model.py"
    order = table(["Seq", "Market", "Why this order", "Source"],
                  [["1", "SIDE (spread)", "Priced first: the spread is the primary market; the total and ML are anchored to it. Any correlation between markets is handled only after the side exists.", link(REPO_MODEL, "engine/model.py (REPO)")],
                   ["2", "TOTAL", "Priced second, conditional on the side's ratings state; totals use the same walk-forward OFF/DEF state.", link(REPO_MODEL, "engine/model.py (REPO)")],
                   ["3", "MONEYLINE", "Derived last from the fair spread (normal CDF, σ frozen from calibration residuals) — never independent of the side.", link(REPO_MODEL, "engine/model.py (REPO)")]])
    trs = []
    for r in sorted(rows, key=lambda x: (x["gameday"], x["market_seq"], x["game_id"])):
        trs.append([esc(r["gameday"]), esc(r["market_seq"]), f"<strong>{esc(r['market'])}</strong>",
                    esc(r["away_team"]) + " @ " + esc(r["home_team"]),
                    fmt(r["model_fair_line"]), fmt(r["market_close_line"], 2) or "—", fmt(r["diff_close_line"]) or "—",
                    chip("ORIGINATED — not a validated edge", "flag"),
                    link(r["official_source_url"], "nfl.com game")])
    t_own = table(["Gameday", "Seq", "Market", "Matchup", "Fair line (ours)", "Market line (posted)", "Difference", "Status", "Source"], trs)
    body = f"""
<h2>Origination order (frozen policy)</h2>{order}
<h2>Calibration (frozen on the training window; no market data enters the model)</h2>
{table(["Parameter", "Value", "Meaning", "Source"],
 [["Training window", esc(cal["training_window"]), f"n={cal['n_training_games']} games", link("https://github.com/sassnarep3-star/Own4/blob/main/nfl-markets/data/model_calibration.json", "calibration JSON (REPO)")],
  ["Elo→points slope", esc(cal["slope_elo_to_points"]), "least-squares on the training window, then FROZEN", link("https://github.com/sassnarep3-star/Own4/blob/main/nfl-markets/data/model_calibration.json", "calibration JSON (REPO)")],
  ["Home advantage (intercept)", f"{cal['intercept_points_hfa']} pts", "frozen; enters fair spreads", link("https://github.com/sassnarep3-star/Own4/blob/main/nfl-markets/data/model_calibration.json", "calibration JSON (REPO)")],
  ["σ of margin residuals", f"{cal['sigma_margin_residuals']} pts", "frozen; powers fair ML probabilities", link("https://github.com/sassnarep3-star/Own4/blob/main/nfl-markets/data/model_calibration.json", "calibration JSON (REPO)")],
  ["Elo K / HFA(Elo)", f"{cal['k']} / {cal['hfa_elo_constant']}", "update constants", link("https://github.com/sassnarep3-star/Own4/blob/main/nfl-markets/data/model_calibration.json", "calibration JSON (REPO)")],
  ["Totals EWMA α", esc(cal["alpha_totals_ewma"]), "~14-game half-life, shrunk to league mean early season", link("https://github.com/sassnarep3-star/Own4/blob/main/nfl-markets/data/model_calibration.json", "calibration JSON (REPO)")],
  ["Origination first season", esc(cal["origination_first_season"]), "walk-forward from 2011; warm-up 1999-2010", link("https://github.com/sassnarep3-star/Own4/blob/main/nfl-markets/data/model_calibration.json", "calibration JSON (REPO)")]])}
<h2>Originated markets for the current slates (weeks 10-11, 2026)</h2>{t_own}
<div class="callout warn"><strong>These are model outputs, not validated edges.</strong> The gates failed for every
strategy ({plink("pages/gates.html", "Gates")}) — the fair/market difference is published for transparency and
review, never as a recommendation.</div>
"""
    page("pages/origination.html", "Origination — order & own lines", body)

def build_leaderboard():
    global BASE
    BASE = ".."
    lb = jload("leaderboard.json")
    sels = cload("selections.csv")
    sig_rows = []
    for r in sorted([x for x in lb if x.get("signal_rank")], key=lambda x: x["signal_rank"]):
        s = r["signal"]
        sig_rows.append([esc(r["signal_rank"]), f"<strong>{esc(r['id'])}</strong>", esc(r["family"]),
                         esc(r["name"]), f"{s['n_selections']:,}",
                         fmt(s["mean_edge_vs_close_pts"]) if s.get("mean_edge_vs_close_pts") is not None else "—",
                         fmt(s.get("beat_close_rate"), 4) if s.get("beat_close_rate") is not None else "—",
                         f"[{s['beat_close_rate_ci95'][0]:.3f}, {s['beat_close_rate_ci95'][1]:.3f}]" if s.get("beat_close_rate_ci95") else "—",
                         esc(s.get("beat_close_rate_perm_p")) if s.get("beat_close_rate_perm_p") is not None else "—",
                         f"{s['seasons_positive_edge']}/{s['seasons_total']}",
                         plink("pages/gates.html", "gates"), link("https://www.nfl.com/schedules/", "results source")])
    st_rows = []
    for r in sorted([x for x in lb if x.get("staking_rank")], key=lambda x: x["staking_rank"]):
        k = r["staking"]
        st_rows.append([esc(r["staking_rank"]), f"<strong>{esc(r['id'])}</strong>",
                        f"{k['n_staked']:,}", fmt(k.get("roi_flat"), 4), esc(k.get("units")),
                        f"{k['wins']}-{k['losses']}-{k['pushes']}",
                        fmt(k.get("max_drawdown_units")),
                        chip("price assumption −110", "flag"),
                        esc(k.get("entry_price_policy", "")),
                        link("https://www.nfl.com/schedules/", "results source")])
    sig_rows.append(["—", "<strong>STRAT-PROP-COMBO</strong>", "prop-combo",
                     "Player-prop combos (NOT IMPLEMENTED — no verifiable results source exists)", "—",
                     "—", "—", "—", "—", "—", chip("BLOCKED", "flag"), plink("pages/decisions.html", "DEC-M4") + " · " +
                     link("https://github.com/sassnarep3-star/Own4/blob/main/nfl-markets/data/leaderboard.json", "registry JSON (REPO)")])
    t_sig = table(["Rank", "Strategy", "Family", "Rule", "n", "Mean edge vs close (pts)", "Beat-close rate",
                   "95% CI", "Perm p", "Seasons pos.", "Gates", "Source"], sig_rows)
    t_st = table(["Rank", "Strategy", "n staked", "ROI (flat 1u)", "Units", "W-L-P", "Max DD (u)",
                  "Price flag", "Entry price policy", "Source"], st_rows)
    body = f"""
<div class="callout warn"><strong>Signal and staking are separate.</strong> Left table = SIGNAL quality only
(line value vs the closing market — a lucky bankroll cannot move it). Right table = STAKING only (flat-stake ROI at an
assumed price — variance-heavy at these n). Ranks are computed independently; the combined order of the site is
<strong>signal-first</strong>: staking never upgrades a weak signal.</div>
<h2>SIGNAL (line quality vs the closing market)</h2>{t_sig}
<h2>STAKING (flat-stake performance — separate columns, separate ranks)</h2>{t_st}
<div class="callout note"><strong>Rewards: 0.</strong> The rewarded tier requires ALL promotion gates; none passed
({plink("pages/gates.html", "details")}). Honest negative results are published, not hidden. Full graded-selection
audit trail ({len(sels):,} rows): <code>data/selections.csv</code>.</div>
<p class="small">Entry-price policy differs by archive availability (documented per row): opening numbers
(2013-2021) where archived, otherwise the archived market line. Settlement: verified results feed only;
pushes void the stake.</p>
"""
    page("pages/leaderboard.html", "Leaderboard — signal vs staking", body)

REPO_GATES = "https://github.com/sassnarep3-star/Own4/blob/main/nfl-markets/engine/gates.py"
REPO_GE = "https://github.com/sassnarep3-star/Own4/blob/main/nfl-markets/data/gates_evaluation.json"

def build_gates():
    global BASE
    BASE = ".."
    ge = jload("gates_evaluation.json")
    lb = jload("leaderboard.json")
    mg_rows = [[esc(g["id"]), f"<strong>{esc(g['name'])}</strong>", esc(g["rule"]),
                chip("blocking", "flag") if g.get("blocking") else "",
                link(REPO_GATES, "rules live here (REPO)")] for g in ge["promotion_gates"]]
    t_mg = table(["ID", "Gate", "Rule", "", "Source"], mg_rows)
    strats = [r for r in lb if r.get("gates")]
    ids = [g["id"] for g in strats[0]["gates"]]
    matrix = []
    for r in strats:
        cells = []
        for g in r["gates"]:
            mark = "✔" if g["pass"] is True else ("✘" if g["pass"] is False else "n/a")
            cls = "pass" if g["pass"] is True else ("fail" if g["pass"] is False else "na")
            cells.append(f'<span class="mark {cls}">{mark}</span>')
        matrix.append([f"<strong>{esc(r['id'])}</strong>"] + cells + [esc(sum(1 for g in r['gates'] if g['pass'] is True)),
                       link(REPO_GE, "evaluation JSON (REPO)")])
    t_matrix = table(["Strategy"] + ids + ["Passed", "Source"], matrix)
    dm_rows = [[esc(d["id"]), esc(d["trigger"]), esc(d["action"]), link(REPO_GATES, "state machine (REPO)")] for d in ge["demotion"]["rules"]]
    t_dm = table(["ID", "Trigger (any sends the strategy back to PAPER)", "Action", "Source"], dm_rows)
    sim_rows = []
    for strat, d in ge["demotion"]["simulations"].items():
        sim_rows.append([f"<strong>{esc(strat)}</strong>", f"{d['n_settled']:,}",
                         esc(d["n_trigger_events"]),
                         " / ".join(f"{e['rule']} @sel {e['index']}" for e in d["events_first_10"][:4]),
                         chip("counterfactual — nothing is live", "flag"),
                         link(REPO_GE, "simulation JSON (REPO)")])
    t_sim = table(["Strategy (simulated AS IF live since first window)", "n settled", "Demotion triggers",
                   "First triggers", "Status", "Source"], sim_rows)
    cfg = ge["demotion"]["config"]
    body = f"""
<h2>Promotion gates (paper → live; frozen; all must pass)</h2>{t_mg}
<h2>Gate matrix — current evaluation</h2>{t_matrix}
<div class="callout warn"><strong>No strategy passes.</strong> MG-5 (CI excludes 50%), MG-7 (placebo p&lt;0.05) and
MG-8 (season stability) fail on every implementable strategy; the 2026 frozen holdout is negative on both staked
strategies ({esc(ge['holdout_2026'].get('STRAT-SIDE-3',{}).get('detail',''))} sides;
{esc(ge['holdout_2026'].get('STRAT-TOTAL-3',{}).get('detail',''))} totals). Nothing is promoted; rewards = 0.</div>
<h2>Demotion gate (live → paper)</h2>{t_dm}
<p class="small">Config: window {cfg['window']} settled stakes · ROI floor {cfg['roi_floor']:.0%} · beat-close floor
{cfg['beat_close_floor']:.0%} · {cfg['edge_windows_consecutive']} consecutive zero-edge windows · re-lock
{cfg['relock_windows']} windows · cadence: {cfg['cadence']}.</p>
<h2>Counterfactual demonstration on real historical windows</h2>{t_sim}
<div class="callout note">The state machine is exercised on each strategy's real selection history with
<em>forced live</em> status so the triggers can be observed; events are counterfactual by definition — nothing in this
repository is a live strategy (see {plink("pages/decisions.html", "DEC-M1")}). DM-4 (feed integrity) and DM-5
(unpriced correlation exposure) are wired to the {plink("pages/results-feed.html", "results feed")} verification
statuses and the {plink("pages/correlations.html", "measured leg dependence")} respectively.</div>
"""
    page("pages/gates.html", "Gates & demotion", body)

def build_injuries():
    global BASE
    BASE = ".."
    inj = jload("replacement_depth.json")
    meta, rows, summary = inj["meta"], inj["rows"], inj["team_summary"]
    out_rows = [r for r in rows if r["starter_out_row"]]
    trs = []
    for r in out_rows:
        disc = chip("official↔depth discrepancy", "flag") if r.get("official_vs_depth_discrepancy") else ""
        trs.append([f"<strong>{esc(r['team'])}</strong>", esc(r["unit"]), esc(r["position"]),
                    esc(r["starter"]), esc(r["starter_depth_marker"]),
                    esc(r["official_game_status"]) or "—", esc(r["official_practice_status"]) or "—",
                    f"<strong>{esc(r['replacement']) if r['replacement'] else chip('NONE — no available backup on chart', 'flag')}</strong>",
                    f"<strong>{esc(r['replacement_depth'])}</strong>" if r["replacement_depth"] != "" else "",
                    esc(r["deficiency_points"]),
                    chip("OFFICIAL", "off") + " " + link("https://www.nfl.com/injuries/", "nfl.com/injuries") +
                    " · " + chip("THIRD-PARTY", "third") + " " + link("https://www.espn.com/nfl/depth", "ESPN depth"),
                    disc])
    t_out = table(["Team", "Unit", "Pos", "Starter", "Chart marker", "Official game status",
                   "Official practice status", "Replacement", "DEPTH of replacement", "Deficiency pts",
                   "Sources", "Flag"], trs)
    sum_rows = []
    for t in sorted(summary, key=lambda x: -(summary[x].get("deficiency_index") or -1)):
        v = summary[t]
        if v.get("deficiency_index") is None:
            sum_rows.append([f"<strong>{esc(t)}</strong>", "—", "—", "—", "—",
                             chip("UNVERIFIED — no depth chart captured (blank, never inferred)", "flag"),
                             link("https://www.nfl.com/injuries/", "official report rows only")])
        else:
            d = v["replacement_depth_counts"]
            sum_rows.append([f"<strong>{esc(t)}</strong>", esc(v["n_starters_out"]),
                             f"2nd: {d.get('2',0)} · 3rd: {d.get('3',0)} · 4th: {d.get('4',0)} · none: {d.get('NONE',0)}",
                             esc(v["deficiency_index"]), chip("QB1 out", "flag") if v.get("qb_out") else "",
                             chip("depth THIRD-PARTY", "third"),
                             link("https://www.espn.com/nfl/depth", "ESPN") + " · " + link("https://www.nfl.com/injuries/", "nfl.com")])
    t_sum = table(["Team", "Starters out", "Replacement depth counts", "Deficiency index (repo convention)",
                   "", "Source labels", "Sources"], sum_rows)
    body = f"""
<div class="callout warn"><strong>The requirement:</strong> track the <em>depth of the replacement</em>, not just the
fact of one. Rows below quantify, for each unavailable starter, which string replaces them (2nd / 3rd / 4th / NONE).
Depth values come from ESPN/RotoWire charts (THIRD-PARTY — the NFL publishes no machine-readable depth chart) and are
flagged as such; availability designations come from the OFFICIAL nfl.com report. Teams without a captured chart stay
blank and flagged — never inferred.</div>
<h2>Starter-out rows — Week 10, 2026 ({len(out_rows)} rows, official + flagged third-party)</h2>{t_out}
<h2>Team summary (covered {len(meta['covered_teams'])} · uncovered {len(meta['uncovered_teams_with_official_rows'])})</h2>{t_sum}
<div class="callout note"><strong>Weighting convention (ours, published, flagged):</strong>
{esc(meta['weights_convention'])} — see {plink("pages/decisions.html", "DEC-M5")} for the validation proposal.
Discrepancies between the third-party chart markers and the official report are kept and shown (5 rows) rather than
silently resolved — {plink("pages/flagged.html", "FLAG-M6")}.</div>
"""
    page("pages/injuries.html", "Injuries & replacement depth", body)

def build_correlations():
    global BASE
    BASE = ".."
    corr = jload("correlations.json")
    def rows_of(group, official):
        out = []
        for r in group:
            if r.get("value") is not None:
                val = f"<strong>{r['value']:+.4f}</strong>"
            else:
                val = "—"
            ci = f"[{r['ci95'][0]:+.4f}, {r['ci95'][1]:+.4f}]" if r.get("ci95") else "—"
            srcs = " · ".join(src_link(k) for k in r["source_keys"]) if r["source_keys"] else "—"
            ch = chip("OFFICIAL inputs", "off") if official else chip("THIRD-PARTY inputs — flagged", "third")
            out.append([f"<strong>{esc(r['id'])}</strong>", esc(r["label"]), esc(r["method"]), val,
                        f"{r['n']:,}", ci, ch, esc(r["reading"]), srcs])
        return out
    t_off = table(["ID", "Relationship", "Method", "Value", "n", "95% CI", "Inputs", "Reading", "Sources"],
                  rows_of(corr["official_inputs"], True))
    t_3p = table(["ID", "Relationship", "Method", "Value", "n", "95% CI", "Inputs", "Reading", "Sources"],
                 rows_of(corr["third_party_inputs_flagged"], False))
    ps1 = [p for p in corr["official_inputs"] if p["id"] == "CO-1b"]
    ps2 = [p for r in [corr["third_party_inputs_flagged"]] for p in r if p["id"] == "CT-1b"]
    per_rows = []
    if ps1:
        for p in ps1[0]["per_season"]:
            per_rows.append(["CO-1b", esc(p["season"]), fmt(p["value"], 4), f"{p['n']:,}",
                             chip("OFFICIAL", "off"), link("https://www.nfl.com/schedules/", "official scores")])
    if ps2:
        for p in ps2[0]["per_season"][:12]:
            per_rows.append(["CT-1b", esc(p["season"]), fmt(p["value"], 4), f"{p['n']:,}",
                             chip("THIRD-PARTY lines", "third"),
                             link("https://github.com/nflverse/nfldata/blob/master/data/games.csv", "archive lines") +
                             " · " + link("https://www.nfl.com/schedules/", "scores")])
    t_per = table(["ID", "Season", "Value", "n", "Inputs", "Source"], per_rows)
    body = f"""
<div class="callout note"><strong>Rule enforced here:</strong> correlations are computed only from officially sourced
numbers where possible and <strong>n is published with every value</strong>. Correlations that necessarily involve
market numbers (a cover needs a line) live in their own flagged group and are never blended into the official group.
{esc(corr["method_note"])}</div>
<h2>Group A — official inputs only</h2>{t_off}
<h2>Group B — third-party inputs (flagged)</h2>{t_3p}
<h2>Per-season detail</h2>{t_per}
<div class="callout warn"><strong>Key finding for parlays (CT-2):</strong> same-week cross-game legs both cover
<strong>−1.19pp vs market-implied independence</strong> (observed 23.8% vs expected 25.0%; SE 0.26pp;
n=27,129 pairs over 269 weeks) — cross-game parlays at standard prices are marginally worse than they look.
Same-game prop correlations remain <strong>blank by rule</strong>: no verifiable prop-results source exists
({plink("pages/decisions.html", "DEC-M4")}).</div>
"""
    page("pages/correlations.html", "Correlations (n published)", body)

def build_suggestions():
    global BASE
    BASE = ".."
    sugg = jload("suggestions.json")
    rows = []
    for s in sugg["suggestions"]:
        srcs = " · ".join(link(u) for u in s["sources"]) if s["sources"] else "—"
        rows.append([f"<strong>{esc(s['id'])}</strong>", esc(s["title"]), esc(s["rationale"]),
                     esc(s["discovers"]), esc(s["effort"]), esc(s["priority"]),
                     chip(f"{s['status']} — awaiting reviewer choice", "flag"), srcs])
    t = table(["ID", "Suggestion", "Rationale", "What it discovers", "Effort", "Priority", "Status", "Sources"], rows)
    body = f"""
<div class="callout warn"><strong>This is the review queue.</strong> Every item is a proposal — nothing is implemented
until someone picks the best path here and records the choice. The column “What it discovers” maps each suggestion to
the missing information that currently blocks a decision ({plink("pages/decisions.html", "Decisions register")}).</div>
{t}
<div class="callout note"><strong>How to choose:</strong> highest discovery-value per effort first — SUG-M4 (opens with
timestamps) and SUG-M6 (weekly re-verification) are cheap and unblock measurement quality permanently; SUG-M7
(pre-registration) is what keeps any future signal honest; SUG-M2 gates prop combos entirely. Record decisions as a
new dated note in COORDINATION.md and flip the status here.</div>
"""
    page("pages/suggestions.html", "Suggestions — review before implementation", body)

def build_decisions():
    global BASE
    BASE = ".."
    dec = jload("decisions.json")
    rows = []
    for d in dec["decisions"]:
        known = "<ul>" + "".join(f"<li>{esc(x)}</li>" for x in d["we_know"]) + "</ul>"
        unknown = "<ul>" + "".join(f"<li>{esc(x)}</li>" for x in d["we_do_not_know"]) + "</ul>"
        discover = "<ul>" + "".join(f"<li>{esc(x)}</li>" for x in d["how_to_discover"]) + "</ul>"
        srcs = " · ".join(link(u) for u in d["sources"]) if d["sources"] else "—"
        rows.append([f"<strong>{esc(d['id'])}</strong>", esc(d["question"]), known, unknown, discover,
                     chip(esc(d["status"]), "flag"), srcs])
    t = table(["ID", "Decision needed", "What we already know (measured, sourced)",
               "What we do NOT know", "How to discover it (suggestions)", "Status", "Sources"], rows)
    body = f"""
<div class="callout warn"><strong>Purpose:</strong> a decision is only reasonable on information that actually exists.
Each row separates what is measured (with values and sources) from what is missing, and proposes how to discover the
missing part — instead of deciding on assumptions.</div>
{t}
<div class="callout note">Two rows genuinely need owner input ({plink("pages/decisions.html", "DEC-M2")} bankroll/reward
policy and {plink("pages/decisions.html", "DEC-M6")} namespace-of-record) — everything else is blocked on measurable
evidence or a missing data source, not on opinion.</div>
"""
    page("pages/decisions.html", "Decisions & unknowns", body)

REPO_EVIDENCE = {
    "FLAG-M3": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-markets/data/price_snapshots.csv",
    "FLAG-M4": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-markets/engine/strategies.py",
    "FLAG-M7": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-markets/engine/injuries.py",
    "FLAG-M9": "https://github.com/sassnarep3-star/Own4/blob/main/nfl-markets/data/gates_evaluation.json",
}
def build_flagged():
    global BASE
    BASE = ".."
    flags = jload("flags.json")
    rows = []
    for fl in flags["flags"]:
        srcs = " · ".join(link(u) for u in fl["sources"]) if fl["sources"] else link(REPO_EVIDENCE.get(fl["id"], REPO_EVIDENCE["FLAG-M9"]), "repo evidence (REPO)")
        rows.append([f"<strong>{esc(fl['id'])}</strong>", esc(fl["summary"]), esc(fl["evidence"]),
                     esc(fl["affected"]), chip(esc(fl["severity"]), "flag"), srcs])
    t = table(["ID", "Irregularity", "Evidence", "Affected fields", "Severity", "Sources"], rows)
    body = f"""
<div class="callout warn"><strong>Flagged for Review — non-blocking.</strong> Values that cannot be confirmed from an
official source are blank in the data and listed here with evidence and source links. Nothing was inferred to fill a
gap. Review and request changes at any time; flags never block publication or merges.</div>
{t}
"""
    page("pages/flagged.html", "Flagged for review", body)

def build_sources():
    global BASE
    BASE = ".."
    src_rows = []
    for k, s in sources().items():
        src_rows.append([f"<code>{esc(k)}</code>", chip(esc(s["label"]), "off" if s["label"] == "OFFICIAL" else ("third" if s["label"] == "THIRD-PARTY" else "flag")),
                         esc(s["used_for"]), link(s["url"])])
    t = table(["Key", "Label", "Used for", "URL"], src_rows)
    qc = jload("results_feed_qc.json")
    body = f"""
<h2>Source registry</h2>{t}
<h2>Convention verification (this session — no guessing)</h2>
{table(["Test", "Result", "Meaning", "Evidence", link("https://github.com/sassnarep3-star/Own4/blob/main/nfl-markets/data/verification.json", "evidence (REPO)")],
 [["spread_line vs actual home margin: outright win rate of 7+ point favorites", "home favs 81.7% (n=1,200); away favs 77.2% (n=408)",
   "games.csv spread_line = expected HOME margin (positive = home favored) — matches the documented convention", link("https://github.com/sassnarep3-star/Own4/blob/main/nfl-markets/data/verification.json", "evidence")],
  ["per-season mean(spread_line − result)", "within ±1.9 pts, all seasons 2011-2026", "line series behaves as a market line vs outcomes", link("https://github.com/sassnarep3-star/Own4/blob/main/nfl-markets/data/verification.json", "evidence")],
  ["closing_lines.csv team line → home-margin conversion vs games.csv spread_line", "mean diff −0.05 pts, sd 0.41 (n=1,967)",
   "conversion rule (home margin = −team line) verified", link("https://github.com/sassnarep3-star/Own4/blob/main/nfl-markets/data/verification.json", "evidence")],
  ["closing archive settlement column vs computed cover", "99.8% agreement excl pushes (n=3,808)", "settlement semantics verified", link("https://github.com/sassnarep3-star/Own4/blob/main/nfl-markets/data/verification.json", "evidence")],
  ["initial_lines.csv (Westgate 2021) vs live-verified reality", "TB −6.5 open → −9.5/−10 close matches live reports (2021 opener)",
   "per-team book line conversion + open-vs-close drift quantified (mean |Δ| 3.40 pts, 272 games)", link("https://www.pennlive.com/sports/2021/09/tampa-bay-buccaneers-vs-dallas-cowboys-betting-guide-money-line-point-spread-team-and-player-picks-for-nfl-opener.html", "evidence")],
  ["2026 standings recomputed from the results feed vs official capture", "32/32 exact, 0 mismatches", "results feed integrity", link("https://github.com/sassnarep3-star/Own4/blob/main/nfl-markets/data/results_feed_qc.json", "evidence")],
  ["live NFL.com spot check (2026-11-14)", "NFC East records 4/4 match; official game-page URL pattern validated",
   "per-row official links resolve to the right game", link("https://www.nfl.com/games/commanders-at-giants-2026-reg-10", "official game page")]])}
<div class="callout note"><strong>Labelling policy:</strong> OFFICIAL = published by the NFL. THIRD-PARTY = trusted
analyst/archive source, always labelled, never passed off as official. REPO = this repository's own files with
provenance. Values with no source stay blank and are flagged ({plink("pages/flagged.html", "Flagged for review")}).
See {plink("pages/methods.html", "Methods")} for the full verification protocol and
{plink("pages/origination.html", "Origination")} for the model's frozen calibration.</div>
"""
    page("pages/sources.html", "Sources & conventions", body)

def build_methods():
    global BASE
    BASE = ".."
    qc = jload("results_feed_qc.json")
    cal = qc["model"]
    snap = cload("price_snapshots.csv")
    body = f"""
<h2>Origination model (v1, frozen)</h2>
<p>Elo with margin-of-victory multiplier for sides; EWMA OFF/DEF point ratings for totals; fair ML from the fair spread
via a frozen normal CDF. Calibration (slope {esc(cal['slope_elo_to_points'])}, HFA {esc(cal['intercept_points_hfa'])} pts,
σ {esc(cal['sigma_margin_residuals'])}) is fitted on 1999-2010 and frozen; origination is walk-forward from 2011 with a
day-before-kickoff cutoff — no same-day or future information can enter any fair line, and every snapshot row records
its state size (<code>state_games_used</code>). No market number enters the model anywhere.</p>
<h2>Snapshot conventions</h2>
<ul>
<li>SPREAD SIGN: home-margin convention everywhere (positive = home favored) — verified empirically
({plink("pages/sources.html", "sources page")}).

</li>
<li>ORIGINATION ORDER: side → total → moneyline, enforced by <code>market_seq</code>.</li>
<li>ORIGINATION TIME: gameday − 1 day, recorded per row (<code>model_captured_at</code>).</li>
<li>Diff columns: <code>diff_open_line = fair − open</code>, <code>diff_close_line = fair − close</code> — separate
columns, never merged.</li>
<li>Moneyline diff: fair probability − vig-included implied probability of the archived close (conservative).</li>
</ul>
<h2>Settlement & staking assumptions (all flagged)</h2>
<ul>
<li>Settlement uses the {plink("pages/results-feed.html", "verified results feed")} only (32/32 reconciled).</li>
<li>Singles priced at assumed standard −110 (no official odds archive exists); 2-leg parlays at 2.646×; pushes void.</li>
<li>ML strategies are signal-only: no opening ML odds archive exists anywhere.</li>
<li>Entry price = opening number where archived (2013-2021), else the archived market line (labelled).</li>
</ul>
<h2>Verification protocol</h2>
<ul>
<li>Every table row on this site carries a source link (official where it exists; labelled third-party otherwise).</li>
<li>2026 standings recomputed from the feed match the official capture <strong>32/32, 0 mismatches</strong>.</li>
<li>Live spot checks 2026-11-14: official game-page URL pattern resolves; NFC East records 4/4 match.</li>
<li>Line conventions verified by outcome-based tests (7+ favorites' win rates; settlement agreement 99.8%).</li>
<li>Build-time verifier: every row must keep its source link or the build fails (engine/verify.py).</li>
</ul>
<h2>What is deliberately absent</h2>
<ul>
<li>Same-game prop correlations: blank — no verifiable prop-results source ({plink("pages/decisions.html", "DEC-M4")}).</li>
<li>Opening numbers 2022-2026: blank — no archive ({plink("pages/flagged.html", "FLAG-M2")}).</li>
<li>Depth strings for 24 teams: blank — no captured chart ({plink("pages/flagged.html", "FLAG-M5")}).</li>
<li>Any claim that a strategy beats the market: none exists; gates failed ({plink("pages/gates.html", "Gates")}).</li>
</ul>
<p class="small">Snapshot store: {len(snap):,} rows · results feed: {qc['n_rows']:,} rows ·
manifest with SHA-256 of every data file: <code>data/manifest.json</code>.</p>
"""
    page("pages/methods.html", "Methods & verification", body)

def main():
    build_index()
    build_results_feed()
    build_snapshots()
    build_origination()
    build_leaderboard()
    build_gates()
    build_injuries()
    build_correlations()
    build_suggestions()
    build_decisions()
    build_flagged()
    build_sources()
    build_methods()
    css = """:root{--bg:#0e1116;--panel:#151a21;--panel2:#1b222b;--ink:#e8edf4;--mut:#8b98a9;--acc:#4da3ff;--ok:#3fb972;--warn:#e3b341;--bad:#e5534b;--line:#2a3340}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 -apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:0 18px}
.top{background:var(--panel);border-bottom:1px solid var(--line)}
.brand{padding:16px 0 6px;font-size:22px;font-weight:700}
.brand .tagline{font-size:12px;color:var(--mut);font-weight:400;margin-left:10px}
.mainnav{display:flex;flex-wrap:wrap;gap:2px 14px;padding:8px 0 12px}
.mainnav a{color:var(--mut);text-decoration:none;font-size:13.5px;padding:3px 6px;border-radius:6px}
.mainnav a:hover{color:var(--ink);background:var(--panel2)}
.mainnav a.active{color:var(--acc);background:var(--panel2)}
h1{font-size:26px;margin:26px 0 4px}
.subtitle{color:var(--mut);margin:0 0 18px}
h2{font-size:18px;margin:28px 0 10px;border-bottom:1px solid var(--line);padding-bottom:6px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin:18px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px;text-decoration:none;color:inherit;display:block}
.card:hover{border-color:var(--acc)}
.kpi{font-size:24px;font-weight:700;color:var(--acc)}
.kpi-l{font-size:13px;margin-top:2px}
.kpi-d{font-size:12px;color:var(--mut);margin-top:4px}
.callout{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--acc);border-radius:8px;padding:12px 16px;margin:16px 0;font-size:14.5px}
.callout.warn{border-left-color:var(--warn)}
.callout.note{border-left-color:var(--mut)}
.tblwrap{overflow-x:auto;border:1px solid var(--line);border-radius:8px;margin:12px 0 20px}
table{border-collapse:collapse;width:100%;font-size:13.5px;background:var(--panel)}
th{background:var(--panel2);color:var(--mut);text-align:left;padding:8px 10px;font-weight:600;white-space:nowrap;border-bottom:1px solid var(--line)}
td{padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}
tr:last-child td{border-bottom:none}
tbody tr:hover{background:var(--panel2)}
a{color:var(--acc)}
.small{color:var(--mut);font-size:12.5px}
.foot{color:var(--mut);font-size:12.5px;margin:30px auto 40px;border-top:1px solid var(--line);padding-top:14px}
.chip{display:inline-block;font-size:11px;padding:1px 7px;border-radius:99px;border:1px solid var(--line);color:var(--mut);white-space:nowrap}
.chip.ok{border-color:var(--ok);color:var(--ok)}
.chip.off{border-color:var(--acc);color:var(--acc)}
.chip.third{border-color:var(--warn);color:var(--warn)}
.chip.flag{border-color:var(--bad);color:var(--bad)}
.mark{font-weight:700}
.mark.pass{color:var(--ok)}.mark.fail{color:var(--bad)}.mark.na{color:var(--mut)}
ul{margin:8px 0 8px 18px;padding:0}li{margin:4px 0}
code{background:var(--panel2);border-radius:4px;padding:1px 5px;font-size:12.5px}"""
    os.makedirs(ASSETS, exist_ok=True)
    with open(os.path.join(ASSETS, "style.css"), "w") as f:
        f.write(css)
    print("site built:", "13 pages + assets/style.css")

if __name__ == "__main__":
    main()
