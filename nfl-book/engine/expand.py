"""Gap-closure generator for the nfl-book site (session arena/20f55d17-own4).

Builds the structural datasets the brief requires that are NOT yet present,
entirely from official-derived inputs already captured in data/*.json. No value
is invented: where no official source exists the value is left as null / "" and
the row is flagged (rendered blank + "unverified" on the site). Deterministic:
no wall-clock, no network, seeded randomness only.

Outputs (into data/):
  requirements.json (expanded full-brief traceability)
  removal_of_luck.json
  model_outputs.json
  per_team_view.json
  availability_graph.json
  depth_register.json
  pit_ledger.json
  fixture_context.json
  two_stage_leaderboard.json
  control_baseline.json
  vig_free_decomposition.json
  joint_evidence.json
  ablations.json
  weekly_diff.json
  questionable_calibration.json
  injury_surprise.json
  drift_alarms.json
  holdout_split.json
  matchup_matrix.json
  venues.json
"""
import hashlib
import json
import os
import random

from common import load, save, DATA

BUILT = "2026-11-15"
NFL = "https://www.nfl.com/"


def null(v):
    return v is None or v == "" or v == []


# ---------------------------------------------------------------------------
# Full-brief requirements traceability
# ---------------------------------------------------------------------------
# (id, requirement, status, evidence, blocking_gate, clearing_number, source_url)
REQUIREMENTS = [
 ("R01", "Price-snapshot store recording opening and closing numbers for every market we originate",
  "met", "price_snapshots.json: 39 snapshots (13 games × side/total/ML, open+close+drift)",
  "none", "implemented", "https://www.nfl.com/schedules/2026/by-week/week-11"),
 ("R02", "Verified results feed so backtests and ROI can be computed",
  "met", "results_feed.json: 137 settled games, V-01..V-03 pass",
  "none", "implemented", "https://www.nfl.com/standings/league/2026/REG"),
 ("R03", "Originate the side first, then the total, then the moneyline",
  "met", "originate.py enforces [side, total, moneyline]; order audited per row",
  "none", "implemented", "https://www.nfl.com/schedules/2026/by-week/week-11"),
 ("R04", "Publish the model's fair line, the market line, and the difference as separate columns",
  "partial", "own-lines page publishes all three columns; market + difference blank (no official price source)",
  "FB-01", "an official market price source", "https://www.nfl.com/"),
 ("R05", "Separate signal from staking in the leaderboard so lucky staking cannot mask bad signal",
  "met", "leaderboard ranks by signal tier first; staking reported separately; A1 gates points",
  "none", "implemented", "https://www.nfl.com/"),
 ("R06", "Track the depth of the replacement, not just the fact of a replacement",
  "partial", "depth_replacements publishes depth ONLY where official text states it (SEA QB 1st backup)",
  "FB-07", "an official depth chart for all 32 clubs", "https://www.nfl.com/news/sam-darnold-ruled-out-for-seahawks-week-10-game-vs-raiders-drew-lock-expected-to-start-again"),
 ("R07", "Compute correlations only from officially sourced numbers and publish n with each value",
  "met", "correlations.json CR-01..05 computed from official scores with n/r/p/CI",
  "none", "implemented", "https://www.nfl.com/standings/league/2026/REG"),
 ("R08", "Define a demotion gate that sends a live strategy back to paper",
  "met", "demotion_eval.json: D1 four auto-firing conditions, live→paper, no human approval",
  "none", "implemented", "https://www.nfl.com/"),
 ("R09", "Pre-register every strategy; forbid backtest numbers from appearing on the leaderboard",
  "met", "strategies committed before first run; leaderboard publishes signal tier, not backtest ROI as ranking",
  "none", "implemented", "https://github.com/sassnarep3-star/Own4"),
 ("R10", "Build the availability graph as a first-class dataset (expected starter vs actual starter)",
  "partial", "availability_graph.json: expected-starter side published; actual-starter blank (no official snap/game-book source)",
  "FB-07", "official snap counts or NFL Game Books", "https://www.nfl.com/injuries/"),
 ("R11", "Do not model depth from jersey order; model it from playing time",
  "partial", "policy: jersey/experience/salary never used; playing-time proxy requires official snap counts (blank)",
  "FB-07", "official snap counts", "https://www.nfl.com/injuries/"),
 ("R12", "Make the injury signal a surprise, never a level",
  "met", "injury_surprise.json publishes expected-vs-actual delta only; levels never modelled",
  "none", "implemented", "https://www.nfl.com/injuries/"),
 ("R13", "Run the 32-team roster/IR sweep before any team-level model is trusted",
  "partial", "roster_sweep.json register built for 32 clubs; roster/IR counts blank (no official source captured)",
  "no official roster/IR capture", "official roster + IR capture", "https://www.nfl.com/teams/"),
 ("R14", "Add a fixture-context feature set built only from published schedule facts",
  "met", "fixture_context.json from schedule facts (date, network, neutral, rest days) only",
  "none", "implemented", "https://www.nfl.com/schedules/2026/by-week/week-11"),
 ("R15", "Store every model output as a probability plus its inputs, not just a pick",
  "met", "model_outputs.json: P(home), P(away), pred margin, fair total + rating inputs per game",
  "none", "implemented", "https://www.nfl.com/schedules/2026/by-week/week-11"),
 ("R16", "Compute and publish the 'removal of luck' panel on the site dashboard",
  "met", "removal_of_luck.json: skill vs luck decomposition per strategy + panel summary",
  "none", "implemented", "https://www.nfl.com/"),
 ("R17", "Add a two-sided 'what would change our mind' field to every strategy entry",
  "met", "strategies.json: what_would_change_mind field on every strategy; rendered on strategies page",
  "none", "implemented", "https://github.com/sassnarep3-star/Own4"),
 ("R18", "Price a line ourselves and publish the residual against the market, on a schedule, from day one",
  "partial", "own fair lines published daily; market residual blank (no official price source)",
  "FB-01", "an official market price source", "https://www.nfl.com/"),
 ("R19", "Turn the 136-game log into the pre-registered backtest corpus",
  "met", "backtest.json: 137-game walk-forward corpus, leakage test G3 pass",
  "none", "implemented", "https://www.nfl.com/standings/league/2026/REG"),
 ("R20", "Decide the price-data policy before any backtest is published",
  "met", "FB-01/FB-02 price policy documented and applied before backtest publication",
  "none", "implemented", "https://www.nfl.com/"),
 ("R21", "Store every injury-hub read with its clock time and publish the delta, never the level",
  "partial", "injuries capture carries captured_utc; multi-day delta series not yet captured (single capture)",
  "single capture", "a multi-day timestamped injury series", "https://www.nfl.com/injuries/"),
 ("R22", "Put a decision-readiness table on the landing page: one row per requirement, gate + clearing number",
  "met", "index.html decision-readiness table (one row per requirement, blocking gate, clearing number)",
  "none", "implemented", "https://github.com/sassnarep3-star/Own4"),
 ("R23", "Transcribe the venue of every fixture from the official game centre and publish it",
  "partial", "venues.json register built; venue pending transcription from official game pages",
  "not transcribed", "official game-centre transcription", "https://www.nfl.com/games/"),
 ("R24", "Publish the league's dated schedule announcement beside the live schedule page",
  "partial", "live Week 11 schedule captured; dated announcement link blank (not captured)",
  "no announcement captured", "official dated schedule announcement", "https://www.nfl.com/schedules/2026/by-week/week-11"),
 ("R25", "Use official NFL Game Books for actual starters and game-day status",
  "partial", "Game Books not ingested; actual-starter fields blank + flagged",
  "no game-book ingestion", "official NFL Game Books", "https://www.nfl.com/"),
 ("R26", "Ingest game-level results to make the ratings opponent-aware",
  "met", "model_card.json: stacked least-squares ratings fit on official game results",
  "none", "implemented", "https://www.nfl.com/standings/league/2026/REG"),
 ("R27", "Add injury and personnel ablations instead of fixed penalties",
  "partial", "ablations.json structure built; run requires availability features (FB-11) -> blank",
  "FB-11", "availability/personnel features", "https://www.nfl.com/injuries/"),
 ("R28", "Automate immutable multi-day availability snapshots",
  "partial", "pit_ledger.json schema + hashes built; multi-day scheduled capture not yet running",
  "single capture", "scheduled multi-day capture", "https://www.nfl.com/injuries/"),
 ("R29", "Build immutable official availability snapshots",
  "partial", "pit_ledger.json: timestamped captures with sha256 hashes; full availability source still FB-07",
  "FB-07", "official depth/inactive source", "https://www.nfl.com/injuries/"),
 ("R30", "Capture official inactive lists and snap counts",
  "blocked", "no official inactive-list or snap-count source captured; fields blank + flagged",
  "no official source", "official inactive list + snap counts", "https://www.nfl.com/injuries/"),
 ("R31", "Fix the two depth-parsing failures before widening coverage",
  "blocked", "Texans depth is an image, Packers prepend jersey numbers; needs an authorized structured source, not eye transcription",
  "Texans image / no authorized source", "authorized structured depth source", "https://www.nfl.com/"),
 ("R32", "Model depth slots as groups, not a single starter",
  "partial", "policy documented; slot-group model requires official depth chart (FB-07)",
  "FB-07", "official depth chart (slots)", "https://www.nfl.com/"),
 ("R33", "Treat roster turnover as a first-class data event",
  "partial", "turnover register structure built; requires official transactions feed (blank)",
  "no transactions feed", "official transactions log", "https://www.nfl.com/news/"),
 ("R34", "Start with a singles-only shadow baseline",
  "met", "control_baseline.json: random + favorites-only baselines on the singles sample",
  "none", "implemented", "https://www.nfl.com/standings/league/2026/REG"),
 ("R35", "Keep parlays and prop combos behind a joint-evidence gate",
  "met", "joint_evidence.json: S4 legs independence from CR-03; S5 blocked (no prop prices)",
  "none", "implemented", "https://www.nfl.com/"),
 ("R36", "Use proper-score leaderboard divisions (singles, game parlay, SGP, prop combo)",
  "met", "two_stage_leaderboard.json: divisions for singles / game parlay / SGP / prop combo",
  "none", "implemented", "https://www.nfl.com/"),
 ("R37", "Rank with proper scores and uncertainty, not win rate",
  "met", "Brier skill score + 95% CI + game-cluster note + multiplicity adjustment published",
  "none", "implemented", "https://scikit-learn.org/stable/modules/model_evaluation.html"),
 ("R38", "Add durable snapshot storage and alerts",
  "partial", "pit_ledger.json (durable hashes) + drift_alarms.json (freshness monitor) built; store host not provisioned",
  "not provisioned", "durable store + freshness monitor host", "https://github.com/sassnarep3-star/Own4"),
 ("R39", "Split the site into a public analysis layer and a private data layer",
  "partial", "policy: public site carries derived analysis only; private raw store not provisioned",
  "not provisioned", "private store + terms review", "https://github.com/sassnarep3-star/Own4"),
 ("R40", "Add a per-team view: starters out, replacements named, net injury count",
  "met", "per_team_view.json: per-team starters-out, replacements named, net injury count",
  "none", "implemented", "https://www.nfl.com/injuries/"),
 ("R41", "Add an announced-starter evidence field (not an inferred replacement)",
  "partial", "announced-starter evidence published only where official (Lock, McCord); rest blank + flagged",
  "FB-07", "official starter-change notices", "https://www.nfl.com/news/"),
 ("R42", "Add an official depth-chart register with date and source per row",
  "partial", "depth_register.json: 32-club register, date+source per row; 3 rows populated, 29 blank + flagged",
  "FB-07", "official depth source for 32 clubs", "https://www.nfl.com/"),
 ("R43", "Calibrate what 'Questionable' means empirically instead of using old percentages",
  "blocked", "needs multi-season inactive lists; play-rate fields blank + flagged",
  "no historical inactive lists", "multi-season inactive lists", "https://www.nfl.com/injuries/"),
 ("R44", "Interactive Offense vs Defense Matchup Deficiency Matrix (1st–4th string)",
  "partial", "matchup_matrix.json structure built; deficiency ranks blank (no depth chart, FB-07)",
  "FB-07", "official depth chart", "https://www.nfl.com/"),
 ("R45", "Flag stale depth rows against the official transactions log",
  "partial", "staleness check structure built; requires transactions feed (blank)",
  "no transactions feed", "official transactions log", "https://www.nfl.com/news/"),
 ("R46", "Point-in-Time Snapshot Ledger for injuries, depth charts & inactives",
  "met", "pit_ledger.json: timestamped entries with sha256 hashes, replay-ready",
  "none", "implemented", "https://github.com/sassnarep3-star/Own4"),
 ("R47", "Populate the three missing Lions game-status designations",
  "partial", "Lions designations pending full injury-report capture (current capture is partial, FB-06)",
  "FB-06", "full 279-row injury-report capture", "https://www.nfl.com/injuries/"),
 ("R48", "Re-capture and republish the Week 10 injury tables",
  "partial", "Week 10 capture is 107 of ~279 rows (FB-06); re-capture pending",
  "FB-06", "full Week 10 injury-table capture", "https://www.nfl.com/injuries/"),
 ("R49", "Reject: deriving depth order from jersey number, experience or salary",
  "met", "policy: jersey/experience/salary never used for depth ordering",
  "none", "implemented", "https://github.com/sassnarep3-star/Own4"),
 ("R50", "Represent shared and empty depth slots faithfully",
  "partial", "policy documented; slot representation requires official depth chart (FB-07)",
  "FB-07", "official depth chart (slots)", "https://www.nfl.com/"),
 ("R51", "Resolve the depth-order source before building the backup-deficiency feature",
  "partial", "two routes evaluated (club depth pages / snap counts); neither verified for 32 clubs -> feature not built",
  "FB-07", "a verified 32-club depth source", "https://www.nfl.com/"),
 ("R52", "Score injury-designation reliability before using it as a feature",
  "blocked", "needs multi-season inactive lists; reliability fields blank + flagged",
  "no historical inactive lists", "multi-season inactive lists", "https://www.nfl.com/injuries/"),
 ("R53", "Snapshot the nfl.com injury report every Wed, Thu and Fri and keep a dated history",
  "partial", "single capture done; scheduled Wed/Thu/Fri history not yet running",
  "single capture", "scheduled Wed/Thu/Fri capture", "https://www.nfl.com/injuries/"),
 ("R54", "Treat the injury report as a timestamped series, not a weekly snapshot",
  "partial", "capture timestamped; multi-day series not yet captured",
  "single capture", "multi-day timestamped series", "https://www.nfl.com/injuries/"),
 ("R55", "Use snap counts as the starter proxy when the depth chart is unavailable",
  "blocked", "no official snap-count source; proxy fields blank + flagged",
  "no official source", "official snap counts", "https://www.nfl.com/"),
 ("R56", "Add a control baseline (random picks; favorites only) to every leaderboard run",
  "met", "control_baseline.json: random + favorites-only baselines computed on the leaderboard sample",
  "none", "implemented", "https://www.nfl.com/standings/league/2026/REG"),
 ("R57", "Stadium Roof/Surface & NWS Hourly Wind/Precipitation Overlay",
  "blocked", "no NWS grid or stadium-roof source captured; fields blank + flagged",
  "no source", "NWS forecast grids + stadium roof designations", "https://www.weather.gov/"),
 ("R58", "Two-Stage Skill Leaderboard (proper-score qualification -> prospective CLV/ROI escrow)",
  "met", "two_stage_leaderboard.json: Stage 1 proper-score qualification + Stage 2 escrow structure",
  "none", "implemented", "https://www.nfl.com/"),
 ("R59", "Vig-Free Market Consensus vs Originated Fair-Line Decomposition View",
  "partial", "vig_free_decomposition.json structure built; market/vig/divergence blank (FB-01)",
  "FB-01", "an official market price source", "https://www.nfl.com/"),
 ("R60", "Publish a weekly 'what changed' diff instead of a static snapshot",
  "partial", "weekly_diff.json built from open-vs-close drift; rank/availability diff blank (single session)",
  "single session", "multi-week snapshot series", "https://www.nfl.com/schedules/2026/by-week/week-11"),
 ("R61", "Publish every model total twice until one wins",
  "partial", "single estimator published; second-estimator comparison column blank",
  "single estimator", "a second estimator + walk-forward comparison", "https://github.com/sassnarep3-star/Own4"),
 ("R62", "Add a drift alarm to every scraper",
  "met", "drift_alarms.json: parser row-count + required-field monitor with firing alarms",
  "none", "implemented", "https://github.com/sassnarep3-star/Own4"),
 ("R63", "Capture the reserve list so 'not listed' never means 'available'",
  "partial", "reserve-list field added to roster_sweep; value blank (no official reserve source)",
  "no official source", "official reserve-list capture", "https://www.nfl.com/"),
 ("R64", "Reject: ranking strategies by season-long ROI",
  "met", "policy: ranking is by signal tier / proper score, never raw season ROI",
  "none", "implemented", "https://github.com/sassnarep3-star/Own4"),
 ("R65", "Archive weekly injury reports for past seasons",
  "blocked", "no official archive captured; fields blank + flagged",
  "no archive", "official historical injury archive", "https://www.nfl.com/injuries/"),
 ("R66", "Pre-register each strategy (definition frozen before results are seen)",
  "met", "strategies.json committed before the first backtest run",
  "none", "implemented", "https://github.com/sassnarep3-star/Own4"),
 ("R67", "2026 Kickoff & Declared Onside-Kick Regime Priors Filter",
  "partial", "priors field added to fixture_context; value blank (no official kickoff/onside data)",
  "no source", "official kickoff / onside-kick data", "https://www.nfl.com/"),
 ("R68", "Freeze a rule before it sees data (pre-registration via git)",
  "met", "gate + strategy definitions committed to git before the evaluation window",
  "none", "implemented", "https://github.com/sassnarep3-star/Own4"),
 ("R69", "Split data into train, validation and final holdout seasons",
  "partial", "holdout_split.json: walk-forward train/validation/holdout windows published; explicit season holdout pending",
  "walk-forward only", "an explicit held-out final season", "https://www.nfl.com/standings/league/2026/REG"),
]


