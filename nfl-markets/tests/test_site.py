#!/usr/bin/env python3
"""nfl-markets — unit tests (stdlib unittest).

Invariants that must never break:
  T1 snapshot store: every game carries markets seq 1,2,3 exactly once; side rows always have a fair line
  T2 snapshot store: played games always have a close line or an explicit UNVERIFIED-BLANK status
  T3 results feed QC: 2026 standings reconciliation is exact (32/32, 0 mismatches)
  T4 leaderboard: signal and staking ranks exist independently; all strategies PAPER; rewards 0
  T5 demotion gate: counterfactual simulation produces trigger events (state machine exercises)
  T6 correlations: every value row publishes n
  T7 replacement depth: starter-out rows always carry a depth label (2/3/4/NONE); no inferred blanks
  T8 site verifier passes (subprocess)
"""
import csv, json, os, subprocess, sys, unittest
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
NS = os.path.dirname(HERE)
DATA = os.path.join(NS, "data")

def rows(name):
    with open(os.path.join(DATA, name), newline="") as f:
        return list(csv.DictReader(f))

def j(name):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)

class T1T2(unittest.TestCase):
    def test_origination_order_and_fair(self):
        snap = rows("price_snapshots.csv")
        per = Counter(r["game_id"] for r in snap)
        self.assertTrue(all(v == 3 for v in per.values()), "every game must have exactly 3 market rows")
        seqs = Counter((r["game_id"], r["market_seq"]) for r in snap)
        self.assertTrue(all(v == 1 for v in seqs.values()), "market_seq 1,2,3 must be unique per game")
        self.assertTrue(all(r["model_fair_line"] != "" for r in snap if r["market"] == "SIDE"))

    def test_played_games_have_close_or_flag(self):
        snap = rows("price_snapshots.csv")
        for r in snap:
            if r["close_verification_status"] in ("VERIFIED-ARCHIVE", "ARCHIVE-UNPUBLISHED-TIMING"):
                self.assertNotEqual(r["market_close_line"], "", r["snapshot_id"])
            if r["close_verification_status"] == "UNVERIFIED-BLANK":
                self.assertEqual(r["market_close_line"], "", "blank status must mean blank value")

class T3(unittest.TestCase):
    def test_standings_reconciliation_exact(self):
        qc = j("results_feed_qc.json")
        mm = qc["standings_reconciliation_2026"]["mismatches_vs_official_capture"]
        self.assertEqual(mm.get("status"), "OK")
        self.assertEqual(mm.get("official_rows_matched"), 32)
        self.assertEqual(mm.get("mismatches"), [])

class T4(unittest.TestCase):
    def test_leaderboard_separation_and_status(self):
        lb = j("leaderboard.json")
        for r in lb:
            self.assertTrue(r["status"].startswith("PAPER"), r["status"])
            self.assertEqual(r["rewards"], 0)
            if r.get("signal_rank") is not None:
                self.assertIn("beat_close_rate", r["signal"])
            if r.get("staking_rank") is not None:
                self.assertIn("roi_flat", r["staking"])

class T5(unittest.TestCase):
    def test_demotion_machine_exercises(self):
        ge = j("gates_evaluation.json")
        sims = ge["demotion"]["simulations"]
        self.assertTrue(sims)
        for strat, d in sims.items():
            self.assertGreater(d["n_trigger_events"], 0, f"{strat} must exercise the state machine")
            self.assertTrue(d["counterfactual_force_live"])

class T6(unittest.TestCase):
    def test_correlations_publish_n(self):
        corr = j("correlations.json")
        for group in ("official_inputs", "third_party_inputs_flagged"):
            for r in corr[group]:
                self.assertIn("n", r, r["id"])
                if r.get("value") is not None:
                    self.assertIsInstance(r["n"], int) and self.assertGreater(r["n"], 0)
                for k in ("source_keys", "verification"):
                    self.assertIn(k, r, r["id"])

class T7(unittest.TestCase):
    def test_replacement_depth_rows(self):
        inj = j("replacement_depth.json")
        for r in inj["rows"]:
            if r["starter_out_row"]:
                self.assertIn(str(r["replacement_depth"]), ("2", "3", "4", "NONE"), r)
                self.assertNotEqual(r["deficiency_points"], "")
        self.assertGreater(len([r for r in inj["rows"] if r["starter_out_row"]]), 0)
        # uncovered teams explicitly flagged, never silently blank
        for t, v in inj["team_summary"].items():
            if v.get("deficiency_index") is None:
                self.assertIn("flag", v)

class T8(unittest.TestCase):
    def test_site_verifier_passes(self):
        res = subprocess.run([sys.executable, os.path.join(NS, "engine", "verify.py")],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("VERIFY: ALL PASS", res.stdout)

if __name__ == "__main__":
    unittest.main(verbosity=2)
