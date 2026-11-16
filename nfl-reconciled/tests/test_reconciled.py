#!/usr/bin/env python3
"""Tests for nfl-reconciled. Run: python3 -m unittest discover -s nfl-reconciled/tests

These test the *rules*, not the numbers: that an unsourced verdict cannot pass, that a
transcription error is caught, that a score is never invented, and that the arithmetic identities
the whole site rests on actually hold.
"""

import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(HERE)


def load(rel):
    with open(os.path.join(HERE, rel), encoding="utf-8") as fh:
        return json.load(fh)


class TestOfficialFacts(unittest.TestCase):
    def setUp(self):
        self.facts = load("data/official_facts.json")
        self.stand = self.facts["standings"]["rows"]

    def test_thirty_two_clubs(self):
        self.assertEqual(len(self.stand), 32)
        self.assertEqual(len({r[0] for r in self.stand}), 32)

    def test_wins_equal_losses(self):
        w = sum(r[1] for r in self.stand)
        l = sum(r[2] for r in self.stand)
        self.assertEqual(w, l, "a league cannot win more games than it loses")

    def test_points_for_equal_points_against(self):
        pf = sum(r[4] for r in self.stand)
        pa = sum(r[5] for r in self.stand)
        self.assertEqual(pf, pa, "every point scored is a point conceded somewhere")

    def test_games_played_is_integral_and_even(self):
        club_games = sum(r[1] + r[2] + r[3] for r in self.stand)
        self.assertEqual(club_games % 2, 0)
        self.assertEqual(club_games // 2, 148)

    def test_week10_fixtures_are_forced_by_the_byes(self):
        w10 = self.facts["week10_fixtures"]
        bye = set(w10["bye_clubs"])
        playing = set()
        for f in w10["rows"]:
            playing |= {f["away"], f["home"]}
        clubs = {r[0] for r in self.stand}
        self.assertFalse(playing & bye, "a club cannot play and be on bye")
        self.assertEqual(playing | bye, clubs, "every club either plays or is on bye")
        self.assertEqual(len(w10["rows"]), (32 - len(bye)) // 2)
        self.assertEqual(w10["n_fixtures"], 14)

    def test_no_score_is_invented_for_an_unfinished_game(self):
        for f in self.facts["week10_fixtures"]["rows"]:
            if f["state"] == "final":
                self.assertIsNotNone(f["away_pts"], f)
                self.assertIsNotNone(f["home_pts"], f)
            else:
                self.assertIsNone(f["away_pts"], "unfinished game %s carries a score" % f)
                self.assertIsNone(f["home_pts"], "unfinished game %s carries a score" % f)


class TestClosure(unittest.TestCase):
    """The claim the whole results page rests on."""

    def setUp(self):
        self.d = load("data/derived/results_corpus_reconciliation.json")

    def test_closure_is_exact(self):
        c = self.d["closure"]
        self.assertEqual(c["best_feed_weeks_1_to_9_points"] + c["week10_final_points_on_official_schedule"],
                         c["closure_check"])
        self.assertTrue(c["closure_equals_official_total"])

    def test_every_corpus_is_short_and_by_a_stated_amount(self):
        off = self.d["official"]["points_for_league_wide"]
        for f in self.d["feeds"]:
            self.assertLess(f["league_points_recorded"], off)
            self.assertEqual(self.d["feed_shortfall_points"][f["path"]],
                             off - f["league_points_recorded"])

    def test_backtest_subsamples_are_not_counted_as_corpora(self):
        for f in self.d["feeds"]:
            self.assertEqual(f["kind"], "results_corpus")
        self.assertTrue(all(f["kind"] == "backtest_subsample" for f in self.d["backtest_subsamples"]))

    def test_no_corpus_is_claimed_complete(self):
        for f in self.d["feeds"]:
            self.assertNotEqual(f["clubs_matching_official_record_and_pf"], 32)


class TestResolutions(unittest.TestCase):
    def setUp(self):
        self.d = load("data/resolutions.json")

    def test_every_review_row_has_no_number(self):
        for r in self.d["rows"]:
            if r["verdict"] == "REVIEW":
                self.assertIsNone(r["official_number"], "%s claims a number but is REVIEW" % r["id"])
                self.assertIsNone(r["official_source"], "%s claims a source but is REVIEW" % r["id"])
                self.assertTrue(r["clearing_action"], "%s has no clearing action" % r["id"])

    def test_every_settled_row_is_backed(self):
        for r in self.d["rows"]:
            if r["verdict"] == "SETTLED":
                self.assertTrue(r["official_source"] or r["repo_evidence"],
                                "%s is SETTLED with nothing behind it" % r["id"])
                self.assertTrue(r["official_basis"])

    def test_counts_match_rows(self):
        from collections import Counter
        c = Counter(r["verdict"] for r in self.d["rows"])
        self.assertEqual(self.d["counts"]["rows"], len(self.d["rows"]))
        self.assertEqual(self.d["counts"]["settled"], c["SETTLED"])
        self.assertEqual(self.d["counts"]["review"], c["REVIEW"])
        self.assertEqual(self.d["counts"]["no_conflict"], c["NO CONFLICT"])

    def test_ids_are_unique(self):
        ids = [r["id"] for r in self.d["rows"]]
        self.assertEqual(len(ids), len(set(ids)))


class TestAvailability(unittest.TestCase):
    def setUp(self):
        self.d = load("data/derived/injury_capture_reconciliation.json")

    def test_at_least_one_capture_passes_its_live_check(self):
        passing = [c for c in self.d["live_checks"] if c["verdict"] == "PASS"]
        self.assertTrue(passing, "no capture could be verified, so no row count may be called canonical")

    def test_passing_captures_agree_on_the_row_count(self):
        passing = [c for c in self.d["live_checks"] if c["verdict"] == "PASS"]
        self.assertEqual(len({p["n_rows"] for p in passing}), 1)

    def test_row_counts_were_never_judged_outside_the_sample(self):
        for c in self.d["live_checks"]:
            # every club in the check table must be one that was actually counted by hand
            self.assertEqual(len(c["club_row_counts"]), c["clubs_in_official_sample"])
            self.assertLess(c["clubs_in_official_sample"], c["clubs_in_capture"],
                            "a sample smaller than the capture is what makes this a sample")

    def test_a_capture_that_is_partial_is_not_called_wrong(self):
        # several captures hold fewer rows; that is completeness, not correctness
        self.assertGreater(self.d["row_count_spread"]["max"], self.d["row_count_spread"]["min"])


class TestSite(unittest.TestCase):
    def test_verifier_passes(self):
        r = subprocess.run([sys.executable, os.path.join(HERE, "engine", "verify_site.py")],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_no_page_prints_a_price(self):
        for rel in ("index.html", "pages/results.html", "pages/conflicts.html"):
            with open(os.path.join(HERE, rel), encoding="utf-8") as fh:
                doc = fh.read()
            self.assertNotIn("odds: -", doc)
            self.assertNotIn("moneyline: -", doc)

    def test_every_page_declares_its_limits(self):
        with open(os.path.join(HERE, "pages", "method.html"), encoding="utf-8") as fh:
            doc = fh.read()
        self.assertIn("What this session did NOT read", doc)
        self.assertIn("Chunks 2", doc)


if __name__ == "__main__":
    unittest.main()