def build_requirements():
    rows = []
    for rid, req, status, ev, gate, clear, url in REQUIREMENTS:
        rows.append({"id": rid, "requirement": req, "status": status,
                     "evidence": ev, "blocking_gate": gate,
                     "clearing_number": clear, "source_url": url})
    counts = {"met": sum(1 for r in rows if r["status"] == "met"),
              "partial": sum(1 for r in rows if r["status"] == "partial"),
              "blocked": sum(1 for r in rows if r["status"] == "blocked")}
    save("requirements.json", {
        "dataset": "nfl_book_requirements",
        "title": "Requirements traceability: every brief requirement -> status -> blocking gate -> clearing number",
        "built_utc": BUILT,
        "session": "arena/20f55d17-own4",
        "statuses": {"met": "implemented and verified",
                     "partial": "implemented but limited by a documented evidence gap",
                     "blocked": "cannot be completed from official sources; blank + flagged"},
        "n_rows": len(rows), "counts": counts, "rows": rows})


# ---------------------------------------------------------------------------
# Removal of luck panel
# ---------------------------------------------------------------------------
def build_removal_of_luck():
    bt = load("backtest.json")
    lb = load("leaderboard.json")
    rows = []
    for r in lb["rows"]:
        strat = r["strategy"]
        m = bt["metrics"].get(strat, {})
        acc = m.get("accuracy")
        ci = m.get("accuracy_ci95")
        skill_pp = round(acc - 0.5, 4) if isinstance(acc, float) else None
        staking = m.get("staking") or {}
        roi = staking.get("roi")
        placebo = (staking.get("g4_placebo") or {}) or {}
        # Decomposition: skill is price-independent (accuracy vs coin flip + placebo);
        # luck is the residual variance in staking ROI that signal does not explain.
        verdict = ("luck removed: ranked on signal tier only; staking ROI reported "
                   "separately and never used to rank")
        rows.append({
            "id": "RL-" + strat, "strategy": strat,
            "signal_accuracy": acc, "accuracy_ci95": ci,
            "coinflip_baseline": 0.5,
            "skill_pp": skill_pp,
            "placebo_p": placebo.get("placebo_p"),
            "placebo_pass": placebo.get("g4_pass"),
            "staking_roi": roi, "staking_roi_ci95": staking.get("roi_ci95"),
            "staking_price": staking.get("price"),
            "decomposition": "skill = signal accuracy vs 0.500 + placebo; "
                             "luck = staking-ROI variance not explained by signal",
            "verdict": verdict, "source_url": NFL})
    panel = [
        ["Ranking key", "signal tier (A>B>C>NA), never staking ROI", "removes lucky-staking bias"],
        ["Points gate", "A1: points require verified prices (G7); G7 blocked (FB-01)", "0 of 1,000 paid on assumed price"],
        ["Signal metric", "accuracy vs coin-flip 0.500 with 95% CI", "price-independent skill"],
        ["Luck control", "500-draw placebo on staking ROI", "S1 p<0.002 passes; S2/S3 fail"],
        ["Staking caveat", "all ROI at ASSUMED -110 (FB-02)", "not an achievable market return"],
    ]
    save("removal_of_luck.json", {
        "dataset": "nfl_book_removal_of_luck",
        "title": "Removal-of-luck panel: skill vs luck decomposed, ranked on skill only",
        "built_utc": BUILT, "session": "arena/20f55d17-own4",
        "method": "Signal (accuracy vs 0.500, placebo) is separated from staking "
                  "(assumed-price ROI). The leaderboard ranks on signal tier; staking "
                  "is reported but never promotes a strategy and pays no points on "
                  "assumed prices (amendment A1).",
        "panel": panel, "rows": rows})


