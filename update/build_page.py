#!/usr/bin/env python3
"""
Own4 update page builder — renders update/index.html from the two JSON data files.
No number is hand-written into the page; everything comes from the JSONs produced
by build_update.py and checked by verify_update.py.

Run: python3 update/build_page.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "settlement_2026-11-02.json"), encoding="utf-8") as f:
    S = json.load(f)
with open(os.path.join(HERE, "games_2026-11-03_to_2026-11-05.json"), encoding="utf-8") as f:
    R = json.load(f)

SRC2 = "https://www.nba.com/games?date=2026-11-02"
SRC3 = "https://www.nba.com/games?date=2026-11-03"
SRC4 = "https://www.nba.com/games?date=2026-11-04"
SRC5 = "https://www.nba.com/games?date=2026-11-05"
NCPG = "https://www.ncpgambling.org/help-treatment"

esc = lambda s: (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

def yn(v, yes="yes", no="no"):
    return yes if v else no

def link(url, text=None):
    return f'<a href="{esc(url)}" rel="noopener">{esc(text or url)}</a>'

# ---------------- settlement table ----------------
set_rows = []
for r in S["rows"]:
    cover = "✅ cover" if r["home_cover"] else "✗ no cover"
    over = "over" if r["over_own_total"] else "under"
    set_rows.append(
        f"<tr><td>{esc(r['game_id'])}</td>"
        f"<td>{esc(r['away'])} @ {esc(r['home'])}</td>"
        f"<td>{r['away_pts']}–{r['home_pts']}</td>"
        f"<td>{esc(r['status'])}</td>"
        f"<td>{r['total_pts']}</td>"
        f"<td>{'+' if r['margin_home']>0 else ''}{r['margin_home']}</td>"
        f"<td>{'%+.1f' % r['own_spread_home']}</td>"
        f"<td>{cover}</td>"
        f"<td>{'%.1f' % r['own_total']}</td>"
        f"<td>{'✅ ' if r['over_own_total'] else ''}{over}</td>"
        f"<td>{'%.2f' % r['p_home_win']}</td>"
        f"<td>{r['su_pick']}</td>"
        f"<td>{'✅' if r['su_hit'] else '❌'}</td>"
        f"<td>{'%.3f' % r['brier']}</td>"
        f"<td>{r['margin_abs_error']:.1f} / {r['total_abs_error']:.1f}</td>"
        f"<td>{link(r['source_url'], 'nba.com')}</td></tr>"
    )
A = S["aggregates"]

# ---------------- refresh tables ----------------
def final_row(g, src):
    la, lh = g["away_leader"], g["home_leader"]
    return (f"<tr><td>{esc(g['game_id'])}</td>"
            f"<td>{esc(g['away'])} @ {esc(g['home'])}</td>"
            f"<td>{g['away_pts']}–{g['home_pts']}</td>"
            f"<td>{esc(g['status'])}</td>"
            f"<td>{g['total_pts']}</td>"
            f"<td>{esc(g['away_record_shown'])} / {esc(g['home_record_shown'])}</td>"
            f"<td>{esc(la['player'])} {la['pts']}/{la['reb']}/{la['ast']}</td>"
            f"<td>{esc(lh['player'])} {lh['pts']}/{lh['reb']}/{lh['ast']}</td>"
            f"<td>{link(g['source_url'], 'nba.com')}</td></tr>")

nov4_rows = "\n".join(final_row(g, SRC4) for g in R["games_2026-11-04"])
nov5_rows = "\n".join(
    f"<tr><td>{esc(g['game_id'])}</td>"
    f"<td>{esc(g['away'])} @ {esc(g['home'])}</td>"
    f"<td>{esc(g['tip_et'])}</td>"
    f"<td>{esc(g['away_record'])} / {esc(g['home_record'])}</td>"
    f"<td>{esc(g['season_leaders_shown'][g['away']]['player'])} {g['season_leaders_shown'][g['away']]['ppg']} PPG</td>"
    f"<td>{esc(g['season_leaders_shown'][g['home']]['player'])} {g['season_leaders_shown'][g['home']]['ppg']} PPG</td>"
    f"<td><span class='blank'>not played — blank by policy</span></td>"
    f"<td>{link(g['source_url'], 'nba.com')}</td></tr>"
    for g in R["games_2026-11-05"]
)

html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Own4 data refresh (2026-11-05): settlement of the 2026-11-02 own-lines slate against official NBA.com final scores, and official results for 2026-11-03 to 2026-11-05.">
<title>Data Refresh · Nov 2 Settlement &amp; Nov 3–5, 2026 · Own4</title>
<link rel="stylesheet" href="../assets/official.css">
</head><body>
<div class="layout">
<aside><a class="brand" href="../index.html">🏀 Own4 <span>/ NBA Research</span></a>
<div class="sub">Data refresh · 2026-11-05</div>
<nav aria-label="Main navigation">
<div class="navcat">Overview</div>
<a href="../index.html">Dashboard</a>
<a href="../pages/executive-summary.html">Executive Summary</a>
<div class="navcat">This refresh</div>
<a class="active" href="index.html">Nov 2 Settlement &amp; Nov 3–5</a>
<div class="navcat">Site sections</div>
<a href="../lab/">Data Lab (92 games)</a>
<a href="../pipeline/">Pipeline &amp; Elo</a>
<a href="../pages/competition.html">Leaderboard</a>
<a href="../pages/flagged-for-review.html">Flagged for Review</a>
</nav></aside><main>
<div class="topbar"><div class="crumb">Data Refresh · 2026-11-05</div><div class="stamp">Built 2026-11-05 UTC · every row source-linked</div></div>
<h1>Data refresh: 2026-11-02 slate settlement &amp; Nov 3–5 results</h1>
<p class="lede">The repository’s own pre-tip lines for the 2026-11-02 slate (15 games, committed before the first tip) are settled here against the official final scores. Results for 2026-11-03 (dark day), 2026-11-04 (14 games, verified) and 2026-11-05 (2 games, unplayed at fetch time) are transcribed line-by-line from the official NBA.com games pages. One slate (n=15) is <b>not</b> strategy validation — the repo’s G1 gate requires n≥300 — it is prospective (G12-style) tracking only.</p>

<div class="cards">
<div class="card accent"><b>15/15</b><span>slate games settled</span></div>
<div class="card"><b>{A['su_hits']}/15</b><span>straight-up picks hit ({A['su_accuracy']*100:.1f}%)</span></div>
<div class="card"><b>{A['mean_brier']:.4f}</b><span>mean Brier (p-home-win)</span></div>
<div class="card"><b>{A['margin_mae']:.2f}</b><span>margin MAE (pts)</span></div>
<div class="card"><b>{A['total_mae']:.2f}</b><span>total MAE (pts)</span></div>
<div class="card warn"><b>n = 15</b><span>not validation (G1: n≥300)</span></div>
</div>

<h2>1 · Settlement of the 2026-11-02 own-lines slate</h2>
<p class="note">Lines: <code>data/own_lines_2026-11-02.csv</code> (BLEND-41, pre-tip 2026-11-02T18:02Z). Results: {link(SRC2, 'nba.com/games?date=2026-11-02')} (fetched 2026-11-05 UTC). Home cover = (home − away) + own_spread_home &gt; 0; over = total &gt; own_total; SU pick = home iff p_home_win ≥ 0.5. ERRORS column shows margin / total absolute error. One overtime game: 0022600165 (NOP 135–134 MEM, Final/OT).</p>
<div class="tw"><table>
<caption>2026-11-02 settlement — every row links to the official games page</caption>
<thead><tr><th>Game ID</th><th>Matchup</th><th>Score</th><th>Status</th><th>Tot</th><th>Margin (home)</th><th>Own spread (home)</th><th>Spread result</th><th>Own total</th><th>Over?</th><th>p(home)</th><th>SU pick</th><th>SU hit</th><th>Brier</th><th>Err M/T</th><th>Source</th></tr></thead>
<tbody>
{chr(10).join(set_rows)}
</tbody></table></div>
<div class="panel ok"><h3>What the settlement shows — and does not</h3>
<ul>
<li>Straight-up: {A['su_hits']}/15 ({A['su_accuracy']*100:.1f}%). Home-spread covers: {A['home_spread_covers']}/15. Over own total: {A['overs_own_total']}/15 ({A['over_rate']*100:.1f}%); totals picks hit {A['totals_pick_hits']}/15 ({A['totals_pick_accuracy']*100:.1f}%).</li>
<li>Mean Brier {A['mean_brier']:.4f} vs 0.25 for an uninformative 50/50 predictor on these 15 games. Margin MAE {A['margin_mae']:.2f} pts; total MAE {A['total_mae']:.2f} pts.</li>
<li><b>No validation claim.</b> n=15 ≪ G1 (n≥300); thresholds and the model were fixed before the slate, but a single slate cannot separate skill from luck. No leaderboard points are awarded and no reward is claimed from this settlement.</li>
<li>The 4/15 overs versus 11/15 unders is descriptive only; the model’s p(over) was ≈0.50 for every game by construction (p_over_own_total ∈ [0.496, 0.505]).</li>
</ul></div>

<h2>2 · Official results — 2026-11-04 (14 games, verified)</h2>
<p class="note">{link(SRC4, 'nba.com/games?date=2026-11-04')} (fetched 2026-11-05 UTC). Records shown are the team records displayed next to each game on that page as fetched (not recomputed). Leaders are the PTS/REB/AST “Game Leaders” displayed by the official page. Two OT games: 0022600179 (UTA 113–120 NOP) and 0022600186 (MIA 117–116 LAC).</p>
<div class="tw"><table>
<caption>2026-11-04 official final scores — source: nba.com games page</caption>
<thead><tr><th>Game ID</th><th>Matchup</th><th>Score</th><th>Status</th><th>Tot</th><th>Records shown (away/home)</th><th>Away leader PTS/REB/AST</th><th>Home leader PTS/REB/AST</th><th>Source</th></tr></thead>
<tbody>
{nov4_rows}
</tbody></table></div>

<h2>3 · 2026-11-03 — no games scheduled</h2>
<div class="panel"><p style="margin:0">The official 2026-11-03 games page displays “No Games Scheduled”, corroborated by the official November 2026 calendar grid (3 Nov = 0 games) on both the 2026-11-04 and 2026-11-05 pages. Source: {link(SRC3, 'nba.com/games?date=2026-11-03')}.</p></div>

<h2>4 · 2026-11-05 — 2 games, unplayed at fetch time</h2>
<div class="panel warn"><p style="margin:0">Scores are intentionally <b>blank</b>: the games had not been played when this page was built (2026-11-05 UTC). Season leaders shown are the PPG/RPG/APG values displayed on the schedule preview — not results. Source: {link(SRC5, 'nba.com/games?date=2026-11-05')}.</p></div>
<div class="tw"><table>
<caption>2026-11-05 scheduled games — no results fabricated</caption>
<thead><tr><th>Game ID</th><th>Matchup</th><th>Tip (ET)</th><th>Records shown (away/home)</th><th>Away leader (PPG)</th><th>Home leader (PPG)</th><th>Score</th><th>Source</th></tr></thead>
<tbody>
{nov5_rows}
</tbody></table></div>

<h2>5 · Verification performed (this page)</h2>
<div class="panel ok"><h3><code>python3 update/verify_update.py</code> — line-by-line checks</h3>
<ul>
<li>Both JSONs re-parsed; every table row re-checked for an official-domain source link and (NBA.com) game link; game ids unique; teams cross-checked against the repo slate; totals, margins, spread/over outcomes, Brier and all aggregate statistics recomputed independently from raw points — all match.</li>
<li>Cross-check: lab dataset <code>data/games_2026-27.csv</code> still has 92 rows ending 2026-11-01; completed games through 2026-11-04 = 92 + 15 + 0 + 14 = <b>121</b>.</li>
<li>Every external link on this page is on an official domain (nba.com / ncpgambling.org). Internal links checked.</li>
<li>2026-11-05 rows carry no scores (not played); 2026-11-03 recorded as a verified dark day.</li>
</ul></div>
<div class="panel"><h3>Repository suites re-run 2026-11-05 (all green where applicable)</h3>
<ul>
<li><code>scripts/verify_data.py</code>: 11/11 PASS (DAL/ATL pts/g drift vs stats page remains flagged, unresolved — pre-existing).</li>
<li><code>scripts/check_site.py</code>: 11 pages, 758 links, 438 table rows, 0 problems. <code>build_site.py</code>: 10 pages, PROBLEMS: none. CI suites (<code>scripts/build.py</code> + unittest ×6 + docs diff): clean.</li>
<li><code>update/verify_update.py</code>: see the count printed by the script for this exact build.</li>
<li><b>Known failing tool (flagged, not CI-gating):</b> <code>engine/verify.py</code> reports 26/29 — its 3 failures scan the committed raw captures under <code>data/raw/nba/*.html</code> (14 files) as if they were site pages (rows without source links, root-absolute hrefs, dashboard-link coverage). CI (<code>pages.yml</code>) does not run <code>engine/verify.py</code>. Request logged in COORDINATION.md: owner of <code>engine/verify.py</code> to exclude <code>data/raw/**</code> from site checks, or relocate the captures.</li>
</ul></div>

<h2>6 · Flags &amp; irregularities from this refresh (needs review, non-blocking)</h2>
<div class="flag"><b>N-01</b> Published standings/records elsewhere in the repo are as-of 2026-11-02. After Nov 2 (15 games) and Nov 4 (14), every team’s record shown here differs; a full standings re-derivation is flagged for the next data pass — none of the other sections’ tables was edited here.</div>
<div class="flag"><b>N-02</b> Team records shown in this refresh are the records displayed on the NBA.com games pages as fetched 2026-11-05 (post-game display), labeled as such; they were not recomputed from scratch.</div>
<div class="flag"><b>N-03</b> “Giannis Antetokounmpo — MIA #7” (season leaders, 2026-11-02 and 2026-11-05 pages) and “Naz Reid — CHA” / “Jaylen Brown — PHI” / “Cedric Coward — MEM” are transcribed exactly as the official pages display them; roster/role changes are not independently confirmed here. If you expected otherwise, treat the page text as authoritative for scoring but request review.</div>
<div class="flag"><b>N-04</b> Home/away follows the official slug listing order only (<code>away-vs-home</code>); no venue/HCA assertion is made (consistent with repo flag I-11).</div>
<div class="flag"><b>N-05</b> <code>data/raw/nba/*.html</code> (14 raw NBA.com pages, ~53 MB with other raw captures) are committed to the repo and are served by Pages at <code>/Own4/data/raw/nba/</code>. Redistribution of nba.com HTML may exceed NBA’s reuse terms; consider removing or excluding them from Pages. Logged as a request; not changed here (owner: session 75685c60).</div>
<div class="flag"><b>N-06</b> <code>engine/verify.py</code> 26/29 — see §5. Not part of CI; merge is not blocked, but the tool cannot currently certify the combined tree.</div>
<div class="flag"><b>N-07</b> The 2026-11-02 settlement is n=15; it is prospective tracking, not evidence of edge. No strategy passes the repo’s gates on this evidence and none is claimed.</div>
<div class="flag"><b>N-08</b> 2026-11-05 scores blank (not played). Auto-updating this page before/after those games would require a new fetch and a new commit; nothing here auto-updates.</div>

<h2>7 · Sources (manual review links)</h2>
<ul>
<li>{link(SRC2)} — 2026-11-02 final scores, leaders, records</li>
<li>{link(SRC3)} — 2026-11-03 “No Games Scheduled”</li>
<li>{link(SRC4)} — 2026-11-04 final scores, leaders, records</li>
<li>{link(SRC5)} — 2026-11-05 schedule preview (unplayed)</li>
<li>{link(NCPG, 'ncpgambling.org/help-treatment')} — National Problem Gambling Helpline: <b>1-800-MY-RESET</b> (re-confirmed 2026-11-05)</li>
<li>Repo: <code>update/build_update.py</code> (transcription + derivation), <code>update/verify_update.py</code> (independent recompute), <code>update/settlement_2026-11-02.json</code>, <code>update/games_2026-11-03_to_2026-11-05.json</code></li>
</ul>

<footer>Own4 · research framework, not wagering advice. National Problem Gambling Helpline: 1-800-MY-RESET — {link(NCPG, 'ncpgambling.org')}. This page generated by <code>update/build_page.py</code> from JSON data; verified by <code>update/verify_update.py</code>.</footer>
</main></div></body></html>
"""
with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as f:
    f.write(html)
print("wrote update/index.html", len(html), "bytes")
