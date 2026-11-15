<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dashboard · NFL Decision Desk</title>
<style>
:root{--ink:#10151c;--ink2:#3b4654;--ink3:#67717f;--bg:#f6f7f9;--panel:#fff;--line:#e2e6eb;
--brand:#0b5cd5;--ok:#0f7b4f;--okbg:#e7f6ee;--warn:#a3560a;--warnbg:#fdf1e2;
--bad:#a3182a;--badbg:#fdecee;--info:#0b5cd5;--infobg:#eaf1fd;
--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--brand);text-decoration:none}a:hover{text-decoration:underline}
code{font-family:var(--mono);font-size:.88em;background:#eef1f5;padding:.1em .35em;border-radius:4px}
.wrap{display:flex;min-height:100vh;align-items:flex-start}
.side{width:248px;flex:0 0 248px;background:#0f1621;color:#cfd7e3;padding:20px 14px 40px;
position:sticky;top:0;max-height:100vh;overflow-y:auto}
.side .brand{color:#fff;font-weight:700;font-size:16px;display:block}
.side .brand span{color:#8fa2bb;font-weight:500;font-size:11.5px;display:block;margin-top:3px}
.side .grp{font-size:10px;text-transform:uppercase;letter-spacing:.09em;color:#7c8ba1;margin:18px 8px 6px}
.side a.nav{display:block;padding:6px 9px;border-radius:7px;color:#cfd7e3;font-size:13px;line-height:1.35}
.side a.nav:hover{background:#1a2331;color:#fff;text-decoration:none}
.side a.nav.active{background:#1d2c42;color:#fff;font-weight:600}
.side .foot{margin-top:24px;font-size:11px;color:#7c8ba1;border-top:1px solid #1e2836;padding-top:12px}
.main{flex:1 1 auto;min-width:0;padding:26px 30px 60px;max-width:1400px}
.crumb{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--ink3);margin-bottom:4px}
h1{font-size:26px;line-height:1.25;margin:2px 0 10px;letter-spacing:-.2px}
h2{font-size:18px;margin:32px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h3{font-size:15px;margin:20px 0 8px}
p{margin:0 0 12px;color:var(--ink2)}
p.lede{font-size:15.5px;color:var(--ink);max-width:80ch}
.muted{color:var(--ink3);font-size:13px}
table{border-collapse:collapse;width:100%;font-size:13px;margin:10px 0 18px;background:var(--panel)}
th{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--ink3);
background:#f2f4f7;padding:8px 9px;border-bottom:1px solid var(--line);vertical-align:bottom}
td{padding:7px 9px;border-bottom:1px solid var(--line);vertical-align:top}
tr:hover td{background:#fafbfc}
.num{font-family:var(--mono);font-size:12.5px;white-space:nowrap}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:8px;margin:10px 0 18px}
.scroll table{margin:0;border-radius:0}
.badge{display:inline-block;font-size:10.5px;font-weight:700;letter-spacing:.04em;
padding:1px 6px;border-radius:5px;text-transform:uppercase;white-space:nowrap}
.b-ok{background:var(--okbg);color:var(--ok)}.b-warn{background:var(--warnbg);color:var(--warn)}
.b-bad{background:var(--badbg);color:var(--bad)}.b-info{background:var(--infobg);color:var(--info)}
.b-n{background:#eef1f5;color:var(--ink3)}
.blank{color:#9aa4b1;font-style:italic;font-size:12px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(178px,1fr));gap:10px;margin:14px 0 8px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:12px 13px}
.card .k{font-size:22px;font-weight:700;letter-spacing:-.4px;line-height:1.15}
.card .l{font-size:11.5px;color:var(--ink3);margin-top:3px;line-height:1.35}
.card.good .k{color:var(--ok)}.card.warn .k{color:var(--warn)}.card.bad .k{color:var(--bad)}
.note{border-left:3px solid var(--brand);background:var(--infobg);padding:10px 13px;
border-radius:0 7px 7px 0;margin:14px 0;font-size:13px;color:#1c3a63}
.note.warn{border-color:var(--warn);background:var(--warnbg);color:#5d3308}
.note.bad{border-color:var(--bad);background:var(--badbg);color:#6d101d}
.note.ok{border-color:var(--ok);background:var(--okbg);color:#0a4d33}
footer{margin-top:44px;padding-top:14px;border-top:1px solid var(--line);
font-size:12px;color:var(--ink3);max-width:95ch}
.src{font-size:11.5px;white-space:nowrap}
details{margin:8px 0}summary{cursor:pointer;font-weight:600;font-size:13.5px;color:var(--ink)}
.kv{font-size:12.5px}.kv b{color:var(--ink)}
@media(max-width:860px){.wrap{flex-direction:column}.side{width:100%;flex:none;position:static;
max-height:none}.main{padding:18px 14px 50px}}
</style></head><body><div class="wrap">
<nav class="side">
<span class="brand">NFL Decision Desk<span>own lines · gates · honest uncertainty</span></span>
<div class="grp">Start here</div>
<a class="nav{ACT}" href="{UP}index.html">Dashboard &amp; readiness</a>
<a class="nav{EXEC}" href="{UP}pages/executive-summary.html">Executive summary</a>
<div class="grp">Data</div>
<a class="nav{FX}" href="{UP}pages/fixtures.html">Results &amp; fixture context</a>
<a class="nav{AV}" href="{UP}pages/availability.html">Availability (injuries)</a>
<a class="nav{PR}" href="{UP}pages/prices.html">Prices &amp; own lines</a>
<div class="grp">Model &amp; scoring</div>
<a class="nav{MD}" href="{UP}pages/model.html">Model &amp; own probabilities</a>
<a class="nav{LD}" href="{UP}pages/leaderboard.html">Leaderboard &amp; luck</a>
<a class="nav{CR}" href="{UP}pages/correlations.html">Correlations</a>
<a class="nav{GV}" href="{UP}pages/governance.html">Pre-registration &amp; gates</a>
<div class="grp">Decide</div>
<a class="nav{QU}" href="{UP}pages/questions.html">Questions register</a>
<a class="nav{SG}" href="{UP}pages/suggestions.html">Suggestions</a>
<a class="nav{RV}" href="{UP}pages/repo-review.html">Repo review</a>
<a class="nav{FL}" href="{UP}pages/flagged.html">⚑ Flagged for review</a>
<div class="grp">Sources</div>
<a class="nav{SR}" href="{UP}pages/sources.html">Every source read</a>
<div class="foot">Research notebook. No wagering is offered or implied.
Session <code>arena/e0ed20d1-own4</code>.</div>
</nav>
<main>