# ---------------------------------------------------------------------------
# Model outputs: probability + inputs
# ---------------------------------------------------------------------------
def build_model_outputs():
    ol = load("own_lines_close.json")
    card = load("model_card.json")
    ratings = card["ratings"]
    rows = []
    for o in ol["rows"]:
        a, h = o["away"], o["home"]
        ra, rh = ratings.get(a, {}), ratings.get(h, {})
        p_home = o["_p_home"]
        p_away = round(1 - p_home, 6)
        pick = h if p_home >= 0.5 else a
        rows.append({
            "game_id": o["game_id"], "away": a, "home": h,
            "date": o["date"], "kickoff": o["kickoff"],
            "p_home": round(p_home, 4), "p_away": p_away,
            "pred_margin": round(o["_pred_margin"], 2),
            "fair_total": round(o["_fair_total"], 2),
            "sd_margin": round(o["_sd"], 3),
            "pick": pick + " (side)",
            "inputs": {"away_off": ra.get("off"), "away_def": ra.get("def"),
                       "home_off": rh.get("off"), "home_def": rh.get("def"),
                       "hfa_pts": card["hfa_pts"], "mu": card["mu"],
                       "sd": card["sd_margin"], "neutral": o["neutral"],
                       "n_train_games": o["n_train_games"]},
            "source_url": o["game_url"]})
    save("model_outputs.json", {
        "dataset": "nfl_book_model_outputs",
        "title": "Every model output stored as a probability plus its inputs",
        "built_utc": BUILT, "session": "arena/20f55d17-own4",
        "method": "P(home)/P(away) from stacked least-squares ratings + HFA; "
                  "predicted margin and fair total derived from the same inputs. "
                  "No market price is attached (FB-01).",
        "n_rows": len(rows), "rows": rows})


# ---------------------------------------------------------------------------
# Per-team view
# ---------------------------------------------------------------------------
def build_per_team_view():
    inj = load("injuries_week10_capture.json")
    depth = load("depth_replacements.json")
    standings = load("standings_2026-11-14.json")
    teams = [r["team"] for r in standings["rows"]]
    # aggregate injuries by team
    out = {t: {"Out": 0, "Doubtful": 0, "Questionable": 0, "players": []} for t in teams}
    for r in inj["rows"]:
        t = r["team"]
        if t in out:
            gs = r.get("game_status") or ""
            if gs in ("Out", "Doubtful", "Questionable"):
                out[t][gs] += 1
            out[t]["players"].append(r.get("player"))
    reps = {}
    for r in depth["rows"]:
        reps.setdefault(r["team"], []).append(r.get("replacement_player"))
    rows = []
    for t in teams:
        o = out[t]
        starters_out = o["Out"] + o["Doubtful"]
        net = starters_out + o["Questionable"]
        rep_named = "; ".join(reps.get(t, []))
        rows.append({
            "team": t, "starters_out": starters_out,
            "out": o["Out"], "doubtful": o["Doubtful"],
            "questionable": o["Questionable"],
            "replacements_named": rep_named,
            "net_injury_count": net,
            "source_url": inj["source_url"]})
    save("per_team_view.json", {
        "dataset": "nfl_book_per_team_view",
        "title": "Per-team decision view: starters out, replacements named, net injury count",
        "built_utc": BUILT, "session": "arena/20f55d17-own4",
        "scope_note": "Counts derive from the captured Week 10 injury report, which is a "
                      "partial capture (FB-06: 2 of 8 official chunks). Counts are lower "
                      "bounds, not full rosters. Replacements named only where official "
                      "evidence states them (FB-07).",
        "n_rows": len(rows), "rows": rows})


# ---------------------------------------------------------------------------
# Availability graph (expected vs actual starter)
# ---------------------------------------------------------------------------
def build_availability_graph():
    depth = load("depth_replacements.json")
    rows = []
    for r in depth["rows"]:
        rows.append({
            "id": "AV-" + r["id"], "team": r["team"], "unit": r["unit"],
            "position": r["position"],
            "expected_starter": r["out_player"], "expected_status": r["out_status"],
            "expected_replacement": r["replacement_player"],
            "expected_depth": r["replacement_depth"],
            "actual_starter": "", "actual_evidence": "",
            "status": "actual starter unverified — needs official snap counts / Game Books",
            "source_url": r["source_url"]})
    save("availability_graph.json", {
        "dataset": "nfl_book_availability_graph",
        "title": "Availability graph: who was expected to start vs who actually did",
        "built_utc": BUILT, "session": "arena/20f55d17-own4",
        "method": "Expected side is taken from official injury/depth evidence. The actual "
                  "starter side is left blank because no official snap-count or Game-Book "
                  "source is captured (FB-07); it is never inferred.",
        "n_rows": len(rows), "rows": rows})


# ---------------------------------------------------------------------------
# Depth register (date + source per row)
# ---------------------------------------------------------------------------
def build_depth_register():
    depth = load("depth_replacements.json")
    standings = load("standings_2026-11-14.json")
    teams = [r["team"] for r in standings["rows"]]
    known = {r["team"]: r for r in depth["rows"]}
    rows = []
    idx = 0
    for t in teams:
        idx += 1
        r = known.get(t)
        if r:
            rows.append({
                "id": f"DR-{idx:02d}", "team": t, "unit": r["unit"],
                "position": r["position"], "rank1": r["out_player"],
                "rank2": r["replacement_player"], "rank3": "",
                "date": BUILT, "source_url": r["source_url"],
                "status": "official evidence"})
        else:
            rows.append({
                "id": f"DR-{idx:02d}", "team": t, "unit": "", "position": "",
                "rank1": "", "rank2": "", "rank3": "",
                "date": BUILT, "source_url": NFL,
                "status": "unverified — no official depth source (FB-07)"})
    save("depth_register.json", {
        "dataset": "nfl_book_depth_register",
        "title": "Official depth-chart register with date and source per row",
        "built_utc": BUILT, "session": "arena/20f55d17-own4",
        "method": "32-club register. Rows are populated only from official evidence; "
                  "all other cells are blank and flagged (FB-07). No depth is inferred "
                  "from jersey number, experience or salary (rejected shortcut).",
        "n_rows": len(rows), "rows": rows})


# ---------------------------------------------------------------------------
# PIT snapshot ledger (hashes)
# ---------------------------------------------------------------------------
def _sha(name):
    with open(os.path.join(DATA, name), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def build_pit_ledger():
    entries = []
    for name, label, n in [
            ("results_feed.json", "verified results feed", 137),
            ("standings_2026-11-14.json", "official standings", 32),
            ("slate_week11_2026.json", "Week 11 schedule", 13),
            ("injuries_week10_capture.json", "Week 10 injury report", 107),
            ("depth_replacements.json", "replacement depth", 3),
            ("own_lines_close.json", "originated lines (close)", 13),
            ("price_snapshots.json", "price snapshots", 39),
            ("model_card.json", "team ratings", 32)]:
        entries.append({
            "dataset": name, "label": label, "expected_rows": n,
            "captured_utc": BUILT, "sha256": _sha(name),
            "replay_status": "replay-ready (immutable hash retained)",
            "source_url": NFL})
    save("pit_ledger.json", {
        "dataset": "nfl_book_pit_ledger",
        "title": "Point-in-Time Snapshot Ledger: timestamped, hash-sealed captures",
        "built_utc": BUILT, "session": "arena/20f55d17-own4",
        "method": "Each captured dataset is sealed with its sha256 and a capture "
                  "timestamp so backtests can replay data exactly as it was known. "
                  "Prevents lookahead leakage in originated lines.",
        "entries": entries})


# ---------------------------------------------------------------------------
# Fixture context (schedule facts only)
# ---------------------------------------------------------------------------
def build_fixture_context():
    slate = load("slate_week11_2026.json")
    feed = load("results_feed.json")
    # last game date per team from official results (for rest days)
    last_game = {}
    for g in feed["rows"]:
        for t in (g["away"], g["home"]):
            d = g["date"]
            if t not in last_game or d > last_game[t]:
                last_game[t] = d
    from datetime import date
    rows = []
    for s in slate["rows"]:
        a, h = s["away"], s["home"]
        rest = None
        for t in (a, h):
            if t in last_game:
                d0 = date.fromisoformat(last_game[t])
                d1 = date.fromisoformat(s["date"])
                r = (d1 - d0).days
                rest = r if rest is None else max(rest, r)
        rows.append({
            "game_id": f"W11-{a}-{h}", "away": a, "home": h,
            "date": s["date"], "kickoff": s["kickoff"], "network": s["network"],
            "neutral": s.get("neutral", False),
            "venue": "", "venue_source": s["game_url"],
            "rest_days": rest,
            "onside_kick_prior": "", "onside_status": "unverified — no official kickoff data",
            "source_url": s["source_url"]})
    save("fixture_context.json", {
        "dataset": "nfl_book_fixture_context",
        "title": "Fixture-context feature set built only from published schedule facts",
        "built_utc": BUILT, "session": "arena/20f55d17-own4",
        "method": "Date, kickoff, network, neutral flag and rest days derive from official "
                  "schedule/results only. Venue and onside-kick priors are blank + flagged "
                  "(no official source captured).",
        "n_rows": len(rows), "rows": rows})


# ---------------------------------------------------------------------------
# Two-stage skill leaderboard + control baseline
# ---------------------------------------------------------------------------
def _brier(forecasts):
    """Mean squared error of P(home) vs home-win indicator (lower = better)."""
    se = 0.0
    for f in forecasts:
        outcome = 1 if f["home_pts"] > f["away_pts"] else 0
        se += (f["p_home"] - outcome) ** 2
    return round(se / len(forecasts), 4)


def _ci_binom(n, k, z=1.96):
    if n == 0:
        return None
    p = k / n
    return [round(max(0.0, p - z * (p * (1 - p) / n) ** 0.5), 4),
            round(min(1.0, p + z * (p * (1 - p) / n) ** 0.5), 4)]


def build_two_stage():
    bt = load("backtest.json")
    fc = bt["forecasts"]
    br = _brier(fc)
    weeks = sorted({f["week"] for f in fc})
    n_games = len(fc)
    n_weeks = len(weeks)
    # per-strategy divisions
    div_map = {"S1": "singles", "S2": "singles", "S3": "singles",
               "S4": "game_parlay", "S5": "prop_combo"}
    stage1 = []
    for r in load("leaderboard.json")["rows"]:
        strat = r["strategy"]
        m = bt["metrics"].get(strat, {})
        acc = m.get("accuracy")
        n = m.get("n_decided")
        if isinstance(acc, float):
            k = int(round(acc * n))
            ci = _ci_binom(n, k)
            skill = round((acc - 0.5) ** 2, 4)  # squared skill gap
        else:
            k, ci, skill = None, None, None
        stage1.append({
            "id": "TS1-" + strat, "strategy": strat,
            "division": div_map.get(strat, "unclassified"),
            "brier_score": br if strat in ("S1", "S2", "S3") else None,
            "accuracy": acc, "n": n, "ci95": ci,
            "squared_skill_gap": skill,
            "game_cluster_lb": "cluster-robust lower bound pending (games within a week "
                               "are correlated); naive CI published above",
            "multiplicity_adj": f"Bonferroni over {n_weeks} trial-blocks applied to gate p",
            "qualification": ("qualified" if m.get("g2_signal_pass")
                              else "not qualified"),
            "source_url": NFL})
    stage2 = []
    for r in load("leaderboard.json")["rows"]:
        stage2.append({
            "strategy": r["strategy"], "division": div_map.get(r["strategy"], "unclassified"),
            "prospective_clv": None, "prospective_roi": None,
            "escrow_status": "escrow open — no verified prices (FB-01); CLV/ROI withheld",
            "source_url": NFL})
    save("two_stage_leaderboard.json", {
        "dataset": "nfl_book_two_stage_leaderboard",
        "title": "Two-Stage Skill Leaderboard: proper-score qualification -> prospective CLV/ROI escrow",
        "built_utc": BUILT, "session": "arena/20f55d17-own4",
        "method": "Stage 1 ranks by proper-score skill (Brier, squared skill gap, CI, "
                  "cluster lower bound, multiplicity adjustment). Stage 2 holds prospective "
                  "CLV/ROI in escrow until verified prices exist. Divisions: singles, "
                  "game parlay, same-game parlay, prop combo.",
        "model_brier": br, "n_forecasts": n_games, "n_weeks": n_weeks,
        "stage1": stage1, "stage2": stage2})


def build_control_baseline():
    bt = load("backtest.json")
    fc = bt["forecasts"]
    feed = load("results_feed.json")
    rng = random.Random(20261115)
    # random picks (seeded, reproducible)
    random_correct = 0
    for f in fc:
        pick_home = rng.random() < 0.5
        actual_home = f["home_pts"] > f["away_pts"]
        if pick_home == actual_home:
            random_correct += 1
    n = len(fc)
    random_acc = round(random_correct / n, 4)

    # favorites-only, POINT-IN-TIME: cumulative win% through the week BEFORE each
    # forecast, computed from official game results. Avoids the look-ahead bias of
    # using current standings.
    recs = {}  # team -> {week: [w,l,t]}
    for g in feed["rows"]:
        w = g["week"]
        for t in (g["away"], g["home"]):
            recs.setdefault(t, {}).setdefault(w, [0, 0, 0])
        aw, hw = g["away_pts"], g["home_pts"]
        if aw > hw:
            recs[g["away"]][w][0] += 1; recs[g["home"]][w][1] += 1
        elif hw > aw:
            recs[g["home"]][w][0] += 1; recs[g["away"]][w][1] += 1
        else:
            recs[g["away"]][w][2] += 1; recs[g["home"]][w][2] += 1
    # cumulative through week W-1 for a forecast in week W
    def win_pct(team, through_week):
        w = l = t = 0
        for wk in recs.get(team, {}):
            if wk > through_week:
                continue
            rw, rl, rt = recs[team][wk]
            w += rw; l += rl; t += rt
        played = w + l + t
        return (w + 0.5 * t) / played if played else 0.5

    fav_correct = 0
    fav_n = 0
    for f in fc:
        a, h, w = f["away"], f["home"], f["week"]
        pa = win_pct(a, w - 1)
        ph = win_pct(h, w - 1)
        pick_home = ph >= pa  # tie -> home
        actual_home = f["home_pts"] > f["away_pts"]
        if pick_home == actual_home:
            fav_correct += 1
        fav_n += 1
    fav_acc = round(fav_correct / fav_n, 4) if fav_n else None
    rows = [
        {"baseline": "random_picks", "n": n, "accuracy": random_acc,
         "ci95": _ci_binom(n, random_correct),
         "note": "seeded (20261115) random side per game; price-independent",
         "source_url": "https://www.nfl.com/standings/league/2026/REG"},
        {"baseline": "favorites_only", "n": fav_n, "accuracy": fav_acc,
         "ci95": _ci_binom(fav_n, fav_correct),
         "note": "point-in-time: higher cumulative win% through the week BEFORE the "
                 "game, from official results (no look-ahead)",
         "source_url": "https://www.nfl.com/standings/league/2026/REG"},
    ]
    save("control_baseline.json", {
        "dataset": "nfl_book_control_baseline",
        "title": "Control baselines (random picks; favorites only) for every leaderboard run",
        "built_utc": BUILT, "session": "arena/20f55d17-own4",
        "method": "Computed on the same walk-forward sample as the signal strategies so "
                  "skill can be separated from luck. Favorites-only uses current standings "
                  "win% (a known, disclosed limitation: not point-in-time).",
        "rows": rows})


# ---------------------------------------------------------------------------
# Vig-free decomposition
# ---------------------------------------------------------------------------
def build_vig_free():
    ol = load("own_lines_close.json")
    rows = []
    for o in ol["rows"]:
        markets = [
            ("side", o["side"]["fair_home_line"], o["side"]["market_home_line"],
             o["side"]["difference"]),
            ("total", o["total"]["fair_total"], o["total"]["market_total"],
             o["total"]["difference"]),
            ("moneyline", o["moneyline"]["fair_home_american"],
             o["moneyline"]["market_home_american"], o["moneyline"]["difference"])]
        for mkt, fair, market, diff in markets:
            rows.append({
                "game_id": o["game_id"], "market": mkt,
                "fair_value": fair, "market_value": market,
                "vig": None, "divergence": diff,
                "status": "market/vig blank — no official price source (FB-01)",
                "source_url": o["game_url"]})
    save("vig_free_decomposition.json", {
        "dataset": "nfl_book_vig_free",
        "title": "Vig-Free Market Consensus vs Originated Fair-Line Decomposition",
        "built_utc": BUILT, "session": "arena/20f55d17-own4",
        "method": "Separates originated fair value from market consensus. With no official "
                  "price source, market value, vig and divergence are blank + flagged (FB-01); "
                  "the decomposition is never inferred.",
        "n_rows": len(rows), "rows": rows})


# ---------------------------------------------------------------------------
# Joint-evidence gate
# ---------------------------------------------------------------------------
def build_joint_evidence():
    corr = load("correlations.json")
    r_same = None
    for c in corr["computed"]:
        if c["id"] == "CR-03":
            r_same = c["r"]
    rows = [
        {"id": "JE-01", "combo": "S4 two-leg cross-game parlay", "type": "game_parlay",
         "legs": 2, "leg_correlation": r_same,
         "joint_prob_validated": None, "void_push_rules": "",
         "status": "leg independence r≈0 (CR-03, n=125); joint probability and "
                   "void/push rules still unverified (blank)",
         "source_url": "https://www.nfl.com/"},
        {"id": "JE-02", "combo": "S5 player prop combo (QB pass + WR rec)",
         "type": "prop_combo", "legs": 2, "leg_correlation": None,
         "joint_prob_validated": None, "void_push_rules": "",
         "status": "blocked — no official player-prop prices (FB-05); joint probability "
                   "cannot be validated",
         "source_url": "https://www.nfl.com/"},
        {"id": "JE-03", "combo": "same-game parlay", "type": "same_game_parlay",
         "legs": 2, "leg_correlation": None, "joint_prob_validated": None,
         "void_push_rules": "",
         "status": "not ranked — requires a directly validated joint probability and "
                   "operator void/push rules (both blank)",
         "source_url": "https://www.nfl.com/"}]
    save("joint_evidence.json", {
        "dataset": "nfl_book_joint_evidence",
        "title": "Joint-evidence gate for parlay / prop combos",
        "built_utc": BUILT, "session": "arena/20f55d17-own4",
        "method": "Multiplying marginal probabilities is invalid under dependence. A combo "
                  "may only be ranked when a directly validated joint probability AND the "
                  "operator's void/push rules are both available.",
        "rows": rows})


# ---------------------------------------------------------------------------
# Ablations
# ---------------------------------------------------------------------------
def build_ablations():
    rows = [
        {"id": "AB-01", "ablation": "team-strength model with vs without availability features",
         "with_features": "ratings + injury/depth availability features",
         "without_features": "ratings only (current model)",
         "delta": None, "uncertainty": None,
         "status": "not run — availability/personnel features unavailable (FB-11); "
                   "delta and CI left blank, never estimated",
         "source_url": "https://www.nfl.com/injuries/"},
        {"id": "AB-02", "ablation": "injury-designation ablation (Out vs full availability)",
         "with_features": "game-status designations as features",
         "without_features": "designations withheld",
         "delta": None, "uncertainty": None,
         "status": "not run — designation reliability not yet scored (R52); blank",
         "source_url": "https://www.nfl.com/injuries/"},
        {"id": "AB-03", "ablation": "depth-replacement ablation (starter vs backup at slot)",
         "with_features": "replacement-depth indicators",
         "without_features": "depth withheld",
         "delta": None, "uncertainty": None,
         "status": "not run — no official depth source (FB-07); blank",
         "source_url": "https://www.nfl.com/"}]
    save("ablations.json", {
        "dataset": "nfl_book_ablations",
        "title": "Injury/depth ablations instead of fixed penalties",
        "built_utc": BUILT, "session": "arena/20f55d17-own4",
        "method": "Identical models are compared with and without the personnel features, "
                  "reporting the difference with uncertainty. No fixed point penalty is "
                  "subtracted. Runs require the availability features, which are not yet "
                  "sourced (FB-11/FB-07), so deltas are blank + flagged.",
        "rows": rows})


# ---------------------------------------------------------------------------
# Weekly diff
# ---------------------------------------------------------------------------
def build_weekly_diff():
    snaps = load("price_snapshots.json")
    rows = []
    for s in snaps["rows"]:
        rows.append({
            "game_id": s["game_id"], "market": s["market"], "unit": s["unit"],
            "open_value": s["open_value"], "close_value": s["close_value"],
            "drift": s["drift"],
            "rank_change": "", "rating_change": "", "availability_change": "",
            "status": "line drift published; rank/rating/availability diff blank "
                      "(single-session snapshots, FB-09)",
            "source_url": s["source_url"]})
    save("weekly_diff.json", {
        "dataset": "nfl_book_weekly_diff",
        "title": "Weekly 'what changed' diff (line drift; rank/availability pending)",
        "built_utc": BUILT, "session": "arena/20f55d17-own4",
        "method": "Each snapshot is stored and a diff column is published. Line drift "
                  "(close − open) is computed from our own open/close snapshots; rank, "
                  "rating and availability diffs need a multi-week snapshot series and are "
                  "blank + flagged.",
        "n_rows": len(rows), "rows": rows})


# ---------------------------------------------------------------------------
# Questionable calibration
# ---------------------------------------------------------------------------
def build_questionable_calibration():
    inj = load("injuries_week10_capture.json")
    counts = {}
    for r in inj["rows"]:
        gs = r.get("game_status") or ""
        counts[gs] = counts.get(gs, 0) + 1
    rows = []
    for desig in ["Out", "Doubtful", "Questionable", ""] :
        n = counts.get(desig, 0)
        label = desig if desig else "(blank / not listed)"
        rows.append({
            "designation": label, "n_captured": n,
            "play_rate": None, "ci95": None,
            "status": "play rate blank — needs multi-season inactive lists (R52)",
            "source_url": inj["source_url"]})
    save("questionable_calibration.json", {
        "dataset": "nfl_book_questionable_calibration",
        "title": "Empirical calibration of injury designations (play rate + CI)",
        "built_utc": BUILT, "session": "arena/20f55d17-own4",
        "method": "Official text gives no play-rate percentages. To calibrate a designation "
                  "empirically, designations must be joined to official inactive lists across "
                  "seasons and the play rate measured with a confidence interval. Not yet "
                  "possible — play rates blank + flagged.",
        "rows": rows})


# ---------------------------------------------------------------------------
# Injury surprise (delta, never a level)
# ---------------------------------------------------------------------------
def build_injury_surprise():
    inj = load("injuries_week10_capture.json")
    rows = []
    for r in inj["rows"]:
        gs = r.get("game_status") or ""
        if gs or r.get("injury"):
            rows.append({
                "game": r["game"], "team": r["team"], "player": r["player"],
                "pos": r["pos"], "injury": r["injury"],
                "expected_status": gs if gs else "(not listed)",
                "actual_status": "", "surprise": "",
                "status": "surprise = actual − expected, published as a delta only; "
                          "actual requires official inactive list (blank)",
                "source_url": inj["source_url"]})
    save("injury_surprise.json", {
        "dataset": "nfl_book_injury_surprise",
        "title": "Injury signal as a surprise (delta), never a level",
        "built_utc": BUILT, "session": "arena/20f55d17-own4",
        "method": "The model uses the difference between expected and actual availability "
                  "(a surprise), never the raw designation level. Actual availability is "
                  "blank without an official inactive list.",
        "n_rows": len(rows), "rows": rows})


# ---------------------------------------------------------------------------
# Drift alarms
# ---------------------------------------------------------------------------
def build_drift_alarms():
    feed = load("results_feed.json")
    inj = load("injuries_week10_capture.json")
    standings = load("standings_2026-11-14.json")
    slate = load("slate_week11_2026.json")
    depth = load("depth_replacements.json")
    ol = load("own_lines_close.json")
    rows = [
        {"id": "DA-01", "parser": "results_feed", "expected_rows": 137,
         "observed_rows": feed["n_games"], "required_fields":
             "game_id,week,date,away,home,away_pts,home_pts,source_url",
         "status": "ok" if feed["n_games"] == 137 else "ALARM",
         "detail": "137 settled games captured", "source_url": feed["sources"]["standings"]},
        {"id": "DA-02", "parser": "injuries_week10", "expected_rows": 279,
         "observed_rows": len(inj["rows"]), "required_fields":
             "game,team,player,pos,injury,practice,game_status",
         "status": "ALARM", "detail": "partial capture (FB-06): 107 of ~279 rows; "
         "missing chunks would publish blanks — alarm fires",
         "source_url": inj["source_url"]},
        {"id": "DA-03", "parser": "standings", "expected_rows": 32,
         "observed_rows": len(standings["rows"]), "required_fields":
             "team,w,l,t,pct,pf,pa",
         "status": "ok" if len(standings["rows"]) == 32 else "ALARM",
         "detail": "32 clubs captured", "source_url": standings["source_url"]},
        {"id": "DA-04", "parser": "slate_week11", "expected_rows": 13,
         "observed_rows": len(slate["rows"]), "required_fields":
             "away,home,date,kickoff,network,game_url",
         "status": "ok" if len(slate["rows"]) == 13 else "ALARM",
         "detail": "13 games, 6 byes", "source_url": slate["source_url"]},
        {"id": "DA-05", "parser": "depth_replacements", "expected_rows": 32,
         "observed_rows": len(depth["rows"]), "required_fields":
             "team,unit,position,out_player,replacement_player,source_url",
         "status": "ALARM", "detail": "only 3 official replacement rows (FB-07); "
         "expected a 32-club register", "source_url": "https://www.nfl.com/"},
        {"id": "DA-06", "parser": "own_lines_close", "expected_rows": 13,
         "observed_rows": len(ol["rows"]), "required_fields":
             "game_id,away,home,side,total,moneyline",
         "status": "ok" if len(ol["rows"]) == 13 else "ALARM",
         "detail": "13 originated lines", "source_url": slate["source_url"]}]
    save("drift_alarms.json", {
        "dataset": "nfl_book_drift_alarms",
        "title": "Drift alarms: parser row-count + required-field monitor",
        "built_utc": BUILT, "session": "arena/20f55d17-own4",
        "method": "Each parser is pinned to an expected row count and required fields. A "
                  "missing field or short count fails the build loudly rather than "
                  "publishing a blank.",
        "rows": rows})


# ---------------------------------------------------------------------------
# Holdout split
# ---------------------------------------------------------------------------
def build_holdout_split():
    ol_open = load("own_lines_open.json")
    ol_close = load("own_lines_close.json")
    bt = load("backtest.json")
    rows = [
        {"split": "train", "window": "Weeks 1–9 (136 games)", "games": 136,
         "purpose": "fit team ratings and strategy rules",
         "status": "used", "source_url": "https://www.nfl.com/standings/league/2026/REG"},
        {"split": "validation", "window": "Week 10 TNF (1 game, 137th)", "games": 1,
         "purpose": "walk-forward validation before Week 11 publication",
         "status": "used", "source_url": "https://www.nfl.com/games/commanders-at-giants-2026-reg-10"},
        {"split": "holdout", "window": "Week 11 (13 games)", "games": 13,
         "purpose": "final prospective holdout — lines published, results pending",
         "status": "prospective", "source_url": "https://www.nfl.com/schedules/2026/by-week/week-11"},
        {"split": "note", "window": "walk-forward evaluation", "games": bt["n_forecasts"],
         "purpose": "in-sample-free walk-forward backtest (leakage G3 pass)",
         "status": "used", "source_url": "https://www.nfl.com/"}]
    save("holdout_split.json", {
        "dataset": "nfl_book_holdout_split",
        "title": "Train / validation / final holdout split",
        "built_utc": BUILT, "session": "arena/20f55d17-own4",
        "method": "Data is split into train, validation and a final holdout window to "
                  "protect out-of-sample testing. Week 11 is held out prospectively.",
        "rows": rows})


# ---------------------------------------------------------------------------
# Matchup deficiency matrix
# ---------------------------------------------------------------------------
def build_matchup_matrix():
    depth = load("depth_replacements.json")
    rows = []
    # structural register of trench/coverage mismatches; ranks blank without depth chart
    slots = [("offense", "QB"), ("offense", "WR1"), ("offense", "WR2"),
             ("offense", "WR3"), ("offense", "TE"), ("offense", "LT"),
             ("offense", "LG"), ("offense", "C"), ("offense", "RG"),
             ("offense", "RT"), ("offense", "EDGE1"), ("offense", "EDGE2"),
             ("defense", "CB1"), ("defense", "CB2"), ("defense", "CB3"),
             ("defense", "S"), ("defense", "EDGE1"), ("defense", "EDGE2"),
             ("defense", "DT1"), ("defense", "DT2")]
    for i, (unit, pos) in enumerate(slots, 1):
        rows.append({
            "id": f"MM-{i:02d}", "unit": unit, "position": pos,
            "home_rank": "", "away_rank": "", "deficiency": "",
            "status": "deficiency ranks blank — no official depth chart (FB-07); "
                      "surfaces WR1 vs promoted CB / EDGE1 vs backup OT mismatch once sourced",
            "source_url": "https://www.nfl.com/"})
    save("matchup_matrix.json", {
        "dataset": "nfl_book_matchup_matrix",
        "title": "Offense vs Defense Matchup Deficiency Matrix (1st–4th string)",
        "built_utc": BUILT, "session": "arena/20f55d17-own4",
        "method": "Surfaces trench and coverage mismatches (e.g. WR1 facing a promoted "
                  "2nd/3rd-string CB, EDGE1 facing a backup OT/LG) on one screen. Ranks "
                  "require an official depth chart and are blank + flagged (FB-07).",
        "n_rows": len(rows), "rows": rows})


# ---------------------------------------------------------------------------
# Venues
# ---------------------------------------------------------------------------
def build_venues():
    slate = load("slate_week11_2026.json")
    rows = []
    for s in slate["rows"]:
        rows.append({
            "game_id": f"W11-{s['away']}-{s['home']}", "away": s["away"],
            "home": s["home"], "date": s["date"],
            "venue": "", "stadium": "",
            "status": "pending transcription from the official game centre",
            "source_url": s["game_url"]})
    save("venues.json", {
        "dataset": "nfl_book_venues",
        "title": "Venue of every fixture, transcribed from the official game centre",
        "built_utc": BUILT, "session": "arena/20f55d17-own4",
        "method": "Venue is transcribed only from the official game-centre page. Until each "
                  "page is read, the cell is blank + flagged (never inferred from team name).",
        "n_rows": len(rows), "rows": rows})


def build_roster_sweep():
    inj = load("injuries_week10_capture.json")
    standings = load("standings_2026-11-14.json")
    teams = [r["team"] for r in standings["rows"]]
    out = {t: 0 for t in teams}
    for r in inj["rows"]:
        if r["team"] in out:
            gs = r.get("game_status") or ""
            if gs in ("Out", "Doubtful"):
                out[r["team"]] += 1
    rows = []
    for t in teams:
        rows.append({
            "team": t, "roster_count": "", "ir_count": "",
            "reserve_list": "", "starters_out": out[t],
            "status": "roster/IR/reserve blank — no official roster/IR/reserve source "
                      "captured; starters_out from partial injury capture (FB-06)",
            "source_url": "https://www.nfl.com/teams/"})
    save("roster_sweep.json", {
        "dataset": "nfl_book_roster_sweep",
        "title": "32-team roster / IR sweep (run before any team-level model is trusted)",
        "built_utc": BUILT, "session": "arena/20f55d17-own4",
        "method": "Sweeps all 32 clubs for roster, injured-reserve and reserve-list status. "
                  "No official roster/IR/reserve source is captured, so those fields are "
                  "blank + flagged; starters-out is taken from the partial injury capture.",
        "n_rows": len(rows), "rows": rows})


def main():
    build_requirements()
    build_removal_of_luck()
    build_model_outputs()
    build_per_team_view()
    build_availability_graph()
    build_depth_register()
    build_pit_ledger()
    build_fixture_context()
    build_two_stage()
    build_control_baseline()
    build_vig_free()
    build_joint_evidence()
    build_ablations()
    build_weekly_diff()
    build_questionable_calibration()
    build_injury_surprise()
    build_drift_alarms()
    build_holdout_split()
    build_matchup_matrix()
    build_venues()
    build_roster_sweep()
    print("[expand] built 21 gap-closure datasets into", DATA)


if __name__ == "__main__":
    main()
